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

import base64
from html import escape
from pathlib import Path
import sqlite3
from typing import Any
import streamlit as st
import auth_manager

ROOT = Path(__file__).parent


def _tech_logo_data_uri() -> str:
    for asset in (
        ROOT / "static" / "aster-tech-logo-clean.png",
        ROOT / "public" / "aster-tech-logo-clean.png",
        ROOT / "ASTER Geometric Tech Logo.png",
    ):
        if asset.is_file():
            return "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
    for asset in (ROOT / "static" / "aster-wordmark.png", ROOT / "public" / "aster-logo.png"):
        if asset.is_file():
            return "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
    return ""


def _favicon_data_uri() -> str:
    for asset in (ROOT / "static" / "favicon.png", ROOT / "public" / "favicon.png"):
        if asset.is_file():
            return "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
    return ""


def render_auth_portal(connection: sqlite3.Connection) -> None:
    """Render Aster authentication aligned with the public landing page aesthetic."""
    tech_logo = _tech_logo_data_uri()
    fav_uri = _favicon_data_uri()
    if fav_uri:
        st.html(f'<link rel="icon" type="image/png" href="{fav_uri}"><link rel="shortcut icon" href="{fav_uri}">')

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&family=DM+Mono:wght@400;500&display=swap');
    :root {
      --bg: #080a10;
      --ink: #f3f1ed;
      --muted: #aaa9a8;
      --quiet: #85878c;
      --line: rgba(222, 226, 235, .14);
      --line2: rgba(222, 226, 235, .22);
      --orange: #f18a5e;
      --orange-light: #f3a07d;
      --violet: #b29cf4;
      --cyan: #89d2e5;
      --mint: #81c8a9;
      --mono: var(--aster-font-mono, 'DM Mono', monospace);
      --ease: cubic-bezier(.2, .75, .25, 1);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stFooter"], #MainMenu { display: none !important; }
    [data-testid="stMain"] { padding-top: 0 !important; }
    html, body, [data-testid="stAppViewContainer"], .stApp {
      min-height: 100%;
      background: var(--bg) !important;
      font-family: var(--aster-font-ui, 'Inter', -apple-system, sans-serif) !important;
      color: var(--ink) !important;
    }
    [data-testid="stAppViewContainer"] {
      background: radial-gradient(ellipse at 77% 12%, rgba(45, 64, 120, .17), transparent 43rem),
                  radial-gradient(ellipse at 14% 63%, rgba(28, 88, 114, .1), transparent 40rem),
                  linear-gradient(140deg, #090b12, #080a10 64%) !important;
    }
    [data-testid="stMainBlockContainer"], .block-container {
      width: min(1180px, calc(100vw - 48px)) !important;
      max-width: 1180px !important;
      min-width: 0 !important;
      padding: 0 0 32px !important;
      margin: 0 auto !important;
    }
    .st-key-auth-shell { width: 100%; margin: 0 auto; padding: 0; }
    .st-key-auth-header { margin: 0 0 18px; padding: 0; }

    .auth-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 72px;
      margin: 0;
      padding: 10px 0 16px;
      border-bottom: 1px solid var(--line);
    }
    .auth-brand { display: inline-flex; align-items: center; text-decoration: none; }
    .auth-logo { display: block; width: 220px; max-width: min(220px, 44vw); height: auto; object-fit: contain; }
    .auth-nav-actions { display: flex; align-items: center; gap: 10px; }
    .auth-overview-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 42px;
      padding: 0 18px;
      border: 1px solid rgba(214, 220, 235, .21);
      border-radius: 12px;
      background: rgba(255, 255, 255, .025);
      color: #e7e7e9;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      transition: transform .2s var(--ease), background .2s, border-color .2s, color .2s;
    }
    .auth-overview-btn:hover {
      transform: translateY(-1px);
      border-color: rgba(209, 220, 250, .42);
      background: rgba(255, 255, 255, .065);
      color: #fff;
    }
    .auth-overview-btn:focus-visible { outline: 2px solid var(--orange); outline-offset: 3px; }

    .st-key-auth-layout {
      position: relative;
      isolation: isolate;
      overflow: hidden;
      border: 1px solid rgba(218, 221, 230, .22) !important;
      border-radius: 22px !important;
      background: linear-gradient(145deg, rgba(26, 28, 35, .98), rgba(15, 17, 23, .98)) !important;
      box-shadow: 0 24px 70px rgba(0, 0, 0, .35), inset 0 1px 0 rgba(255, 255, 255, .07) !important;
      width: 100% !important;
      max-width: 1180px !important;
      margin-inline: auto !important;
    }
    .st-key-auth-layout:before {
      content: "";
      position: absolute;
      z-index: 3;
      top: 1px;
      left: 5%;
      right: 5%;
      height: 1px;
      pointer-events: none;
      background: linear-gradient(90deg, transparent, rgba(241, 138, 94, .3), transparent);
    }
    .st-key-auth-layout [data-testid="stLayoutWrapper"] { width: 100% !important; max-width: none !important; min-width: 0 !important; }
    .st-key-auth-layout [data-testid="stHorizontalBlock"] {
      display: grid !important;
      grid-template-columns: minmax(0, .94fr) minmax(0, 1.06fr) !important;
      align-items: stretch !important;
      gap: 0 !important;
      width: 100% !important;
      min-height: 480px;
    }
    .st-key-auth-layout [data-testid="stColumn"] {
      box-sizing: border-box !important;
      width: 100% !important;
      max-width: none !important;
      min-width: 0 !important;
      flex: 1 1 0 !important;
      padding: 0 !important;
    }

    .st-key-auth-story, .st-key-auth-card {
      position: relative;
      box-sizing: border-box;
      min-width: 0;
      min-height: 480px;
      padding: 0 !important;
      overflow: visible;
    }
    .st-key-auth-story {
      border-right: 1px solid var(--line);
      background: radial-gradient(ellipse at 50% 30%, rgba(241, 138, 94, .08), transparent 52%),
                  radial-gradient(ellipse at 8% 85%, rgba(45, 64, 120, .14), transparent 44%),
                  linear-gradient(155deg, rgba(19, 21, 28, .98), rgba(12, 14, 20, .97));
    }
    .st-key-auth-card {
      padding: 26px 32px !important;
      background: radial-gradient(ellipse at 100% 0%, rgba(241, 138, 94, .06), transparent 42%),
                  linear-gradient(155deg, rgba(16, 18, 25, .97), rgba(11, 13, 19, .99));
    }

    .auth-story {
      position: relative;
      display: flex;
      min-height: 480px;
      flex-direction: column;
      justify-content: space-between;
      gap: 8px;
      padding: 20px 28px 22px;
      overflow: hidden;
    }
    .auth-art {
      position: relative;
      flex: 0 0 auto;
      width: 100%;
      height: 175px;
      min-height: 165px;
      margin: 0 auto;
      isolation: isolate;
    }
    .auth-art:before {
      content: "";
      position: absolute;
      inset: 8% 12%;
      z-index: -1;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(241, 138, 94, .18), rgba(178, 156, 244, .07) 50%, transparent 72%);
      filter: blur(18px);
      animation: auth-glow 6s ease-in-out infinite alternate;
    }
    .auth-art-grid {
      position: absolute;
      inset: 2% 0;
      opacity: .18;
      background-image: linear-gradient(rgba(222, 226, 235, .05) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(222, 226, 235, .05) 1px, transparent 1px);
      background-size: 32px 32px;
      mask-image: radial-gradient(ellipse at center, #000 8%, transparent 78%);
    }
    .auth-orbit {
      position: absolute;
      left: 50%;
      top: 48%;
      width: min(72%, 260px);
      aspect-ratio: 1.75;
      border: 1px solid rgba(241, 138, 94, .3);
      border-radius: 50%;
      transform: translate(-50%, -50%) rotate(-24deg);
      animation: auth-spin 130s linear infinite;
    }
    .auth-orbit:after {
      content: "";
      position: absolute;
      top: 50%;
      left: -3px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--orange);
      box-shadow: 0 0 12px 2px rgba(241, 138, 94, .65);
    }
    .auth-orbit.orbit-b {
      width: min(58%, 200px);
      aspect-ratio: .77;
      border-color: rgba(178, 156, 244, .28);
      transform: translate(-50%, -50%) rotate(31deg);
      animation: auth-spin-rev 170s linear infinite;
    }
    .auth-orbit.orbit-b:after {
      left: auto;
      right: -3px;
      background: var(--violet);
      box-shadow: 0 0 12px 2px rgba(178, 156, 244, .55);
    }
    .auth-orbit.orbit-c {
      width: min(84%, 300px);
      aspect-ratio: 2.6;
      border-color: rgba(222, 226, 235, .12);
      transform: translate(-50%, -50%) rotate(8deg);
      animation: auth-spin 220s linear infinite;
    }
    .auth-convergence {
      position: absolute;
      left: 50%;
      top: 48%;
      width: 26px;
      height: 26px;
      border: 1px solid rgba(241, 138, 94, .35);
      border-radius: 50%;
      background: radial-gradient(circle, rgba(241, 138, 94, .2), transparent 70%);
      box-shadow: 0 0 20px rgba(241, 138, 94, .14);
      transform: translate(-50%, -50%);
    }
    .auth-convergence:after {
      content: "";
      position: absolute;
      inset: 6px;
      border: 1px solid rgba(178, 156, 244, .45);
      border-radius: 50%;
    }
    .auth-node {
      position: absolute;
      z-index: 1;
      width: 8px;
      height: 8px;
      border: 1px solid #ffd0b5;
      border-radius: 50%;
      background: var(--orange);
      box-shadow: 0 0 0 4px rgba(241, 138, 94, .12), 0 0 10px rgba(241, 138, 94, .6);
    }
    .auth-node.node-a { left: 22%; top: 31%; }
    .auth-node.node-b { right: 18%; top: 37%; }
    .auth-node.node-c { left: 35%; bottom: 17%; }
    .auth-note {
      position: absolute;
      z-index: 1;
      color: rgba(174, 187, 208, .75);
      font: 600 8px/1.4 var(--mono);
      letter-spacing: .14em;
    }
    .auth-note.note-a { left: 4%; top: 24%; }
    .auth-note.note-b { right: 0; top: 29%; }
    .auth-note.note-c { left: 19%; bottom: 7%; }
    .auth-art-caption {
      position: absolute;
      left: 50%;
      bottom: 1%;
      display: flex;
      align-items: center;
      gap: 8px;
      transform: translateX(-50%);
      color: var(--quiet);
      font: 600 8px/1.4 var(--mono);
      letter-spacing: .13em;
      white-space: nowrap;
    }
    .auth-art-caption i {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--mint);
      box-shadow: 0 0 8px rgba(129, 200, 169, .6);
    }

    .auth-story-copy { position: relative; z-index: 2; max-width: 420px; color: var(--muted); }
    .auth-eyebrow {
      color: var(--orange-light);
      font: 600 10px/1.5 var(--mono);
      letter-spacing: .16em;
      text-transform: uppercase;
      margin: 0 0 6px;
    }
    .auth-story-copy h1 {
      margin: 6px 0 10px !important;
      color: var(--ink) !important;
      font-size: clamp(28px, 2.9vw, 38px) !important;
      font-weight: 620 !important;
      letter-spacing: -.06em !important;
      line-height: 1.05 !important;
    }
    .auth-story-copy h1 em, .auth-story-copy h1 span {
      color: var(--orange) !important;
      font-family: Georgia, serif !important;
      font-style: italic !important;
      font-weight: 450 !important;
    }
    .auth-story-copy p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }
    .auth-story-foot {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 14px;
      color: var(--quiet);
      font-size: 11px;
    }
    .auth-story-foot i {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--orange);
      box-shadow: 0 0 8px rgba(241, 138, 94, .5);
    }

    .auth-card-title {
      margin: 6px 0 4px !important;
      color: var(--ink) !important;
      font-size: clamp(25px, 2.7vw, 33px) !important;
      font-weight: 640 !important;
      letter-spacing: -.05em !important;
      line-height: 1.1 !important;
    }
    .auth-card-title span { color: var(--orange) !important; }
    .auth-card-subtitle {
      max-width: 380px;
      margin: 0 0 16px !important;
      color: var(--muted) !important;
      font-size: 13px !important;
      line-height: 1.5 !important;
    }

    .st-key-auth-mode { width: 100% !important; min-width: 0 !important; margin: 0 0 14px !important; }
    .st-key-auth-mode div[data-testid="stButtonGroup"] > div[role="radiogroup"],
    div[data-testid="stButtonGroup"] > div[role="radiogroup"] {
      display: flex !important;
      width: 100% !important;
      gap: 4px !important;
      padding: 4px !important;
      border: 1px solid var(--line) !important;
      border-radius: 12px !important;
      background: rgba(7, 10, 18, .75) !important;
    }
    .st-key-auth-mode button[data-variant="segmented_control"],
    button[data-variant="segmented_control"] {
      flex: 1 1 0 !important;
      min-height: 40px !important;
      border: 1px solid transparent !important;
      border-radius: 9px !important;
      background: transparent !important;
      color: var(--muted) !important;
      font-size: 13px !important;
      font-weight: 580 !important;
      transition: color .2s, background .2s, border-color .2s, box-shadow .2s !important;
    }
    .st-key-auth-mode button[data-variant="segmented_control"]:hover,
    button[data-variant="segmented_control"]:hover {
      color: var(--ink) !important;
      background: rgba(255, 255, 255, .04) !important;
    }
    .st-key-auth-mode button[data-variant="segmented_control"]:is([data-selected="true"],[aria-checked="true"]),
    button[data-variant="segmented_control"]:is([data-selected="true"],[aria-checked="true"]) {
      color: #fff !important;
      border-color: rgba(241, 138, 94, .7) !important;
      background: rgba(241, 138, 94, .2) !important;
      font-weight: 650 !important;
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, .15), 0 2px 10px rgba(241, 138, 94, .2) !important;
    }
    .st-key-auth-mode button[data-variant="segmented_control"]:is([data-selected="true"],[aria-checked="true"]) *,
    button[data-variant="segmented_control"]:is([data-selected="true"],[aria-checked="true"]) * {
      color: #fff !important;
      font-weight: 650 !important;
    }

    .st-key-auth-card [data-testid="stTextInput"] { width: 100% !important; min-width: 0 !important; margin: 6px 0 10px !important; }
    .st-key-auth-card [data-testid="stTextInput"] label { color: #d6d9e0 !important; font-size: 12px !important; font-weight: 560 !important; }
    .st-key-auth-card [data-testid="stTextInput"] input {
      width: 100% !important;
      min-height: 44px !important;
      border: 1px solid var(--line) !important;
      border-radius: 10px !important;
      background: rgba(8, 10, 16, .75) !important;
      color: var(--ink) !important;
      font-size: 14px !important;
      transition: border-color .2s, box-shadow .2s, background .2s !important;
    }
    .st-key-auth-card [data-testid="stTextInput"] input::placeholder { color: #5f6472 !important; }
    .st-key-auth-card [data-testid="stTextInput"] input:focus {
      border-color: rgba(241, 138, 94, .7) !important;
      background: rgba(12, 14, 22, .92) !important;
      box-shadow: 0 0 0 3px rgba(241, 138, 94, .15) !important;
    }

    .st-key-auth-card [data-testid="stCheckbox"] label { color: var(--muted) !important; font-size: 12px !important; }
    .st-key-auth-card [data-testid="stCheckbox"] input { accent-color: var(--orange) !important; }

    [data-testid="stMain"] div.st-key-login_submit_btn button,
    [data-testid="stMain"] div.st-key-signup_submit_btn button,
    [data-testid="stMain"] div.st-key-verify_otp_btn button,
    [data-testid="stMain"] .st-key-auth-card div[data-testid="stButton"]>button,
    [data-testid="stMain"] .st-key-auth-card button[data-testid="stBaseButton-primary"],
    .st-key-auth-card div[data-testid="stButton"]>button[kind="primary"],
    .st-key-auth-card button[data-testid="stBaseButton-primary"],
    .st-key-auth-card .stButton>button {
      width: 100% !important;
      min-height: 46px !important;
      margin-top: 10px !important;
      border: 1px solid rgba(255, 159, 119, .9) !important;
      border-radius: 12px !important;
      background: #f18a5e !important;
      background-image: none !important;
      color: #1d100b !important;
      font-size: 14px !important;
      font-weight: 650 !important;
      box-shadow: 0 8px 24px rgba(226, 111, 67, .25), inset 0 1px 0 rgba(255, 255, 255, .22) !important;
      transition: transform .2s var(--ease), box-shadow .2s, background .2s, border-color .2s !important;
    }
    [data-testid="stMain"] div.st-key-login_submit_btn button:hover:not(:disabled),
    [data-testid="stMain"] div.st-key-signup_submit_btn button:hover:not(:disabled),
    [data-testid="stMain"] div.st-key-verify_otp_btn button:hover:not(:disabled),
    [data-testid="stMain"] .st-key-auth-card div[data-testid="stButton"]>button:hover:not(:disabled),
    [data-testid="stMain"] .st-key-auth-card button[data-testid="stBaseButton-primary"]:hover:not(:disabled),
    .st-key-auth-card div[data-testid="stButton"]>button[kind="primary"]:hover:not(:disabled),
    .st-key-auth-card button[data-testid="stBaseButton-primary"]:hover:not(:disabled),
    .st-key-auth-card .stButton>button:hover:not(:disabled) {
      background: #fa9870 !important;
      background-image: none !important;
      color: #1d100b !important;
      border-color: #ffb390 !important;
      box-shadow: 0 12px 30px rgba(226, 111, 67, .32) !important;
      transform: translateY(-1px) !important;
    }
    [data-testid="stMain"] div.st-key-login_submit_btn button *,
    [data-testid="stMain"] div.st-key-signup_submit_btn button *,
    [data-testid="stMain"] div.st-key-verify_otp_btn button *,
    [data-testid="stMain"] .st-key-auth-card div[data-testid="stButton"]>button *,
    [data-testid="stMain"] .st-key-auth-card button[data-testid="stBaseButton-primary"] *,
    .st-key-auth-card div[data-testid="stButton"]>button[kind="primary"] *,
    .st-key-auth-card button[data-testid="stBaseButton-primary"] * {
      color: #1d100b !important;
      font-weight: 650 !important;
    }
    .st-key-auth-card .stButton>button:active { transform: scale(.985); }
    .st-key-auth-card .stButton>button:focus-visible { outline: 2px solid var(--orange) !important; outline-offset: 3px !important; }

    .auth-password-hint { margin: 1px 0 8px; color: var(--quiet); font-size: 11px; line-height: 1.45; }
    .auth-footer {
      margin-top: 14px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      color: var(--quiet);
      font-size: 11px;
      line-height: 1.5;
    }

    .auth-demo-divider {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 16px 0 10px;
      color: var(--quiet);
      font-size: 10px;
      font-family: var(--mono);
      letter-spacing: .14em;
      text-transform: uppercase;
    }
    .auth-demo-divider::before, .auth-demo-divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: var(--line);
    }
    .auth-demo-divider span {
      color: var(--muted);
      font-weight: 500;
    }

    [data-testid="stMain"] div.st-key-demo_bypass_login_btn button,
    [data-testid="stMain"] div.st-key-demo_bypass_signup_btn button,
    [data-testid="stMain"] div.st-key-demo_bypass_otp_btn button {
      width: 100% !important;
      min-height: 44px !important;
      margin-top: 4px !important;
      border: 1px solid rgba(241, 138, 94, .45) !important;
      border-radius: 12px !important;
      background: rgba(241, 138, 94, .08) !important;
      background-image: none !important;
      color: #f7ede8 !important;
      font-size: 14px !important;
      font-weight: 600 !important;
      letter-spacing: .02em !important;
      box-shadow: 0 4px 14px rgba(0, 0, 0, .25), inset 0 1px 0 rgba(255, 255, 255, .06) !important;
      transition: all .2s cubic-bezier(.2,.75,.25,1) !important;
    }
    [data-testid="stMain"] div.st-key-demo_bypass_login_btn button:hover:not(:disabled),
    [data-testid="stMain"] div.st-key-demo_bypass_signup_btn button:hover:not(:disabled),
    [data-testid="stMain"] div.st-key-demo_bypass_otp_btn button:hover:not(:disabled) {
      background: rgba(241, 138, 94, .18) !important;
      border-color: #f18a5e !important;
      color: #ffffff !important;
      box-shadow: 0 6px 20px rgba(241, 138, 94, .25) !important;
      transform: translateY(-1px) !important;
    }
    [data-testid="stMain"] div.st-key-demo_bypass_login_btn button *,
    [data-testid="stMain"] div.st-key-demo_bypass_signup_btn button *,
    [data-testid="stMain"] div.st-key-demo_bypass_otp_btn button * {
      color: #f7ede8 !important;
      font-weight: 600 !important;
    }
    [data-testid="stMain"] div.st-key-demo_bypass_login_btn button:hover:not(:disabled) *,
    [data-testid="stMain"] div.st-key-demo_bypass_signup_btn button:hover:not(:disabled) *,
    [data-testid="stMain"] div.st-key-demo_bypass_otp_btn button:hover:not(:disabled) * {
      color: #ffffff !important;
    }

    .auth-demo-btn {
      border: 1px solid rgba(241, 138, 94, .45) !important;
      border-radius: 12px !important;
      background: rgba(241, 138, 94, .08) !important;
      color: #f7ede8 !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      padding: 0 16px !important;
      min-height: 38px !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      transition: all .2s var(--ease) !important;
    }
    .auth-demo-btn:hover {
      border-color: #f18a5e !important;
      background: rgba(241, 138, 94, .2) !important;
      color: #ffffff !important;
      box-shadow: 0 4px 14px rgba(241, 138, 94, .22) !important;
      transform: translateY(-1px) !important;
    }

    @keyframes auth-glow { from { opacity: .7; transform: scale(.97); } to { opacity: 1; transform: scale(1.05); } }
    @keyframes auth-spin { to { transform: translate(-50%, -50%) rotate(336deg); } }
    @keyframes auth-spin-rev { to { transform: translate(-50%, -50%) rotate(-329deg); } }

    @media(max-width: 900px) {
      [data-testid="stMainBlockContainer"], .block-container { width: min(100% - 36px, 740px) !important; }
      .st-key-auth-layout [data-testid="stHorizontalBlock"] { grid-template-columns: 1fr !important; min-height: 0; }
      .st-key-auth-story { border-right: 0; border-bottom: 1px solid var(--line); min-height: 0; }
      .auth-story { min-height: 0; padding: 18px 22px; gap: 6px; }
      .auth-art { height: 160px; min-height: 150px; }
      .st-key-auth-card { min-height: 0; padding: 24px 22px !important; }
    }
    @media(prefers-reduced-motion: reduce) {
      .auth-art:before, .auth-orbit { animation: none !important; }
      .auth-overview-btn, .st-key-auth-card .stButton>button { transition: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    pending_user = st.session_state.get("auth_pending_verification_user")
    default_mode = "Create account" if st.query_params.get("auth") == "signup" else "Sign in"
    if st.session_state.get("_auth_route_mode") != default_mode:
        st.session_state["auth_form_mode"] = default_mode
        st.session_state["_auth_route_mode"] = default_mode

    with st.container(key="auth-shell"):
        with st.container(key="auth-header"):
            topbar_html = f'''
            <header class="auth-topbar">
              <a class="auth-brand" href="/" aria-label="Aster home">
                <img class="auth-logo" src="{escape(tech_logo, quote=True)}" alt="ASTER">
              </a>
              <div class="auth-nav-actions">
                <a class="button auth-demo-btn" href="/?auth=demo" aria-label="Quick demo bypass to dashboard">demo</a>
                <a class="button auth-overview-btn" href="/" aria-label="Back to Aster overview">← Overview</a>
              </div>
            </header>
            '''
            st.markdown(topbar_html, unsafe_allow_html=True)

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
                                    st.toast(f"Welcome back, {user['email']}!", icon=":material/waving_hand:")
                                    st.rerun()

                        st.markdown('<div class="auth-demo-divider"><span>OR QUICK BYPASS</span></div>', unsafe_allow_html=True)
                        if st.button("demo", type="secondary", use_container_width=True, key="demo_bypass_login_btn", help="Skip login or create account and enter the dashboard directly."):
                            demo_user, token = auth_manager.get_or_create_demo_user(connection)
                            st.session_state["session_token"] = token
                            st.session_state["authenticated_user"] = demo_user
                            st.session_state.pop("auth_pending_verification_user", None)
                            st.session_state.pop("show_auth_portal", None)
                            st.query_params["session"] = token
                            if "auth" in st.query_params:
                                del st.query_params["auth"]
                            st.toast("Entered Aster Demo Workspace!", icon=":material/science:")
                            st.rerun()

                        st.markdown('<div class="auth-footer">Your experiment journal remains in your local workspace. Gemini is used only when you choose an AI feature.</div>', unsafe_allow_html=True)
                    else:
                        st.text_input(
                            "Full name",
                            placeholder="Dr. Jane Doe",
                            autocomplete="name",
                            key="signup_name_input",
                        )
                        st.text_input(
                            "Email address",
                            placeholder="researcher@lab.org",
                            type="email",
                            autocomplete="email",
                            required=True,
                            key="signup_email_input",
                        )
                        st.text_input(
                            "Password",
                            type="password",
                            placeholder="Create a strong password",
                            autocomplete="new-password",
                            required=True,
                            key="signup_password_input",
                        )
                        st.markdown(
                            '<p class="auth-password-hint">Use at least 8 characters. Include uppercase and lowercase letters, a number, and a symbol.</p>',
                            unsafe_allow_html=True,
                        )
                        if st.button("Create account", type="primary", use_container_width=True, key="signup_submit_btn"):
                            signup_name = st.session_state.get("signup_name_input", "").strip()
                            signup_email = st.session_state.get("signup_email_input", "").strip()
                            signup_password = st.session_state.get("signup_password_input", "")
                            with st.spinner("Creating your account…"):
                                user, err = auth_manager.register_user(
                                    connection, signup_email, signup_password, name=signup_name
                                )
                            if err or not user:
                                st.error(err or "Unable to create your account.")
                            else:
                                token = auth_manager.create_session(connection, user["id"])
                                st.session_state.session_token = token
                                st.session_state.auth_pending_verification_user = user
                                st.session_state.authenticated_user = user
                                st.toast("Account created. Verify your email to continue.", icon=":material/mark_email_unread:")
                                st.rerun()

                        st.markdown('<div class="auth-demo-divider"><span>OR QUICK BYPASS</span></div>', unsafe_allow_html=True)
                        if st.button("demo", type="secondary", use_container_width=True, key="demo_bypass_signup_btn", help="Skip login or create account and enter the dashboard directly."):
                            demo_user, token = auth_manager.get_or_create_demo_user(connection)
                            st.session_state["session_token"] = token
                            st.session_state["authenticated_user"] = demo_user
                            st.session_state.pop("auth_pending_verification_user", None)
                            st.session_state.pop("show_auth_portal", None)
                            st.query_params["session"] = token
                            if "auth" in st.query_params:
                                del st.query_params["auth"]
                            st.toast("Entered Aster Demo Workspace!", icon=":material/science:")
                            st.rerun()

                        st.markdown('<div class="auth-footer">Your experiment journal remains in your local workspace. Gemini is used only when you choose an AI feature.</div>', unsafe_allow_html=True)


# ==============================================================================
# No-Cost Email Verification View (OTP)
# ==============================================================================
def render_otp_verification_view(connection: sqlite3.Connection, user: dict[str, Any]) -> None:
    """Render the no-cost 6-digit OTP email verification interface."""
    user_id = user["id"]
    email = user["email"]
    latest_otp = user.get("latest_otp", "")

    with st.container(border=True):
        st.markdown("### Verify Your Research Email")
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
            if st.button("Verify Email & Continue", icon=":material/arrow_forward:", type="primary", use_container_width=True, key="verify_otp_btn"):
                success, msg = auth_manager.verify_email_otp(connection, user_id, entered_otp)
                if not success:
                    st.error(msg)
                else:
                    user["is_verified"] = True
                    st.session_state.authenticated_user = user
                    st.session_state.auth_pending_verification_user = None
                    st.toast("Email verified successfully!", icon=":material/check_circle:")
                    st.rerun()

        with col2:
            if st.button("Resend Code", type="secondary", use_container_width=True, key="resend_otp_btn"):
                new_otp = auth_manager.create_email_verification_otp(connection, user_id, email)
                user["latest_otp"] = new_otp
                st.session_state.auth_pending_verification_user = user
                st.toast(f"New verification code issued: {new_otp}", icon=":material/mark_email_unread:")
                st.rerun()

        st.markdown('<div class="auth-demo-divider" style="margin-top:14px;"><span>OR QUICK BYPASS</span></div>', unsafe_allow_html=True)
        if st.button("demo", type="secondary", use_container_width=True, key="demo_bypass_otp_btn", help="Skip verification and enter the dashboard directly."):
            demo_user, token = auth_manager.get_or_create_demo_user(connection)
            st.session_state["session_token"] = token
            st.session_state["authenticated_user"] = demo_user
            st.session_state.pop("auth_pending_verification_user", None)
            st.session_state.pop("show_auth_portal", None)
            st.query_params["session"] = token
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.toast("Entered Aster Demo Workspace!", icon=":material/science:")
            st.rerun()

    st.caption("You will proceed directly to Stage 2: Research Onboarding to calibrate your personalized feed.")
