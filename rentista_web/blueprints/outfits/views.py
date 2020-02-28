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


outfits_blueprint = Blueprint('outfits',
                              __name__,
                              template_folder='templates')


@outfits_blueprint.route('/new', methods=['POST', 'GET'])
@login_required
def new():
    return render_template('outfits/new.html')


@outfits_blueprint.route('/show/')
def show():
    outfits = Outfit.select()
    out= Outfit.select()
    outfits_cart = Outfit.select().order_by(Outfit.outfit_price.desc()) 
    subscription = None
    amount = 0
    # outfits = []
    discount = 0
    # user = None
    surplus = []
    sub = []
    sess = []
    if 'cart' in session:
        sess =  session['cart']  
        if current_user.is_authenticated:
            # user= User.select().where(User.id == current_user.id)
            subscription = Subscription.get_or_none(Subscription.user == current_user.id)
            if subscription:
                
                sub_length = int(subscription.subscription_type) 
                
                if len(sess) > sub_length:
                    sess2 = len(sess) - sub_length    
                    count =0
                    for item in outfits_cart:
                        if count<sess2:
                            if item.id in sess:
                                amount = amount + item.outfit_price
                                if item.id not in surplus:
                                    surplus.append(item.id) 
                                count += 1    
                        else:
                            break                                                          
                                    
                if len(sess) > (sub_length+1):
                    sess2 = len(sess) - (sub_length+1)
                    count = 0
                    for item in outfits_cart:
                        if count < sess2:
                            if item.id in sess:
                                price = float(item.outfit_price)
                                discount = discount + price*0.35
                                count = count+1 
                        else:
                            break

                if len(surplus) > 0:
                    for s in sess:
                        if s not in surplus:
                            sub.append(s) 
                   
                else:
                    for s in sess:
                        sub.append(s)                               
        else:
            count = 0
            for s in sess:
                item = Outfit.get(Outfit.id == s).outfit_price
                amount = amount + item
                item = float(item)
                # outfits.append(outfit)
                if count>0:
                    discount= discount + item*0.33   
                count= count+1                 
            
    
    return object_list('outfits/show.html', outfits, out=out, sub=sub, subscription=subscription, surplus=surplus, discount=discount, amount=amount, sess=sess,paginate_by=9)


@outfits_blueprint.route('/<id>/detail')
def detail(id):
    pictures = Outfit_Picture.select().where(Outfit_Picture.outfit == id)
    outfit = Outfit.select().where(Outfit.id == id)

    return render_template('outfits/detail.html', pictures=pictures, outfit=outfit)


@outfits_blueprint.route('/create', methods=['POST', 'GET'])
def create():
    outfit_name = request.form.get('outfit_name')
    brand_name = request.form.get('brand_name')
    apparell_type = request.form.get('apparell_type')
    size_xs = request.form.get('size_xs')
    size_s = request.form.get('size_s')
    size_m = request.form.get('size_m')
    size_l = request.form.get('size_l')
    size_xl = request.form.get('size_xl')
    enter_stock_date = request.form.get('enter_stock')
    outfit_price = request.form.get('outfit_price')
    retail_price = request.form.get('retail_price')
    state = request.form.get('state')
    style_matrix = request.form.get('trend_matrix')

    outfit = Outfit(owner=current_user.id, brand_name=brand_name, apparell_type=apparell_type, outfit_name=outfit_name,
                    size_xs=size_xs, size_s=size_s, size_m=size_m, size_l=size_l, size_xl=size_xl, in_stock=True, enter_stock_date=enter_stock_date, state=state, outfit_price=outfit_price, retail_price=retail_price, profile_pic="default", style_matrix=style_matrix)

    if outfit.save():
        flash("outfit stored succesfully")
    else:
        flash("outfit not saved, please try again")

    files = request.files.getlist("pic_link")

    if 'pic_link' not in request.files:
        return "No user_file key in request.files"

    x = 0
    y = 0
    for file in files:
        y = y+1

        file.filename = secure_filename(file.filename)
        output = upload_file_to_s3(file, os.getenv("S3_BUCKET_NAME"))
        link = (
            f"https://rentista.s3.us-east-2.amazonaws.com/{file.filename}")

        pic = Outfit_Picture(outfit=outfit.id,
                             picture=link,
                             )
        if pic.save():
            x = x+1
            # pic = Outfit_Picture(outfit=outfit.id,
            #                      picture=link,
            #                      )
        if x == 2:
            outfit.profile_pic = link
            outfit.save()

        if x == len(files):
            if x == y:
                flash("all pictures uploaded succesfully")
            else:
                z = y - x
                flash(f"{z}pictures uploaded succesfully")
    return redirect(url_for('outfits.show'))

    # if pic.save():
    #     flash("upload succesfull")
    #     return redirect(url_for('outfits.show')
    # else:
    #     flash("pic failed to save")

@outfits_blueprint.route("/add_to_cart/<outfit>")
def add_to_cart(outfit):
    # outfits = Outfit.select()
    outfit = int(outfit) 
    if 'cart' not in session:
        session['cart'] = []
    if outfit not in session['cart']:   
        session['cart'].append(outfit)
        flash("added to cart")
    # sess =  session['cart']  
    # subscription = None
    # amount = 0
    # # outfits = []
    # discount = 0
    # # user = None
    # surplus = []
    # sub = []
    # if current_user.is_authenticated:
    #     # user= User.select().where(User.id == current_user.id)
    #     subscription = Subscription.get_or_none(Subscription.user == current_user.id)
    #     if not subscription:
    #         for s in sess:
    #             item = Outfit.select().where(Outfit.id == s)
    #             item = amount + item.outfit_price
    #         # outfits.append(outfit)
    #             if len(sess)>1:
    #                 discount= discount + (item.outfit_price*0.35)    
    #     else:  
    #         outfits_cart = Outfit.select().order_by(Outfit.outfit_price.desc()) 
    #         if len(sess) > subscription.subscription_type:
    #             sess2 = len(sess) - subscription.subscription_type + 1
    #             s= 0
    #             while s < sess2:
    #                 for item in outfits_cart:
    #                     if item.id in sess:
    #                         amount = amount + item.outfit_price
    #                         surplus.append(s)
    #                         s = s+1        
    #         if len(sess) > (subscription.subscription_type+1):
    #             sess2 = len(sess) - subscription.subscription_type + 1
    #             s= 0
    #             while s < sess2:
    #                 for item in outfits_cart:
    #                     if item.id in sess:
    #                         discount = discount + item.outfit_price*35
    #                         surplus.append(s)
    #                         s = s+1       
    #         if surplus > 0:
    #             for s in sess:
    #                 if s not in surplus:
    #                     sub.append(s) 
    #         else:
    #             for s in sess:
    #                 sub.append(s)                               
    # else:
    #     count = 0
    #     for s in sess:
    #         item = Outfit.get(Outfit.id == s).outfit_price
    #         amount = amount + item
    #         item = float(item)
    #         # outfits.append(outfit)
    #         if count>0:
    #             discount= discount + item*0.33   
    #         count= count+1                 
            
      
   
    return redirect(url_for('outfits.show'))



# @outfits_blueprint.route("/checkout/<id>")
# def checkout(id):
#     subscription = None
#     amount = 0
#     outfits = []
#     discount = 0
#     sess = id
#     user= User.select().where(User.id == current_user.id)
#     # if current_user.is_authenticated: # ask user to create an account before sign-up
#         if user.subscription != None:
#             subscription = Subscription.select().where(Subscription.user == current_user.id)
#             count = 0
#             for s in sess:
#                 outfit = c # order by
#                 outfits.append(outfit)
#                 if count >= (subscription.subscription_type):
#                     amount = amount + outfit.out_price
#                 if count >= (subscription.subscription_type+1):
#                     discount = discount + (outfit.outfit_price*0.33)
#                 count = count+1                  
#         else:             
#             for s in sess:
#                 outfit = Outfit.select().where(Outfit.id == s)
#                 amount = amount + outfit.outfit_price
#                 outfits.append(outfit)
#                 if len(sess)>1:
#                     discount= discount + (outfit.outfit_price*0.33)

#     breakpoint()
#     return object_list('outfits/show.html', outfits, paginate_by=9)     
   