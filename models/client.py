from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Client(BaseModel):
    client_id = pw.DecimalField(unique=False, default="0")
    bottom_size = pw.CharField(unique=False, default="default")
    top_size = pw.CharField(unique=False, default="default")
    user = pw.ForeignKeyField(User, backref="clients")
    subscription_active = pw.BooleanField(default="false")
    subscription_type = pw.CharField(unique=False, default="none")
    DOB = pw.DateField(unique=False, default="01/01/01")
    sex = pw.CharField(unique=False, default="female")
