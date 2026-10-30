from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Subscription(BaseModel):
    # subscription_reference = pw.IntegerField(unique=True)
    user = pw.ForeignKeyField(User, backref="clients")
    subscription_type = pw.CharField(unique=False, default=3)
    subscription_price = pw.DecimalField(unique=False, default=93)
    subscription_active = pw.BooleanField(unique=False, default=False)
    mollie_payment_id = pw.CharField(unique=False, null=True)
    mollie_subscription_id = pw.CharField(unique=False, null=True)
