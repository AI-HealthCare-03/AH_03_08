from datetime import date, datetime
from typing import Any

from pydantic import EmailStr

from app.core import config
from app.models.users import Gender, User

ALLOWED_UPDATE_FIELDS = ["name", "phone_number", "gender", "birth_date"]
UPDATED_AT_FIELD = "updated_at"


class UserRepository:
    def __init__(self):
        self._model = User

    async def get_all(self):
        return await self._model.all()

    async def get_user(self, user_id: int) -> User | None:
        return await self._model.get_or_none(id=user_id)

    async def create_user(
        self,
        email: str | EmailStr,
        hashed_password: str,
        name: str,
        phone_number: str,
        gender: Gender,
        birth_date: date,
        *,
        height_cm: float | None = None,
        weight_kg: float | None = None,
        is_active: bool = True,
        is_admin: bool = False,
    ) -> User:
        return await self._model.create(
            email=email,
            hashed_password=hashed_password,
            name=name,
            phone_number=phone_number,
            gender=gender,
            birth_date=birth_date,
            height_cm=height_cm,
            weight_kg=weight_kg,
            is_active=is_active,
            is_admin=is_admin,
        )

    async def get_user_by_email(self, email: str) -> User | None:
        return await self._model.get_or_none(email=email)

    async def exists_by_email(self, email: str) -> bool:
        return await self._model.filter(email=email).exists()

    async def exists_by_phone_number(self, phone_number: str) -> bool:
        return await self._model.filter(phone_number=phone_number).exists()

    async def update_last_login(self, user_id: int) -> None:
        await self._model.filter(id=user_id).update(last_login=datetime.now(config.TIMEZONE))

    async def update_instance(self, user: User, data: dict[str, Any]) -> None:
        update_fields = []
        for key, value in data.items():
            if value is not None:
                setattr(user, key, value)
                update_fields.append(key)
        if update_fields:
            user.updated_at = datetime.now(config.TIMEZONE)
            update_fields.append(UPDATED_AT_FIELD)
            await user.save(update_fields=update_fields)

    async def get_user_by_oauth(self, oauth_provider: str, oauth_id: str) -> User | None:
        return await self._model.get_or_none(oauth_provider=oauth_provider, oauth_id=oauth_id)

    async def create_oauth_user(
        self,
        email: str,
        name: str,
        oauth_provider: str,
        oauth_id: str,
    ) -> User:
        return await self._model.create(
            email=email,
            hashed_password="",
            name=name,
            phone_number="",
            gender="MALE",
            birth_date="2000-01-01",
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            is_active=True,
            is_admin=False,
        )
