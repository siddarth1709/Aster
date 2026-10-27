"""Authentication and Access Control State Machine.

Governs:
1. User identity model (ID, normalised lowercase email, salted PBKDF2 password hash, interests list, onboarding flag, verified status).
2. Registration validation (RFC-compliant email, password complexity: 8-12+ chars, mixed case, digits, symbols).
3. No-cost email verifier with cryptographically secure OTP generation, expiration, and verification.
4. Persistent user sessions with secure bearer tokens and database backing.
5. Onboarding state tracking (blocks dashboard until interest tags are selected and persisted).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PASSWORD_MIN_LENGTH = 8
PASSWORD_RECOMMENDED_LENGTH = 12
OTP_EXPIRATION_MINUTES = 15
SESSION_EXPIRATION_DAYS = 30


# ==============================================================================
# Database Schema Initialization
# ==============================================================================
def init_auth_tables(connection: sqlite3.Connection) -> None:
    """Initialize user state model, OTP verification, and session tables."""
    connection.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT DEFAULT '',
        interests_json TEXT NOT NULL DEFAULT '[]',
        has_completed_onboarding INTEGER NOT NULL DEFAULT 0,
        is_verified INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )""")
    try:
        connection.execute("ALTER TABLE users ADD COLUMN name TEXT DEFAULT ''")
    except Exception:
        pass

    connection.execute("""CREATE TABLE IF NOT EXISTS email_verifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        email TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )""")

    connection.execute("""CREATE TABLE IF NOT EXISTS user_sessions (
        session_token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )""")


# ==============================================================================
# Cryptographic Password Hashing & Strength Validation
# ==============================================================================
def hash_password(password: str) -> str:
    """Generate salted PBKDF2-HMAC-SHA256 password hash. Never store raw passwords."""
    salt = secrets.token_hex(16)
    iterations = 200_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2:sha256:{iterations}${salt}${dk.hex()}"


def verify_password(password: str, hashed_value: str) -> bool:
    """Constant-time verification of raw password against stored salted hash."""
    if not hashed_value or "$" not in hashed_value:
        return False
    try:
        parts = hashed_value.split("$")
        if len(parts) != 3:
            return False
        meta, salt, expected_hex = parts
        _, algo, iters_str = meta.split(":")
        iterations = int(iters_str)
        dk = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(dk.hex(), expected_hex)
    except Exception:
        return False


def normalize_email(email: str) -> str:
    """Normalize email string: trimmed and lowercase."""
    return (email or "").strip().lower()


def validate_email_format(email: str) -> tuple[bool, str]:
    """Validate email against RFC format rules."""
    norm = normalize_email(email)
    if not norm:
        return False, "Email address is required."
    if len(norm) > 254:
        return False, "Email address exceeds maximum permitted length."
    if not EMAIL_REGEX.match(norm):
        return False, "Please enter a valid academic or professional email address (e.g. researcher@lab.org)."
    return True, ""


def validate_password_security(password: str) -> tuple[bool, str]:
    """Enforce password security policy: min 8-12 characters, mixed character types."""
    if not password:
        return False, "Password cannot be blank."
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long (12+ recommended)."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one numerical digit (0-9)."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must include at least one special symbol (!@#$%^&*()_+-=[]{}|;:,.<>?)."
    return True, ""


# ==============================================================================
# User Account Handlers
# ==============================================================================
def register_user(
    connection: sqlite3.Connection,
    email: str,
    password: str,
    name: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """Sign up handler: validate format, check duplicates, enforce password complexity, store salted hash."""
    valid_email, email_err = validate_email_format(email)
    if not valid_email:
        return None, email_err

    valid_pw, pw_err = validate_password_security(password)
    if not valid_pw:
        return None, pw_err

    norm_email = normalize_email(email)

    # Check for existing duplicate account
    existing = connection.execute(
        "SELECT id FROM users WHERE email=?", (norm_email,)
    ).fetchone()
    if existing:
        return None, "An account registered with this email already exists. Please log in instead."

    user_id = str(uuid4())
    pw_hash = hash_password(password)
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_name = (name or "").strip()

    try:
        connection.execute(
            """INSERT INTO users
               (id, email, password_hash, name, interests_json, has_completed_onboarding, is_verified, created_at)
               VALUES (?, ?, ?, ?, '[]', 0, 0, ?)""",
            (user_id, norm_email, pw_hash, clean_name, now_iso),
        )
    except sqlite3.OperationalError:
        connection.execute(
            """INSERT INTO users
               (id, email, password_hash, interests_json, has_completed_onboarding, is_verified, created_at)
               VALUES (?, ?, ?, '[]', 0, 0, ?)""",
            (user_id, norm_email, pw_hash, now_iso),
        )

    # Issue initial verification OTP
    otp_code = create_email_verification_otp(connection, user_id, norm_email)

    # Auto-provision user metadata ledger
    try:
        import user_metadata_manager
        user_metadata_manager.get_user_metadata(connection, user_id)
    except Exception:
        pass

    user_record = {
        "id": user_id,
        "email": norm_email,
        "name": clean_name,
        "interests": [],
        "has_completed_onboarding": False,
        "is_verified": False,
        "created_at": now_iso,
        "latest_otp": otp_code,
    }

    return user_record, ""


def login_user(
    connection: sqlite3.Connection,
    email: str,
    password: str,
) -> tuple[dict[str, Any] | None, str]:
    """Login handler: authenticate email and password against salted hash."""
    norm_email = normalize_email(email)
    if not norm_email:
        return None, "Please enter your email."
    if not password:
        return None, "Please enter your password."

    row = connection.execute(
        "SELECT * FROM users WHERE email=?", (norm_email,)
    ).fetchone()
    if not row:
        return None, "No account found matching this email. Please sign up first."

    stored_hash = row["password_hash"]
    if not verify_password(password, stored_hash):
        return None, "Invalid credentials. Please verify your email and password."

    # Update metadata last_login_at
    try:
        import user_metadata_manager
        meta = user_metadata_manager.get_user_metadata(connection, row["id"])
        meta["account_details"]["last_login_at"] = datetime.now(timezone.utc).isoformat()
        user_metadata_manager.save_user_metadata(connection, row["id"], meta)
    except Exception:
        pass

    interests = []
    try:
        interests = json.loads(row["interests_json"] or "[]")
    except Exception:
        interests = []

    user_record = {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] if "name" in row.keys() else "",
        "interests": interests,
        "has_completed_onboarding": bool(row["has_completed_onboarding"]),
        "is_verified": bool(row["is_verified"]),
        "created_at": row["created_at"],
    }

    return user_record, ""


# ==============================================================================
# No-Cost Email Verification & OTP Management
# ==============================================================================
def create_email_verification_otp(
    connection: sqlite3.Connection,
    user_id: str,
    email: str,
) -> str:
    """Generate cryptographically secure 6-digit OTP with 15-minute expiration."""
    otp_int = secrets.randbelow(900_000) + 100_000
    otp_code = str(otp_int)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=OTP_EXPIRATION_MINUTES)).isoformat()
    now_iso = now.isoformat()
    verification_id = str(uuid4())

    # Invalidate previous unexpired OTPs for this user
    connection.execute("DELETE FROM email_verifications WHERE user_id=?", (user_id,))

    connection.execute(
        """INSERT INTO email_verifications
           (id, user_id, email, otp_code, expires_at, attempts, created_at)
           VALUES (?, ?, ?, ?, ?, 0, ?)""",
        (verification_id, user_id, email, otp_code, expires_at, now_iso),
    )

    return otp_code


def verify_email_otp(
    connection: sqlite3.Connection,
    user_id: str,
    submitted_otp: str,
) -> tuple[bool, str]:
    """Verify submitted 6-digit OTP against active token record."""
    clean_otp = (submitted_otp or "").strip()
    if not clean_otp:
        return False, "Please enter the 6-digit verification code."

    row = connection.execute(
        "SELECT * FROM email_verifications WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    if not row:
        return False, "No active verification code found. Please request a new code."

    # Check maximum attempt limit to prevent brute force
    attempts = row["attempts"]
    if attempts >= 5:
        return False, "Too many incorrect attempts. Please request a new verification code."

    # Check expiration
    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        return False, "This verification code has expired. Please request a new one."

    # Compare OTP using constant-time comparison
    if not hmac.compare_digest(row["otp_code"], clean_otp):
        connection.execute(
            "UPDATE email_verifications SET attempts = attempts + 1 WHERE id=?",
            (row["id"],),
        )
        remaining = 4 - attempts
        return False, f"Incorrect code. {remaining} attempt(s) remaining."

    # Code is valid: mark user as verified
    connection.execute(
        "UPDATE users SET is_verified=1 WHERE id=?", (user_id,)
    )
    connection.execute("DELETE FROM email_verifications WHERE id=?", (row["id"],))

    return True, "Email successfully verified!"


# ==============================================================================
# Stage 2 Onboarding State Transition
# ==============================================================================
def persist_user_onboarding_interests(
    connection: sqlite3.Connection,
    user_id: str,
    interest_tags: list[str],
) -> tuple[bool, str]:
    """Persist interest tags array and set has_completed_onboarding = True."""
    cleaned_tags = [str(t).strip() for t in interest_tags if str(t).strip()]
    if not cleaned_tags:
        return False, "Please select at least one research focus tag to calibrate your feed."

    json_tags = json.dumps(cleaned_tags, ensure_ascii=False)
    connection.execute(
        """UPDATE users
           SET interests_json=?, has_completed_onboarding=1
           WHERE id=?""",
        (json_tags, user_id),
    )
    return True, ""


def update_user_field(
    connection: sqlite3.Connection,
    user_id: str,
    field_name: str,
    value: Any,
) -> None:
    """Safely update a column value for a given user."""
    allowed_fields = {"has_completed_onboarding", "is_verified", "name", "interests_json"}
    if field_name in allowed_fields:
        connection.execute(f"UPDATE users SET {field_name}=? WHERE id=?", (value, user_id))
        try:
            connection.commit()
        except Exception:
            pass


# ==============================================================================
# Session Token Management
# ==============================================================================
def create_session(
    connection: sqlite3.Connection,
    user_id: str,
) -> str:
    """Issue authenticated session bearer token immediately."""
    session_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=SESSION_EXPIRATION_DAYS)).isoformat()
    now_iso = now.isoformat()

    connection.execute(
        """INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
           VALUES (?, ?, ?, ?)""",
        (session_token, user_id, now_iso, expires_at),
    )
    try:
        connection.commit()
    except Exception:
        pass

    return session_token


def get_user_by_session(
    connection: sqlite3.Connection,
    session_token: str,
) -> dict[str, Any] | None:
    """Retrieve user record associated with an active session token."""
    if not session_token:
        return None

    row = connection.execute(
        """SELECT u.* FROM users u
           JOIN user_sessions s ON u.id = s.user_id
           WHERE s.session_token = ? AND s.expires_at > ?""",
        (session_token, datetime.now(timezone.utc).isoformat()),
    ).fetchone()

    if not row:
        return None

    interests = []
    try:
        interests = json.loads(row["interests_json"] or "[]")
    except Exception:
        interests = []

    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] if "name" in row.keys() else "",
        "interests": interests,
        "has_completed_onboarding": bool(row["has_completed_onboarding"]),
        "is_verified": bool(row["is_verified"]),
        "created_at": row["created_at"],
    }


def destroy_session(
    connection: sqlite3.Connection,
    session_token: str,
) -> None:
    """Revoke and delete session token upon logout."""
    if session_token:
        connection.execute("DELETE FROM user_sessions WHERE session_token=?", (session_token,))
        try:
            connection.commit()
        except Exception:
            pass


# ==============================================================================
# Demo Account Bypass System
# ==============================================================================
def get_or_create_demo_user(
    connection: sqlite3.Connection,
) -> tuple[dict[str, Any], str]:
    """Retrieve or automatically initialize a verified demo research scientist user and issue a valid session token."""
    demo_email = "demo.researcher@aster.ai"
    row = connection.execute(
        "SELECT * FROM users WHERE email=?", (demo_email,)
    ).fetchone()

    now_iso = datetime.now(timezone.utc).isoformat()
    demo_interests = ["agent-evaluation", "llm-reasoning", "long-context-retrieval", "prompt-optimization"]

    if row:
        user_id = row["id"]
        # Ensure demo user is verified and has completed onboarding so it goes directly to dashboard
        try:
            connection.execute(
                """UPDATE users
                   SET is_verified=1, has_completed_onboarding=1, name='Dr. Aster Demo',
                       interests_json=COALESCE(NULLIF(interests_json, '[]'), ?)
                   WHERE id=?""",
                (json.dumps(demo_interests), user_id),
            )
        except sqlite3.OperationalError:
            connection.execute(
                """UPDATE users
                   SET is_verified=1, has_completed_onboarding=1,
                       interests_json=COALESCE(NULLIF(interests_json, '[]'), ?)
                   WHERE id=?""",
                (json.dumps(demo_interests), user_id),
            )
    else:
        user_id = str(uuid4())
        pw_hash = hash_password(secrets.token_hex(16))
        demo_name = "Dr. Aster Demo"
        try:
            connection.execute(
                """INSERT INTO users
                   (id, email, password_hash, name, interests_json, has_completed_onboarding, is_verified, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, 1, ?)""",
                (user_id, demo_email, pw_hash, demo_name, json.dumps(demo_interests), now_iso),
            )
        except sqlite3.OperationalError:
            connection.execute(
                """INSERT INTO users
                   (id, email, password_hash, interests_json, has_completed_onboarding, is_verified, created_at)
                   VALUES (?, ?, ?, ?, 1, 1, ?)""",
                (user_id, demo_email, pw_hash, json.dumps(demo_interests), now_iso),
            )

    try:
        connection.commit()
    except Exception:
        pass

    # Auto-provision or update user metadata ledger
    try:
        import user_metadata_manager
        meta = user_metadata_manager.get_user_metadata(connection, user_id)
        if not meta.get("personal_details", {}).get("full_name"):
            meta["personal_details"]["full_name"] = "Dr. Aster Demo"
        if not meta.get("personal_details", {}).get("username"):
            meta["personal_details"]["username"] = "demo.researcher"
        meta["account_details"]["email_verified"] = True
        meta["account_details"]["account_status"] = "Active (Demo Mode)"
        meta["account_details"]["account_role"] = "Principal AI Researcher"
        meta["account_details"]["last_login_at"] = now_iso
        user_metadata_manager.save_user_metadata(connection, user_id, meta)
    except Exception:
        pass

    session_token = create_session(connection, user_id)

    updated_row = connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    interests = []
    try:
        interests = json.loads(updated_row["interests_json"] or "[]")
    except Exception:
        interests = demo_interests

    user_record = {
        "id": updated_row["id"],
        "email": updated_row["email"],
        "name": updated_row["name"] if "name" in updated_row.keys() else "Dr. Aster Demo",
        "interests": interests,
        "has_completed_onboarding": True,
        "is_verified": True,
        "created_at": updated_row["created_at"],
    }

    try:
        connection.commit()
    except Exception:
        pass

    return user_record, session_token
