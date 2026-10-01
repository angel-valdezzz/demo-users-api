"""FastAPI factory. Set API_KEYS to a JSON object of credential labels and secrets."""

import hashlib
import json
import os
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.security import APIKeyHeader

from demo_api.models import Role, User, UserInput, UserList, UserPatch
from demo_api.store import UserStore


def create_app(api_keys: dict[str, str] | None = None) -> FastAPI:
    if api_keys is None:
        try:
            api_keys = json.loads(os.environ.get("API_KEYS", "{}"))
        except json.JSONDecodeError:
            raise RuntimeError("API_KEYS must be a JSON object") from None
    if (
        not isinstance(api_keys, dict)
        or not api_keys
        or any(
            not isinstance(k, str) or not k or not isinstance(v, str) or len(v) < 32
            for k, v in api_keys.items()
        )
    ):
        raise RuntimeError("API_KEYS needs named credentials of at least 32 characters")
    if len(set(api_keys.values())) != len(api_keys):
        raise RuntimeError("API_KEYS credentials must be unique")
    key_hashes = [
        (label, hashlib.sha256(value.encode()).hexdigest()) for label, value in api_keys.items()
    ]
    app = FastAPI(
        title="Demo Users API",
        version="0.1.0",
        description=(
            "Business flows for automated API testing. Use Authorize with X-API-Key. "
            "Each key has isolated temporary data; restarts restore initial data. "
            "Use fictitious information only."
        ),
        swagger_ui_parameters={"defaultModelsExpandDepth": -1, "displayRequestDuration": True},
    )
    store = UserStore()
    header = APIKeyHeader(name="X-API-Key", auto_error=False)

    def authenticate(key: Annotated[str | None, Depends(header)]):
        digest = hashlib.sha256((key or "").encode()).hexdigest()
        for label, expected in key_hashes:
            if secrets.compare_digest(digest, expected):
                return label
        raise HTTPException(401, "Invalid or missing API key")

    owner_dep = Annotated[str, Depends(authenticate)]

    @app.get("/health", tags=["Availability"])
    def health():
        return {"status": "ok", "storage": "temporary"}

    @app.get("/users", response_model=UserList, tags=["Users"])
    def list_users(
        owner: owner_dep,
        role: Role | None = None,
        active: bool | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        """List users with optional filters and pagination."""
        return store.list(owner, role, active, limit, offset)

    @app.post("/users", response_model=User, status_code=201, tags=["Users"])
    def create_user(owner: owner_dep, data: UserInput, response: Response):
        """Create a user. Emails are unique within each credential's data."""
        user = store.create(owner, data)
        response.headers["Location"] = f"/users/{user.id}"
        return user

    @app.get("/users/{user_id}", response_model=User, tags=["Users"])
    def get_user(owner: owner_dep, user_id: UUID):
        return store.get(owner, user_id)

    @app.put("/users/{user_id}", response_model=User, tags=["Users"])
    def replace_user(owner: owner_dep, user_id: UUID, data: UserInput):
        """Replace editable fields; omitted optional fields return to defaults."""
        return store.update(owner, user_id, data)

    @app.patch("/users/{user_id}", response_model=User, tags=["Users"])
    def patch_user(owner: owner_dep, user_id: UUID, data: UserPatch):
        """Update only supplied fields. Explicit null values are rejected."""
        return store.update(owner, user_id, data)

    @app.delete("/users/{user_id}", status_code=204, tags=["Users"])
    def delete_user(owner: owner_dep, user_id: UUID):
        store.delete(owner, user_id)
        return Response(status_code=204)

    return app
