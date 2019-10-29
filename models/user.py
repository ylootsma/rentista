from models.base_model import BaseModel
import peewee as pw


class User(BaseModel):
    # user_reference = pw.IntegerField(unique=True)
    name = pw.CharField(unique=False, default="default")
    email = pw.CharField(unique=True, default="default")
    password = pw.CharField(unique=False, default="default")
    Admin = pw.BooleanField(unique=False, default=False)
    Partner = pw.BooleanField(unique=False, default=False)
    DOB = pw.DateField(unique=False, default="01/01/01")
    bottom_size = pw.CharField(unique=False, default="default")
    top_size = pw.CharField(unique=False, default="default")

    def is_authenticated(self):
        return True

    def is_active(self):
        return True
