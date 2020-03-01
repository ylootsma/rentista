from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
from models.subscription import Subscription
from models.outfit_picture import Outfit_Picture
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from rentista_web.util.oauth import oauth
from app import app
import boto3
import math
from rentista_web.util.helpers import *
from playhouse.flask_utils import FlaskDB, object_list
from peewee import *
from database import *

orders_blueprint = Blueprint('orders',
                              __name__,
                              template_folder='templates')


@orders_blueprint.route('/new/<price>/', methods=['POST', 'GET'])
@login_required
def new(price):
    price=price
    return render_template('orders/new.html', price=price)

@orders_blueprint.route('/create/<price>/', methods=['POST', 'GET'])
@login_required
def create(price):
    price=price
    name = request.form.get('name')
    street = request.form.get('street')
    housenumber = request.form.get('housenumber')
    postal = request.form.get('postal')
    city = request.form.get('city')
    country = request.form.get('country')
    phone = request.form.get('phone')

    adress = Adress(user_id=current_user.id, name=name, street=street, housenumber=housenumber, postal=postal, city=city, country=country, phone=phone)
    if adress.save:
        return render_template('orders/new.html')    
