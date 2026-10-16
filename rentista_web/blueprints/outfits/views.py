from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
from models.subscription import Subscription
from models.outfit_picture import Outfit_Picture
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
from rentista_web.util.shop import cart_summary, in_stock, SIZES


outfits_blueprint = Blueprint('outfits',
                              __name__,
                              template_folder='templates')


@outfits_blueprint.route('/new', methods=['POST', 'GET'])
@admin_required
def new():
    return render_template('outfits/new.html')


@outfits_blueprint.route('/remove/<int:outfit>/')
def remove(outfit):
    cart = session.get('cart', [])
    if outfit in cart:
        index = cart.index(outfit)
        del session['size'][index]
        del session['cart'][index]
        session.modified = True
    return redirect(url_for('outfits.show'))


def _user_flags():
    admin = False
    authentic = current_user.is_authenticated
    if authentic:
        admin = current_user.Admin == True
    return admin, authentic


@outfits_blueprint.route('/show/')
def show():
    admin, authentic = _user_flags()
    outfits = Outfit.select().order_by(Outfit.id)
    size = Size.select()
    out = Outfit.select()
    summary = cart_summary(current_user if authentic else None)
    return object_list('outfits/show.html', outfits, admin=admin, authentic=authentic, size=size, out=out, paginate_by=9, **summary)


@outfits_blueprint.route('/<int:id>/detail')
def detail(id):
    pictures = Outfit_Picture.select().where(Outfit_Picture.outfit == id)
    outfit = Outfit.select().where(Outfit.id == id)
    if not outfit.exists():
        abort(404)
    size = Size.select().where(Size.outfit == id)
    admin, authentic = _user_flags()
    out = Outfit.select()
    summary = cart_summary(current_user if authentic else None)
    return render_template('outfits/detail.html', size=size, pictures=pictures, outfit=outfit, admin=admin, authentic=authentic, out=out, **summary)


@outfits_blueprint.route('/create', methods=['POST'])
@admin_required
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
    description = request.form.get('description')
    material = request.form.get('material')

    outfit = Outfit(description=description, material=material, owner=current_user.id, brand_name=brand_name, apparell_type=apparell_type, outfit_name=outfit_name,
                    in_stock=True, enter_stock_date=enter_stock_date, state=state, outfit_price=outfit_price, retail_price=retail_price, profile_pic="default", style_matrix=style_matrix)

    if outfit.save():
        size = Size(size_s=size_s, size_m=size_m, size_l=size_l, size_xl=size_xl, size_xs=size_xs,outfit=outfit.id)
        size.save()    

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

    

@outfits_blueprint.route("/add_to_cart/<int:outfit>/<size>/", methods=['POST', 'GET'])
def add_to_cart(outfit, size):
    if size not in SIZES or not in_stock(outfit, size):
        flash("Deze maat is niet op voorraad")
        return redirect(url_for('outfits.show'))
    if 'cart' not in session:
        session['cart'] = []
        session['size'] = []
    if outfit not in session['cart']:
        session['cart'].append(outfit)
        session['size'].append(size)
        session.modified = True
        flash("added to cart")
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
   