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


def generate_client_token(client_token):
    return gateway.client_token.generate(client_token)


def transact(options):
    return gateway.transaction.sale(options)


def find_transaction(id):
    return gateway.transaction.find(id)


def create_customer(customer):
    return gateway.customer.create(customer)


def subscription_create(subscription):
    return gateway.subscription.create(subscription)
