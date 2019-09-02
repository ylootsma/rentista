
from models.base_model import BaseModel
import peewee as pw


class Inspiration(BaseModel):
    as_seen_on = pw.BooleanField(unique=False, default=False)
    picture = pw.BlobField(unique=False, null=True)
    name = pw.CharField(unique=False, null=True)
    description = pw.CharField(unique=False, null=True)
    source = pw.TextField(unique=False, null=True)
