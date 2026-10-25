"""Public Aster landing page restored from the supplied desktop reference."""

from __future__ import annotations

import base64
from html import escape
from math import cos, sin, pi
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent


def _wordmark_data_uri() -> str:
    for asset in (ROOT / "static" / "aster-wordmark.png", ROOT / "public" / "aster-logo.png"):
        if asset.is_file():
            return "data:image/png;base64," + base64.b64encode(asset.read_bytes()).decode("ascii")
    return ""


def _sculpture_svg() -> str:
    """Build the landing sculpture as self-contained animated SVG geometry."""
    cx, cy, rx, ry = 320.0, 258.0, 157.0, 139.0
    step = 2 * pi / 36
    start = -7 * pi / 9  # index 8 opens at the upper-right, as in the reference
    pieces: list[str] = []
    for index in range(36):
        if index == 8:
            continue
        angle = start + index * step
        px, py = cx + cos(angle) * rx, cy + sin(angle) * ry
        tx, ty = -sin(angle), cos(angle)
        ux, uy = cos(angle), sin(angle)
        half_t, half_r = 7.0, 10.0
        pts = [
            (px - tx * half_t - ux * half_r, py - ty * half_t - uy * half_r),
            (px + tx * half_t - ux * half_r, py + ty * half_t - uy * half_r),
            (px + tx * half_t + ux * half_r, py + ty * half_t + uy * half_r),
            (px - tx * half_t + ux * half_r, py - ty * half_t + uy * half_r),
        ]
        front = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        extruded = [(x + 4.0, y + 7.0) for x, y in pts]
        side = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pts[2], pts[3], extruded[3], extruded[2]))
        top = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pts[0], pts[1], extruded[1], extruded[0]))
        pieces.append(
            f'<g class="aster-segment" style="--segment:{index}">'
            f'<polygon points="{side}" fill="#343942" stroke="#9d725a" stroke-opacity=".48" stroke-width=".8"/>'
            f'<polygon points="{front}" fill="url(#aster-copper)" stroke="#f3b08b" stroke-opacity=".52" stroke-width=".9"/>'
            f'<polygon points="{top}" fill="url(#aster-steel)" stroke="#e9e4dc" stroke-opacity=".7" stroke-width=".65"/>'
            f'<path d="M {pts[0][0]:.1f} {pts[0][1]:.1f} L {pts[1][0]:.1f} {pts[1][1]:.1f}" stroke="#fff1e5" stroke-opacity=".68" stroke-width=".8"/>'
            '</g>'
        )
    return '''<svg class="aster-sculpture-svg" viewBox="0 0 640 520" role="img" aria-label="A segmented copper sculpture with one open slot. A matching piece orbits, docks into the gap, and sends a light pulse through the ring.">
      <defs>
        <linearGradient id="aster-copper" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#f1a173"/><stop offset=".32" stop-color="#bd6947"/><stop offset=".68" stop-color="#75442f"/><stop offset="1" stop-color="#d58a5f"/></linearGradient>
        <linearGradient id="aster-steel" x1="0" y1="0" x2="1" y2=".4"><stop stop-color="#e2ded6"/><stop offset=".42" stop-color="#89909a"/><stop offset="1" stop-color="#353b45"/></linearGradient>
        <radialGradient id="aster-halo"><stop stop-color="#f18a5e" stop-opacity=".13"/><stop offset="1" stop-color="#10151e" stop-opacity="0"/></radialGradient>
        <filter id="aster-soft-glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="6"/></filter>
      </defs>
      <ellipse cx="320" cy="258" rx="250" ry="220" fill="url(#aster-halo)"/>
      <g class="aster-ring-turn">''' + "".join(pieces) + '''
        <circle cx="398.8" cy="138.5" r="10" fill="#15171c" stroke="#e3875c" stroke-opacity=".58" stroke-width="1.2"/>
        <circle class="aster-socket-glow" cx="398.8" cy="138.5" r="13" fill="none" stroke="#f18a5e" stroke-width="2"/>
      </g>
      <path id="aster-fragment-route" d="M 505 74 C 545 165 525 278 451 337 C 374 399 263 399 186 348 C 112 300 112 216 156 153 C 207 80 299 70 398.8 138.5 L 421 116 L 505 74" fill="none"/>
      <g class="aster-arriving-piece" aria-hidden="true">
        <polygon points="-14,-9 10,-9 17,-4 17,8 -10,8 -16,3" fill="url(#aster-copper)" stroke="#f4c09d" stroke-width="1"/>
        <polygon points="-14,-9 10,-9 13,-5 -12,-5" fill="url(#aster-steel)"/>
        <polygon points="10,-9 17,-4 17,8 11,4" fill="#313741"/>
        <path d="M-13 -8 L9 -8" stroke="#fff0e4" stroke-opacity=".8" stroke-width="1"/>
        <circle class="aster-piece-glow" cx="0" cy="0" r="20" fill="#f18a5e" fill-opacity=".6" filter="url(#aster-soft-glow)"/>
      </g>
      <g class="aster-atmosphere" fill="#d89770"><circle cx="145" cy="111" r="1.8"/><circle cx="501" cy="402" r="1.8"/><circle cx="177" cy="389" r="1.2"/><circle cx="461" cy="90" r="1.1"/></g>
    </svg>'''


def render_landing_page(connection=None) -> None:
    """Render the public landing page while preserving existing auth routes."""
    logo = _wordmark_data_uri()
    brand = (
        f'<img class="brand-wordmark" src="{escape(logo, quote=True)}" alt="ASTER">'
        if logo else '<span class="brand-fallback">ASTER</span>'
    )
    st.markdown(
        """<style>
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stFooter"], #MainMenu {display:none!important}
        [data-testid="stAppViewContainer"], .stApp {background:#080a10!important;border-top:0!important;box-shadow:none!important}
        [data-testid="stMainBlockContainer"], .block-container {max-width:none!important;width:100%!important;padding:0!important;margin:0!important}
        [data-testid="stMain"] {padding-top:0!important}
        div[data-testid="stElementContainer"]:has(.topbar),.stElementContainer:has(.topbar){position:relative!important;top:-56px!important;margin:0!important;padding:0!important;background:transparent!important}
        @media(max-width:740px){div[data-testid="stElementContainer"]:has(.topbar),.stElementContainer:has(.topbar){top:-28px!important}}
        </style>""",
        unsafe_allow_html=True,
    )

    html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Capture AI experiments in your own words, connect related runs, and carry useful lessons into your next research question with Aster.">
<meta name="theme-color" content="#080a10"><title>Aster — Keep the thread behind every result</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&family=DM+Mono:wght@400;500&display=swap');
:root{color-scheme:dark;--bg:#080a10;--ink:#f3f1ed;--muted:#aaa9a8;--quiet:#85878c;--line:rgba(222,226,235,.14);--line2:rgba(222,226,235,.22);--orange:#f18a5e;--orange-light:#f3a07d;--violet:#b29cf4;--cyan:#89d2e5;--mint:#81c8a9;--mono:var(--aster-font-mono,'SFMono-Regular',Consolas,monospace);--serif:Georgia,'Times New Roman',serif;--ease:cubic-bezier(.2,.75,.25,1)}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;min-width:320px;overflow-x:hidden;background:radial-gradient(ellipse at 77% 12%,rgba(45,64,120,.17),transparent 43rem),radial-gradient(ellipse at 14% 63%,rgba(28,88,114,.1),transparent 40rem),linear-gradient(140deg,#090b12,#080a10 64%);color:var(--ink);font-family:var(--aster-font-ui,'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif);-webkit-font-smoothing:antialiased}a{color:inherit;text-decoration:none}button{font:inherit}.shell{width:min(1784px,calc(100% - 96px));margin-inline:auto}
.topbar{position:sticky;z-index:30;top:0;display:flex;align-items:center;justify-content:space-between;min-height:139px;border-bottom:1px solid transparent;transition:background .2s,border-color .2s}.topbar.scrolled{border-color:var(--line);background:rgba(8,10,16,.86);backdrop-filter:blur(22px) saturate(145%);-webkit-backdrop-filter:blur(22px) saturate(145%)}.brand{display:inline-flex;align-items:center;min-width:0}.brand-wordmark{display:block;width:360px;max-width:min(360px,46vw);height:auto}.brand-fallback{color:#f4f6fc;font-size:25px;font-weight:600;letter-spacing:.26em}.desktop-nav{display:flex;align-items:center;gap:52px;margin-left:auto;margin-right:47px;color:#a3a4aa;font-size:16px}.desktop-nav a{transition:color .18s}.desktop-nav a:hover{color:#f1f1f4}.nav-actions{display:flex;align-items:center;gap:13px}.button{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:60px;padding:0 26px;border:1px solid rgba(214,220,235,.21);border-radius:16px;background:rgba(255,255,255,.025);color:#e7e7e9;font-size:16px;font-weight:600;white-space:nowrap;transition:transform .2s var(--ease),background .2s,border-color .2s,box-shadow .2s}.button:hover{transform:translateY(-2px);border-color:rgba(209,220,250,.42);background:rgba(255,255,255,.065)}.button:active{transform:scale(.98)}.button-primary{border-color:rgba(255,159,119,.9);background:var(--orange);color:#1d100b;box-shadow:0 10px 28px rgba(226,111,67,.13),inset 0 1px 0 rgba(255,255,255,.22)}.button-primary:hover{border-color:#ffb390;background:#fa9870;color:#1d100b;box-shadow:0 13px 34px rgba(226,111,67,.2)}.menu-toggle,.mobile-menu{display:none}
.hero{display:grid;grid-template-columns:minmax(0,1.13fr) minmax(0,.87fr);align-items:center;gap:clamp(48px,6vw,116px);min-height:900px;padding:88px 0 92px}.hero-copy{max-width:900px;animation:rise .65s var(--ease) both}.eyebrow,.section-kicker,.visual-caption,.workspace-top,.record-kicker,.graph-note,.record-bottom,.flow-index{font-family:var(--mono);text-transform:uppercase}.eyebrow{display:flex;align-items:center;gap:14px;margin:0 0 45px;color:#bebdbb;font-size:13px;font-weight:600;letter-spacing:.16em}.eyebrow:before{content:"";width:30px;height:1px;background:var(--orange)}h1{max-width:890px;margin:0;color:#f2f0eb;font-size:clamp(58px,5.3vw,86px);font-weight:620;letter-spacing:-.078em;line-height:1.04}h1 em{color:#d4cdc5;font-family:var(--serif);font-weight:450;letter-spacing:-.06em}.hero-lede{max-width:785px;margin:37px 0 0;color:#b4b3b2;font-size:clamp(18px,1.42vw,23px);line-height:1.82}.hero-actions{display:flex;flex-wrap:wrap;gap:16px;margin-top:39px}.hero-actions .button{min-height:69px;padding-inline:29px}.hero-meta{display:flex;flex-wrap:wrap;align-items:center;gap:16px;margin-top:31px;color:#85878d;font-size:14px}.hero-meta b{color:#c3c4c7;font-weight:520}.hero-meta i{width:4px;height:4px;border-radius:50%;background:#60636b}
.hero-visual{position:relative;min-width:0;padding:0 0 0 32px;animation:rise .78s .08s var(--ease) both}.visual-rule{position:absolute;inset:0 auto 0 0;width:1px;background:linear-gradient(180deg,transparent,var(--line2) 10%,var(--line2) 94%,transparent)}.visual-caption{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 17px;color:#85868c;font-size:11px;letter-spacing:.13em}.visual-caption span:last-child{color:var(--orange-light)}.workspace{overflow:hidden;border:1px solid rgba(218,221,230,.27);border-radius:27px;background:linear-gradient(145deg,rgba(33,34,39,.98),rgba(22,23,27,.98));box-shadow:0 30px 90px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.075)}.workspace-top{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:67px;padding:0 24px;border-bottom:1px solid var(--line);color:#b5b4b2;font-size:12px;letter-spacing:.1em}.workspace-top b{color:#e1ded9;font-weight:500}.workspace-main{display:grid;grid-template-columns:minmax(0,1.27fr) minmax(260px,.88fr);min-height:405px}.graph-pane{position:relative;display:grid;min-width:0;place-items:center;overflow:hidden;border-right:1px solid var(--line);background:radial-gradient(ellipse at 50% 49%,rgba(100,104,145,.09),transparent 59%)}.graph-pane:before{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.02) 1px,transparent 1px);background-size:34px 34px;content:"";mask-image:radial-gradient(ellipse at center,#000,transparent 85%)}.graph-map{position:relative;width:min(100%,480px);height:360px;isolation:isolate}.graph-orbits{position:absolute;z-index:0;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}.graph-orbits ellipse{fill:none;stroke:rgba(151,157,174,.15);stroke-width:.35}.graph-orbits .orbit-dashed{stroke:rgba(157,133,217,.25);stroke-dasharray:1 1}.graph-edge{position:absolute;z-index:1;height:1px;transform-origin:left center;background:linear-gradient(90deg,rgba(207,211,221,.32),rgba(207,211,221,.65))}.graph-edge.association{height:0;border-top:1px dashed rgba(177,155,240,.76);background:none}.edge-a{top:35%;left:18%;width:33%;transform:rotate(17deg)}.edge-b{top:45%;left:51%;width:33%;transform:rotate(-17deg)}.edge-c{top:56%;left:51%;width:24%;transform:rotate(130deg)}.edge-d{top:56%;left:51%;width:24%;transform:rotate(50deg)}.graph-flow{position:absolute;z-index:2;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}.graph-flow path{fill:none;stroke-width:.55;stroke-linecap:round;stroke-dasharray:12 88;stroke-dashoffset:100;opacity:0;filter:drop-shadow(0 0 2px currentColor)}.graph-flow .solid-flow{color:#ef936d;stroke:#ef936d}.graph-flow .concept-flow{color:#b5a0f4;stroke:#b5a0f4;stroke-dasharray:7 93}.graph-map[data-phase="baseline"] .flow-baseline,.graph-map[data-phase="followup"] .flow-followup,.graph-map[data-phase="shared"] .flow-shared,.graph-map[data-phase="lesson"] .flow-lesson{animation:trace 1.15s var(--ease) both}.graph-item{position:absolute;z-index:3;display:grid;justify-items:center;gap:8px;min-width:78px;transform:translate(-50%,-50%);transition:opacity .35s,filter .35s}.graph-dot{width:17px;height:17px;border:1.5px solid #bdc6d5;border-radius:50%;background:#252830;box-shadow:0 0 0 6px rgba(190,203,220,.045);transition:box-shadow .5s,border-color .5s,transform .5s var(--ease)}.graph-item.current .graph-dot{width:22px;height:22px;border:3px solid var(--orange);background:#4b3027;box-shadow:0 0 0 8px rgba(239,128,82,.09)}.graph-name{color:#d0d0d1;font-size:12px;white-space:nowrap;text-shadow:0 1px 5px #15171b}.graph-note{color:#888a91;font-size:9px;letter-spacing:.06em;white-space:nowrap}.graph-item.baseline{top:35%;left:18%}.graph-item.current{top:50%;left:51%}.graph-item.followup{top:35%;left:84%}.graph-item.shared{top:81%;left:34%}.graph-item.lesson{top:81%;left:68%}.graph-map[data-phase="baseline"] .baseline .graph-dot,.graph-map[data-phase="followup"] .followup .graph-dot{border-color:#b5c8e5;background:#354052;box-shadow:0 0 0 8px rgba(114,163,236,.11),0 0 18px rgba(114,163,236,.26);transform:scale(1.08)}.graph-map[data-phase="current"] .current .graph-dot{box-shadow:0 0 0 9px rgba(239,128,82,.15),0 0 24px rgba(239,128,82,.3);transform:scale(1.08)}.graph-map[data-phase="shared"] .shared .graph-dot,.graph-map[data-phase="lesson"] .lesson .graph-dot{box-shadow:0 0 0 8px rgba(169,154,241,.12),0 0 18px rgba(169,154,241,.27);transform:scale(1.07)}.record-pane{display:flex;flex-direction:column;justify-content:space-between;gap:17px;min-width:0;padding:26px 21px 22px}.record-kicker{color:var(--orange-light);font-size:11px;font-weight:650;letter-spacing:.12em}.record-title{margin:12px 0 0;color:#e9e7e2;font-size:clamp(20px,1.7vw,27px);font-weight:620;letter-spacing:-.04em;line-height:1.22}.record-meta{margin-top:9px;color:#8f9198;font-size:13px;line-height:1.5}.record-list{display:grid;gap:18px;margin:0;padding:0;list-style:none}.record-list li{display:grid;grid-template-columns:minmax(78px,.62fr) minmax(0,1fr);align-items:start;gap:12px;color:#a8a9ad;font-size:13px;line-height:1.45}.record-list li span{min-width:0;overflow-wrap:normal;word-break:normal}.record-list b{min-width:0;color:#d7d5d0;font-size:13px;font-weight:560;text-align:right;overflow-wrap:anywhere}.record-list .signal{color:#b8e0d7}.record-bottom{padding-top:18px;border-top:1px solid var(--line);color:#92949a;font-size:10px;letter-spacing:.06em}.workspace-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:54px;padding:0 20px;border-top:1px solid var(--line);color:#8c8e94;font-size:12px}.workspace-foot span{display:inline-flex;align-items:center;gap:10px}.workspace-foot i{width:9px;height:9px;border-radius:50%;background:var(--mint)}@keyframes trace{0%{opacity:0;stroke-dashoffset:100}18%{opacity:.9}82%{opacity:.72}100%{opacity:0;stroke-dashoffset:-12}}@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.problem{display:grid;grid-template-columns:minmax(180px,.55fr) minmax(0,1.45fr);gap:44px;padding:42px 0 60px;border-block:1px solid var(--line)}.problem-label{color:#8f9297;font:11px var(--mono);letter-spacing:.15em;text-transform:uppercase}.problem p{max-width:1250px;margin:0;color:#c0bfbd;font-size:clamp(20px,1.55vw,29px);line-height:1.72}.problem em{color:#e8e3dc;font-family:var(--serif)}.section{padding:98px 0}.section-head{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,.62fr);align-items:end;gap:50px;margin-bottom:36px}.section-kicker{color:var(--orange-light);font-size:11px;letter-spacing:.15em}.section h2{max-width:850px;margin:13px 0 0;color:#f0eee9;font-size:clamp(38px,4.3vw,68px);font-weight:580;letter-spacing:-.065em;line-height:1.04}.section h2 em{color:#cec6bc;font-family:var(--serif);font-weight:450}.section-intro{max-width:500px;margin:0;color:#a4a5a5;font-size:16px;line-height:1.75}.flow-rail{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid var(--line)}.flow-step{min-height:175px;padding:24px 22px 24px 0}.flow-step+.flow-step{padding-left:22px;border-left:1px solid var(--line)}.flow-index{color:var(--orange-light);font-size:10px;letter-spacing:.1em}.flow-step h3{margin:23px 0 9px;color:#e9e7e2;font-size:19px;font-weight:600;letter-spacing:-.025em}.flow-step p{max-width:320px;margin:0;color:#999b9d;font-size:14px;line-height:1.7}.data-row{display:grid;grid-template-columns:minmax(220px,.65fr) minmax(0,1.35fr);gap:48px;padding:34px 0 60px;border-top:1px solid var(--line)}.data-row h2{max-width:520px;margin:0;font-size:clamp(34px,3.3vw,50px);font-weight:570;letter-spacing:-.06em;line-height:1.05}.data-copy{max-width:850px;color:#9ea0a2;font-size:14px;line-height:1.8}.data-copy p{margin:0 0 12px}.data-copy strong{color:#e2dfd9;font-weight:570}.final-cta{display:flex;align-items:center;justify-content:space-between;gap:28px;padding:28px 0 36px;border-block:1px solid var(--line)}.final-cta h2{max-width:870px;margin:0;color:#eeeae5;font-size:clamp(34px,4vw,58px);font-weight:570;letter-spacing:-.065em;line-height:1.06}.footer{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:25px 0 34px;color:#83868e;font-size:12px}.footer-nav{display:flex;flex-wrap:wrap;gap:24px}.footer a:hover{color:#e7e7e8}.reveal{opacity:1;transform:none;transition:opacity .55s var(--ease),transform .55s var(--ease)}.motion-ready .reveal:not(.visible){opacity:0;transform:translateY(12px)}.motion-ready .reveal.visible{opacity:1;transform:none}
@media(max-width:1250px){.shell{width:min(100% - 64px,1200px)}.topbar{min-height:105px}.desktop-nav{gap:24px;margin-right:24px}.hero{min-height:760px;grid-template-columns:minmax(0,1fr) minmax(0,.94fr);gap:48px;padding:68px 0}.hero-visual{padding-left:22px}.workspace-main{grid-template-columns:minmax(0,1.18fr) minmax(225px,.88fr)}.workspace-top{padding-inline:17px;font-size:10px}.record-pane{padding:21px 16px}.record-list li{grid-template-columns:minmax(70px,.65fr) minmax(0,1fr);gap:8px}}
@media(max-width:940px){.shell{width:calc(100% - 52px)}.topbar{min-height:88px}.desktop-nav{display:none}.nav-actions{margin-left:auto}.menu-toggle{display:grid;place-items:center;width:48px;height:48px;margin-left:12px;border:1px solid var(--line2);border-radius:14px;background:rgba(255,255,255,.035);color:#e6e8ed;cursor:pointer}.menu-toggle span,.menu-toggle span:before,.menu-toggle span:after{display:block;width:18px;height:1.5px;border-radius:3px;background:currentColor;transition:transform .2s,opacity .2s}.menu-toggle span{position:relative}.menu-toggle span:before,.menu-toggle span:after{position:absolute;left:0;content:""}.menu-toggle span:before{top:-6px}.menu-toggle span:after{top:6px}.menu-toggle[aria-expanded="true"] span{background:transparent}.menu-toggle[aria-expanded="true"] span:before{top:0;transform:rotate(45deg)}.menu-toggle[aria-expanded="true"] span:after{top:0;transform:rotate(-45deg)}.mobile-menu{position:absolute;top:calc(100% + 8px);right:0;display:grid;min-width:min(320px,calc(100vw - 48px));gap:4px;padding:10px;border:1px solid var(--line2);border-radius:16px;background:rgba(18,21,29,.96);backdrop-filter:blur(22px);box-shadow:0 22px 52px rgba(0,0,0,.35);opacity:0;pointer-events:none;transform:translateY(-6px);transition:opacity .18s,transform .18s}.mobile-menu.open{opacity:1;pointer-events:auto;transform:none}.mobile-menu a{display:flex;align-items:center;min-height:45px;padding:0 13px;border-radius:9px;color:#cfd1d6;font-size:13px}.mobile-menu a:hover{background:rgba(255,255,255,.06)}.mobile-menu .mobile-cta{margin-top:3px;background:var(--orange);color:#1b100b;font-weight:650}.hero{grid-template-columns:1fr;gap:42px;min-height:0;padding:75px 0 78px}.hero-copy{max-width:760px}.hero h1{max-width:850px;font-size:clamp(54px,8vw,82px)}.hero-lede{max-width:760px;font-size:clamp(17px,2.15vw,21px)}.hero-visual{width:min(100%,840px);margin-inline:auto;padding-left:24px}.workspace-main{grid-template-columns:minmax(0,1.2fr) minmax(240px,.8fr);min-height:390px}.graph-map{height:330px}.record-pane{padding:22px 20px}.record-list li{grid-template-columns:minmax(80px,.62fr) minmax(0,1fr)}.problem{grid-template-columns:1fr;gap:15px}.section-head{grid-template-columns:1fr;gap:16px}}
@media(max-width:740px){.workspace-main{grid-template-columns:1fr;min-height:0}.graph-pane{min-height:330px;border-right:0;border-bottom:1px solid var(--line)}.graph-map{height:300px}.record-pane{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);align-items:start;gap:17px 20px;padding:20px}.record-pane>:first-child{grid-row:span 2}.record-list{gap:14px}.record-list li{grid-template-columns:minmax(78px,.72fr) minmax(0,1fr)}.record-list li span{white-space:nowrap}.record-bottom{grid-column:1/-1}.problem{padding:30px 0 42px}.flow-rail{grid-template-columns:repeat(2,minmax(0,1fr))}.flow-step{min-height:155px;padding:20px 14px 18px 0}.flow-step+.flow-step{padding-left:16px}.flow-step:nth-child(3){padding-left:0;border-left:0;border-top:1px solid var(--line)}.flow-step:nth-child(4){border-top:1px solid var(--line)}.data-row{grid-template-columns:1fr;gap:16px}.workspace-top{min-height:57px}.record-title{font-size:22px}}
@media(max-width:520px){.shell{width:calc(100% - 34px)}.topbar{min-height:74px}.brand-wordmark{width:min(240px,60vw)}.nav-actions .button{min-height:42px;padding-inline:12px;border-radius:12px;font-size:11px}.nav-actions .button:not(.button-primary){display:none}.menu-toggle{width:44px;height:44px}.hero{gap:32px;padding:52px 0 48px}.eyebrow{margin-bottom:28px;font-size:10px;letter-spacing:.13em}.hero h1{font-size:clamp(43px,11vw,58px);line-height:1.04}.hero-lede{margin-top:23px;font-size:15px;line-height:1.72}.hero-actions{gap:9px;margin-top:27px}.hero-actions .button{min-height:52px;padding-inline:13px;font-size:11px}.hero-meta{gap:8px;margin-top:22px;font-size:9px}.hero-visual{padding-left:0}.visual-rule{display:none}.visual-caption{font-size:8px;letter-spacing:.09em}.workspace{border-radius:18px}.workspace-top{min-height:47px;padding-inline:11px;font-size:7px;letter-spacing:.055em}.workspace-main{grid-template-columns:1fr}.graph-pane{min-height:260px}.graph-map{height:250px}.graph-item{min-width:58px;gap:6px}.graph-name{font-size:9px}.graph-note{font-size:7px}.graph-dot{width:13px;height:13px}.graph-item.current .graph-dot{width:18px;height:18px}.record-pane{grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:13px;padding:15px 13px}.record-kicker{font-size:8px}.record-title{margin-top:7px;font-size:17px}.record-meta{font-size:9px}.record-list{gap:10px}.record-list li{grid-template-columns:minmax(66px,.7fr) minmax(0,1fr);gap:5px;font-size:9px}.record-list b{font-size:9px}.record-bottom{padding-top:11px;font-size:7px}.workspace-foot{min-height:39px;padding-inline:11px;font-size:8px}.problem{gap:10px}.problem-label{font-size:9px}.problem p{font-size:17px}.section{padding:62px 0}.section h2{font-size:37px}.section-intro{font-size:13px}.flow-step{min-height:140px;padding:16px 9px 15px 0}.flow-step+.flow-step{padding-left:12px}.flow-index{font-size:8px}.flow-step h3{margin-top:15px;font-size:14px}.flow-step p{font-size:10px}.data-row{padding:27px 0 42px}.data-row h2{font-size:34px}.data-copy{font-size:12px}.final-cta{align-items:flex-start;flex-direction:column}.final-cta h2{font-size:35px}.final-cta .button{width:100%}.footer{align-items:flex-start;flex-direction:column;gap:13px}.footer-nav{gap:14px;font-size:10px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}.reveal{opacity:1;transform:none}}
</style>
</head>
<body>
<header class="topbar shell" id="top">
  <a class="brand" href="#top" aria-label="Aster home">__BRAND__</a>
  <nav class="desktop-nav" aria-label="Main navigation"><a href="#product">Product</a><a href="#workflow">How it works</a><a href="#data">Data handling</a></nav>
  <div class="nav-actions"><a class="button" href="/?auth=login">Sign in</a><a class="button button-primary" href="/?auth=signup">Create account <span aria-hidden="true">↗</span></a></div>
  <button class="menu-toggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="mobile-menu"><span></span></button>
  <nav class="mobile-menu" id="mobile-menu" aria-label="Mobile navigation" inert><a href="#product">Product</a><a href="#workflow">How it works</a><a href="#data">Data handling</a><a href="/?auth=login">Sign in</a><a class="mobile-cta" href="/?auth=signup">Create account ↗</a></nav>
</header>
<main class="shell">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-copy"><p class="eyebrow">A workspace for applied AI research</p><h1 id="hero-title">Keep the thread<br>behind every <em>result.</em></h1><p class="hero-lede">Capture an experiment in your own words. Keep its hypothesis, setup, metrics, and lesson together—then connect the run to the next question.</p><div class="hero-actions"><a class="button button-primary" href="/?auth=signup">Create your workspace <span aria-hidden="true">↗</span></a><a class="button" href="#workflow">See how it works <span aria-hidden="true">↓</span></a></div><div class="hero-meta"><span><b>Voice or notes</b></span><i></i><span>Local experiment journal</span><i></i><span>Gemini when you choose</span></div></div>
    <figure class="hero-visual sculpture-visual" aria-label="The Missing Piece Living Sculpture: an open orange metal ribbon and a fragment that completes its gap.">
      <div class="sculpture-stage" data-sculpture-stage>
        <div class="sculpture-fallback">__SCULPTURE_ART__</div>
        <div class="sculpture-canvas-host" aria-hidden="true"></div>
      </div>
    </figure>
  </section>
  <section class="problem reveal" aria-label="The problem"><div class="problem-label">The problem</div><p>Experiment notes spread across notebooks, terminals, and chat. Later, the <em>reason behind a result</em> is hard to recover—and the next run starts without its context.</p></section>
  <section class="section reveal" id="workflow" aria-labelledby="workflow-heading"><div class="section-head"><div><div class="section-kicker">A connected research loop</div><h2 id="workflow-heading">Keep the conditions<br>with the <em>conclusion.</em></h2></div><p class="section-intro">Aster helps you move from a rough experiment note to a reviewable record, a connected follow-up, and a useful next question.</p></div><div class="flow-rail"><article class="flow-step"><div class="flow-index">01 / CAPTURE</div><h3>Start in your own words</h3><p>Dictate with Wispr Flow or paste notes, logs, and research context.</p></article><article class="flow-step"><div class="flow-index">02 / STRUCTURE</div><h3>Make the run legible</h3><p>Review a hypothesis, setup, results, metrics, insights, and next steps.</p></article><article class="flow-step"><div class="flow-index">03 / CONNECT</div><h3>Link related experiments</h3><p>Keep explicit follow-ups distinct from shared concepts and methods.</p></article><article class="flow-step"><div class="flow-index">04 / REFLECT</div><h3>Carry lessons forward</h3><p>Compare runs and keep the useful insight near the next test.</p></article></div></section>
  <section class="data-row reveal" id="product" aria-labelledby="product-heading"><div><div class="section-kicker">Product &amp; data</div><h2 id="product-heading">A research journal with its context attached.</h2></div><div class="data-copy"><p>Aster brings experiment notes, structured fields, metrics, memory, comparisons, and research lineage into one workspace.</p><p><strong>Local setup:</strong> experiment records are stored in SQLite on this machine. When you choose an AI feature, the relevant content is sent to Google’s Gemini API for that action. The graph preview above is illustrative, not live experiment data.</p></div></section>
  <section class="data-row reveal" id="data" aria-labelledby="data-heading"><div><div class="section-kicker">Data handling</div><h2 id="data-heading">Know what leaves your workspace.</h2></div><div class="data-copy"><p>Structuring, summaries, comparisons, and other Gemini actions use the API key configured in Settings. Content is sent to Google only when you invoke one of those AI features. The app does not display the full saved key.</p></div></section>
  <section class="final-cta reveal" aria-label="Create a workspace"><h2>Keep the work. Carry the lesson forward.</h2><a class="button button-primary" href="/?auth=signup">Create your workspace ↗</a></section>
  <footer class="footer"><span>Aster · AI experiment workspace</span><nav class="footer-nav" aria-label="Footer links"><a href="#workflow">How it works</a><a href="#product">Product</a><a href="#data">Data handling</a><a href="/?auth=login">Sign in</a></nav></footer>
</main>
<script>
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const voiceDemo=document.querySelector('.voice-capture'), voiceButton=document.querySelector('.voice-toggle');
  if(voiceDemo&&voiceButton){voiceButton.addEventListener('click',()=>{const active=voiceButton.getAttribute('aria-pressed')!=='true';voiceButton.setAttribute('aria-pressed',String(active));voiceDemo.classList.toggle('is-playing',active);voiceButton.innerHTML=active?'<span aria-hidden="true">Ⅱ</span> Pause preview':'<span aria-hidden="true">▶</span> Animate preview';});}
  const topbar = document.querySelector('.topbar');
  const scrollContainers = [
    document.scrollingElement,
    document.documentElement,
    document.body,
    document.querySelector('[data-testid="stAppViewContainer"]'),
    document.querySelector('[data-testid="stMain"]')
  ].filter(Boolean);
  let lastScrollY = Math.max(window.scrollY, ...scrollContainers.map(node => node.scrollTop || 0));
  let scrollIntent = 0;
  const setNavVisible = (visible, forcePeek = false) => {
    const currentY = Math.max(window.scrollY, ...scrollContainers.map(node => node.scrollTop || 0));
    const peek = visible && (forcePeek || scrollIntent < 0 || currentY > 12);
    topbar.classList.toggle('nav-hidden', !visible);
    topbar.classList.toggle('nav-visible', visible);
    topbar.classList.toggle('nav-peek', peek);
    topbar.style.setProperty('transform', peek ? 'translateX(-50%) translateY(0)' : visible ? 'translateY(0)' : 'translateY(calc(-100% - 28px))', 'important');
    topbar.style.setProperty('opacity', visible ? '1' : '0', 'important');
    topbar.style.setProperty('pointer-events', visible ? 'auto' : 'none', 'important');
    topbar.inert = !visible;
  };
  const hideNav = () => {
    if (topbar.contains(document.activeElement)) document.activeElement.blur();
    setNavVisible(false);
  };
  setNavVisible(true);
  const handleScroll = event => {
    const eventY = event.target && typeof event.target.scrollTop === 'number' ? event.target.scrollTop : 0;
    const currentY = Math.max(window.scrollY, eventY, ...scrollContainers.map(node => node.scrollTop || 0));
    topbar.classList.toggle('scrolled', currentY > 12);
    if (currentY > lastScrollY + 3) { scrollIntent = 1; hideNav(); }
    else if (currentY < lastScrollY - 3) { scrollIntent = -1; setNavVisible(true); }
    else if (currentY <= 12 && scrollIntent !== 1) setNavVisible(true);
    lastScrollY = currentY;
  };
  window.addEventListener('scroll', handleScroll, {passive:true});
  document.addEventListener('scroll', handleScroll, {passive:true,capture:true});
  document.addEventListener('wheel', event => {
    const currentY = Math.max(window.scrollY, ...scrollContainers.map(node => node.scrollTop || 0));
    if (event.deltaY > 0) { scrollIntent = 1; hideNav(); }
    else if (event.deltaY < 0) { scrollIntent = -1; setNavVisible(true); }
  }, {passive:true,capture:true});
  let lastTouchY = null;
  document.addEventListener('touchstart', event => { lastTouchY = event.touches[0]?.clientY ?? null; }, {passive:true,capture:true});
  document.addEventListener('touchmove', event => {
    const touchY = event.touches[0]?.clientY;
    if (lastTouchY !== null && Number.isFinite(touchY)) {
      if (touchY < lastTouchY) { scrollIntent = 1; hideNav(); }
      else if (touchY > lastTouchY) { scrollIntent = -1; setNavVisible(true); }
    }
    lastTouchY = Number.isFinite(touchY) ? touchY : null;
  }, {passive:true,capture:true});
  let lastPointerY = Number.POSITIVE_INFINITY;
  document.addEventListener('pointermove', event => {
    if (event.clientY <= 24 && lastPointerY > 24) { scrollIntent = 0; setNavVisible(true, true); }
    lastPointerY = event.clientY;
  }, {passive:true});
  document.addEventListener('keydown', event => { if (event.key === 'Tab') setNavVisible(true); });
  const menuButton = document.querySelector('.menu-toggle'), menu = document.querySelector('.mobile-menu');
  const closeMenu = () => { menu.classList.remove('open'); menu.inert = true; menuButton.setAttribute('aria-expanded','false'); menuButton.setAttribute('aria-label','Open navigation'); };
  menuButton.addEventListener('click', () => { const open = menuButton.getAttribute('aria-expanded') !== 'true'; menu.classList.toggle('open',open); menu.inert = !open; menuButton.setAttribute('aria-expanded',String(open)); menuButton.setAttribute('aria-label',open?'Close navigation':'Open navigation'); });
  menu.querySelectorAll('a').forEach(link => link.addEventListener('click',closeMenu));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
  const reveals = document.querySelectorAll('.reveal');
  if (reduced || !('IntersectionObserver' in window)) reveals.forEach(item => item.classList.add('visible'));
  else { document.documentElement.classList.add('motion-ready'); const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } }), {threshold:.12,rootMargin:'0px 0px -20px 0px'}); reveals.forEach(item => observer.observe(item)); }
  const sculpture = document.querySelector('[data-sculpture-stage]');
  if (sculpture) {
    // Create the canvas after sanitization: Streamlit's HTML sanitizer can drop
    // canvas elements embedded in the authored markup on some versions.
    const host = sculpture.querySelector('.sculpture-canvas-host');
    const canvas = host && document.createElement('canvas');
    if (host && canvas) { canvas.className = 'sculpture-canvas'; canvas.setAttribute('role','img'); canvas.setAttribute('aria-label','An open orange metallic ribbon. A fragment follows an orbital path, aligns with its gap, and sends a light pulse through the sculpture.'); host.appendChild(canvas); }
    const startThreeSculpture = () => {
      if (!window.THREE || !host) return false;
      try {
        const T=window.THREE,scene=new T.Scene();
        scene.background=null;
        const box=host.getBoundingClientRect(),width=Math.max(1,box.width),height=Math.max(1,box.height);
        const camera=new T.PerspectiveCamera(38,width/height,.1,100);camera.position.set(0,1.8,6.2);camera.lookAt(0,0,0);
        const renderer=new T.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'});
        renderer.setSize(width,height);renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.45;renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
        renderer.domElement.className='sculpture-webgl-canvas';renderer.domElement.setAttribute('aria-hidden','true');host.appendChild(renderer.domElement);
        const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
        const metallicTextureCanvas=document.createElement('canvas');metallicTextureCanvas.width=512;metallicTextureCanvas.height=512;
        const textureContext=metallicTextureCanvas.getContext('2d');textureContext.fillStyle='#cc520e';textureContext.fillRect(0,0,512,512);
        const imageData=textureContext.getImageData(0,0,512,512),pixels=imageData.data;
        for(let i=0;i<pixels.length;i+=4){const noise=(Math.random()-.5)*65,shimmer=Math.random()>.96?50:0;pixels[i]=Math.max(0,Math.min(255,pixels[i]+noise+shimmer));pixels[i+1]=Math.max(0,Math.min(255,pixels[i+1]+noise*.5+shimmer*.4));pixels[i+2]=Math.max(0,Math.min(255,pixels[i+2]+noise*.1));}
        textureContext.putImageData(imageData,0,0);
        const flakeTexture=new T.CanvasTexture(metallicTextureCanvas);flakeTexture.wrapS=T.RepeatWrapping;flakeTexture.wrapT=T.RepeatWrapping;flakeTexture.repeat.set(2,2);
        const orangeMaterial=new T.MeshStandardMaterial({color:0xdb5812,map:flakeTexture,roughness:.28,metalness:.88,emissive:0x3d1402,emissiveIntensity:.2});
        const steelMaterial=new T.MeshStandardMaterial({color:0x98a2b0,metalness:.95,roughness:.22});
        const darkCoreMaterial=new T.MeshStandardMaterial({color:0x16181e,metalness:.85,roughness:.4});
        const ambient=new T.AmbientLight(0x10131c,1.8);scene.add(ambient);
        const keyLight=new T.DirectionalLight(0xffecd6,3.2);keyLight.position.set(5,7,5);keyLight.castShadow=true;keyLight.shadow.mapSize.width=512;keyLight.shadow.mapSize.height=512;scene.add(keyLight);
        const rimLight=new T.DirectionalLight(0x76b6ff,2.4);rimLight.position.set(-6,3,-6);scene.add(rimLight);
        const surgeLight=new T.PointLight(0xff6818,.4,8);scene.add(surgeLight);
        const masterSculpture=new T.Group();scene.add(masterSculpture);
        const TOTAL_BLOCKS=36,ringRadius=2.05,MISSING_INDEX=8,blockWidth=.28,blockHeight=.22,blockDepth=.28;
        const mainGeometry=new T.BoxGeometry(blockWidth,blockHeight,blockDepth);
        const trimGeometry=new T.BoxGeometry(blockWidth*1.02,blockHeight*.18,blockDepth*1.02);
        const seamGeometry=new T.BoxGeometry(blockWidth*.88,.02,blockDepth*.88);
        const createModularBlock=()=>{
          const group=new T.Group(),mainMaterial=orangeMaterial.clone(),mainMesh=new T.Mesh(mainGeometry,mainMaterial);mainMesh.castShadow=true;mainMesh.receiveShadow=true;group.add(mainMesh);
          const trimMesh=new T.Mesh(trimGeometry,steelMaterial);trimMesh.position.y=blockHeight*.42;group.add(trimMesh);
          const bottomTrim=trimMesh.clone();bottomTrim.position.y=-blockHeight*.42;group.add(bottomTrim);
          const seamMaterial=new T.MeshBasicMaterial({color:0xff6210}),seamMesh=new T.Mesh(seamGeometry,seamMaterial);group.add(seamMesh);
          const coreMesh=new T.Mesh(new T.BoxGeometry(blockWidth*.56,blockHeight*.52,blockDepth*.56),darkCoreMaterial);coreMesh.position.z=-blockDepth*.27;group.add(coreMesh);
          return {group,mainMesh,seamMesh};
        };
        const getBlockTransform=i=>{
          const theta=i/TOTAL_BLOCKS*Math.PI*2,foldY=Math.sin(theta*2)*.22;
          const pos=new T.Vector3(Math.cos(theta)*ringRadius,Math.sin(theta)*(ringRadius*.84)+foldY,Math.sin(theta*2)*.38);
          const nextTheta=(i+.05)/TOTAL_BLOCKS*Math.PI*2,nextPos=new T.Vector3(Math.cos(nextTheta)*ringRadius,Math.sin(nextTheta)*(ringRadius*.84)+Math.sin(nextTheta*2)*.22,Math.sin(nextTheta*2)*.38);
          const dummy=new T.Object3D();dummy.position.copy(pos);dummy.lookAt(nextPos);return {pos,quat:dummy.quaternion.clone()};
        };
        const allRingBlocks=[];
        for(let i=0;i<TOTAL_BLOCKS;i++){
          if(i===MISSING_INDEX)continue;
          const block=createModularBlock(),transform=getBlockTransform(i);block.group.position.copy(transform.pos);block.group.quaternion.copy(transform.quat);masterSculpture.add(block.group);allRingBlocks.push({...block,index:i});
        }
        const targetTransform=getBlockTransform(MISSING_INDEX),targetTheta=MISSING_INDEX/TOTAL_BLOCKS*Math.PI*2;
        surgeLight.position.copy(targetTransform.pos);
        const missingBlock=createModularBlock();masterSculpture.add(missingBlock.group);
        const particleCount=80,particlePositions=new Float32Array(particleCount*3);
        for(let p=0;p<particleCount*3;p+=3){particlePositions[p]=(Math.random()-.5)*10;particlePositions[p+1]=(Math.random()-.5)*8;particlePositions[p+2]=(Math.random()-.5)*7;}
        const particleGeometry=new T.BufferGeometry();particleGeometry.setAttribute('position',new T.BufferAttribute(particlePositions,3));
        const particleMaterial=new T.PointsMaterial({color:0xdb5812,size:.022,transparent:true,opacity:.35,depthWrite:false});scene.add(new T.Points(particleGeometry,particleMaterial));
        const CYCLE_TIME=7.2,clock=new T.Clock(),lookObject=new T.Object3D(),exitObject=new T.Object3D(),preAlignQuaternion=new T.Quaternion();
        const smoothStep=(edge0,edge1,x)=>{const t=Math.max(0,Math.min(1,(x-edge0)/(edge1-edge0)));return t*t*(3-2*t);};
        const resize=()=>{const b=host.getBoundingClientRect(),w=Math.max(1,b.width),h=Math.max(1,b.height);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);};
        if('ResizeObserver'in window)new ResizeObserver(resize).observe(host);else window.addEventListener('resize',resize,{passive:true});resize();
        let pointerX=0,pointerY=0;
        if(matchMedia('(pointer:fine)').matches&&!reduced){sculpture.addEventListener('pointermove',e=>{const b=sculpture.getBoundingClientRect();pointerX=((e.clientX-b.left)/b.width-.5)*.05;pointerY=((e.clientY-b.top)/b.height-.5)*.035;},{passive:true});sculpture.addEventListener('pointerleave',()=>{pointerX=pointerY=0;},{passive:true});}
        let raf=0,active=true,hasStarted=false;
        const animate=()=>{
          if(!active||document.hidden)return;
          const elapsed=clock.getElapsedTime(),cycleT=reduced ? .72 : (elapsed%CYCLE_TIME)/CYCLE_TIME;
          masterSculpture.rotation.y=elapsed*.25+pointerX;masterSculpture.rotation.x=Math.sin(elapsed*.3)*.14+.1-pointerY;masterSculpture.rotation.z=Math.cos(elapsed*.2)*.08;
          const targetPos=targetTransform.pos,radialDir=targetPos.clone().normalize(),normalDir=new T.Vector3(0,0,1).applyQuaternion(targetTransform.quat).normalize();
          let glowIntensity=0,pulseProgress=0;
          if(reduced){missingBlock.group.position.copy(targetPos);missingBlock.group.quaternion.copy(targetTransform.quat);glowIntensity=.15;}
          else if(cycleT<.70){
            const p=cycleT/.70,pSmooth=smoothStep(0,1,p),totalAngle=3*Math.PI*2,theta=(targetTheta-totalAngle)+pSmooth*totalAngle;
            if(p<.82){
              const orbitP=p/.82,rClearance=3.65-orbitP,zClearance=1.05+Math.sin(theta*2)*.35+(1-orbitP)*.45;
              const pos=new T.Vector3(Math.cos(theta)*rClearance,Math.sin(theta)*(rClearance*.84),zClearance);missingBlock.group.position.copy(pos);
              const dTheta=theta+.04,nextPos=new T.Vector3(Math.cos(dTheta)*rClearance,Math.sin(dTheta)*(rClearance*.84),zClearance+Math.cos(theta*2)*.02);
              lookObject.position.copy(pos);lookObject.lookAt(nextPos);missingBlock.group.quaternion.copy(lookObject.quaternion);
            }else{
              const insertP=(p-.82)/.18,insertSmooth=smoothStep(0,1,insertP);
              const hoverPosition=targetPos.clone().addScaledVector(radialDir,.55*(1-insertSmooth)).addScaledVector(normalDir,.95*Math.pow(1-insertSmooth,1.4));
              missingBlock.group.position.copy(hoverPosition);
              if(insertP<.04)preAlignQuaternion.copy(missingBlock.group.quaternion);
              missingBlock.group.quaternion.slerpQuaternions(preAlignQuaternion,targetTransform.quat,insertSmooth);
              glowIntensity=insertSmooth*.3;
            }
          }else if(cycleT<.86){
            const dockProgress=(cycleT-.70)/.16;missingBlock.group.position.copy(targetPos);missingBlock.group.quaternion.copy(targetTransform.quat);
            glowIntensity=1+Math.sin(dockProgress*Math.PI*2.5)*.7;pulseProgress=(cycleT-.70)/.16;
          }else{
            const exitProgress=(cycleT-.86)/.14,exitSmooth=smoothStep(0,1,exitProgress),liftDist=exitSmooth*1.1,radialOffset=exitSmooth*.65,orbitCarry=Math.sin(exitSmooth*Math.PI*.5)*.8;
            const tangentDir=new T.Vector3(-Math.sin(targetTheta),Math.cos(targetTheta),0).normalize();
            const exitPos=targetPos.clone().addScaledVector(normalDir,liftDist).addScaledVector(radialDir,radialOffset).addScaledVector(tangentDir,orbitCarry);
            missingBlock.group.position.copy(exitPos);const lookTarget=exitPos.clone().add(tangentDir).addScaledVector(normalDir,.2);exitObject.position.copy(exitPos);exitObject.lookAt(lookTarget);missingBlock.group.quaternion.slerpQuaternions(targetTransform.quat,exitObject.quaternion,exitSmooth);glowIntensity=(1-exitSmooth)*.6;
          }
          const baseGlow=glowIntensity>.05 ? .2+glowIntensity*1.4 : .2;
          orangeMaterial.emissive.setHex(glowIntensity>.05?0xff5000:0x3d1402);orangeMaterial.emissiveIntensity=baseGlow;
          surgeLight.intensity=glowIntensity>.05 ? .4+glowIntensity*4.2 : .4;
          steelMaterial.emissive.setHex(0xff8833);steelMaterial.emissiveIntensity=glowIntensity>.05 ? glowIntensity*.7 : 0;
          for(const block of allRingBlocks){block.mainMesh.material.emissive.setHex(glowIntensity>.05?0xff5000:0x3d1402);block.mainMesh.material.emissiveIntensity=baseGlow;block.seamMesh.material.color.setHex(0xff6210);}
          missingBlock.mainMesh.material.emissive.setHex(glowIntensity>.05?0xff5000:0x3d1402);missingBlock.mainMesh.material.emissiveIntensity=baseGlow;
          if(pulseProgress>0){const pulseIndex=(MISSING_INDEX+1+pulseProgress*(TOTAL_BLOCKS-1))%TOTAL_BLOCKS;for(const block of allRingBlocks){const d=Math.abs(block.index-pulseIndex),distance=Math.min(d,TOTAL_BLOCKS-d),highlight=Math.max(0,1-distance/2.3);block.mainMesh.material.emissiveIntensity=baseGlow+highlight*2.2;block.seamMesh.material.color.setRGB(1,.25+highlight*.5,.04);}}
          renderer.render(scene,camera);
          if(!reduced)raf=requestAnimationFrame(animate);
        };
        document.addEventListener('visibilitychange',()=>{if(document.hidden){active=false;cancelAnimationFrame(raf);}else if(!reduced){active=true;raf=requestAnimationFrame(animate);}});
        sculpture.classList.add('webgl-ready');
        animate();
        return true;
      }catch(error){sculpture.setAttribute('data-sculpture-error',String(error&&error.message||error));console.error('Aster 3D sculpture failed to initialize:',error);return false;}
    };
    let webglReady=startThreeSculpture();
    if(!webglReady&&!window.THREE){
      const loader=document.createElement('script');loader.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';loader.async=true;
      loader.onload=()=>{webglReady=startThreeSculpture();if(webglReady&&sculpture.__asterStopFallback)sculpture.__asterStopFallback();};
      loader.onerror=()=>sculpture.setAttribute('data-sculpture-error','Three.js CDN could not be loaded; showing the animated canvas fallback.');
      document.head.appendChild(loader);
    }
    const ctx = canvas && canvas.getContext('2d');
    if (canvas && ctx && !webglReady) {
      const ribbonStart = [354,78];
      const ribbonSegments = [
        [433,76,493,125,516,191],[543,270,501,345,429,382],
        [350,422,259,418,190,379],[124,342,98,273,120,202],
        [143,129,210,83,289,78]
      ];
      // Start on the upper-right orbit, travel around the ring, dock at its
      // open crown, then peel away along a short return arc.
      const routeStart = [500,130];
      const routeSegments = [
        [543,150,543,270,501,345],[429,420,259,418,190,379],
        [98,342,98,273,120,202],[143,129,210,83,289,78],
        [300,78,322,78,322,78],[382,73,450,90,500,130]
      ];
      const sampleCurves = (start, segments, steps=44) => {
        const points=[{x:start[0],y:start[1]}];
        let origin={x:start[0],y:start[1]};
        for (const segment of segments) {
          const [x1,y1,x2,y2,x3,y3]=segment;
          for (let step=1; step<=steps; step++) {
            const t=step/steps, u=1-t;
            points.push({x:u*u*u*origin.x+3*u*u*t*x1+3*u*t*t*x2+t*t*t*x3,y:u*u*u*origin.y+3*u*u*t*y1+3*u*t*t*y2+t*t*t*y3});
          }
          origin={x:x3,y:y3};
        }
        const lengths=[0];
        for (let i=1;i<points.length;i++) lengths.push(lengths[i-1]+Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y));
        return {points,lengths,total:lengths[lengths.length-1]};
      };
      const ribbon=sampleCurves(ribbonStart,ribbonSegments);
      const route=sampleCurves(routeStart,routeSegments);
      const pointAt=(path,distance)=>{
        let low=0,high=path.lengths.length-1;
        while(low<high){const mid=(low+high)>>1;if(path.lengths[mid]<distance)low=mid+1;else high=mid;}
        const i=Math.max(1,low),a=path.points[i-1],b=path.points[i],span=path.lengths[i]-path.lengths[i-1],f=span?(distance-path.lengths[i-1])/span:0;
        return {x:a.x+(b.x-a.x)*f,y:a.y+(b.y-a.y)*f,angle:Math.atan2(b.y-a.y,b.x-a.x)};
      };
      let dockFraction=.82, gapError=Infinity;
      for(let i=Math.floor(route.points.length*.62);i<Math.floor(route.points.length*.92);i++){const p=route.points[i],e=Math.hypot(p.x-400,p.y-120);if(e<gapError){gapError=e;dockFraction=route.lengths[i]/route.total;}}
      const keyframes=[[0,0],[.48,.58],[.69,Math.max(.58,dockFraction-.075)],[.77,dockFraction],[.87,dockFraction],[1,1]];
      const smooth=v=>v*v*(3-2*v);
      const progressAt=time=>{for(let i=1;i<keyframes.length;i++){const [endT,endD]=keyframes[i];if(time<=endT){const [startT,startD]=keyframes[i-1],f=smooth((time-startT)/(endT-startT));return startD+(endD-startD)*f;}}return 1;};
      const trace=(ctx,path)=>{ctx.beginPath();ctx.moveTo(path.points[0].x,path.points[0].y);for(let i=1;i<path.points.length;i++)ctx.lineTo(path.points[i].x,path.points[i].y);};
      const strokeRibbon=(ctx)=>{ctx.beginPath();ctx.moveTo(ribbonStart[0],ribbonStart[1]);for(const s of ribbonSegments)ctx.bezierCurveTo(s[0],s[1],s[2],s[3],s[4],s[5]);};
      const strokeSlice=(ctx,path,endDistance,tailLength)=>{const begin=Math.max(0,endDistance-tailLength),start=pointAt(path,begin);ctx.beginPath();ctx.moveTo(start.x,start.y);for(let i=1;i<path.points.length;i++)if(path.lengths[i]>begin&&path.lengths[i]<endDistance)ctx.lineTo(path.points[i].x,path.points[i].y);const end=pointAt(path,endDistance);ctx.lineTo(end.x,end.y);ctx.stroke();};
      const dust=[{x:148,y:111,r:2.2,p:.3},{x:504,y:151,r:1.8,p:1.7},{x:475,y:411,r:2.4,p:2.8},{x:163,y:412,r:1.6,p:4.2},{x:92,y:251,r:1.7,p:5.1},{x:397,y:66,r:1.5,p:3.7}];
      // Local, dependency-free version of the supplied Three.js sculpture.
      // Each point is a real projected cuboid; the gap, identical insert, and
      // metallic top/side faces remain visible even when external CDNs are offline.
      const draw=(time,fragmentPoint,connected,pulseProgress,pulseAlpha=1)=>{
        ctx.clearRect(0,0,640,520);
        const haze=ctx.createRadialGradient(320,250,10,320,250,255);haze.addColorStop(0,'rgba(241,138,94,.105)');haze.addColorStop(.48,'rgba(35,47,62,.12)');haze.addColorStop(1,'rgba(8,10,16,0)');ctx.fillStyle=haze;ctx.fillRect(20,0,600,520);
        for(const d of dust){const x=d.x+Math.sin(time*.0012+d.p)*4,y=d.y+Math.cos(time*.001+d.p)*5;ctx.beginPath();ctx.fillStyle=d.p%2?'rgba(241,138,94,.38)':'rgba(221,216,208,.35)';ctx.shadowColor='rgba(241,138,94,.2)';ctx.shadowBlur=8;ctx.arc(x,y,d.r,0,Math.PI*2);ctx.fill();}ctx.shadowBlur=0;
        const yaw=time*.00042+Math.sin(time*.0007)*.13, tilt=-.2+Math.sin(time*.0009)*.055, ringStart=-2.44, rx=164, ry=147;
        const rotate=(x,y,z)=>{const xx=x*Math.cos(yaw)-z*Math.sin(yaw),zz=x*Math.sin(yaw)+z*Math.cos(yaw), yy=y*Math.cos(tilt)-zz*Math.sin(tilt), z2=y*Math.sin(tilt)+zz*Math.cos(tilt);return {x:320+xx*(1+z2*.0009),y:252-yy*(1+z2*.0009),z:z2};};
        const project=(x,y,z)=>rotate(x,y,z);
        const blockAt=(theta,highlight=0)=>{
          const fold=Math.sin(theta*2)*16, x=Math.cos(theta)*rx,y=Math.sin(theta)*ry+fold,z=Math.sin(theta*2)*23;
          const tangent={x:-Math.sin(theta),y:Math.cos(theta)},radial={x:Math.cos(theta),y:Math.sin(theta)};
          const L=12.8,W=10.8,H=11.2, corners=[];
          for(const a of [-1,1])for(const b of [-1,1])corners.push({x:x+tangent.x*L*a+radial.x*W*b,y:y+tangent.y*L*a+radial.y*W*b,z});
          const p=corners.map(q=>project(q.x,q.y,q.z)), depth=H*.72;
          const top=p.map(q=>({x:q.x,y:q.y-depth,z:q.z+depth}));
          const avg=p.reduce((n,q)=>n+q.z,0)/p.length;
          ctx.save();ctx.globalAlpha=.82+Math.max(-.12,Math.min(.12,avg/230));
          const poly=(pts,fill,stroke='rgba(255,221,195,.24)')=>{ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);for(let k=1;k<pts.length;k++)ctx.lineTo(pts[k].x,pts[k].y);ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=.7;ctx.stroke();};
          const light=Math.max(0,Math.min(1,(Math.sin(theta+yaw)+1)*.5));
          const side=ctx.createLinearGradient(p[1].x,p[1].y,p[3].x,p[3].y);side.addColorStop(0,'#262a31');side.addColorStop(.5,'#554b45');side.addColorStop(1,'#1c2028');
          poly([p[1],p[3],top[3],top[1]],side,'rgba(225,181,151,.15)');
          const face=ctx.createLinearGradient(p[0].x,p[0].y,p[3].x,p[3].y);face.addColorStop(0,highlight?'#ffd0ac':'#ef9b6b');face.addColorStop(.42,highlight?'#fa7a3d':(light>.56?'#c7744c':'#824a34'));face.addColorStop(1,'#382e2d');
          poly(p,face,highlight?'rgba(255,225,205,.85)':'rgba(255,212,185,.22)');
          const trim=ctx.createLinearGradient(top[0].x,top[0].y,top[2].x,top[2].y);trim.addColorStop(0,'#d3d1ca');trim.addColorStop(.42,'#777c82');trim.addColorStop(1,'#292e36');
          poly([top[0],top[1],top[3],top[2]],trim,'rgba(242,241,233,.34)');
          ctx.beginPath();ctx.moveTo(top[0].x,top[0].y);ctx.lineTo(top[1].x,top[1].y);ctx.strokeStyle=highlight?'rgba(255,167,112,.95)':'rgba(255,228,209,.48)';ctx.lineWidth=1.15;ctx.stroke();
          if(highlight){ctx.shadowColor='#f18a5e';ctx.shadowBlur=12;ctx.strokeStyle=`rgba(255,146,88,${Math.min(.9,highlight)})`;ctx.lineWidth=2;ctx.stroke();}
          ctx.restore();return avg;
        };
        const blocks=[];for(let i=0;i<36;i++){if(i===8)continue;const theta=ringStart+i/36*Math.PI*2;blocks.push({i,theta,z:Math.sin(theta*2)*23});}
        blocks.sort((a,b)=>a.z-b.z);
        for(const block of blocks){let pulse=0;if(connected&&pulseProgress>0){const distance=(block.i-8+36)%36,pulseIndex=pulseProgress*36;pulse=Math.max(0,1-Math.abs(distance-pulseIndex)/2.4)*pulseAlpha;}blockAt(block.theta,pulse);}
        // Fine internal connector and a single open receiving socket.
        const socketTheta=ringStart+8/36*Math.PI*2, sx=Math.cos(socketTheta)*rx,sy=Math.sin(socketTheta)*ry+Math.sin(socketTheta*2)*16,sz=Math.sin(socketTheta*2)*23;
        const socket=project(sx,sy,sz);ctx.save();ctx.beginPath();ctx.arc(socket.x,socket.y,10,0,Math.PI*2);ctx.strokeStyle=connected?'rgba(255,145,88,.9)':'rgba(241,138,94,.38)';ctx.lineWidth=connected?2.5:1;ctx.shadowColor='#f18a5e';ctx.shadowBlur=connected?16:5;ctx.stroke();ctx.restore();
        // Draw the traveling fragment as the same faceted cuboid as every ring unit.
        const f=fragmentPoint;ctx.save();ctx.translate(f.x,f.y);ctx.rotate(f.angle||0);ctx.shadowColor=connected?'rgba(241,138,94,.9)':'rgba(0,0,0,.6)';ctx.shadowBlur=connected?19:10;ctx.shadowOffsetY=5;
        const shard=ctx.createLinearGradient(-17,-12,18,11);shard.addColorStop(0,'#f4eee5');shard.addColorStop(.24,'#d8d5ce');shard.addColorStop(.48,'#aa603f');shard.addColorStop(.72,'#e59458');shard.addColorStop(1,'#343942');
        ctx.fillStyle=shard;ctx.strokeStyle=connected?'#ffd0ac':'rgba(245,222,204,.72)';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(-17,-9);ctx.lineTo(11,-9);ctx.lineTo(17,-4);ctx.lineTo(17,8);ctx.lineTo(-11,8);ctx.lineTo(-17,3);ctx.closePath();ctx.fill();ctx.stroke();
        ctx.shadowBlur=0;ctx.fillStyle='rgba(232,230,223,.75)';ctx.beginPath();ctx.moveTo(-17,-9);ctx.lineTo(11,-9);ctx.lineTo(13,-5);ctx.lineTo(-14,-5);ctx.closePath();ctx.fill();ctx.fillStyle='rgba(25,30,38,.82)';ctx.beginPath();ctx.moveTo(11,-9);ctx.lineTo(17,-4);ctx.lineTo(17,8);ctx.lineTo(12,4);ctx.closePath();ctx.fill();ctx.restore();
        if(connected&&pulseProgress>0){ctx.save();ctx.globalAlpha=pulseAlpha;ctx.beginPath();ctx.arc(socket.x,socket.y,18+8*Math.sin(pulseProgress*Math.PI),0,Math.PI*2);ctx.strokeStyle='#ffb081';ctx.lineWidth=2;ctx.shadowColor='#f18a5e';ctx.shadowBlur=18;ctx.stroke();ctx.restore();}
      };
      let dpr=1;
      const staticPoint=pointAt(route,route.total*dockFraction);
      const resize=()=>{const rect=sculpture.getBoundingClientRect();dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.max(1,Math.round(rect.width*dpr));canvas.height=Math.max(1,Math.round(rect.height*dpr));ctx.setTransform(canvas.width/640,0,0,canvas.height/520,0,0);draw(0,pointAt(route,0),false,0);};
      resize();
      if('ResizeObserver'in window)new ResizeObserver(resize).observe(sculpture);else window.addEventListener('resize',resize,{passive:true});
      sculpture.classList.add('canvas-ready');
      let elapsed=0,lastFrame=0,raf=0,active=false;
      const renderFrame=now=>{if(!active||document.hidden)return;if(lastFrame)elapsed+=Math.min(now-lastFrame,50);lastFrame=now;const t=(elapsed%7200)/7200,progress=progressAt(t),dist=route.total*progress,point=pointAt(route,dist),ahead=pointAt(route,Math.min(route.total,dist+2));let angle=ahead.angle;if(t>=.69&&t<.77)angle*=1-smooth((t-.69)/.08);const connected=t>=.77&&t<.90;const pulse=Math.min(1,Math.max(0,(t-.77)/.09));const pulseAlpha=t<.86?1:Math.max(0,1-(t-.86)/.04);sculpture.classList.toggle('is-aligning',t>=.69&&t<.77);sculpture.classList.toggle('is-connected',connected);draw(elapsed,{x:point.x,y:point.y,angle:connected?0:angle},connected,pulse,pulseAlpha);raf=requestAnimationFrame(renderFrame);};
      const setActive=value=>{const next=value&&!document.hidden;if(next===active)return;active=next;if(active){lastFrame=0;raf=requestAnimationFrame(renderFrame);}else{cancelAnimationFrame(raf);lastFrame=0;}};
      sculpture.__asterStopFallback=()=>setActive(false);
      if(reduced){sculpture.classList.add('is-static','is-connected');const p=pointAt(route,route.total*dockFraction);draw(0,{x:p.x,y:p.y,angle:0},true,0);}
      else{setActive(true);document.addEventListener('visibilitychange',()=>setActive(!document.hidden));}
      if(matchMedia('(pointer:fine)').matches&&!reduced){sculpture.addEventListener('pointermove',event=>{const bounds=sculpture.getBoundingClientRect(),x=(event.clientX-bounds.left)/bounds.width,y=(event.clientY-bounds.top)/bounds.height;sculpture.style.setProperty('--pointer-x',`${(x*100).toFixed(1)}%`);sculpture.style.setProperty('--pointer-y',`${(y*100).toFixed(1)}%`);canvas.style.transform=`perspective(1200px) rotateX(${((.5-y)*1.8).toFixed(2)}deg) rotateY(${((x-.5)*2.2).toFixed(2)}deg)`;},{passive:true});sculpture.addEventListener('pointerleave',()=>{canvas.style.transform='';sculpture.style.setProperty('--pointer-x','50%');sculpture.style.setProperty('--pointer-y','48%');});}
    } else if (!webglReady) {
      sculpture.classList.add('is-static');
    }
  }
  const graph = document.querySelector('.graph-map'), visual = document.querySelector('.hero-visual');
  if (!graph || reduced || !('IntersectionObserver' in window)) return;
  const phases = [['baseline',350],['followup',2100],['current',3900],['shared',5650],['lesson',7350],['idle',9000]];
  let active = false, cycle = 0, timers = [];
  const clear = () => { timers.forEach(clearTimeout); timers = []; };
  const run = () => { clear(); if (!active || document.hidden) return; const id = ++cycle; phases.forEach(([phase,delay]) => timers.push(setTimeout(() => { if (active && !document.hidden && cycle === id) graph.dataset.phase = phase; },delay))); timers.push(setTimeout(run,10500)); };
  const observer = new IntersectionObserver(entries => { active = Boolean(entries[0] && entries[0].isIntersecting); if (active && !document.hidden) run(); else { cycle++; clear(); graph.dataset.phase = 'idle'; } }, {threshold:.15});
  observer.observe(visual);
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cycle++; clear(); graph.dataset.phase = 'idle'; } else if (active) run(); });
})();
</script>
</body></html>'''
    html = html.replace("</style>", "\n/* Aster editorial landing system */\n:root{--bg:#090b12;--ink:#f3f5fb;--muted:#b3bdcc;--quiet:#8794a8;--line:rgba(214,224,244,.14);--line2:rgba(214,224,244,.22);--orange:#f18a5e;--orange-light:#f3a07d;--violet:#a990ff;--cyan:#6ed3e8;--mint:#7bd0b3;--mono:var(--aster-font-mono,'DM Mono',monospace);--ease:cubic-bezier(.2,.75,.25,1)}\nbody{font-family:var(--aster-font-ui,'Inter',-apple-system,sans-serif);font-size:16px}\n.shell{width:min(2560px,calc(100% - clamp(64px,13vw,320px)));max-width:2560px;margin-inline:auto;min-width:0}\n.topbar{position:sticky;top:0;margin:0;min-height:78px;padding-block:4px}.brand-wordmark{width:310px;max-width:min(310px,42vw)}\n.desktop-nav{gap:34px;margin-right:34px;font-size:14px}\n.hero{grid-template-columns:minmax(0,1.04fr) minmax(0,.96fr);gap:clamp(34px,3.4vw,64px);min-height:0;padding:32px 0 48px}\n.hero-copy{max-width:780px;min-width:0}.hero-visual{max-width:1120px;min-width:0}.eyebrow{margin-bottom:30px;font-size:12px}\n.hero h1{max-width:780px;font-size:clamp(66px,6vw,98px);line-height:1.01;letter-spacing:-.078em}\n.hero-lede{max-width:710px;margin-top:27px;font-size:clamp(19px,1.45vw,22px);line-height:1.7}\n.hero-actions{margin-top:32px;gap:13px}.hero-actions .button{min-height:62px;padding-inline:23px;font-size:15px}\n.hero-meta{gap:12px;margin-top:24px;font-size:12px}\n.workspace{border-radius:22px}.workspace-top{min-height:58px;padding-inline:19px;font-size:10px}\n.workspace-main{grid-template-columns:minmax(0,1.2fr) minmax(245px,.8fr);min-height:355px}\n.graph-map{height:330px}.record-pane{padding:22px 18px 19px}.record-title{font-size:clamp(22px,1.9vw,29px)}\n.record-list li,.record-list b{font-size:12px}.record-list{gap:15px}.record-meta{font-size:12px}\n.workspace-foot{font-size:11px;min-height:44px}\n@media(max-width:1250px){.shell{width:min(100% - 96px,1160px)}.topbar{min-height:80px}.hero{min-height:0;gap:32px;padding:30px 0 40px}.workspace-main{grid-template-columns:minmax(0,1.1fr) minmax(220px,.9fr)}.record-pane{padding:19px 15px}.record-list li{grid-template-columns:minmax(72px,.7fr) minmax(0,1fr)}}\n@media(max-width:940px){.shell{width:calc(100% - 48px)}.topbar{top:0;margin:0;min-height:84px}.desktop-nav{display:none}.hero{grid-template-columns:1fr;gap:34px;min-height:0;padding:34px 0 46px}.hero-copy{max-width:800px}.hero h1{font-size:clamp(62px,8.3vw,84px)}.hero-visual{width:min(100%,820px);margin:0 auto;padding-left:0}.visual-rule{display:none}.workspace-main{grid-template-columns:minmax(0,1.2fr) minmax(230px,.8fr)}}\n@media(max-width:740px){.workspace-main{grid-template-columns:1fr}.graph-pane{min-height:300px;border-right:0;border-bottom:1px solid var(--line)}.graph-map{height:280px}.record-pane{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:14px 20px;padding:19px}.record-pane>:first-child{grid-row:span 2}.record-list li{grid-template-columns:minmax(82px,.7fr) minmax(0,1fr)}.record-list li span{white-space:nowrap}.record-bottom{grid-column:1/-1}}\n@media(max-width:520px){.shell{width:calc(100% - 36px)}.topbar{top:0;margin:0;min-height:70px}.brand-wordmark{width:min(230px,57vw)}.hero{gap:22px;padding:28px 0 36px}.eyebrow{margin-bottom:23px;font-size:10px}.hero h1{font-size:clamp(46px,12vw,62px);line-height:1.04}.hero-lede{margin-top:20px;font-size:17px}.hero-actions{gap:9px;margin-top:23px}.hero-actions .button{min-height:50px;padding-inline:13px;font-size:12px}.hero-meta{font-size:9px;gap:7px}.visual-caption{font-size:8px}.workspace{border-radius:17px}.workspace-top{min-height:45px;padding-inline:10px;font-size:7px}.graph-pane{min-height:245px}.graph-map{height:235px}.graph-name{font-size:9px}.graph-note{font-size:7px}.record-pane{grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr);gap:11px 12px;padding:14px 12px}.record-kicker{font-size:8px}.record-title{font-size:18px}.record-meta{font-size:9px}.record-list{gap:9px}.record-list li,.record-list b{font-size:9px}.record-list li{grid-template-columns:minmax(67px,.72fr) minmax(0,1fr);gap:5px}.record-bottom{font-size:7px}.problem{padding:25px 0 34px}.problem p{font-size:16px}.section{padding:54px 0}.section h2{font-size:34px}.section-intro{font-size:14px}.flow-rail{grid-template-columns:1fr}.flow-step,.flow-step+.flow-step{min-height:0;padding:18px 4px;border-left:0;border-top:1px solid var(--line)}.flow-index{font-size:10px}.flow-step h3{font-size:17px}.flow-step p{font-size:13px}.data-row{grid-template-columns:1fr;gap:12px}.data-row h2{font-size:31px}.data-copy{font-size:14px}.final-cta h2{font-size:32px}}\n@media(prefers-reduced-motion:reduce){.hero-copy,.hero-visual{animation:none!important}}\n\n" + "</style>", 1)
    html = html.replace("</style>", '\n.voice-capture{display:grid;grid-template-columns:minmax(220px,1.1fr) minmax(160px,1fr) auto;align-items:center;gap:20px;min-height:86px;padding:14px 20px;border-bottom:1px solid var(--line);background:linear-gradient(100deg,rgba(95,106,158,.075),rgba(21,25,36,.15))}\n.voice-leading{display:flex;align-items:center;gap:13px;min-width:0}.voice-mic{display:grid;place-items:center;width:43px;height:43px;flex:0 0 43px;border:1px solid rgba(111,204,230,.28);border-radius:14px;color:#94d9eb;background:rgba(69,152,188,.12);box-shadow:inset 0 1px rgba(255,255,255,.08)}.voice-mic svg{width:21px;height:21px}.voice-leading strong{display:block;color:#e9edf5;font-size:14px;font-weight:600}.voice-leading small{display:block;margin-top:4px;color:#929baa;font-size:11px;line-height:1.4}\n.voice-wave{display:flex;align-items:center;justify-content:center;gap:4px;height:38px;min-width:0;overflow:hidden}.voice-wave i{width:3px;height:var(--wave);flex:0 0 3px;max-height:28px;border-radius:5px;background:linear-gradient(180deg,#8fe1ee,#8782df);opacity:.55;transform:scaleY(.32);transform-origin:center;animation:voice-idle 1.8s ease-in-out var(--delay) infinite alternate}.voice-capture.is-playing .voice-wave i{opacity:.92;animation-name:voice-active;animation-duration:.62s}.voice-capture.is-playing .voice-mic{color:#ffc0a2;border-color:rgba(241,138,94,.55);background:rgba(241,138,94,.15);box-shadow:0 0 22px rgba(241,138,94,.12)}\n.voice-toggle{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:38px;padding:0 13px;border:1px solid rgba(214,224,244,.16);border-radius:10px;background:rgba(255,255,255,.04);color:#c8d0de;font-family:var(--aster-font-ui,Inter,sans-serif);font-size:11px;font-weight:550;white-space:nowrap;cursor:pointer;transition:background .18s,border-color .18s,transform .18s}.voice-toggle:hover{border-color:rgba(110,211,232,.35);background:rgba(255,255,255,.075);transform:translateY(-1px)}.voice-toggle:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}.voice-toggle:active{transform:scale(.98)}\n@keyframes voice-idle{to{transform:scaleY(.7);opacity:.82}}@keyframes voice-active{0%{transform:scaleY(.22)}50%{transform:scaleY(1)}100%{transform:scaleY(.35)}}\n@media(max-width:980px){.shell{width:min(100% - 52px,900px)}.voice-capture{grid-template-columns:1fr auto;gap:12px}.voice-wave{grid-column:1/-1;grid-row:2;justify-content:flex-start}.voice-toggle{grid-column:2;grid-row:1}.workspace-main{min-height:340px}}\n@media(max-width:520px){.shell{width:calc(100% - 32px)}.topbar{min-height:64px}.voice-capture{grid-template-columns:minmax(0,1fr) auto;min-height:74px;gap:9px;padding:11px 12px}.voice-mic{width:36px;height:36px;flex-basis:36px;border-radius:11px}.voice-leading{gap:9px}.voice-leading strong{font-size:12px}.voice-leading small{font-size:9px}.voice-toggle{min-height:34px;padding-inline:9px;font-size:9px}.voice-wave{height:25px;gap:3px}.voice-wave i{width:2px;flex-basis:2px}}\n@media(prefers-reduced-motion:reduce){.voice-wave i{animation:none!important;transform:scaleY(.45)!important}.voice-capture.is-playing .voice-wave i{transform:scaleY(.6)!important}}\n\n' + "</style>", 1)
    html = html.replace("</style>", "\n@media(max-width:1250px) and (min-width:941px){.brand-wordmark{width:250px}.desktop-nav{gap:17px;margin-right:15px;font-size:13px}.nav-actions{gap:8px}.nav-actions .button{min-height:48px;padding-inline:15px;font-size:13px}}\n.shell>*{min-width:0;max-width:100%}img,svg{max-width:100%}\n</style>", 1)
    nav_css = """
.topbar{position:relative;top:auto;z-index:50;display:flex;align-items:center;justify-content:space-between;box-sizing:border-box;min-height:78px;margin:0 auto;padding:0;border:0;border-bottom:1px solid var(--line);border-radius:0;background:transparent;backdrop-filter:none;-webkit-backdrop-filter:none;box-shadow:none;transition:transform .24s cubic-bezier(.2,.75,.25,1),opacity .18s ease,border-color .2s}
.topbar.nav-peek{position:fixed!important;top:0!important;left:50%!important;width:min(1784px,calc(100vw - 96px))!important;margin:0!important;z-index:1000!important}
.topbar.scrolled{border-color:var(--line);background:transparent;backdrop-filter:none;-webkit-backdrop-filter:none}
.topbar .brand-wordmark{width:220px;max-width:min(220px,32vw)}
.topbar .desktop-nav{position:static;left:auto;transform:none;margin:0 28px 0 auto;gap:26px}.topbar .nav-actions{margin-left:0;gap:9px}.topbar .nav-actions .button{min-height:44px;padding:0 16px;border-radius:12px;font-size:13px}
.topbar.nav-hidden,.topbar.nav-hidden:focus-within{transform:translateY(calc(-100% - 28px))!important;opacity:0!important;pointer-events:none!important}.topbar.nav-visible{transform:translateY(0)!important;opacity:1!important;pointer-events:auto!important}.topbar:focus-within{transform:translateY(0)!important;opacity:1!important;pointer-events:auto!important}
@media(max-width:1250px){.topbar{min-height:72px}.topbar.nav-peek{width:min(1160px,calc(100vw - 96px))!important}.topbar .brand-wordmark{width:200px;max-width:min(200px,32vw)}.topbar .desktop-nav{gap:20px;margin-right:20px;font-size:12px}.topbar .nav-actions .button{min-height:40px;padding-inline:13px;font-size:12px}}
@media(max-width:940px){.topbar{min-height:68px}.topbar.nav-peek{width:calc(100vw - 48px)!important}.topbar .brand-wordmark{width:min(190px,40vw)}.topbar .desktop-nav{display:none}.topbar .nav-actions{margin-left:auto}}
@media(max-width:520px){.topbar{min-height:60px}.topbar.nav-peek{width:calc(100vw - 36px)!important}.topbar .brand-wordmark{width:min(170px,45vw)}.topbar .nav-actions .button{min-height:38px;padding-inline:10px;border-radius:10px;font-size:10px}}
@media(prefers-reduced-motion:reduce){.topbar{transition:none!important}}
"""
    html = html.replace("</style>", nav_css + "</style>", 1)
    sculpture_css = """
.sculpture-visual{display:grid;place-items:center;min-height:500px;margin:0;padding:0;max-width:100%;overflow:visible}
.sculpture-stage{position:relative;display:grid;place-items:center;width:min(100%,680px);aspect-ratio:640/520;isolation:isolate;overflow:visible;background:radial-gradient(ellipse at var(--pointer-x,50%) var(--pointer-y,48%),rgba(241,138,94,.07),transparent 38%),radial-gradient(ellipse at 50% 52%,rgba(31,43,58,.32),transparent 68%);perspective:1200px}
.sculpture-canvas-host,.sculpture-canvas,.sculpture-webgl-canvas{position:absolute;inset:0;display:block;width:100%;height:100%}.sculpture-canvas,.sculpture-webgl-canvas{opacity:0;transform:perspective(1200px) rotateX(0) rotateY(0);transform-origin:50% 50%;transition:opacity .28s,transform .48s cubic-bezier(.2,.75,.25,1)}.sculpture-webgl-canvas{pointer-events:none}.canvas-ready .sculpture-canvas,.webgl-ready .sculpture-webgl-canvas{opacity:1}.canvas-ready .sculpture-fallback,.webgl-ready .sculpture-fallback{opacity:0;visibility:hidden}.webgl-ready .sculpture-canvas{display:none}
.sculpture-fallback{position:absolute;inset:4% 6%;display:grid;place-items:center;transition:opacity .25s,visibility .25s}
.fallback-ribbon{position:relative;display:block;width:72%;height:76%;border-radius:50%;transform:rotate(-18deg) scaleY(.84);background:conic-gradient(from -48deg,transparent 0deg 42deg,#4b4e51 48deg,#c17a5d 84deg,#f18a5e 144deg,#b56143 230deg,#656363 298deg,transparent 326deg);-webkit-mask:radial-gradient(ellipse,transparent 0 52%,#000 54% 70%,transparent 72%);mask:radial-gradient(ellipse,transparent 0 52%,#000 54% 70%,transparent 72%);filter:drop-shadow(0 14px 18px rgba(0,0,0,.45)) drop-shadow(0 0 9px rgba(241,138,94,.12))}
.fallback-fragment{position:absolute;left:50%;top:11%;width:46px;height:23px;transform:translateX(-50%) rotate(-2deg);background:linear-gradient(130deg,#fff0e5,#ec966f 34%,#a85a40 72%,#d9d0c6);clip-path:polygon(0 14%,74% 14%,100% 50%,74% 86%,0 86%,14% 50%);filter:drop-shadow(0 6px 10px rgba(0,0,0,.55))}
.fallback-ribbon{animation:fallback-turn 7.2s ease-in-out infinite}.fallback-fragment{offset-path:ellipse(36% 35% at 50% 50%);offset-rotate:auto;animation:fallback-orbit 7.2s cubic-bezier(.42,0,.58,1) infinite}@keyframes fallback-turn{0%,100%{rotate:-5deg;scale:1 .98}50%{rotate:5deg;scale:1 1.02}}@keyframes fallback-orbit{0%{offset-distance:3%;opacity:1}70%{offset-distance:72%;opacity:1}78%,87%{offset-distance:80%;opacity:1}100%{offset-distance:100%;opacity:1}}
.fallback-dust{position:absolute;width:4px;height:4px;border-radius:50%;background:#f0c2a6;opacity:.55;box-shadow:0 0 12px rgba(241,138,94,.4);animation:fallback-drift 7s ease-in-out infinite alternate}.dust-a{left:21%;top:28%}.dust-b{right:18%;bottom:21%;animation-delay:-3s}@keyframes fallback-drift{to{transform:translate(5px,-7px);opacity:.3}}
.is-connected .sculpture-fallback:after{content:"";position:absolute;left:14%;right:14%;top:18%;bottom:18%;border-radius:50%;border:1px solid rgba(241,138,94,.22);filter:blur(2px)}
.sculpture-fallback{inset:0;display:block;opacity:1;visibility:visible;transition:opacity .25s,visibility .25s}
.aster-sculpture-svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible;pointer-events:none}
.aster-ring-turn{transform-box:view-box;transform-origin:320px 258px;animation:aster-ring-drift 28s ease-in-out infinite alternate}
.aster-segment{animation:aster-segment-pulse 7.2s linear infinite;animation-delay:calc(-.08s + var(--segment)*.022s);transform-box:fill-box}
.aster-arriving-piece{offset-path:path("M 505 74 C 545 165 525 278 451 337 C 374 399 263 399 186 348 C 112 300 112 216 156 153 C 207 80 299 70 398.8 138.5 L 421 116 L 505 74");offset-distance:0%;offset-rotate:auto;offset-anchor:center;animation:aster-piece-journey 7.2s linear infinite;filter:drop-shadow(0 5px 7px rgba(0,0,0,.64));transform-box:view-box}
.aster-piece-glow{opacity:0;animation:aster-dock-glow 7.2s linear infinite}
.aster-socket-glow{opacity:.18;animation:aster-socket-pulse 7.2s ease-in-out infinite}
.aster-atmosphere{opacity:.55;animation:aster-atmosphere 5s ease-in-out infinite alternate}
@keyframes aster-ring-drift{0%{transform:rotate(-2.4deg) scaleY(.985)}100%{transform:rotate(2.4deg) scaleY(1.015)}}
@keyframes aster-segment-pulse{0%,69%{filter:brightness(1)}72%{filter:brightness(1.9)}77%{filter:brightness(1.35)}90%,100%{filter:brightness(1)}}
@keyframes aster-piece-journey{0%{offset-distance:0%}64%{offset-distance:78%}73%{offset-distance:89%}86%{offset-distance:89%}100%{offset-distance:100%}}
@keyframes aster-dock-glow{0%,71%{opacity:0}75%,84%{opacity:.82}91%,100%{opacity:0}}
@keyframes aster-socket-pulse{0%,72%{opacity:.14;stroke-width:1.2}77%,84%{opacity:.9;stroke-width:3.2}92%,100%{opacity:.14;stroke-width:1.2}}
@keyframes aster-atmosphere{to{opacity:.3;transform:translateY(-4px)}}
@media(max-width:980px){.sculpture-visual{min-height:0;padding:0;margin:0 auto;width:min(100%,760px)}.sculpture-stage{width:min(100%,620px)}}
@media(max-width:520px){.sculpture-visual{width:100%;min-height:0}.sculpture-stage{width:min(100%,440px)}}
@media(prefers-reduced-motion:reduce){.sculpture-canvas{transition:none!important}.aster-ring-turn,.aster-segment,.aster-piece-glow,.aster-socket-glow,.aster-atmosphere{animation:none!important}.aster-arriving-piece{animation:none!important;offset-distance:89%}.aster-segment{filter:none!important}}
"""
    html = html.replace("</style>", sculpture_css + "</style>", 1)
    html = html.replace("__BRAND__", brand).replace("__SCULPTURE_ART__", _sculpture_svg())
    st.html(html, unsafe_allow_javascript=True)
