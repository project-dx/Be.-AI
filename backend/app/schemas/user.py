from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    support_start_date: date | None = None
    assigned_staff_id: int | None = None
    notes: str | None = None


class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int


class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=72)
    role: str = Field(pattern="^(admin|staff|user)$")
    profile: ProfileBase


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    is_active: bool | None = None
    role: str | None = Field(default=None, pattern="^(admin|staff|user)$")
    profile: ProfileBase | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime
    profile: ProfileOut | None = None
