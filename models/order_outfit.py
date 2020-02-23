from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit
from models.order import Order


class Order_Outfit(BaseModel):
    order = pw.ForeignKeyField(Order, backref='outfits')
    outfit = pw.ForeignKeyField(Outfit, backref='orders')