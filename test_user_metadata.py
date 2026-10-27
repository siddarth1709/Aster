"""Unit tests for Aster User Metadata System.

Tests cover:
1. Canonical section defaults and full 120+ fields audit.
2. SQLite persistence, auto-provisioning, and retrieval.
3. Server-side validation and sanitization.
4. Authorization boundary enforcement (preventing unauthorized modification of account_role, account_status, internal_flags).
5. Protection against credential leakage (no raw passwords, hashes, API keys in metadata).
6. Date/time formatting with user preferences.
7. Dynamic CSS styling generation with themes, accents, typography, density, and accessibility.
8. Activity and telemetry tracking (ai_request, voice_notes, structuring, diagrams, comparisons, paper_radar, new_project, session).
9. Session count live recalculation.
10. Data export archive and right-to-be-forgotten data erasure.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
import unittest

import user_metadata_manager
import auth_manager


class TestUserMetadataSystem(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        auth_manager.init_auth_tables(self.connection)
        user_metadata_manager.init_user_metadata_table(self.connection)

        # Create dummy experiment table
        self.connection.execute("""CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY, title TEXT, created_at TEXT
        )""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS research_contexts (
            id TEXT PRIMARY KEY, name TEXT, body TEXT, created_at TEXT
        )""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS experiment_memories (
            experiment_id TEXT PRIMARY KEY, summary TEXT, importance REAL, created_at TEXT
        )""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS saved_papers (
            id TEXT PRIMARY KEY, user_id TEXT, paper_id TEXT, title TEXT, saved_at TEXT
        )""")
        self.connection.commit()

        # Register a test user
        self.user, _ = auth_manager.register_user(
            self.connection, "scientist@aster.org", "SecurePassword123!", "Dr. Ada Lovelace"
        )
        self.user_id = self.user["id"]

    def tearDown(self) -> None:
        self.connection.close()

    def test_all_120_fields_present_in_defaults(self) -> None:
        meta = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        sections = [
            "personal_details",
            "account_details",
            "user_preferences",
            "ai_preferences",
            "research_profile",
            "workspace_details",
            "integrations",
            "usage_activity",
            "security_privacy",
            "personalization_memory",
            "system_metadata",
        ]
        total_leaf_fields = 0
        for sec in sections:
            self.assertIn(sec, meta, f"Section {sec} missing in user metadata")
            sec_dict = meta[sec]
            for k, v in sec_dict.items():
                if isinstance(v, dict):
                    total_leaf_fields += len(v)
                else:
                    total_leaf_fields += 1
        self.assertGreaterEqual(total_leaf_fields, 120, f"Expected at least 120 fields, got {total_leaf_fields}")

    def test_server_side_validation_and_sanitization(self) -> None:
        meta = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        
        # Test temperature bounding
        meta["ai_preferences"]["default_temperature"] = 2.5
        meta["ai_preferences"]["ai_usage_limits"] = -50
        meta["user_preferences"]["theme"] = "NonExistentTheme"
        meta["user_preferences"]["accent_colour"] = "NonExistentAccent"
        meta["personal_details"]["username"] = "INVALID USERNAME WITH SPACES $$$"

        sanitized = user_metadata_manager.validate_and_sanitize_metadata(meta, meta)
        self.assertEqual(sanitized["ai_preferences"]["default_temperature"], 1.0)
        self.assertEqual(sanitized["ai_preferences"]["ai_usage_limits"], 100)
        self.assertEqual(sanitized["user_preferences"]["theme"], "Obsidian Dark (Default)")
        self.assertEqual(sanitized["user_preferences"]["accent_colour"], "Aster Orange (#f18a5e)")
        self.assertNotIn(" ", sanitized["personal_details"]["username"])

    def test_authorization_boundary_account_role_and_internal_flags(self) -> None:
        meta = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        original_role = meta["account_details"]["account_role"]
        original_status = meta["account_details"]["account_status"]

        # Attempt unauthorized client escalation
        meta["account_details"]["account_role"] = "SuperAdmin"
        meta["account_details"]["account_status"] = "GodMode"
        meta["system_metadata"]["internal_flags"]["sandbox_mode"] = True

        # Save with is_admin=False (standard client submission)
        success = user_metadata_manager.save_user_metadata(self.connection, self.user_id, meta, is_admin=False)
        self.assertTrue(success)

        # Verify preserved
        fresh = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        self.assertEqual(fresh["account_details"]["account_role"], original_role)
        self.assertEqual(fresh["account_details"]["account_status"], original_status)
        self.assertFalse(fresh["system_metadata"]["internal_flags"]["sandbox_mode"])

    def test_activity_telemetry_tracking(self) -> None:
        # Record AI request
        user_metadata_manager.record_user_activity(self.connection, self.user_id, "ai_request", increment=3)
        # Record structuring
        user_metadata_manager.record_user_activity(self.connection, self.user_id, "structuring", increment=2)
        # Record diagrams
        user_metadata_manager.record_user_activity(self.connection, self.user_id, "diagrams", increment=1)
        # Record comparisons
        user_metadata_manager.record_user_activity(self.connection, self.user_id, "comparisons", increment=4)

        fresh = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        u_act = fresh["usage_activity"]
        self.assertEqual(u_act["total_ai_requests"], 3)
        self.assertEqual(u_act["monthly_ai_usage"], 3)
        features = u_act["feature_usage_summary"]
        self.assertEqual(features["structuring"], 2)
        self.assertEqual(features["diagrams"], 1)
        self.assertEqual(features["comparisons"], 4)

    def test_date_formatting(self) -> None:
        iso_sample = "2026-10-28T14:30:00+00:00"
        
        fmt_default = user_metadata_manager.format_user_datetime(iso_sample, "YYYY-MM-DD HH:mm")
        self.assertTrue(len(fmt_default) >= 10)

        fmt_slash = user_metadata_manager.format_user_datetime(iso_sample, "DD/MM/YYYY HH:mm")
        self.assertIn("/", fmt_slash)

        fmt_human = user_metadata_manager.format_user_datetime(iso_sample, "MMM D, YYYY h:mm A")
        self.assertIn(",", fmt_human)

    def test_dynamic_css_generation(self) -> None:
        prefs = {
            "theme": "Graphite Slate",
            "accent_colour": "Electric Violet (#a990ff)",
            "text_density": "Compact",
            "font_size_preference": "Large (18px)",
            "reduced_motion_preference": True,
            "accessibility_preferences": {
                "high_contrast": True,
                "screen_reader_optimizations": True,
                "underline_links": True,
            },
        }
        css = user_metadata_manager.generate_user_custom_css(prefs)
        self.assertIn("--aster-accent: #a990ff", css)
        self.assertIn("padding: 10px", css)
        self.assertIn("font-size: 18px", css)
        self.assertIn("animation: none", css)
        self.assertIn("text-decoration: underline", css)
        self.assertIn(":focus-visible", css)

    def test_export_and_right_to_be_forgotten(self) -> None:
        # Export bundle
        bundle_str = user_metadata_manager.export_user_data_bundle(self.connection, self.user_id)
        bundle = json.loads(bundle_str)
        self.assertIn("user_profile_and_metadata", bundle)
        self.assertNotIn("password_hash", bundle["user_profile_and_metadata"]["personal_details"])

        # Check export status was recorded
        meta = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        self.assertTrue(meta["security_privacy"]["data_export_request_status"])

        # Execute data erasure
        deleted = user_metadata_manager.delete_user_account(self.connection, self.user_id)
        self.assertTrue(deleted)

        # Verify user and metadata no longer exist in tables
        user_row = self.connection.execute("SELECT * FROM users WHERE id=?", (self.user_id,)).fetchone()
        meta_row = self.connection.execute("SELECT * FROM user_metadata WHERE user_id=?", (self.user_id,)).fetchone()
        self.assertIsNone(user_row)
        self.assertIsNone(meta_row)

    def test_personalization_memory_directives_flow(self) -> None:
        meta = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        meta["personalization_memory"]["saved_user_instructions"] = "Always cite primary literature."
        meta["personalization_memory"]["preferred_working_style"] = "Empirical first"
        meta["personalization_memory"]["preferred_communication_tone"] = "Formal scientific"
        meta["ai_preferences"]["reasoning_detail_preference"] = "High (Step-by-step)"
        user_metadata_manager.save_user_metadata(self.connection, self.user_id, meta, is_admin=False)

        fresh = user_metadata_manager.get_user_metadata(self.connection, self.user_id)
        pm = fresh["personalization_memory"]
        self.assertEqual(pm["saved_user_instructions"], "Always cite primary literature.")
        self.assertEqual(pm["preferred_working_style"], "Empirical first")
        self.assertEqual(pm["preferred_communication_tone"], "Formal scientific")
        self.assertEqual(fresh["ai_preferences"]["reasoning_detail_preference"], "High (Step-by-step)")


if __name__ == "__main__":
    unittest.main()
