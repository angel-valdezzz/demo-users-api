"""Public request and response schemas."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Role(StrEnum):
    ADMIN = "admin"
    SUPPORT = "support"
    SALES = "sales"


class UserInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100, examples=["Angel Demo"])
    email: EmailStr = Field(examples=["angel@example.com"])
    role: Role = Role.SUPPORT
    active: bool = True


class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: Role | None = None
    active: bool | None = None

    @field_validator("name", "email", "role", "active")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Omit unchanged fields; null is not accepted")
        return value


class User(UserInput):
    id: UUID


class UserList(BaseModel):
    items: list[User]
    total: int
    limit: int
    offset: int


class UserStatistics(BaseModel):
    total: int
    active: int
    inactive: int
    roles: dict[Role, int]
