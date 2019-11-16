from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models.outfit import Outfit
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
    return object_list('outfits/show.html', outfits, paginate_by=9)


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
    pricing_type = request.form.get('pricing')
    add_on_percentage = request.form.get('add_on')
    retail_price = request.form.get('retail_price')
    occassion = request.form.get('occassion')
    state = request.form.get('state')

    outfit = Outfit(owner=current_user.id, brand_name=brand_name, apparell_type=apparell_type, outfit_name=outfit_name,
                    size_xs=size_xs, size_s=size_s, size_m=size_m, size_l=size_l, size_xl=size_xl, in_stock=True, enter_stock_date=enter_stock_date, state=state, pricing_type=pricing_type, add_on_percentage=add_on_percentage, retail_price=retail_price, occassion=occassion, approved=False, profile_pic="default")

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
