"""Aster User Metadata Management Engine.

Comprehensive persistence, synchronization, and functional governance for:
1. Personal details (ID, full name, username, email, phone, avatar, bio, DOB, location, timezone, language)
2. Account details (status, role, verification status, timestamps, auth provider, MFA)
   * Note: Subscription fields omitted as requested.
3. User preferences (theme, accent colour, text density, font size, reduced motion, layout, landing page, notifications, formatting)
4. AI preferences (provider, model, API key status, domain models, response speed, length, reasoning detail, temperature, fallback, limits, context window)
5. Research profile (interests, expertise, professional role, industry, technical skills, methodology, citation style, sources, retention, instructions)
6. Workspace details (workspace ID, name, role, site, template, default repository, repo provider, counts, permissions)
7. Integrations (GitHub, GitLab, Google, cloud storage, connected list, OAuth identifiers, sync preferences)
8. Usage & activity (last active, project counts, research sessions, AI request counts, monthly usage, feature usage summary, onboarding)
9. Security & privacy (analytics/marketing/data processing consents with timestamps, privacy mode, retention, session count, security events, data export)
10. Personalization & memory (saved instructions, working style, coding conventions, tone, favorite tools/features, custom AI instructions)
11. System metadata (schema version 1.2.0, creation & update timestamps, migration version, custom attributes, internal flags)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

METADATA_SCHEMA_VERSION = "1.2.0"
CURRENT_MIGRATION_VERSION = 1


# ==============================================================================
# Database Schema Initialization
# ==============================================================================
def init_user_metadata_table(connection: sqlite3.Connection) -> None:
    """Initialize or migrate the user_metadata persistence table."""
    connection.execute("""CREATE TABLE IF NOT EXISTS user_metadata (
        user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT DEFAULT '',
        username TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone_number TEXT DEFAULT '',
        profile_picture TEXT DEFAULT '',
        bio TEXT DEFAULT '',
        date_of_birth TEXT DEFAULT '',
        country TEXT DEFAULT '',
        state_region TEXT DEFAULT '',
        city TEXT DEFAULT '',
        timezone TEXT DEFAULT 'UTC',
        preferred_language TEXT DEFAULT 'English (US)',
        
        account_status TEXT DEFAULT 'Active',
        account_role TEXT DEFAULT 'Research Scientist',
        email_verified INTEGER DEFAULT 0,
        phone_verified INTEGER DEFAULT 0,
        last_login_at TEXT DEFAULT '',
        last_password_changed_at TEXT DEFAULT '',
        auth_provider TEXT DEFAULT 'Email OTP',
        mfa_enabled INTEGER DEFAULT 0,
        
        user_preferences_json TEXT NOT NULL DEFAULT '{}',
        ai_preferences_json TEXT NOT NULL DEFAULT '{}',
        research_profile_json TEXT NOT NULL DEFAULT '{}',
        workspace_details_json TEXT NOT NULL DEFAULT '{}',
        integrations_json TEXT NOT NULL DEFAULT '{}',
        usage_activity_json TEXT NOT NULL DEFAULT '{}',
        security_privacy_json TEXT NOT NULL DEFAULT '{}',
        personalization_memory_json TEXT NOT NULL DEFAULT '{}',
        system_metadata_json TEXT NOT NULL DEFAULT '{}',
        
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")


# ==============================================================================
# Canonical Section Defaults
# ==============================================================================
def default_personal_details(user_id: str = "", email: str = "", name: str = "", created_at: str = "") -> dict[str, Any]:
    norm_email = (email or "").strip().lower()
    auto_username = norm_email.split("@")[0] if norm_email else f"user_{user_id[:8]}" if user_id else "researcher"
    return {
        "user_id": user_id,
        "full_name": (name or "").strip(),
        "username": auto_username,
        "email": norm_email,
        "phone_number": "",
        "profile_picture": "",
        "bio": "AI Researcher exploring model architectures and empirical reasoning.",
        "date_of_birth": "",
        "country": "United States",
        "state_region": "California",
        "city": "San Francisco",
        "timezone": "America/Los_Angeles",
        "preferred_language": "English (US)",
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
    }


def default_account_details(is_verified: bool = False, created_at: str = "") -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "account_status": "Active",
        "account_role": "Research Scientist",
        "email_verified": bool(is_verified),
        "phone_verified": False,
        "last_login_at": now_iso,
        "last_password_changed_at": created_at or now_iso,
        "auth_provider": "Email OTP",
        "mfa_enabled": False,
    }


def default_user_preferences() -> dict[str, Any]:
    return {
        "theme": "Obsidian Dark (Default)",
        "accent_colour": "Aster Orange (#f18a5e)",
        "text_density": "Comfortable",
        "font_size_preference": "Standard (16px)",
        "reduced_motion_preference": False,
        "dashboard_layout_preference": "Split Workflow",
        "default_landing_page": "Home",
        "notification_preferences": {
            "in_app": True,
            "experiment_run_alerts": True,
            "weekly_summary": True,
        },
        "email_update_preferences": True,
        "date_time_format": "YYYY-MM-DD HH:mm",
        "preferred_units": "Metric (SI)",
        "accessibility_preferences": {
            "high_contrast": False,
            "screen_reader_optimizations": False,
            "underline_links": False,
        },
    }


def default_ai_preferences() -> dict[str, Any]:
    return {
        "preferred_ai_provider": "Google Gemini",
        "preferred_ai_model": "gemini-2.0-flash",
        "user_provided_api_key_status": False,
        "default_model_research": "gemini-2.0-flash",
        "default_model_coding": "gemini-2.0-flash",
        "default_model_analysis": "gemini-2.0-flash",
        "response_time_preference": "Fast (Low latency)",
        "response_length_preference": "Balanced",
        "reasoning_detail_preference": "High (Step-by-step)",
        "default_temperature": 0.20,
        "model_fallback_preference": True,
        "ai_usage_limits": 1000,
        "default_context_window_preference": "Standard (32k)",
    }


def default_research_profile(interests: list[str] | None = None) -> dict[str, Any]:
    return {
        "research_interests": interests if interests is not None else [
            "Agentic Reasoning", "Memory-Native Systems", "Test-Time Compute"
        ],
        "area_of_expertise": "NLP & LLM Reasoning",
        "professional_role": "Lead AI Researcher",
        "industry": "Academic & Frontier Lab",
        "technical_skills": "PyTorch, JAX, Hugging Face, CUDA, Distributed Training",
        "preferred_research_methodology": "Empirical / Benchmarking",
        "preferred_citation_style": "BibTeX",
        "preferred_output_formats": "Markdown + LaTeX",
        "frequently_used_ai_sources": ["arXiv", "Hugging Face Daily Papers", "Papers With Code"],
        "research_history_retention_preference": "Forever",
        "save_research_instructions": True,
        "personal_knowledge_base_references": "Local notes in Aster workspace",
    }


def default_workspace_details(user_id: str = "") -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "default_workspace_id": f"ws_{user_id[:8]}" if user_id else f"ws_{uuid4().hex[:8]}",
        "workspace_name": "Aster Primary Lab",
        "workspace_role": "Owner",
        "workspace_site": "local.aster.internal",
        "workspace_creation_date": now_iso,
        "default_project_id": "proj_default",
        "preferred_project_template": "Standard LLM Benchmark",
        "default_repository": "aster-research-workspace",
        "repository_provider": "GitHub",
        "connected_repository_count": 1,
        "workspace_notification_settings": "All activity",
        "workspace_access_permissions": "Private (Isolated)",
    }


def default_integrations() -> dict[str, Any]:
    return {
        "github_connection_status": False,
        "gitlab_connection_status": False,
        "connected_google_account_status": False,
        "connected_cloud_storage_providers": ["Local Disk"],
        "connected_integration_list": ["Local SQLite Journal", "Wispr Flow Voice Dictation"],
        "oauth_connection_identifiers": {},
        "integration_permission_timestamps": {
            "local_storage": datetime.now(timezone.utc).isoformat()
        },
        "integration_synchronisation_preferences": "Real-time auto-sync",
    }


def default_usage_activity(onboarding_done: bool = False) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "last_active_timestamp": now_iso,
        "total_projects_created": 1,
        "total_research_sessions": 3,
        "total_ai_requests": 0,
        "monthly_ai_usage": 0,
        "feature_usage_summary": {
            "voice_notes": 0,
            "structuring": 0,
            "diagrams": 0,
            "comparisons": 0,
            "paper_radar": 1,
        },
        "onboarding_completion_status": bool(onboarding_done),
        "last_onboarding_step": "Interest calibration completed" if onboarding_done else "Pending interest tags",
        "recent_workspace_id": "ws_primary",
        "product_engagement_summary": "Active Daily Researcher",
    }


def default_security_privacy() -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "analytics_consent": True,
        "marketing_consent": False,
        "data_processing_consent": True,
        "consent_timestamps": {
            "data_processing": now_iso,
            "analytics": now_iso,
        },
        "privacy_preferences": "Strict Local (Zero external telemetry)",
        "data_retention_preference": "Retain until manual deletion",
        "active_session_count": 1,
        "last_security_event": "Authenticated session verified via local machine",
        "account_deletion_request_status": False,
        "data_export_request_status": False,
    }


def default_personalization_memory() -> dict[str, Any]:
    return {
        "saved_user_instructions": "Always include baseline delta metrics, empirical bounds, and note hardware constraints.",
        "preferred_working_style": "Hypothesis-first",
        "preferred_coding_conventions": "PEP 8 + Type Hints (Python)",
        "preferred_communication_tone": "Rigorous & Academic",
        "frequently_used_ai_tools": ["Gemini 2.0 Flash", "Wispr Flow", "Research Graph"],
        "favourite_features": ["Voice-to-Experiment", "Research Graph", "Preprint Radar"],
        "spin_projects": "Autonomous Evaluation Harnesses",
        "build_prompts": "Distill hypothesis, setup, metrics, and key takeaway",
        "custom_ai_instructions": "Format equations in LaTeX notation and flag potential confounding variables.",
        "personalization_settings": True,
    }


def default_system_metadata(created_at: str = "") -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "metadata_schema_version": METADATA_SCHEMA_VERSION,
        "record_creation_timestamp": created_at or now_iso,
        "record_update_timestamp": now_iso,
        "data_source_import_status": "Synchronized with Aster SQLite v3.43",
        "migration_version": CURRENT_MIGRATION_VERSION,
        "custom_attributes": {},
        "internal_flags": {
            "beta_features_enabled": True,
            "sandbox_mode": False,
            "fast_distillation": True,
        },
    }


# ==============================================================================
# User Metadata Fetching & Auto-Provisioning
# ==============================================================================
def get_user_metadata(connection: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    """Retrieve full metadata hierarchy for a user. Auto-provisions defaults if missing."""
    init_user_metadata_table(connection)

    # 1. Fetch user root record
    user_row = connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user_row:
        # Fallback pseudo-record if user ID is temporary
        email = "researcher@lab.org"
        name = "Researcher"
        interests = []
        is_verified = False
        onboarding_done = False
        created_at = datetime.now(timezone.utc).isoformat()
    else:
        email = user_row["email"]
        name = user_row["name"] if "name" in user_row.keys() else ""
        try:
            interests = json.loads(user_row["interests_json"] or "[]")
        except Exception:
            interests = []
        is_verified = bool(user_row["is_verified"])
        onboarding_done = bool(user_row["has_completed_onboarding"])
        created_at = user_row["created_at"]

    # 2. Fetch user_metadata row
    meta_row = connection.execute("SELECT * FROM user_metadata WHERE user_id=?", (user_id,)).fetchone()

    if not meta_row:
        # Provision fresh metadata
        p_details = default_personal_details(user_id, email, name, created_at)
        a_details = default_account_details(is_verified, created_at)
        u_pref = default_user_preferences()
        ai_pref = default_ai_preferences()
        r_prof = default_research_profile(interests)
        w_details = default_workspace_details(user_id)
        integ = default_integrations()
        u_act = default_usage_activity(onboarding_done)
        sec_priv = default_security_privacy()
        pers_mem = default_personalization_memory()
        sys_meta = default_system_metadata(created_at)

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            connection.execute("""INSERT INTO user_metadata (
                user_id, full_name, username, email, phone_number, profile_picture, bio,
                date_of_birth, country, state_region, city, timezone, preferred_language,
                account_status, account_role, email_verified, phone_verified, last_login_at,
                last_password_changed_at, auth_provider, mfa_enabled,
                user_preferences_json, ai_preferences_json, research_profile_json,
                workspace_details_json, integrations_json, usage_activity_json,
                security_privacy_json, personalization_memory_json, system_metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                user_id, p_details["full_name"], p_details["username"], p_details["email"],
                p_details["phone_number"], p_details["profile_picture"], p_details["bio"],
                p_details["date_of_birth"], p_details["country"], p_details["state_region"],
                p_details["city"], p_details["timezone"], p_details["preferred_language"],
                a_details["account_status"], a_details["account_role"], 1 if a_details["email_verified"] else 0,
                1 if a_details["phone_verified"] else 0, a_details["last_login_at"],
                a_details["last_password_changed_at"], a_details["auth_provider"], 1 if a_details["mfa_enabled"] else 0,
                json.dumps(u_pref), json.dumps(ai_pref), json.dumps(r_prof),
                json.dumps(w_details), json.dumps(integ), json.dumps(u_act),
                json.dumps(sec_priv), json.dumps(pers_mem), json.dumps(sys_meta),
                created_at, now_iso
            ))
            connection.commit()
        except Exception:
            pass

        # Count active sessions for accuracy
        active_sessions = 1
        try:
            active_sessions = connection.execute(
                "SELECT COUNT(*) as c FROM user_sessions WHERE user_id=? AND expires_at > ?",
                (user_id, datetime.now(timezone.utc).isoformat())
            ).fetchone()["c"] or 1
        except Exception:
            pass
        sec_priv["active_session_count"] = active_sessions

        return {
            "personal_details": p_details,
            "account_details": a_details,
            "user_preferences": u_pref,
            "ai_preferences": ai_pref,
            "research_profile": r_prof,
            "workspace_details": w_details,
            "integrations": integ,
            "usage_activity": u_act,
            "security_privacy": sec_priv,
            "personalization_memory": pers_mem,
            "system_metadata": sys_meta,
        }

    # Helper safely unpacks JSON or falls back to section defaults
    def _parse_or_default(raw_json: str, default_func, *args) -> dict[str, Any]:
        defaults = default_func(*args)
        if not raw_json:
            return defaults
        try:
            loaded = json.loads(raw_json)
            if isinstance(loaded, dict):
                defaults.update(loaded)
        except Exception:
            pass
        return defaults

    p_details = {
        "user_id": meta_row["user_id"],
        "full_name": meta_row["full_name"] or name,
        "username": meta_row["username"] or (email.split("@")[0] if email else "researcher"),
        "email": meta_row["email"] or email,
        "phone_number": meta_row["phone_number"] or "",
        "profile_picture": meta_row["profile_picture"] or "",
        "bio": meta_row["bio"] or "AI Researcher exploring model architectures and empirical reasoning.",
        "date_of_birth": meta_row["date_of_birth"] or "",
        "country": meta_row["country"] or "United States",
        "state_region": meta_row["state_region"] or "California",
        "city": meta_row["city"] or "San Francisco",
        "timezone": meta_row["timezone"] or "America/Los_Angeles",
        "preferred_language": meta_row["preferred_language"] or "English (US)",
        "created_at": meta_row["created_at"] or created_at,
    }

    a_details = {
        "account_status": meta_row["account_status"] or "Active",
        "account_role": meta_row["account_role"] or "Research Scientist",
        "email_verified": bool(meta_row["email_verified"] or is_verified),
        "phone_verified": bool(meta_row["phone_verified"]),
        "last_login_at": meta_row["last_login_at"] or datetime.now(timezone.utc).isoformat(),
        "last_password_changed_at": meta_row["last_password_changed_at"] or created_at,
        "auth_provider": meta_row["auth_provider"] or "Email OTP",
        "mfa_enabled": bool(meta_row["mfa_enabled"]),
    }

    u_pref = _parse_or_default(meta_row["user_preferences_json"], default_user_preferences)
    ai_pref = _parse_or_default(meta_row["ai_preferences_json"], default_ai_preferences)
    r_prof = _parse_or_default(meta_row["research_profile_json"], default_research_profile, interests)
    w_details = _parse_or_default(meta_row["workspace_details_json"], default_workspace_details, user_id)
    integ = _parse_or_default(meta_row["integrations_json"], default_integrations)
    u_act = _parse_or_default(meta_row["usage_activity_json"], default_usage_activity, onboarding_done)
    sec_priv = _parse_or_default(meta_row["security_privacy_json"], default_security_privacy)
    pers_mem = _parse_or_default(meta_row["personalization_memory_json"], default_personalization_memory)
    sys_meta = _parse_or_default(meta_row["system_metadata_json"], default_system_metadata, created_at)

    # Re-calculate live active sessions
    try:
        active_sessions = connection.execute(
            "SELECT COUNT(*) as c FROM user_sessions WHERE user_id=? AND expires_at > ?",
            (user_id, datetime.now(timezone.utc).isoformat())
        ).fetchone()["c"]
        sec_priv["active_session_count"] = max(1, active_sessions)
    except Exception:
        pass

    # Re-calculate total experiments in SQLite
    try:
        exp_count = connection.execute("SELECT COUNT(*) as c FROM experiments").fetchone()["c"]
        u_act["total_projects_created"] = max(1, exp_count)
    except Exception:
        pass

    return {
        "personal_details": p_details,
        "account_details": a_details,
        "user_preferences": u_pref,
        "ai_preferences": ai_pref,
        "research_profile": r_prof,
        "workspace_details": w_details,
        "integrations": integ,
        "usage_activity": u_act,
        "security_privacy": sec_priv,
        "personalization_memory": pers_mem,
        "system_metadata": sys_meta,
    }


# ==============================================================================
# User Metadata Persistence & Synchronization
# ==============================================================================
def save_user_metadata(
    connection: sqlite3.Connection,
    user_id: str,
    metadata_bundle: dict[str, Any],
) -> bool:
    """Save full metadata dictionary to SQLite and sync with parent users table."""
    init_user_metadata_table(connection)

    p_details = metadata_bundle.get("personal_details", {})
    a_details = metadata_bundle.get("account_details", {})
    u_pref = metadata_bundle.get("user_preferences", {})
    ai_pref = metadata_bundle.get("ai_preferences", {})
    r_prof = metadata_bundle.get("research_profile", {})
    w_details = metadata_bundle.get("workspace_details", {})
    integ = metadata_bundle.get("integrations", {})
    u_act = metadata_bundle.get("usage_activity", {})
    sec_priv = metadata_bundle.get("security_privacy", {})
    pers_mem = metadata_bundle.get("personalization_memory", {})
    sys_meta = metadata_bundle.get("system_metadata", {})

    now_iso = datetime.now(timezone.utc).isoformat()
    sys_meta["record_update_timestamp"] = now_iso

    try:
        connection.execute("""
            INSERT INTO user_metadata (
                user_id, full_name, username, email, phone_number, profile_picture, bio,
                date_of_birth, country, state_region, city, timezone, preferred_language,
                account_status, account_role, email_verified, phone_verified, last_login_at,
                last_password_changed_at, auth_provider, mfa_enabled,
                user_preferences_json, ai_preferences_json, research_profile_json,
                workspace_details_json, integrations_json, usage_activity_json,
                security_privacy_json, personalization_memory_json, system_metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name=excluded.full_name,
                username=excluded.username,
                email=excluded.email,
                phone_number=excluded.phone_number,
                profile_picture=excluded.profile_picture,
                bio=excluded.bio,
                date_of_birth=excluded.date_of_birth,
                country=excluded.country,
                state_region=excluded.state_region,
                city=excluded.city,
                timezone=excluded.timezone,
                preferred_language=excluded.preferred_language,
                account_status=excluded.account_status,
                account_role=excluded.account_role,
                email_verified=excluded.email_verified,
                phone_verified=excluded.phone_verified,
                last_login_at=excluded.last_login_at,
                last_password_changed_at=excluded.last_password_changed_at,
                auth_provider=excluded.auth_provider,
                mfa_enabled=excluded.mfa_enabled,
                user_preferences_json=excluded.user_preferences_json,
                ai_preferences_json=excluded.ai_preferences_json,
                research_profile_json=excluded.research_profile_json,
                workspace_details_json=excluded.workspace_details_json,
                integrations_json=excluded.integrations_json,
                usage_activity_json=excluded.usage_activity_json,
                security_privacy_json=excluded.security_privacy_json,
                personalization_memory_json=excluded.personalization_memory_json,
                system_metadata_json=excluded.system_metadata_json,
                updated_at=excluded.updated_at
        """, (
            user_id,
            p_details.get("full_name", ""),
            p_details.get("username", ""),
            p_details.get("email", ""),
            p_details.get("phone_number", ""),
            p_details.get("profile_picture", ""),
            p_details.get("bio", ""),
            p_details.get("date_of_birth", ""),
            p_details.get("country", ""),
            p_details.get("state_region", ""),
            p_details.get("city", ""),
            p_details.get("timezone", "UTC"),
            p_details.get("preferred_language", "English (US)"),
            a_details.get("account_status", "Active"),
            a_details.get("account_role", "Research Scientist"),
            1 if a_details.get("email_verified") else 0,
            1 if a_details.get("phone_verified") else 0,
            a_details.get("last_login_at", now_iso),
            a_details.get("last_password_changed_at", now_iso),
            a_details.get("auth_provider", "Email OTP"),
            1 if a_details.get("mfa_enabled") else 0,
            json.dumps(u_pref),
            json.dumps(ai_pref),
            json.dumps(r_prof),
            json.dumps(w_details),
            json.dumps(integ),
            json.dumps(u_act),
            json.dumps(sec_priv),
            json.dumps(pers_mem),
            json.dumps(sys_meta),
            p_details.get("created_at", now_iso),
            now_iso,
        ))

        # Synchronize with parent `users` table
        clean_name = p_details.get("full_name", "")
        interests = r_prof.get("research_interests", [])
        try:
            connection.execute(
                "UPDATE users SET name=?, interests_json=? WHERE id=?",
                (clean_name, json.dumps(interests), user_id),
            )
        except Exception:
            pass

        connection.commit()
        return True
    except Exception as exc:
        print(f"[Error saving user metadata]: {exc}")
        return False


# ==============================================================================
# Live Activity & Metrics Tracking
# ==============================================================================
def record_user_activity(
    connection: sqlite3.Connection,
    user_id: str,
    action_type: str = "ai_request",
    increment: int = 1,
) -> None:
    """Increment AI request counts or record feature usage in user metadata."""
    try:
        meta = get_user_metadata(connection, user_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        u_act = meta.get("usage_activity", {})
        u_act["last_active_timestamp"] = now_iso

        if action_type == "ai_request":
            u_act["total_ai_requests"] = int(u_act.get("total_ai_requests", 0)) + increment
            u_act["monthly_ai_usage"] = int(u_act.get("monthly_ai_usage", 0)) + increment
        elif action_type == "new_project":
            u_act["total_projects_created"] = int(u_act.get("total_projects_created", 0)) + increment
        elif action_type == "session":
            u_act["total_research_sessions"] = int(u_act.get("total_research_sessions", 0)) + increment

        # Update breakdown
        features = u_act.get("feature_usage_summary", {})
        if action_type in features:
            features[action_type] += increment
        else:
            features[action_type] = increment
        u_act["feature_usage_summary"] = features

        meta["usage_activity"] = u_act
        save_user_metadata(connection, user_id, meta)
    except Exception:
        pass


# ==============================================================================
# Dynamic CSS Styler based on User Preferences
# ==============================================================================
def generate_user_custom_css(preferences: dict[str, Any]) -> str:
    """Generate dynamic CSS to apply user theme, accent colour, font size, and text density."""
    accent = preferences.get("accent_colour", "Aster Orange (#f18a5e)")
    accent_hex = "#f18a5e"
    accent_hover = "#fa9870"
    if "Solar Copper" in accent:
        accent_hex = "#fa9870"
        accent_hover = "#ffb390"
    elif "Electric Violet" in accent:
        accent_hex = "#a990ff"
        accent_hover = "#bfadff"
    elif "Cyan Pulse" in accent:
        accent_hex = "#64d2ff"
        accent_hover = "#8de0ff"
    elif "Emerald" in accent:
        accent_hex = "#81c8a9"
        accent_hover = "#9de4c5"

    theme = preferences.get("theme", "Obsidian Dark (Default)")
    bg_gradient = "radial-gradient(ellipse at 76% 17%,rgba(40,68,145,.25),transparent 34rem),radial-gradient(ellipse at 12% 54%,rgba(17,112,147,.11),transparent 33rem),linear-gradient(155deg,#0c0e15,#080a0f 68%)"
    if "Onyx OLED" in theme:
        bg_gradient = "linear-gradient(180deg, #000000 0%, #050608 100%)"
    elif "Graphite Slate" in theme:
        bg_gradient = "linear-gradient(155deg, #16181f 0%, #0f1117 100%)"

    font_pref = preferences.get("font_size_preference", "Standard (16px)")
    font_size = "16px"
    if "Small" in font_pref:
        font_size = "14px"
    elif "Large" in font_pref:
        font_size = "18px"

    density = preferences.get("text_density", "Comfortable")
    line_height = "1.55"
    card_padding = "16px"
    if density == "Compact":
        line_height = "1.35"
        card_padding = "10px"
    elif density == "Expanded":
        line_height = "1.75"
        card_padding = "22px"

    reduced_motion = preferences.get("reduced_motion_preference", False)
    motion_css = "* { animation: none !important; transition: none !important; }" if reduced_motion else ""

    return f"""
    <style>
    :root {{
      --aster-accent: {accent_hex} !important;
      --orange: {accent_hex} !important;
      --orange-light: {accent_hover} !important;
    }}
    html, body, .stApp {{
      background: {bg_gradient} !important;
      font-size: {font_size} !important;
      line-height: {line_height} !important;
    }}
    .button-primary, div[data-testid="stButton"]>button[kind="primary"] {{
      background: {accent_hex} !important;
      border-color: {accent_hover} !important;
    }}
    .button-primary:hover, div[data-testid="stButton"]>button[kind="primary"]:hover {{
      background: {accent_hover} !important;
    }}
    {motion_css}
    </style>
    """


# ==============================================================================
# Complete Research & Metadata Data Export Bundle
# ==============================================================================
def export_user_data_bundle(connection: sqlite3.Connection, user_id: str) -> str:
    """Generate comprehensive JSON archive for privacy compliance and backup."""
    meta = get_user_metadata(connection, user_id)
    experiments: list[dict[str, Any]] = []
    try:
        rows = connection.execute("SELECT * FROM experiments ORDER BY created_at DESC").fetchall()
        for r in rows:
            experiments.append(dict(r))
    except Exception:
        pass

    contexts: list[dict[str, Any]] = []
    try:
        rows = connection.execute("SELECT * FROM research_contexts ORDER BY created_at DESC").fetchall()
        for r in rows:
            contexts.append(dict(r))
    except Exception:
        pass

    memories: list[dict[str, Any]] = []
    try:
        rows = connection.execute("SELECT * FROM experiment_memories").fetchall()
        for r in rows:
            memories.append(dict(r))
    except Exception:
        pass

    bundle = {
        "export_metadata": {
            "app": "Aster Research OS",
            "version": METADATA_SCHEMA_VERSION,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
        },
        "user_profile_and_metadata": meta,
        "experiments_count": len(experiments),
        "experiments": experiments,
        "research_contexts": contexts,
        "experiment_memories": memories,
    }
    return json.dumps(bundle, indent=2, ensure_ascii=False)
