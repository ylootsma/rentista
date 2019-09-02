from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit


class Combination(BaseModel):
    main_item = pw.ForeignKeyField(Outfit, backref='combo_items')
    combo_item = pw.ForeignKeyField(Outfit, backref='main_items')
    is_set = pw.BooleanField(unique=False, default=False)
    set_fee = pw.DecimalField(unique=False, default=0)
