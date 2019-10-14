import os
import config
from authlib.flask.client import OAuth
from flask import Flask, jsonify


oauth = OAuth()

oauth.register('google',
               client_id=os.getenv('Google_Client_ID'),
               client_secret=os.getenv('Google_Client_secret'),
               access_token_url='https://accounts.google.com/o/oauth2/token',
               access_token_params=None,
               refresh_token_url=None,
               authorize_url='https://accounts.google.com/o/oauth2/auth',
               api_base_url='https://www.googleapis.com/oauth2/v1/',
               client_kwargs={
                   'scope': ('https://www.googleapis.com/auth/userinfo.profile',
                             'https://www.googleapis.com/auth/userinfo.email'),
                   'token_endpoint_auth_method': 'client_secret_basic',
                   'token_placement': 'header',
                   'prompt': 'consent'
               }
               )

oauth.register(name="facebook",
               client_id=os.getenv('Facebook_App_ID'),
               client_secret=os.getenv('Facebook_App_Secret'),
               request_token_url=None,
               request_token_params=None,
               access_token_url="https://graph.facebook.com/v2.10/oauth/access_token",
               access_token_params=None,
               refresh_token_url="https://graph.facebook.com/v2.10/oauth/refresh_token",
               authorize_url="https://www.facebook.com/v2.10/dialog/oauth",
               api_base_url="https://graph.facebook.com/v2.10",
               client_kwargs={"scope": "email"}
               )
