# Rentista

Clothing rental webshop built with Flask, Peewee and PostgreSQL. Payments run through Braintree, product photos are stored on S3 and emails are sent with Mailgun.

## Development

**Install dependencies** (Python 3.13 and PostgreSQL)

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Create a `.env` file**

Copy `.env.example` to `.env` and fill in the values. `SECRET_KEY` and `DATABASE_URL` are required; the other keys are needed for payments, emails, photo uploads and social login.

When running commands using `flask`, environment variables from `.env` are loaded automatically. `python migrate.py` loads them itself.

**Create a Database**

- this application is configured to use Postgresql

```
createdb rentista_dev
```

_\*if you name your database something else, tweak the settings in `.env`_

**Ignoring Files from Git**

Before git commiting, remember to ignore key files. Here's an example of `.gitignore`

```
.vscode
*.DS_Store
*__pycache__
*.env
```

---

## Database Migrations

```
python migrate.py
```

\*_this template is configured to use Peewee's PooledConnection, however, migrations using Peewee-DB-Evolve doesn't work well. A hack was used to not use PooledConnection when running migration. Pending investigation. There are no known side effects to run this template in production._

## Starting Server

```
flask run
```

## Starting Shell

```
flask shell
```

---

## Deploying to Production

- ensure environment variables are configured appropriately (see `.env.example`); set `BRAINTREE_ENVIRONMENT=production` to take real payments
- the `Procfile` starts the site with gunicorn
- migrations will not run in interactive mode when FLASK_ENV is set to 'production'
- It's important to set your own `SECRET_KEY` environment variable and keep that private.

---

## Architecture

This template separates out API and Web to separate packages. Both API and Web are configured to use Flask's Blueprints.

All new models should go into it's own file/script within the models directory.

The entry point for a Flask server to start is located at `start.py`

---

## Dependencies

This template was created against `Python 3.7`. Should work with newer versions of Python. Not tested with older versions.

`Peewee` is used as ORM along with a database migration library `peewee-db-evolve`.

This template also comes packaged with Bootstrap 4.1.3 and it's dependencies (jQuery).

A copy of requirements.txt is included in the repository.

```
autopep8==1.4.3
certifi==2018.11.29
Click==7.0
colorama==0.4.1
Flask==1.0.2
Flask-Cors==3.0.7
itsdangerous==1.1.0
Jinja2==2.10
MarkupSafe==1.1.0
peewee==3.8.2
peewee-db-evolve==3.7.0
psycopg2-binary==2.7.7
pycodestyle==2.5.0
python-dotenv==0.10.1
six==1.12.0
Werkzeug==0.14.1
```

Remove `certifi==2018.11.29` if you're having trouble installing dependencies.
