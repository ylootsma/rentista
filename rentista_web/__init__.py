from app import app
from flask import render_template, flash
from rentista_web.blueprints.users.views import users_blueprint
from rentista_web.blueprints.sessions.views import sessions_blueprint
from rentista_web.blueprints.outfits.views import outfits_blueprint
from rentista_web.blueprints.subscriptions.views import subscriptions_blueprint
from flask_assets import Environment, Bundle
from .util.assets import bundles
from rentista_web.util.oauth import oauth
from flask_login import login_required, current_user, login_user
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from models.outfit import Outfit
import os
import config


oauth.init_app(app)


assets = Environment(app)
assets.register(bundles)

app.register_blueprint(users_blueprint, url_prefix="/users")
app.register_blueprint(sessions_blueprint, url_prefix="/sessions")
app.register_blueprint(outfits_blueprint, url_prefix="/outfits")
app.register_blueprint(subscriptions_blueprint, url_prefix="/subscriptions")


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route("/")
def home():
    outfits = Outfit.select()
    outfit_length = len(outfits)

    return object_list('home.html', outfits, paginate_by=6, outfit_length=outfit_length)
