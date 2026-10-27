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

METADATA_SCHEMA_VERSION = "2.0.0"
CURRENT_MIGRATION_VERSION = 2

# Allowed Whitelists for Server-Side Validation
ALLOWED_THEMES = {"Obsidian Dark (Default)", "Onyx OLED", "Graphite Slate"}
ALLOWED_ACCENTS = {
    "Aster Orange (#f18a5e)",
    "Solar Copper (#fa9870)",
    "Electric Violet (#a990ff)",
    "Cyan Pulse (#64d2ff)",
    "Emerald (#81c8a9)",
}
ALLOWED_DENSITIES = {"Comfortable", "Compact", "Expanded"}
ALLOWED_FONTS = {"Standard (16px)", "Small (14px)", "Large (18px)"}
ALLOWED_LAYOUTS = {"Split Workflow", "Linear Feed", "Matrix Grid"}
ALLOWED_LANDING_PAGES = {
    "Home",
    "Create Experiment",
    "All Experiments",
    "Research Graph",
    "Weekly Summary",
    "Compare Experiments",
    "Settings",
}
ALLOWED_DT_FORMATS = {"YYYY-MM-DD HH:mm", "DD/MM/YYYY HH:mm", "MMM D, YYYY h:mm A"}
ALLOWED_UNITS = {"Metric (SI)", "US Customary"}
ALLOWED_AI_PROVIDERS = {"Google Gemini", "Anthropic Claude (BYOK)", "OpenAI (BYOK)", "Ollama / Local"}
ALLOWED_AI_MODELS = {"gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "claude-3-7-sonnet", "gpt-4o", "deepseek-r1-local"}
ALLOWED_SPEEDS = {"Fast (Low latency)", "Balanced", "Deep deliberate thought"}
ALLOWED_LENGTHS = {"Concise", "Balanced", "Exhaustive / Detailed"}
ALLOWED_REASONINGS = {"High (Step-by-step)", "Standard", "Minimal"}
ALLOWED_WINDOWS = {"Standard (32k)", "Extended (128k)", "Ultra (1M+ tokens)"}
ALLOWED_PRIVACY_MODES = {"Strict Local (Zero external telemetry)", "Protected Cloud", "Full Sync"}
ALLOWED_RETENTION_POLICIES = {"Retain until manual deletion", "Purge after 1 year", "Purge after 90 days"}


# ==============================================================================
# Database Schema Initialization & Idempotent Migrations
# ==============================================================================
def ensure_foreign_keys(connection: sqlite3.Connection) -> None:
    """Ensure foreign key constraint enforcement is enabled on this connection."""
    try:
        connection.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    if connection.row_factory is None:
        connection.row_factory = sqlite3.Row


def _apply_migration_v1(connection: sqlite3.Connection) -> None:
    """Migration 1: Base metadata schema and indexes."""
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


def _apply_migration_v2(connection: sqlite3.Connection) -> None:
    """Migration 2: Relational tables for workspaces, saved prompts, consents, integrations, audit logs, and privacy requests."""
    # 1. Workspaces
    connection.execute("""CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        site TEXT NOT NULL DEFAULT 'local.aster.internal',
        default_repository TEXT NOT NULL DEFAULT 'aster-research-workspace',
        privacy TEXT NOT NULL DEFAULT 'Private (Local SQLite)',
        notification_settings TEXT NOT NULL DEFAULT 'All activity',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_id)")

    # 2. Workspace Memberships
    connection.execute("""CREATE TABLE IF NOT EXISTS workspace_members (
        workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role TEXT NOT NULL DEFAULT 'Owner',
        joined_at TEXT NOT NULL,
        PRIMARY KEY (workspace_id, user_id)
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id)")

    # 3. Saved Prompts
    connection.execute("""CREATE TABLE IF NOT EXISTS user_saved_prompts (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        prompt_template TEXT NOT NULL,
        task_domain TEXT NOT NULL DEFAULT 'general',
        tags_json TEXT NOT NULL DEFAULT '[]',
        is_pinned INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, title)
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_saved_prompts_user ON user_saved_prompts(user_id, is_pinned DESC, updated_at DESC)")

    # 4. Consent History (Append-only audit trail of consent events)
    connection.execute("""CREATE TABLE IF NOT EXISTS user_consents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        consent_type TEXT NOT NULL,
        granted INTEGER NOT NULL DEFAULT 0,
        policy_version TEXT NOT NULL DEFAULT '1.0',
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_user_consents_user ON user_consents(user_id, consent_type, created_at DESC)")

    # 5. Connected Integrations (Authoritative connection registry, strictly NO plaintext tokens)
    connection.execute("""CREATE TABLE IF NOT EXISTS user_integrations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        provider TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'disconnected',
        account_identifier TEXT DEFAULT '',
        config_json TEXT NOT NULL DEFAULT '{}',
        scopes_json TEXT NOT NULL DEFAULT '[]',
        connected_at TEXT,
        last_synced_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(user_id, provider)
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_user_integrations_user ON user_integrations(user_id, provider)")

    # 6. Security Audit Logs (Append-only security events log with severity & IP)
    connection.execute("""CREATE TABLE IF NOT EXISTS user_audit_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'info',
        details TEXT NOT NULL DEFAULT '',
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_user_audit_logs_user ON user_audit_logs(user_id, created_at DESC)")

    # 7. Privacy Requests (Lifecycle of GDPR export & right-to-be-forgotten requests)
    connection.execute("""CREATE TABLE IF NOT EXISTS user_privacy_requests (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        request_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        format TEXT NOT NULL DEFAULT 'json',
        details TEXT DEFAULT '',
        requested_at TEXT NOT NULL,
        completed_at TEXT,
        expires_at TEXT
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_user_privacy_requests_user ON user_privacy_requests(user_id, requested_at DESC)")

    # 8. Safe Alter Tables for existing tables (experiments, saved_papers)
    exp_table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiments'").fetchone()
    if exp_table:
        exp_columns = {row[1] for row in connection.execute("PRAGMA table_info(experiments)")}
        if "user_id" not in exp_columns:
            try:
                connection.execute("ALTER TABLE experiments ADD COLUMN user_id TEXT REFERENCES users(id) ON DELETE CASCADE")
            except Exception:
                pass
        if "workspace_id" not in exp_columns:
            try:
                connection.execute("ALTER TABLE experiments ADD COLUMN workspace_id TEXT REFERENCES workspaces(id) ON DELETE SET NULL")
            except Exception:
                pass
        connection.execute("CREATE INDEX IF NOT EXISTS idx_experiments_user ON experiments(user_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_experiments_workspace ON experiments(workspace_id)")

    saved_table = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='saved_papers'").fetchone()
    if saved_table:
        connection.execute("CREATE INDEX IF NOT EXISTS idx_saved_papers_user ON saved_papers(user_id)")

    # 9. Safe backfill for existing users in `users` table
    _backfill_existing_users(connection)


def _backfill_existing_users(connection: sqlite3.Connection) -> None:
    """Idempotently backfill default workspace, integrations, and initial records for existing users."""
    try:
        user_rows = connection.execute("SELECT id, email, name, created_at FROM users").fetchall()
    except Exception:
        return

    now_iso = datetime.now(timezone.utc).isoformat()
    for u in user_rows:
        uid = u["id"] if isinstance(u, (sqlite3.Row, dict)) else u[0]
        u_email = u["email"] if isinstance(u, (sqlite3.Row, dict)) else u[1]
        u_name = u["name"] if isinstance(u, (sqlite3.Row, dict)) else u[2]
        u_created = u["created_at"] if isinstance(u, (sqlite3.Row, dict)) else u[3]

        # Fetch metadata row if present
        meta_row = connection.execute(
            "SELECT workspace_details_json, personalization_memory_json, security_privacy_json FROM user_metadata WHERE user_id=?",
            (uid,)
        ).fetchone()
        w_json = {}
        pers_json = {}
        sec_json = {}
        if meta_row:
            raw_w = meta_row["workspace_details_json"] if isinstance(meta_row, (sqlite3.Row, dict)) else meta_row[0]
            raw_p = meta_row["personalization_memory_json"] if isinstance(meta_row, (sqlite3.Row, dict)) else meta_row[1]
            raw_s = meta_row["security_privacy_json"] if isinstance(meta_row, (sqlite3.Row, dict)) else meta_row[2]
            try:
                w_json = json.loads(raw_w or "{}")
            except Exception:
                pass
            try:
                pers_json = json.loads(raw_p or "{}")
            except Exception:
                pass
            try:
                sec_json = json.loads(raw_s or "{}")
            except Exception:
                pass

        # 1. Backfill workspace
        existing_ws = connection.execute("SELECT id FROM workspaces WHERE owner_id=?", (uid,)).fetchone()
        ws_id = existing_ws[0] if existing_ws else (w_json.get("default_workspace_id") or f"ws_{uid[:8]}")
        ws_name = w_json.get("workspace_name") or f"{u_name or 'Researcher'}'s Primary Lab"
        ws_repo = w_json.get("default_repository") or "aster-research-workspace"
        ws_site = w_json.get("workspace_site") or "local.aster.internal"
        ws_privacy = w_json.get("workspace_privacy") or "Private (Local SQLite)"
        ws_notif = w_json.get("workspace_notification_settings") or "All activity"
        ws_created = w_json.get("workspace_creation_date") or u_created or now_iso

        if not existing_ws:
            connection.execute("""
                INSERT OR IGNORE INTO workspaces (id, owner_id, name, site, default_repository, privacy, notification_settings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ws_id, uid, ws_name, ws_site, ws_repo, ws_privacy, ws_notif, ws_created, now_iso))
            connection.execute("""
                INSERT OR IGNORE INTO workspace_members (workspace_id, user_id, role, joined_at)
                VALUES (?, ?, 'Owner', ?)
            """, (ws_id, uid, ws_created))

        # 2. Backfill integrations
        for provider, default_status in [
            ("git_local", "connected"),
            ("wispr_voice", "connected"),
            ("zotero", "disconnected"),
            ("github", "disconnected"),
            ("mendeley", "disconnected"),
            ("huggingface", "disconnected"),
            ("wandb", "disconnected"),
            ("overleaf", "disconnected"),
        ]:
            connection.execute("""
                INSERT OR IGNORE INTO user_integrations (id, user_id, provider, status, account_identifier, config_json, scopes_json, connected_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, '{}', '[]', ?, ?, ?)
            """, (str(uuid4()), uid, provider, default_status, "local" if default_status == "connected" else "", now_iso if default_status == "connected" else None, now_iso, now_iso))

        # 3. Backfill consents
        audit_opt = 1 if sec_json.get("audit_logging_enabled", True) else 0
        telem_opt = 1 if sec_json.get("telemetry_opt_in", False) else 0
        connection.execute("""
            INSERT OR IGNORE INTO user_consents (id, user_id, consent_type, granted, policy_version, created_at)
            VALUES (?, ?, 'audit_logging', ?, '1.0', ?)
        """, (str(uuid4()), uid, audit_opt, now_iso))
        connection.execute("""
            INSERT OR IGNORE INTO user_consents (id, user_id, consent_type, granted, policy_version, created_at)
            VALUES (?, ?, 'telemetry', ?, '1.0', ?)
        """, (str(uuid4()), uid, telem_opt, now_iso))

        # 4. Backfill initial audit event
        existing_log = connection.execute("SELECT id FROM user_audit_logs WHERE user_id=? LIMIT 1", (uid,)).fetchone()
        if not existing_log:
            connection.execute("""
                INSERT INTO user_audit_logs (id, user_id, event_type, severity, details, created_at)
                VALUES (?, ?, 'system_migration', 'info', 'Schema version 2 migration applied and relational structures initialized.', ?)
            """, (str(uuid4()), uid, now_iso))

        # 5. Backfill saved prompts from personalization_memory_json if present
        prompts = pers_json.get("build_prompts") or []
        if isinstance(prompts, list):
            for idx, p in enumerate(prompts):
                p_text = str(p).strip()
                if p_text:
                    p_title = p_text[:40].replace("\n", " ")
                    if len(p_text) > 40:
                        p_title += "..."
                    connection.execute("""
                        INSERT OR IGNORE INTO user_saved_prompts (id, user_id, title, prompt_template, task_domain, is_pinned, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'general', 0, ?, ?)
                    """, (str(uuid4()), uid, p_title, p_text, now_iso, now_iso))


def run_schema_migrations(connection: sqlite3.Connection) -> int:
    """Execute all pending schema migrations idempotently in transaction."""
    ensure_foreign_keys(connection)

    connection.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        applied_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS app_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""")

    applied = {row[0] for row in connection.execute("SELECT version FROM schema_migrations").fetchall()}

    if 1 not in applied:
        with connection:
            _apply_migration_v1(connection)
            now_iso = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (1, "base_metadata_schema", now_iso)
            )
            connection.execute(
                "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('schema_version', '1')"
            )
        applied.add(1)

    if 2 not in applied:
        with connection:
            _apply_migration_v2(connection)
            now_iso = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (2, "relational_user_extensions", now_iso)
            )
            connection.execute(
                "INSERT OR REPLACE INTO app_meta (key, value) VALUES ('schema_version', '2')"
            )
        applied.add(2)

    return max(applied) if applied else 2


def init_user_metadata_table(connection: sqlite3.Connection) -> None:
    """Initialize or migrate user metadata persistence and relational extensions."""
    run_schema_migrations(connection)


# ==============================================================================
# Relational Extensions Management APIs
# ==============================================================================
def list_user_saved_prompts(
    connection: sqlite3.Connection,
    user_id: str,
    task_domain: str | None = None,
) -> list[dict[str, Any]]:
    """List all saved prompts for a user, ordered by pinned status and updated time."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    if task_domain:
        rows = connection.execute(
            """SELECT * FROM user_saved_prompts
               WHERE user_id=? AND (task_domain=? OR task_domain='general')
               ORDER BY is_pinned DESC, updated_at DESC""",
            (user_id, task_domain)
        ).fetchall()
    else:
        rows = connection.execute(
            """SELECT * FROM user_saved_prompts
               WHERE user_id=?
               ORDER BY is_pinned DESC, updated_at DESC""",
            (user_id,)
        ).fetchall()
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["tags"] = json.loads(item["tags_json"] or "[]")
        except Exception:
            item["tags"] = []
        item["is_pinned"] = bool(item["is_pinned"])
        results.append(item)
    return results


def create_or_update_saved_prompt(
    connection: sqlite3.Connection,
    user_id: str,
    title: str,
    prompt_template: str,
    task_domain: str = "general",
    tags: list[str] | None = None,
    is_pinned: bool = False,
    prompt_id: str | None = None,
) -> dict[str, Any]:
    """Create or update a user saved prompt with validation."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)

    title_clean = title.strip()[:120]
    template_clean = prompt_template.strip()
    if not title_clean:
        raise ValueError("Prompt title must not be empty.")
    if not template_clean:
        raise ValueError("Prompt template must not be empty.")

    tags_clean = [str(t).strip()[:50] for t in (tags or []) if str(t).strip()]
    now_iso = datetime.now(timezone.utc).isoformat()
    pid = prompt_id or str(uuid4())

    with connection:
        connection.execute("""
            INSERT INTO user_saved_prompts (
                id, user_id, title, prompt_template, task_domain, tags_json, is_pinned, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, title) DO UPDATE SET
                prompt_template=excluded.prompt_template,
                task_domain=excluded.task_domain,
                tags_json=excluded.tags_json,
                is_pinned=excluded.is_pinned,
                updated_at=excluded.updated_at
        """, (
            pid, user_id, title_clean, template_clean, task_domain,
            json.dumps(tags_clean), 1 if is_pinned else 0, now_iso, now_iso
        ))

        # Synchronize into personalization_memory_json for backward compatibility
        try:
            meta = get_user_metadata(connection, user_id)
            pers_mem = meta.get("personalization_memory", {})
            build_list = pers_mem.get("build_prompts", [])
            if isinstance(build_list, list):
                if template_clean not in build_list:
                    build_list.insert(0, template_clean)
                    pers_mem["build_prompts"] = build_list[:10]
                    save_user_metadata(connection, user_id, meta, is_admin=True)
        except Exception:
            pass

    return {
        "id": pid,
        "user_id": user_id,
        "title": title_clean,
        "prompt_template": template_clean,
        "task_domain": task_domain,
        "tags": tags_clean,
        "is_pinned": is_pinned,
        "updated_at": now_iso,
    }


def delete_saved_prompt(connection: sqlite3.Connection, user_id: str, prompt_id: str) -> bool:
    """Delete a user saved prompt by ID."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    with connection:
        cursor = connection.execute(
            "DELETE FROM user_saved_prompts WHERE id=? AND user_id=?",
            (prompt_id, user_id)
        )
        return cursor.rowcount > 0


def record_user_consent(
    connection: sqlite3.Connection,
    user_id: str,
    consent_type: str,
    granted: bool,
    policy_version: str = "1.0",
    ip_address: str = "",
    user_agent: str = "",
) -> dict[str, Any]:
    """Record an immutable consent event in the consent history ledger."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    cid = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute("""
            INSERT INTO user_consents (
                id, user_id, consent_type, granted, policy_version, ip_address, user_agent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cid, user_id, consent_type, 1 if granted else 0, policy_version, ip_address[:45], user_agent[:250], now_iso))

        # Sync with security_privacy in user_metadata
        try:
            meta = get_user_metadata(connection, user_id)
            sec = meta.get("security_privacy", {})
            if consent_type == "telemetry":
                sec["telemetry_opt_in"] = granted
            elif consent_type == "audit_logging":
                sec["audit_logging_enabled"] = granted
            elif consent_type == "analytics":
                sec["analytics_consent"] = granted
            elif consent_type == "marketing":
                sec["marketing_consent"] = granted
            elif consent_type == "data_processing":
                sec["data_processing_consent"] = granted
            save_user_metadata(connection, user_id, meta, is_admin=True)
        except Exception:
            pass

    log_user_security_event(
        connection, user_id, "consent_update",
        f"Consent for '{consent_type}' set to {'granted' if granted else 'revoked'} (policy {policy_version}).",
        "info", ip_address=ip_address, user_agent=user_agent
    )

    return {
        "id": cid,
        "user_id": user_id,
        "consent_type": consent_type,
        "granted": granted,
        "policy_version": policy_version,
        "created_at": now_iso,
    }


def get_user_consent_history(
    connection: sqlite3.Connection,
    user_id: str,
    consent_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve chronological audit trail of consent events for compliance."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    if consent_type:
        rows = connection.execute(
            """SELECT * FROM user_consents
               WHERE user_id=? AND consent_type=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, consent_type, limit)
        ).fetchall()
    else:
        rows = connection.execute(
            """SELECT * FROM user_consents
               WHERE user_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    return [{
        "id": r["id"],
        "user_id": r["user_id"],
        "consent_type": r["consent_type"],
        "granted": bool(r["granted"]),
        "policy_version": r["policy_version"],
        "ip_address": r["ip_address"],
        "created_at": r["created_at"],
    } for r in rows]


def list_user_integrations(connection: sqlite3.Connection, user_id: str) -> list[dict[str, Any]]:
    """List all registered external and local integrations for a user."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    rows = connection.execute(
        "SELECT * FROM user_integrations WHERE user_id=? ORDER BY provider ASC",
        (user_id,)
    ).fetchall()
    results = []
    for r in rows:
        item = dict(r)
        try:
            item["config"] = json.loads(item["config_json"] or "{}")
        except Exception:
            item["config"] = {}
        try:
            item["scopes"] = json.loads(item["scopes_json"] or "[]")
        except Exception:
            item["scopes"] = []
        # Redact any accidental tokens in response
        for k in list(item["config"].keys()):
            if any(s in k.lower() for s in ("token", "secret", "password", "key")):
                item["config"][k] = "REDACTED"
        results.append(item)
    return results


def set_user_integration(
    connection: sqlite3.Connection,
    user_id: str,
    provider: str,
    status: str,
    account_identifier: str = "",
    config: dict[str, Any] | None = None,
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Register or update an integration connection status without storing plaintext secrets."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)

    safe_config = dict(config or {})
    # Strip any plaintext credentials from config
    for k in list(safe_config.keys()):
        if any(s in k.lower() for s in ("password", "secret", "token", "raw_key")):
            safe_config.pop(k, None)

    now_iso = datetime.now(timezone.utc).isoformat()
    pid = str(uuid4())
    with connection:
        connection.execute("""
            INSERT INTO user_integrations (
                id, user_id, provider, status, account_identifier, config_json, scopes_json, connected_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, provider) DO UPDATE SET
                status=excluded.status,
                account_identifier=excluded.account_identifier,
                config_json=excluded.config_json,
                scopes_json=excluded.scopes_json,
                connected_at=CASE WHEN excluded.status='connected' THEN ? ELSE user_integrations.connected_at END,
                updated_at=excluded.updated_at
        """, (
            pid, user_id, provider, status, account_identifier[:150],
            json.dumps(safe_config), json.dumps(scopes or []),
            now_iso if status == "connected" else None, now_iso, now_iso, now_iso
        ))

    log_user_security_event(
        connection, user_id, "integration_updated",
        f"Integration '{provider}' status updated to '{status}'.", "info"
    )

    return {
        "user_id": user_id,
        "provider": provider,
        "status": status,
        "account_identifier": account_identifier,
        "updated_at": now_iso,
    }


def disconnect_user_integration(connection: sqlite3.Connection, user_id: str, provider: str) -> bool:
    """Disconnect an integration provider."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    now_iso = datetime.now(timezone.utc).isoformat()
    with connection:
        cursor = connection.execute(
            """UPDATE user_integrations
               SET status='disconnected', account_identifier='', updated_at=?
               WHERE user_id=? AND provider=?""",
            (now_iso, user_id, provider)
        )
        if cursor.rowcount > 0:
            log_user_security_event(
                connection, user_id, "integration_disconnected",
                f"Integration '{provider}' was disconnected.", "warning"
            )
            return True
        return False


def log_user_security_event(
    connection: sqlite3.Connection,
    user_id: str,
    event_type: str,
    details: str = "",
    severity: str = "info",
    ip_address: str = "",
    user_agent: str = "",
) -> dict[str, Any]:
    """Append a security or operational event to the user's relational audit log."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)

    eid = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute("""
            INSERT INTO user_audit_logs (
                id, user_id, event_type, severity, details, ip_address, user_agent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (eid, user_id, event_type[:50], severity[:20], details[:500], ip_address[:45], user_agent[:250], now_iso))

    return {
        "id": eid,
        "user_id": user_id,
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "created_at": now_iso,
    }


def get_user_security_events(
    connection: sqlite3.Connection,
    user_id: str,
    limit: int = 50,
    severity: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve security audit logs for a user with optional severity filtering."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    if severity:
        rows = connection.execute(
            """SELECT * FROM user_audit_logs
               WHERE user_id=? AND severity=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, severity, limit)
        ).fetchall()
    else:
        rows = connection.execute(
            """SELECT * FROM user_audit_logs
               WHERE user_id=?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def prune_audit_logs_by_retention(connection: sqlite3.Connection, retention_days: int) -> int:
    """Prune audit logs older than the specified retention window in days."""
    ensure_foreign_keys(connection)
    if retention_days <= 0:
        return 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with connection:
        cursor = connection.execute("DELETE FROM user_audit_logs WHERE created_at < ?", (cutoff,))
        return cursor.rowcount


def create_privacy_request(
    connection: sqlite3.Connection,
    user_id: str,
    request_type: str,
    status: str = "pending",
    format: str = "json",
    details: str = "",
) -> dict[str, Any]:
    """Create a tracked GDPR privacy lifecycle request (export or erasure)."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    rid = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute("""
            INSERT INTO user_privacy_requests (
                id, user_id, request_type, status, format, details, requested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (rid, user_id, request_type[:30], status[:30], format[:20], details[:500], now_iso))
    return {
        "id": rid,
        "user_id": user_id,
        "request_type": request_type,
        "status": status,
        "format": format,
        "requested_at": now_iso,
    }


def get_user_privacy_requests(connection: sqlite3.Connection, user_id: str) -> list[dict[str, Any]]:
    """Get all privacy requests for a user."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    rows = connection.execute(
        "SELECT * FROM user_privacy_requests WHERE user_id=? ORDER BY requested_at DESC",
        (user_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_user_workspaces(connection: sqlite3.Connection, user_id: str) -> list[dict[str, Any]]:
    """Retrieve all workspaces owned by or joined by the user."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    rows = connection.execute("""
        SELECT w.*, wm.role as member_role,
               (SELECT COUNT(*) FROM workspace_members WHERE workspace_id=w.id) as collaborator_count
        FROM workspaces w
        JOIN workspace_members wm ON w.id = wm.workspace_id
        WHERE wm.user_id=?
        ORDER BY w.created_at ASC
    """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def create_user_workspace(
    connection: sqlite3.Connection,
    owner_id: str,
    name: str,
    site: str = "local.aster.internal",
    default_repository: str = "aster-research-workspace",
    privacy: str = "Private (Local SQLite)",
    notification_settings: str = "All activity",
) -> dict[str, Any]:
    """Create a new workspace and register the owner membership."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    ws_id = f"ws_{owner_id[:8]}_{uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    with connection:
        connection.execute("""
            INSERT INTO workspaces (
                id, owner_id, name, site, default_repository, privacy, notification_settings, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ws_id, owner_id, name.strip()[:100], site.strip()[:100], default_repository.strip()[:120], privacy, notification_settings, now_iso, now_iso))
        connection.execute("""
            INSERT INTO workspace_members (workspace_id, user_id, role, joined_at)
            VALUES (?, ?, 'Owner', ?)
        """, (ws_id, owner_id, now_iso))
    return {
        "id": ws_id,
        "owner_id": owner_id,
        "name": name,
        "site": site,
        "default_repository": default_repository,
        "privacy": privacy,
        "created_at": now_iso,
    }


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
        "total_projects_created": 0,
        "total_research_sessions": 1,
        "total_ai_requests": 0,
        "monthly_ai_usage": 0,
        "feature_usage_summary": {
            "voice_notes": 0,
            "structuring": 0,
            "diagrams": 0,
            "comparisons": 0,
            "paper_radar": 0,
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
        u_act["total_projects_created"] = int(exp_count or 0)
    except Exception:
        pass

    # Enrich from relational extensions if present
    try:
        ws_row = connection.execute("SELECT * FROM workspaces WHERE owner_id=? LIMIT 1", (user_id,)).fetchone()
        if ws_row:
            w_details["default_workspace_id"] = ws_row["id"]
            w_details["workspace_name"] = ws_row["name"]
            w_details["workspace_site"] = ws_row["site"]
            w_details["default_repository"] = ws_row["default_repository"]
            w_details["workspace_notification_settings"] = ws_row["notification_settings"]
            w_details["workspace_access_permissions"] = ws_row["privacy"]
    except Exception:
        pass

    try:
        audit_rows = connection.execute(
            "SELECT * FROM user_audit_logs WHERE user_id=? ORDER BY created_at DESC LIMIT 15",
            (user_id,)
        ).fetchall()
        if audit_rows:
            sec_priv["recent_security_events"] = [
                f"{r['created_at']} - [{r['event_type']}] {r['details']}" for r in audit_rows
            ]
    except Exception:
        pass

    try:
        prompt_rows = connection.execute(
            "SELECT prompt_template FROM user_saved_prompts WHERE user_id=? ORDER BY is_pinned DESC, updated_at DESC LIMIT 10",
            (user_id,)
        ).fetchall()
        if prompt_rows:
            pers_mem["build_prompts"] = [r["prompt_template"] for r in prompt_rows]
    except Exception:
        pass

    try:
        integ_rows = connection.execute(
            "SELECT provider, status FROM user_integrations WHERE user_id=?",
            (user_id,)
        ).fetchall()
        for ir in integ_rows:
            p_key = f"{ir['provider']}_status"
            if p_key in integ:
                integ[p_key] = ir["status"].capitalize()
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
# Helpers & Server-Side Validation / Authorization
# ==============================================================================
def format_user_datetime(dt_val: Any, format_pref: str = "YYYY-MM-DD HH:mm") -> str:
    """Format datetime string or object according to user date_time_format preference."""
    if not dt_val:
        return ""
    if isinstance(dt_val, str):
        try:
            clean_str = dt_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_str)
        except Exception:
            return str(dt_val)
    elif isinstance(dt_val, datetime):
        dt = dt_val
    else:
        return str(dt_val)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()

    if format_pref == "DD/MM/YYYY HH:mm":
        return local_dt.strftime("%d/%m/%Y %H:%M")
    elif format_pref == "MMM D, YYYY h:mm A":
        return local_dt.strftime("%b %d, %Y %I:%M %p")
    elif format_pref == "YYYY-MM-DD":
        return local_dt.strftime("%Y-%m-%d")
    else:  # "YYYY-MM-DD HH:mm"
        return local_dt.strftime("%Y-%m-%d %H:%M")


def validate_and_sanitize_metadata(
    metadata_bundle: dict[str, Any],
    existing_metadata: dict[str, Any] | None = None,
    is_admin: bool = False,
) -> dict[str, Any]:
    """Server-side validation and authorization enforcement for user metadata.
    
    Prevents unauthorized privilege escalation (account_role, account_status, internal_flags),
    sanitizes input lengths and types, validates ISO dates, and guards against secret leakage.
    """
    clean_bundle: dict[str, Any] = {}
    existing = existing_metadata or {}
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Personal Details
    raw_p = metadata_bundle.get("personal_details", {})
    exist_p = existing.get("personal_details", {})
    clean_full_name = str(raw_p.get("full_name") or exist_p.get("full_name") or "").strip()[:120]
    
    # Username: lowercase alphanumeric with underscores/hyphens, 2-40 chars
    raw_uname = str(raw_p.get("username") or exist_p.get("username") or "researcher").strip().lower()
    clean_uname = "".join(c for c in raw_uname if c.isalnum() or c in ("_", "-", "."))[:40] or "researcher"

    # Profile picture URL or data URI
    clean_avatar = str(raw_p.get("profile_picture") or "").strip()
    if clean_avatar and not (clean_avatar.startswith("http://") or clean_avatar.startswith("https://") or clean_avatar.startswith("data:image/")):
        clean_avatar = ""

    # DOB validation
    clean_dob = str(raw_p.get("date_of_birth") or "").strip()
    if clean_dob:
        try:
            datetime.fromisoformat(clean_dob[:10])
            clean_dob = clean_dob[:10]
        except Exception:
            clean_dob = exist_p.get("date_of_birth", "")

    clean_bundle["personal_details"] = {
        "user_id": exist_p.get("user_id") or raw_p.get("user_id", ""),
        "full_name": clean_full_name,
        "username": clean_uname,
        "email": exist_p.get("email") or raw_p.get("email", ""),
        "phone_number": str(raw_p.get("phone_number") or "").strip()[:30],
        "profile_picture": clean_avatar,
        "bio": str(raw_p.get("bio") or "").strip()[:1500],
        "date_of_birth": clean_dob,
        "country": str(raw_p.get("country") or "United States").strip()[:100],
        "state_region": str(raw_p.get("state_region") or "").strip()[:100],
        "city": str(raw_p.get("city") or "").strip()[:100],
        "timezone": str(raw_p.get("timezone") or "UTC").strip()[:60],
        "preferred_language": str(raw_p.get("preferred_language") or "English (US)").strip()[:60],
        "created_at": exist_p.get("created_at") or raw_p.get("created_at") or now_iso,
    }

    # 2. Account Details (Protected authorization boundary)
    raw_a = metadata_bundle.get("account_details", {})
    exist_a = existing.get("account_details", {})
    if is_admin:
        role = str(raw_a.get("account_role") or exist_a.get("account_role") or "Research Scientist").strip()[:60]
        status = str(raw_a.get("account_status") or exist_a.get("account_status") or "Active").strip()[:60]
    else:
        role = exist_a.get("account_role", "Research Scientist")
        status = exist_a.get("account_status", "Active")

    clean_bundle["account_details"] = {
        "account_status": status,
        "account_role": role,
        "email_verified": bool(exist_a.get("email_verified", raw_a.get("email_verified", False))),
        "phone_verified": bool(exist_a.get("phone_verified", False)),
        "last_login_at": str(exist_a.get("last_login_at") or raw_a.get("last_login_at") or now_iso),
        "last_password_changed_at": str(exist_a.get("last_password_changed_at") or raw_a.get("last_password_changed_at") or ""),
        "auth_provider": exist_a.get("auth_provider") or raw_a.get("auth_provider", "Email OTP"),
        "mfa_enabled": bool(exist_a.get("mfa_enabled", False)),
    }

    # 3. User Preferences
    raw_u = metadata_bundle.get("user_preferences", {})
    theme = raw_u.get("theme") if raw_u.get("theme") in ALLOWED_THEMES else "Obsidian Dark (Default)"
    accent = raw_u.get("accent_colour") if raw_u.get("accent_colour") in ALLOWED_ACCENTS else "Aster Orange (#f18a5e)"
    density = raw_u.get("text_density") if raw_u.get("text_density") in ALLOWED_DENSITIES else "Comfortable"
    font = raw_u.get("font_size_preference") if raw_u.get("font_size_preference") in ALLOWED_FONTS else "Standard (16px)"
    layout = raw_u.get("dashboard_layout_preference") if raw_u.get("dashboard_layout_preference") in ALLOWED_LAYOUTS else "Split Workflow"
    landing = raw_u.get("default_landing_page") if raw_u.get("default_landing_page") in ALLOWED_LANDING_PAGES else "Home"
    dt_fmt = raw_u.get("date_time_format") if raw_u.get("date_time_format") in ALLOWED_DT_FORMATS else "YYYY-MM-DD HH:mm"
    units = raw_u.get("preferred_units") if raw_u.get("preferred_units") in ALLOWED_UNITS else "Metric (SI)"

    raw_notif = raw_u.get("notification_preferences") or {}
    clean_notif = {
        "in_app": bool(raw_notif.get("in_app", True)),
        "experiment_run_alerts": bool(raw_notif.get("experiment_run_alerts", True)),
        "weekly_summary": bool(raw_notif.get("weekly_summary", True)),
    }

    raw_acc = raw_u.get("accessibility_preferences") or {}
    clean_acc = {
        "high_contrast": bool(raw_acc.get("high_contrast", False)),
        "screen_reader_optimizations": bool(raw_acc.get("screen_reader_optimizations", False)),
        "underline_links": bool(raw_acc.get("underline_links", False)),
    }

    clean_bundle["user_preferences"] = {
        "theme": theme,
        "accent_colour": accent,
        "text_density": density,
        "font_size_preference": font,
        "reduced_motion_preference": bool(raw_u.get("reduced_motion_preference", False)),
        "dashboard_layout_preference": layout,
        "default_landing_page": landing,
        "notification_preferences": clean_notif,
        "email_update_preferences": bool(raw_u.get("email_update_preferences", True)),
        "date_time_format": dt_fmt,
        "preferred_units": units,
        "accessibility_preferences": clean_acc,
    }

    # 4. AI Preferences
    raw_ai = metadata_bundle.get("ai_preferences", {})
    provider = raw_ai.get("preferred_ai_provider") if raw_ai.get("preferred_ai_provider") in ALLOWED_AI_PROVIDERS else "Google Gemini"
    model = str(raw_ai.get("preferred_ai_model") or "gemini-2.0-flash").strip()[:60]
    r_model = str(raw_ai.get("default_model_research") or "gemini-2.0-flash").strip()[:60]
    c_model = str(raw_ai.get("default_model_coding") or "gemini-2.0-flash").strip()[:60]
    a_model = str(raw_ai.get("default_model_analysis") or "gemini-2.0-flash").strip()[:60]
    
    speed = raw_ai.get("response_time_preference") if raw_ai.get("response_time_preference") in ALLOWED_SPEEDS else "Fast (Low latency)"
    length = raw_ai.get("response_length_preference") if raw_ai.get("response_length_preference") in ALLOWED_LENGTHS else "Balanced"
    reasoning = raw_ai.get("reasoning_detail_preference") if raw_ai.get("reasoning_detail_preference") in ALLOWED_REASONINGS else "High (Step-by-step)"
    window = raw_ai.get("default_context_window_preference") if raw_ai.get("default_context_window_preference") in ALLOWED_WINDOWS else "Standard (32k)"

    try:
        temp = max(0.0, min(1.0, float(raw_ai.get("default_temperature", 0.20))))
    except Exception:
        temp = 0.20

    try:
        limit = max(100, min(100000, int(raw_ai.get("ai_usage_limits", 1000))))
    except Exception:
        limit = 1000

    clean_bundle["ai_preferences"] = {
        "preferred_ai_provider": provider,
        "preferred_ai_model": model,
        "user_provided_api_key_status": bool(raw_ai.get("user_provided_api_key_status", False)),
        "default_model_research": r_model,
        "default_model_coding": c_model,
        "default_model_analysis": a_model,
        "response_time_preference": speed,
        "response_length_preference": length,
        "reasoning_detail_preference": reasoning,
        "default_temperature": temp,
        "model_fallback_preference": bool(raw_ai.get("model_fallback_preference", True)),
        "ai_usage_limits": limit,
        "default_context_window_preference": window,
    }

    # 5. Research Profile
    raw_rp = metadata_bundle.get("research_profile", {})
    interests = [str(t).strip()[:80] for t in raw_rp.get("research_interests", []) if str(t).strip()]
    sources = [str(s).strip()[:60] for s in raw_rp.get("frequently_used_ai_sources", []) if str(s).strip()]
    retention = raw_rp.get("research_history_retention_preference") if raw_rp.get("research_history_retention_preference") in ALLOWED_RETENTION_POLICIES else "Forever"

    clean_bundle["research_profile"] = {
        "research_interests": interests,
        "area_of_expertise": str(raw_rp.get("area_of_expertise") or "NLP & LLM Reasoning").strip()[:150],
        "professional_role": str(raw_rp.get("professional_role") or "Lead AI Researcher").strip()[:150],
        "industry": str(raw_rp.get("industry") or "Academic & Frontier Lab").strip()[:150],
        "technical_skills": str(raw_rp.get("technical_skills") or "").strip()[:500],
        "preferred_research_methodology": str(raw_rp.get("preferred_research_methodology") or "Empirical / Benchmarking").strip()[:100],
        "preferred_citation_style": str(raw_rp.get("preferred_citation_style") or "BibTeX").strip()[:50],
        "preferred_output_formats": str(raw_rp.get("preferred_output_formats") or "Markdown + LaTeX").strip()[:100],
        "frequently_used_ai_sources": sources or ["arXiv", "Hugging Face Daily Papers"],
        "research_history_retention_preference": retention,
        "save_research_instructions": bool(raw_rp.get("save_research_instructions", True)),
        "personal_knowledge_base_references": str(raw_rp.get("personal_knowledge_base_references") or "").strip()[:2000],
    }

    # 6. Workspace Details
    raw_w = metadata_bundle.get("workspace_details", {})
    exist_w = existing.get("workspace_details", {})
    repo_count_val = raw_w.get("connected_repository_count")
    if repo_count_val is None:
        repo_count_val = raw_w.get("connected_repo_count", 1)
    try:
        repo_count = max(0, min(100, int(repo_count_val)))
    except Exception:
        repo_count = 1

    clean_bundle["workspace_details"] = {
        "default_workspace_id": exist_w.get("default_workspace_id") or raw_w.get("default_workspace_id", ""),
        "workspace_name": str(raw_w.get("workspace_name") or "Aster Primary Lab").strip()[:100],
        "workspace_role": str(raw_w.get("workspace_role") or exist_w.get("workspace_role", "Owner")).strip()[:50],
        "workspace_site": str(raw_w.get("workspace_site") or "local.aster.internal").strip()[:100],
        "workspace_creation_date": exist_w.get("workspace_creation_date") or raw_w.get("workspace_creation_date", ""),
        "default_project_id": str(raw_w.get("default_project_id") or exist_w.get("default_project_id", "proj_default")).strip()[:50],
        "preferred_project_template": str(raw_w.get("preferred_project_template") or "Standard LLM Benchmark").strip()[:100],
        "default_repository": str(raw_w.get("default_repository") or "aster-research-workspace").strip()[:120],
        "repository_provider": str(raw_w.get("repository_provider") or "GitHub").strip()[:50],
        "connected_repository_count": repo_count,
        "connected_repo_count": repo_count,
        "workspace_notification_settings": str(raw_w.get("workspace_notification_settings") or "All activity").strip()[:60],
        "workspace_access_permissions": str(raw_w.get("workspace_access_permissions") or "Private (Isolated)").strip()[:60],
    }

    # 7. Integrations (Distinguish genuine local from placeholder / external)
    raw_i = metadata_bundle.get("integrations", {})
    cloud_providers = [str(p).strip() for p in raw_i.get("connected_cloud_storage_providers", ["Local Disk"]) if str(p).strip()]
    integ_list = [str(item).strip() for item in raw_i.get("connected_integration_list", []) if str(item).strip()]
    if not integ_list:
        integ_list = ["Local SQLite Journal", "Wispr Flow Voice Dictation"]

    clean_bundle["integrations"] = {
        "github_connection_status": bool(raw_i.get("github_connection_status", False)),
        "gitlab_connection_status": bool(raw_i.get("gitlab_connection_status", False)),
        "connected_google_account_status": bool(raw_i.get("connected_google_account_status", False)),
        "connected_cloud_storage_providers": cloud_providers or ["Local Disk"],
        "connected_integration_list": integ_list,
        "oauth_connection_identifiers": {str(k)[:50]: str(v)[:100] for k, v in (raw_i.get("oauth_connection_identifiers") or {}).items()},
        "integration_permission_timestamps": {str(k)[:50]: str(v)[:50] for k, v in (raw_i.get("integration_permission_timestamps") or {}).items()},
        "integration_synchronisation_preferences": str(raw_i.get("integration_synchronisation_preferences") or "Real-time auto-sync").strip()[:60],
    }

    # 8. Usage & Activity
    raw_ua = metadata_bundle.get("usage_activity", {})
    exist_ua = existing.get("usage_activity", {})
    features = raw_ua.get("feature_usage_summary") or exist_ua.get("feature_usage_summary") or {}
    clean_features = {
        "voice_notes": int(features.get("voice_notes", 0)),
        "structuring": int(features.get("structuring", 0)),
        "diagrams": int(features.get("diagrams", 0)),
        "comparisons": int(features.get("comparisons", 0)),
        "paper_radar": int(features.get("paper_radar", 0)),
    }

    clean_bundle["usage_activity"] = {
        "last_active_timestamp": str(raw_ua.get("last_active_timestamp") or exist_ua.get("last_active_timestamp") or now_iso),
        "total_projects_created": int(raw_ua.get("total_projects_created", exist_ua.get("total_projects_created", 0))),
        "total_research_sessions": max(1, int(raw_ua.get("total_research_sessions", exist_ua.get("total_research_sessions", 1)))),
        "total_ai_requests": int(raw_ua.get("total_ai_requests", exist_ua.get("total_ai_requests", 0))),
        "monthly_ai_usage": int(raw_ua.get("monthly_ai_usage", exist_ua.get("monthly_ai_usage", 0))),
        "feature_usage_summary": clean_features,
        "onboarding_completion_status": bool(raw_ua.get("onboarding_completion_status", exist_ua.get("onboarding_completion_status", False))),
        "last_onboarding_step": str(raw_ua.get("last_onboarding_step") or exist_ua.get("last_onboarding_step") or "Pending interest tags").strip()[:100],
        "recent_workspace_id": str(raw_ua.get("recent_workspace_id") or exist_ua.get("recent_workspace_id") or "ws_primary").strip()[:50],
        "product_engagement_summary": str(raw_ua.get("product_engagement_summary") or "Active Daily Researcher").strip()[:100],
    }

    # 9. Security & Privacy
    raw_sp = metadata_bundle.get("security_privacy", {})
    exist_sp = existing.get("security_privacy", {})
    priv_mode = raw_sp.get("privacy_preferences") if raw_sp.get("privacy_preferences") in ALLOWED_PRIVACY_MODES else "Strict Local (Zero external telemetry)"
    ret_pref = raw_sp.get("data_retention_preference") if raw_sp.get("data_retention_preference") in ALLOWED_RETENTION_POLICIES else "Retain until manual deletion"

    clean_bundle["security_privacy"] = {
        "analytics_consent": bool(raw_sp.get("analytics_consent", True)),
        "marketing_consent": bool(raw_sp.get("marketing_consent", False)),
        "data_processing_consent": bool(raw_sp.get("data_processing_consent", True)),
        "consent_timestamps": {
            "data_processing": str(raw_sp.get("consent_timestamps", {}).get("data_processing") or now_iso),
            "analytics": str(raw_sp.get("consent_timestamps", {}).get("analytics") or now_iso),
            "marketing": str(raw_sp.get("consent_timestamps", {}).get("marketing") or now_iso),
        },
        "privacy_preferences": priv_mode,
        "data_retention_preference": ret_pref,
        "active_session_count": max(1, int(raw_sp.get("active_session_count", exist_sp.get("active_session_count", 1)))),
        "last_security_event": str(raw_sp.get("last_security_event") or exist_sp.get("last_security_event") or "Authenticated session verified via local machine").strip()[:200],
        "account_deletion_request_status": bool(raw_sp.get("account_deletion_request_status", False)),
        "data_export_request_status": bool(raw_sp.get("data_export_request_status", exist_sp.get("data_export_request_status", False))),
    }

    # 10. Personalization & Memory
    raw_pm = metadata_bundle.get("personalization_memory", {})
    clean_bundle["personalization_memory"] = {
        "saved_user_instructions": str(raw_pm.get("saved_user_instructions") or "").strip()[:2000],
        "preferred_working_style": str(raw_pm.get("preferred_working_style") or "Hypothesis-first").strip()[:100],
        "preferred_coding_conventions": str(raw_pm.get("preferred_coding_conventions") or "PEP 8 + Type Hints (Python)").strip()[:100],
        "preferred_communication_tone": str(raw_pm.get("preferred_communication_tone") or "Rigorous & Academic").strip()[:100],
        "frequently_used_ai_tools": [str(t).strip()[:60] for t in raw_pm.get("frequently_used_ai_tools", []) if str(t).strip()],
        "favourite_features": [str(f).strip()[:60] for f in raw_pm.get("favourite_features", []) if str(f).strip()],
        "spin_projects": str(raw_pm.get("spin_projects") or "").strip()[:200],
        "build_prompts": str(raw_pm.get("build_prompts") or "").strip()[:500],
        "custom_ai_instructions": str(raw_pm.get("custom_ai_instructions") or "").strip()[:2000],
        "personalization_settings": bool(raw_pm.get("personalization_settings", True)),
    }

    # 11. System Metadata (Protected internal flags)
    raw_sm = metadata_bundle.get("system_metadata", {})
    exist_sm = existing.get("system_metadata", {})
    if is_admin:
        flags = raw_sm.get("internal_flags") or exist_sm.get("internal_flags") or {}
    else:
        flags = exist_sm.get("internal_flags") or {
            "beta_features_enabled": True,
            "sandbox_mode": False,
            "fast_distillation": True,
        }

    clean_bundle["system_metadata"] = {
        "metadata_schema_version": METADATA_SCHEMA_VERSION,
        "record_creation_timestamp": exist_sm.get("record_creation_timestamp") or raw_sm.get("record_creation_timestamp") or now_iso,
        "record_update_timestamp": now_iso,
        "data_source_import_status": exist_sm.get("data_source_import_status") or "Synchronized with Aster SQLite v3.43",
        "migration_version": CURRENT_MIGRATION_VERSION,
        "custom_attributes": raw_sm.get("custom_attributes") if isinstance(raw_sm.get("custom_attributes"), dict) else {},
        "internal_flags": {
            "beta_features_enabled": bool(flags.get("beta_features_enabled", True)),
            "sandbox_mode": bool(flags.get("sandbox_mode", False)),
            "fast_distillation": bool(flags.get("fast_distillation", True)),
        },
    }

    return clean_bundle


# ==============================================================================
# User Metadata Persistence & Synchronization
# ==============================================================================
def save_user_metadata(
    connection: sqlite3.Connection,
    user_id: str,
    metadata_bundle: dict[str, Any],
    is_admin: bool = False,
) -> bool:
    """Save validated metadata dictionary to SQLite and sync with parent users table."""
    init_user_metadata_table(connection)

    # Fetch existing metadata to enforce authorization and immutability
    try:
        existing_meta = get_user_metadata(connection, user_id)
    except Exception:
        existing_meta = None

    # Server-side validation and authorization
    sanitized = validate_and_sanitize_metadata(metadata_bundle, existing_meta, is_admin=is_admin)

    p_details = sanitized["personal_details"]
    a_details = sanitized["account_details"]
    u_pref = sanitized["user_preferences"]
    ai_pref = sanitized["ai_preferences"]
    r_prof = sanitized["research_profile"]
    w_details = sanitized["workspace_details"]
    integ = sanitized["integrations"]
    u_act = sanitized["usage_activity"]
    sec_priv = sanitized["security_privacy"]
    pers_mem = sanitized["personalization_memory"]
    sys_meta = sanitized["system_metadata"]

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
        elif action_type in ("voice_notes", "structuring", "diagrams", "comparisons", "paper_radar"):
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
    """Generate dynamic CSS to apply user theme, accent colour, font size, density, and accessibility."""
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

    # Accessibility enhancements
    accessibility = preferences.get("accessibility_preferences") or {}
    acc_css = []
    if accessibility.get("high_contrast"):
        acc_css.append("""
        body, .stApp, p, span, h1, h2, h3, h4 { color: #ffffff !important; }
        .home-stat, .home-hero, div[data-testid="stExpander"], div[data-testid="stForm"], .card, .record-pane {
          border: 1px solid rgba(255, 255, 255, 0.45) !important;
        }
        """)
    if accessibility.get("underline_links"):
        acc_css.append("""
        a, .stMarkdown a { text-decoration: underline !important; font-weight: 550 !important; }
        """)
    if accessibility.get("screen_reader_optimizations"):
        acc_css.append(f"""
        :focus-visible {{ outline: 3px solid {accent_hex} !important; outline-offset: 3px !important; }}
        """)

    extra_acc_css = "\n".join(acc_css)

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
    .home-stat, div[data-testid="stExpander"], .home-empty, .record-pane, .card {{
      padding: {card_padding} !important;
    }}
    .button-primary, div[data-testid="stButton"]>button[kind="primary"] {{
      background: {accent_hex} !important;
      border-color: {accent_hover} !important;
    }}
    .button-primary:hover, div[data-testid="stButton"]>button[kind="primary"]:hover {{
      background: {accent_hover} !important;
    }}
    {motion_css}
    {extra_acc_css}
    </style>
    """


# ==============================================================================
# Complete Research & Metadata Data Export & Deletion
# ==============================================================================
def export_user_data_bundle(connection: sqlite3.Connection, user_id: str) -> str:
    """Generate comprehensive JSON archive for privacy compliance and backup."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    meta = get_user_metadata(connection, user_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Mark data export request status and timestamp
    try:
        meta["security_privacy"]["data_export_request_status"] = True
        meta["security_privacy"]["last_security_event"] = f"Exported complete research & metadata bundle on {now_iso[:10]}"
        save_user_metadata(connection, user_id, meta, is_admin=True)
    except Exception:
        pass

    # Record completed privacy request and audit log
    try:
        connection.execute("""
            INSERT INTO user_privacy_requests (
                id, user_id, request_type, status, format, details, requested_at, completed_at
            ) VALUES (?, ?, 'export', 'completed', 'json', 'User initiated full data bundle download', ?, ?)
        """, (str(uuid4()), user_id, now_iso, now_iso))
        connection.commit()
    except Exception:
        pass

    try:
        log_user_security_event(connection, user_id, "data_export", "Full GDPR JSON research archive downloaded", "info")
    except Exception:
        pass

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

    # Query relational user extensions
    workspaces: list[dict[str, Any]] = []
    try:
        rows = connection.execute("SELECT * FROM workspaces WHERE owner_id=?", (user_id,)).fetchall()
        workspaces = [dict(r) for r in rows]
    except Exception:
        pass

    saved_prompts: list[dict[str, Any]] = []
    try:
        saved_prompts = list_user_saved_prompts(connection, user_id)
    except Exception:
        pass

    consent_history: list[dict[str, Any]] = []
    try:
        consent_history = get_user_consent_history(connection, user_id)
    except Exception:
        pass

    integrations: list[dict[str, Any]] = []
    try:
        integrations = list_user_integrations(connection, user_id)
    except Exception:
        pass

    audit_logs: list[dict[str, Any]] = []
    try:
        audit_logs = get_user_security_events(connection, user_id, limit=100)
    except Exception:
        pass

    privacy_requests: list[dict[str, Any]] = []
    try:
        privacy_requests = get_user_privacy_requests(connection, user_id)
    except Exception:
        pass

    # Ensure no credentials or tokens are exported
    safe_meta = json.loads(json.dumps(meta))
    safe_meta["personal_details"].pop("password_hash", None)

    bundle = {
        "export_metadata": {
            "app": "Aster Research OS",
            "version": METADATA_SCHEMA_VERSION,
            "export_timestamp": now_iso,
            "user_id": user_id,
            "compliance": "GDPR Article 15/20 Data Portability Standard",
        },
        "user_profile_and_metadata": safe_meta,
        "workspaces": workspaces,
        "saved_prompts": saved_prompts,
        "consent_history": consent_history,
        "integrations": integrations,
        "audit_logs": audit_logs,
        "privacy_requests": privacy_requests,
        "experiments_count": len(experiments),
        "experiments": experiments,
        "research_contexts": contexts,
        "experiment_memories": memories,
    }
    return json.dumps(bundle, indent=2, ensure_ascii=False)


def delete_user_account(connection: sqlite3.Connection, user_id: str) -> bool:
    """Execute complete data erasure and account deletion for privacy sovereignty."""
    ensure_foreign_keys(connection)
    init_user_metadata_table(connection)
    try:
        with connection:
            for tbl, col in [
                ("saved_papers", "user_id"),
                ("experiments", "user_id"),
                ("user_saved_prompts", "user_id"),
                ("user_consents", "user_id"),
                ("user_integrations", "user_id"),
                ("user_audit_logs", "user_id"),
                ("user_privacy_requests", "user_id"),
                ("workspace_members", "user_id"),
                ("workspaces", "owner_id"),
                ("user_sessions", "user_id"),
                ("email_verifications", "user_id"),
                ("user_metadata", "user_id"),
                ("users", "id"),
            ]:
                try:
                    exists = connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
                    ).fetchone()
                    if exists:
                        connection.execute(f"DELETE FROM {tbl} WHERE {col}=?", (user_id,))
                except Exception:
                    pass
        return True
    except Exception as exc:
        print(f"[Error deleting user account]: {exc}")
        return False
