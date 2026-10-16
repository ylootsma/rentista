from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from models.subscription import Subscription
from flask_login import current_user, login_required
from rentista_web.util.braintree import generate_client_token, transact
from rentista_web.util.shop import PLANS

subscriptions_blueprint = Blueprint('subscriptions',
                                    __name__,
                                    template_folder='templates')


@subscriptions_blueprint.route('/pick', methods=['POST', 'GET'])
def pick():
    return render_template('subscriptions/pick.html')


def start_subscription(subscriptiontype):
    if Subscription.get_or_none(Subscription.user == current_user.id):
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))
    price = PLANS[subscriptiontype]['price']
    return render_template('subscriptions/new.html', client_token=generate_client_token(), price=price, subscriptiontype=subscriptiontype)


@subscriptions_blueprint.route('/standard', methods=['POST', 'GET'])
@login_required
def standard():
    return start_subscription('standard')


@subscriptions_blueprint.route('/premium', methods=['POST', 'GET'])
@login_required
def premium():
    return start_subscription('premium')


@subscriptions_blueprint.route('/exclusive', methods=['POST', 'GET'])
@login_required
def exclusive():
    return start_subscription('exclusive')


# The price in the URL is ignored: the plan decides what is charged.
@subscriptions_blueprint.route('/subscriptions/<subscriptiontype>/<price>/', methods=['POST'])
@login_required
def create_checkout(subscriptiontype, price):
    plan = PLANS.get(subscriptiontype)
    if plan is None:
        abort(404)
    if Subscription.get_or_none(Subscription.user == current_user.id):
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))

    result = transact({
        'amount': f"{plan['price']:.2f}",
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
        return redirect(url_for('subscriptions.pick'))

    # subscription_type stores the number of outfits included in the plan
    Subscription.create(user=current_user.id,
                        subscription_type=str(plan['outfits']),
                        subscription_price=plan['price'])
    flash("Grazie Mille!!")
    return redirect(url_for('home'))
