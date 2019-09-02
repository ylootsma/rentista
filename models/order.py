from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit
from models.user import User


class Order(BaseModel):
    order_id = pw.IntegerField
    outfit_id = pw.ForeignKeyField(Outfit, backref='orders')
    user_id = pw.ForeignKeyField(User, backref='orders')
    order_date = pw.DateField(unique=False)
    status = pw.CharField(unique=False)
    is_open = pw.BooleanField(unique=False)
