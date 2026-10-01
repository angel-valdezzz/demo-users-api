"""Thread-safe ephemeral storage, separated for each credential."""

from threading import RLock
from uuid import UUID, uuid4

from fastapi import HTTPException

from demo_api.models import Role, User, UserInput, UserPatch


class UserStore:
    def __init__(self):
        self._lock = RLock()
        self._spaces: dict[str, dict[UUID, User]] = {}

    def _space(self, owner: str):
        if owner not in self._spaces:
            seed = User(
                id=uuid4(), name="Demo Support", email="support@example.com", role=Role.SUPPORT
            )
            self._spaces[owner] = {seed.id: seed}
        return self._spaces[owner]

    def list(self, owner, role, active, limit, offset):
        with self._lock:
            items = [
                u
                for u in self._space(owner).values()
                if (role is None or u.role == role) and (active is None or u.active == active)
            ]
            return {
                "items": items[offset : offset + limit],
                "total": len(items),
                "limit": limit,
                "offset": offset,
            }

    def get(self, owner: str, user_id: UUID):
        with self._lock:
            user = self._space(owner).get(user_id)
            if user is None:
                raise HTTPException(404, "User not found")
            return user

    def _unique(self, space, email, excluded=None):
        if any(
            u.email.casefold() == str(email).casefold() and u.id != excluded for u in space.values()
        ):
            raise HTTPException(409, "Email already registered")

    def create(self, owner: str, data: UserInput):
        with self._lock:
            space = self._space(owner)
            self._unique(space, data.email)
            if len(space) >= 1000:
                raise HTTPException(409, "Demo capacity reached; delete unused users")
            user = User(id=uuid4(), **data.model_dump())
            space[user.id] = user
            return user

    def update(self, owner: str, user_id: UUID, data: UserInput | UserPatch):
        with self._lock:
            old = self.get(owner, user_id)
            values = old.model_dump()
            values.update(data.model_dump(exclude_unset=isinstance(data, UserPatch)))
            updated = User.model_validate(values)
            self._unique(self._space(owner), updated.email, user_id)
            self._space(owner)[user_id] = updated
            return updated

    def delete(self, owner: str, user_id: UUID):
        with self._lock:
            self.get(owner, user_id)
            del self._space(owner)[user_id]
