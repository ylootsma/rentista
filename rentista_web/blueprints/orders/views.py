from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from flask_login import current_user, login_required
from models.outfit import Outfit
from models.order_outfit import Order_Outfit
from models.order import Order
from models.adress import Adress
from models.invoice import Invoice
from models.user import User
from app import app, csrf
from rentista_web.util import mollie
from rentista_web.util.pricing import calculate_cart, subscription_outfits
from rentista_web.util.payments import (
    AWAITING_PAYMENT, PAYMENT_FAILED, PREPARATION, UNPAID_STATUSES,
    active_subscription, base_url, finalize_order, handle_order_payment)
from random import randrange
import datetime
import requests
from config import Config


orders_blueprint = Blueprint('orders',
                             __name__,
                             template_folder='templates')


@orders_blueprint.route('/show/', methods=['POST', 'GET'])
@login_required
def show():
    user = User.get_by_id(current_user.id)
    orderstate = 0
    order_open = []
    order_closed = []
    orders = Order.select().where(
        (Order.user == user) & (Order.status.not_in(UNPAID_STATUSES)))

    for order in orders:
        order_outfit = Order_Outfit.get(Order_Outfit.order == order.id)
        outfit = Outfit.get(Outfit.id == order_outfit.outfit)
        order_info = [order.order_date, order_outfit.size, outfit.outfit_name, outfit.brand_name]
        if order.is_open == True:
            order_open.append(order_info)
        else:
            order_closed.append(order_info)

    order_open_length = len(order_open)
    order_closed_length = len(order_closed)
    if order_open_length == 0 and order_closed_length == 0:
        orderstate = 0
    else:
        orderstate = 1

    return render_template('orders/show.html', orderstate=orderstate, order_open=order_open, user=user, order_closed=order_closed, order_open_length=order_open_length, order_closed_length=order_closed_length)


@orders_blueprint.route('/new/<price>/', methods=['POST', 'GET'])
@login_required
def new(price):
    adress = Adress.get_or_none(Adress.user == current_user.id)
    if adress:
        return redirect(url_for('orders.create', price=price))
    else:
        return render_template('orders/adress.html', price=price)


@orders_blueprint.route('/create_adress/<price>/', methods=['POST', 'GET'])
@login_required
def create_adress(price):
    invoice = request.form.get('invoice')
    name = request.form.get('name')
    street = request.form.get('street')
    housenumber = request.form.get('housenumber')
    postal = request.form.get('postal')
    city = request.form.get('city')
    country = request.form.get('country')
    phone = request.form.get('phone')

    adress = Adress(user_id=current_user.id, name=name, street=street, housenumber=housenumber, postal=postal, city=city, country=country, phone=phone)
    if adress.save():
        if invoice == "true":
            return render_template('users/invoice.html', price=price)
        else:
            return redirect(url_for('orders.create', price=price))
    flash('Er is iets fout gegaan. Probeer het opnieuw aub')
    return redirect(url_for('orders.new', price=price))


@orders_blueprint.route('/create_invoice/<price>/', methods=['POST', 'GET'])
@login_required
def create_invoice(price):
    name = request.form.get('name')
    street = request.form.get('street')
    housenumber = request.form.get('housenumber')
    postal = request.form.get('postal')
    city = request.form.get('city')
    country = request.form.get('country')
    phone = request.form.get('phone')

    invoice = Invoice(user_id=current_user.id, name=name, street=street, housenumber=housenumber, postal=postal, city=city, country=country, phone=phone)
    if invoice.save():
        return redirect(url_for('orders.create', price=price))
    flash('Er is iets fout gegaan. Probeer het opnieuw aub')
    return redirect(url_for('orders.new', price=price))


# ---------------------------------------------------------------- checkout

def _cart():
    """Outfits and sizes in the session cart, in cart order."""
    outfit_ids = session.get('cart') or []
    sizes = session.get('size') or []
    outfits = []
    for outfit_id in outfit_ids:
        outfit = Outfit.get_or_none(Outfit.id == outfit_id)
        if outfit is not None:
            outfits.append(outfit)
    return outfits, sizes


def _quote():
    outfits, sizes = _cart()
    subscription = active_subscription(current_user.id)
    quote = calculate_cart(outfits, subscription_outfits(subscription))
    return outfits, sizes, quote


def _has_order():
    return Order.select().where(
        (Order.user == current_user.id) & (Order.status.not_in(UNPAID_STATUSES))).exists()


def _create_order(outfits, sizes, amount):
    order = Order(order_customer_id=randrange(10), user=current_user.id,
                  order_date=datetime.datetime.today(), status=AWAITING_PAYMENT,
                  is_open=False, amount=amount)
    order.save()
    session_ids = session.get('cart') or []
    for outfit in outfits:
        size = sizes[session_ids.index(outfit.id)] if outfit.id in session_ids else None
        Order_Outfit(order=order.id, outfit=outfit.id, size=size or 'size_m').save()
    return order


def _clear_cart():
    session.pop("cart", None)
    session.pop("size", None)


@orders_blueprint.route('/create/<price>/', methods=['POST', 'GET'])
@login_required
def create(price):
    # The price in the URL is only shown on the cart page; what is charged is
    # always calculated again here on the server.
    outfits, sizes, quote = _quote()
    if not outfits:
        flash('Je winkelmandje is leeg.')
        return redirect(url_for('outfits.show'))
    if _has_order():
        flash('Je hebt al een bestelling. Contacteer ons om je bestelling te wijzigen.')
        return redirect(url_for('home'))

    if quote['price'] <= 0:
        # Fully covered by the subscription: no payment needed.
        order = _create_order(outfits, sizes, 0)
        finalize_order(order.id)
        _clear_cart()
        flash('Bedankt voor je bestelling')
        return redirect(url_for('orders.show'))

    return render_template('orders/checkout.html', quote=quote)


@orders_blueprint.route('/pay/', methods=['POST'])
@login_required
def pay():
    outfits, sizes, quote = _quote()
    if not outfits or quote['price'] <= 0:
        return redirect(url_for('orders.create', price=0))
    if _has_order():
        flash('Je hebt al een bestelling. Contacteer ons om je bestelling te wijzigen.')
        return redirect(url_for('home'))
    adress = Adress.get_or_none(Adress.user == current_user.id)
    if adress is None:
        return redirect(url_for('orders.new', price=quote['price']))

    user = User.get_by_id(current_user.id)
    order = _create_order(outfits, sizes, quote['price'])
    address = mollie.build_address(
        adress.name or user.name, user.email, adress.street, adress.housenumber,
        adress.postal, adress.city, adress.country, adress.phone)
    lines = mollie.build_order_lines(
        [("%s %s" % (o.brand_name, o.outfit_name), o.outfit_price) for o in quote['charged']],
        quote['discount'])

    try:
        payment = mollie.create_payment(
            amount=quote['price'],
            description='Rentista bestelling %s' % order.id,
            redirect_url=base_url() + url_for('orders.payment_return', order_id=order.id),
            webhook=mollie.webhook_url(base_url(), url_for('orders.webhook')),
            metadata={'order_id': order.id},
            lines=lines,
            billing_address=address,
            shipping_address=address,
        )
    except mollie.MollieError as error:
        app.logger.error('Mollie payment for order %s failed: %s', order.id, error)
        order.status = PAYMENT_FAILED
        order.save()
        flash('Afrekenen lukt nu niet. Probeer het later opnieuw.')
        return redirect(url_for('outfits.show'))

    order.mollie_payment_id = payment['id']
    order.save()
    return redirect(mollie.checkout_url(payment))


@orders_blueprint.route('/payment_return/<int:order_id>/', methods=['GET'])
@login_required
def payment_return(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if order is None or order.user_id != current_user.id or not order.mollie_payment_id:
        abort(404)

    payment = mollie.get_payment(order.mollie_payment_id)
    order = handle_order_payment(payment) or order

    if order.status == PREPARATION:
        _clear_cart()
        flash('Bedankt voor je bestelling!')
        return redirect(url_for('orders.show'))
    if order.status == PAYMENT_FAILED:
        flash('De betaling is niet gelukt of geannuleerd. Je kunt het opnieuw proberen.')
        return redirect(url_for('outfits.show'))
    flash('We wachten nog op de bevestiging van je betaling. Je krijgt bericht zodra die binnen is.')
    return redirect(url_for('home'))


@orders_blueprint.route('/webhook/', methods=['POST'])
@csrf.exempt
def webhook():
    """Mollie calls this with only a payment id; the status is fetched from Mollie."""
    payment_id = request.form.get('id')
    if not payment_id:
        return '', 200
    try:
        payment = mollie.get_payment(payment_id)
    except mollie.MollieError as error:
        if error.status == 404:
            return '', 200
        raise
    handle_order_payment(payment)
    return '', 200


@orders_blueprint.route('/orders/simple_message/', methods=['POST', 'GET'])
@login_required
def simple_message():
    user = User.get_by_id(current_user.id)
    return requests.post(
                    "https://api.eu.mailgun.net/v3/rentista@sandboxaa7f9769c89d4e3fbf3eaa85adea5215.mailgun.org/messages",
                    auth=("api", Config.mailgun),
                    data={"from": "Rentista <rentista@sandboxaa7f9769c89d4e3fbf3eaa85adea5215.mailgun.org>",
                    "to": [user.name, "ylootsma@gmail.com"],
                    "subject": "Hello",
                    "text": "Testing some Mailgun awesomness!"})
