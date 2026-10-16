from flask import Blueprint, render_template, request, flash, redirect, url_for
from models.outfit import Outfit
from models.order_outfit import Order_Outfit
from models.order import Order
from models.adress import Adress
from models.invoice import Invoice
from models.user import User
from flask_login import current_user, login_required
from rentista_web.util.helpers import send_email
from rentista_web.util.braintree import generate_client_token, transact
from rentista_web.util.shop import cart_summary, cart_problems, get_cart, open_order, place_order


orders_blueprint = Blueprint('orders',
                              __name__,
                              template_folder='templates')


@orders_blueprint.route('/show/', methods=['POST', 'GET'])
@login_required
def show():
    user = User.get_by_id(current_user.id)
    order_open = []
    order_closed = []
    orders = Order.select().where(Order.user == user).order_by(Order.order_date.desc())

    for order in orders:
        for order_outfit in Order_Outfit.select().where(Order_Outfit.order == order.id):
            outfit = Outfit.get(Outfit.id == order_outfit.outfit)
            order_info = [order.order_date, order_outfit.size, outfit.outfit_name, outfit.brand_name]
            if order.is_open:
                order_open.append(order_info)
            else:
                order_closed.append(order_info)

    order_open_length = len(order_open)
    order_closed_length = len(order_closed)
    orderstate = 0 if order_open_length == 0 and order_closed_length == 0 else 1

    return render_template('orders/show.html', orderstate=orderstate, order_open=order_open, user=user, order_closed=order_closed, order_open_length=order_open_length, order_closed_length=order_closed_length)


def _check_can_order():
    """Return a redirect response when the current cart can't be ordered, else None."""
    cart, _ = get_cart()
    if not cart:
        flash('Je winkelmand is leeg.')
        return redirect(url_for('outfits.show'))
    if open_order(current_user):
        flash('Je hebt al een lopende bestelling. Contacteer ons om je bestelling te wijzigen.')
        return redirect(url_for('orders.show'))
    problems = cart_problems()
    if problems:
        for problem in problems:
            flash(problem)
        return redirect(url_for('outfits.show'))
    return None


def _finish_order():
    order = place_order(current_user)
    send_email(current_user.email, 'Bedankt voor je bestelling bij Rentista',
               f'Hoi {current_user.name},\n\n'
               f'We hebben je bestelling #{order.id} ontvangen en gaan deze klaarmaken.\n\n'
               'Groet,\nRentista')
    flash('Bedankt voor je bestelling')
    return redirect(url_for('orders.show'))


# The price in the URL is ignored: it is only kept so old links keep working.
# The amount to pay is always calculated on the server from the cart.
@orders_blueprint.route('/new/', defaults={'price': None}, methods=['POST', 'GET'])
@orders_blueprint.route('/new/<price>/', methods=['POST', 'GET'])
@login_required
def new(price):
    adress = Adress.get_or_none(Adress.user == current_user.id)
    if adress:
        return redirect(url_for('orders.create'))
    else:
        return render_template('orders/adress.html')


@orders_blueprint.route('/create_adress/', defaults={'price': None}, methods=['POST'])
@orders_blueprint.route('/create_adress/<price>/', methods=['POST'])
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
            return render_template('orders/invoice.html')
        else:
            return redirect(url_for('orders.create'))
    flash('Er is iets fout gegaan. Probeer het opnieuw aub')
    return redirect(url_for('orders.new'))


@orders_blueprint.route('/create_invoice/', defaults={'price': None}, methods=['POST'])
@orders_blueprint.route('/create_invoice/<price>/', methods=['POST'])
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
        return redirect(url_for('orders.create'))
    flash('Er is iets fout gegaan. Probeer het opnieuw aub')
    return redirect(url_for('orders.new'))


@orders_blueprint.route('/create/', defaults={'price': None}, methods=['POST', 'GET'])
@orders_blueprint.route('/create/<price>/', methods=['POST', 'GET'])
@login_required
def create(price):
    problem = _check_can_order()
    if problem:
        return problem

    price = cart_summary(current_user)['price']
    if price > 0:
        return render_template('orders/checkout.html', price=price, client_token=generate_client_token())

    # Everything in the cart is covered by the subscription
    return _finish_order()


@orders_blueprint.route('/orders/simple_message/', methods=['POST', 'GET'])
@login_required
def simple_message():
    # Old confirmation URL, kept for existing links
    return redirect(url_for('orders.show'))


@orders_blueprint.route('/orders/create_checkout/', methods=['POST'])
@login_required
def create_checkout():
    problem = _check_can_order()
    if problem:
        return problem

    price = cart_summary(current_user)['price']
    if price <= 0:
        return _finish_order()

    result = transact({
        'amount': f'{price:.2f}',
        'payment_method_nonce': request.form.get('payment_method_nonce'),
        'options': {
            "submit_for_settlement": True
        }
    })

    if not result.is_success:
        if result.errors.deep_errors:
            for x in result.errors.deep_errors:
                flash('Error: %s: %s' % (x.code, x.message))
        else:
            flash('De betaling is niet gelukt: %s' % result.message)
        return redirect(url_for('orders.create'))

    return _finish_order()
