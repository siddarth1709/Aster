"""Optional FastAPI service exposing internal API routes protected by API keys."""
from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api_keys import APIKeyConfigurationError, manager

app = FastAPI(title="Experiment OS Internal API", docs_url=None, redoc_url=None, openapi_url=None)


class CreateKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=list)
    rate_limit: int = Field(default=60, ge=1, le=100_000)
    expire_at: str | None = None


class UpdateKeyRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    scopes: list[str] | None = None
    rate_limit: int | None = Field(default=None, ge=1, le=100_000)
    is_active: bool | None = None
    expire_at: str | None = None


def verify_admin(request: Request) -> None:
    expected = os.getenv("API_KEY_ADMIN_TOKEN", "")
    supplied = request.headers.get("authorization", "")
    supplied = supplied[7:] if supplied.startswith("Bearer ") else ""
    if len(expected) < 32 or not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def protect_internal_routes(request: Request, call_next):
    if not request.url.path.startswith("/internal/"):
        return await call_next(request)
    authorization = request.headers.get("authorization", "")
    bearer = authorization[7:] if authorization.startswith("Bearer ") else ""
    custom = request.headers.get("x-api-key", "")
    if bearer and custom:
        return JSONResponse({"detail": "Provide one API key credential"}, status_code=401)
    raw_key = bearer or custom
    if not raw_key:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    try:
        identity = manager.authenticate(raw_key)
    except APIKeyConfigurationError:
        return JSONResponse({"detail": "Authentication is unavailable"}, status_code=503)
    except Exception:
        return JSONResponse({"detail": "Authentication is unavailable"}, status_code=503)
    if not identity:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    if not manager.consume_rate_limit(identity):
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    request.state.api_key = identity
    request.state.scopes = identity["scopes"]
    return await call_next(request)


@app.post("/admin/api-keys", status_code=201)
def create_api_key(body: CreateKeyRequest, request: Request) -> dict[str, Any]:
    verify_admin(request)
    try:
        return manager.create_key(body.name, body.scopes, body.rate_limit, body.expire_at)
    except (ValueError, APIKeyConfigurationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/admin/api-keys")
def list_api_keys(request: Request) -> list[dict[str, Any]]:
    verify_admin(request)
    # The hashed key and raw key are deliberately excluded from list results.
    return manager.list_keys()


@app.patch("/admin/api-keys/{key_id}")
def update_api_key(key_id: str, body: UpdateKeyRequest, request: Request) -> dict[str, str]:
    verify_admin(request)
    changes = body.model_dump(exclude_unset=True)
    try:
        if not manager.update_key(key_id, changes):
            raise HTTPException(status_code=404, detail="API key not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"status": "updated"}


@app.delete("/admin/api-keys/{key_id}")
def revoke_api_key(key_id: str, request: Request) -> dict[str, str]:
    verify_admin(request)
    if not manager.revoke_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "revoked"}


@app.delete("/admin/api-keys/{key_id}/permanent")
def delete_api_key(key_id: str, request: Request) -> dict[str, str]:
    verify_admin(request)
    if not manager.delete_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "deleted"}


@app.get("/internal/whoami")
def whoami(request: Request) -> dict[str, Any]:
    identity = request.state.api_key
    if "read:self" not in request.state.scopes:
        raise HTTPException(status_code=403, detail="Insufficient scope")
    return {"id": identity["id"], "name": identity["name"], "scopes": request.state.scopes}
