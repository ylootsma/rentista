from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
from models.subscription import Subscription
from models.outfit_picture import Outfit_Picture
from models.order_outfit import Order_Outfit
from models.order import Order
from models.adress import Adress
from models.user import User
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
import requests
import config


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



@orders_blueprint.route('/show/', methods=['POST', 'GET'])
@login_required
def show():
    user = User.get_by_id(current_user.id)
    orderstate = 0
    order_open = []
    order_closed = []
    orders = Order.select().where(Order.user == user)
    
    for order in orders:
        if order.is_open == True:
            order_info= []
            orderdate = order.order_date
            order_info.append(orderdate)

            order_outfit = Order_Outfit.get(Order_Outfit.order == order.id)
            outfitsize = order_outfit.size 
            order_info.append(outfitsize)

            outfit = Outfit.get(Outfit.id == order_outfit.outfit)
            outfitname = outfit.outfit_name
            order_info.append(outfitname)
            outfitbrand = outfit.brand_name
            order_info.append(outfitbrand)
            order_open.append(order_info)
        else:
            order_info = []
            orderdate = order.order_date
            order_info.append(orderdate)

            order_outfit = Order_Outfit.get(Order_Outfit.order == order.id)
            outfitsize = order_outfit.size 
            order_info.append(outfitsize)

            outfit = Outfit.get(Outfit.id == order_outfit.outfit)
            outfitname = outfit.outfit_name
            order_info.append(outfitname)
            outfitbrand = outfit.brand_name
            order_info.append(outfitbrand)
            order_closed.append(order_info)
            

    order_open_length=len(order_open)
    order_closed_length=len(order_closed)
    if order_open_length == 0 and order_closed_length == 0:
        orderstate = 0
    else:
        orderstate = 1    

    return render_template('orders/show.html', orderstate=orderstate, order_open=order_open, user=user, order_closed=order_closed, order_open_length=order_open_length, order_closed_length=order_closed_length)




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

                for s in sess:
                    si = Size.get(Size.outfit_id == s)
                    total= int(si.size_xs)+int(si.size_s)+int(si.size_m)+int(si.size_l)+int(si.size_xl)
             
                    if total < 1:
                        outfit = Outfit.get(Outfit.id==s)
                        outfit.in_stock = False
                        outfit.save()     

                session.pop("cart", None)   
                session.pop("size", None)  
                
                flash('Bedankt voor je bestelling')
                return redirect(url_for('orders.simple_message'))
                    

            else:
                flash('Er is iets fout gegaan. Probeer het opnieuw aub')    
                return redirect(url_for('home'))
    else:            
        flash('Je hebt al een bestelling. Contacteer ons om je bestelling te wijzigen.')    
        return redirect(url_for('home'))

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
       
            for s in sess:
                si = Size.get(Size.outfit_id == s)
                total= int(si.size_xs)+int(si.size_s)+int(si.size_m)+int(si.size_l)+int(si.size_xl)
                # breakpoint()
                if total < 1:
                    outfit = Outfit.get(Outfit.id==s)
                    outfit.in_stock = False
                    outfit.save()

            session.pop("cart", None)   
            session.pop("size", None) 
                 
            flash('Bedankt voor je bestelling')
            return redirect(url_for('orders.simple_message'))
                

        else:
            flash("Something went wrong please try again")   
            return redirect(url_for('home'))    
        
    else:
        for x in result.errors.deep_errors:
            flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('home'))

    

   