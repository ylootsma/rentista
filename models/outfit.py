
from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Outfit (BaseModel):
    owner = pw.ForeignKeyField(User, backref="outfits")
    outfit_name = pw.CharField(default="default")
    brand_name = pw.CharField(unique=False, default="default")
    apparell_type = pw.CharField(unique=False, default="default")
    size_xs = pw.IntegerField(unique=False, default=0)
    size_s = pw.IntegerField(unique=False, default=0)
    size_m = pw.IntegerField(unique=False, default=0)
    size_l = pw.IntegerField(unique=False, default=0)
    size_xl = pw.IntegerField(unique=False, default=0)
    in_stock = pw.BooleanField(unique=False, default=True)
    enter_stock_date = pw.DateField(default="01/01/01")
    state = pw.CharField(unique=False, default="new")
    retail_price = pw.DecimalField(unique=False, default=150)
    # purchase_price = pw.DecimalField(unique=False, default=0)
    profile_pic = pw.TextField(unique=True, null=True)
    style_matrix = pw.IntegerField(unique=False, default=5)
    outfit_price = pw.DecimalField(unique=False, default=50)
    