from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
from models.subscription import Subscription
from models.outfit_picture import Outfit_Picture
from models.order_outfit import Order_Outfit
from models.order import Order
from models.adress import Adress
from models.size import Size
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
        return render_template('orders/adress.html', price=price)


@orders_blueprint.route('/create_adress/<price>/', methods=['POST', 'GET'])
@login_required
def create_adress(price):
    price=price   
    name = request.form.get('name')
    street = request.form.get('street')
    housenumber = request.form.get('housenumber')
    postal = request.form.get('postal')
    city = request.form.get('city')
    country = request.form.get('country')
    phone = request.form.get('phone')

    adress = Adress(user_id=current_user.id, name=name, street=street, housenumber=housenumber, postal=postal, city=city, country=country, phone=phone)
    if adress.save():   
        return redirect(url_for('orders.create', price=price))

@orders_blueprint.route('/create/<price>/', methods=['POST', 'GET'])
@login_required
def create(price):
    client_token = generate_client_token()
    price=float(price)
    order = Order.get_or_none(Order.user == current_user.id)
    if not order:
        if price>0:
            return render_template('orders/checkout.html', price=price, client_token=client_token)   
        else:
            order = Order(order_customer_id=randrange(10), user=current_user.id, order_date=datetime.datetime.today(), status='preparation', is_open=True)
            if order.save():
                sess = session['cart']
                size = session['size']
                count = 0
                for s in sess:
                    order_size = size[count]
                   
                    order_outfit = Order_Outfit(order=order.id, outfit=s, size=order_size)
                    order_outfit.save()
                    si = Size.get(Size.outfit_id == s)
                    if order_size == 'size_xs':
                        si_old = int(si.size_xs)
                        si_new = si_old-1
                        si.size_xs=si_new
                    if order_size == 'size_s':
                        si_old = int(si.size_s)
                        si_new = si_old-1
                        si.size_s=si_new
                    if order_size == 'size_m':
                        si_old = int(si.size_m)
                        si_new = si_old-1
                        si.size_m=si_new
                    if order_size == 'size_l':
                        si_old = int(si.size_l)
                        si_new = si_old-1
                        si.size_l=si_new
                    if order_size == 'size_xl':
                        si_old = int(si.size_xl)   
                        si_new = si_old-1
                        si.size_xl=si_new 
                    si.save()
                    count = count+1

                session.pop("cart", None)   
                session.pop("size", None)  

                flash('Bedankt voor je bestelling')
                return redirect(url_for('home'))

            else:
                flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
                return redirect(url_for('home'))
    else:            
        flash('Je hebt al een bestelling. Contacteer ons om je bestelling te wijzigen.')    
        return redirect(url_for('home'))

@orders_blueprint.route('/orders/create_checkout/', methods=['POST', 'GET'])
@login_required
def create_checkout():
    
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
            size = session['size']
            count = 0
            for s in sess:
                order_size = size[count]
                
                order_outfit = Order_Outfit(order=order.id, outfit=s, size=order_size)
                order_outfit.save()
                si = Size.get(Size.outfit_id == s)
                if order_size == 'size_xs':
                    si_old = int(si.size_xs)
                    si_new = si_old-1
                    si.size_xs=si_new
                if order_size == 'size_s':
                    si_old = int(si.size_s)
                    si_new = si_old-1
                    si.size_s=si_new
                if order_size == 'size_m':
                    si_old = int(si.size_m)
                    si_new = si_old-1
                    si.size_m=si_new
                if order_size == 'size_l':
                    si_old = int(si.size_l)
                    si_new = si_old-1
                    si.size_l=si_new
                if order_size == 'size_xl':
                    si_old = int(si.size_xl)   
                    si_new = si_old-1
                    si.size_xl=si_new         
               
                si.save()
                count = count+1

            session.pop("cart", None)   
            session.pop("size", None) 
                 
            flash('Bedankt voor je bestelling')
            return redirect(url_for('home'))
                

        else:
            flash("Something went wrong please try again")   
            return redirect(url_for('home'))    
        
    else:
        for x in result.errors.deep_errors:
            flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('home'))

    

   