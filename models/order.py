from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit
from models.user import User


class Order(BaseModel):
    order_customer_id = pw.IntegerField(unique=False)
    order_date = pw.DateField(unique=False)
    status = pw.CharField(unique=False)
    is_open = pw.BooleanField(unique=False)
    user = pw.ForeignKeyField(User, backref='orders')

     
