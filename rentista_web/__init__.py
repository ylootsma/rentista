from app import app
from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session
from rentista_web.blueprints.users.views import users_blueprint
from rentista_web.blueprints.sessions.views import sessions_blueprint
from rentista_web.blueprints.outfits.views import outfits_blueprint
from rentista_web.blueprints.subscriptions.views import subscriptions_blueprint
from rentista_web.blueprints.orders.views import orders_blueprint
from flask_assets import Environment, Bundle
from .util.assets import bundles
from rentista_web.util.oauth import oauth
from flask_login import login_required, current_user, login_user
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from models.outfit import Outfit
from models.outfit_picture import Outfit_Picture
from models.subscription import Subscription
import os
import config
from rentista_web.util.pricing import PLAN_BY_PRICE
from rentista_web.blueprints.subscriptions.views import confirm_page



oauth.init_app(app)


assets = Environment(app)
assets.register(bundles)

app.register_blueprint(users_blueprint, url_prefix="/users")
app.register_blueprint(sessions_blueprint, url_prefix="/sessions")
app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
app.register_blueprint(subscriptions_blueprint, url_prefix="/subscriptions")
app.register_blueprint(orders_blueprint, url_prefix="/orders")


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route("/")
def home():
    pictures = Outfit_Picture.select().where(Outfit_Picture.outfit == 78)

    return render_template('home.html', pictures=pictures)


def _plan_from_form():
    try:
        return PLAN_BY_PRICE[int(request.form.get('price', ''))]
    except (KeyError, ValueError):
        return 3


@app.route('/new_1', methods=['POST', 'GET'])
def new_1():
    return confirm_page(_plan_from_form())


@app.route('/new_2', methods=['POST', 'GET'])
def new_2():
    return confirm_page(_plan_from_form())
