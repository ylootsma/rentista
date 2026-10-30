import os


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or os.urandom(32)
    # Mollie payments: test_... key while testing, live_... key in production
    MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY")
    # Public address of the site, used for Mollie webhooks, e.g. https://www.rentista.nl
    BASE_URL = os.environ.get("BASE_URL")
    mailgun = os.environ.get("MAILGUN_API_KEY")


class ProductionConfig(Config):
    DEBUG = False
    ASSETS_DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = False
    DEBUG = False
    ASSETS_DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    ASSETS_DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    ASSETS_DEBUG = True
