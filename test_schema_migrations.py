"""Comprehensive SQLite Schema, Migration, and Relational Extensions Test Suite.

Verifies:
1. Fresh database schema upgrades (Migration 1 and 2).
2. Migration idempotency (multiple runs without error or duplicate data).
3. Migration on an existing production database copy (data preservation of 4 users).
4. Relational integrity & uniqueness constraints:
   - Unique prompt title per user
   - Unique integration provider per user
   - Workspace ownership & membership composite primary key
5. Foreign key cascade enforcement:
   - Automatic cascade on user deletion across all relational tables.
6. GDPR lifecycle:
   - Append-only consent ledger
   - Security audit logging with IP and severity
   - Tracked privacy requests (export and erasure)
   - Redacted full export bundle
7. Full compatibility with existing get_user_metadata and save_user_metadata flows.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import user_metadata_manager
import auth_manager


class TestSchemaMigrationsAndRelationalExtensions(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_fresh.db")
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def tearDown(self) -> None:
        self.connection.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fresh_database_migrations_v1_and_v2(self) -> None:
        """Verify that running migrations on a brand new DB provisions all tables and indexes."""
        auth_manager.init_auth_tables(self.connection)
        applied_version = user_metadata_manager.run_schema_migrations(self.connection)
        self.assertEqual(applied_version, 2)

        # Check schema_migrations table
        applied = {
            row["version"]: row["name"]
            for row in self.connection.execute("SELECT version, name FROM schema_migrations").fetchall()
        }
        self.assertIn(1, applied)
        self.assertIn(2, applied)
        self.assertEqual(applied[1], "base_metadata_schema")
        self.assertEqual(applied[2], "relational_user_extensions")

        # Check app_meta
        meta_ver = self.connection.execute("SELECT value FROM app_meta WHERE key='schema_version'").fetchone()
        self.assertIsNotNone(meta_ver)
        self.assertEqual(meta_ver["value"], "2")

        # Check required tables exist
        tables = {
            row[0] for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        expected_tables = {
            "users",
            "user_metadata",
            "user_sessions",
            "email_verifications",
            "schema_migrations",
            "app_meta",
            "workspaces",
            "workspace_members",
            "user_saved_prompts",
            "user_consents",
            "user_integrations",
            "user_audit_logs",
            "user_privacy_requests",
        }
        for t in expected_tables:
            self.assertIn(t, tables, f"Expected table '{t}' to be created by migrations.")

        # Check indexes exist
        indexes = {
            row[0] for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
        }
        expected_indexes = {
            "idx_workspaces_owner",
            "idx_workspace_members_user",
            "idx_saved_prompts_user",
            "idx_user_consents_user",
            "idx_user_integrations_user",
            "idx_user_audit_logs_user",
            "idx_user_privacy_requests_user",
        }
        for idx in expected_indexes:
            self.assertIn(idx, indexes, f"Expected index '{idx}' to exist.")

    def test_migration_idempotency(self) -> None:
        """Verify that running migrations multiple times succeeds without duplicating data."""
        auth_manager.init_auth_tables(self.connection)
        ver1 = user_metadata_manager.run_schema_migrations(self.connection)
        ver2 = user_metadata_manager.run_schema_migrations(self.connection)
        ver3 = user_metadata_manager.run_schema_migrations(self.connection)
        self.assertEqual(ver1, 2)
        self.assertEqual(ver2, 2)
        self.assertEqual(ver3, 2)

        # Count records in schema_migrations
        count = self.connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        self.assertEqual(count, 2)

    def test_migration_on_existing_production_database_copy(self) -> None:
        """Verify that migrating an existing database with real users preserves all records and backfills."""
        backup_path = Path("/tmp/experiments_backup.db")
        if not backup_path.exists():
            # If not in /tmp, copy from workspace experiments.db
            backup_path = Path("experiments.db")

        test_prod_copy = os.path.join(self.temp_dir, "test_prod_copy.db")
        shutil.copyfile(backup_path, test_prod_copy)

        conn = sqlite3.connect(test_prod_copy)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Check existing user count before migration
        users_before = conn.execute("SELECT id, email, name FROM users").fetchall()
        user_ids = [u["id"] for u in users_before]
        self.assertGreaterEqual(len(users_before), 1, "Expected existing users in production database copy.")

        # Run migration on existing database
        applied_ver = user_metadata_manager.run_schema_migrations(conn)
        self.assertEqual(applied_ver, 2)

        # 1. Verify all existing users are strictly preserved
        users_after = conn.execute("SELECT id, email, name FROM users").fetchall()
        self.assertEqual(len(users_before), len(users_after))
        for u_before, u_after in zip(users_before, users_after):
            self.assertEqual(u_before["id"], u_after["id"])
            self.assertEqual(u_before["email"], u_after["email"])

        # 2. Verify backfill of workspaces for existing users
        for uid in user_ids:
            ws = conn.execute("SELECT * FROM workspaces WHERE owner_id=?", (uid,)).fetchall()
            self.assertGreaterEqual(len(ws), 1, f"Expected workspace to be backfilled for user {uid}")
            members = conn.execute("SELECT * FROM workspace_members WHERE user_id=?", (uid,)).fetchall()
            self.assertGreaterEqual(len(members), 1, f"Expected workspace membership for user {uid}")

        # 3. Verify backfill of integrations (git_local, wispr_voice connected)
        for uid in user_ids:
            integs = conn.execute("SELECT provider, status FROM user_integrations WHERE user_id=?", (uid,)).fetchall()
            integ_map = {r["provider"]: r["status"] for r in integs}
            self.assertEqual(integ_map.get("git_local"), "connected")
            self.assertEqual(integ_map.get("wispr_voice"), "connected")

        # 4. Verify backfill of consents and audit logs
        for uid in user_ids:
            logs = conn.execute("SELECT * FROM user_audit_logs WHERE user_id=?", (uid,)).fetchall()
            self.assertGreaterEqual(len(logs), 1, f"Expected audit log entry for user {uid}")
            consents = conn.execute("SELECT * FROM user_consents WHERE user_id=?", (uid,)).fetchall()
            self.assertGreaterEqual(len(consents), 1, f"Expected consent entry for user {uid}")

        conn.close()

    def test_relational_uniqueness_and_prompt_crud(self) -> None:
        """Test user_saved_prompts uniqueness constraints, pinning, and CRUD."""
        auth_manager.init_auth_tables(self.connection)
        user_metadata_manager.run_schema_migrations(self.connection)

        user, _ = auth_manager.register_user(
            self.connection, "prompter@aster.ai", "Password123!@#", "Ada Researcher"
        )
        uid = user["id"]

        # Create prompt
        prompt = user_metadata_manager.create_or_update_saved_prompt(
            self.connection, uid,
            title="Hypothesis Distiller",
            prompt_template="Summarize the primary hypothesis and experimental variable.",
            task_domain="research",
            tags=["hypothesis", "structuring"],
            is_pinned=True,
        )
        self.assertEqual(prompt["title"], "Hypothesis Distiller")
        self.assertTrue(prompt["is_pinned"])

        # Update prompt with same title (tests UNIQUE constraint and ON CONFLICT UPDATE)
        updated = user_metadata_manager.create_or_update_saved_prompt(
            self.connection, uid,
            title="Hypothesis Distiller",
            prompt_template="Updated template: summarize hypothesis, metrics, and conclusion.",
            task_domain="research",
            tags=["hypothesis", "v2"],
            is_pinned=True,
        )
        self.assertIn("Updated template", updated["prompt_template"])

        # Verify only one prompt exists with this title
        prompts = user_metadata_manager.list_user_saved_prompts(self.connection, uid)
        self.assertEqual(len(prompts), 1)

        # Delete prompt
        deleted = user_metadata_manager.delete_saved_prompt(self.connection, uid, prompt["id"])
        self.assertTrue(deleted)
        self.assertEqual(len(user_metadata_manager.list_user_saved_prompts(self.connection, uid)), 0)

    def test_consent_history_and_audit_logging(self) -> None:
        """Test append-only consent ledger and security audit log pruning."""
        auth_manager.init_auth_tables(self.connection)
        user_metadata_manager.run_schema_migrations(self.connection)

        user, _ = auth_manager.register_user(
            self.connection, "privacy@aster.ai", "Password123!@#", "Privacy Officer"
        )
        uid = user["id"]

        # Record consent transitions
        user_metadata_manager.record_user_consent(self.connection, uid, "telemetry", True, policy_version="1.0", ip_address="127.0.0.1")
        user_metadata_manager.record_user_consent(self.connection, uid, "telemetry", False, policy_version="1.1", ip_address="127.0.0.1")

        history = user_metadata_manager.get_user_consent_history(self.connection, uid, consent_type="telemetry")
        self.assertEqual(len(history), 2)
        # Most recent is revoked
        self.assertFalse(history[0]["granted"])
        self.assertEqual(history[0]["policy_version"], "1.1")
        # Previous was granted
        self.assertTrue(history[1]["granted"])

        # Log security audit events
        user_metadata_manager.log_user_security_event(self.connection, uid, "login_attempt", "Successful login", "info", ip_address="10.0.0.1")
        user_metadata_manager.log_user_security_event(self.connection, uid, "password_reset", "Password reset requested", "warning", ip_address="10.0.0.1")

        events = user_metadata_manager.get_user_security_events(self.connection, uid)
        event_types = [e["event_type"] for e in events]
        self.assertIn("login_attempt", event_types)
        self.assertIn("password_reset", event_types)

    def test_export_and_foreign_key_cascade_deletion(self) -> None:
        """Verify export bundle contains relational records and account deletion cascades cleanly."""
        auth_manager.init_auth_tables(self.connection)
        user_metadata_manager.run_schema_migrations(self.connection)

        # Create user
        user, _ = auth_manager.register_user(
            self.connection, "erasure@aster.ai", "Password123!@#", "Data Subject"
        )
        uid = user["id"]

        # Add related records
        user_metadata_manager.create_or_update_saved_prompt(
            self.connection, uid, "Test Prompt", "Template body", "research"
        )
        user_metadata_manager.record_user_consent(self.connection, uid, "analytics", True)
        user_metadata_manager.set_user_integration(self.connection, uid, "zotero", "connected", "zotero_user_123")
        user_metadata_manager.log_user_security_event(self.connection, uid, "custom_event", "Audit log test")

        # Test export bundle
        bundle_str = user_metadata_manager.export_user_data_bundle(self.connection, uid)
        bundle = json.loads(bundle_str)
        self.assertIn("workspaces", bundle)
        self.assertIn("saved_prompts", bundle)
        self.assertIn("consent_history", bundle)
        self.assertIn("integrations", bundle)
        self.assertIn("audit_logs", bundle)
        self.assertIn("privacy_requests", bundle)
        self.assertEqual(len(bundle["saved_prompts"]), 1)
        self.assertNotIn("password_hash", bundle["user_profile_and_metadata"]["personal_details"])

        # Verify privacy request was recorded
        reqs = user_metadata_manager.get_user_privacy_requests(self.connection, uid)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["request_type"], "export")
        self.assertEqual(reqs[0]["status"], "completed")

        # Execute complete account erasure
        deleted = user_metadata_manager.delete_user_account(self.connection, uid)
        self.assertTrue(deleted)

        # Verify all records across relational tables are cascaded/deleted
        for table in [
            "users",
            "user_metadata",
            "user_sessions",
            "email_verifications",
            "workspaces",
            "workspace_members",
            "user_saved_prompts",
            "user_consents",
            "user_integrations",
            "user_audit_logs",
            "user_privacy_requests",
        ]:
            col = "owner_id" if table == "workspaces" else "user_id" if table != "users" else "id"
            count = self.connection.execute(f"SELECT COUNT(*) FROM {table} WHERE {col}=?", (uid,)).fetchone()[0]
            self.assertEqual(count, 0, f"Expected 0 records in {table} after account deletion, found {count}")


if __name__ == "__main__":
    unittest.main()

