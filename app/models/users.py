from enum import StrEnum
from tortoise import fields, models


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class User(models.Model):
    id = fields.BigIntField(primary_key=True)
    email = fields.CharField(max_length=40)
    hashed_password = fields.CharField(max_length=128)
    name = fields.CharField(max_length=20)
    gender = fields.CharEnumField(enum_type=Gender)
    birth_date = fields.DateField()
    phone_number = fields.CharField(max_length=11)
    is_active = fields.BooleanField(default=True)
    is_admin = fields.BooleanField(default=False)
    is_email_verified = fields.BooleanField(default=False)
    email_verify_token = fields.CharField(max_length=64, null=True)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    height_cm = fields.FloatField(null=True)
    weight_kg = fields.FloatField(null=True)
    oauth_provider = fields.CharField(max_length=20, null=True)
    oauth_id = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "users"