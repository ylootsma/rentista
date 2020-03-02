from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
from models.subscription import Subscription
from models.outfit_picture import Outfit_Picture
from models.adress import Adress
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from rentista_web.util.oauth import oauth
from app import app
import boto3
import math
from rentista_web.util.helpers import *
from playhouse.flask_utils import FlaskDB, object_list
from peewee import *
from database import *
from dotenv import load_dotenv
import braintree
import os
from rentista_web.util.helpers import *
from rentista_web.util.braintree import generate_client_token, gateway, find_transaction, transact, create_customer, subscription_create
from random import randrange
import datetime


orders_blueprint = Blueprint('orders',
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


@orders_blueprint.route('/new/<price>/', methods=['POST', 'GET'])
@login_required
def new(price):
    price=price
    adress = Adress.get_or_none(Adress.user == current_user.id)
    if adress:
        return redirect(url_for('orders.create', price=price))
    else:    
        return render_template('orders/new.html', price=price)


@orders_blueprint.route('/create/<price>/', methods=['POST', 'GET'])
@login_required
def create(price):
    client_token = generate_client_token()
    price=float(price)
    adress = Adress.get_or_none(Adress.user == current_user.id)
    if adress:
        if price>0:
            return render_template('orders/checkout.html', price=price, client_token=client_token)   
        else:
            order = Order(order_customer_id=randrange(10), user=current_user.id, order_date=datetime.datetime.today(), status='preparation', is_open=True)
            if order.save():
                sess = session['cart']
                for s in sess:
                        order_outfit = Order_Outfit(order=order.id, outfit=s)
                        order_outfit.save():
                flash('Bedankt voor je bestelling')
                return redirect(url_for('home'))

                else:
                    flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
                    return render_template('home')

            else:
                flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
                return render_template('home')       
    else:
        name = request.form.get('name')
        street = request.form.get('street')
        housenumber = request.form.get('housenumber')
        postal = request.form.get('postal')
        city = request.form.get('city')
        country = request.form.get('country')
        phone = request.form.get('phone')

        adress = Adress(user_id=current_user.id, name=name, street=street, housenumber=housenumber, postal=postal, city=city, country=country, phone=phone)
        if adress.save():
            if price>0:
                return render_template('orders/checkout.html', price=price, client_token=client_token)   
            else:
                order = Order(order_customer_id=randrange(10), user=current_user.id, order_date=datetime.datetime.today(), status='preparation', is_open=True)
                if order.save():
                    sess = session['cart']
                    for s in sess:
                        order_outfit = Order_Outfit(order=order.id, outfit=s)
                        order_outfit.save():
                flash('Bedankt voor je bestelling')
                return redirect(url_for('home'))

                else:
                    flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
                    return render_template('home')   
             
        else:
            flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
            return render_template('home')    

@subscriptions_blueprint.route('/orders/create_checkout/', methods=['POST', 'GET'])
def create_checkout():
    subscription = ""
    subscriptiontype = subscriptiontype
    result = transact({
        'amount': request.form.get('amount'),
        'payment_method_nonce': request.form.get('payment_method_nonce'),
        'options': {
            "submit_for_settlement": True
        }
    })

    if result.is_success or result.transaction:
        order = Order(order_customer_id=randrange(10), user=current_user.id, order_date=datetime.datetime.today(), status='preparation', is_open=True)
        if order.save():
            sess = session['cart']
            for s in sess:
                order_outfit = Order_Outfit(order=order.id, outfit=s)
                order_outfit.save():
            flash('Bedankt voor je bestelling')
            return redirect(url_for('home'))

        else:
            flash("Something went wrong please try again")   
            return redirect(url_for('home'))
        
    else:
        for x in result.errors.deep_errors:
            flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('home'))

    

   