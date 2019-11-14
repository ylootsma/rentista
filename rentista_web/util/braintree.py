import braintree
from config import Config

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id=Config.merchant_id,
        public_key=Config.public_key,
        private_key=Config.private_key
    )
)


def generate_client_token():
    return gateway.client_token.generate()


def transact():
    return gateway.transaction.sale()


def find_transaction():
    return gateway.transaction.find()


def create_customer():
    return gateway.customer.create()


def subscription_create():
    return gateway.subscription.create()
