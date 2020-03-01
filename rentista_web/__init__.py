from app import app
from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from rentista_web.blueprints.users.views import users_blueprint
from rentista_web.blueprints.sessions.views import sessions_blueprint
from rentista_web.blueprints.outfits.views import outfits_blueprint
from rentista_web.blueprints.subscriptions.views import subscriptions_blueprint
from rentista_web.blueprints.orders.views import orders_blueprint
from flask_assets import Environment, Bundle
from .util.assets import bundles
from rentista_web.util.oauth import oauth
from flask_login import login_required, current_user, login_user
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from models.outfit import Outfit
from models.outfit_picture import Outfit_Picture
from models.subscription import Subscription
import braintree
import os
import config
from rentista_web.util.braintree import generate_client_token, gateway, find_transaction, transact, create_customer, subscription_create



oauth.init_app(app)


assets = Environment(app)
assets.register(bundles)

app.register_blueprint(users_blueprint, url_prefix="/users")
app.register_blueprint(sessions_blueprint, url_prefix="/sessions")
app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
app.register_blueprint(subscriptions_blueprint, url_prefix="/subscriptions")
app.register_blueprint(orders_blueprint, url_prefix="/orders")


TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route("/")
def home():
    pictures = Outfit_Picture.select().where(Outfit_Picture.outfit == 78)
    # outfit = Outfit.select().where(Outfit.id == 78)

    return render_template('home.html', pictures=pictures)


@app.route('/new_1', methods=['POST', 'GET'])
@login_required
def new_1():
    client_token = generate_client_token()
    price = request.form.get('price')
    if price == 93:
        subscriptiontype= 'standard'
    elif price == 109:
        subscriptiontype = 'premium'
    else:
        subscriptiontype = 'exclusive'  
    
    subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    if subscription:
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))
    else:
        return render_template('subscriptions/new.html', client_token=client_token, price=price, subscriptiontype=subscriptiontype)
         
   


@app.route('/new_2', methods=['POST', 'GET'])
@login_required
def new_2():
    client_token = generate_client_token()
    price = request.form.get('price')
    if price == 93:
        subscriptiontype= 'standard'
    elif price == 109:
        subscriptiontype = 'premium'
    else:
        subscriptiontype = 'exclusive'    
    
    subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    if subscription:
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))
    else:
        return render_template('subscriptions/new.html', client_token=client_token, price=price, subscriptiontype=subscriptiontype)
         

