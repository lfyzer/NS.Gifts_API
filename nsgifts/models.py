from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Region(str, Enum):
    """Enum for supported Steam regions."""

    RU = "ru"
    KZ = "kz"
    UA = "ua"


class UserLoginSchema(BaseModel):
    """Schema for user login requests."""

    email: str
    password: str


class UserSchema(BaseModel):
    """Schema for user registration."""

    email: str
    role: str
    bybit_deposit: str = "0"


class CategoryRequest(BaseModel):
    """Schema for category request."""

    category_id: int


class CreateOrder(BaseModel):
    """Schema for order creation."""

    service_id: int
    quantity: float
    custom_id: str
    data: Optional[str] = None


class PayOrder(BaseModel):
    """Schema for order payment."""

    custom_id: str


class SteamRubCalculate(BaseModel):
    """Schema for Steam RUB amount calculation."""

    amount: int


class SteamGiftOrderCalculate(BaseModel):
    """Schema for Steam gift order calculation."""

    sub_id: int
    region: Region


class SteamGiftOrder(BaseModel):
    """Schema for Steam gift order creation."""

    friend_link: str = Field(alias="friendLink")
    sub_id: int
    region: Region
    gift_name: Optional[str] = Field(None, alias="giftName")
    gift_description: Optional[str] = Field(None, alias="giftDescription")


class SteamPackageRequest(BaseModel):
    """Schema for Steam package price request."""

    package_id: int