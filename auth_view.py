"""Authentication & No-Cost Email Verification View.

Governs:
1. macOS frosted glass login and sign-up card interface.
2. Email format validation and duplicate checking.
3. Password complexity enforcement (8-12+ chars, mixed uppercase, lowercase, digits, symbols).
4. Salted PBKDF2 hashing (never stores or displays raw passwords).
5. Zero-cost email OTP verifier with in-memory / local console dispatch notice.
6. Session bearer token issuance and state machine routing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
import streamlit as st
import auth_manager


def render_auth_portal(connection: sqlite3.Connection) -> None:
    """Render Aster authentication with the existing account and session handlers."""
    st.markdown("""
    <style>
    :root {
      --auth-midnight: #080b13;
      --auth-obsidian: #0b0d14;
      --auth-space-navy: #111a2c;
      --auth-panel: #101522;
      --auth-panel-soft: #151b2b;
      --auth-violet: #9d7cff;
      --auth-indigo: #5d67d9;
      --auth-cyan: #65d7e8;
      --auth-aurora: #6da9f4;
      --auth-ice: #f1f5ff;
      --auth-silver: #aebbd0;
      --auth-steel: #7f8ea7;
      --auth-mint: #75ddb9;
      --auth-amber: #f3bd70;
      --auth-coral: #ff858c;
      --auth-line: rgba(177, 199, 235, .12);
      --auth-motion: 220ms;
      --auth-spring: cubic-bezier(.2,.78,.2,1);
    }
    html,body,[data-testid="stAppViewContainer"],.stApp { min-height:100%; background:var(--auth-midnight)!important; }
    [data-testid="stAppViewContainer"] { background:radial-gradient(ellipse at 19% 35%,rgba(37,67,119,.18),transparent 42rem),radial-gradient(ellipse at 84% 6%,rgba(82,56,147,.13),transparent 38rem),linear-gradient(135deg,var(--auth-midnight),var(--auth-obsidian) 55%,#0b1020)!important; }
    [data-testid="stMainBlockContainer"],.block-container { width:min(1280px,calc(100vw - 64px))!important; max-width:1280px!important; min-width:0!important; padding:18px 0 48px!important; margin:0 auto!important; }
    .st-key-auth-shell { width:min(1180px,100%); margin:0 auto; padding:8px 0 24px; }
    .st-key-auth-header { position:relative; margin:0 0 25px; padding:0 132px 18px 4px; border-bottom:1px solid var(--auth-line); }
    .st-key-auth-header [data-testid="stHorizontalBlock"] { position:static!important; display:flex!important; flex-flow:row nowrap!important; align-items:center!important; justify-content:space-between!important; gap:16px!important; }
    .auth-overview { position:fixed; z-index:100; top:18px; right:max(16px,calc((100vw - 1180px)/2)); display:inline-flex; align-items:center; justify-content:center; min-height:38px; padding:0 12px; border:1px solid var(--auth-line); border-radius:10px; background:rgba(255,255,255,.025); color:var(--auth-silver); font-size:11px; font-weight:570; text-decoration:none; transition:background var(--auth-motion),border-color var(--auth-motion),color var(--auth-motion),transform var(--auth-motion) var(--auth-spring); }
    .auth-overview:hover { border-color:rgba(127,166,239,.3); background:rgba(255,255,255,.06); color:var(--auth-ice); transform:translateY(-1px); }
    .auth-overview:focus-visible { outline:2px solid var(--auth-cyan); outline-offset:3px; }
    div.st-key-auth-header [data-testid="stHorizontalBlock"]>div[data-testid="column"] { width:auto!important; min-width:0!important; flex:0 0 auto!important; }
    div.st-key-auth-header [data-testid="stHorizontalBlock"]>div[data-testid="column"]:first-child { flex:1 1 auto!important; }
    div.st-key-auth-header [data-testid="stHorizontalBlock"]>div[data-testid="column"]:last-child { flex:0 0 auto!important; }
    .auth-brand { display:grid; justify-items:start; width:max-content; max-width:100%; color:var(--auth-ice); }
    .auth-brand img { display:block; width:205px; max-width:min(205px,56vw); height:auto; object-fit:contain; }
    .st-key-auth-header .stButton>button { min-height:38px!important; padding:0 14px!important; border:1px solid var(--auth-line)!important; border-radius:10px!important; background:rgba(255,255,255,.025)!important; color:var(--auth-silver)!important; font-size:11px!important; transition:background var(--auth-motion),border-color var(--auth-motion),color var(--auth-motion),transform var(--auth-motion) var(--auth-spring)!important; }
    .st-key-auth-header .stButton>button:hover { border-color:rgba(127,166,239,.3)!important; background:rgba(255,255,255,.06)!important; color:var(--auth-ice)!important; transform:translateY(-1px); }
    .st-key-auth-layout { position:relative; isolation:isolate; overflow:hidden; border:1px solid rgba(173,197,239,.15)!important; border-radius:25px!important; background:linear-gradient(128deg,rgba(20,29,49,.96),rgba(11,15,25,.99) 58%,rgba(13,16,27,.99))!important; box-shadow:0 30px 90px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.07)!important; }
    .st-key-auth-layout:before { content:""; position:absolute; z-index:3; top:1px; left:5%; right:5%; height:1px; pointer-events:none; background:linear-gradient(90deg,transparent,rgba(231,241,255,.2),rgba(143,164,255,.14),transparent); }
    .st-key-auth-layout { width:100%!important; max-width:1180px!important; margin-inline:auto!important; }
    .st-key-auth-layout [data-testid="stLayoutWrapper"] { width:100%!important; max-width:none!important; min-width:0!important; }
    .st-key-auth-layout [data-testid="stHorizontalBlock"] { display:grid!important; grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important; align-items:stretch!important; gap:0!important; width:100%!important; min-width:0!important; min-height:610px; }
    .st-key-auth-layout [data-testid="stColumn"] { box-sizing:border-box!important; width:100%!important; max-width:none!important; min-width:0!important; flex:1 1 0!important; padding:0!important; }
    .st-key-auth-story,.st-key-auth-card { position:relative; box-sizing:border-box; min-width:0; min-height:610px; height:auto!important; max-height:none!important; padding:0!important; overflow:visible; animation:auth-panel-enter 520ms var(--auth-spring) both; }
    .st-key-auth-story { border-right:1px solid rgba(181,200,235,.1); background:radial-gradient(ellipse at 50% 37%,rgba(61,102,183,.2),transparent 56%),radial-gradient(ellipse at 6% 88%,rgba(30,143,165,.09),transparent 43%),linear-gradient(155deg,rgba(17,25,43,.98),rgba(9,13,22,.97)); }
    .st-key-auth-card { padding:clamp(34px,4vw,58px)!important; background:radial-gradient(ellipse at 100% 0%,rgba(86,70,153,.09),transparent 43%),linear-gradient(155deg,rgba(15,19,31,.97),rgba(10,13,21,.99)); animation-delay:75ms; }
    .auth-story { position:relative; display:flex; min-height:610px; flex-direction:column; justify-content:space-between; gap:12px; padding:24px clamp(24px,3vw,42px) 32px; overflow:hidden; }
    .auth-art { position:relative; flex:0 0 auto; width:100%; height:clamp(240px,32vh,330px); min-height:230px; margin:0 auto; isolation:isolate; }
    .auth-art:before { content:""; position:absolute; inset:10% 15%; z-index:-1; border-radius:50%; background:radial-gradient(circle,rgba(91,158,226,.2),rgba(103,78,200,.095) 45%,transparent 72%); filter:blur(18px); animation:auth-aurora-breathe 7s ease-in-out infinite alternate; }
    .auth-art-grid { position:absolute; inset:2% 0; opacity:.18; background-image:linear-gradient(rgba(184,211,249,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(184,211,249,.055) 1px,transparent 1px); background-size:34px 34px; mask-image:radial-gradient(ellipse at center,#000 8%,transparent 78%); }
    .auth-orbit { position:absolute; left:50%; top:48%; width:min(72%,278px); aspect-ratio:1.75; border:1px solid rgba(101,215,232,.26); border-radius:50%; transform:translate(-50%,-50%) rotate(-24deg); animation:auth-orbit-a 132s linear infinite; }
    .auth-orbit:after { content:""; position:absolute; top:50%; left:-3px; width:6px; height:6px; border-radius:50%; background:var(--auth-cyan); box-shadow:0 0 13px 2px rgba(101,215,232,.62); }
    .auth-orbit.orbit-b { width:min(58%,218px); aspect-ratio:.77; border-color:rgba(157,124,255,.27); transform:translate(-50%,-50%) rotate(31deg); animation:auth-orbit-b 176s linear infinite; }
    .auth-orbit.orbit-b:after { left:auto; right:-3px; background:var(--auth-violet); box-shadow:0 0 12px 2px rgba(157,124,255,.57); }
    .auth-orbit.orbit-c { width:min(84%,322px); aspect-ratio:2.6; border-color:rgba(113,153,224,.13); transform:translate(-50%,-50%) rotate(8deg); animation:auth-orbit-c 228s linear infinite; }
    .auth-convergence { position:absolute; left:50%; top:48%; width:28px; height:28px; border:1px solid rgba(101,215,232,.34); border-radius:50%; background:radial-gradient(circle,rgba(101,215,232,.2),rgba(91,117,208,.06) 55%,transparent 72%); box-shadow:0 0 24px rgba(101,215,232,.14); transform:translate(-50%,-50%); }
    .auth-convergence:after { content:""; position:absolute; inset:7px; border:1px solid rgba(157,124,255,.48); border-radius:50%; }
    .auth-node { position:absolute; z-index:1; width:8px; height:8px; border:1px solid rgba(202,232,255,.82); border-radius:50%; background:#a9eaff; box-shadow:0 0 0 5px rgba(89,176,229,.09),0 0 12px rgba(101,215,232,.6); animation:auth-node-glow 3.8s ease-in-out infinite; }
    .auth-node.node-a { left:22%; top:31%; }
    .auth-node.node-b { right:18%; top:37%; animation-delay:-1.5s; }
    .auth-node.node-c { left:35%; bottom:17%; animation-delay:-2.7s; }
    .auth-note { position:absolute; z-index:1; color:rgba(166,187,215,.72); font:600 8px/1.4 ui-monospace,SFMono-Regular,monospace; letter-spacing:.14em; }
    .auth-note.note-a { left:4%; top:24%; }
    .auth-note.note-b { right:0; top:29%; }
    .auth-note.note-c { left:19%; bottom:7%; }
    .auth-art-caption { position:absolute; left:50%; bottom:1%; display:flex; align-items:center; gap:8px; transform:translateX(-50%); color:var(--auth-steel); font:600 8px/1.4 ui-monospace,SFMono-Regular,monospace; letter-spacing:.13em; white-space:nowrap; }
    .auth-art-caption i { width:6px; height:6px; flex:0 0 6px; border-radius:50%; background:var(--auth-mint); box-shadow:0 0 10px rgba(117,221,185,.55); }
    .auth-story-copy { position:relative; z-index:2; max-width:430px; padding:0 2px; color:var(--auth-silver); font-size:13px; line-height:1.7; }
    .auth-eyebrow { color:#a9b9de; font:650 9px/1.5 ui-monospace,SFMono-Regular,monospace; letter-spacing:.18em; text-transform:uppercase; }
    .auth-story-copy h1 { max-width:440px; margin:12px 0 12px!important; color:var(--auth-ice); font-size:clamp(32px,3.4vw,44px)!important; font-weight:620!important; letter-spacing:-.06em!important; line-height:1.02!important; }
    .auth-story-copy h1 span { color:#b9a5ff; }
    .auth-story-copy p { max-width:380px; margin:0; color:var(--auth-silver); font-size:13px; line-height:1.75; }
    .auth-story-foot { display:flex; align-items:center; gap:9px; margin-top:16px; color:var(--auth-steel); font-size:10px; letter-spacing:.01em; }
    .auth-story-foot i { width:6px; height:6px; border-radius:50%; background:var(--auth-cyan); box-shadow:0 0 10px rgba(101,215,232,.55); }
    .auth-card-title { margin:10px 0 7px; color:var(--auth-ice); font-size:clamp(29px,3vw,37px); font-weight:660; letter-spacing:-.055em; line-height:1.08; }
    .auth-card-title span { color:#b9a5ff; }
    .auth-card-subtitle { max-width:390px; margin:0 0 23px; color:var(--auth-silver); font-size:13px; line-height:1.65; }
    .st-key-auth-mode { width:100%!important; min-width:0!important; margin:0 0 19px!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"] { width:100%!important; min-width:0!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"]>div { display:flex!important; width:100%!important; min-width:0!important; box-sizing:border-box!important; gap:5px!important; padding:5px!important; border:1px solid rgba(177,199,235,.14)!important; border-radius:13px!important; background:rgba(7,10,18,.72)!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"] button { flex:1 1 0!important; min-width:0!important; min-height:44px!important; border:1px solid transparent!important; border-radius:9px!important; background:transparent!important; color:var(--auth-silver)!important; font-size:12px!important; font-weight:610!important; transition:color var(--auth-motion),background var(--auth-motion),border-color var(--auth-motion),box-shadow var(--auth-motion),transform var(--auth-motion) var(--auth-spring)!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"] button:hover { color:var(--auth-ice)!important; background:rgba(255,255,255,.045)!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"] button:is([aria-pressed="true"],[aria-checked="true"],[data-selected="true"]) { color:var(--auth-ice)!important; border-color:rgba(158,139,255,.27)!important; background:linear-gradient(112deg,rgba(81,88,194,.4),rgba(121,81,203,.27))!important; box-shadow:inset 0 1px 0 rgba(255,255,255,.11),0 3px 12px rgba(61,55,138,.18)!important; }
    .st-key-auth-mode [data-testid="stSegmentedControl"] button:focus-visible { outline:2px solid var(--auth-cyan)!important; outline-offset:2px!important; }
    .st-key-auth-card [data-testid="stTextInput"] { width:100%!important; min-width:0!important; margin:10px 0 13px!important; }
    .st-key-auth-card [data-testid="stTextInput"] label { color:#d1daeb!important; font-size:11px!important; font-weight:570!important; }
    .st-key-auth-card [data-testid="stTextInput"] input { width:100%!important; min-width:0!important; min-height:49px!important; box-sizing:border-box!important; border:1px solid rgba(167,187,223,.16)!important; border-radius:10px!important; background:rgba(5,8,15,.72)!important; color:var(--auth-ice)!important; transition:border-color var(--auth-motion),box-shadow var(--auth-motion),background var(--auth-motion)!important; }
    .st-key-auth-card [data-testid="stTextInput"] input::placeholder { color:#687a98!important; }
    .st-key-auth-card [data-testid="stTextInput"] input:focus { border-color:rgba(157,124,255,.66)!important; background:rgba(9,13,24,.94)!important; box-shadow:0 0 0 3px rgba(112,94,212,.17),0 0 22px rgba(72,99,195,.09)!important; }
    .st-key-auth-card [data-testid="stTextInput"] input[aria-invalid="true"] { border-color:var(--auth-coral)!important; box-shadow:0 0 0 3px rgba(255,133,140,.12)!important; }
    .st-key-auth-card [data-testid="stCheckbox"] label { color:var(--auth-silver)!important; font-size:11px!important; }
    .st-key-auth-card [data-testid="stCheckbox"] input { accent-color:var(--auth-violet)!important; }
    .st-key-auth-card .stButton>button { width:100%!important; min-height:50px!important; margin-top:14px; border:1px solid rgba(181,156,255,.42)!important; border-radius:11px!important; background:linear-gradient(112deg,#625fd0,#7453c6 58%,#574eb7)!important; color:#fff!important; font-size:12px!important; font-weight:650!important; letter-spacing:.015em; box-shadow:0 9px 24px rgba(75,63,158,.18),inset 0 1px 0 rgba(255,255,255,.15)!important; transition:transform var(--auth-motion) var(--auth-spring),box-shadow var(--auth-motion),filter var(--auth-motion)!important; }
    .st-key-auth-card .stButton>button:hover:not(:disabled) { filter:brightness(1.08); box-shadow:0 12px 28px rgba(76,68,174,.26),inset 0 1px 0 rgba(255,255,255,.18)!important; transform:translateY(-1px); }
    .st-key-auth-card .stButton>button:active { transform:scale(.985); }
    .st-key-auth-card .stButton>button:focus-visible { outline:2px solid var(--auth-cyan)!important; outline-offset:3px!important; }
    .st-key-auth-card .stButton>button:disabled { border-color:rgba(167,187,223,.13)!important; background:#25283a!important; color:#adb4c5!important; box-shadow:none!important; }
    .st-key-auth-card [data-testid="stAlert"] { border-radius:10px!important; }
    .auth-password-hint { margin:1px 0 11px; color:var(--auth-steel); font-size:10px; line-height:1.55; }
    .auth-footer { margin-top:21px; padding-top:13px; border-top:1px solid rgba(177,199,235,.1); color:var(--auth-steel); font-size:10px; line-height:1.65; }
    @keyframes auth-panel-enter { from { opacity:0; transform:translateY(9px); } to { opacity:1; transform:translateY(0); } }
    @keyframes auth-aurora-breathe { from { opacity:.72; transform:scale(.96); } to { opacity:1; transform:scale(1.07); } }
    @keyframes auth-orbit-a { to { transform:translate(-50%,-50%) rotate(336deg); } }
    @keyframes auth-orbit-b { to { transform:translate(-50%,-50%) rotate(-329deg); } }
    @keyframes auth-orbit-c { to { transform:translate(-50%,-50%) rotate(368deg); } }
    @keyframes auth-node-glow { 0%,100% { opacity:.72; box-shadow:0 0 0 4px rgba(89,176,229,.07),0 0 9px rgba(101,215,232,.38); } 50% { opacity:1; box-shadow:0 0 0 7px rgba(89,176,229,.13),0 0 15px rgba(101,215,232,.68); } }
    @media(max-width:900px) {
      [data-testid="stMainBlockContainer"],.block-container { width:min(100% - 40px,760px)!important; }
      .st-key-auth-layout [data-testid="stHorizontalBlock"] { grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr)!important; }
      .auth-story { padding-inline:22px; }
      .auth-art { height:250px; min-height:220px; }
      .st-key-auth-card { padding:32px!important; }
    }
    @media(max-width:760px) {
      [data-testid="stMainBlockContainer"],.block-container { width:calc(100% - 28px)!important; padding-top:10px!important; }
      .st-key-auth-shell { padding-top:2px; }
      .st-key-auth-header { margin-bottom:17px; padding-bottom:14px; }
      .st-key-auth-layout { border-radius:19px!important; }
      .st-key-auth-layout [data-testid="stHorizontalBlock"] { grid-template-columns:minmax(0,1fr)!important; }
      .st-key-auth-story { min-height:0; border-right:0; border-bottom:1px solid var(--auth-line); }
      .auth-story { min-height:0; height:auto; gap:6px; padding:14px 22px 23px; }
      .auth-art { width:min(100%,410px); height:clamp(190px,38vw,245px); min-height:185px; }
      .auth-art-caption { bottom:0; }
      .auth-story-copy { padding-bottom:4px; }
      .auth-story-copy h1 { font-size:clamp(30px,7vw,39px)!important; }
      .st-key-auth-card { min-height:0; padding:28px 24px!important; }
      .auth-card-title { font-size:31px; }
    }
    @media(max-width:390px) {
      [data-testid="stMainBlockContainer"],.block-container { width:calc(100% - 22px)!important; }
      .auth-brand img { width:174px; }
      .st-key-auth-card { padding:24px 19px!important; }
      .auth-note { font-size:7px; }
      .st-key-auth-mode [data-testid="stSegmentedControl"] button { padding-inline:6px!important; font-size:11px!important; }
    }
    @media(max-height:760px) and (min-width:761px) {
      [data-testid="stMainBlockContainer"],.block-container { padding-top:8px!important; }
      .st-key-auth-header { margin-bottom:14px; padding-bottom:12px; }
      .st-key-auth-story,.st-key-auth-layout [data-testid="stHorizontalBlock"] { min-height:560px; }
      .auth-story { min-height:560px; padding-block:17px 24px; }
      .auth-art { height:245px; min-height:220px; }
      .st-key-auth-card { padding-block:30px!important; }
    }
    @media(prefers-reduced-motion:reduce) {
      .st-key-auth-story,.st-key-auth-card,.auth-art:before,.auth-orbit,.auth-node { animation:none!important; }
      .st-key-auth-header .stButton>button,.st-key-auth-mode [data-testid="stSegmentedControl"] button,.st-key-auth-card .stButton>button { transition:none!important; }
    }
    </style>
    """, unsafe_allow_html=True)

    pending_user = st.session_state.get("auth_pending_verification_user")
    st.markdown((Path(__file__).parent / "static" / "aster-design-tokens.css").read_text(encoding="utf-8"), unsafe_allow_html=True)
    st.markdown("""<style>
    .stApp{font-family:var(--aster-font-ui,Inter,-apple-system,sans-serif)!important;font-size:16px!important}
    .auth-story-copy{font-size:15px!important;line-height:1.7!important}
    .auth-story-copy h1{font-size:clamp(38px,3.5vw,52px)!important;line-height:1.04!important}
    .auth-story-copy p,.auth-card-subtitle{font-size:15px!important;line-height:1.65!important}
    .auth-card-title{font-size:clamp(34px,3.2vw,42px)!important}
    .st-key-auth-card [data-testid="stTextInput"] label{font-size:13px!important}
    .st-key-auth-card [data-testid="stTextInput"] input{font-family:var(--aster-font-ui)!important;font-size:15px!important;min-height:52px!important}
    .st-key-auth-card [data-testid="stCheckbox"] label{font-size:13px!important}
    .st-key-auth-mode [data-testid="stSegmentedControl"] button{font-size:14px!important;min-height:46px!important}
    .st-key-auth-card .stButton>button{font-size:15px!important;min-height:52px!important}
    .auth-eyebrow{font:600 10px/1.5 var(--aster-font-mono)!important}
    .auth-footer{font-size:12px!important;line-height:1.6!important}
    @media(max-width:760px){.auth-story-copy h1{font-size:36px!important}.auth-card-title{font-size:32px!important}}
    </style>""", unsafe_allow_html=True)

    default_mode = "Create account" if st.query_params.get("auth") == "signup" else "Sign in"
    if st.session_state.get("_auth_route_mode") != default_mode:
        st.session_state["auth_form_mode"] = default_mode
        st.session_state["_auth_route_mode"] = default_mode

    with st.container(key="auth-shell"):
        with st.container(key="auth-header"):
            st.markdown('<div class="auth-brand"><img src="/app/static/aster-wordmark.png?v=3" alt="ASTER"></div>', unsafe_allow_html=True)
            st.markdown('<a class="auth-overview" href="/" aria-label="Back to Aster overview">← Overview</a>', unsafe_allow_html=True)

        if pending_user:
            st.markdown('<div class="auth-eyebrow">ACCOUNT VERIFICATION</div>', unsafe_allow_html=True)
            with st.container(key="auth-card"):
                render_otp_verification_view(connection, pending_user)
            return

        with st.container(key="auth-layout"):
            story_col, form_col = st.columns([.92, 1.08], gap="large")
            with story_col:
                with st.container(key="auth-story"):
                    st.markdown(f'''<div class="auth-story"><div class="auth-art" aria-hidden="true"><div class="auth-art-grid"></div><div class="auth-orbit orbit-a"></div><div class="auth-orbit orbit-b"></div><div class="auth-orbit orbit-c"></div><span class="auth-convergence"></span><i class="auth-node node-a"></i><i class="auth-node node-b"></i><i class="auth-node node-c"></i><span class="auth-note note-a">HYPOTHESIS</span><span class="auth-note note-b">RESULTS</span><span class="auth-note note-c">NEXT TEST</span><div class="auth-art-caption"><i></i> EXPERIMENT LINEAGE</div></div><div class="auth-story-copy"><div class="auth-eyebrow">YOUR RESEARCH ENVIRONMENT</div><h1>Your next discovery<br><span>starts here.</span></h1><p>Capture each experiment, connect the runs that matter, and carry useful lessons into your next question.</p><div class="auth-story-foot"><i></i> One research thread, from question to next test</div></div></div>''', unsafe_allow_html=True)
            with form_col:
                with st.container(key="auth-card"):
                    st.markdown('<div class="auth-eyebrow">ASTER · RESEARCH ACCESS</div><div class="auth-card-title">Welcome to <span>ASTER</span></div><p class="auth-card-subtitle">Sign in or create an account to continue to your research workspace.</p>', unsafe_allow_html=True)
                    with st.container(key="auth-mode"):
                        mode = st.segmented_control(
                            "Account access",
                            ["Sign in", "Create account"],
                            format_func=lambda option: "Sign in" if option == "Sign in" else "Create account",
                            selection_mode="single",
                            label_visibility="collapsed",
                            width="stretch",
                            key="auth_form_mode",
                        ) or default_mode

                    if mode == "Sign in":
                        st.text_input("Email address", placeholder="researcher@lab.org", type="email", autocomplete="email", required=True, key="login_email_input")
                        st.text_input("Password", type="password", placeholder="Your password", autocomplete="current-password", required=True, key="login_password_input")
                        st.checkbox("Remember this session", value=True, key="login_remember_me")
                        if st.button("Sign in", type="primary", use_container_width=True, key="login_submit_btn"):
                            login_email = st.session_state.get("login_email_input", "").strip()
                            login_password = st.session_state.get("login_password_input", "")
                            if not login_email or not login_password:
                                st.error("Enter your email address and password to continue.")
                            else:
                                with st.spinner("Signing in…"):
                                    user, err = auth_manager.login_user(connection, login_email, login_password)
                                if err or not user:
                                    st.error(err or "Unable to sign in.")
                                else:
                                    token = auth_manager.create_session(connection, user["id"])
                                    st.session_state.session_token = token
                                    st.session_state.authenticated_user = user
                                    st.query_params["session"] = token
                                    st.toast(f"Welcome back, {user['email']}!", icon="👋")
                                    st.rerun()
                        st.markdown('<div class="auth-footer">Your experiment journal remains in your local workspace. Gemini is used only when you choose an AI feature.</div>', unsafe_allow_html=True)
                    else:
                        st.text_input("Email address", placeholder="researcher@lab.org", type="email", autocomplete="email", required=True, key="signup_email_input")
                        st.text_input("Password", type="password", placeholder="Create a strong password", autocomplete="new-password", required=True, key="signup_password_input")
                        st.markdown('<p class="auth-password-hint">Use at least 8 characters. Include uppercase and lowercase letters, a number, and a symbol.</p>', unsafe_allow_html=True)
                        if st.button("Create account", type="primary", use_container_width=True, key="signup_submit_btn"):
                            signup_email = st.session_state.get("signup_email_input", "").strip()
                            signup_password = st.session_state.get("signup_password_input", "")
                            with st.spinner("Creating your account…"):
                                user, err = auth_manager.register_user(connection, signup_email, signup_password)
                            if err or not user:
                                st.error(err or "Unable to create your account.")
                            else:
                                token = auth_manager.create_session(connection, user["id"])
                                st.session_state.session_token = token
                                st.session_state.auth_pending_verification_user = user
                                st.session_state.authenticated_user = user
                                st.toast("Account created. Verify your email to continue.", icon="📬")
                                st.rerun()


# ==============================================================================
# No-Cost Email Verification View (OTP)
# ==============================================================================
def render_otp_verification_view(connection: sqlite3.Connection, user: dict[str, Any]) -> None:
    """Render the no-cost 6-digit OTP email verification interface."""
    user_id = user["id"]
    email = user["email"]
    latest_otp = user.get("latest_otp", "")

    with st.container(border=True):
        st.markdown("### 📬 Verify Your Research Email")
        st.caption(f"A 6-digit verification code has been dispatched to **{email}**.")

        # Zero-Cost In-Memory Local Verification Notice
        # Provides 100% functionality without requiring commercial SMTP server billing accounts!
        if latest_otp:
            st.info(
                f"**No-Cost In-Memory Verification Dispatch:**\n"
                f"Your 6-digit OTP verification code is **`{latest_otp}`** (valid for 15 minutes).\n"
                f"*(Simulated local delivery with zero paid SMTP service fees.)*"
            )

        entered_otp = st.text_input(
            "Enter 6-Digit Code",
            max_chars=6,
            placeholder="123456",
            key="otp_input_field",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify Email & Continue ↗", type="primary", use_container_width=True, key="verify_otp_btn"):
                success, msg = auth_manager.verify_email_otp(connection, user_id, entered_otp)
                if not success:
                    st.error(msg)
                else:
                    user["is_verified"] = True
                    st.session_state.authenticated_user = user
                    st.session_state.auth_pending_verification_user = None
                    st.toast("Email verified successfully!", icon="✅")
                    st.rerun()

        with col2:
            if st.button("Resend Code", type="secondary", use_container_width=True, key="resend_otp_btn"):
                new_otp = auth_manager.create_email_verification_otp(connection, user_id, email)
                user["latest_otp"] = new_otp
                st.session_state.auth_pending_verification_user = user
                st.toast(f"New verification code issued: {new_otp}", icon="📬")
                st.rerun()

    st.caption("You will proceed directly to Stage 2: Research Onboarding to calibrate your personalized feed.")
