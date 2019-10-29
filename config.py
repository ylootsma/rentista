import os


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or os.urandom(32)
    merchant_id = os.environ.get("Merchant_ID")
    public_key = os.environ.get("Public_Key")
    private_key = os.environ.get("Private_Key")


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
