from models.base_model import BaseModel
import peewee as pw


class User(BaseModel):
    name = pw.CharField(unique=False, default="default")
    email = pw.CharField(unique=True, default="default")
    password = pw.CharField(unique=False, default="default")
    Admin = pw.BooleanField(unique=False, default=False)
    Client = pw.BooleanField(unique=False, default=True)
    Partner = pw.BooleanField(unique=False, default=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True
