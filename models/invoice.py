from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Invoice(BaseModel):
    user = pw.ForeignKeyField(User)
    name = pw.CharField(unique=False, default="default")
    street = pw.CharField(unique=False, default="default")
    housenumber = pw.CharField(unique=False, default="default")
    postal = pw.CharField(unique=False, default="default")
    city = pw.CharField(unique=False, default="default")
    country = pw.CharField(unique=False, default="default")
    phone = pw.CharField(unique=False, default="00000")
   