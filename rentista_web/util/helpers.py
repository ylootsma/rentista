from functools import wraps
from urllib.parse import urlparse
from flask import request, url_for, flash, redirect
from flask_login import current_user
import boto3
import botocore
import requests
from config import Config
from werkzeug.utils import secure_filename
import os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY')
)


def upload_file_to_s3(file, bucket_name, acl="public-read"):
    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "Success"


def _is_safe_target(target):
    # Only redirect to pages on this site, and never back to the login pages
    parsed = urlparse(target)
    if parsed.netloc and parsed.netloc != request.host:
        return False
    return not parsed.path.startswith('/sessions/')


def redirect_url(default='home'):
    for target in (request.args.get('next'), request.referrer):
        if target and _is_safe_target(target):
            return target
    return url_for(default)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.Admin:
            flash('Sorry, je hebt geen toegang')
            return redirect(url_for('home'))
        return view(*args, **kwargs)
    return wrapped


def send_email(to, subject, text):
    """Send an email through Mailgun. Never raises: a failed email must not break checkout."""
    domain = os.getenv('MAILGUN_DOMAIN')
    if not Config.mailgun or not domain:
        print("Mailgun not configured, email not sent:", subject)
        return False
    try:
        response = requests.post(
            f"https://api.eu.mailgun.net/v3/{domain}/messages",
            auth=("api", Config.mailgun),
            data={"from": f"Rentista <rentista@{domain}>",
                  "to": [to],
                  "subject": subject,
                  "text": text},
            timeout=10)
        return response.ok
    except requests.RequestException as e:
        print("Sending email failed: ", e)
        return False
