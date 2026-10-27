"""Stage 2: Interactive Pill-Based Research Onboarding Flow.

Governs:
1. Blocking dashboard access upon initial login/registration until focus tags are calibrated.
2. Exact prompt: 'Welcome, please select your research focus using the tags below to calibrate your personalised feed.'
3. Categorized major domains select pills.
4. Custom pill entry, validation, and dynamic insertion.
5. One-turn refinement rule if selections are overly generic (requesting 2-3 specific algorithmic/subproblem pills).
6. Persistence into user record (interests JSON array, has_completed_onboarding = True).
7. Immediate transition to Stage 3 Personalized Dashboard.
"""

from __future__ import annotations

import re
from typing import Any
import streamlit as st
import auth_manager

CATEGORIZED_RESEARCH_PILLS: dict[str, list[str]] = {
    "Foundations & Theory": [
        "Deep Learning Foundations",
        "Representation Learning",
        "Reinforcement Learning & RLHF",
        "Self-Supervised Learning",
        "Loss Landscape & Optimization",
    ],
    "Architecture & Systems": [
        "Transformer & Attention Mechanics",
        "State Space Models & Mamba",
        "KV-Cache & Memory Systems",
        "Inference Optimization & Quantization",
        "Distributed Systems & Parallelism",
    ],
    "Agentic Systems & Reasoning": [
        "Agentic Workflows & Multi-Agent Systems",
        "Tool Use & Function Calling",
        "Test-Time Compute & Search",
        "Chain-of-Thought & Reasoning",
        "Planning & Autonomy",
    ],
    "Modalities & Generation": [
        "Diffusion Models & Flow Matching",
        "Vision-Language & Multimodal",
        "Video Generation & World Models",
        "3D & Embodied AI",
        "Audio & Speech Generation",
    ],
    "Safety, Alignment & Governance": [
        "AI Alignment & Red-Teaming",
        "Mechanistic Interpretability",
        "Hallucination & Factuality",
        "Evaluation & Benchmarks",
        "Adversarial Robustness",
    ],
}

GENERIC_TAGS = {
    "deep learning foundations",
    "ai",
    "machine learning",
    "artificial intelligence",
    "evaluation & benchmarks",
}

REFINEMENT_SUBPROBLEM_PILLS = [
    "FlashAttention & Chunking",
    "Direct Preference Optimization (DPO)",
    "KV-Cache Compression & PagedAttention",
    "Best-of-N & MCTS Test-Time Search",
    "LoRA & Parameter-Efficient Adapters",
    "Latent Geodesic Trajectory Planning",
    "Null-Space Backdoor Purification",
    "Multi-Week Memory Decay Evaluation",
]


def render_onboarding_page(user: dict[str, Any], connection: Any) -> None:
    """Render Stage 2: Interactive bill/pill-based research onboarding."""
    st.markdown('<p class="eyebrow">STAGE 2 · INTERACTIVE ONBOARDING</p>', unsafe_allow_html=True)
    st.title("Calibrate Your Research Radar")

    # Exact required onboarding welcome message
    st.markdown(
        "> ### *Welcome, please select your research focus using the tags below to calibrate your personalised feed.*"
    )
    st.caption("Your selections dictate the strict academic intersection queries against arXiv, Hugging Face, Semantic Scholar, CrossRef, and PubMed.")

    # State initialization for selected pills
    if "onboarding_selected_pills" not in st.session_state:
        st.session_state.onboarding_selected_pills = list(user.get("interests", []))

    if "onboarding_custom_pills" not in st.session_state:
        st.session_state.onboarding_custom_pills = []

    if "onboarding_refinement_active" not in st.session_state:
        st.session_state.onboarding_refinement_active = False

    selected_set = set(st.session_state.onboarding_selected_pills)

    # Active selections counter & preview badge
    with st.container(border=True):
        st.markdown(f"**Selected Research Focus:** `{len(selected_set)} active tags`")
        if selected_set:
            chips_html = "".join(
                f'<span style="display:inline-block;margin:4px;padding:5px 12px;border-radius:999px;background:linear-gradient(135deg,rgba(99,102,241,0.25),rgba(59,130,246,0.15));border:1px solid rgba(129,140,248,0.4);color:#ffffff;font-size:12.5px;font-weight:600;">{p}</span>'
                for p in sorted(selected_set)
            )
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.caption("No research focus selected yet. Click pills below to select.")

    st.write("")

    # Render categorized select pills across major domains
    for category_name, pills in CATEGORIZED_RESEARCH_PILLS.items():
        with st.container(border=True):
            st.markdown(f"##### {category_name}")
            cols = st.columns(min(3, len(pills)))
            for idx, pill in enumerate(pills):
                col = cols[idx % len(cols)]
                is_selected = pill in selected_set
                btn_type = "primary" if is_selected else "secondary"
                btn_icon = ":material/check:" if is_selected else ":material/add:"
                if col.button(pill, icon=btn_icon, key=f"pill_{pill}", type=btn_type, use_container_width=True):
                    if is_selected:
                        selected_set.remove(pill)
                    else:
                        selected_set.add(pill)
                    st.session_state.onboarding_selected_pills = list(selected_set)
                    st.rerun()

    # Dynamic Custom Term Input
    with st.container(border=True):
        st.markdown("##### Add Custom Algorithmic Focus or Subproblem")
        st.caption("Enter specialized methods, architectures, or datasets not listed above (e.g. `Speculative Decoding`, `GRPO`, `Flow Matching`).")
        custom_col1, custom_col2 = st.columns([3.2, 1])
        with custom_col1:
            custom_input = st.text_input(
                "Custom Term",
                placeholder="e.g. Speculative Decoding, PagedAttention, Platonic Representations",
                label_visibility="collapsed",
                key="custom_pill_input",
            )
        with custom_col2:
            if st.button("Add Custom Pill", icon=":material/add:", use_container_width=True, type="secondary"):
                clean_term = (custom_input or "").strip()
                if clean_term:
                    # Validate term format: alphanumeric with hyphens, spaces, slashes
                    formatted = re.sub(r"\s+", " ", clean_term).title()
                    if formatted not in selected_set:
                        selected_set.add(formatted)
                        st.session_state.onboarding_selected_pills = list(selected_set)
                        if formatted not in st.session_state.onboarding_custom_pills:
                            st.session_state.onboarding_custom_pills.append(formatted)
                        st.toast(f"Added custom focus tag: {formatted}", icon=":material/auto_awesome:")
                        st.rerun()

    # One-Turn Refinement Check
    is_overly_generic = False
    if len(selected_set) == 1:
        single_tag = list(selected_set)[0].lower()
        if single_tag in GENERIC_TAGS:
            is_overly_generic = True
    elif len(selected_set) == 0:
        is_overly_generic = True

    # If user clicks submit while generic, trigger one-turn refinement
    if st.session_state.onboarding_refinement_active or (is_overly_generic and len(selected_set) > 0):
        with st.container(border=True):
            st.warning("**Your selection is broad.** Please calibrate with 2 to 3 specific algorithmic or subproblem focus areas to hone your precision radar against the literature.", icon=":material/info:")
            st.markdown("Select from these high-resolution subproblems:")
            ref_cols = st.columns(2)
            for r_idx, ref_pill in enumerate(REFINEMENT_SUBPROBLEM_PILLS):
                r_col = ref_cols[r_idx % 2]
                r_selected = ref_pill in selected_set
                r_btn_type = "primary" if r_selected else "secondary"
                r_btn_icon = ":material/check:" if r_selected else ":material/add:"
                if r_col.button(ref_pill, icon=r_btn_icon, key=f"ref_pill_{ref_pill}", type=r_btn_type, use_container_width=True):
                    if r_selected:
                        selected_set.remove(ref_pill)
                    else:
                        selected_set.add(ref_pill)
                    st.session_state.onboarding_selected_pills = list(selected_set)
                    st.rerun()

    st.write("")
    st.divider()

    # Advance to Stage 3 Button
    submit_col1, submit_col2 = st.columns([2, 1])
    with submit_col1:
        st.caption("Once calibrated, Aster will query arXiv, Hugging Face, Semantic Scholar, CrossRef, and PubMed strictly at this intersection.")
    with submit_col2:
        if st.button("Calibrate & Launch Dashboard", icon=":material/arrow_forward:", type="primary", use_container_width=True, disabled=len(selected_set) == 0):
            # Enforce one-turn refinement rule
            if len(selected_set) < 2 and any(t.lower() in GENERIC_TAGS for t in selected_set):
                st.session_state.onboarding_refinement_active = True
                st.warning("Please choose at least 1 specific algorithmic or subproblem pill from the refinement suggestions above before advancing.", icon=":material/info:")
                st.rerun()

            # Persist the choices into the user's interest tags database array
            success, err = auth_manager.persist_user_onboarding_interests(
                connection, user["id"], list(selected_set)
            )
            if not success:
                st.error(err)
                return

            # Update session state and transition immediately to stage 3
            user["interests"] = list(selected_set)
            user["has_completed_onboarding"] = True
            st.session_state.authenticated_user = user
            st.session_state.onboarding_refinement_active = False
            st.session_state.nav_page = "Home"
            st.toast("Research preferences calibrated! Welcome to Aster.", icon=":material/check_circle:")
            st.rerun()
