from models.base_model import BaseModel
import peewee as pw
from models.outfit import Outfit


class Picture(BaseModel):
    outfit = pw.ForeignKeyField(Outfit, unique=True, backref='pictures')
    main_pic = pw.TextField(unique=True, null=True)
    set_pic = pw.TextField(unique=False, null=True)
    additional_pic1 = pw.TextField(unique=True, null=True)
    additional_pic2 = pw.TextField(unique=True, null=True)
    additional_pic3 = pw.TextField(unique=True, null=True)
    additional_pic4 = pw.TextField(unique=True, null=True)
    additional_pic5 = pw.TextField(unique=True, null=True)
