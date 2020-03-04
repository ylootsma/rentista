from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit


class Size (BaseModel):
    outfit = pw.ForeignKeyField(Outfit, backref="sizes")
    size_xs = pw.IntegerField(unique=False, default=0)
    size_s = pw.IntegerField(unique=False, default=1)
    size_m = pw.IntegerField(unique=False, default=1)
    size_l = pw.IntegerField(unique=False, default=1)
    size_xl = pw.IntegerField(unique=False, default=0)
   