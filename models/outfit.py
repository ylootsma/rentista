
from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Outfit (BaseModel):
    owner = pw.ForeignKeyField(User, backref="outfits")
    brand_name = pw.CharField(unique=False, default="default")
    Apparell_type = pw.CharField(unique=False, default="default")
    description = pw.CharField(unique=False, default="default")
    size = pw.CharField(unique=False, default="default")
    in_stock = pw.BooleanField(unique=False, default="default")
    enter_stock_date = pw.DateField(default="01/01/01")
    state = pw.CharField(unique=False, default="new")
    pricing_type = pw.CharField(unique=False, default="standard")
    items = pw.IntegerField(unique=False, default="0")
    add_on_percentage = pw.IntegerField(unique=False, default="0")
    buying_price = pw.DecimalField(unique=False, default="0")
    occassion = pw.Charfield(unique=False, default="default")
    style = pw.CharField(unique=False, default="default")
    look = pw.CharField(unique=False, default="default")
    # trendy_timeless_matrix = pw.IntegerField(unique=False, default="0")
