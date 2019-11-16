from models.base_model import BaseModel
import peewee as pw
from models.user import User


class Partner(BaseModel):
    website = pw.CharField(unique=False, default="default")
    business_name = pw.CharField(unique=False, default="default")
    business_adress_street = pw.CharField(unique=False, default="default")
    business_adress_streetnr = pw.FloatField(unique=False, default="0")
    business_adress_pc = pw.FloatField(unique=False, default="0")
    business_adress_country = pw.CharField(unique=False, default="default")
    partnership_active = pw.BooleanField(unique=False, default="default")
    business_number = pw.FloatField(unique=False, default="0")
    activation_date = pw.DateField(unique=False, null=True)
    # signed_contract = pw.BlobField(null=True)
    contract_start = pw.DateField(null=True)
    contract_end = pw.DateField(null=True)
    business_type = pw.CharField(unique=False, default="default")
    # retail(webshop, offline, mixxed), wholesale or designer/brand
    average_price_b2b = pw.DecimalField(unique=False, default=0)
    average_price_retail = pw.DecimalField(unique=False, default=0)
    total_items = pw.DecimalField(unique=False, default=0)
    # affiliate_brand = pw.BooleanField(unique=False, default=False)
    user = pw.ForeignKeyField(User, backref="partners")
