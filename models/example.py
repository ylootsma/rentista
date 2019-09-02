from models.base_model import BaseModel
import peewee as pw
from models.inspiration import Inspiration
from models.outfit import Outfit


class Example(BaseModel):
    inspiration = pw.ForeignKeyField(Inspiration, backref='outfits')
    outfit = pw.ForeignKeyField(Outfit, backref='inspirations')
