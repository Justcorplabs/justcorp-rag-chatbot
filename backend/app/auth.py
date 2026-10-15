"""Internal authorization boundary. No production identity provider exists yet."""
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException


@dataclass(frozen=True, slots=True)
class Principal:
    identifier: str
    active: bool
    role: Literal["member", "admin"]

    def __post_init__(self):
        if not valid_principal(self):
            raise ValueError("Invalid internal principal")


def valid_principal(value):
    return (
        type(value) is Principal
        and type(getattr(value, "identifier", None)) is str and bool(value.identifier.strip())
        and type(getattr(value, "active", None)) is bool
        and type(getattr(value, "role", None)) is str and value.role in ("member", "admin")
    )


def resolve_verified_principal():
    # Deliberately ignores all client-supplied identity material.
    raise HTTPException(status_code=401, detail="Verified identity required")


def require_user(principal=Depends(resolve_verified_principal)):
    if not valid_principal(principal):
        raise HTTPException(status_code=401, detail="Verified identity required")
    if not principal.active:
        raise HTTPException(status_code=403, detail="Inactive identity")
    return principal


def require_admin(principal=Depends(require_user)):
    if principal.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator required")
    return principal
