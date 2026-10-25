"""High-entropy API key storage and verification for the optional internal ASGI API.

Raw credentials are returned once by create_key(). Only keyed SHA-256 digests are
persisted. Set API_KEY_PEPPER and API_KEY_ADMIN_TOKEN as deployment secrets.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

KEY_ID_RE = re.compile(r"^eos_([a-f0-9]{24})\.([A-Za-z0-9_-]{43})$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_expiry(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class APIKeyConfigurationError(RuntimeError):
    pass


class APIKeyManager:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("API_KEY_DB_PATH", Path(__file__).with_name("api_keys.db")))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @property
    def pepper(self) -> bytes:
        value = os.getenv("API_KEY_PEPPER", "")
        if len(value.encode("utf-8")) < 32:
            raise APIKeyConfigurationError("API_KEY_PEPPER must be a deployment secret of at least 32 bytes.")
        return value.encode("utf-8")

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10, isolation_level="IMMEDIATE")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                key_hint TEXT NOT NULL,
                hashed_key TEXT NOT NULL,
                used_already INTEGER NOT NULL DEFAULT 0,
                scopes TEXT NOT NULL DEFAULT '[]',
                rate_limit INTEGER NOT NULL DEFAULT 60 CHECK(rate_limit > 0),
                is_active INTEGER NOT NULL DEFAULT 1,
                expire_at TEXT,
                last_used_at TEXT,
                created_at TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix)")
            db.execute("""CREATE TABLE IF NOT EXISTS api_key_rate_windows (
                key_id TEXT NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
                window_start INTEGER NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(key_id, window_start)
            )""")
            db.execute("PRAGMA foreign_keys=ON")

    def _digest(self, secret: str) -> str:
        return hmac.new(self.pepper, secret.encode("ascii"), hashlib.sha256).hexdigest()

    def create_key(
        self,
        name: str,
        scopes: list[str] | None = None,
        rate_limit: int = 60,
        expire_at: str | None = None,
    ) -> dict[str, Any]:
        name = name.strip()
        if not name or len(name) > 120:
            raise ValueError("Key name must be between 1 and 120 characters.")
        if not 1 <= rate_limit <= 100_000:
            raise ValueError("Rate limit must be between 1 and 100000 requests per minute.")
        expiry = parse_expiry(expire_at)
        if expiry and expiry <= datetime.now(timezone.utc):
            raise ValueError("Expiry must be in the future.")
        normalized_scopes = sorted(set(scope.strip() for scope in (scopes or []) if scope.strip()))
        if any(len(scope) > 100 for scope in normalized_scopes):
            raise ValueError("Each scope must be 100 characters or fewer.")

        identifier = uuid4().hex[:24]
        secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii").rstrip("=")
        raw_key = f"eos_{identifier}.{secret}"
        with self.connect() as db:
            db.execute("""INSERT INTO api_keys
                (id,name,key_prefix,key_hint,hashed_key,used_already,scopes,rate_limit,is_active,expire_at,last_used_at,created_at)
                VALUES(?,?,?,?,?,0,?,?,1,?,NULL,?)""", (
                identifier, name, raw_key[:4], secret[:4], self._digest(secret),
                json.dumps(normalized_scopes), rate_limit, expiry.isoformat(timespec="seconds") if expiry else None, utc_now(),
            ))
        # The caller receives the raw key exactly once. It is never persisted.
        return {"id": identifier, "name": name, "key": raw_key, "key_prefix": raw_key[:4], "key_hint": secret[:4],
                "scopes": normalized_scopes, "rate_limit": rate_limit,
                "expire_at": expiry.isoformat(timespec="seconds") if expiry else None}

    def list_keys(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("""SELECT id,name,key_prefix,key_hint,used_already,scopes,rate_limit,
                is_active,expire_at,last_used_at,created_at FROM api_keys ORDER BY created_at DESC""").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["scopes"] = json.loads(item["scopes"] or "[]")
            item["used_already"] = bool(item["used_already"])
            item["is_active"] = bool(item["is_active"])
            result.append(item)
        return result

    def revoke_key(self, key_id: str) -> bool:
        with self.connect() as db:
            cursor = db.execute("UPDATE api_keys SET is_active=0 WHERE id=?", (key_id,))
            return cursor.rowcount > 0

    def update_key(self, key_id: str, changes: dict[str, Any]) -> bool:
        allowed = {"name", "scopes", "rate_limit", "is_active", "expire_at"}
        if not changes or set(changes) - allowed:
            raise ValueError("No valid API key fields were supplied.")
        values = dict(changes)
        if "name" in values:
            if values["name"] is None:
                raise ValueError("Key name cannot be null.")
            values["name"] = str(values["name"]).strip()
            if not values["name"] or len(values["name"]) > 120:
                raise ValueError("Key name must be between 1 and 120 characters.")
        if "scopes" in values:
            if values["scopes"] is None:
                raise ValueError("Scopes cannot be null; use an empty list to remove all scopes.")
            values["scopes"] = json.dumps(sorted(set(str(scope).strip() for scope in values["scopes"] if str(scope).strip())))
        if "rate_limit" in values:
            if values["rate_limit"] is None or not 1 <= int(values["rate_limit"]) <= 100_000:
                raise ValueError("Rate limit must be between 1 and 100000 requests per minute.")
        if "is_active" in values:
            if values["is_active"] is None:
                raise ValueError("Active status cannot be null.")
            values["is_active"] = int(bool(values["is_active"]))
        if "expire_at" in values:
            expiry = parse_expiry(values["expire_at"])
            values["expire_at"] = expiry.isoformat(timespec="seconds") if expiry else None
            if expiry and expiry <= datetime.now(timezone.utc):
                raise ValueError("Expiry must be in the future.")
        assignments = ",".join(f"{field}=?" for field in values)
        with self.connect() as db:
            cursor = db.execute(f"UPDATE api_keys SET {assignments} WHERE id=?", (*values.values(), key_id))
            return cursor.rowcount > 0

    def delete_key(self, key_id: str) -> bool:
        with self.connect() as db:
            db.execute("PRAGMA foreign_keys=ON")
            cursor = db.execute("DELETE FROM api_keys WHERE id=?", (key_id,))
            return cursor.rowcount > 0

    def authenticate(self, raw_key: str) -> dict[str, Any] | None:
        match = KEY_ID_RE.fullmatch(raw_key)
        if not match:
            return None
        identifier, provided_secret = match.groups()
        candidate = self._digest(provided_secret)
        with self.connect() as db:
            row = db.execute("SELECT * FROM api_keys WHERE id=?", (identifier,)).fetchone()
            if not row:
                return None
            # Compare fixed-length digests in constant time.
            if not hmac.compare_digest(row["hashed_key"], candidate):
                return None
            if not row["is_active"]:
                return None
            expiry = parse_expiry(row["expire_at"])
            if expiry and expiry <= datetime.now(timezone.utc):
                return None
            now = utc_now()
            db.execute("UPDATE api_keys SET used_already=1,last_used_at=? WHERE id=?", (now, identifier))
            return {"id": identifier, "name": row["name"], "scopes": json.loads(row["scopes"] or "[]"),
                    "rate_limit": row["rate_limit"]}

    def consume_rate_limit(self, identity: dict[str, Any]) -> bool:
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        window = now_epoch // 60
        with self.connect() as db:
            db.execute("""INSERT INTO api_key_rate_windows(key_id,window_start,request_count) VALUES(?,?,1)
                ON CONFLICT(key_id,window_start) DO UPDATE SET request_count=request_count+1""",
                (identity["id"], window))
            count = db.execute("SELECT request_count FROM api_key_rate_windows WHERE key_id=? AND window_start=?",
                               (identity["id"], window)).fetchone()[0]
            db.execute("DELETE FROM api_key_rate_windows WHERE window_start < ?", (window - 2,))
            return count <= identity["rate_limit"]


manager = APIKeyManager()
