from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit


class Outfit_Picture(BaseModel):
    outfit = pw.ForeignKeyField(Outfit, backref='outfit_pictures')  
    picture = pw.TextField(unique=True, null=True)
