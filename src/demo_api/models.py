"""Public request and response schemas."""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.json_schema import SkipJsonSchema


class Role(StrEnum):
    ADMIN = "admin"
    SUPPORT = "support"
    SALES = "sales"


class UserInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Angel Demo",
                    "email": "angel@example.com",
                    "role": "support",
                    "active": True,
                }
            ]
        },
    )
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Display name; surrounding whitespace is removed.",
        examples=["Angel Demo"],
    )
    email: EmailStr = Field(
        description="Valid email; unique within the authenticated credential's users.",
        examples=["angel@example.com"],
    )
    role: Role = Field(default=Role.SUPPORT, description="Business role: admin, support or sales.")
    active: bool = Field(default=True, description="Whether the user is active.")


class UserPatch(BaseModel):
    """Send only fields to update. Omitted fields stay unchanged; explicit null is rejected."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [{"active": False}, {"name": "Updated user", "role": "sales"}]
        },
    )
    name: str | SkipJsonSchema[None] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="New display name; omit to keep the current value.",
    )
    email: EmailStr | SkipJsonSchema[None] = Field(
        default=None, description="New unique email; explicit null is not accepted."
    )
    role: Role | SkipJsonSchema[None] = Field(
        default=None, description="New business role; omit to keep the current value."
    )
    active: bool | SkipJsonSchema[None] = Field(
        default=None,
        description="Use false to deactivate or true to activate; omit to keep the current value.",
    )

    @field_validator("name", "email", "role", "active", mode="before")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Omit unchanged fields; null is not accepted")
        return value


class User(UserInput):
    """Stored user returned by create, read, replace, patch and lifecycle operations."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "name": "Angel Demo",
                    "email": "angel@example.com",
                    "role": "support",
                    "active": True,
                }
            ]
        }
    )
    id: UUID = Field(
        description="Server-generated identifier.",
        examples=["22222222-2222-4222-8222-222222222222"],
    )


class UserList(BaseModel):
    """Filtered, paginated users and total number of matches before pagination."""

    items: list[User]
    total: int = Field(ge=0, description="Number of users matching the filters before pagination.")
    limit: int = Field(ge=1, le=100, description="Requested page size.")
    offset: int = Field(ge=0, description="Number of matching users skipped.")


class UserStatistics(BaseModel):
    """Counts within the authenticated credential; active + inactive equals total."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 3,
                    "active": 2,
                    "inactive": 1,
                    "roles": {"admin": 1, "support": 1, "sales": 1},
                }
            ]
        }
    )

    total: int
    active: int
    inactive: int
    roles: dict[Role, int] = Field(description="Counts keyed by each supported business role.")


class ErrorResponse(BaseModel):
    """Business or authentication error returned as {detail: message}."""

    detail: str = Field(
        description="Reason the operation was rejected.", examples=["User not found"]
    )


class HealthResponse(BaseModel):
    status: Literal["ok"] = Field(description="Service is available.")
    storage: Literal["temporary"] = Field(description="Data resets when the process restarts.")
