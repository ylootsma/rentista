from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session, request
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from models.adress import Adress
# from werkzeug.utils import secure_filename
import datetime
from flask_login import login_required, current_user, login_user, login_manager
from rentista_web.util.oauth import oauth
from rentista_web.util.helpers import *
from app import app


users_blueprint = Blueprint('users',
                            __name__,
                            template_folder='templates')


# @users_blueprint.route('/new', methods=['GET'])
# def new():
#     pass


@users_blueprint.route('/create', methods=['POST'])
def create():
    name = request.form.get("name")
    email = request.form.get('email')
    password = request.form.get('password')
    pwd = generate_password_hash(password)

    user = User(name=name, email=email,
                password=pwd)
    if user.save():
        flash("Bedankt voor je aanmelding")
        return redirect(redirect_url())

    else:
        flash("Er is iets fout gegaan, probeer het opnieuw")
        return redirect(redirect_url())


@users_blueprint.route('/admin', methods=['POST'])
@login_required
def admin():
    user = User.get_by_id(current_user.id)
    if user.Admin == True:
       return render_template('users/admin.html', user=user)

    else:
        flash('Sorry, je hebt geen toegang')
        return redirect(redirect_url())

@users_blueprint.route('/show', methods=['GET'])
@login_required
def show():
    user = User.get_by_id(current_user.id)
    adress = Adress.get_or_none(Adress.user==user.id)
    if adress:
        ad = True

    return render_template('users/show.html', user=user, ad=ad, adress=adress)

 





# @users_blueprint.route('/google', methods=["GET"])
# def google():
#     redirect_uri = "http://localhost:5000/users/google/login"
#     return oauth.google.authorize_redirect(redirect_uri)


# @users_blueprint.route('/google/login', methods=["GET"])
# def google_login():
#     token = oauth.google.authorize_access_token()
#     profile = oauth.google.get(
#         'https://www.googleapis.com/oauth2/v2/userinfo').json()
#     name = profile['name']
#     email = oauth.google.get(
#         'https://www.googleapis.com/oauth2/v2/userinfo').json()['email']
#     user = User.get_or_none(User.email == email)
#     if user == None:
#         user = User(name=name, email=email)
#         if user.save():
#             login_user(user)
#             flash('succesfully signed-up')
#             return redirect(url_for('home'))
#         else:
#             flash('something went wrong, please try again', 'danger')
#             return redirect(url_for('home'))
#     else:
#         login_user(user)
#         flash('Welcome, successfully signed in.')
#         return redirect(url_for('home', id=user.id))


@users_blueprint.route('/facebook', methods=["GET"])
def facebook():
    redirect_uri = "https://localhost:5000/users/facebook/login"
    return oauth.facebook.authorize_redirect(redirect_uri, state=session['csrf_token'])


@users_blueprint.route('/facebook/login', methods=["GET"])
def facebook_login():
    token = oauth.facebook.authorize_access_token()
    facebook_id = oauth.facebook.get(
        "https://graph.facebook.com/v3.2/me").json()["id"]

    user_data = oauth.facebook.get(
        f"https://graph.facebook.com/v3.2/{facebook_id}?fields=id,name,email").json()
    email = user_data['email']
    name = user_data['name']

    user = User.get_or_none(User.email == email)
    if user == None:
        user = User(name=name, email=email)
        if user.save():
            flash('succesfully signed-up')
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('something went wrong, please try again', 'danger')
            return redirect(redirect_url())
    else:
        login_user(user)
        flash('Welcome, successfully signed in.')
        return redirect(url_for('home', id=user.id))
