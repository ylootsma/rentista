from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from flask_login import login_user, current_user, LoginManager, logout_user, login_required
from rentista_web.util.oauth import oauth
from app import app


sessions_blueprint = Blueprint('sessions',
                               __name__,
                               template_folder='templates')


@sessions_blueprint.route('/new', methods=['GET'])
def new():
    return render_template('sessions/new.html')


@sessions_blueprint.route('/create', methods=['POST', 'GET'])
def create():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.get_or_none(User.email == email)
    if not user:
        flash('Email not valid', 'warning')
        return redirect(url_for('sessions.new'))

    if not check_password_hash(user.password, password):
        flash('Password invalid', 'danger')
        return redirect(url_for('sessions.new'))

    login_user(user)
    session["username"] = "username"
    flash('Welcome, successfully signed in.')
    return redirect(url_for('home'))

    # change to sessions last page visited


@sessions_blueprint.route('/google', methods=['GET'])
def google():
    redirect_uri = "http://localhost:5000/users/google/login"
    return oauth.google.authorize_redirect(redirect_uri)


@sessions_blueprint.route('/facebook', methods=['GET'])
def facebook():
    redirect_uri = "http://localhost:5000/users/facebook/login"
    return oauth.facebook.authorize_redirect(redirect_uri, state=session['csrf_token'])


@sessions_blueprint.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Logged out successfully')
    return redirect(url_for('home'))



