from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Subscription(BaseModel):
    # subscription_reference = pw.IntegerField(unique=True)
    user = pw.ForeignKeyField(User, backref="clients")
    subscription_active = pw.BooleanField(default="false")
    subscription_type = pw.CharField(unique=False, default="none")
