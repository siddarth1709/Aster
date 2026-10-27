"""Aster Settings & User Metadata Management View.

Renders the comprehensive user metadata and profile management control center:
1. Personal details
2. Account details (excluding subscription as requested)
3. User preferences (Theme, Accent colour, Density, Font size, Motion, Layout)
4. AI preferences (Provider, Model, Temperature, Response length, Reasoning detail, Fallback, Limits)
5. Research profile (Interests, Expertise, Methodology, Citation style, Technical skills)
6. Workspace details (Name, Role, Template, Repository, Permissions)
7. Integrations (GitHub, GitLab, Google, Cloud storage, Sync preferences)
8. Usage & activity (Real-time telemetry, AI request counts, Feature usage summary)
9. Security & privacy (Consents with timestamps, Privacy mode, Active sessions, Data export JSON)
10. Personalization & memory (Saved user instructions, Working style, Coding conventions, Custom AI instructions)
11. System metadata (Schema v1.2.0, Timestamps, Migration version, Flags)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from html import escape
from typing import Any, Callable

import streamlit as st
import user_metadata_manager


def render_user_metadata_settings(
    connection: sqlite3.Connection,
    current_user: dict[str, Any],
    get_api_key_fn: Callable[[], str | None],
    save_api_key_fn: Callable[[str], None],
    remove_api_key_fn: Callable[[], None],
    keyring_available_fn: Callable[[], bool],
    render_custom_metrics_fn: Callable[[], None],
    render_research_context_fn: Callable[[], None],
) -> None:
    """Render the state-of-the-art Aster User Profile & Metadata Management Control Center."""
    user_id = current_user.get("id", "")
    metadata = user_metadata_manager.get_user_metadata(connection, user_id)

    p_details = metadata.get("personal_details", {})
    a_details = metadata.get("account_details", {})
    u_pref = metadata.get("user_preferences", {})
    ai_pref = metadata.get("ai_preferences", {})
    r_prof = metadata.get("research_profile", {})
    w_details = metadata.get("workspace_details", {})
    integ = metadata.get("integrations", {})
    u_act = metadata.get("usage_activity", {})
    sec_priv = metadata.get("security_privacy", {})
    pers_mem = metadata.get("personalization_memory", {})
    sys_meta = metadata.get("system_metadata", {})

    # Compute initials
    name = p_details.get("full_name") or current_user.get("name") or "Researcher"
    email = p_details.get("email") or current_user.get("email") or ""
    initials = "".join([part[0].upper() for part in name.split()[:2]]) if name else "AR"

    # Header section
    st.markdown('<p class="eyebrow">RESEARCH OS · USER METADATA & CONTROL CENTER</p>', unsafe_allow_html=True)
    st.title("User Profile & Settings")
    st.caption("Manage your research identity, AI inference configuration, computational preferences, and privacy controls.")

    # Profile Quick Banner
    role = a_details.get("account_role", "Research Scientist")
    is_ver = a_details.get("email_verified", False)
    username = p_details.get("username", "researcher")
    active_sessions = sec_priv.get("active_session_count", 1)
    total_ai = u_act.get("total_ai_requests", 0)

    banner_html = f"""
    <div style="display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 24px;border:1px solid rgba(255,255,255,0.11);border-radius:18px;background:linear-gradient(145deg,rgba(26,29,38,0.7),rgba(15,18,25,0.75));backdrop-filter:blur(16px);margin-bottom:28px;">
      <div style="display:flex;align-items:center;gap:18px;">
        <div style="width:58px;height:58px;border-radius:16px;background:linear-gradient(135deg,#f18a5e,#b29cf4);display:flex;align-items:center;justify-content:center;color:#18100c;font-size:22px;font-weight:700;box-shadow:0 8px 24px rgba(241,138,94,0.25);">
          {escape(initials)}
        </div>
        <div>
          <div style="display:flex;align-items:center;gap:10px;">            <h2 style="margin:0;font-size:21px;font-weight:650;color:#f2f4f8;">{escape(name)}</h2>
            <span style="font-size:12px;color:#929aa8;font-family:var(--aster-font-mono,monospace);">@{escape(username)}</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-top:5px;flex-wrap:wrap;">
            <span style="font-size:11px;padding:2px 9px;border-radius:999px;background:rgba(241,138,94,0.14);color:#f18a5e;border:1px solid rgba(241,138,94,0.3);font-weight:550;">{escape(role)}</span>
            <span style="font-size:11px;padding:2px 9px;border-radius:999px;background:{'rgba(129,200,169,0.12)' if is_ver else 'rgba(241,138,94,0.12)'};color:{'#81c8a9' if is_ver else '#f3a07d'};border:1px solid {'rgba(129,200,169,0.3)' if is_ver else 'rgba(241,138,94,0.3)'};">
              {f'<span style="display:inline-flex;align-items:center;gap:4px;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>Verified Identity</span>' if is_ver else f'<span style="display:inline-flex;align-items:center;gap:4px;"><svg width="7" height="7" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10"/></svg>OTP Pending</span>'}
            </span>
            <span style="font-size:11px;color:#8592a6;">· {escape(email)}</span>
          </div>
        </div>
      </div>
      <div style="display:flex;gap:24px;text-align:right;">
        <div>
          <div style="font-size:10px;color:#78869c;text-transform:uppercase;letter-spacing:0.08em;">AI Operations</div>
          <div style="font-size:18px;font-weight:650;color:#f18a5e;">{total_ai}</div>
        </div>
        <div>
          <div style="font-size:10px;color:#78869c;text-transform:uppercase;letter-spacing:0.08em;">Active Sessions</div>
          <div style="font-size:18px;font-weight:650;color:#a990ff;">{active_sessions}</div>
        </div>
      </div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

    # 10 Functional Tabs
    tab_labels = [
        "AI Preferences",
        "Personal & Account",
        "User Preferences",
        "Research Profile",
        "Workspace Details",
        "Integrations",
        "Usage & Activity",
        "Security & Privacy",
        "Personalization & Memory",
        "System Metadata",
        "Metric Ledgers",
    ]
    tabs = st.tabs(tab_labels)

    # ==========================================================================
    # TAB 1: AI Preferences & Gemini Connection
    # ==========================================================================
    with tabs[0]:
        st.subheader("AI Inference & Model Preferences")
        st.caption("Configure default LLM models, API keys, temperature parameters, and deliberate reasoning preferences.")

        # API Key management section
        st.markdown("#### API Key Configuration")
        active_key = get_api_key_fn()
        has_key = bool(active_key)
        ai_pref["user_provided_api_key_status"] = has_key

        if has_key:
            st.success(f"Active API Key Configured · {active_key[:4]}###", icon=":material/check_circle:")
            if st.button("Remove saved API key", key="btn_remove_key_meta"):
                remove_api_key_fn()
                ai_pref["user_provided_api_key_status"] = False
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("API key removed.", icon=":material/delete:")
                st.rerun()
        else:
            st.warning("No Gemini API key detected. Provide one below to unlock experiment synthesis, diagrams, and semantic search.", icon=":material/info:")
            with st.form("quick_api_key_form"):
                candidate = st.text_input("Gemini API key", type="password", placeholder="AIzaSy...", autocomplete="new-password")
                if st.form_submit_button("Save API key", type="primary"):
                    if candidate.strip():
                        save_api_key_fn(candidate.strip())
                        ai_pref["user_provided_api_key_status"] = True
                        user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                        st.toast("API key saved successfully!", icon=":material/key:")
                        st.rerun()
                    else:
                        st.error("Please enter a valid key.")

        st.divider()
        st.markdown("#### Model Selection & Inference Parameters")
        with st.form("form_ai_preferences"):
            c1, c2 = st.columns(2)
            with c1:
                providers = ["Google Gemini", "Anthropic Claude (BYOK)", "OpenAI (BYOK)", "Ollama / Local"]
                provider_idx = providers.index(ai_pref.get("preferred_ai_provider")) if ai_pref.get("preferred_ai_provider") in providers else 0
                new_provider = st.selectbox("Preferred AI provider", providers, index=provider_idx)

                models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "claude-3-7-sonnet", "gpt-4o", "deepseek-r1-local"]
                model_idx = models.index(ai_pref.get("preferred_ai_model")) if ai_pref.get("preferred_ai_model") in models else 0
                new_model = st.selectbox("Preferred AI model", models, index=model_idx, help="Primary model used for experiment structuring and diagram generation.")

                research_models = ["gemini-2.0-flash", "gemini-1.5-pro", "claude-3-7-sonnet"]
                r_idx = research_models.index(ai_pref.get("default_model_research")) if ai_pref.get("default_model_research") in research_models else 0
                new_r_model = st.selectbox("Default model for research", research_models, index=r_idx)

                coding_models = ["gemini-2.0-flash", "gemini-1.5-pro", "claude-3-7-sonnet", "gpt-4o"]
                c_idx = coding_models.index(ai_pref.get("default_model_coding")) if ai_pref.get("default_model_coding") in coding_models else 0
                new_c_model = st.selectbox("Default model for coding", coding_models, index=c_idx)

                analysis_models = ["gemini-2.0-flash", "gemini-1.5-pro"]
                a_idx = analysis_models.index(ai_pref.get("default_model_analysis")) if ai_pref.get("default_model_analysis") in analysis_models else 0
                new_a_model = st.selectbox("Default model for analysis", analysis_models, index=a_idx)

            with c2:
                speeds = ["Fast (Low latency)", "Balanced", "Deep deliberate thought"]
                speed_idx = speeds.index(ai_pref.get("response_time_preference")) if ai_pref.get("response_time_preference") in speeds else 0
                new_speed = st.selectbox("Response time preference", speeds, index=speed_idx)

                lengths = ["Concise", "Balanced", "Exhaustive / Detailed"]
                length_idx = lengths.index(ai_pref.get("response_length_preference")) if ai_pref.get("response_length_preference") in lengths else 1
                new_length = st.selectbox("Response length preference", lengths, index=length_idx)

                reasoning_opts = ["High (Step-by-step)", "Standard", "Minimal"]
                reason_idx = reasoning_opts.index(ai_pref.get("reasoning_detail_preference")) if ai_pref.get("reasoning_detail_preference") in reasoning_opts else 0
                new_reason = st.selectbox("Reasoning detail preference", reasoning_opts, index=reason_idx)

                new_temp = st.slider("Default temperature", min_value=0.0, max_value=1.0, value=float(ai_pref.get("default_temperature", 0.20)), step=0.05, help="Lower values produce more deterministic, factual output.")

                windows = ["Standard (32k)", "Extended (128k)", "Ultra (1M+ tokens)"]
                win_idx = windows.index(ai_pref.get("default_context_window_preference")) if ai_pref.get("default_context_window_preference") in windows else 0
                new_win = st.selectbox("Default context window preference", windows, index=win_idx)

                new_fallback = st.checkbox("Model fallback preference (auto-switch on rate limit)", value=bool(ai_pref.get("model_fallback_preference", True)))
                new_limit = st.number_input("AI monthly usage limits (max requests)", min_value=100, max_value=50000, value=int(ai_pref.get("ai_usage_limits", 1000)), step=100)

            if st.form_submit_button("Save AI Preferences", type="primary"):
                ai_pref["preferred_ai_provider"] = new_provider
                ai_pref["preferred_ai_model"] = new_model
                ai_pref["default_model_research"] = new_r_model
                ai_pref["default_model_coding"] = new_c_model
                ai_pref["default_model_analysis"] = new_a_model
                ai_pref["response_time_preference"] = new_speed
                ai_pref["response_length_preference"] = new_length
                ai_pref["reasoning_detail_preference"] = new_reason
                ai_pref["default_temperature"] = new_temp
                ai_pref["model_fallback_preference"] = new_fallback
                ai_pref["ai_usage_limits"] = new_limit
                ai_pref["default_context_window_preference"] = new_win

                metadata["ai_preferences"] = ai_pref
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("AI preferences updated!", icon=":material/bolt:")
                st.rerun()

    # ==========================================================================
    # TAB 2: Personal Details & Account Details
    # ==========================================================================
    with tabs[1]:
        st.subheader("Personal & Account Identification")
        st.caption("Manage user identity, demographic attributes, contact information, and security role.")

        with st.form("form_personal_account"):
            st.markdown("#### Personal Identity")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("User ID (Immutable)", value=p_details.get("user_id", user_id), disabled=True)
                new_full_name = st.text_input("Full name", value=p_details.get("full_name", name), placeholder="Dr. Jane Doe")
                new_username = st.text_input("Username", value=p_details.get("username", username), placeholder="janedoe")
                new_email = st.text_input("Email address", value=p_details.get("email", email), disabled=True)
                new_phone = st.text_input("Phone number", value=p_details.get("phone_number", ""), placeholder="+1 (555) 019-2834")
                new_avatar = st.text_input("Profile picture URL", value=p_details.get("profile_picture", ""), placeholder="https://example.org/avatar.jpg")

            with c2:
                new_bio = st.text_area("Bio or description", value=p_details.get("bio", ""), height=100)
                new_dob = st.text_input("Date of birth (optional)", value=p_details.get("date_of_birth", ""), placeholder="YYYY-MM-DD")
                new_country = st.text_input("Country", value=p_details.get("country", "United States"))
                new_region = st.text_input("State / Region", value=p_details.get("state_region", "California"))
                new_city = st.text_input("City", value=p_details.get("city", "San Francisco"))
                timezones = ["America/Los_Angeles", "America/New_York", "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Asia/Kolkata", "UTC"]
                tz_idx = timezones.index(p_details.get("timezone")) if p_details.get("timezone") in timezones else 0
                new_tz = st.selectbox("Time zone", timezones, index=tz_idx)
                langs = ["English (US)", "English (UK)", "German", "French", "Spanish", "Japanese", "Mandarin"]
                lang_idx = langs.index(p_details.get("preferred_language")) if p_details.get("preferred_language") in langs else 0
                new_lang = st.selectbox("Preferred language", langs, index=lang_idx)

            st.divider()
            st.markdown("#### Account Status & Role")
            c3, c4 = st.columns(2)
            with c3:
                statuses = ["Active", "Verified", "Under Review", "Suspended"]
                stat_idx = statuses.index(a_details.get("account_status")) if a_details.get("account_status") in statuses else 0
                new_status = st.selectbox("Account status", statuses, index=stat_idx)

                roles = ["Research Scientist", "Principal Investigator", "Staff Engineer", "Postdoctoral Fellow", "PhD Candidate", "Reviewer"]
                role_idx = roles.index(a_details.get("account_role")) if a_details.get("account_role") in roles else 0
                new_role = st.selectbox("Account role", roles, index=role_idx)

                st.text_input("Account creation date", value=p_details.get("created_at", ""), disabled=True)
                st.text_input("Authentication provider", value=a_details.get("auth_provider", "Email OTP"), disabled=True)

            with c4:
                st.text_input("Last login timestamp", value=a_details.get("last_login_at", ""), disabled=True)
                st.text_input("Last password change", value=a_details.get("last_password_changed_at", ""), disabled=True)
                new_phone_ver = st.checkbox("Phone verification status", value=bool(a_details.get("phone_verified", False)))
                new_mfa = st.checkbox("Multi-factor authentication status (MFA enabled)", value=bool(a_details.get("mfa_enabled", False)))

            if st.form_submit_button("Save Personal & Account Details", type="primary"):
                p_details["full_name"] = new_full_name
                p_details["username"] = new_username
                p_details["phone_number"] = new_phone
                p_details["profile_picture"] = new_avatar
                p_details["bio"] = new_bio
                p_details["date_of_birth"] = new_dob
                p_details["country"] = new_country
                p_details["state_region"] = new_region
                p_details["city"] = new_city
                p_details["timezone"] = new_tz
                p_details["preferred_language"] = new_lang

                a_details["account_status"] = new_status
                a_details["account_role"] = new_role
                a_details["phone_verified"] = new_phone_ver
                a_details["mfa_enabled"] = new_mfa

                metadata["personal_details"] = p_details
                metadata["account_details"] = a_details
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.session_state["authenticated_user"]["name"] = new_full_name
                st.toast("Personal and account details updated!", icon=":material/person:")
                st.rerun()

    # ==========================================================================
    # TAB 3: User Preferences & Appearance
    # ==========================================================================
    with tabs[2]:
        st.subheader("User Preferences & Visual Accessibility")
        st.caption("Customize appearance tokens, layout architecture, typography scale, and notifications.")

        with st.form("form_user_preferences"):
            c1, c2 = st.columns(2)
            with c1:
                themes = ["Obsidian Dark (Default)", "Onyx OLED", "Graphite Slate"]
                theme_idx = themes.index(u_pref.get("theme")) if u_pref.get("theme") in themes else 0
                new_theme = st.selectbox("Theme preference", themes, index=theme_idx)

                accents = [
                    "Aster Orange (#f18a5e)",
                    "Solar Copper (#fa9870)",
                    "Electric Violet (#a990ff)",
                    "Cyan Pulse (#64d2ff)",
                    "Emerald (#81c8a9)",
                ]
                accent_idx = accents.index(u_pref.get("accent_colour")) if u_pref.get("accent_colour") in accents else 0
                new_accent = st.selectbox("Accent colour", accents, index=accent_idx)

                densities = ["Comfortable", "Compact", "Expanded"]
                den_idx = densities.index(u_pref.get("text_density")) if u_pref.get("text_density") in densities else 0
                new_density = st.selectbox("Text density", densities, index=den_idx)

                fonts = ["Standard (16px)", "Small (14px)", "Large (18px)"]
                f_idx = fonts.index(u_pref.get("font_size_preference")) if u_pref.get("font_size_preference") in fonts else 0
                new_font = st.selectbox("Font size preference", fonts, index=f_idx)

                new_motion = st.checkbox("Reduced motion preference (disable UI animations)", value=bool(u_pref.get("reduced_motion_preference", False)))

            with c2:
                layouts = ["Split Workflow", "Linear Feed", "Matrix Grid"]
                l_idx = layouts.index(u_pref.get("dashboard_layout_preference")) if u_pref.get("dashboard_layout_preference") in layouts else 0
                new_layout = st.selectbox("Dashboard layout preference", layouts, index=l_idx)

                landing_pages = ["Home", "Create Experiment", "All Experiments", "Research Graph", "Weekly Summary"]
                lp_idx = landing_pages.index(u_pref.get("default_landing_page")) if u_pref.get("default_landing_page") in landing_pages else 0
                new_lp = st.selectbox("Default landing page", landing_pages, index=lp_idx)

                dt_formats = ["YYYY-MM-DD HH:mm", "DD/MM/YYYY HH:mm", "MMM D, YYYY h:mm A"]
                dt_idx = dt_formats.index(u_pref.get("date_time_format")) if u_pref.get("date_time_format") in dt_formats else 0
                new_dt = st.selectbox("Date and time format", dt_formats, index=dt_idx)

                units = ["Metric (SI)", "US Customary"]
                u_idx = units.index(u_pref.get("preferred_units")) if u_pref.get("preferred_units") in units else 0
                new_units = st.selectbox("Preferred units", units, index=u_idx)

                new_email_updates = st.checkbox("Email update preferences (monthly paper digest)", value=bool(u_pref.get("email_update_preferences", True)))

            st.divider()
            st.markdown("#### Accessibility Preferences")
            acc_dict = u_pref.get("accessibility_preferences", {})
            ca, cb, cc = st.columns(3)
            with ca:
                acc_high_contrast = st.checkbox("High contrast mode", value=bool(acc_dict.get("high_contrast", False)))
            with cb:
                acc_screen_reader = st.checkbox("Screen reader optimizations", value=bool(acc_dict.get("screen_reader_optimizations", False)))
            with cc:
                acc_underline = st.checkbox("Underline navigation links", value=bool(acc_dict.get("underline_links", False)))

            if st.form_submit_button("Save Preferences", type="primary"):
                u_pref["theme"] = new_theme
                u_pref["accent_colour"] = new_accent
                u_pref["text_density"] = new_density
                u_pref["font_size_preference"] = new_font
                u_pref["reduced_motion_preference"] = new_motion
                u_pref["dashboard_layout_preference"] = new_layout
                u_pref["default_landing_page"] = new_lp
                u_pref["date_time_format"] = new_dt
                u_pref["preferred_units"] = new_units
                u_pref["email_update_preferences"] = new_email_updates
                u_pref["accessibility_preferences"] = {
                    "high_contrast": acc_high_contrast,
                    "screen_reader_optimizations": acc_screen_reader,
                    "underline_links": acc_underline,
                }

                metadata["user_preferences"] = u_pref
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Appearance and preferences saved!", icon=":material/palette:")
                st.rerun()

    # ==========================================================================
    # TAB 4: Research Profile
    # ==========================================================================
    with tabs[3]:
        st.subheader("Academic & Research Profile")
        st.caption("Calibration attributes used to tailor paper discoveries, baseline recommendations, and structuring taxonomies.")

        with st.form("form_research_profile"):
            c1, c2 = st.columns(2)
            with c1:
                cur_interests = ", ".join(r_prof.get("research_interests", []))
                new_interests_str = st.text_input("Research interests (comma-separated)", value=cur_interests, help="E.g. Agentic Reasoning, Memory Systems, Test-Time Compute")

                areas = [
                    "NLP & LLM Reasoning",
                    "Computer Vision & Multimodal",
                    "Reinforcement Learning & Robotics",
                    "Systems & Hardware Architecture",
                    "Bioinformatics & Computational Biology",
                ]
                area_idx = areas.index(r_prof.get("area_of_expertise")) if r_prof.get("area_of_expertise") in areas else 0
                new_area = st.selectbox("Area of expertise", areas, index=area_idx)

                new_prof_role = st.text_input("Professional role", value=r_prof.get("professional_role", "Lead AI Researcher"))
                new_industry = st.text_input("Industry", value=r_prof.get("industry", "Academic & Frontier Lab"))
                new_tech_skills = st.text_input("Technical skills", value=r_prof.get("technical_skills", "PyTorch, JAX, Hugging Face, CUDA"))

            with c2:
                methods = [
                    "Empirical / Benchmarking",
                    "Theoretical & Proof-guided",
                    "Ablation-driven",
                    "Applied Prototype",
                ]
                m_idx = methods.index(r_prof.get("preferred_research_methodology")) if r_prof.get("preferred_research_methodology") in methods else 0
                new_method = st.selectbox("Preferred research methodology", methods, index=m_idx)

                citations = ["BibTeX", "APA 7th", "IEEE", "Nature", "ACM"]
                c_idx = citations.index(r_prof.get("preferred_citation_style")) if r_prof.get("preferred_citation_style") in citations else 0
                new_citation = st.selectbox("Preferred citation style", citations, index=c_idx)

                outputs = ["Markdown + LaTeX", "Structured JSON", "Interactive HTML", "Clean Text"]
                o_idx = outputs.index(r_prof.get("preferred_output_formats")) if r_prof.get("preferred_output_formats") in outputs else 0
                new_output = st.selectbox("Preferred output formats", outputs, index=o_idx)

                retention_opts = ["Forever", "365 days", "180 days", "90 days", "30 days"]
                ret_idx = retention_opts.index(r_prof.get("research_history_retention_preference")) if r_prof.get("research_history_retention_preference") in retention_opts else 0
                new_retention = st.selectbox("Research history retention preference", retention_opts, index=ret_idx)

                new_save_instr = st.checkbox("Save research instructions automatically", value=bool(r_prof.get("save_research_instructions", True)))

            new_sources = st.multiselect(
                "Frequently used AI sources",
                options=["arXiv", "Hugging Face Daily Papers", "Papers With Code", "PubMed", "OpenReview", "Semantic Scholar"],
                default=r_prof.get("frequently_used_ai_sources", ["arXiv", "Hugging Face Daily Papers"]),
            )

            new_kb_refs = st.text_area(
                "Personal knowledge base references",
                value=r_prof.get("personal_knowledge_base_references", ""),
                help="Paths, repositories, or external Zotero/Notion collections referenced during analysis.",
            )

            if st.form_submit_button("Save Research Profile", type="primary"):
                clean_tags = [t.strip() for t in new_interests_str.split(",") if t.strip()]
                r_prof["research_interests"] = clean_tags
                r_prof["area_of_expertise"] = new_area
                r_prof["professional_role"] = new_prof_role
                r_prof["industry"] = new_industry
                r_prof["technical_skills"] = new_tech_skills
                r_prof["preferred_research_methodology"] = new_method
                r_prof["preferred_citation_style"] = new_citation
                r_prof["preferred_output_formats"] = new_output
                r_prof["frequently_used_ai_sources"] = new_sources
                r_prof["research_history_retention_preference"] = new_retention
                r_prof["save_research_instructions"] = new_save_instr
                r_prof["personal_knowledge_base_references"] = new_kb_refs

                metadata["research_profile"] = r_prof
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Research profile updated!", icon=":material/science:")
                st.rerun()

    # ==========================================================================
    # TAB 5: Workspace Details
    # ==========================================================================
    with tabs[4]:
        st.subheader("Workspace & Repository Settings")
        st.caption("Configure local experiment workspace roots, default templates, Git repositories, and access policies.")

        with st.form("form_workspace_details"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Default workspace ID", value=w_details.get("default_workspace_id", ""), disabled=True)
                new_ws_name = st.text_input("Workspace name", value=w_details.get("workspace_name", "Aster Primary Lab"))
                ws_roles = ["Owner", "Admin", "Lead Investigator", "Collaborator"]
                r_idx = ws_roles.index(w_details.get("workspace_role")) if w_details.get("workspace_role") in ws_roles else 0
                new_ws_role = st.selectbox("Workspace role", ws_roles, index=r_idx)
                new_ws_site = st.text_input("Workspace site", value=w_details.get("workspace_site", "local.aster.internal"))
                st.text_input("Creation date", value=w_details.get("workspace_creation_date", ""), disabled=True)

            with c2:
                templates = ["Standard LLM Benchmark", "Vision Ablation", "Agent Harness", "RL Environment", "Minimal Blank"]
                t_idx = templates.index(w_details.get("preferred_project_template")) if w_details.get("preferred_project_template") in templates else 0
                new_template = st.selectbox("Preferred project template", templates, index=t_idx)

                new_repo = st.text_input("Default repository", value=w_details.get("default_repository", "aster-research-workspace"))
                providers = ["GitHub", "GitLab", "Local Git", "Bitbucket"]
                p_idx = providers.index(w_details.get("repository_provider")) if w_details.get("repository_provider") in providers else 0
                new_provider = st.selectbox("Repository provider", providers, index=p_idx)

                new_repo_count = st.number_input("Connected repository count", min_value=0, max_value=100, value=int(w_details.get("connected_repo_count", 1)))
                access_opts = ["Private (Isolated)", "Team Shared", "Public Read-Only"]
                acc_idx = access_opts.index(w_details.get("workspace_access_permissions")) if w_details.get("workspace_access_permissions") in access_opts else 0
                new_access = st.selectbox("Workspace access permissions", access_opts, index=acc_idx)

            if st.form_submit_button("Save Workspace Details", type="primary"):
                w_details["workspace_name"] = new_ws_name
                w_details["workspace_role"] = new_ws_role
                w_details["workspace_site"] = new_ws_site
                w_details["preferred_project_template"] = new_template
                w_details["default_repository"] = new_repo
                w_details["repository_provider"] = new_provider
                w_details["connected_repo_count"] = new_repo_count
                w_details["workspace_access_permissions"] = new_access

                metadata["workspace_details"] = w_details
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Workspace details updated!", icon=":material/domain:")
                st.rerun()

    # ==========================================================================
    # TAB 6: Integrations
    # ==========================================================================
    with tabs[5]:
        st.subheader("Connected Integrations & Cloud Sync")
        st.caption("Manage authentication links to version control systems, Google Cloud storage, and real-time synchronization.")

        with st.form("form_integrations"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Version Control & Accounts")
                new_gh = st.checkbox("GitHub connection status", value=bool(integ.get("github_connection_status", False)))
                new_gl = st.checkbox("GitLab connection status", value=bool(integ.get("gitlab_connection_status", False)))
                new_gaccount = st.checkbox("Connected Google account status", value=bool(integ.get("connected_google_account_status", False)))

            with c2:
                st.markdown("#### Cloud Storage Providers")
                storage_providers = ["Local Disk", "Google Cloud Storage", "AWS S3", "Hugging Face Hub"]
                current_providers = [p for p in integ.get("connected_cloud_storage_providers", ["Local Disk"]) if p in storage_providers]
                new_storages = st.multiselect("Connected cloud storage providers", storage_providers, default=current_providers)

                sync_opts = ["Real-time auto-sync", "On manual trigger", "Daily digest"]
                s_idx = sync_opts.index(integ.get("integration_synchronisation_preferences")) if integ.get("integration_synchronisation_preferences") in sync_opts else 0
                new_sync = st.selectbox("Integration synchronisation preferences", sync_opts, index=s_idx)

            st.divider()
            st.markdown("#### Connected Integrations Ledger")
            cur_integ_list = ", ".join(integ.get("connected_integration_list", []))
            new_integ_str = st.text_input("Active integration identifiers (comma-separated)", value=cur_integ_list)

            if st.form_submit_button("Save Integration Preferences", type="primary"):
                integ["github_connection_status"] = new_gh
                integ["gitlab_connection_status"] = new_gl
                integ["connected_google_account_status"] = new_gaccount
                integ["connected_cloud_storage_providers"] = new_storages
                integ["integration_synchronisation_preferences"] = new_sync
                integ["connected_integration_list"] = [i.strip() for i in new_integ_str.split(",") if i.strip()]

                metadata["integrations"] = integ
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Integration preferences saved!", icon=":material/hub:")
                st.rerun()

    # ==========================================================================
    # TAB 7: Usage & Activity
    # ==========================================================================
    with tabs[6]:
        st.subheader("Usage Telemetry & Engagement Summary")
        st.caption("Audit real-time research session volume, total AI requests, feature adoption, and onboarding progression.")

        ca, cb, cc, cd = st.columns(4)
        with ca:
            st.metric("Total Experiments", u_act.get("total_projects_created", 1))
        with cb:
            st.metric("Research Sessions", u_act.get("total_research_sessions", 3))
        with cc:
            st.metric("Total AI Requests", u_act.get("total_ai_requests", 0))
        with cd:
            st.metric("Monthly AI Usage", f"{u_act.get('monthly_ai_usage', 0)} req")

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Feature Usage Breakdown")
            breakdown = u_act.get("feature_usage_summary", {})
            for feature_name, count in breakdown.items():
                st.write(f"• **{feature_name.replace('_', ' ').title()}**: {count} interactions")

        with c2:
            st.markdown("#### Activity Lifecycle")
            st.write(f"• **Last active timestamp**: `{u_act.get('last_active_timestamp', '')}`")
            st.write(f"• **Onboarding completion status**: `{'Completed' if u_act.get('onboarding_completion_status') else 'In Progress'}`")
            st.write(f"• **Last onboarding step**: {u_act.get('last_onboarding_step', '')}")
            st.write(f"• **Product engagement summary**: {u_act.get('product_engagement_summary', 'Active Daily Researcher')}")

    # ==========================================================================
    # TAB 8: Security & Privacy
    # ==========================================================================
    with tabs[7]:
        st.subheader("Security, Privacy & Data Sovereignty")
        st.caption("Audit active cryptographic sessions, manage privacy consents, and execute instant data export or erasure.")

        with st.form("form_security_privacy"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Consent Management")
                new_analytics = st.checkbox("Analytics consent (anonymized system telemetry)", value=bool(sec_priv.get("analytics_consent", True)))
                new_marketing = st.checkbox("Marketing consent (product updates)", value=bool(sec_priv.get("marketing_consent", False)))
                new_data_proc = st.checkbox("Data processing consent (LLM synthesis)", value=bool(sec_priv.get("data_processing_consent", True)))

            with c2:
                st.markdown("#### Privacy Preferences & Retention")
                priv_modes = ["Strict Local (Zero external telemetry)", "Protected Cloud", "Full Sync"]
                p_idx = priv_modes.index(sec_priv.get("privacy_preferences")) if sec_priv.get("privacy_preferences") in priv_modes else 0
                new_priv_mode = st.selectbox("Privacy preferences", priv_modes, index=p_idx)

                ret_policies = ["Retain until manual deletion", "Purge after 1 year", "Purge after 90 days"]
                rp_idx = ret_policies.index(sec_priv.get("data_retention_preference")) if sec_priv.get("data_retention_preference") in ret_policies else 0
                new_ret_policy = st.selectbox("Data retention preference", ret_policies, index=rp_idx)

            st.write(f"• **Active Sessions**: {sec_priv.get('active_session_count', 1)}")
            st.write(f"• **Last Security Event**: {sec_priv.get('last_security_event', 'Authenticated from local session')}")

            if st.form_submit_button("Save Security & Privacy Settings", type="primary"):
                now_iso = datetime.now(timezone.utc).isoformat()
                sec_priv["analytics_consent"] = new_analytics
                sec_priv["marketing_consent"] = new_marketing
                sec_priv["data_processing_consent"] = new_data_proc
                sec_priv["privacy_preferences"] = new_priv_mode
                sec_priv["data_retention_preference"] = new_ret_policy
                sec_priv["consent_timestamps"] = {
                    "analytics": now_iso,
                    "data_processing": now_iso,
                }

                metadata["security_privacy"] = sec_priv
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Security and privacy preferences updated!", icon=":material/lock:")
                st.rerun()

        st.divider()
        st.markdown("#### Data Export & Erasure Sovereignty")
        export_bundle_json = user_metadata_manager.export_user_data_bundle(connection, user_id)
        st.download_button(
            label="Download Complete Research & Metadata Archive (.JSON)",
            data=export_bundle_json,
            file_name=f"aster_research_export_{user_id[:8]}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            help="Generates an audit-ready JSON bundle containing all your experiments, research contexts, memories, and full metadata ledger.",
        )

    # ==========================================================================
    # TAB 9: Personalization & Memory
    # ==========================================================================
    with tabs[8]:
        st.subheader("Personalization & Persistent Memory")
        st.caption("Define persistent system prompts, personal coding standards, and research tone applied across all AI inference.")

        with st.form("form_personalization_memory"):
            new_saved_instr = st.text_area(
                "Saved user instructions (Injected into every Gemini experiment structuring prompt)",
                value=pers_mem.get("saved_user_instructions", ""),
                height=90,
                help="E.g. Always quantify delta over baseline and note hardware configuration.",
            )

            c1, c2 = st.columns(2)
            with c1:
                styles = ["Hypothesis-first", "Data-first exploration", "Benchmark comparison", "Mathematical derivation"]
                s_idx = styles.index(pers_mem.get("preferred_working_style")) if pers_mem.get("preferred_working_style") in styles else 0
                new_style = st.selectbox("Preferred working style", styles, index=s_idx)

                conventions = ["PEP 8 + Type Hints (Python)", "JAX Pure Functional", "PyTorch Lightning", "Clean Minimalist"]
                c_idx = conventions.index(pers_mem.get("preferred_coding_conventions")) if pers_mem.get("preferred_coding_conventions") in conventions else 0
                new_conv = st.selectbox("Preferred coding conventions", conventions, index=c_idx)

            with c2:
                tones = ["Rigorous & Academic", "Direct & Concise", "Exploratory & Collaborative", "Socratic"]
                t_idx = tones.index(pers_mem.get("preferred_communication_tone")) if pers_mem.get("preferred_communication_tone") in tones else 0
                new_tone = st.selectbox("Preferred communication tone", tones, index=t_idx)

                new_spin = st.text_input("Spin projects", value=pers_mem.get("spin_projects", "Autonomous Evaluation Harnesses"))

            new_custom_ai = st.text_area(
                "Custom AI instructions",
                value=pers_mem.get("custom_ai_instructions", ""),
                height=90,
                help="Formatting constraints, mathematical rigor directives, or citation rules.",
            )

            new_fav_features = st.multiselect(
                "Favourite features",
                options=["Voice-to-Experiment", "Research Graph", "Preprint Radar", "Run Comparison Matrix", "Weekly Digest"],
                default=pers_mem.get("favourite_features", ["Voice-to-Experiment", "Research Graph"]),
            )

            new_pers_enabled = st.checkbox("Enable personalization memory across workspace", value=bool(pers_mem.get("personalization_settings", True)))

            if st.form_submit_button("Save Personalization Directives", type="primary"):
                pers_mem["saved_user_instructions"] = new_saved_instr
                pers_mem["preferred_working_style"] = new_style
                pers_mem["preferred_coding_conventions"] = new_conv
                pers_mem["preferred_communication_tone"] = new_tone
                pers_mem["spin_projects"] = new_spin
                pers_mem["custom_ai_instructions"] = new_custom_ai
                pers_mem["favourite_features"] = new_fav_features
                pers_mem["personalization_settings"] = new_pers_enabled

                metadata["personalization_memory"] = pers_mem
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("Personalization directives saved!", icon=":material/psychology:")
                st.rerun()

    # ==========================================================================
    # TAB 10: System Metadata
    # ==========================================================================
    with tabs[9]:
        st.subheader("System Metadata & Versioning")
        st.caption("Low-level platform state flags, schema contract versions, and migration ledgers.")

        with st.form("form_system_metadata"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Metadata schema version", value=sys_meta.get("metadata_schema_version", "1.2.0"), disabled=True)
                st.text_input("Record creation timestamp", value=sys_meta.get("record_creation_timestamp", ""), disabled=True)
                st.text_input("Record update timestamp", value=sys_meta.get("record_update_timestamp", ""), disabled=True)

            with c2:
                st.text_input("Data source import status", value=sys_meta.get("data_source_import_status", "Synchronized with Aster SQLite v3.43"), disabled=True)
                st.text_input("Migration version", value=str(sys_meta.get("migration_version", 1)), disabled=True)

            st.markdown("#### Internal Flags")
            flags = sys_meta.get("internal_flags", {})
            f1, f2, f3 = st.columns(3)
            with f1:
                flag_beta = st.checkbox("Beta features enabled", value=bool(flags.get("beta_features_enabled", True)))
            with f2:
                flag_sandbox = st.checkbox("Sandbox execution mode", value=bool(flags.get("sandbox_mode", False)))
            with f3:
                flag_fast = st.checkbox("Fast distillation pipeline", value=bool(flags.get("fast_distillation", True)))

            if st.form_submit_button("Save System Metadata Flags", type="primary"):
                flags["beta_features_enabled"] = flag_beta
                flags["sandbox_mode"] = flag_sandbox
                flags["fast_distillation"] = flag_fast
                sys_meta["internal_flags"] = flags

                metadata["system_metadata"] = sys_meta
                user_metadata_manager.save_user_metadata(connection, user_id, metadata)
                st.toast("System metadata updated!", icon=":material/settings:")
                st.rerun()

    # ==========================================================================
    # TAB 11: Metric Ledgers & Reusable Research Context
    # ==========================================================================
    with tabs[10]:
        render_custom_metrics_fn()
        render_research_context_fn()
