from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required
from models.user import User
from models.subscription import Subscription
from app import app, csrf
from rentista_web.util import mollie
from rentista_web.util.pricing import SUBSCRIPTION_PLANS
from rentista_web.util.payments import active_subscription, base_url, handle_subscription_payment

subscriptions_blueprint = Blueprint('subscriptions',
                                    __name__,
                                    template_folder='templates')


def confirm_page(outfits):
    """Show the chosen plan with a button that starts the Mollie payment."""
    if outfits not in SUBSCRIPTION_PLANS:
        abort(404)
    if current_user.is_authenticated and active_subscription(current_user.id):
        flash("Je hebt al een abonnement. Neem contact met ons op als je het wilt wijzigen.")
        return redirect(url_for('home'))
    return render_template('subscriptions/new.html', outfits=outfits,
                           price=SUBSCRIPTION_PLANS[outfits])


@subscriptions_blueprint.route('/pick', methods=['POST', 'GET'])
def pick():
    return render_template('subscriptions/pick.html')


@subscriptions_blueprint.route('/standard', methods=['POST', 'GET'])
def standard():
    return confirm_page(3)


@subscriptions_blueprint.route('/premium', methods=['POST', 'GET'])
def premium():
    return confirm_page(4)


@subscriptions_blueprint.route('/exclusive', methods=['POST', 'GET'])
def exclusive():
    return confirm_page(5)


@subscriptions_blueprint.route('/start/<int:outfits>/', methods=['POST'])
@login_required
def start(outfits):
    if outfits not in SUBSCRIPTION_PLANS:
        abort(404)
    if active_subscription(current_user.id):
        flash("Je hebt al een abonnement. Neem contact met ons op als je het wilt wijzigen.")
        return redirect(url_for('home'))

    price = SUBSCRIPTION_PLANS[outfits]
    user = User.get_by_id(current_user.id)
    try:
        if not user.mollie_customer_id:
            customer = mollie.create_customer(user.name, user.email)
            user.mollie_customer_id = customer['id']
            user.save()

        subscription = Subscription(user=user.id, subscription_type=str(outfits),
                                    subscription_price=price, subscription_active=False)
        subscription.save()

        # The first payment pays month one and gives Mollie a mandate for
        # the automatic monthly payments after that.
        payment = mollie.create_payment(
            amount=price,
            description='Rentista abonnement %s outfits - eerste maand' % outfits,
            redirect_url=base_url() + url_for('subscriptions.payment_return', subscription_id=subscription.id),
            webhook=mollie.webhook_url(base_url(), url_for('subscriptions.webhook')),
            metadata={'subscription_id': subscription.id},
            customer_id=user.mollie_customer_id,
            sequence_type='first',
        )
    except mollie.MollieError as error:
        app.logger.error('Mollie subscription start for user %s failed: %s', user.id, error)
        flash('Afrekenen lukt nu niet. Probeer het later opnieuw.')
        return redirect(url_for('subscriptions.pick'))

    subscription.mollie_payment_id = payment['id']
    subscription.save()
    return redirect(mollie.checkout_url(payment))


@subscriptions_blueprint.route('/payment_return/<int:subscription_id>/', methods=['GET'])
@login_required
def payment_return(subscription_id):
    subscription = Subscription.get_or_none(Subscription.id == subscription_id)
    if subscription is None or subscription.user_id != current_user.id or not subscription.mollie_payment_id:
        abort(404)

    payment = mollie.get_payment(subscription.mollie_payment_id)
    subscription = handle_subscription_payment(payment) or subscription

    if subscription.subscription_active:
        flash("Welkom! Je abonnement is actief.")
        return redirect(url_for('outfits.show'))
    if payment['status'] in ('failed', 'canceled', 'expired'):
        flash("De betaling is niet gelukt of geannuleerd. Je kunt het opnieuw proberen.")
        return redirect(url_for('subscriptions.pick'))
    flash("We wachten nog op de bevestiging van je betaling. Je abonnement wordt actief zodra die binnen is.")
    return redirect(url_for('home'))


@subscriptions_blueprint.route('/webhook', methods=['POST'])
@csrf.exempt
def webhook():
    """Called by Mollie for the first payment and for every monthly payment."""
    payment_id = request.form.get('id')
    if not payment_id:
        return '', 200
    try:
        payment = mollie.get_payment(payment_id)
    except mollie.MollieError as error:
        if error.status == 404:
            return '', 200
        raise
    handle_subscription_payment(payment)
    return '', 200
