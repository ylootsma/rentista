from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.user import User
from models.subscription import Subscription
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from rentista_web.util.oauth import oauth
from app import app
from os.path import join, dirname
from dotenv import load_dotenv
import braintree
import os
from rentista_web.util.helpers import *
from rentista_web.util.braintree import generate_client_token, gateway, find_transaction, transact, create_customer, subscription_create

subscriptions_blueprint = Blueprint('subscriptions',
                                    __name__,
                                    template_folder='templates')


TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]


@subscriptions_blueprint.route('/pick', methods=['POST', 'GET'])

def pick():
  

    return render_template('subscriptions/pick.html')


@subscriptions_blueprint.route('/standard', methods=['POST', 'GET'])

def standard():
    client_token = generate_client_token()
    price = 93
    subscriptiontype= "standard"
   

    subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    if subscription:
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))
    else:
        return render_template('subscriptions/new.html', client_token=client_token, price=price, subscriptiontype=subscriptiontype)


@subscriptions_blueprint.route('/premium', methods=['POST', 'GET'])

def premium():
    client_token = generate_client_token()
    price = 109
    subscriptiontype= "premium"
    
    subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    if subscription:
        flash("You already have a subscription. Contact us in case you would like to change.")
        return redirect(url_for('home'))
    else:
        return render_template('subscriptions/new.html', client_token=client_token, price=price, subscriptiontype=subscriptiontype)


@subscriptions_blueprint.route('/exclusive', methods=['POST', 'GET'])

def exclusive():
    client_token = generate_client_token()
    price = 125
    subscriptiontype= "exclusive"
   
    
    subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    if subscription:
        flash("You already have a subscription. Contact us in case you would like to change.")
    else:
        return render_template('subscriptions/new.html', client_token=client_token, price=price, subscriptiontype=subscriptiontype)


@subscriptions_blueprint.route('/subscriptions/<subscriptiontype>/<price>/', methods=['POST', 'GET'])
def create_checkout(subscriptiontype,price):
    subscription = ""
    subscriptiontype = subscriptiontype
    subscriptionprice = price
    result = transact({
        'amount': request.form.get('amount'),
        'payment_method_nonce': request.form.get('payment_method_nonce'),
        'options': {
            "submit_for_settlement": True
        }
    })
    if result.is_success or result.transaction:
        subscription = Subscription(user=current_user.id,
                                    subscription_active=True, subscription_type=subscriptiontype,subscription_price=subscriptionprice)
        if subscription.save():
            flash("Grazie Mille!!")
            return render_template('home.html')
    else:
        for x in result.errors.deep_errors:
            flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('subscriptions.pick'))

