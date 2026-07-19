from __future__ import annotations

import json
import math
import os
import html
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent
from typing import Any
from urllib.parse import quote as url_quote

import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception:  # pragma: no cover - optional chart upgrade
    go = None
    make_subplots = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover - the app still works without yfinance
    yf = None

try:
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
except Exception:  # pragma: no cover - Alpaca is an optional free data upgrade
    DataFeed = None
    StockBarsRequest = None
    StockHistoricalDataClient = None
    TimeFrame = None
    TimeFrameUnit = None


APP_DIR = Path(__file__).resolve().parent
APP_NAME = "Trading for Dummys 101"
DATA_DIR = APP_DIR / "data"
ASSETS_DIR = APP_DIR / "assets"
LIGHTWEIGHT_CHARTS_FILE = ASSETS_DIR / "lightweight-charts.standalone.production.js"
COMPANION_PROFILES = {
    "Scout": {
        "asset": "companion_scout.svg",
        "tagline": "Clean setup coach",
        "style": "balanced",
        "accent": "#38BDF8",
    },
    "Null": {
        "asset": "companion_null.svg",
        "tagline": "Quiet risk checker",
        "style": "defensive",
        "accent": "#A78BFA",
    },
    "Nova": {
        "asset": "companion_nova.svg",
        "tagline": "Catalyst and news scout",
        "style": "curious",
        "accent": "#22D3EE",
    },
    "Flux": {
        "asset": "companion_flux.svg",
        "tagline": "Fast momentum watcher",
        "style": "aggressive",
        "accent": "#F59E0B",
    },
}
AI_COMPANION_HTML = """
<div id="msaAiCompanionRoot"></div>
"""
AI_COMPANION_CSS = """
:host {
  --pet-accent: #38BDF8;
  --pet-bg: #101821;
  --pet-panel: rgba(11, 17, 23, .94);
  --pet-text: #F3F7FA;
  --pet-muted: #B7C2D0;
  --pet-border: rgba(148, 163, 184, .28);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.pet-shell {
  position: fixed;
  right: 22px;
  bottom: 24px;
  z-index: 2147483000;
  width: min(276px, calc(100vw - 24px));
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr);
  gap: 7px;
  align-items: end;
  pointer-events: none;
  user-select: none;
}
.pet-shell.pet-focus {
  width: min(318px, calc(100vw - 24px));
  grid-template-columns: 84px minmax(0, 1fr);
}
.pet-shell.pet-hidden {
  display: none;
}
.pet-bubble {
  pointer-events: auto;
  border: 1px solid var(--pet-border);
  border-radius: 9px;
  background: var(--pet-panel);
  color: var(--pet-text);
  box-shadow: 0 18px 44px rgba(0, 0, 0, .34);
  padding: 9px 10px;
  min-height: 76px;
  backdrop-filter: blur(14px);
}
.pet-ready .pet-bubble {
  border-color: rgba(0, 200, 5, .62);
  box-shadow: 0 18px 48px rgba(0, 200, 5, .18), 0 18px 44px rgba(0, 0, 0, .34);
}
.pet-watch .pet-bubble {
  border-color: rgba(245, 158, 11, .68);
  box-shadow: 0 18px 48px rgba(245, 158, 11, .16), 0 18px 44px rgba(0, 0, 0, .34);
}
.pet-danger .pet-bubble {
  border-color: rgba(255, 55, 95, .68);
  box-shadow: 0 18px 48px rgba(255, 55, 95, .18), 0 18px 44px rgba(0, 0, 0, .34);
}
.pet-sell .pet-bubble {
  border-color: rgba(56, 189, 248, .72);
  box-shadow: 0 18px 48px rgba(56, 189, 248, .20), 0 18px 44px rgba(0, 0, 0, .34);
}
.pet-kicker {
  color: var(--pet-accent);
  font-size: 9px;
  font-weight: 900;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.pet-status-row {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 7px;
  min-width: 0;
}
.pet-status-pill {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: 1px solid rgba(148, 163, 184, .24);
  border-radius: 999px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, .05);
  color: var(--pet-text);
  font-size: 10px;
  font-weight: 800;
}
.pet-status-light {
  flex: 0 0 auto;
  width: 13px;
  height: 13px;
  border-radius: 999px;
  background: var(--pet-muted);
  border: 2px solid rgba(255, 255, 255, .58);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, .07), 0 0 14px rgba(183, 194, 208, .46);
}
.pet-status-time {
  flex: 0 0 auto;
  color: var(--pet-muted);
  font-size: 9px;
}
.pet-ready .pet-status-light {
  background: #00C805;
  box-shadow: 0 0 0 3px rgba(0, 200, 5, .12), 0 0 18px rgba(0, 200, 5, .74);
}
.pet-watch .pet-status-light,
.pet-neutral .pet-status-light {
  background: #FF375F;
  box-shadow: 0 0 0 3px rgba(255, 55, 95, .12), 0 0 18px rgba(255, 55, 95, .68);
}
.pet-danger .pet-status-light {
  background: #FF375F;
  box-shadow: 0 0 0 3px rgba(255, 55, 95, .12), 0 0 18px rgba(255, 55, 95, .74);
}
.pet-sell .pet-status-light {
  background: #38BDF8;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, .16), 0 0 18px rgba(56, 189, 248, .78);
}
.pet-ready .pet-status-pill {
  border-color: rgba(0, 200, 5, .72);
  color: #D9FFE5;
}
.pet-watch .pet-status-pill {
  border-color: rgba(245, 158, 11, .76);
  color: #FFF3D4;
}
.pet-danger .pet-status-pill {
  border-color: rgba(255, 55, 95, .76);
  color: #FFE1E8;
}
.pet-sell .pet-status-pill {
  border-color: rgba(56, 189, 248, .78);
  color: #DFF6FF;
}
.pet-message {
  margin-top: 5px;
  color: var(--pet-text);
  font-size: 12px;
  line-height: 1.28;
  min-height: 40px;
}
.pet-controls {
  display: flex;
  gap: 6px;
  margin-top: 7px;
}
.pet-control {
  display: grid;
  place-items: center;
  min-width: 34px;
  height: 22px;
  border: 1px solid var(--pet-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, .04);
  color: var(--pet-muted);
  padding: 0 8px;
  font-size: 10px;
  font-weight: 850;
  cursor: pointer;
}
.pet-control:hover {
  border-color: var(--pet-accent);
  color: var(--pet-text);
}
.pet-stage {
  pointer-events: auto;
  width: 76px;
  height: 112px;
  position: relative;
  cursor: grab;
  touch-action: none;
  filter: drop-shadow(0 18px 28px rgba(0, 0, 0, .36));
  animation: pet-breathe 3.8s ease-in-out infinite;
}
.pet-focus .pet-stage {
  transform-origin: bottom center;
  scale: 1.08;
}
.pet-stage:active {
  cursor: grabbing;
}
.pet-shadow {
  position: absolute;
  left: 18px;
  bottom: 0;
  width: 40px;
  height: 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, .32);
  filter: blur(2px);
  animation: pet-shadow 3.8s ease-in-out infinite;
}
.pet-body {
  position: absolute;
  left: 18px;
  bottom: 12px;
  width: 40px;
  height: 51px;
  border-radius: 9px 9px 6px 6px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, .13) 0 15%, transparent 16%),
    linear-gradient(180deg, color-mix(in srgb, var(--pet-accent) 18%, #162132) 0%, #0F1722 80%);
  border: 2px solid var(--pet-accent);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .08), inset 0 -14px 22px rgba(0, 0, 0, .24);
  overflow: hidden;
}
.pet-body:before {
  content: "";
  position: absolute;
  left: 5px;
  right: 5px;
  top: 4px;
  height: 2px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--pet-accent) 62%, transparent);
}
.pet-shoulders {
  position: absolute;
  left: 11px;
  bottom: 59px;
  width: 54px;
  height: 15px;
  border-radius: 8px 8px 4px 4px;
  background: linear-gradient(180deg, #152030, #101821);
  border: 2px solid var(--pet-accent);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .08);
}
.pet-neck {
  position: absolute;
  left: 32px;
  bottom: 65px;
  width: 11px;
  height: 11px;
  border-radius: 3px;
  background: #101821;
  border: 2px solid var(--pet-accent);
}
.pet-chest {
  position: absolute;
  left: 6px;
  top: 9px;
  width: 28px;
  height: 24px;
  border-radius: 5px;
  border: 1px solid rgba(148, 163, 184, .28);
  background: linear-gradient(180deg, rgba(255, 255, 255, .08), rgba(255, 255, 255, .02));
}
.pet-chest:after {
  content: "";
  position: absolute;
  left: 6px;
  right: 6px;
  bottom: 5px;
  height: 3px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--pet-accent) 72%, #293546);
}
.pet-belt {
  position: absolute;
  left: 6px;
  right: 6px;
  bottom: 10px;
  height: 4px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--pet-accent) 62%, #293546), transparent);
}
.pet-core {
  position: absolute;
  left: 15px;
  top: 14px;
  width: 10px;
  height: 10px;
  border-radius: 4px;
  background: #00C805;
  box-shadow: 0 0 16px color-mix(in srgb, var(--pet-accent) 65%, transparent);
}
.pet-watch .pet-core,
.pet-watch .pet-eye,
.pet-watch .pet-antenna:after {
  background: #F59E0B;
}
.pet-danger .pet-core,
.pet-danger .pet-eye,
.pet-danger .pet-antenna:after {
  background: #FF375F;
}
.pet-sell .pet-core,
.pet-sell .pet-eye,
.pet-sell .pet-antenna:after {
  background: #38BDF8;
}
.pet-danger .pet-mouth {
  border-bottom-color: #FF9CB1;
}
.pet-sell .pet-mouth {
  border-bottom-color: #DFF6FF;
}
.pet-head {
  position: absolute;
  left: 11px;
  bottom: 70px;
  width: 54px;
  height: 41px;
  border-radius: 11px 11px 9px 9px;
  background:
    radial-gradient(circle at 50% 0%, color-mix(in srgb, var(--pet-accent) 28%, transparent), transparent 48%),
    linear-gradient(180deg, #172232 0%, #101821 100%);
  border: 2px solid var(--pet-accent);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .08), 0 0 22px color-mix(in srgb, var(--pet-accent) 20%, transparent);
  animation: pet-head 5.4s ease-in-out infinite;
}
.pet-head:before {
  content: "";
  position: absolute;
  inset: 6px 8px auto 8px;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .17), transparent);
}
.pet-ear {
  position: absolute;
  bottom: 84px;
  width: 9px;
  height: 19px;
  border-radius: 5px;
  background: #101821;
  border: 2px solid var(--pet-accent);
}
.pet-ear-left {
  left: 7px;
  rotate: -14deg;
}
.pet-ear-right {
  right: 7px;
  rotate: 14deg;
}
.pet-crest {
  position: absolute;
  left: 33px;
  bottom: 107px;
  width: 10px;
  height: 13px;
  border-radius: 5px 5px 2px 2px;
  background: var(--pet-accent);
  box-shadow: 0 0 18px color-mix(in srgb, var(--pet-accent) 70%, transparent);
}
.pet-antenna {
  position: absolute;
  left: 36px;
  bottom: 107px;
  width: 3px;
  height: 12px;
  border-radius: 999px;
  background: var(--pet-accent);
}
.pet-antenna:after {
  content: "";
  position: absolute;
  left: -4px;
  top: -9px;
  width: 11px;
  height: 11px;
  border-radius: 3px;
  background: #00C805;
  box-shadow: 0 0 18px color-mix(in srgb, var(--pet-accent) 70%, transparent);
}
.pet-face {
  position: absolute;
  left: 7px;
  top: 9px;
  width: 38px;
  height: 23px;
  border-radius: 6px;
  background: #0B1117;
  border: 1px solid rgba(148, 163, 184, .24);
  overflow: hidden;
}
.pet-face:before {
  content: "";
  position: absolute;
  left: 5px;
  right: 5px;
  top: 4px;
  height: 2px;
  border-radius: 999px;
  background: rgba(255, 255, 255, .16);
}
.pet-avatar-decal {
  position: absolute;
  left: 6px;
  top: 6px;
  width: 28px;
  height: 28px;
  object-fit: contain;
  opacity: .32;
  mix-blend-mode: screen;
  pointer-events: none;
}
.pet-eye {
  position: absolute;
  top: 8px;
  width: 6px;
  height: 6px;
  border-radius: 2px;
  background: #00C805;
  animation: pet-blink 4.8s infinite;
}
.pet-eye-left {
  left: 9px;
}
.pet-eye-right {
  right: 9px;
}
.pet-mouth {
  position: absolute;
  left: 13px;
  bottom: 5px;
  width: 12px;
  height: 4px;
  border-bottom: 2px solid var(--pet-muted);
  border-radius: 999px;
}
.pet-arm {
  position: absolute;
  bottom: 38px;
  width: 8px;
  height: 31px;
  border-radius: 5px;
  background: #101821;
  border: 2px solid var(--pet-accent);
  transform-origin: top center;
}
.pet-arm-left {
  left: 8px;
  rotate: 16deg;
  animation: pet-wave-left 5.8s ease-in-out infinite;
}
.pet-arm-right {
  right: 8px;
  rotate: -16deg;
  animation: pet-wave-right 6.2s ease-in-out infinite;
}
.pet-hand {
  position: absolute;
  bottom: 33px;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--pet-accent) 54%, #101821);
  border: 2px solid #101821;
}
.pet-hand-left {
  left: 6px;
}
.pet-hand-right {
  right: 6px;
}
.pet-leg {
  position: absolute;
  bottom: 4px;
  width: 9px;
  height: 16px;
  border-radius: 3px;
  background: #101821;
  border: 2px solid var(--pet-accent);
}
.pet-leg-left {
  left: 24px;
}
.pet-leg-right {
  right: 24px;
}
.pet-foot {
  position: absolute;
  bottom: 0;
  width: 17px;
  height: 8px;
  border-radius: 4px;
  background: #101821;
  border: 2px solid var(--pet-accent);
}
.pet-foot-left {
  left: 19px;
}
.pet-foot-right {
  right: 19px;
}
.pet-spark {
  position: absolute;
  border-radius: 999px;
  background: var(--pet-accent);
  opacity: .38;
  box-shadow: 0 0 14px var(--pet-accent);
}
.pet-spark-one {
  width: 5px;
  height: 5px;
  left: 8px;
  top: 25px;
  animation: pet-orbit-one 4s linear infinite;
}
.pet-spark-two {
  width: 4px;
  height: 4px;
  right: 8px;
  top: 48px;
  animation: pet-orbit-two 5s linear infinite;
}
.pet-wander {
  animation: pet-wander 42s ease-in-out infinite;
}
.pet-manual {
  animation: none;
}
.pet-style-defensive .pet-antenna,
.pet-style-defensive .pet-crest {
  display: none;
}
.pet-style-defensive .pet-head {
  border-radius: 19px 19px 12px 12px;
}
.pet-style-curious .pet-crest {
  width: 14px;
  left: 34px;
  border-radius: 999px;
  opacity: .86;
}
.pet-style-aggressive .pet-crest {
  width: 12px;
  height: 22px;
  left: 35px;
  bottom: 108px;
  border-radius: 3px 999px 3px 999px;
  rotate: 12deg;
}
@keyframes pet-breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
@keyframes pet-shadow {
  0%, 100% { transform: scaleX(1); opacity: .34; }
  50% { transform: scaleX(.74); opacity: .2; }
}
@keyframes pet-head {
  0%, 100% { transform: rotate(-1.2deg); }
  50% { transform: rotate(1.6deg); }
}
@keyframes pet-blink {
  0%, 92%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(.08); }
}
@keyframes pet-wave-left {
  0%, 100% { transform: rotate(5deg); }
  50% { transform: rotate(-8deg); }
}
@keyframes pet-wave-right {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(7deg); }
}
@keyframes pet-orbit-one {
  0% { transform: translate(0, 0); }
  50% { transform: translate(10px, 18px); }
  100% { transform: translate(0, 0); }
}
@keyframes pet-orbit-two {
  0% { transform: translate(0, 0); }
  50% { transform: translate(-12px, -15px); }
  100% { transform: translate(0, 0); }
}
@keyframes pet-wander {
  0%, 100% { transform: translate(0, 0); }
  25% { transform: translate(-8px, -5px); }
  50% { transform: translate(-4px, -10px); }
  75% { transform: translate(8px, -4px); }
}
@media (max-width: 720px) {
  .pet-shell {
    width: min(260px, calc(100vw - 22px));
    grid-template-columns: 78px minmax(0, 1fr);
    right: 10px;
    bottom: 12px;
  }
  .pet-stage {
    width: 78px;
    height: 112px;
    scale: .82;
    transform-origin: bottom left;
  }
  .pet-bubble {
    font-size: 12px;
    min-height: 78px;
  }
}
"""
AI_COMPANION_JS = """
export default function(component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component
  const root = parentElement.querySelector("#msaAiCompanionRoot")
  if (!root) return

  if (!data || data.enabled === false) {
    root.innerHTML = ""
    return
  }

  const name = data.name || "Scout"
  const accentRaw = data.accent || "#38BDF8"
  const accent = /^#[0-9a-fA-F]{3,8}$/.test(String(accentRaw)) ? String(accentRaw) : "#38BDF8"
  const mode = data.motion || "Docked"
  const status = data.status || "Watching"
  const updated = data.updated || ""
  const avatar = data.avatar || ""
  const styleValue = String(data.style || "balanced").toLowerCase()
  const safeStyle = ["balanced", "defensive", "curious", "aggressive"].includes(styleValue) ? styleValue : "balanced"
  const moodValue = String(data.mood || "neutral").toLowerCase()
  const safeMood = ["ready", "watch", "danger", "neutral", "sell"].includes(moodValue) ? moodValue : "neutral"
  const messages = Array.isArray(data.messages) && data.messages.length
    ? data.messages
    : [`${name} is watching your paper-trading workflow.`]
  const storageKey = `msa-ai-companion-position-${name}`
  const tipStorageKey = `msa-ai-companion-tip-${name}`
  const saved = (() => {
    try { return JSON.parse(localStorage.getItem(storageKey) || "null") } catch (_) { return null }
  })()
  const savedTipIndex = (() => {
    try {
      const parsed = parseInt(localStorage.getItem(tipStorageKey) || "0", 10)
      return Number.isFinite(parsed) ? parsed : 0
    } catch (_) {
      return 0
    }
  })()
  const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
  let tipIndex = ((savedTipIndex % messages.length) + messages.length) % messages.length
  const message = String(messages[tipIndex] || "")
  const avatarMarkup = avatar
    ? `<img class="pet-avatar-decal" alt="" src="${escapeHtml(avatar)}">`
    : ""
  const faceMarkup = `<div class="pet-eye pet-eye-left"></div><div class="pet-eye pet-eye-right"></div><div class="pet-mouth"></div>`
  const shellClass = ["pet-shell", `pet-${safeMood}`, `pet-style-${safeStyle}`]
  if (mode === "Wander") shellClass.push("pet-wander")
  if (mode === "Focus") shellClass.push("pet-focus")
  const updatedMarkup = updated
    ? `<span class="pet-status-time">${escapeHtml(updated)}</span>`
    : ""

  root.innerHTML = `
    <div class="${shellClass.join(" ")}" style="--pet-accent: ${accent};">
      <div class="pet-stage" title="Drag ${name} anywhere">
        <div class="pet-shadow"></div>
        <div class="pet-spark pet-spark-one"></div>
        <div class="pet-spark pet-spark-two"></div>
        <div class="pet-ear pet-ear-left"></div>
        <div class="pet-ear pet-ear-right"></div>
        <div class="pet-crest"></div>
        <div class="pet-antenna"></div>
        <div class="pet-arm pet-arm-left"></div>
        <div class="pet-arm pet-arm-right"></div>
        <div class="pet-hand pet-hand-left"></div>
        <div class="pet-hand pet-hand-right"></div>
        <div class="pet-neck"></div>
        <div class="pet-shoulders"></div>
        <div class="pet-body">${avatarMarkup}<div class="pet-chest"></div><div class="pet-core"></div><div class="pet-belt"></div></div>
        <div class="pet-head">
          <div class="pet-face">
            ${faceMarkup}
          </div>
        </div>
        <div class="pet-leg pet-leg-left"></div>
        <div class="pet-leg pet-leg-right"></div>
        <div class="pet-foot pet-foot-left"></div>
        <div class="pet-foot pet-foot-right"></div>
      </div>
      <div class="pet-bubble">
        <div class="pet-kicker">${escapeHtml(name)} AI companion</div>
        <div class="pet-status-row">
          <span class="pet-status-light"></span>
          <span class="pet-status-pill">${escapeHtml(status)}</span>
          ${updatedMarkup}
        </div>
        <div class="pet-message">${escapeHtml(message)}</div>
        <div class="pet-controls">
          <button class="pet-control pet-next" type="button" title="Next tip">tip</button>
          <button class="pet-control pet-home" type="button" title="Dock bottom right">dock</button>
        </div>
      </div>
    </div>
  `

  const shell = root.querySelector(".pet-shell")
  const stage = root.querySelector(".pet-stage")
  const nextButton = root.querySelector(".pet-next")
  const homeButton = root.querySelector(".pet-home")
  if (!shell || !stage) return

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value))
  if (saved && Number.isFinite(saved.left) && Number.isFinite(saved.top)) {
    const rect = shell.getBoundingClientRect()
    shell.classList.add("pet-manual")
    shell.style.left = `${clamp(saved.left, 8, window.innerWidth - rect.width - 8)}px`
    shell.style.top = `${clamp(saved.top, 8, window.innerHeight - rect.height - 8)}px`
    shell.style.right = "auto"
    shell.style.bottom = "auto"
  }

  let dragging = false
  let offsetX = 0
  let offsetY = 0
  let lastPosition = null

  const moveTo = (left, top) => {
    const rect = shell.getBoundingClientRect()
    const nextLeft = clamp(left, 8, window.innerWidth - rect.width - 8)
    const nextTop = clamp(top, 8, window.innerHeight - rect.height - 8)
    shell.classList.add("pet-manual")
    shell.style.left = `${nextLeft}px`
    shell.style.top = `${nextTop}px`
    shell.style.right = "auto"
    shell.style.bottom = "auto"
    lastPosition = { left: nextLeft, top: nextTop }
    try { localStorage.setItem(storageKey, JSON.stringify({ left: nextLeft, top: nextTop })) } catch (_) {}
  }

  const onPointerDown = (event) => {
    dragging = true
    const rect = shell.getBoundingClientRect()
    offsetX = event.clientX - rect.left
    offsetY = event.clientY - rect.top
    stage.setPointerCapture(event.pointerId)
    shell.classList.add("pet-manual")
    event.preventDefault()
  }
  const onPointerMove = (event) => {
    if (!dragging) return
    moveTo(event.clientX - offsetX, event.clientY - offsetY)
  }
  const onPointerUp = (event) => {
    if (!dragging) return
    dragging = false
    try { stage.releasePointerCapture(event.pointerId) } catch (_) {}
    if (setStateValue && lastPosition) setStateValue("position", lastPosition)
    if (setTriggerValue) setTriggerValue("moved", Date.now())
  }

  stage.addEventListener("pointerdown", onPointerDown)
  stage.addEventListener("pointermove", onPointerMove)
  stage.addEventListener("pointerup", onPointerUp)
  stage.addEventListener("pointercancel", onPointerUp)

  const rotateMessage = () => {
    const bubble = root.querySelector(".pet-message")
    if (!bubble) return
    tipIndex = (tipIndex + 1) % messages.length
    try { localStorage.setItem(tipStorageKey, String(tipIndex)) } catch (_) {}
    bubble.textContent = String(messages[tipIndex] || "")
    if (setStateValue) setStateValue("tip_index", tipIndex)
    if (setTriggerValue) setTriggerValue("next_tip", Date.now())
  }
  nextButton?.addEventListener("click", rotateMessage)
  homeButton?.addEventListener("click", () => {
    try { localStorage.removeItem(storageKey) } catch (_) {}
    shell.classList.remove("pet-manual")
    shell.style.left = ""
    shell.style.top = ""
    shell.style.right = "22px"
    shell.style.bottom = "24px"
    if (setStateValue) setStateValue("position", null)
    if (setTriggerValue) setTriggerValue("docked", Date.now())
  })

  return () => {
    stage.removeEventListener("pointerdown", onPointerDown)
    stage.removeEventListener("pointermove", onPointerMove)
    stage.removeEventListener("pointerup", onPointerUp)
    stage.removeEventListener("pointercancel", onPointerUp)
  }
}
"""
AI_COMPANION_COMPONENT = st.components.v2.component(
    "floating_ai_companion",
    html=AI_COMPANION_HTML,
    css=AI_COMPANION_CSS,
    js=AI_COMPANION_JS,
)
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
JOURNAL_FILE = DATA_DIR / "trade_journal.csv"
ORDERS_FILE = DATA_DIR / "paper_orders.csv"
COMPANION_STATUS_FILE = DATA_DIR / "companion_status.json"
YFINANCE_CACHE_DIR = DATA_DIR / "yfinance_cache"
LIVE_REFRESH_SECONDS = 30
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
FINNHUB_API_URL = "https://finnhub.io/api/v1/{endpoint}"
SP500_SOURCE_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
DEFAULT_MARKET_SCAN_BATCH = 80
SYMBOL_ALIASES = {
    "S&P500": "^GSPC",
    "S&P 500": "^GSPC",
    "S AND P 500": "^GSPC",
    "SANDP500": "^GSPC",
    "S P 500": "^GSPC",
    "SP 500": "^GSPC",
    "SP500": "^GSPC",
    "SNP500": "^GSPC",
    "STANDARD AND POORS 500": "^GSPC",
    "STANDARD & POORS 500": "^GSPC",
    "SPX": "^GSPC",
    "GSPC": "^GSPC",
    "NASDAQ": "^IXIC",
    "NASDAQ COMPOSITE": "^IXIC",
    "NASDAQCOMP": "^IXIC",
    "IXIC": "^IXIC",
    "NASDAQ 100": "^NDX",
    "NASDAQ100": "^NDX",
    "NDX": "^NDX",
    "DOW": "^DJI",
    "DOW 30": "^DJI",
    "DOW30": "^DJI",
    "DOW JONES": "^DJI",
    "DOW JONES INDUSTRIAL AVERAGE": "^DJI",
    "DJIA": "^DJI",
    "DJI": "^DJI",
    "RUSSELL": "^RUT",
    "RUSSELL 2000": "^RUT",
    "RUSSELL2000": "^RUT",
    "RUSSELL 2K": "^RUT",
    "RUSSELL2K": "^RUT",
    "RUT": "^RUT",
    "VOLATILITY INDEX": "^VIX",
    "VIX": "^VIX",
}
INDEX_PROFILES = {
    "^GSPC": {"company": "S&P 500 Index", "sector": "Broad market index", "float_m": 0.0, "catalyst": "Broad US large-cap market movement"},
    "^IXIC": {"company": "Nasdaq Composite Index", "sector": "Technology-heavy market index", "float_m": 0.0, "catalyst": "Broad Nasdaq market movement"},
    "^NDX": {"company": "Nasdaq 100 Index", "sector": "Large-cap technology-heavy index", "float_m": 0.0, "catalyst": "Broad Nasdaq 100 market movement"},
    "^DJI": {"company": "Dow Jones Industrial Average", "sector": "Blue-chip market index", "float_m": 0.0, "catalyst": "Broad Dow market movement"},
    "^RUT": {"company": "Russell 2000 Index", "sector": "Small-cap market index", "float_m": 0.0, "catalyst": "Broad small-cap market movement"},
    "^VIX": {"company": "CBOE Volatility Index", "sector": "Volatility index", "float_m": 0.0, "catalyst": "Market volatility movement"},
}
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
YFINANCE_CACHE_DIR.mkdir(exist_ok=True)

if yf is not None:
    try:
        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
    except Exception:
        pass

DEFAULT_RULES = {
    "min_price": 2.0,
    "max_price": 20.0,
    "min_gain_pct": 10.0,
    "max_float_m": 10.0,
    "min_rvol": 3.0,
}

CORE_MARKET_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AMD",
    "PLTR",
    "SMCI",
    "AVGO",
    "QQQ",
    "SPY",
    "IWM",
    "DIA",
]

SP500_SAMPLE_TICKERS = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "AVGO",
    "TSLA",
    "BRK-B",
    "JPM",
    "WMT",
    "LLY",
    "V",
    "MA",
    "XOM",
    "UNH",
    "COST",
    "NFLX",
    "HD",
    "PG",
    "ORCL",
    "JNJ",
    "BAC",
    "ABBV",
    "KO",
    "AMD",
    "CRM",
    "PLTR",
    "CSCO",
    "MCD",
    "IBM",
    "GE",
    "NOW",
    "WFC",
    "PM",
    "ABT",
    "DIS",
    "LIN",
    "MS",
]

GLOBAL_MARKET_WATCH = {
    "United States": ["SPY", "QQQ", "IWM", "DIA", "NVDA", "TSLA", "AMD"],
    "Europe": ["EWG", "EWU", "FEZ", "VGK", "ASML", "SAP"],
    "Asia": ["EWJ", "MCHI", "FXI", "INDA", "EWT", "TSM"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
}

MARKET_CLOCKS = [
    {
        "Market": "New York",
        "Timezone": "America/New_York",
        "Typical session": "9:30 AM - 4:00 PM",
        "Open": "09:30",
        "Close": "16:00",
        "Premarket": "04:00",
        "After hours": "20:00",
        "Beginner read": "Main US stock session.",
    },
    {
        "Market": "Phoenix",
        "Timezone": "America/Phoenix",
        "Typical session": "6:30 AM - 1:00 PM",
        "Open": "06:30",
        "Close": "13:00",
        "Premarket": "01:00",
        "After hours": "17:00",
        "Beginner read": "Same US session shown in Arizona time.",
    },
    {
        "Market": "London",
        "Timezone": "Europe/London",
        "Typical session": "8:00 AM - 4:30 PM",
        "Open": "08:00",
        "Close": "16:30",
        "Beginner read": "European cash market reference.",
    },
    {
        "Market": "Frankfurt",
        "Timezone": "Europe/Berlin",
        "Typical session": "9:00 AM - 5:30 PM",
        "Open": "09:00",
        "Close": "17:30",
        "Beginner read": "German cash market reference.",
    },
    {
        "Market": "Tokyo",
        "Timezone": "Asia/Tokyo",
        "Typical session": "9:00 AM - 3:00 PM",
        "Open": "09:00",
        "Close": "15:00",
        "Beginner read": "Japan cash market reference.",
    },
    {
        "Market": "Hong Kong",
        "Timezone": "Asia/Hong_Kong",
        "Typical session": "9:30 AM - 4:00 PM",
        "Open": "09:30",
        "Close": "16:00",
        "Beginner read": "Hong Kong cash market reference.",
    },
    {
        "Market": "Sydney",
        "Timezone": "Australia/Sydney",
        "Typical session": "10:00 AM - 4:00 PM",
        "Open": "10:00",
        "Close": "16:00",
        "Beginner read": "Australia cash market reference.",
    },
]

DEMO_PROFILES: list[dict[str, Any]] = [
    {
        "ticker": "KULR",
        "company": "KULR Technology",
        "sector": "Battery systems",
        "price": 3.12,
        "daily_gain_pct": 21.4,
        "float_m": 4.7,
        "rvol": 9.6,
        "volume": 38_400_000,
        "catalyst": "Momentum news and unusual volume",
    },
    {
        "ticker": "BBAI",
        "company": "BigBear.ai",
        "sector": "AI analytics",
        "price": 4.92,
        "daily_gain_pct": 18.3,
        "float_m": 9.7,
        "rvol": 7.9,
        "volume": 52_700_000,
        "catalyst": "AI sector strength and gapper scan hit",
    },
    {
        "ticker": "LUNR",
        "company": "Intuitive Machines",
        "sector": "Space",
        "price": 10.18,
        "daily_gain_pct": 16.6,
        "float_m": 9.2,
        "rvol": 5.9,
        "volume": 44_900_000,
        "catalyst": "Contract speculation and heavy premarket interest",
    },
    {
        "ticker": "SERV",
        "company": "Serve Robotics",
        "sector": "Robotics",
        "price": 13.38,
        "daily_gain_pct": 15.2,
        "float_m": 5.4,
        "rvol": 7.2,
        "volume": 25_100_000,
        "catalyst": "Small-float robotics momentum",
    },
    {
        "ticker": "SOUN",
        "company": "SoundHound AI",
        "sector": "AI voice",
        "price": 7.84,
        "daily_gain_pct": 14.0,
        "float_m": 8.8,
        "rvol": 6.6,
        "volume": 68_400_000,
        "catalyst": "AI name with high retail volume",
    },
    {
        "ticker": "QBTS",
        "company": "D-Wave Quantum",
        "sector": "Quantum",
        "price": 8.36,
        "daily_gain_pct": 13.1,
        "float_m": 6.5,
        "rvol": 4.8,
        "volume": 31_800_000,
        "catalyst": "Quantum momentum and volume expansion",
    },
    {
        "ticker": "IONQ",
        "company": "IonQ",
        "sector": "Quantum",
        "price": 16.28,
        "daily_gain_pct": 12.4,
        "float_m": 9.9,
        "rvol": 3.8,
        "volume": 29_700_000,
        "catalyst": "Sector sympathy move",
    },
    {
        "ticker": "RGTI",
        "company": "Rigetti Computing",
        "sector": "Quantum",
        "price": 12.45,
        "daily_gain_pct": 11.8,
        "float_m": 7.4,
        "rvol": 5.1,
        "volume": 36_200_000,
        "catalyst": "Quantum breakout watch",
    },
    {
        "ticker": "ACHR",
        "company": "Archer Aviation",
        "sector": "Aviation",
        "price": 6.74,
        "daily_gain_pct": 10.9,
        "float_m": 8.1,
        "rvol": 4.2,
        "volume": 41_600_000,
        "catalyst": "EV aviation momentum",
    },
    {
        "ticker": "RKLB",
        "company": "Rocket Lab",
        "sector": "Space",
        "price": 9.61,
        "daily_gain_pct": 10.7,
        "float_m": 8.6,
        "rvol": 3.5,
        "volume": 22_400_000,
        "catalyst": "Space sector follow-through",
    },
]

PROFILE_BY_TICKER = {row["ticker"]: row for row in DEMO_PROFILES}


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        number = float(value)
        if not math.isfinite(number):
            return default
        return number
    except Exception:
        return default


def first_number(*values: Any, default: float | None = None) -> float | None:
    for value in values:
        number = safe_float(value)
        if number is not None:
            return number
    return default


def timestamp_label(value: Any) -> str:
    seconds = safe_float(value)
    if seconds is None:
        return "n/a"
    try:
        return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return "n/a"


def money(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"${float(value):,.2f}"


def pct(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"{float(value):.1f}%"


def compact_number(value: float | int | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def markdown_text(value: Any) -> str:
    return str(value).replace("$", "\\$")


def clean_html_markup(markup: Any) -> str:
    return dedent(str(markup or "")).strip()


def render_html(markup: Any, target: Any | None = None) -> None:
    renderer = target or st
    cleaned = clean_html_markup(markup)
    if hasattr(renderer, "html"):
        renderer.html(cleaned)
    else:
        renderer.markdown(cleaned, unsafe_allow_html=True)


def playbook_fit_label(stats: dict[str, Any], score: float | int | None = None) -> str:
    price = safe_float(stats.get("Price"), 0) or 0
    gain = safe_float(stats.get("Daily gain %"), 0) or 0
    float_m = safe_float(stats.get("Float M"), 999) or 999
    rvol = safe_float(stats.get("RVOL"), 0) or 0
    score_value = safe_float(score, safe_float(stats.get("AI score"), 0)) or 0

    price_ok = DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]
    gain_ok = gain >= DEFAULT_RULES["min_gain_pct"]
    float_ok = float_m <= DEFAULT_RULES["max_float_m"]
    rvol_ok = rvol >= DEFAULT_RULES["min_rvol"]
    fit_count = sum([price_ok, gain_ok, float_ok, rvol_ok])

    if fit_count == 4 and score_value >= 74:
        return "Playbook fit"
    if price_ok and rvol_ok and fit_count >= 3:
        return "Developing setup"
    if not price_ok or not float_ok:
        return "Market context"
    if fit_count <= 1:
        return "Study only"
    return "Wait for confirmation"


def playbook_fit_color(label: str) -> str:
    if label == "Playbook fit":
        return "green"
    if label == "Developing setup":
        return "blue"
    if label == "Wait for confirmation":
        return "orange"
    if label == "Market context":
        return "violet"
    return "gray"


def data_quality_badge(source: Any) -> tuple[str, str]:
    source_text = str(source or "Unknown")
    lowered = source_text.lower()
    if "alpaca" in lowered:
        return "Alpaca IEX", "green"
    if "finnhub" in lowered:
        return "Finnhub quote", "green"
    if "yahoo finance api" in lowered:
        return "Yahoo candles", "blue"
    if "yahoo finance" in lowered:
        return "Yahoo quote", "blue"
    if "learning" in lowered:
        return "Learning fallback", "orange"
    return source_text[:22], "gray"


CATALYST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Earnings": ("earnings", "eps", "revenue", "guidance", "quarter", "q1", "q2", "q3", "q4"),
    "Contract": ("contract", "award", "deal", "partnership", "customer", "order", "launch"),
    "FDA/regulatory": ("fda", "approval", "clinical", "trial", "phase", "patent", "regulatory"),
    "Analyst": ("upgrade", "downgrade", "price target", "initiates", "rating"),
    "Sector": ("ai", "quantum", "crypto", "semiconductor", "space", "robotics", "ev"),
    "M&A": ("acquisition", "merger", "buyout", "takeover"),
}

RISK_NEWS_KEYWORDS: tuple[str, ...] = (
    "offering",
    "dilution",
    "bankruptcy",
    "investigation",
    "sec",
    "lawsuit",
    "halt",
    "delisting",
    "reverse split",
)


def catalyst_tags(headline: str, summary: str = "") -> list[str]:
    text = f"{headline} {summary}".lower()
    tags = [label for label, words in CATALYST_KEYWORDS.items() if any(word in text for word in words)]
    if any(word in text for word in RISK_NEWS_KEYWORDS):
        tags.insert(0, "Risk headline")
    return list(dict.fromkeys(tags))[:4]


def catalyst_score(news: list[dict[str, Any]]) -> tuple[str, str]:
    if not news:
        return "No news", "gray"

    score = 0
    for item in news[:5]:
        tags = catalyst_tags(str(item.get("headline") or ""), str(item.get("summary") or ""))
        for tag in tags:
            if tag in {"Contract", "FDA/regulatory", "Earnings"}:
                score += 2
            elif tag in {"Analyst", "Sector", "M&A"}:
                score += 1
            elif tag == "Risk headline":
                score -= 3

    if score >= 4:
        return "Strong catalyst", "green"
    if score >= 2:
        return "Catalyst watch", "blue"
    if score < 0:
        return "News risk", "red"
    return "Unclear catalyst", "gray"


NEWS_IMPORTANCE: dict[str, int] = {
    "Risk headline": 7,
    "FDA/regulatory": 6,
    "M&A": 6,
    "Earnings": 5,
    "Contract": 5,
    "Analyst": 3,
    "Sector": 2,
}


def news_age_hours(item: dict[str, Any]) -> float:
    published = safe_float(item.get("datetime"))
    if published is None:
        return 999.0
    if published > 10_000_000_000:
        published = published / 1000
    try:
        return max((datetime.now() - datetime.fromtimestamp(float(published))).total_seconds() / 3600, 0)
    except Exception:
        return 999.0


def news_impact_score(item: dict[str, Any]) -> int:
    headline = str(item.get("headline") or "")
    summary = str(item.get("summary") or "")
    text = f"{headline} {summary}".lower()
    tags = catalyst_tags(headline, summary)
    score = sum(NEWS_IMPORTANCE.get(tag, 1) for tag in tags)
    if any(word in text for word in ("announces", "wins", "launches", "surges", "approval", "raises", "beats")):
        score += 2
    if any(word in text for word in ("offering", "halt", "investigation", "bankruptcy", "delisting")):
        score += 3

    age = news_age_hours(item)
    if age <= 2:
        score += 4
    elif age <= 6:
        score += 3
    elif age <= 24:
        score += 2
    elif age <= 72:
        score += 1
    return score


def news_related_symbol(item: dict[str, Any]) -> str:
    for field in ("_symbol", "symbol", "related"):
        value = str(item.get(field) or "").strip()
        if not value:
            continue
        parts = [part for chunk in value.replace(";", ",").split(",") for part in chunk.split() if part]
        if parts:
            return normalize_user_symbol(parts[0])
    return "Market"


@st.cache_data(ttl=300, max_entries=30, show_spinner=False)
def biggest_stock_news(symbols: tuple[str, ...], api_marker: str, limit: int = 8) -> list[dict[str, Any]]:
    if api_marker == "no-key":
        return []

    cleaned_symbols = tuple(unique_symbols([normalize_user_symbol(symbol) for symbol in symbols if normalize_user_symbol(symbol)]))
    items: list[dict[str, Any]] = []

    for item in finnhub_market_news("general", limit=20):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["_symbol"] = news_related_symbol(row)
        row["_feed"] = "Market"
        row["_score"] = news_impact_score(row)
        items.append(row)

    for symbol in cleaned_symbols[:12]:
        for item in finnhub_company_news(symbol, days=3, limit=3):
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row["_symbol"] = symbol
            row["_feed"] = "Stock"
            row["_score"] = news_impact_score(row)
            items.append(row)

    unique_items: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("url") or item.get("headline") or item.get("id") or "")
        if not key:
            continue
        if key not in unique_items or int(item.get("_score", 0)) > int(unique_items[key].get("_score", 0)):
            unique_items[key] = item

    return sorted(
        unique_items.values(),
        key=lambda item: (int(item.get("_score", 0)), safe_float(item.get("datetime"), 0) or 0),
        reverse=True,
    )[:limit]


def render_big_news_rail(symbols: tuple[str, ...]) -> None:
    with st.container(border=True):
        st.markdown("**Biggest news dropped**")
        st.caption("Ranks fresh headlines by catalyst strength, risk, and recency.")
        if not finnhub_enabled():
            st.info("Add your free Finnhub key to turn on ranked stock news.", icon=":material/key:")
            return

        news = biggest_stock_news(symbols, finnhub_key_marker(), limit=8)
        if not news:
            st.caption("No high-impact stock news returned yet.")
            return

        for item in news:
            headline = str(item.get("headline") or "Untitled news")
            url = str(item.get("url") or "")
            source = str(item.get("source") or "News")
            symbol = news_related_symbol(item)
            tags = catalyst_tags(headline, str(item.get("summary") or ""))
            score = int(item.get("_score", 0))
            with st.container(border=True):
                with st.container(horizontal=True):
                    st.badge(symbol, icon=":material/finance_chip:", color="blue")
                    st.badge(f"Impact {score}", icon=":material/bolt:", color="red" if "Risk headline" in tags else "green" if score >= 8 else "orange")
                if url:
                    st.markdown(f"**[{headline}]({url})**")
                else:
                    st.markdown(f"**{headline}**")
                if tags:
                    with st.container(horizontal=True):
                        for tag in tags[:3]:
                            st.badge(tag, color="red" if tag == "Risk headline" else "blue")
                st.caption(f"{source} | {timestamp_label(item.get('datetime'))}")


def setup_check_items(analysis: dict[str, Any]) -> list[tuple[str, bool, str]]:
    price = safe_float(analysis.get("Price"))
    gain = safe_float(analysis.get("Daily gain %"), 0) or 0
    float_m = safe_float(analysis.get("Float M"))
    rvol = safe_float(analysis.get("RVOL"), 0) or 0
    ema9 = safe_float(analysis.get("EMA 9"))
    ema20 = safe_float(analysis.get("EMA 20"))
    risk_reward = safe_float(analysis.get("Risk/reward"), 0) or 0
    status = live_status(analysis)

    price_ok = price is not None and DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]
    float_ok = float_m is not None and float_m <= DEFAULT_RULES["max_float_m"]
    trend_ok = price is not None and ema9 is not None and ema20 is not None and price > ema9 > ema20
    action_ok = status in {"Breakout trigger", "In buy zone", "Near buy zone"}
    return [
        ("Price", price_ok, money(price)),
        ("Gap", gain >= DEFAULT_RULES["min_gain_pct"], pct(gain)),
        ("Float", float_ok, f"{float_m:.1f}M" if float_m is not None else "n/a"),
        ("RVOL", rvol >= DEFAULT_RULES["min_rvol"], f"{rvol:.1f}x"),
        ("Trend", trend_ok, "above EMAs" if trend_ok else "needs hold"),
        ("Risk", risk_reward >= 1.4, f"{risk_reward:.2f}R"),
        ("Action", action_ok, status),
    ]


def setup_completion(analysis: dict[str, Any]) -> tuple[int, int]:
    checks = setup_check_items(analysis)
    return sum(1 for _, passed, _ in checks if passed), len(checks)


def normalize_user_symbol(symbol: Any) -> str:
    raw = str(symbol or "").strip().upper().replace("$", "")
    raw = " ".join(raw.split())
    if not raw:
        return ""
    if raw in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[raw]

    compact = raw.replace(" ", "").replace(".", "")
    if compact in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[compact]

    cleaned = raw.replace(".", "-").replace("/", "-")
    return SYMBOL_ALIASES.get(cleaned, cleaned)


def clean_market_symbol(symbol: Any) -> str:
    clean = normalize_user_symbol(symbol)
    if not clean or clean in {"N/A", "NAN", "NONE"}:
        return ""
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-^")
    if any(char not in allowed for char in clean):
        return ""
    excluded_suffixes = ("-W", "-WS", "-WT", "-U", "-R", "-RT", "-PR", "-P")
    if clean.endswith(excluded_suffixes):
        return ""
    return clean


def tradeable_security_name(name: Any, include_etfs: bool) -> bool:
    text = str(name or "").lower()
    if not text:
        return True
    normalized = text
    for char in ",.;:/()[]{}-":
        normalized = normalized.replace(char, " ")
    words = set(normalized.split())
    blocked_words = {
        "warrant",
        "warrants",
        "right",
        "rights",
        "unit",
        "units",
        "preferred",
        "preference",
        "note",
        "notes",
        "bond",
        "bonds",
        "debenture",
        "debentures",
        "redeemable",
    }
    blocked_phrases = ("preferred stock", "depositary share", "depositary shares")
    if words.intersection(blocked_words) or any(phrase in text for phrase in blocked_phrases):
        return False
    if not include_etfs and any(word in text for word in ("etf", "fund", "trust", "etn")):
        return False
    return True


def unique_symbols(symbols: list[str]) -> list[str]:
    return [symbol for symbol in dict.fromkeys(symbols) if symbol]


def get_secret(name: str) -> str:
    value = ""
    try:
        value = str(st.secrets.get(name, "") or "")
    except Exception:
        value = ""
    clean = (value or os.environ.get(name, "")).strip()
    if clean.lower() in {
        "paste-your-finnhub-key-here",
        "paste-your-alpaca-key-id-here",
        "paste-your-alpaca-secret-key-here",
        "your_key_here",
        "your-key-here",
        "your_secret_here",
        "your-secret-here",
    }:
        return ""
    return clean


def finnhub_api_key() -> str:
    return get_secret("FINNHUB_API_KEY") or get_secret("finnhub_api_key")


def finnhub_enabled() -> bool:
    return bool(finnhub_api_key())


def alpaca_api_key() -> str:
    return get_secret("ALPACA_API_KEY") or get_secret("ALPACA_API_KEY_ID") or get_secret("APCA_API_KEY_ID")


def alpaca_secret_key() -> str:
    return get_secret("ALPACA_SECRET_KEY") or get_secret("ALPACA_API_SECRET") or get_secret("APCA_API_SECRET_KEY")


def alpaca_enabled() -> bool:
    return bool(alpaca_api_key() and alpaca_secret_key() and StockHistoricalDataClient is not None)


def alpaca_key_marker() -> str:
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        return "no-alpaca-key"
    return f"alpaca-{len(key)}-{key[-4:]}-{len(secret)}"


@st.cache_resource(show_spinner=False)
def alpaca_data_client(marker: str) -> Any | None:
    if marker == "no-alpaca-key" or StockHistoricalDataClient is None:
        return None
    key = alpaca_api_key()
    secret = alpaca_secret_key()
    if not key or not secret:
        return None
    return StockHistoricalDataClient(api_key=key, secret_key=secret)


def finnhub_get(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    key = finnhub_api_key()
    if not key:
        return None
    clean_endpoint = endpoint.strip("/")
    response = requests.get(
        FINNHUB_API_URL.format(endpoint=clean_endpoint),
        params={**(params or {}), "token": key},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def finnhub_key_marker() -> str:
    key = finnhub_api_key()
    return f"key-{len(key)}-{key[-4:]}" if key else "no-key"


@st.cache_data(ttl=86400, max_entries=4, show_spinner=False)
def finnhub_us_symbols(api_marker: str, include_etfs: bool = True) -> list[str]:
    if api_marker == "no-key":
        return []
    try:
        payload = finnhub_get("stock/symbol", {"exchange": "US"})
        if not isinstance(payload, list):
            return []
        symbols: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            symbol = clean_market_symbol(item.get("symbol"))
            if not symbol:
                continue
            security_type = str(item.get("type") or "").lower()
            description = item.get("description")
            if not include_etfs and "etf" in security_type:
                continue
            if tradeable_security_name(description, include_etfs):
                symbols.append(symbol)
        return sorted(unique_symbols(symbols))
    except Exception:
        return []


def parse_symbol_directory(text: str, symbol_column: str, include_etfs: bool = True) -> list[str]:
    lines = [line for line in text.splitlines() if line and not line.startswith("File Creation")]
    if not lines:
        return []
    headers = lines[0].split("|")
    symbols: list[str] = []
    for line in lines[1:]:
        values = line.split("|")
        if len(values) != len(headers):
            continue
        row = dict(zip(headers, values))
        if str(row.get("Test Issue", "")).upper() == "Y":
            continue
        if not include_etfs and str(row.get("ETF", "")).upper() == "Y":
            continue
        if not tradeable_security_name(row.get("Security Name"), include_etfs):
            continue
        symbol = clean_market_symbol(row.get(symbol_column))
        if symbol:
            symbols.append(symbol)
    return symbols


@st.cache_data(ttl=86400, max_entries=4, show_spinner=False)
def nasdaqtrader_symbols(include_etfs: bool = True) -> list[str]:
    symbols: list[str] = []
    try:
        response = requests.get(NASDAQ_LISTED_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
        response.raise_for_status()
        symbols.extend(parse_symbol_directory(response.text, "Symbol", include_etfs=include_etfs))
    except Exception:
        pass
    try:
        response = requests.get(OTHER_LISTED_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
        response.raise_for_status()
        symbols.extend(parse_symbol_directory(response.text, "ACT Symbol", include_etfs=include_etfs))
    except Exception:
        pass
    return sorted(unique_symbols(symbols))


@st.cache_data(ttl=86400, max_entries=6, show_spinner=False)
def full_us_market_universe(include_etfs: bool = True, api_marker: str = "no-key") -> tuple[list[str], str]:
    symbols = finnhub_us_symbols(api_marker, include_etfs=include_etfs)
    if symbols:
        return symbols, "Finnhub US symbol list"
    symbols = nasdaqtrader_symbols(include_etfs=include_etfs)
    if symbols:
        return symbols, "Nasdaq Trader symbol directory"
    return [], "Full universe unavailable"


def ticker_seed(ticker: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(ticker.upper())) % (2**32)


def profile_for(ticker: str) -> dict[str, Any]:
    ticker = normalize_user_symbol(ticker)
    if ticker in PROFILE_BY_TICKER:
        return dict(PROFILE_BY_TICKER[ticker])
    if ticker in INDEX_PROFILES:
        profile = INDEX_PROFILES[ticker]
        return {
            "ticker": ticker,
            "company": profile["company"],
            "sector": profile["sector"],
            "price": 5000.0,
            "prev_close": 4980.0,
            "daily_gain_pct": 0.4,
            "volume": 1_000_000,
            "avg_volume": 1_000_000,
            "rvol": 1.0,
            "float_m": 999999.0,
            "catalyst": profile["catalyst"],
        }

    seed = ticker_seed(ticker)
    rng = np.random.default_rng(seed)
    price = round(float(rng.uniform(2.25, 18.75)), 2)
    gain = round(float(rng.uniform(7.0, 18.0)), 1)
    rvol = round(float(rng.uniform(2.0, 8.5)), 1)
    float_m = round(float(rng.uniform(4.0, 18.0)), 1)
    return {
        "ticker": ticker,
        "company": f"{ticker} learning profile",
        "sector": "Custom watch",
        "price": price,
        "daily_gain_pct": gain,
        "float_m": float_m,
        "rvol": rvol,
        "volume": int(rng.uniform(4_000_000, 55_000_000)),
        "catalyst": "Custom stock. Verify live float, news, and volume.",
    }


def period_days(period: str) -> int:
    return {
        "1d": 2,
        "5d": 7,
        "1mo": 24,
        "3mo": 66,
        "6mo": 132,
        "1y": 252,
        "2y": 504,
    }.get(period, 132)


def normalize_history(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    keep = [column for column in ["Open", "High", "Low", "Close", "Volume"] if column in df.columns]
    df = df[keep].dropna()
    if set(["Open", "High", "Low", "Close", "Volume"]) - set(df.columns):
        return pd.DataFrame()
    index = pd.to_datetime(df.index)
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    df.index = index
    return df.sort_index()


@st.cache_data(ttl=600, max_entries=200, show_spinner=False)
def learning_history(ticker: str, days: int) -> pd.DataFrame:
    profile = profile_for(ticker)
    rng = np.random.default_rng(ticker_seed(ticker))

    price = float(profile["price"])
    final_gain = float(profile["daily_gain_pct"]) / 100
    prev_close = price / (1 + final_gain)
    avg_volume = max(float(profile["volume"]) / max(float(profile["rvol"]), 1.1), 250_000)

    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=max(days, 32))
    closes = [prev_close * float(rng.uniform(0.58, 0.78))]
    for _ in range(1, len(dates) - 2):
        drift = 0.0025 + rng.normal(0, 0.018)
        closes.append(max(0.5, closes[-1] * (1 + drift)))

    closes = np.array(closes, dtype=float)
    event_start = 28 + int(ticker_seed(ticker) % 7)
    for index in range(event_start, len(closes) - 8, 31):
        jump = 1 + float(rng.uniform(0.08, 0.16))
        closes[index] = closes[index - 1] * jump
        for follow_index in range(index + 1, min(index + 5, len(closes))):
            closes[follow_index] = max(0.5, closes[follow_index - 1] * (1 + rng.normal(0.01, 0.03)))

    closes *= prev_close / max(closes[-1], 0.01)
    closes = np.concatenate([closes, [prev_close, price]])

    opens = np.empty_like(closes)
    opens[0] = closes[0] * (1 + rng.normal(0, 0.01))
    opens[1:] = closes[:-1] * (1 + rng.normal(0, 0.015, len(closes) - 1))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0.025, 0.012, len(closes))))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0.022, 0.01, len(closes))))
    volumes = rng.normal(avg_volume, avg_volume * 0.16, len(closes)).clip(avg_volume * 0.35, None)

    for index in range(event_start, len(closes) - 8, 31):
        volumes[index] = avg_volume * float(rng.uniform(3.4, 6.8))

    opens[-1] = prev_close * (1 + final_gain * 0.55)
    highs[-1] = max(opens[-1], price) * 1.045
    lows[-1] = min(opens[-1], price) * 0.955
    volumes[-1] = float(profile["volume"])

    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes.astype(int),
        },
        index=dates,
    )


def yahoo_chart_api_history(ticker: str, period: str, interval: str, prepost: bool = True) -> pd.DataFrame:
    ticker = normalize_user_symbol(ticker)
    response = requests.get(
        YAHOO_CHART_URL.format(ticker=url_quote(ticker, safe="")),
        params={
            "range": period,
            "interval": interval,
            "includePrePost": str(bool(prepost)).lower(),
            "events": "div,splits",
        },
        headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        return pd.DataFrame()

    result = results[0]
    timestamps = result.get("timestamp") or []
    quotes = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    if not timestamps or not quotes:
        return pd.DataFrame()

    df = pd.DataFrame(
        {
            "Open": quotes.get("open"),
            "High": quotes.get("high"),
            "Low": quotes.get("low"),
            "Close": quotes.get("close"),
            "Volume": quotes.get("volume"),
        },
        index=pd.to_datetime(timestamps, unit="s", utc=True),
    )
    return normalize_history(df)


def alpaca_timeframe(interval: str) -> Any | None:
    if TimeFrame is None or TimeFrameUnit is None:
        return None
    interval = str(interval or "1d").lower()
    if interval == "1d":
        return TimeFrame.Day
    if interval == "60m":
        return TimeFrame.Hour
    if interval.endswith("m"):
        minutes = safe_float(interval[:-1])
        if minutes is not None and 1 <= int(minutes) <= 59:
            return TimeFrame(int(minutes), TimeFrameUnit.Minute)
    return None


def alpaca_lookback_window(period: str, interval: str) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    days = period_days(period)
    if str(interval).endswith("m"):
        days = max(days, 2)
    start = end - timedelta(days=days)
    return start, end


@st.cache_data(ttl=20, max_entries=220, show_spinner=False)
def alpaca_iex_history(ticker: str, period: str, interval: str, api_marker: str) -> pd.DataFrame:
    ticker = normalize_user_symbol(ticker)
    if not ticker or ticker.startswith("^") or api_marker == "no-alpaca-key":
        return pd.DataFrame()
    if StockBarsRequest is None or DataFeed is None:
        return pd.DataFrame()
    timeframe = alpaca_timeframe(interval)
    if timeframe is None:
        return pd.DataFrame()
    client = alpaca_data_client(api_marker)
    if client is None:
        return pd.DataFrame()
    start, end = alpaca_lookback_window(period, interval)
    request = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=timeframe,
        start=start,
        end=end,
        feed=DataFeed.IEX,
        limit=10_000,
    )
    bars = client.get_stock_bars(request)
    raw = bars.dict() if hasattr(bars, "dict") else {}
    rows = raw.get(ticker) or raw.get(ticker.upper()) or []
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(
        [
            {
                "Open": row.get("open"),
                "High": row.get("high"),
                "Low": row.get("low"),
                "Close": row.get("close"),
                "Volume": row.get("volume"),
                "Time": row.get("timestamp"),
            }
            for row in rows
        ]
    ).dropna(subset=["Open", "High", "Low", "Close", "Volume", "Time"])
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.pop("Time"), utc=True)
    return normalize_history(df)


@st.cache_data(ttl=20, max_entries=250, show_spinner=False)
def load_history(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    prefer_live: bool = False,
    prepost: bool = True,
) -> tuple[pd.DataFrame, str]:
    ticker = normalize_user_symbol(ticker)
    if prefer_live:
        if alpaca_enabled():
            try:
                df = alpaca_iex_history(ticker, period=period, interval=interval, api_marker=alpaca_key_marker())
                if not df.empty and len(df) >= 5:
                    return df, f"Alpaca IEX {interval}"
                print(f"[live-history] Alpaca IEX returned no usable bars for {ticker} {period}/{interval}", flush=True)
            except Exception as exc:
                print(f"[live-history] Alpaca IEX failed for {ticker} {period}/{interval}: {exc}", flush=True)

        try:
            df = yahoo_chart_api_history(ticker, period=period, interval=interval, prepost=prepost)
            if not df.empty and len(df) >= 5:
                return df, f"Yahoo Finance API {interval}"
            print(f"[live-history] Yahoo chart API returned no usable bars for {ticker} {period}/{interval}", flush=True)
        except Exception as exc:
            print(f"[live-history] Yahoo chart API failed for {ticker} {period}/{interval}: {exc}", flush=True)

        if yf is not None:
            try:
                yf.set_tz_cache_location(str(DATA_DIR / "yfinance_cache"))
                raw = yf.Ticker(ticker).history(
                    period=period,
                    interval=interval,
                    auto_adjust=False,
                    prepost=prepost,
                    timeout=10,
                )
                df = normalize_history(raw)
                if not df.empty and len(df) >= 5:
                    return df, f"Yahoo Finance {interval}"
                print(f"[live-history] yfinance returned no usable bars for {ticker} {period}/{interval}", flush=True)
            except Exception as exc:
                print(f"[live-history] yfinance failed for {ticker} {period}/{interval}: {exc}", flush=True)

    return learning_history(ticker, period_days(period)), "Learning data"


def quote_to_stats(quote: dict[str, Any]) -> dict[str, Any] | None:
    ticker = str(quote.get("symbol") or "").strip().upper()
    if not ticker:
        return None

    price = first_number(
        quote.get("regularMarketPrice"),
        quote.get("postMarketPrice"),
        quote.get("preMarketPrice"),
        quote.get("intradayprice"),
    )
    previous_close = first_number(quote.get("regularMarketPreviousClose"), quote.get("previousClose"))
    gain_pct = first_number(quote.get("regularMarketChangePercent"), quote.get("percentchange"))
    volume = first_number(quote.get("regularMarketVolume"), quote.get("dayvolume"), quote.get("volume"), default=0)
    average_volume = first_number(
        quote.get("averageDailyVolume10Day"),
        quote.get("averageDailyVolume3Month"),
        quote.get("avgdailyvol3m"),
        default=0,
    )
    rvol = (volume / average_volume) if volume and average_volume else 0.0
    float_shares = first_number(quote.get("floatShares"))
    shares_outstanding = first_number(quote.get("sharesOutstanding"), quote.get("impliedSharesOutstanding"))
    share_count = float_shares if float_shares else shares_outstanding

    if price is None:
        return None

    profile = profile_for(ticker)
    return {
        "Ticker": ticker,
        "Company": quote.get("shortName") or quote.get("longName") or quote.get("displayName") or profile["company"],
        "Sector": quote.get("sector") or profile["sector"],
        "Price": price,
        "Previous close": previous_close or price,
        "Daily gain %": gain_pct if gain_pct is not None else 0.0,
        "Volume": volume or 0.0,
        "Average volume": average_volume or 0.0,
        "RVOL": rvol,
        "Float M": (share_count / 1_000_000) if share_count else float(profile["float_m"]),
        "Catalyst": quote.get("quoteSourceName") or "Yahoo Finance live quote",
        "Data source": f"Yahoo Finance ({quote.get('quoteSourceName', 'quote')})",
        "Float source": "Yahoo floatShares" if float_shares else "Yahoo shares outstanding proxy",
        "Market state": quote.get("marketState", "n/a"),
        "Quote time": timestamp_label(quote.get("regularMarketTime") or quote.get("postMarketTime") or quote.get("preMarketTime")),
        "Exchange": quote.get("fullExchangeName") or quote.get("exchange") or "n/a",
    }


def finnhub_quote_to_stats(ticker: str, quote: dict[str, Any]) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    price = safe_float(quote.get("c"))
    prev = safe_float(quote.get("pc"))
    if price is None:
        return None

    profile = profile_for(ticker)
    gain_pct = safe_float(quote.get("dp"))
    if gain_pct is None and prev:
        gain_pct = ((price - prev) / prev) * 100
    volume = safe_float(quote.get("v"), profile["volume"]) or profile["volume"]
    avg_volume = max(float(profile["volume"]) / max(float(profile["rvol"]), 1.1), 1)
    return {
        "Ticker": ticker,
        "Company": profile["company"],
        "Sector": profile["sector"],
        "Price": price,
        "Previous close": prev or price,
        "Daily gain %": gain_pct or 0.0,
        "Volume": volume,
        "Average volume": avg_volume,
        "RVOL": volume / avg_volume,
        "Float M": float(profile["float_m"]),
        "Catalyst": "Finnhub live quote",
        "Data source": "Finnhub quote",
        "Float source": "Profile estimate",
        "Market state": "n/a",
        "Quote time": timestamp_label(quote.get("t")),
        "Exchange": "US",
    }


@st.cache_data(ttl=20, max_entries=150, show_spinner=False)
def finnhub_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    if not ticker:
        return None
    try:
        quote = finnhub_get("quote", {"symbol": ticker})
        if not isinstance(quote, dict):
            return None
        return finnhub_quote_to_stats(ticker, quote)
    except Exception:
        return None


@st.cache_data(ttl=300, max_entries=300, show_spinner=False)
def finnhub_company_news(ticker: str, days: int = 3, limit: int = 5) -> list[dict[str, Any]]:
    ticker = normalize_user_symbol(ticker)
    if not ticker:
        return []
    end = date.today()
    start = end - timedelta(days=days)
    try:
        payload = finnhub_get(
            "company-news",
            {"symbol": ticker, "from": start.isoformat(), "to": end.isoformat()},
        )
        if not isinstance(payload, list):
            return []
        return sorted(payload, key=lambda item: item.get("datetime", 0), reverse=True)[:limit]
    except Exception:
        return []


@st.cache_data(ttl=300, max_entries=50, show_spinner=False)
def finnhub_market_news(category: str = "general", limit: int = 8) -> list[dict[str, Any]]:
    try:
        payload = finnhub_get("news", {"category": category})
        if not isinstance(payload, list):
            return []
        return sorted(payload, key=lambda item: item.get("datetime", 0), reverse=True)[:limit]
    except Exception:
        return []


def render_news_items(news: list[dict[str, Any]], empty_message: str = "No Finnhub news returned yet.") -> None:
    if not finnhub_enabled():
        st.info("Add your free Finnhub key to turn on live news.", icon=":material/key:")
        return
    if not news:
        st.caption(empty_message)
        return

    label, color = catalyst_score(news)
    st.badge(label, icon=":material/article:", color=color)

    for item in news:
        headline = str(item.get("headline") or "Untitled news")
        source = str(item.get("source") or "News")
        url = str(item.get("url") or "")
        published = timestamp_label(item.get("datetime"))
        summary = str(item.get("summary") or "").strip()
        tags = catalyst_tags(headline, summary)
        with st.container(border=True):
            if url:
                st.markdown(f"**[{headline}]({url})**")
            else:
                st.markdown(f"**{headline}**")
            if tags:
                with st.container(horizontal=True):
                    for tag in tags:
                        st.badge(tag, color="red" if tag == "Risk headline" else "blue")
            st.caption(f"{source} | {published}")
            if summary:
                st.markdown(markdown_text(summary[:360] + ("..." if len(summary) > 360 else "")))


def render_lazy_news_expander(
    label: str,
    news_loader: Any,
    empty_message: str = "No Finnhub news returned yet.",
    expanded: bool = False,
    icon: str = ":material/article:",
) -> None:
    news_panel = st.expander(label, expanded=expanded, icon=icon, on_change="rerun")
    is_open = bool(news_panel.open) if news_panel.open is not None else expanded
    if is_open:
        with news_panel:
            render_news_items(news_loader(), empty_message)
    else:
        st.caption(f"Open {label.lower()} when you need headlines. Keeping it closed makes auto-refresh pages faster.")


@st.cache_data(ttl=20, max_entries=150, show_spinner=False)
def yahoo_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    if yf is None:
        return None

    try:
        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
        stock = yf.Ticker(ticker)
        fast_info = dict(stock.fast_info or {})
        info = stock.info or {}
        quote = {
            "symbol": ticker,
            "shortName": info.get("shortName") or info.get("longName"),
            "longName": info.get("longName"),
            "sector": info.get("sector") or info.get("industry"),
            "regularMarketPrice": first_number(
                fast_info.get("last_price"),
                info.get("currentPrice"),
                info.get("regularMarketPrice"),
                info.get("previousClose"),
            ),
            "regularMarketPreviousClose": first_number(fast_info.get("previous_close"), info.get("previousClose")),
            "regularMarketChangePercent": info.get("regularMarketChangePercent"),
            "regularMarketVolume": first_number(info.get("regularMarketVolume"), info.get("volume")),
            "averageDailyVolume10Day": first_number(info.get("averageVolume10days"), info.get("averageVolume10Day")),
            "averageDailyVolume3Month": first_number(info.get("averageVolume"), info.get("averageDailyVolume3Month")),
            "floatShares": info.get("floatShares"),
            "sharesOutstanding": info.get("sharesOutstanding"),
            "impliedSharesOutstanding": info.get("impliedSharesOutstanding"),
            "quoteSourceName": info.get("quoteSourceName") or "Yahoo Finance quote",
            "marketState": info.get("marketState", "n/a"),
            "regularMarketTime": info.get("regularMarketTime"),
            "exchange": info.get("exchange"),
            "fullExchangeName": info.get("fullExchangeName"),
        }

        price = safe_float(quote["regularMarketPrice"])
        prev = safe_float(quote["regularMarketPreviousClose"])
        if price is not None and prev:
            quote["regularMarketChangePercent"] = ((price - prev) / prev) * 100
        return quote_to_stats(quote)
    except Exception:
        return None


@st.cache_data(ttl=20, max_entries=40, show_spinner=False)
def live_quote_stats(ticker: str) -> dict[str, Any] | None:
    ticker = normalize_user_symbol(ticker)
    finnhub_stats = finnhub_quote_stats(ticker)
    if finnhub_stats:
        return finnhub_stats
    return yahoo_quote_stats(ticker)


@st.cache_data(ttl=20, max_entries=20, show_spinner=False)
def live_screener_rows(
    min_price: float,
    max_price: float,
    min_gain_pct: float,
    min_day_volume: int = 100_000,
    result_size: int = 100,
) -> list[dict[str, Any]]:
    if yf is None:
        return []

    try:
        from yfinance import EquityQuery

        yf.set_tz_cache_location(str(YFINANCE_CACHE_DIR))
        query = EquityQuery(
            "and",
            [
                EquityQuery("btwn", ["intradayprice", float(min_price), float(max_price)]),
                EquityQuery("gte", ["percentchange", float(min_gain_pct)]),
                EquityQuery("eq", ["region", "us"]),
                EquityQuery("gt", ["dayvolume", int(min_day_volume)]),
            ],
        )
        response = yf.screen(query, size=min(result_size, 250), sortField="percentchange", sortAsc=False)
        quotes = response.get("quotes", []) if isinstance(response, dict) else []
        rows = [row for quote in quotes if (row := quote_to_stats(quote))]
        return rows
    except Exception:
        return []


def latest_market_stats(
    ticker: str,
    history: pd.DataFrame,
    source: str,
    live_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if live_stats:
        return live_stats

    profile = profile_for(ticker)
    df = history.tail(80).copy()
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    close = float(last["Close"])
    prev_close = float(prev["Close"]) if float(prev["Close"]) else close
    gain_pct = ((close - prev_close) / prev_close) * 100
    volume = float(last["Volume"])
    avg_volume = float(df["Volume"].iloc[:-1].tail(20).mean()) if len(df) > 22 else float(profile["volume"]) / float(profile["rvol"])
    rvol = volume / max(avg_volume, 1)

    return {
        "Ticker": normalize_user_symbol(ticker),
        "Company": profile["company"],
        "Sector": profile["sector"],
        "Price": close,
        "Previous close": prev_close,
        "Daily gain %": gain_pct,
        "Volume": volume,
        "Average volume": avg_volume,
        "RVOL": rvol,
        "Float M": float(profile["float_m"]),
        "Catalyst": profile["catalyst"],
        "Data source": source,
        "Float source": "Learning estimate" if source == "Learning data" else "Profile estimate",
        "Market state": "Practice data" if source == "Learning data" else "Chart-derived",
        "Quote time": chart_timestamp_label(history.index[-1]),
        "Exchange": "n/a",
    }


def build_trade_plan(stats: dict[str, Any], history: pd.DataFrame) -> dict[str, Any]:
    close = history["Close"].astype(float)
    high = history["High"].astype(float)
    low = history["Low"].astype(float)
    price = float(stats["Price"])

    ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
    ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
    atr = float((high - low).tail(14).mean())
    if not math.isfinite(atr) or atr <= 0:
        atr = max(price * 0.045, 0.1)

    buy_low = max(0.01, max(ema9, price - atr * 0.45))
    buy_high = max(buy_low * 1.01, price + atr * 0.12)
    entry_trigger = max(float(high.iloc[-1]) * 1.002, price * 1.01)
    stop = max(0.01, min(buy_low - atr * 0.65, price * 0.925))
    risk = max(entry_trigger - stop, price * 0.025)
    target1 = entry_trigger + risk * 1.5
    target2 = entry_trigger + risk * 2.4

    return {
        "EMA 9": ema9,
        "EMA 20": ema20,
        "ATR": atr,
        "Buy low": buy_low,
        "Buy high": buy_high,
        "Entry trigger price": entry_trigger,
        "Stop price": stop,
        "Target 1 price": target1,
        "Target 2 price": target2,
        "Buy zone": f"{money(buy_low)} - {money(buy_high)}",
        "Entry trigger": f"Break over {money(entry_trigger)}",
        "Stop": money(stop),
        "Target 1": money(target1),
        "Target 2": money(target2),
        "Risk/reward": round((target1 - entry_trigger) / max(entry_trigger - stop, 0.01), 2),
    }


def entry_confirmation_text(plan: dict[str, Any]) -> str:
    trigger = safe_float(plan.get("Entry trigger price"))
    if trigger is not None:
        return f"a break over {money(trigger)}"
    return str(plan.get("Entry trigger", "confirmation")).replace("Break over", "a break over")


def score_setup(stats: dict[str, Any], plan: dict[str, Any]) -> tuple[int, str, str, list[str], list[str]]:
    price = float(stats["Price"])
    gain = float(stats["Daily gain %"])
    float_m = float(stats["Float M"])
    rvol = float(stats["RVOL"])
    ema9 = float(plan["EMA 9"])
    ema20 = float(plan["EMA 20"])

    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"]:
        score += 20
        reasons.append("Price is inside the $2 to $20 momentum range.")
    else:
        warnings.append("Price is outside the preferred $2 to $20 range.")

    if gain >= DEFAULT_RULES["min_gain_pct"]:
        score += 25
        reasons.append("Daily gain is above the 10% gapper threshold.")
    else:
        warnings.append("Daily gain has not cleared the 10% gapper threshold.")

    if float_m <= DEFAULT_RULES["max_float_m"]:
        score += 20
        reasons.append("Float estimate is under 10 million shares.")
    else:
        warnings.append("Float estimate is over 10 million shares.")

    if rvol >= DEFAULT_RULES["min_rvol"]:
        score += 20
        reasons.append("Relative volume is high versus its recent average.")
    elif rvol >= 2:
        score += 10
        warnings.append("RVOL is active, but below the preferred 3.0x level.")
    else:
        warnings.append("RVOL is light for this strategy.")

    if price > ema9 > ema20:
        score += 15
        reasons.append("Price is holding above short-term trend lines.")
    elif price > ema20:
        score += 8
        reasons.append("Price is still above the 20-day trend.")
    else:
        warnings.append("Trend is weak or below key moving averages.")

    if score >= 88:
        return score, "A+ momentum gapper", "High", reasons, warnings
    if score >= 74:
        return score, "Strong watch", "Medium-high", reasons, warnings
    if score >= 60:
        return score, "Watch only", "Medium", reasons, warnings
    return score, "Study setup", "Low", reasons, warnings


@st.cache_data(ttl=20, max_entries=300, show_spinner=False)
def analyze_ticker(
    ticker: str,
    period: str = "3mo",
    interval: str = "1d",
    prefer_live: bool = False,
) -> dict[str, Any]:
    ticker = normalize_user_symbol(ticker)
    history, source = load_history(ticker, period=period, interval=interval, prefer_live=prefer_live)
    live_stats = live_quote_stats(ticker) if prefer_live else None
    stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
    plan = build_trade_plan(stats, history)
    score, setup, confidence, reasons, warnings = score_setup(stats, plan)
    fit = playbook_fit_label(stats, score)
    data_quality, _ = data_quality_badge(stats.get("Data source", source))
    status = live_status({**stats, **plan})

    return {
        **stats,
        **plan,
        "AI score": int(score),
        "Setup": setup,
        "Confidence": confidence,
        "Playbook fit": fit,
        "Data quality": data_quality,
        "Data confidence": data_confidence_summary({**stats, **plan}).get("label", "n/a"),
        "Status": status,
        "Reasons": reasons,
        "Warnings": warnings,
        "Plan": (
            f"Watch {stats['Ticker']} for a clean hold inside {plan['Buy zone']} and only consider a "
            f"paper entry after {entry_confirmation_text(plan)}. Keep risk defined near {plan['Stop']}."
        ),
    }


def row_matches_rules(row: dict[str, Any], rules: dict[str, float]) -> bool:
    return (
        rules["min_price"] <= float(row["Price"]) <= rules["max_price"]
        and float(row["Daily gain %"]) >= rules["min_gain_pct"]
        and float(row["Float M"]) <= rules["max_float_m"]
        and float(row["RVOL"]) >= rules["min_rvol"]
    )


@st.cache_data(ttl=20, max_entries=80, show_spinner=False)
def run_scan(
    min_price: float,
    max_price: float,
    min_gain_pct: float,
    max_float_m: float,
    min_rvol: float,
    prefer_live: bool = False,
    include_learning: bool = True,
) -> pd.DataFrame:
    rules = {
        "min_price": float(min_price),
        "max_price": float(max_price),
        "min_gain_pct": float(min_gain_pct),
        "max_float_m": float(max_float_m),
        "min_rvol": float(min_rvol),
    }
    rows = []
    if prefer_live:
        live_rows = live_screener_rows(min_price, max_price, min_gain_pct)
        for row in live_rows:
            if not row_matches_rules(row, rules):
                continue
            history, _ = load_history(row["Ticker"], period="3mo", interval="1d", prefer_live=True)
            plan = build_trade_plan(row, history) if not history.empty else {}
            score, setup, confidence, reasons, warnings = score_setup(row, plan) if plan else (0, "Live watch", "Low", [], [])
            fit = playbook_fit_label(row, score)
            data_quality, _ = data_quality_badge(row.get("Data source"))
            status = live_status({**row, **plan}) if plan else "Watching"
            enriched = {
                **row,
                **plan,
                "AI score": int(score),
                "Setup": setup,
                "Confidence": confidence,
                "Playbook fit": fit,
                "Data quality": data_quality,
                "Data confidence": data_confidence_summary({**row, **plan}).get("label", "n/a"),
                "Status": status,
                "Reasons": reasons,
                "Warnings": warnings,
                "Plan": (
                    f"Watch {row['Ticker']} for a clean hold inside {plan.get('Buy zone', 'the pullback zone')} "
                    f"and only consider a paper entry after {entry_confirmation_text(plan)}."
                ),
            }
            rows.append(enriched)
            if len(rows) >= 12:
                break

    if (not prefer_live) or (not rows and include_learning):
        for profile in DEMO_PROFILES:
            analysis = analyze_ticker(profile["ticker"], prefer_live=False)
            if row_matches_rules(analysis, rules):
                rows.append(analysis)

    if not rows and include_learning:
        for profile in DEMO_PROFILES[:6]:
            rows.append(analyze_ticker(profile["ticker"], prefer_live=False))

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["AI score", "Daily gain %", "RVOL"], ascending=False).reset_index(drop=True)


@st.cache_data(ttl=86400, max_entries=3, show_spinner=False)
def sp500_tickers() -> list[str]:
    try:
        from bs4 import BeautifulSoup

        response = requests.get(SP500_SOURCE_URL, headers={"User-Agent": f"Mozilla/5.0 {APP_NAME}"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "constituents"})
        if table is None:
            return SP500_SAMPLE_TICKERS
        tickers = []
        for row in table.select("tbody tr"):
            first_cell = row.find("td")
            if first_cell is None:
                continue
            ticker = first_cell.get_text(strip=True).replace(".", "-").upper()
            if ticker:
                tickers.append(ticker)
        return tickers or SP500_SAMPLE_TICKERS
    except Exception:
        return SP500_SAMPLE_TICKERS


def market_scan_universe(presets: list[str], custom_tickers: str = "", include_etfs: bool = True) -> list[str]:
    tickers: list[str] = []
    if "Core movers" in presets:
        tickers.extend(CORE_MARKET_TICKERS)
    if "S&P 500" in presets or "S&P 500 sample" in presets:
        tickers.extend(sp500_tickers())
    if "Watchlist" in presets:
        tickers.extend(read_watchlist())
    if "All US stocks" in presets:
        full_universe, _ = full_us_market_universe(include_etfs=include_etfs, api_marker=finnhub_key_marker())
        tickers.extend(full_universe)
    for preset, values in GLOBAL_MARKET_WATCH.items():
        if preset in presets:
            tickers.extend(values)
    tickers.extend(clean_market_symbol(part) for part in custom_tickers.replace("\n", ",").split(",") if part.strip())
    return unique_symbols(tickers)


def ticker_batch(tickers: list[str], start_at: int, batch_size: int) -> list[str]:
    if not tickers:
        return []
    start = min(max(int(start_at), 0), max(len(tickers) - 1, 0))
    end = min(start + max(int(batch_size), 1), len(tickers))
    return tickers[start:end]


def next_batch_start(start_at: int, batch_size: int, total: int) -> int:
    if total <= 0:
        return 0
    next_start = int(start_at) + int(batch_size)
    return 0 if next_start >= total else next_start


def merge_market_scan_results(existing: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    frames = [frame for frame in [existing, latest] if isinstance(frame, pd.DataFrame) and not frame.empty]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    if "Ticker" in combined.columns:
        combined = combined.drop_duplicates("Ticker", keep="last")
    sort_columns = [column for column in ["Daily gain %", "RVOL", "AI score"] if column in combined.columns]
    if sort_columns:
        combined = combined.sort_values(sort_columns, ascending=False)
    return combined.reset_index(drop=True)


@st.cache_data(ttl=30, max_entries=60, show_spinner=False)
def broad_market_scan(tickers: tuple[str, ...], max_names: int = 80) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ticker in tickers[:max_names]:
        history, source = load_history(ticker, period="5d", interval="5m", prefer_live=True)
        live_stats = live_quote_stats(ticker)
        if history.empty and live_stats is None:
            continue
        stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
        if history.empty:
            history, _ = load_history(ticker, period="3mo", interval="1d", prefer_live=False)
        plan = build_trade_plan(stats, history) if not history.empty else {}
        if plan:
            score, setup, confidence, reasons, warnings = score_setup(stats, plan)
        else:
            score, setup, confidence, reasons, warnings = 0, "Live watch", "Low", [], []
        rows.append(
            {
                **stats,
                **plan,
                "AI score": int(score),
                "Setup": setup,
                "Confidence": confidence,
                "Playbook fit": playbook_fit_label(stats, score),
                "Data quality": data_quality_badge(stats.get("Data source", source))[0],
                "Data confidence": data_confidence_summary({**stats, **plan}).get("label", "n/a"),
                "Status": live_status({**stats, **plan}) if plan else "Watching",
                "Reasons": reasons,
                "Warnings": warnings,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Daily gain %", "RVOL", "AI score"], ascending=False).reset_index(drop=True)


def scan_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Ticker",
        "Priority",
        "Rules ready",
        "Playbook fit",
        "Company",
        "Status",
        "Price",
        "Daily gain %",
        "Float M",
        "RVOL",
        "AI score",
        "Setup",
        "Confidence",
        "Data quality",
        "Data confidence",
        "Buy zone",
        "Entry trigger",
        "Stop",
        "Target 1",
        "Risk/reward",
        "Data source",
        "Float source",
        "Market state",
        "Quote time",
    ]
    return df[[column for column in columns if column in df.columns]]


def remember_selected_ticker(display_df: pd.DataFrame, event: Any) -> None:
    try:
        rows = list(event.selection.rows)
    except Exception:
        rows = []
    if not rows or "Ticker" not in display_df.columns:
        return
    ticker = str(display_df.iloc[rows[0]]["Ticker"]).upper()
    if ticker:
        st.session_state.selected_ticker = ticker
        st.caption(f"{ticker} stock selected for Charts and AI Coach.")


def scanner_rule_match_label(row: pd.Series | dict[str, Any]) -> str:
    price = safe_float(row.get("Price"), 0) or 0
    gain = safe_float(row.get("Daily gain %"), 0) or 0
    float_m = safe_float(row.get("Float M"), 999) or 999
    rvol = safe_float(row.get("RVOL"), 0) or 0
    checks = [
        DEFAULT_RULES["min_price"] <= price <= DEFAULT_RULES["max_price"],
        gain >= DEFAULT_RULES["min_gain_pct"],
        float_m <= DEFAULT_RULES["max_float_m"],
        rvol >= DEFAULT_RULES["min_rvol"],
    ]
    return f"{sum(bool(check) for check in checks)}/4"


def scanner_priority_label(row: pd.Series | dict[str, Any]) -> str:
    status = str(row.get("Status", "Watching"))
    data_confidence = str(row.get("Data confidence", ""))
    score = safe_float(row.get("AI score"), 0) or 0
    if status == "No quote" or "Low" in data_confidence:
        return "Verify data"
    if status == "Breakout trigger" and score >= 74:
        return "Review now"
    if status == "In buy zone":
        return "Wait trigger"
    if status in {"Near buy zone", "Momentum active"}:
        return "Watchlist"
    if status == "Below stop":
        return "Skip"
    if score >= 74:
        return "Strong study"
    return "Study"


def add_scanner_readability_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display_df = df.copy()
    priority = display_df.apply(scanner_priority_label, axis=1)
    rules_ready = display_df.apply(scanner_rule_match_label, axis=1)
    if "Priority" in display_df.columns:
        display_df["Priority"] = priority
    else:
        display_df.insert(1, "Priority", priority)
    if "Rules ready" in display_df.columns:
        display_df["Rules ready"] = rules_ready
    else:
        display_df.insert(2, "Rules ready", rules_ready)
    return display_df


def show_scan_table(df: pd.DataFrame, key: str = "scan_table") -> None:
    if df.empty:
        st.info("No matches with the current filters.")
        return
    display_df = scan_columns(add_scanner_readability_columns(df))
    st.caption("Rank read: Priority explains the next action; Rules ready is price/gain/float/RVOL. Verify data confidence and quote time before trusting any paper plan.")
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key=key,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
            "Priority": st.column_config.TextColumn("Priority"),
            "Rules ready": st.column_config.TextColumn("Rules"),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Status": st.column_config.TextColumn("Status"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.1f%%"),
            "Float M": st.column_config.NumberColumn("Float", format="%.1fM"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
            "Data confidence": st.column_config.TextColumn("Data confidence"),
            "Risk/reward": st.column_config.NumberColumn("R/R", format="%.2f"),
        },
    )
    remember_selected_ticker(display_df, event)


def show_broad_market_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No market rows returned yet. Try a smaller preset or check your data key/network.")
        return
    columns = [
        "Ticker",
        "Playbook fit",
        "Company",
        "Status",
        "Price",
        "Daily gain %",
        "RVOL",
        "Volume",
        "AI score",
        "Data quality",
        "Data confidence",
        "Entry trigger",
        "Stop",
        "Target 1",
        "Data source",
        "Quote time",
    ]
    display_df = add_scanner_readability_columns(df)
    columns = ["Ticker", "Priority", "Rules ready", *columns[1:]]
    display_df = display_df[[column for column in columns if column in display_df.columns]]
    st.caption("Rank read: Priority explains the next action; Rules ready is price/gain/float/RVOL. Use the chart price audit if a number looks stale or unusual.")
    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        key="broad_market_table",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
            "Priority": st.column_config.TextColumn("Priority"),
            "Rules ready": st.column_config.TextColumn("Rules"),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.2f%%"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "Volume": st.column_config.NumberColumn("Volume", format="compact"),
            "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
            "Data confidence": st.column_config.TextColumn("Data confidence"),
        },
    )
    remember_selected_ticker(display_df, event)


def action_queue_frame(df: pd.DataFrame, limit: int = 8) -> pd.DataFrame:
    if df.empty or "Ticker" not in df.columns:
        return pd.DataFrame()

    status_rank = {
        "Breakout trigger": 0,
        "In buy zone": 1,
        "Near buy zone": 2,
        "Momentum active": 3,
        "Watching": 4,
        "Below stop": 5,
        "No quote": 6,
    }
    action_map = {
        "Breakout trigger": ("Review approval", "At or above trigger. Confirm news, spread, and risk."),
        "In buy zone": ("Wait for trigger", "Inside buy area. Do not buy until confirmation."),
        "Near buy zone": ("Watch closely", "Close to the planned area."),
        "Momentum active": ("Check chart", "Momentum is active, but the entry still needs review."),
        "Below stop": ("Skip", "Plan is invalid until a new setup forms."),
        "No quote": ("Verify data", "No usable quote returned."),
    }
    confidence_rank = {
        "High confidence": 0,
        "Usable for paper": 1,
        "Verify first": 2,
        "Practice data": 3,
        "Practice only": 4,
    }
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        raw = row.to_dict()
        ticker = normalize_user_symbol(raw.get("Ticker"))
        if not ticker:
            continue
        status = str(raw.get("Status") or live_status(raw))
        action, why = action_map.get(status, ("Study", "Use it for context until the setup improves."))
        price = safe_float(raw.get("Price"))
        entry = safe_float(raw.get("Entry")) or safe_float(raw.get("Entry trigger price"))
        stop = safe_float(raw.get("Stop")) or safe_float(raw.get("Stop price"))
        target = safe_float(raw.get("Target 1")) or safe_float(raw.get("Target 1 price"))
        distance = safe_float(raw.get("Distance to entry %"))
        if distance is None and price is not None and entry is not None and price:
            distance = (entry - price) / price * 100
        score = safe_float(raw.get("AI score"), 0) or 0
        rvol = safe_float(raw.get("RVOL"), 0) or 0
        confidence = str(raw.get("Data confidence") or data_confidence_summary(raw).get("label", "n/a"))
        rows.append(
            {
                "_Rank": status_rank.get(status, 9),
                "_ConfidenceRank": confidence_rank.get(confidence, 5),
                "Stock": ticker,
                "Action": action,
                "Status": status,
                "Price": price,
                "Entry": entry,
                "Stop": stop,
                "Target 1": target,
                "To entry %": distance,
                "AI score": score,
                "RVOL": rvol,
                "Why": why,
                "Data": raw.get("Data quality") or data_quality_badge(raw.get("Data source"))[0],
                "Confidence": confidence,
            }
        )

    if not rows:
        return pd.DataFrame()
    queue = pd.DataFrame(rows).sort_values(["_Rank", "_ConfidenceRank", "AI score", "RVOL"], ascending=[True, True, False, False]).head(limit)
    return queue.drop(columns=["_Rank", "_ConfidenceRank"]).reset_index(drop=True)


def render_action_queue(df: pd.DataFrame, key: str) -> None:
    queue = action_queue_frame(df)
    with st.container(border=True):
        st.markdown("**Live action queue**")
        st.caption("Ranked by action status first, then AI score and RVOL. Data confidence flags whether the quote is usable for paper practice. Select a row to send that stock into Charts, AI Coach, and Trade Desk.")
        if queue.empty:
            st.info("No action queue rows yet. Run a scan or add stocks to the watchlist.")
            return

        event = st.dataframe(
            queue,
            width="stretch",
            hide_index=True,
            key=key,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "Stock": st.column_config.TextColumn("Stock", pinned=True),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
                "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
                "Target 1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
                "To entry %": st.column_config.NumberColumn("To entry", format="%.2f%%"),
                "AI score": st.column_config.ProgressColumn("AI score", min_value=0, max_value=100),
                "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
                "Confidence": st.column_config.TextColumn("Confidence"),
            },
        )
        try:
            selected_rows = list(event.selection.rows)
        except Exception:
            selected_rows = []
        if selected_rows:
            selected = str(queue.iloc[selected_rows[0]]["Stock"])
            st.session_state.selected_ticker = selected
            with st.container(horizontal=True):
                st.badge(f"{selected} selected", icon=":material/check_circle:", color="green")
                st.caption("Open Charts, AI Coach, or Trade Desk from the left menu to continue with this stock.")


def data_health_frame(df: pd.DataFrame) -> pd.DataFrame:
    labels = ["High confidence", "Usable for paper", "Verify first", "Practice data", "Practice only"]
    counts = {label: 0 for label in labels}
    if df.empty:
        return pd.DataFrame([{"Label": label, "Rows": count} for label, count in counts.items()])

    for _, row in df.iterrows():
        raw = row.to_dict()
        stored_label = raw.get("Data confidence")
        label = "" if pd.isna(stored_label) else str(stored_label).strip()
        if not label or label.lower() in {"n/a", "nan", "none"}:
            label = str(data_confidence_summary(raw).get("label", "n/a"))
        if label not in counts:
            label = "Practice only" if "practice" in label.lower() else "Verify first"
        counts[label] += 1
    return pd.DataFrame([{"Label": label, "Rows": count} for label, count in counts.items()])


def data_source_mix(df: pd.DataFrame, limit: int = 3) -> str:
    if df.empty or "Data source" not in df.columns:
        return "No source rows yet"
    sources = df["Data source"].fillna("Unknown").astype(str).str.strip()
    sources = sources.replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})
    counts = sources.value_counts().head(limit)
    if counts.empty:
        return "No source rows yet"
    return ", ".join(f"{source}: {int(count)}" for source, count in counts.items())


def render_data_health_summary(df: pd.DataFrame) -> None:
    health = data_health_frame(df)
    total = int(health["Rows"].sum()) if not health.empty else 0
    values = {str(row["Label"]): int(row["Rows"]) for _, row in health.iterrows()}
    trusted_total = values.get("High confidence", 0) + values.get("Usable for paper", 0)
    verify_total = values.get("Verify first", 0)
    practice_data = values.get("Practice data", 0)
    practice_only = values.get("Practice only", 0)
    practice_total = practice_data + practice_only
    trusted_pct = (trusted_total / total) if total else 0.0
    with st.container(border=True):
        st.markdown("**Data health**")
        st.caption("Use this before trusting any scanner result. It shows whether the gameplan is using cleaner live rows, verify-first rows, or practice fallback rows.")
        cols = st.columns(4)
        cols[0].metric("Rows checked", str(total), border=True)
        cols[1].metric("Usable rows", str(trusted_total), f"{trusted_pct:.0%} trusted", border=True)
        cols[2].metric("Verify first", str(verify_total), border=True)
        cols[3].metric("Practice rows", str(practice_total), f"{practice_data} fallback / {practice_only} weak", border=True)

        if total == 0:
            st.warning("No scanner rows are loaded yet. Run or refresh the scan to build the health readout.", icon=":material/warning:")
        elif practice_total == total:
            st.warning(
                "This gameplan is using practice fallback rows right now. It is useful for learning the workflow, but verify a live quote before trusting a paper setup.",
                icon=":material/model_training:",
            )
        elif trusted_total == 0:
            st.warning("No rows are clean enough to trust without another source check yet.", icon=":material/warning:")
        elif verify_total or practice_total:
            st.info("Some rows need another quote/news check before you use them for paper trading.", icon=":material/info:")
        else:
            st.success("All displayed rows are in the cleaner data buckets for paper practice.", icon=":material/verified:")

        st.progress(float(trusted_pct))
        bucket_text = (
            f"Buckets: high {values.get('High confidence', 0)}, usable {values.get('Usable for paper', 0)}, "
            f"verify {verify_total}, practice {practice_total}."
        )
        st.caption(f"Sources: {data_source_mix(df)}. {bucket_text}")


def provider_status_items() -> list[dict[str, str]]:
    alpaca_ready = alpaca_enabled()
    finnhub_ready = finnhub_enabled()
    yahoo_ready = yf is not None
    chart_ready = LIGHTWEIGHT_CHARTS_FILE.exists()
    return [
        {
            "name": "Alpaca IEX",
            "state": "Connected" if alpaca_ready else "Add paper keys",
            "tone": "ready" if alpaca_ready else "watch",
            "detail": "First choice for regular-stock intraday candles when keys are present. Free IEX feed can still be limited or delayed.",
        },
        {
            "name": "Finnhub",
            "state": "Connected" if finnhub_ready else "Add key",
            "tone": "ready" if finnhub_ready else "watch",
            "detail": "Used for quotes, company news, market news, and symbol lists. News quality depends on the free endpoint.",
        },
        {
            "name": "Yahoo fallback",
            "state": "Available" if yahoo_ready else "Package missing",
            "tone": "info" if yahoo_ready else "watch",
            "detail": "Backup candles, index symbols like S&P 500, and quote estimates when the primary free feeds cannot answer.",
        },
        {
            "name": "TradingView chart",
            "state": "Local asset" if chart_ready else "Online fallback",
            "tone": "ready" if chart_ready else "watch",
            "detail": "The app uses TradingView Lightweight Charts locally for smooth candles, zooming, volume, and level overlays.",
        },
    ]


def provider_cards_html(items: list[dict[str, str]]) -> str:
    parts = ['<div class="msa-provider-grid">']
    for item in items:
        parts.append(
            '<div class="msa-provider-card msa-provider-{tone}">'
            '<div class="msa-provider-name">{name}</div>'
            '<div class="msa-provider-state">{state}</div>'
            '<div class="msa-provider-detail">{detail}</div>'
            '</div>'.format(
                tone=html.escape(item["tone"]),
                name=html.escape(item["name"]),
                state=html.escape(item["state"]),
                detail=html.escape(item["detail"]),
            )
        )
    parts.append("</div>")
    return "".join(parts)


def render_data_stack_panel(compact: bool = False) -> None:
    items = provider_status_items()
    connected = sum(1 for item in items if item["tone"] == "ready")
    with st.container(border=True):
        st.markdown("**Data stack**")
        with st.container(horizontal=True):
            st.badge(f"{connected}/{len(items)} ready", icon=":material/database:", color="green" if connected >= 3 else "orange")
            st.badge("Free feeds", icon=":material/savings:", color="blue")
            st.badge("Paper-trading only", icon=":material/edit_note:", color="blue")
        if not compact:
            render_html(provider_cards_html(items))
        render_html(
            '<div class="msa-source-flow">'
            '<b>Source order:</b> regular-stock candles try Alpaca IEX first, then Yahoo-style chart fallback, then learning data. '
            'Quotes and news use Finnhub when available. Indexes like S&P 500 use Yahoo-style symbols because Alpaca IEX is a stock feed.'
            '</div>',
        )


def source_explanation(source: Any) -> str:
    source_text = str(source or "Unknown")
    lowered = source_text.lower()
    if "alpaca" in lowered:
        return "Alpaca IEX candle feed. Good free intraday source for regular stocks, but still verify fast moves and after-hours behavior."
    if "finnhub" in lowered:
        return "Finnhub quote/news feed. Useful for live context, catalysts, and scanner metadata."
    if "yahoo" in lowered:
        return "Yahoo-style fallback data. Helpful for indexes and backup candles, but free data can be delayed or rate-limited."
    if "learning" in lowered:
        return "Learning fallback data. Use it to study the app and practice the workflow, not as a live market quote."
    return "Unknown source. Verify with another quote source before trusting the number."


def render_source_brief(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    active_source = str(analysis.get("Data source", "n/a"))
    chart_label = chart_source or active_source
    confidence = data_confidence_summary(analysis, chart_source)
    with st.container(border=True):
        st.markdown("**Source brief**")
        cols = st.columns(3)
        cols[0].metric("Active price source", data_quality_badge(active_source)[0], active_source, border=True)
        cols[1].metric("Chart source", data_quality_badge(chart_label)[0], str(chart_label), border=True)
        cols[2].metric("Confidence", str(confidence["label"]), f"{confidence['score']}/100", border=True)
        st.caption(source_explanation(chart_label))


def clock_minutes(value: Any) -> int | None:
    try:
        hour, minute = str(value).split(":", 1)
        return int(hour) * 60 + int(minute)
    except (TypeError, ValueError):
        return None


def market_clock_state(local: pd.Timestamp, item: dict[str, Any]) -> str:
    if local.weekday() >= 5:
        return "Weekend"
    minutes = int(local.hour) * 60 + int(local.minute)
    open_minutes = clock_minutes(item.get("Open"))
    close_minutes = clock_minutes(item.get("Close"))
    premarket_minutes = clock_minutes(item.get("Premarket"))
    after_hours_minutes = clock_minutes(item.get("After hours"))

    if open_minutes is None or close_minutes is None:
        return "Check session"
    if premarket_minutes is not None and premarket_minutes <= minutes < open_minutes:
        return "Premarket"
    if open_minutes <= minutes < close_minutes:
        return "Regular session"
    if after_hours_minutes is not None and close_minutes <= minutes < after_hours_minutes:
        return "After-hours"
    return "Closed"


def market_clock_frame() -> pd.DataFrame:
    rows = []
    now_utc = pd.Timestamp.now(tz="UTC")
    for item in MARKET_CLOCKS:
        local = now_utc.tz_convert(item["Timezone"])
        state = market_clock_state(local, item)
        rows.append(
            {
                "Market": item["Market"],
                "Local time": local.strftime("%a %I:%M %p"),
                "State": state,
                "Typical session": item["Typical session"],
                "Beginner read": item.get("Beginner read", "Typical session reference."),
            }
        )
    return pd.DataFrame(rows)


def read_watchlist() -> list[str]:
    if WATCHLIST_FILE.exists():
        try:
            data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
            return sorted({clean for item in data if (clean := normalize_user_symbol(item))})
        except Exception:
            pass
    return ["BBAI", "KULR", "LUNR", "SOUN"]


def write_watchlist(tickers: list[str]) -> None:
    clean = sorted({clean_ticker for ticker in tickers if (clean_ticker := normalize_user_symbol(ticker))})
    WATCHLIST_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def empty_journal() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Date",
            "Ticker",
            "Setup",
            "Entry",
            "Exit",
            "Stop",
            "Shares",
            "P/L $",
            "P/L %",
            "R multiple",
            "Notes",
        ]
    )


def read_journal() -> pd.DataFrame:
    if JOURNAL_FILE.exists():
        try:
            return pd.read_csv(JOURNAL_FILE)
        except Exception:
            pass
    return empty_journal()


def save_journal(df: pd.DataFrame) -> None:
    df.to_csv(JOURNAL_FILE, index=False)


def append_journal(row: dict[str, Any]) -> None:
    df = read_journal()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_journal(df)


def empty_orders() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Created",
            "Status",
            "Ticker",
            "Side",
            "Order type",
            "Entry",
            "Stop",
            "Target 1",
            "Shares",
            "Risk $",
            "Reason",
        ]
    )


def read_orders() -> pd.DataFrame:
    if ORDERS_FILE.exists():
        try:
            return pd.read_csv(ORDERS_FILE)
        except Exception:
            pass
    return empty_orders()


def save_order(row: dict[str, Any]) -> None:
    df = read_orders()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(ORDERS_FILE, index=False)


def stage_order_from_analysis(analysis: dict[str, Any], risk_dollars: float = 25.0) -> dict[str, Any]:
    entry = safe_float(analysis.get("Entry trigger price"), safe_float(analysis.get("Price"), 0)) or 0
    stop = safe_float(analysis.get("Stop price"), max(entry * 0.95, 0.01)) or max(entry * 0.95, 0.01)
    risk_per_share = max(entry - stop, entry * 0.01, 0.01)
    shares = max(1, int(float(risk_dollars) // risk_per_share))
    label, reason = ai_action_summary(analysis)
    return {
        "Created": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "Status": "Staged",
        "Ticker": analysis.get("Ticker", ""),
        "Side": "Buy",
        "Order type": "Paper stop-limit plan",
        "Entry": round(entry, 4),
        "Stop": round(stop, 4),
        "Target 1": round(safe_float(analysis.get("Target 1 price"), entry) or entry, 4),
        "Shares": shares,
        "Risk $": round(shares * risk_per_share, 2),
        "Reason": f"{label}: {reason}",
    }


def order_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display = df.copy()
    if "Created" in display.columns:
        display["Created"] = pd.to_datetime(display["Created"], errors="coerce")
    return display


def order_column_config() -> dict[str, Any]:
    return {
        "Created": st.column_config.DatetimeColumn("Created", format="MMM DD, YYYY h:mm A"),
        "Ticker": st.column_config.TextColumn("Stock", pinned=True),
        "Entry": st.column_config.NumberColumn("Entry", format="$%.4f"),
        "Stop": st.column_config.NumberColumn("Stop", format="$%.4f"),
        "Target 1": st.column_config.NumberColumn("Target 1", format="$%.4f"),
        "Shares": st.column_config.NumberColumn("Shares", format="%d"),
        "Risk $": st.column_config.NumberColumn("Paper risk", format="$%.2f"),
        "Reason": st.column_config.TextColumn("Reason"),
    }


def approve_paper_order(order: dict[str, Any]) -> None:
    approved = {**order, "Status": "Approved paper order", "Created": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")}
    save_order(approved)
    append_journal(
        {
            "Date": date.today().isoformat(),
            "Ticker": approved["Ticker"],
            "Setup": "AI-approved paper order",
            "Entry": approved["Entry"],
            "Exit": approved["Entry"],
            "Stop": approved["Stop"],
            "Shares": approved["Shares"],
            "P/L $": 0,
            "P/L %": 0,
            "R multiple": 0,
            "Notes": approved["Reason"],
        }
    )


def render_paper_approval_gate(
    analysis: dict[str, Any],
    order: dict[str, Any],
    chart_source: str,
    risk_dollars: float,
) -> bool:
    confidence = data_confidence_summary(analysis, chart_source)
    status = live_status(analysis)
    math_data = ai_trade_math(analysis)
    rr_1 = math_data["rr_1"]
    risk_per_share = math_data["risk"]
    hard_blocks: list[str] = []
    caution_notes: list[str] = []

    if confidence["score"] < 45:
        hard_blocks.append("Data confidence is too weak for approval. Verify another source first.")
    elif confidence["score"] < 65:
        caution_notes.append(f"Data confidence is {confidence['label']}. Confirm the quote before approval.")
    if status == "Below stop":
        hard_blocks.append("Price is below the stop area, so the staged plan is invalid.")
    if risk_per_share is None or risk_per_share <= 0:
        hard_blocks.append("The staged order does not have a valid entry-to-stop risk.")
    if rr_1 is not None and rr_1 < 1.4:
        caution_notes.append("Target 1 reward/risk is below the preferred 1.4R threshold.")

    st.markdown("**Approval checklist**")
    with st.container(horizontal=True):
        st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))
        st.badge(status, icon=":material/candlestick_chart:", color="red" if status == "Below stop" else "green" if status in {"Breakout trigger", "In buy zone"} else "orange")
        st.badge(f"Max paper risk {money(risk_dollars)}", icon=":material/account_balance_wallet:", color="blue")
        st.badge(f"Staged risk {money(safe_float(order.get('Risk $')))}", icon=":material/rule:", color="blue")

    checklist_key = f"{normalize_user_symbol(order.get('Ticker'))}_{order.get('Entry')}_{order.get('Stop')}_{safe_float(order.get('Risk $'), 0)}"
    items = [
        "I checked the data source, confidence, and quote time.",
        "I checked the chart and the entry trigger is not a chase.",
        "I understand the stop loss and where the paper idea is wrong.",
        "I checked that target 1 pays enough reward for the risk.",
        "I checked news, spread, volume, and halt risk before approval.",
    ]
    completed = 0
    for index, item in enumerate(items):
        if st.checkbox(item, key=f"paper_gate_{checklist_key}_{index}"):
            completed += 1
    st.progress(completed / len(items))
    st.caption(f"{completed} of {len(items)} approval checks complete. This still saves a paper order only.")

    if hard_blocks:
        st.error(" ".join(hard_blocks), icon=":material/block:")
    elif caution_notes:
        st.warning(" ".join(caution_notes), icon=":material/warning:")
    else:
        st.caption("No hard approval blockers from the current model. Keep this paper-only unless a real broker integration is separately approved.")

    return completed == len(items) and not hard_blocks


def journal_stats(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {"trades": 0, "win_rate": 0.0, "total_pl": 0.0, "avg_r": 0.0}
    pl = pd.to_numeric(df["P/L $"], errors="coerce").fillna(0)
    r_mult = pd.to_numeric(df["R multiple"], errors="coerce").fillna(0)
    wins = int((pl > 0).sum())
    return {
        "trades": int(len(df)),
        "win_rate": wins / max(len(df), 1) * 100,
        "total_pl": float(pl.sum()),
        "avg_r": float(r_mult.mean()) if len(r_mult) else 0.0,
    }


def journal_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display = df.copy()
    if "Date" in display.columns:
        display["Date"] = pd.to_datetime(display["Date"], errors="coerce")
    for column in ["Entry", "Exit", "Stop", "Shares", "P/L $", "P/L %", "R multiple"]:
        if column in display.columns:
            display[column] = pd.to_numeric(display[column], errors="coerce")
    return display


def journal_column_config() -> dict[str, Any]:
    return {
        "Date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
        "Ticker": st.column_config.TextColumn("Stock", pinned=True),
        "Entry": st.column_config.NumberColumn("Entry", format="$%.4f"),
        "Exit": st.column_config.NumberColumn("Exit", format="$%.4f"),
        "Stop": st.column_config.NumberColumn("Stop", format="$%.4f"),
        "Shares": st.column_config.NumberColumn("Shares", format="%d"),
        "P/L $": st.column_config.NumberColumn("P/L", format="$%.2f"),
        "P/L %": st.column_config.NumberColumn("P/L %", format="%.2f%%"),
        "R multiple": st.column_config.NumberColumn("R", format="%.2f"),
        "Notes": st.column_config.TextColumn("Review notes"),
    }


def journal_review_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    display = journal_display_frame(df)
    if display.empty:
        return {
            "trades": 0,
            "expectancy_r": 0.0,
            "avg_win_r": 0.0,
            "avg_loss_r": 0.0,
            "best_r": 0.0,
            "worst_r": 0.0,
            "best_stock": "n/a",
            "worst_stock": "n/a",
            "common_setup": "n/a",
            "review_tags": pd.DataFrame(columns=["Tag", "Count"]),
            "coaching": ["Save a few paper trades, then the review coach will start finding patterns."],
            "equity": pd.DataFrame(columns=["Date", "Cumulative P/L"]),
        }

    pl = pd.to_numeric(display.get("P/L $"), errors="coerce").fillna(0)
    r_mult = pd.to_numeric(display.get("R multiple"), errors="coerce").fillna(0)
    wins = r_mult[r_mult > 0]
    losses = r_mult[r_mult < 0]
    best_index = int(r_mult.idxmax()) if len(r_mult) else 0
    worst_index = int(r_mult.idxmin()) if len(r_mult) else 0
    setup_counts = display["Setup"].astype(str).replace("", "Unknown setup").value_counts()

    tag_keywords = {
        "Chased entry": ["chase", "late", "fomo", "too high"],
        "Stop issue": ["stop", "held", "ignored", "moved stop"],
        "News miss": ["news", "catalyst", "offering", "dilution"],
        "Spread/slippage": ["spread", "slippage", "fill"],
        "Size too big": ["size", "oversized", "too many shares"],
        "No plan": ["no plan", "guess", "random"],
    }
    tag_counts = {tag: 0 for tag in tag_keywords}
    for note in display["Notes"].fillna("").astype(str):
        lowered = note.lower()
        for tag, keywords in tag_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                tag_counts[tag] += 1
    review_tags = pd.DataFrame(
        [{"Tag": tag, "Count": count} for tag, count in tag_counts.items() if count > 0]
    ).sort_values("Count", ascending=False) if any(tag_counts.values()) else pd.DataFrame(columns=["Tag", "Count"])

    coaching: list[str] = []
    expectancy = float(r_mult.mean()) if len(r_mult) else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    win_rate = len(wins) / max(len(r_mult), 1) * 100
    worst_r = float(r_mult.min()) if len(r_mult) else 0.0
    if len(display) < 5:
        coaching.append("Keep collecting paper trades. Fewer than five trades is too small to judge the system.")
    if expectancy < 0:
        coaching.append("Expectancy is negative. Prioritize smaller losses, cleaner entries, and skipping weak setups.")
    elif expectancy > 0:
        coaching.append("Expectancy is positive in this sample. Keep checking whether wins came from following the plan, not luck.")
    if worst_r <= -2:
        coaching.append("Your worst loss is larger than -2R. Review whether the stop was respected and whether size was too high.")
    if win_rate < 40 and avg_win <= abs(avg_loss):
        coaching.append("Win rate is low and average wins are not bigger than losses. Tighten entry quality before adding risk.")
    if not review_tags.empty:
        top_tag = str(review_tags.iloc[0]["Tag"])
        coaching.append(f"Most repeated review tag: {top_tag}. Make that the next rule to improve.")
    if not coaching:
        coaching.append("The sample is balanced so far. Keep journaling skipped trades and rule-following, not only winners.")

    equity = display[["Date", "P/L $"]].dropna().sort_values("Date").copy()
    if not equity.empty:
        equity["Cumulative P/L"] = pd.to_numeric(equity["P/L $"], errors="coerce").fillna(0).cumsum()

    return {
        "trades": int(len(display)),
        "expectancy_r": expectancy,
        "avg_win_r": avg_win,
        "avg_loss_r": avg_loss,
        "best_r": float(r_mult.max()) if len(r_mult) else 0.0,
        "worst_r": worst_r,
        "best_stock": str(display.loc[best_index, "Ticker"]) if len(display) else "n/a",
        "worst_stock": str(display.loc[worst_index, "Ticker"]) if len(display) else "n/a",
        "common_setup": str(setup_counts.index[0]) if len(setup_counts) else "n/a",
        "review_tags": review_tags,
        "coaching": coaching[:4],
        "equity": equity,
    }


def render_journal_review_panel(df: pd.DataFrame) -> None:
    review = journal_review_snapshot(df)
    with st.container(border=True):
        st.markdown("**Review coach**")
        st.caption("This reads your paper-trade history for patterns. It is for learning discipline, not predicting future trades.")
        cols = st.columns(4)
        cols[0].metric("Expectancy", f"{review['expectancy_r']:.2f}R", border=True)
        cols[1].metric("Average win", f"{review['avg_win_r']:.2f}R", border=True)
        cols[2].metric("Average loss", f"{review['avg_loss_r']:.2f}R", border=True)
        cols[3].metric("Common setup", str(review["common_setup"]), border=True)

        detail_cols = st.columns([1, 1, 1.2])
        detail_cols[0].metric("Best trade", f"{review['best_r']:.2f}R", str(review["best_stock"]), border=True)
        detail_cols[1].metric("Worst trade", f"{review['worst_r']:.2f}R", str(review["worst_stock"]), border=True)
        with detail_cols[2]:
            for item in review["coaching"]:
                st.caption(item)

        equity = review["equity"]
        if not equity.empty:
            st.line_chart(equity, x="Date", y="Cumulative P/L", height=180)
        tags = review["review_tags"]
        if not tags.empty:
            st.dataframe(
                tags,
                width="stretch",
                hide_index=True,
                column_config={
                    "Tag": st.column_config.TextColumn("Review tag", pinned=True),
                    "Count": st.column_config.ProgressColumn("Count", min_value=0, max_value=max(int(tags["Count"].max()), 1)),
                },
            )


def backtest_strategy(
    ticker: str,
    period: str,
    prefer_live: bool,
    min_gap_pct: float,
    min_rvol: float,
    hold_days: int,
) -> dict[str, Any]:
    history, source = load_history(ticker, period=period, prefer_live=prefer_live)
    df = history.copy()
    df["Prev close"] = df["Close"].shift(1)
    df["Gap %"] = ((df["Close"] - df["Prev close"]) / df["Prev close"]) * 100
    df["Avg volume"] = df["Volume"].shift(1).rolling(20).mean()
    df["RVOL"] = df["Volume"] / df["Avg volume"]
    df["EMA 9"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["EMA 20"] = df["Close"].ewm(span=20, adjust=False).mean()

    trades = []
    for index in range(25, len(df) - hold_days):
        row = df.iloc[index]
        price_ok = 2 <= float(row["Close"]) <= 20
        signal = (
            price_ok
            and float(row["Gap %"]) >= min_gap_pct
            and float(row["RVOL"]) >= min_rvol
            and float(row["Close"]) > float(row["EMA 9"]) > float(row["EMA 20"])
        )
        if not signal:
            continue

        entry = max(float(row["Close"]), float(row["High"]) * 1.001)
        exit_row = df.iloc[index + hold_days]
        exit_price = float(exit_row["Close"])
        stop = max(0.01, float(row["Low"]) * 0.985)
        risk = max(entry - stop, entry * 0.02)
        trades.append(
            {
                "Date": df.index[index].date().isoformat(),
                "Entry": entry,
                "Exit": exit_price,
                "Stop": stop,
                "Gain %": (exit_price - entry) / entry * 100,
                "R multiple": (exit_price - entry) / risk,
                "RVOL": float(row["RVOL"]),
                "Gap %": float(row["Gap %"]),
            }
        )

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        return {
            "source": source,
            "history": df,
            "trades": trades_df,
            "summary": {"Trades": 0, "Win rate": 0.0, "Average gain %": 0.0, "Average R": 0.0},
        }

    wins = (trades_df["Gain %"] > 0).sum()
    return {
        "source": source,
        "history": df,
        "trades": trades_df,
        "summary": {
            "Trades": int(len(trades_df)),
            "Win rate": float(wins / len(trades_df) * 100),
            "Average gain %": float(trades_df["Gain %"].mean()),
            "Average R": float(trades_df["R multiple"].mean()),
        },
    }


def backtest_review_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    trades = result.get("trades", pd.DataFrame())
    if not isinstance(trades, pd.DataFrame) or trades.empty:
        return {
            "expectancy_r": 0.0,
            "avg_win_r": 0.0,
            "avg_loss_r": 0.0,
            "profit_factor": 0.0,
            "max_drawdown_r": 0.0,
            "best_r": 0.0,
            "worst_r": 0.0,
            "strictness": "No signals",
            "equity": pd.DataFrame(columns=["Date", "Cumulative R"]),
            "coaching": [
                "No trades matched the settings. Lower the gap/RVOL filters, use a longer period, or test another stock.",
            ],
        }

    display = trades.copy()
    display["Date"] = pd.to_datetime(display["Date"], errors="coerce")
    r_mult = pd.to_numeric(display["R multiple"], errors="coerce").fillna(0)
    wins = r_mult[r_mult > 0]
    losses = r_mult[r_mult < 0]
    gross_win = float(wins.sum()) if len(wins) else 0.0
    gross_loss = abs(float(losses.sum())) if len(losses) else 0.0
    profit_factor = gross_win / gross_loss if gross_loss else gross_win
    cumulative = r_mult.cumsum()
    running_peak = cumulative.cummax()
    drawdown = cumulative - running_peak
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0
    trade_count = int(len(display))
    if trade_count < 4:
        strictness = "Very selective"
    elif trade_count <= 18:
        strictness = "Balanced sample"
    else:
        strictness = "Very active"

    coaching: list[str] = []
    expectancy = float(r_mult.mean()) if len(r_mult) else 0.0
    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0
    win_rate = len(wins) / max(len(r_mult), 1) * 100
    if expectancy > 0:
        coaching.append("This test has positive average R. Next check whether the trade count is large enough to trust.")
    else:
        coaching.append("This test has negative average R. Tighten entries, reduce hold time, or raise quality filters.")
    if trade_count < 5:
        coaching.append("Sample size is small. Treat this as a clue, not proof.")
    if trade_count > 25:
        coaching.append("This rule fires often. Add a chart-quality or news filter before trusting it.")
    if profit_factor < 1 and trade_count:
        coaching.append("Profit factor is under 1. Losses are larger than wins in this sample.")
    if max_drawdown <= -3:
        coaching.append("Drawdown went past -3R. A beginner should lower risk or improve filters before using this rule.")
    if win_rate < 40 and avg_win <= abs(avg_loss):
        coaching.append("Low win rate needs bigger winners than losers. This sample does not show that yet.")

    equity = display[["Date"]].copy()
    equity["Cumulative R"] = cumulative
    return {
        "expectancy_r": expectancy,
        "avg_win_r": avg_win,
        "avg_loss_r": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown_r": max_drawdown,
        "best_r": float(r_mult.max()) if len(r_mult) else 0.0,
        "worst_r": float(r_mult.min()) if len(r_mult) else 0.0,
        "strictness": strictness,
        "equity": equity,
        "coaching": list(dict.fromkeys(coaching))[:4],
    }


def render_backtest_review_panel(result: dict[str, Any]) -> None:
    review = backtest_review_snapshot(result)
    with st.container(border=True):
        st.markdown("**Backtest read**")
        st.caption("A simplified historical check. Use it to learn whether a rule is worth studying, not to promise future results.")
        cols = st.columns(4)
        cols[0].metric("Expectancy", f"{review['expectancy_r']:.2f}R", border=True)
        cols[1].metric("Profit factor", f"{review['profit_factor']:.2f}", border=True)
        cols[2].metric("Max drawdown", f"{review['max_drawdown_r']:.2f}R", border=True)
        cols[3].metric("Signal pace", str(review["strictness"]), border=True)
        cols = st.columns([1, 1, 1.4])
        cols[0].metric("Best trade", f"{review['best_r']:.2f}R", border=True)
        cols[1].metric("Worst trade", f"{review['worst_r']:.2f}R", border=True)
        with cols[2]:
            for item in review["coaching"]:
                st.caption(item)
        equity = review["equity"]
        if not equity.empty:
            st.line_chart(equity, x="Date", y="Cumulative R", height=180)


def theme_palette(mode: str | None = None) -> dict[str, str]:
    mode = (mode or st.session_state.get("display_mode", "Dark")).lower()
    if mode == "light":
        return {
            "app_bg": "#F7F8FA",
            "panel": "#FFFFFF",
            "panel_alt": "#F1F5F9",
            "border": "#D9E0E8",
            "text": "#101418",
            "muted": "#475569",
            "muted_soft": "#64748B",
            "shadow": "rgba(15, 23, 42, 0.08)",
            "hero": "linear-gradient(135deg, #FFFFFF 0%, #F1F8F4 58%, #EFF6FF 100%)",
            "up": "#008F2D",
            "up_bright": "#00A854",
            "down": "#D92D20",
            "blue": "#2563EB",
            "cyan": "#0891B2",
            "violet": "#7C3AED",
            "orange": "#B45309",
            "grid": "#DDE5EE",
            "chart_grid": "rgba(148, 163, 184, 0.16)",
        }
    return {
        "app_bg": "#090C10",
        "panel": "#0B1117",
        "panel_alt": "#101821",
        "border": "#293546",
        "text": "#F3F7FA",
        "muted": "#B7C2D0",
        "muted_soft": "#A8B3C2",
        "shadow": "rgba(0, 0, 0, 0.28)",
        "hero": "linear-gradient(135deg, #121A24 0%, #0B1118 72%)",
        "up": "#00C805",
        "up_bright": "#00C805",
        "down": "#FF375F",
        "blue": "#38BDF8",
        "cyan": "#22D3EE",
        "violet": "#A78BFA",
        "orange": "#F59E0B",
        "grid": "#223041",
        "chart_grid": "rgba(148, 163, 184, 0.09)",
    }


def display_mode_control() -> str:
    options = ["Dark", "Light"]
    default = st.session_state.get("display_mode", "Dark")
    index = options.index(default) if default in options else 0
    with st.sidebar:
        mode = st.selectbox(
            "Display mode",
            options,
            index=index,
            key="display_mode",
        )
    return str(mode or default)


def apply_style(mode: str | None = None) -> None:
    palette = theme_palette(mode)
    st.html(
        clean_html_markup(
        f"""
        <style>
        :root {{
            --msa-app-bg: {palette["app_bg"]};
            --msa-panel: {palette["panel"]};
            --msa-panel-alt: {palette["panel_alt"]};
            --msa-border: {palette["border"]};
            --msa-text: {palette["text"]};
            --msa-muted: {palette["muted"]};
            --msa-muted-soft: {palette["muted_soft"]};
            --msa-shadow: {palette["shadow"]};
            --msa-up: {palette["up"]};
            --msa-down: {palette["down"]};
            --msa-blue: {palette["blue"]};
            --msa-orange: {palette["orange"]};
        }}
        .stApp {{background: var(--msa-app-bg);}}
        .block-container {{max-width: 1320px; padding-top: 1.15rem; padding-bottom: 3rem;}}
        h1, h2, h3 {{letter-spacing: 0; color: var(--msa-text);}}
        [data-testid="stMetric"] {{
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 15px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
        }}
        div[data-testid="stMetricLabel"] {{color: var(--msa-muted-soft);}}
        div[data-testid="stMetricValue"] {{font-weight: 750; color: var(--msa-text);}}
        div[data-testid="stMetricDelta"] {{font-weight: 650;}}
        div[data-testid="stDataFrame"] {{border: 1px solid var(--msa-border); border-radius: 8px; overflow: hidden;}}
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {{
            color: var(--msa-muted) !important;
        }}
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {{
            color: var(--msa-text);
        }}
        .stAlert,
        [data-testid="stAlert"] {{
            border-radius: 8px;
            border: 1px solid var(--msa-border);
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            color: var(--msa-text);
        }}
        .stAlert *,
        [data-testid="stAlert"] *,
        [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
            color: var(--msa-text) !important;
            font-weight: 650;
        }}
        .msa-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 0;
            background:
                radial-gradient(circle at 18% -10%, rgba(0, 200, 5, 0.20), transparent 30%),
                radial-gradient(circle at 85% 20%, rgba(56, 189, 248, 0.18), transparent 34%),
                {palette["hero"]};
            box-shadow: 0 24px 60px var(--msa-shadow);
        }}
        .msa-hero:after {{
            content: "";
            position: absolute;
            inset: auto -20% -48px -20%;
            height: 96px;
            background:
                linear-gradient(90deg, transparent 0%, rgba(0, 168, 84, 0.25) 35%, rgba(37, 99, 235, 0.22) 55%, transparent 100%);
            animation: msa-pulse 5.5s ease-in-out infinite;
            transform: skewY(-3deg);
        }}
        @keyframes msa-pulse {{
            0%, 100% {{transform: translateX(-18%) skewY(-3deg); opacity: .55;}}
            50% {{transform: translateX(18%) skewY(-3deg); opacity: .95;}}
        }}
        .msa-hero-grid {{
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: minmax(260px, 1fr) minmax(250px, 330px);
            gap: 18px;
            align-items: center;
            padding: 26px 28px;
        }}
        .msa-logo-lockup {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .msa-brand-mark {{
            width: 54px;
            height: 54px;
            flex: 0 0 54px;
            filter: drop-shadow(0 12px 22px rgba(0, 200, 5, 0.18));
        }}
        .msa-logo-copy span {{
            display: block;
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 820;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .msa-logo-copy strong {{
            display: block;
            color: var(--msa-text);
            font-size: 1.02rem;
            font-weight: 880;
            line-height: 1.05;
        }}
        .msa-hero h1 {{margin: 0 0 8px 0; font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.02;}}
        .msa-hero p {{max-width: 820px; margin: 0; color: var(--msa-muted); font-size: 1.02rem;}}
        .msa-hero-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 14px;
        }}
        .msa-hero-badge {{
            border: 1px solid var(--msa-border);
            border-radius: 999px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            font-size: .78rem;
            font-weight: 760;
            padding: 6px 10px;
        }}
        .msa-companion-card {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-top: 3px solid var(--msa-character-accent, var(--msa-blue));
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(0, 200, 5, .10), transparent 38%),
                linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            padding: 13px;
            box-shadow: 0 18px 38px var(--msa-shadow);
        }}
        .msa-companion-card:before {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(120deg, transparent 0%, rgba(56, 189, 248, .10) 46%, transparent 74%);
            transform: translateX(-100%);
            animation: msa-scanline 6.5s ease-in-out infinite;
        }}
        @keyframes msa-scanline {{
            0%, 52%, 100% {{transform: translateX(-100%); opacity: 0;}}
            62% {{opacity: 1;}}
            84% {{transform: translateX(100%); opacity: 0;}}
        }}
        .msa-companion-inner {{
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 86px 1fr;
            gap: 12px;
            align-items: center;
        }}
        .msa-companion-inner-text-only {{
            grid-template-columns: 1fr;
        }}
        .msa-companion-sidebar .msa-companion-inner {{
            grid-template-columns: 72px 1fr;
        }}
        .msa-companion-bot {{
            width: 86px;
            height: 86px;
            filter: drop-shadow(0 14px 26px rgba(0, 0, 0, .22));
        }}
        .msa-companion-sidebar .msa-companion-bot {{
            width: 72px;
            height: 72px;
        }}
        .msa-companion-avatar {{
            display: block;
            width: 86px;
            height: 86px;
            object-fit: contain;
            filter: drop-shadow(0 14px 26px rgba(0, 0, 0, .22));
        }}
        .msa-companion-sidebar .msa-companion-avatar {{
            width: 72px;
            height: 72px;
        }}
        .msa-companion-picker {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            padding: 10px;
            margin: 8px 0 12px 0;
            text-align: center;
        }}
        .msa-companion-picker-title {{
            color: var(--msa-text);
            font-size: .88rem;
            font-weight: 860;
            margin-top: 5px;
        }}
        .msa-companion-picker-copy {{
            color: var(--msa-muted);
            font-size: .76rem;
            line-height: 1.25;
            margin-top: 3px;
        }}
        .msa-companion-kicker {{
            color: var(--msa-muted-soft);
            font-size: .68rem;
            font-weight: 820;
            letter-spacing: .06em;
            text-transform: uppercase;
        }}
        .msa-companion-title {{
            color: var(--msa-text);
            font-size: 1.02rem;
            font-weight: 880;
            line-height: 1.08;
            margin-top: 4px;
        }}
        .msa-companion-message {{
            color: var(--msa-muted);
            font-size: .82rem;
            line-height: 1.3;
            margin-top: 6px;
        }}
        .msa-companion-chip {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border: 1px solid var(--msa-border);
            border-radius: 999px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            font-size: .72rem;
            font-weight: 780;
            padding: 5px 8px;
            margin-top: 9px;
        }}
        .msa-sidebar-brand {{
            margin: 10px 0 12px 0;
        }}
        .msa-sidebar-logo {{
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 10px 10px 9px;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
        }}
        .msa-sidebar-logo .msa-brand-mark {{
            width: 38px;
            height: 38px;
            flex-basis: 38px;
        }}
        .msa-sidebar-logo strong {{
            display: block;
            color: var(--msa-text);
            font-size: .9rem;
            font-weight: 860;
            line-height: 1.05;
        }}
        .msa-sidebar-logo span {{
            display: block;
            color: var(--msa-muted-soft);
            font-size: .68rem;
            font-weight: 760;
            margin-top: 3px;
        }}
        .msa-status-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 12px;
            margin: 14px 0 16px 0;
        }}
        .msa-status-card {{
            border: 1px solid var(--msa-border);
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
        }}
        .msa-label {{font-size: .78rem; color: var(--msa-muted-soft); text-transform: uppercase; letter-spacing: .04em;}}
        .msa-value {{font-size: 1.4rem; font-weight: 750; color: var(--msa-text); margin-top: 4px;}}
        .msa-good {{border-left: 4px solid var(--msa-up);}}
        .msa-hot {{border-left: 4px solid var(--msa-orange);}}
        .msa-calm {{border-left: 4px solid var(--msa-blue);}}
        .msa-danger {{border-left: 4px solid var(--msa-down);}}
        .msa-command-strip {{
            display: grid;
            grid-template-columns: minmax(280px, 1.45fr) repeat(4, minmax(130px, .72fr));
            gap: 10px;
            margin: 12px 0 14px 0;
        }}
        .msa-command-main,
        .msa-command-stat {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 16px 34px var(--msa-shadow);
        }}
        .msa-command-main {{
            position: relative;
            overflow: hidden;
            padding: 14px 15px;
        }}
        .msa-command-main:before {{
            content: "";
            position: absolute;
            inset: 0;
            border-left: 5px solid var(--msa-blue);
            pointer-events: none;
        }}
        .msa-command-main.msa-command-ready:before {{border-left-color: var(--msa-up);}}
        .msa-command-main.msa-command-watch:before {{border-left-color: var(--msa-orange);}}
        .msa-command-main.msa-command-danger:before {{border-left-color: var(--msa-down);}}
        .msa-command-kicker,
        .msa-command-stat-label {{
            color: var(--msa-muted-soft);
            font-size: .68rem;
            font-weight: 840;
            letter-spacing: .06em;
            text-transform: uppercase;
        }}
        .msa-command-title {{
            color: var(--msa-text);
            font-size: 1.08rem;
            font-weight: 900;
            line-height: 1.1;
            margin: 4px 0 5px 0;
        }}
        .msa-command-copy {{
            color: var(--msa-muted);
            font-size: .86rem;
            line-height: 1.32;
        }}
        .msa-command-stat {{
            padding: 12px 13px;
            min-width: 0;
        }}
        .msa-command-stat-value {{
            color: var(--msa-text);
            font-size: 1.02rem;
            font-weight: 880;
            line-height: 1.1;
            margin-top: 5px;
            overflow-wrap: anywhere;
        }}
        .msa-command-stat-detail {{
            color: var(--msa-muted);
            font-size: .74rem;
            line-height: 1.25;
            margin-top: 4px;
        }}
        .msa-glossary-empty {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 14px;
        }}
        .msa-provider-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 10px;
            margin: 10px 0 8px 0;
        }}
        .msa-provider-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            padding: 12px 13px;
            min-height: 126px;
            box-shadow: 0 12px 28px var(--msa-shadow);
        }}
        .msa-provider-card:before {{
            content: "";
            display: block;
            height: 4px;
            width: 44px;
            border-radius: 999px;
            background: var(--msa-muted-soft);
            margin-bottom: 10px;
        }}
        .msa-provider-ready:before {{background: var(--msa-up);}}
        .msa-provider-watch:before {{background: var(--msa-orange);}}
        .msa-provider-info:before {{background: var(--msa-blue);}}
        .msa-provider-name {{
            color: var(--msa-text);
            font-weight: 820;
            font-size: 1rem;
            line-height: 1.1;
        }}
        .msa-provider-state {{
            color: var(--msa-muted-soft);
            font-size: .76rem;
            font-weight: 760;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        .msa-provider-detail {{
            color: var(--msa-muted);
            font-size: .84rem;
            line-height: 1.32;
            margin-top: 7px;
        }}
        .msa-source-flow {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 10px 12px;
            line-height: 1.35;
            margin-top: 8px;
        }}
        .msa-cockpit {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(34, 211, 238, 0.10), transparent 34%),
                linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 18px 42px var(--msa-shadow);
            padding: 15px;
            margin: 10px 0 14px 0;
        }}
        .msa-cockpit-head {{
            display: grid;
            grid-template-columns: minmax(220px, 1fr) minmax(240px, 1.45fr);
            gap: 12px;
            align-items: stretch;
            margin-bottom: 12px;
        }}
        .msa-cockpit-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 800;
            text-transform: uppercase;
        }}
        .msa-cockpit-title {{
            color: var(--msa-text);
            font-size: clamp(1.45rem, 2.8vw, 2.1rem);
            font-weight: 880;
            line-height: 1.04;
            margin-top: 5px;
        }}
        .msa-cockpit-detail {{
            color: var(--msa-muted);
            font-size: .88rem;
            line-height: 1.34;
            margin-top: 7px;
        }}
        .msa-cockpit-next {{
            border: 1px solid var(--msa-border);
            border-left: 4px solid var(--msa-blue);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px 13px;
        }}
        .msa-cockpit-next-ready {{border-left-color: var(--msa-up);}}
        .msa-cockpit-next-watch {{border-left-color: var(--msa-orange);}}
        .msa-cockpit-next-danger {{border-left-color: var(--msa-down);}}
        .msa-cockpit-next-title {{
            color: var(--msa-text);
            font-size: 1.1rem;
            font-weight: 840;
            line-height: 1.08;
        }}
        .msa-cockpit-next-copy {{
            color: var(--msa-muted);
            font-size: .84rem;
            line-height: 1.32;
            margin-top: 7px;
        }}
        .msa-cockpit-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(158px, 1fr));
            gap: 9px;
        }}
        .msa-cockpit-step {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 11px 12px;
            min-height: 116px;
        }}
        .msa-cockpit-ready {{border-top: 4px solid var(--msa-up);}}
        .msa-cockpit-watch {{border-top: 4px solid var(--msa-orange);}}
        .msa-cockpit-danger {{border-top: 4px solid var(--msa-down);}}
        .msa-cockpit-neutral {{border-top: 4px solid var(--msa-blue);}}
        .msa-cockpit-step-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}
        .msa-cockpit-step-number {{
            display: grid;
            place-items: center;
            width: 26px;
            height: 26px;
            border-radius: 999px;
            background: var(--msa-panel-alt);
            border: 1px solid var(--msa-border);
            color: var(--msa-muted-soft);
            font-size: .78rem;
            font-weight: 820;
        }}
        .msa-cockpit-step-state {{
            color: var(--msa-muted-soft);
            font-size: .68rem;
            font-weight: 780;
            text-transform: uppercase;
        }}
        .msa-cockpit-step-title {{
            color: var(--msa-text);
            font-weight: 840;
            line-height: 1.08;
            margin-top: 8px;
        }}
        .msa-cockpit-step-detail {{
            color: var(--msa-muted);
            font-size: .78rem;
            line-height: 1.25;
            margin-top: 6px;
        }}
        .msa-cockpit-blockers {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 10px 12px;
            line-height: 1.35;
            margin-top: 10px;
        }}
        .msa-pulse {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(16, 185, 129, 0.10), transparent 34%),
                linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 18px 42px var(--msa-shadow);
            padding: 15px;
            margin: 10px 0 14px 0;
        }}
        .msa-pulse-head {{
            display: grid;
            grid-template-columns: minmax(230px, .9fr) minmax(260px, 1.35fr);
            gap: 12px;
            align-items: stretch;
        }}
        .msa-pulse-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 800;
            text-transform: uppercase;
        }}
        .msa-pulse-title {{
            color: var(--msa-text);
            font-size: clamp(1.35rem, 2.7vw, 2rem);
            font-weight: 880;
            line-height: 1.06;
            margin-top: 5px;
        }}
        .msa-pulse-copy {{
            color: var(--msa-muted);
            font-size: .86rem;
            line-height: 1.34;
            margin-top: 7px;
        }}
        .msa-pulse-next {{
            border: 1px solid var(--msa-border);
            border-left: 4px solid var(--msa-blue);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px 13px;
        }}
        .msa-pulse-next-ready {{border-left-color: var(--msa-up);}}
        .msa-pulse-next-watch {{border-left-color: var(--msa-orange);}}
        .msa-pulse-next-danger {{border-left-color: var(--msa-down);}}
        .msa-pulse-next-neutral {{border-left-color: var(--msa-blue);}}
        .msa-pulse-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(172px, 1fr));
            gap: 9px;
            margin-top: 12px;
        }}
        .msa-pulse-stat {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 11px 12px;
            min-height: 96px;
        }}
        .msa-pulse-stat-ready {{border-top: 4px solid var(--msa-up);}}
        .msa-pulse-stat-watch {{border-top: 4px solid var(--msa-orange);}}
        .msa-pulse-stat-danger {{border-top: 4px solid var(--msa-down);}}
        .msa-pulse-stat-neutral {{border-top: 4px solid var(--msa-blue);}}
        .msa-pulse-stat-label {{
            color: var(--msa-muted-soft);
            font-size: .7rem;
            font-weight: 800;
            text-transform: uppercase;
        }}
        .msa-pulse-stat-value {{
            color: var(--msa-text);
            font-size: clamp(1.35rem, 2.2vw, 1.85rem);
            font-weight: 840;
            line-height: 1.06;
            margin-top: 6px;
        }}
        .msa-pulse-stat-detail {{
            color: var(--msa-muted);
            font-size: .78rem;
            line-height: 1.25;
            margin-top: 6px;
        }}
        .msa-pulse-flags {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-muted);
            padding: 10px 12px;
            line-height: 1.35;
            margin-top: 10px;
        }}
        .msa-pulse-flags b {{color: var(--msa-text);}}
        .msa-level-board {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 10px 0 14px 0;
        }}
        .msa-level-card {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            border-radius: 8px;
            padding: 15px 16px 14px 16px;
            box-shadow: 0 18px 36px var(--msa-shadow);
            min-height: 122px;
        }}
        .msa-level-card:before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--msa-muted-soft);
        }}
        .msa-level-profit:before {{background: var(--msa-up);}}
        .msa-level-danger:before {{background: var(--msa-down);}}
        .msa-level-neutral:before {{background: var(--msa-blue);}}
        .msa-level-label {{
            color: var(--msa-muted-soft);
            font-size: .78rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .msa-level-value {{
            color: var(--msa-text);
            font-size: clamp(1.8rem, 3vw, 2.45rem);
            font-weight: 820;
            line-height: 1.04;
            margin-top: 8px;
            letter-spacing: 0;
        }}
        .msa-level-profit .msa-level-value {{color: var(--msa-up);}}
        .msa-level-danger .msa-level-value {{color: var(--msa-down);}}
        .msa-level-detail {{
            color: var(--msa-muted);
            margin-top: 8px;
            font-size: .86rem;
            line-height: 1.25;
        }}
        .msa-compact-header {{
            margin: 0 0 10px 0;
            padding: 0;
        }}
        .msa-compact-header h1 {{
            margin: 0;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            line-height: 1.05;
            color: var(--msa-text);
        }}
        .msa-compact-header p {{
            margin: 5px 0 0 0;
            color: var(--msa-muted);
            font-size: .95rem;
        }}
        .msa-compact-header small {{
            display: block;
            margin-top: 4px;
            color: var(--msa-muted-soft);
            font-size: .78rem;
            line-height: 1.25;
        }}
        .msa-chart-stat-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin: 10px 0 2px 0;
        }}
        .msa-chart-stat-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 10px 12px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 12px 26px var(--msa-shadow);
        }}
        .msa-chart-stat-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 750;
            text-transform: uppercase;
        }}
        .msa-chart-stat-value {{
            color: var(--msa-text);
            font-size: 1.15rem;
            line-height: 1.1;
            font-weight: 800;
            margin-top: 5px;
        }}
        .msa-chart-stat-detail {{
            color: var(--msa-muted);
            font-size: .8rem;
            margin-top: 4px;
        }}
        .msa-chart-stat-up .msa-chart-stat-value {{color: var(--msa-up);}}
        .msa-chart-stat-down .msa-chart-stat-value {{color: var(--msa-down);}}
        .msa-readiness-command {{
            display: grid;
            grid-template-columns: minmax(180px, .8fr) minmax(260px, 1.4fr) minmax(160px, .8fr);
            gap: 12px;
            align-items: stretch;
            margin: 8px 0 12px 0;
        }}
        .msa-readiness-tile {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 13px 14px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 14px 28px var(--msa-shadow);
        }}
        .msa-readiness-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-readiness-primary {{
            color: var(--msa-text);
            font-size: 1.45rem;
            font-weight: 840;
            line-height: 1.05;
            margin-top: 5px;
        }}
        .msa-readiness-detail {{
            color: var(--msa-muted);
            font-size: .84rem;
            line-height: 1.28;
            margin-top: 7px;
        }}
        .msa-readiness-ready {{border-left: 4px solid var(--msa-up);}}
        .msa-readiness-watch {{border-left: 4px solid var(--msa-orange);}}
        .msa-readiness-hold {{border-left: 4px solid var(--msa-muted-soft);}}
        .msa-readiness-danger {{border-left: 4px solid var(--msa-down);}}
        .msa-check-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(142px, 1fr));
            gap: 9px;
        }}
        .msa-check-card {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 10px 11px;
            background: var(--msa-panel);
        }}
        .msa-check-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-check-value {{
            color: var(--msa-text);
            font-size: 1rem;
            font-weight: 760;
            margin-top: 4px;
        }}
        .msa-check-ok {{border-left: 4px solid var(--msa-up);}}
        .msa-check-wait {{border-left: 4px solid var(--msa-orange);}}
        .msa-ai-command {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0 14px 0;
            background:
                linear-gradient(135deg, rgba(0, 200, 5, 0.08), transparent 36%),
                linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 18px 38px var(--msa-shadow);
        }}
        .msa-ai-command:before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--msa-muted-soft);
        }}
        .msa-ai-ready:before {{background: var(--msa-up);}}
        .msa-ai-watch:before {{background: var(--msa-orange);}}
        .msa-ai-danger:before {{background: var(--msa-down);}}
        .msa-ai-sell:before {{background: var(--msa-blue);}}
        .msa-ai-header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 14px;
            margin-bottom: 12px;
        }}
        .msa-ai-topline {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .msa-ai-signal-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 10px 12px;
            min-width: 210px;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .035);
        }}
        .msa-ai-light {{
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 999px;
            background: rgba(148, 163, 184, .10);
            border: 1px solid var(--msa-border);
        }}
        .msa-ai-light span {{
            width: 22px;
            height: 22px;
            border-radius: 999px;
            background: var(--msa-muted-soft);
            box-shadow: 0 0 0 5px rgba(148, 163, 184, .11), 0 0 20px rgba(148, 163, 184, .46);
        }}
        .msa-ai-signal-ready .msa-ai-light span {{
            background: var(--msa-up);
            box-shadow: 0 0 0 5px rgba(0, 200, 5, .13), 0 0 24px rgba(0, 200, 5, .74);
        }}
        .msa-ai-signal-danger .msa-ai-light span,
        .msa-ai-signal-watch .msa-ai-light span,
        .msa-ai-signal-hold .msa-ai-light span {{
            background: var(--msa-down);
            box-shadow: 0 0 0 5px rgba(255, 55, 95, .13), 0 0 24px rgba(255, 55, 95, .72);
        }}
        .msa-ai-signal-sell .msa-ai-light span {{
            background: var(--msa-blue);
            box-shadow: 0 0 0 5px rgba(56, 189, 248, .16), 0 0 24px rgba(56, 189, 248, .78);
        }}
        .msa-ai-signal-kicker {{
            color: var(--msa-muted);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .07em;
            text-transform: uppercase;
        }}
        .msa-ai-signal-action {{
            color: var(--msa-text);
            font-size: 1.03rem;
            font-weight: 900;
            line-height: 1.1;
            margin-top: 3px;
        }}
        .msa-ai-signal-detail {{
            color: var(--msa-muted);
            font-size: .76rem;
            font-weight: 650;
            line-height: 1.25;
            margin-top: 3px;
        }}
        .msa-ai-kicker {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 780;
            letter-spacing: .04em;
            text-transform: uppercase;
        }}
        .msa-ai-title {{
            color: var(--msa-text);
            font-size: clamp(1.6rem, 3vw, 2.25rem);
            font-weight: 860;
            line-height: 1.02;
            margin-top: 4px;
        }}
        .msa-ai-detail {{
            color: var(--msa-text);
            font-size: .92rem;
            line-height: 1.36;
            margin-top: 7px;
            max-width: 860px;
            font-weight: 620;
        }}
        .msa-ai-score {{
            min-width: 116px;
            text-align: right;
            color: var(--msa-text);
            font-weight: 820;
        }}
        .msa-ai-score span {{
            display: block;
            color: var(--msa-muted-soft);
            font-size: .74rem;
            font-weight: 760;
            text-transform: uppercase;
        }}
        .msa-ai-level-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }}
        .msa-ai-level {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px;
            min-height: 104px;
        }}
        .msa-ai-level-label {{
            color: var(--msa-muted-soft);
            font-size: .72rem;
            font-weight: 780;
            text-transform: uppercase;
        }}
        .msa-ai-level-value {{
            color: var(--msa-text);
            font-size: clamp(1.35rem, 2.4vw, 1.95rem);
            font-weight: 860;
            line-height: 1.06;
            margin-top: 6px;
        }}
        .msa-ai-level-profit .msa-ai-level-value {{color: var(--msa-up);}}
        .msa-ai-level-danger .msa-ai-level-value {{color: var(--msa-down);}}
        .msa-ai-level-note {{
            color: var(--msa-text);
            font-size: .78rem;
            line-height: 1.25;
            margin-top: 6px;
            font-weight: 620;
        }}
        .msa-plan-ladder {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 10px;
            margin: 10px 0 14px 0;
        }}
        .msa-plan-step {{
            position: relative;
            min-height: 148px;
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: linear-gradient(180deg, var(--msa-panel) 0%, var(--msa-panel-alt) 100%);
            box-shadow: 0 14px 30px var(--msa-shadow);
            padding: 13px 13px 12px 13px;
            overflow: hidden;
        }}
        .msa-plan-step:before {{
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 4px;
            background: var(--msa-muted-soft);
        }}
        .msa-plan-ready:before {{background: var(--msa-up);}}
        .msa-plan-watch:before {{background: var(--msa-orange);}}
        .msa-plan-danger:before {{background: var(--msa-down);}}
        .msa-plan-neutral:before {{background: var(--msa-blue);}}
        .msa-plan-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }}
        .msa-plan-number {{
            display: grid;
            place-items: center;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            background: var(--msa-panel);
            border: 1px solid var(--msa-border);
            color: var(--msa-muted-soft);
            font-size: .8rem;
            font-weight: 820;
        }}
        .msa-plan-state {{
            color: var(--msa-muted-soft);
            font-size: .7rem;
            font-weight: 780;
            text-transform: uppercase;
        }}
        .msa-plan-title {{
            color: var(--msa-text);
            font-size: 1.05rem;
            font-weight: 840;
            line-height: 1.08;
            margin-top: 10px;
        }}
        .msa-plan-value {{
            color: var(--msa-text);
            font-size: clamp(1.35rem, 2.2vw, 1.82rem);
            font-weight: 870;
            line-height: 1.05;
            margin-top: 6px;
        }}
        .msa-plan-ready .msa-plan-value {{color: var(--msa-up);}}
        .msa-plan-danger .msa-plan-value {{color: var(--msa-down);}}
        .msa-plan-watch .msa-plan-value {{color: var(--msa-orange);}}
        .msa-plan-detail {{
            color: var(--msa-text);
            font-size: .8rem;
            line-height: 1.28;
            margin-top: 7px;
            font-weight: 610;
        }}
        .msa-plan-rule {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-text);
            padding: 10px 12px;
            margin: 0 0 14px 0;
            line-height: 1.35;
            font-weight: 640;
        }}
        .msa-ai-list {{
            border: 1px solid var(--msa-border);
            border-radius: 8px;
            background: var(--msa-panel);
            padding: 12px 13px;
            height: 100%;
        }}
        .msa-ai-list strong {{
            display: block;
            color: var(--msa-text);
            margin-bottom: 7px;
        }}
        .msa-ai-list ul {{
            margin: 0;
            padding-left: 18px;
            color: var(--msa-text);
        }}
        .msa-ai-list li {{
            margin: 5px 0;
            line-height: 1.32;
            color: var(--msa-text);
            font-weight: 610;
        }}
        .msa-ai-plain {{
            border: 1px solid var(--msa-border);
            border-left: 4px solid var(--msa-blue);
            border-radius: 8px;
            background: var(--msa-panel);
            color: var(--msa-text);
            padding: 11px 13px;
            margin-top: 12px;
            line-height: 1.34;
            font-weight: 640;
        }}
        @media (max-width: 900px) {{
            .msa-cockpit-head {{
                grid-template-columns: 1fr;
            }}
            .msa-pulse-head {{
                grid-template-columns: 1fr;
            }}
            .msa-readiness-command {{
                grid-template-columns: 1fr;
            }}
            .msa-ai-header {{
                display: block;
            }}
            .msa-ai-score {{
                text-align: left;
                margin-top: 10px;
            }}
            .msa-ai-topline {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .msa-ai-signal-card {{
                width: 100%;
            }}
            .msa-hero-grid {{
                grid-template-columns: 1fr;
                padding: 22px;
            }}
            .msa-command-strip {{
                grid-template-columns: 1fr 1fr;
            }}
            .msa-command-main {{
                grid-column: 1 / -1;
            }}
            .msa-companion-inner {{
                grid-template-columns: 72px 1fr;
            }}
        }}
        </style>
        """
        ),
    )


def brand_mark_svg() -> str:
    return clean_html_markup(
        """
    <svg class="msa-brand-mark" viewBox="0 0 72 72" role="img" aria-label="Trading for Dummys 101 logo" xmlns="http://www.w3.org/2000/svg">
      <rect x="6" y="6" width="60" height="60" rx="14" fill="#00C805"/>
      <path d="M18 48L30 36L39 42L54 22" fill="none" stroke="#081018" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M54 22V36" fill="none" stroke="#081018" stroke-width="5" stroke-linecap="round"/>
      <circle cx="55" cy="18" r="7" fill="#38BDF8" stroke="#081018" stroke-width="3"/>
      <text x="17" y="58" fill="#081018" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="900">101</text>
    </svg>
    """
    )


def companion_names() -> list[str]:
    return list(COMPANION_PROFILES)


def selected_companion_name() -> str:
    current = str(st.session_state.get("ai_companion", "Scout") or "Scout")
    return current if current in COMPANION_PROFILES else "Scout"


def companion_profile(name: str | None = None) -> dict[str, str]:
    profile_name = name if name in COMPANION_PROFILES else selected_companion_name()
    profile = dict(COMPANION_PROFILES[profile_name])
    profile["name"] = profile_name
    return profile


def companion_asset_path(profile: dict[str, str] | None = None) -> Path:
    active = profile or companion_profile()
    return ASSETS_DIR / str(active["asset"])


def companion_svg_text(profile: dict[str, str] | None = None) -> str:
    path = companion_asset_path(profile)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def companion_avatar_src(profile: dict[str, str] | None = None) -> str:
    svg = companion_svg_text(profile)
    if not svg:
        return ""
    return "data:image/svg+xml;utf8," + url_quote(svg)


def companion_avatar_html(profile: dict[str, str] | None = None) -> str:
    active = profile or companion_profile()
    src = companion_avatar_src(active)
    if not src:
        return ""
    name = html.escape(str(active["name"]))
    return f'<img class="msa-companion-avatar" alt="{name} character" src="{src}">'


def companion_copy(analysis: dict[str, Any] | None = None, profile: dict[str, str] | None = None) -> tuple[str, str, str]:
    active = profile or companion_profile()
    character = str(active["name"])
    if analysis:
        ticker = str(analysis.get("Ticker") or "Stock")
        status = live_status(analysis)
        entry = str(analysis.get("Entry trigger") or "entry trigger")
        stop = str(analysis.get("Stop") or "planned stop")
        target = str(analysis.get("Target 1") or "target 1")
        confidence = data_confidence_summary(analysis).get("label", "data check")

        if status == "Breakout trigger":
            return (
                f"{character} sees a trigger",
                f"{ticker} is at the planned trigger. Check volume, spread, news, and risk to {stop} before approving any paper trade.",
                f"{ticker} - trigger active - {character} - {confidence}",
            )
        if status == "In buy zone":
            return (
                f"{character} sees the buy zone",
                f"{ticker} is inside the planned zone. Wait for confirmation at {entry}; first planned trim is {target}.",
                f"{ticker} - buy zone - {character} - {confidence}",
            )
        if status == "Near buy zone":
            return (
                f"{character} says wait for proof",
                f"{ticker} is close, but the cleaner plan is still confirmation at {entry} with risk controlled near {stop}.",
                f"{ticker} - near zone - {character} - {confidence}",
            )
        if status == "Below stop":
            return (
                f"{character} says rebuild",
                f"{ticker} is below the risk line. Treat the old plan as invalid until fresh candles create a new setup.",
                f"{ticker} - below stop - {character} - {confidence}",
            )
        if status == "Momentum active":
            return (
                f"{character} sees momentum",
                f"{ticker} has active momentum. Do not chase; use the chart to wait for the next clean trigger and defined stop.",
                f"{ticker} - momentum - {character} - {confidence}",
            )
        return (
            f"{character} is watching",
            f"{ticker} is on the board, but it still needs a cleaner trigger, stronger data, or better risk/reward before approval.",
            f"{ticker} - {status} - {character} - {confidence}",
        )

    selected = normalize_user_symbol(st.session_state.get("selected_ticker", ""))
    stock = selected or "your top stock"
    return (
        f"Meet {character}",
        f"{character} follows {stock}, keeps the next step readable, and reminds beginners to verify data, entry, stop, target, and news before any paper approval.",
        f"{character} - {active['tagline']} - paper trading only",
    )


def companion_card_html(
    title: str,
    message: str,
    chip: str,
    context: str = "card",
    profile: dict[str, str] | None = None,
    include_avatar: bool = True,
) -> str:
    active = profile or companion_profile()
    safe_context = "".join(ch for ch in str(context).lower() if ch.isalnum() or ch in {"-", "_"}) or "card"
    avatar = companion_avatar_html(active) if include_avatar else ""
    inner_class = "msa-companion-inner" if include_avatar else "msa-companion-inner msa-companion-inner-text-only"
    return clean_html_markup(
        """
    <div class="msa-companion-card msa-companion-{context}" style="--msa-character-accent: {accent};">
      <div class="{inner_class}">
        {avatar}
        <div>
          <div class="msa-companion-kicker">AI character</div>
          <div class="msa-companion-title">{title}</div>
          <div class="msa-companion-message">{message}</div>
          <div class="msa-companion-chip">{chip}</div>
        </div>
      </div>
    </div>
    """.format(
        context=html.escape(safe_context),
        accent=html.escape(str(active["accent"])),
        inner_class=inner_class,
        avatar=avatar,
        title=html.escape(title),
        message=html.escape(message),
        chip=html.escape(chip),
    )
    )


def render_companion_card(analysis: dict[str, Any] | None = None, context: str = "card", include_avatar: bool = True) -> None:
    profile = companion_profile()
    title, message, chip = companion_copy(analysis, profile)
    render_html(companion_card_html(title, message, chip, context=context, profile=profile, include_avatar=include_avatar))


def render_companion_picker() -> None:
    options = companion_names()
    if st.session_state.get("ai_companion") not in options:
        st.session_state["ai_companion"] = "Scout"
    st.session_state.setdefault("ai_companion_enabled", True)
    if st.session_state.get("ai_companion_motion") not in {"Wander", "Docked", "Focus"}:
        st.session_state["ai_companion_motion"] = "Docked"
    with st.sidebar:
        selected = st.segmented_control("Choose AI character", options, key="ai_companion")
        profile = companion_profile(str(selected or selected_companion_name()))
        st.image(str(companion_asset_path(profile)), width=118)
        st.caption(f"{profile['name']}: {profile['tagline']}")
        st.toggle("Floating companion", key="ai_companion_enabled")
        st.segmented_control(
            "Movement",
            ["Wander", "Docked", "Focus"],
            key="ai_companion_motion",
        )
        st.caption("Docked is the steady mode. Use Wander only when you want him to drift a little.")


def companion_status_mood(status: str) -> str:
    if status == "Sell / trim":
        return "sell"
    if status in {"Breakout trigger", "In buy zone"}:
        return "ready"
    if status in {"Below stop", "No quote"}:
        return "danger"
    if status in {"Near buy zone", "Momentum active"}:
        return "watch"
    return "neutral"


def remember_companion_analysis(analysis: dict[str, Any] | None) -> None:
    if not analysis:
        return
    status = live_status(analysis)
    confidence = data_confidence_summary(analysis)
    signal = ai_signal_light(analysis)
    mood = str(signal.get("mood", companion_status_mood(status)))
    if safe_float(confidence.get("score"), 0) < 45:
        mood = "danger"
    elif safe_float(confidence.get("score"), 0) < 65 and mood == "neutral":
        mood = "watch"
    profile = companion_profile()
    latest = {
        "Ticker": str(analysis.get("Ticker") or "Stock"),
        "Status": status,
        "Entry trigger": str(analysis.get("Entry trigger") or "entry trigger"),
        "Stop": str(analysis.get("Stop") or "planned stop"),
        "Target 1": str(analysis.get("Target 1") or "target 1"),
        "Data confidence": str(confidence.get("label", "data check")),
        "Playbook fit": str(analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score")))),
        "AI light": str(signal.get("label", "Red light")),
        "Signal action": str(signal.get("action", "Wait")),
        "Signal detail": str(signal.get("detail", "Wait for a cleaner setup.")),
        "Signal color": str(signal.get("color", "red")),
        "Mood": mood,
        "Updated": datetime.now().strftime("%I:%M:%S %p"),
        "Companion": str(profile["name"]),
        "Accent": str(profile["accent"]),
        "Tagline": str(profile["tagline"]),
    }
    st.session_state["companion_latest_analysis"] = latest
    try:
        COMPANION_STATUS_FILE.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    except OSError as exc:
        st.session_state["companion_status_write_error"] = str(exc)


def companion_overlay_messages(profile: dict[str, str]) -> list[str]:
    name = str(profile["name"])
    latest = st.session_state.get("companion_latest_analysis")
    if isinstance(latest, dict) and latest.get("Ticker"):
        ticker = str(latest.get("Ticker", "Stock"))
        status = str(latest.get("Status", "Watching"))
        entry = str(latest.get("Entry trigger", "entry trigger"))
        stop = str(latest.get("Stop", "planned stop"))
        target = str(latest.get("Target 1", "target 1"))
        confidence = str(latest.get("Data confidence", "data check"))
        fit = str(latest.get("Playbook fit", "setup check"))
        updated = str(latest.get("Updated", "now"))
        signal = str(latest.get("AI light", "Red light"))
        signal_action = str(latest.get("Signal action", "Wait"))
        signal_detail = str(latest.get("Signal detail", "Wait for a cleaner setup."))
        return [
            f"{ticker}: {status}. Updated {updated}. Use {entry}, {stop}, and {target} as the paper-trade map.",
            f"{name} signal: {signal} - {signal_action}. {signal_detail}",
            f"{name} check: data confidence is {confidence}. Verify fast moves before trusting the number.",
            f"{ticker} fit: {fit}. If the setup is not clean, keep scanning instead of forcing a trade.",
            f"Paper rule: approve only after entry, stop, target, news, volume, and spread all make sense.",
        ]

    selected = normalize_user_symbol(st.session_state.get("selected_ticker", ""))
    stock = selected or "the stock you are studying"
    return [
        f"{name} is watching {stock}. Drag me anywhere and use the tip button for another reminder.",
        "Beginner rule: do not buy early. Wait for the entry trigger and define the stop first.",
        "Before any paper approval, check news, volume, spread, halt risk, and data source.",
        "Use the journal after every paper trade so the app can help you learn from the setup.",
    ]


def render_floating_companion() -> None:
    profile = companion_profile()
    enabled = bool(st.session_state.get("ai_companion_enabled", True))
    motion = str(st.session_state.get("ai_companion_motion", "Docked"))
    latest = st.session_state.get("companion_latest_analysis")
    latest = latest if isinstance(latest, dict) else {}
    AI_COMPANION_COMPONENT(
        key="floating_ai_companion",
        data={
            "enabled": enabled,
            "name": profile["name"],
            "accent": profile["accent"],
            "tagline": profile["tagline"],
            "style": profile["style"],
            "avatar": companion_avatar_src(profile),
            "motion": motion,
            "status": str(latest.get("Status", "Watching")),
            "mood": str(latest.get("Mood", "neutral")),
            "updated": str(latest.get("Updated", "")),
            "messages": companion_overlay_messages(profile),
        },
        height=1,
        width="stretch",
        on_position_change=lambda: None,
        on_tip_index_change=lambda: None,
        on_moved_change=lambda: None,
        on_next_tip_change=lambda: None,
        on_docked_change=lambda: None,
    )


def render_companion_showcase(analysis: dict[str, Any] | None = None, context: str = "dashboard") -> None:
    remember_companion_analysis(analysis)
    profile = companion_profile()
    title, message, chip = companion_copy(analysis, profile)
    with st.container(border=True):
        cols = st.columns([0.22, 0.78], vertical_alignment="center")
        with cols[0]:
            st.image(str(companion_asset_path(profile)), width=150)
            st.caption(f"{profile['name']} selected")
        with cols[1]:
            render_html(companion_card_html(title, message, chip, context=context, profile=profile, include_avatar=False))


def render_sidebar_brand() -> None:
    render_html(
        """
        <div class="msa-sidebar-brand">
          <div class="msa-sidebar-logo">
            {logo}
            <div>
              <strong>{name}</strong>
              <span>Momentum scanner and learning lab</span>
            </div>
          </div>
        </div>
        """.format(
            logo=brand_mark_svg(),
            name=html.escape(APP_NAME),
        ),
        target=st.sidebar,
    )
    render_companion_picker()
    with st.sidebar:
        render_companion_card(context="sidebar", include_avatar=False)


def dashboard_hero() -> None:
    profile = companion_profile()
    title, message, chip = companion_copy(profile=profile)
    render_html(
        f"""
        <div class="msa-hero">
          <div class="msa-hero-grid">
            <div>
              <div class="msa-logo-lockup">
                {brand_mark_svg()}
                <div class="msa-logo-copy">
                  <span>Beginner momentum lab</span>
                  <strong>{html.escape(APP_NAME)}</strong>
                </div>
              </div>
              <h1>{html.escape(APP_NAME)}</h1>
              <p>Live scanners, chart levels, stock news, paper-trade planning, and a learning system for studying momentum without guessing.</p>
              <div class="msa-hero-badges">
                <span class="msa-hero-badge">Real charts</span>
                <span class="msa-hero-badge">AI plan helper</span>
                <span class="msa-hero-badge">Beginner lessons</span>
                <span class="msa-hero-badge">Paper approval gate</span>
              </div>
            </div>
            {companion_card_html(title, message, chip, context="hero", profile=profile)}
          </div>
        </div>
        """
    )


def status_cards(cards: list[tuple[str, str, str]]) -> None:
    parts = ['<div class="msa-status-row">']
    for label, value, tone in cards:
        parts.append(
            f'<div class="msa-status-card msa-{html.escape(tone)}"><div class="msa-label">{html.escape(label)}</div><div class="msa-value">{html.escape(value)}</div></div>'
        )
    parts.append("</div>")
    render_html("".join(parts))


def header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(markdown_text(subtitle))
    st.caption(
        "Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. "
        "This is not financial advice."
    )


def compact_header(title: str, subtitle: str | None = None) -> None:
    render_html(
        """
        <div class="msa-compact-header">
          <h1>{title}</h1>
          {subtitle}
          <small>Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. This is not financial advice.</small>
        </div>
        """.format(
            title=html.escape(title),
            subtitle=f"<p>{html.escape(subtitle)}</p>" if subtitle else "",
        ),
    )


def render_setup_checks(analysis: dict[str, Any]) -> None:
    passed, total = setup_completion(analysis)
    st.markdown(f"**Setup checks: {passed}/{total} ready**")
    with st.container(horizontal=True):
        for name, ok, detail in setup_check_items(analysis):
            st.badge(
                f"{name}: {detail}",
                icon=":material/check_circle:" if ok else ":material/radio_button_unchecked:",
                color="green" if ok else "orange",
            )


def workflow_cockpit_data(analysis: dict[str, Any], chart_source: str | None = None) -> dict[str, Any]:
    label, _ = ai_action_summary(analysis)
    status = live_status(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    math_data = ai_trade_math(analysis)
    passed, total = setup_completion(analysis)
    ticker = str(analysis.get("Ticker", "Stock"))
    fit = str(analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score"))))
    rr_1 = math_data["rr_1"]
    risk = math_data["risk"]
    entry = math_data["entry"]
    stop = math_data["stop"]

    data_tone = "ready" if confidence["score"] >= 65 else "watch" if confidence["score"] >= 45 else "danger"
    setup_tone = "ready" if passed >= max(total - 1, 1) else "watch" if passed >= max(total - 3, 1) else "danger"
    chart_tone = "ready" if status in {"Breakout trigger", "In buy zone"} else "watch" if status in {"Near buy zone", "Momentum active", "Watching"} else "danger"
    risk_tone = "ready" if rr_1 is not None and rr_1 >= 1.4 and risk is not None and risk > 0 else "watch"
    plan_tone = "ready" if label == "Trigger active" and data_tone == "ready" and risk_tone == "ready" else "watch"
    journal_tone = "neutral"

    if confidence["score"] < 45:
        next_title = "Verify data before anything else"
        next_copy = "The quote source or age is weak. Use Charts and another quote source before trusting this as even a paper setup."
        next_tone = "danger"
        next_link = ("/Charts", "Open Charts", ":material/candlestick_chart:")
    elif status == "Below stop" or label == "Plan invalid":
        next_title = "Stand down and rebuild"
        next_copy = "The setup is below its risk line. Treat the old entry and targets as expired until fresh candles rebuild the plan."
        next_tone = "danger"
        next_link = ("/Market_Scan", "Find another stock", ":material/radar:")
    elif passed < max(total - 2, 1):
        next_title = "Keep scanning"
        next_copy = "Too many rules are missing. Use Market Scan or Scanner to find a cleaner stock before staging a paper plan."
        next_tone = "watch"
        next_link = ("/Market_Scan", "Open Market Scan", ":material/radar:")
    elif status in {"Breakout trigger", "In buy zone"} and rr_1 is not None and rr_1 >= 1.4:
        next_title = "Review paper approval"
        next_copy = "The idea is close enough for a careful paper-trade review. Confirm news, spread, candle strength, and max risk first."
        next_tone = "ready"
        next_link = ("/Trade_Desk", "Open Trade Desk", ":material/order_approve:")
    elif status in {"Near buy zone", "Momentum active", "Watching"}:
        next_title = "Watch the chart, do not chase"
        next_copy = "The stock needs either a cleaner pullback or a trigger break. Keep the chart open and wait for the level."
        next_tone = "watch"
        next_link = ("/Charts", "Open Charts", ":material/candlestick_chart:")
    else:
        next_title = "Use it as a study idea"
        next_copy = "This can still teach the workflow, but it is not an active paper-trade review yet."
        next_tone = "neutral"
        next_link = ("/Learn?track=AI%20ladder", "Study AI ladder", ":material/school:")

    steps = [
        {
            "title": "Stock found",
            "state": ticker,
            "detail": f"Fit: {fit}. AI read: {label}.",
            "tone": "ready" if ticker and ticker != "Stock" else "watch",
        },
        {
            "title": "Data verified",
            "state": str(confidence["label"]),
            "detail": f"{confidence['score']}/100 confidence. Age: {confidence['age']}.",
            "tone": data_tone,
        },
        {
            "title": "Setup rules",
            "state": f"{passed}/{total}",
            "detail": "Price, gap, float, RVOL, trend, risk, and status.",
            "tone": setup_tone,
        },
        {
            "title": "Chart status",
            "state": status,
            "detail": f"Entry {money(entry)}. Stop {money(stop)}.",
            "tone": chart_tone,
        },
        {
            "title": "Risk/reward",
            "state": f"{rr_1:.2f}R" if rr_1 is not None else "n/a",
            "detail": f"Risk per share {money(risk)}. Target must pay for risk.",
            "tone": risk_tone,
        },
        {
            "title": "Paper workflow",
            "state": "approval",
            "detail": "Stage only after the ladder is clean, then journal the result.",
            "tone": plan_tone if next_tone == "ready" else journal_tone,
        },
    ]
    blockers = [str(item) for item in analysis.get("Warnings", [])[:3]]
    if confidence["score"] < 65:
        blockers.insert(0, f"Data confidence is {confidence['label']}.")
    if status == "Below stop":
        blockers.insert(0, "Price is below the stop area.")
    if rr_1 is not None and rr_1 < 1.4:
        blockers.append("Target 1 reward/risk is under the preferred 1.4R threshold.")
    return {
        "ticker": ticker,
        "next_title": next_title,
        "next_copy": next_copy,
        "next_tone": next_tone,
        "next_link": next_link,
        "steps": steps,
        "blockers": list(dict.fromkeys(blockers))[:4],
    }


def render_workflow_cockpit(
    analysis: dict[str, Any],
    chart_source: str | None = None,
    context: str = "workflow",
) -> None:
    remember_companion_analysis(analysis)
    cockpit = workflow_cockpit_data(analysis, chart_source)
    step_parts = ['<div class="msa-cockpit-grid">']
    for index, step in enumerate(cockpit["steps"], start=1):
        step_parts.append(
            '<div class="msa-cockpit-step msa-cockpit-{tone}">'
            '<div class="msa-cockpit-step-top"><div class="msa-cockpit-step-number">{index}</div><div class="msa-cockpit-step-state">{state}</div></div>'
            '<div class="msa-cockpit-step-title">{title}</div>'
            '<div class="msa-cockpit-step-detail">{detail}</div>'
            '</div>'.format(
                tone=html.escape(str(step["tone"])),
                index=index,
                state=html.escape(str(step["state"])),
                title=html.escape(str(step["title"])),
                detail=html.escape(str(step["detail"])),
            )
        )
    step_parts.append("</div>")
    blocker_text = "No major workflow blockers from the current model."
    if cockpit["blockers"]:
        blocker_text = " ".join(f"{index}. {item}" for index, item in enumerate(cockpit["blockers"], start=1))

    render_html(
        """
        <div class="msa-cockpit">
          <div class="msa-cockpit-head">
            <div>
              <div class="msa-cockpit-kicker">Workflow cockpit</div>
              <div class="msa-cockpit-title">{ticker} next move</div>
              <div class="msa-cockpit-detail">A guided paper-trading workflow that keeps new traders in order: scan, verify, chart, plan, approve, journal.</div>
            </div>
            <div class="msa-cockpit-next msa-cockpit-next-{tone}">
              <div class="msa-cockpit-kicker">Recommended next step</div>
              <div class="msa-cockpit-next-title">{next_title}</div>
              <div class="msa-cockpit-next-copy">{next_copy}</div>
            </div>
          </div>
          {steps}
          <div class="msa-cockpit-blockers"><b>Slow-down checks:</b> {blockers}</div>
        </div>
        """.format(
            ticker=html.escape(str(cockpit["ticker"])),
            tone=html.escape(str(cockpit["next_tone"])),
            next_title=html.escape(str(cockpit["next_title"])),
            next_copy=html.escape(str(cockpit["next_copy"])),
            steps="".join(step_parts),
            blockers=html.escape(blocker_text),
        ),
    )

    url, label, icon = cockpit["next_link"]
    with st.container(horizontal=True):
        st.link_button(label, url, type="primary" if cockpit["next_tone"] == "ready" else "secondary", icon=icon, width="stretch")
        st.link_button("Study ladder", "/Learn?track=AI%20ladder", icon=":material/school:", width="stretch")
        st.link_button("Open journal", "/Journal", icon=":material/edit_note:", width="stretch")


def default_scan(prefer_live: bool = True) -> pd.DataFrame:
    return run_scan(
        DEFAULT_RULES["min_price"],
        DEFAULT_RULES["max_price"],
        DEFAULT_RULES["min_gain_pct"],
        DEFAULT_RULES["max_float_m"],
        DEFAULT_RULES["min_rvol"],
        prefer_live=prefer_live,
        include_learning=True,
    )


def render_plan_card(analysis: dict[str, Any]) -> None:
    with st.container(border=True):
        top = st.columns([1.1, 1, 1, 1])
        top[0].metric(analysis["Ticker"], analysis["Setup"], analysis["Confidence"])
        top[1].metric("Price", money(analysis["Price"]), pct(analysis["Daily gain %"]))
        top[2].metric("RVOL", f"{analysis['RVOL']:.1f}x", f"Float {analysis['Float M']:.1f}M")
        top[3].metric("AI score", f"{analysis['AI score']}/100", analysis["Data source"])
        fit = analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score")))
        data_quality, data_color = data_quality_badge(analysis.get("Data source"))
        with st.container(horizontal=True):
            st.badge(str(fit), icon=":material/filter_alt:", color=playbook_fit_color(str(fit)))
            st.badge(data_quality, icon=":material/database:", color=data_color)
        st.caption(
            f"Source: {analysis.get('Data source', 'n/a')} | "
            f"Market: {analysis.get('Market state', 'n/a')} | "
            f"Quote time: {analysis.get('Quote time', 'n/a')} | "
            f"Float: {analysis.get('Float source', 'estimate')}"
        )

        render_setup_checks(analysis)
        st.markdown(markdown_text(analysis["Plan"]))
        levels = st.columns(4)
        levels[0].metric("Buy zone", analysis["Buy zone"])
        levels[1].metric("Entry", analysis["Entry trigger"])
        levels[2].metric("Stop", analysis["Stop"])
        levels[3].metric("Targets", f"{analysis['Target 1']} / {analysis['Target 2']}")

        reason_col, warning_col = st.columns(2)
        with reason_col:
            st.markdown("**Why it is on watch**")
            for reason in analysis["Reasons"]:
                st.markdown(markdown_text(f"- {reason}"))
        with warning_col:
            st.markdown("**Risk checks**")
            if analysis["Warnings"]:
                for warning in analysis["Warnings"]:
                    st.markdown(markdown_text(f"- {warning}"))
            else:
                st.write("- No major rule warnings in this model.")


def ai_action_summary(analysis: dict[str, Any]) -> tuple[str, str]:
    status = live_status(analysis)
    ticker = analysis.get("Ticker", "This ticker")
    price = money(safe_float(analysis.get("Price")))
    entry = str(analysis.get("Entry trigger", "the trigger"))
    entry_level = entry.removeprefix("Break over ").strip()
    entry_phrase = f"over {entry_level}" if entry_level and entry_level != entry else entry
    buy_zone = analysis.get("Buy zone", "the buy zone")
    stop = analysis.get("Stop", "the stop")
    target = analysis.get("Target 1", "target 1")
    score = safe_float(analysis.get("AI score"), 0) or 0
    warnings = [str(warning) for warning in analysis.get("Warnings", [])]
    major_rule_misses = sum(
        any(fragment in warning for fragment in ["outside the preferred", "over 10 million", "not cleared the 10%"])
        for warning in warnings
    )

    if score < 50 or major_rule_misses >= 2:
        return (
            "Study only",
            f"{ticker} is useful to watch, but it does not cleanly match the low-priced momentum playbook right now. Treat it as market context unless the scanner rules, news, volume, and risk line up.",
        )

    if status == "Breakout trigger":
        return (
            "Trigger active",
            f"{ticker} is at or above the planned trigger. For paper trading, only consider it if volume is still expanding and risk to {stop} is acceptable. First target is {target}.",
        )
    if status == "In buy zone":
        return (
            "In buy zone",
            f"{ticker} is trading around {price}, inside the planned buy zone of {buy_zone}. Wait for confirmation {entry_phrase}; do not buy just because it touched the zone.",
        )
    if status == "Near buy zone":
        return (
            "Getting close",
            f"{ticker} is near the plan area. Let it come to you, then look for a clean hold and a break {entry_phrase}.",
        )
    if status == "Below stop":
        return (
            "Plan invalid",
            f"{ticker} is below the planned stop. For this strategy, that means stand down and wait for a new setup.",
        )
    return (
        "Watch only",
        f"{ticker} is not at the ideal action point yet. The current plan is buy zone {buy_zone}, confirmation {entry_phrase}, stop {stop}, and target {target}.",
    )


def wait_coaching(analysis: dict[str, Any], label: str) -> list[str]:
    warnings = [str(warning) for warning in analysis.get("Warnings", [])]
    guidance: list[str] = []
    if label == "Study only":
        guidance.append("Use it for context or learning, not as a primary low-float momentum idea.")
    if label == "Watch only":
        guidance.append("Wait for price to come into the buy zone or break the trigger with real volume.")
    if label == "Plan invalid":
        guidance.append("Do not force a new entry from this plan. Rebuild the setup after a fresh base forms.")
    if any("10% gapper" in warning for warning in warnings):
        guidance.append("Skip the aggressive gapper playbook until the daily move and volume confirm demand.")
    if any("over 10 million" in warning for warning in warnings):
        guidance.append("Treat this as a slower context stock unless it has exceptional volume and a fresh catalyst.")
    if any("RVOL" in warning or "volume" in warning.lower() for warning in warnings):
        guidance.append("Volume is not strong enough yet; avoid guessing before buyers show up.")
    if not guidance:
        guidance.append("Keep the stop and target written before any paper order is approved.")
    return list(dict.fromkeys(guidance))[:4]


def ai_trade_math(analysis: dict[str, Any]) -> dict[str, Any]:
    levels = chart_trade_levels(analysis)
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    stop = levels["stop"]
    target_1 = levels["target_1"]
    target_2 = levels["target_2"]
    risk = (entry - stop) if entry is not None and stop is not None and entry > stop else None
    reward_1 = (target_1 - entry) if target_1 is not None and entry is not None and target_1 > entry else None
    reward_2 = (target_2 - entry) if target_2 is not None and entry is not None and target_2 > entry else None
    distance = ((entry - price) / price * 100) if entry is not None and price else None
    rr_1 = reward_1 / risk if risk and reward_1 is not None else None
    rr_2 = reward_2 / risk if risk and reward_2 is not None else None
    return {
        **levels,
        "price": price,
        "risk": risk,
        "reward_1": reward_1,
        "reward_2": reward_2,
        "distance": distance,
        "rr_1": rr_1,
        "rr_2": rr_2,
    }


def ai_tone(label: str, status: str) -> tuple[str, str, str]:
    if label == "Plan invalid" or status == "Below stop":
        return "danger", "Stand down", "red"
    if label == "Trigger active" or status == "Breakout trigger":
        return "ready", "Review paper approval", "green"
    if label == "In buy zone" or status in {"In buy zone", "Near buy zone", "Momentum active"}:
        return "watch", "Watch for trigger", "orange"
    return "hold", "Wait", "gray"


def ai_signal_light(analysis: dict[str, Any], chart_source: str | None = None) -> dict[str, str]:
    label, _ = ai_action_summary(analysis)
    status = live_status(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    math_data = ai_trade_math(analysis)
    passed, total = setup_completion(analysis)
    price = math_data["price"]
    target_1 = math_data["target_1"]
    rr_1 = math_data["rr_1"]
    weak_data = safe_float(confidence.get("score"), 0) < 65
    too_many_missing_checks = passed < max(total - 2, 1)

    if price is not None and target_1 is not None and price >= target_1:
        return {
            "tone": "sell",
            "color": "blue",
            "mood": "sell",
            "label": "Blue light",
            "action": "Sell / trim",
            "detail": f"Price is at or above target 1 near {money(target_1)}. Lock in practice profit or trim the paper plan.",
        }

    if status in {"Below stop", "No quote"} or label in {"Plan invalid", "Study only"}:
        return {
            "tone": "danger",
            "color": "red",
            "mood": "danger",
            "label": "Red light",
            "action": "Do not buy",
            "detail": "The setup is invalid, missing a quote, or too weak for this momentum playbook. Stand down.",
        }

    if weak_data:
        return {
            "tone": "danger",
            "color": "red",
            "mood": "danger",
            "label": "Red light",
            "action": "Verify first",
            "detail": f"Data confidence is {confidence['label']}. Do not buy until another source confirms the quote.",
        }

    if status == "Breakout trigger" and not too_many_missing_checks and (rr_1 is None or rr_1 >= 1.2):
        return {
            "tone": "ready",
            "color": "green",
            "mood": "ready",
            "label": "Green light",
            "action": "Buy review",
            "detail": "Entry trigger is active. This is review-ready only after news, spread, volume, and risk pass.",
        }

    return {
        "tone": "danger",
        "color": "red",
        "mood": "danger",
        "label": "Red light",
        "action": "Wait",
        "detail": "The stock is not at a clean buy trigger yet. Wait for the chart instead of chasing.",
    }


def setup_command_tone(label: str, status: str, confidence_score: float | int | None) -> str:
    tone, _, _ = ai_tone(label, status)
    score = safe_float(confidence_score, 0) or 0
    if score < 45:
        return "danger"
    if score < 65 and tone not in {"danger", "ready"}:
        return "watch"
    return "watch" if tone == "hold" else tone


def setup_command_title(label: str, status: str) -> str:
    if label == "Plan invalid" or status == "Below stop":
        return "Stand down"
    if label == "Trigger active" or status == "Breakout trigger":
        return "Review approval"
    if label == "In buy zone" or status == "In buy zone":
        return "Wait for trigger"
    if status in {"Near buy zone", "Momentum active"}:
        return "Watch closely"
    if status == "No quote":
        return "Verify data"
    return "Study first"


def render_setup_command_strip(
    analysis: dict[str, Any],
    chart_source: str | None = None,
    context: str = "setup",
) -> None:
    remember_companion_analysis(analysis)
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    math_data = ai_trade_math(analysis)
    passed, total = setup_completion(analysis)
    tone = setup_command_tone(label, status, confidence.get("score"))
    ticker = str(analysis.get("Ticker") or "Stock")
    rr_1 = f"{math_data['rr_1']:.2f}R" if math_data["rr_1"] is not None else "n/a"
    distance = pct(math_data["distance"]) if math_data["distance"] is not None else "wait"
    source = str(chart_source or analysis.get("Data source", "n/a"))
    stat_parts = [
        ("Price / entry", f"{money(math_data['price'])} -> {money(math_data['entry'])}", f"Distance to entry: {distance}"),
        ("Stop / risk", money(math_data["stop"]), f"Risk per share: {money(math_data['risk'])}"),
        ("Target / reward", money(math_data["target_1"]), f"Target 1 reward/risk: {rr_1}"),
        ("Data / checks", str(confidence["label"]), f"{passed}/{total} setup checks | {source}"),
    ]
    stats_html = "".join(
        """
        <div class="msa-command-stat">
          <div class="msa-command-stat-label">{label}</div>
          <div class="msa-command-stat-value">{value}</div>
          <div class="msa-command-stat-detail">{detail}</div>
        </div>
        """.format(
            label=html.escape(label_text),
            value=html.escape(value),
            detail=html.escape(detail),
        )
        for label_text, value, detail in stat_parts
    )
    render_html(
        """
        <div class="msa-command-strip">
          <div class="msa-command-main msa-command-{tone}">
            <div class="msa-command-kicker">{context} command</div>
            <div class="msa-command-title">{ticker}: {title}</div>
            <div class="msa-command-copy">{message}</div>
          </div>
          {stats}
        </div>
        """.format(
            tone=html.escape(tone),
            context=html.escape(context.replace("_", " ")),
            ticker=html.escape(ticker),
            title=html.escape(setup_command_title(label, status)),
            message=html.escape(message),
            stats=stats_html,
        ),
    )
    with st.container(horizontal=True):
        if context == "charts":
            st.link_button("Open Trade Desk", "/Trade_Desk", icon=":material/order_approve:", type="primary" if tone == "ready" else "secondary", width="stretch")
        else:
            st.link_button("Open Charts", "/Charts", icon=":material/candlestick_chart:", width="stretch")
        st.link_button("Study AI ladder", "/Learn?track=AI%20ladder", icon=":material/school:", width="stretch")
        st.link_button("Open Journal", "/Journal", icon=":material/edit_note:", width="stretch")


def ai_now_steps(
    analysis: dict[str, Any],
    label: str,
    status: str,
    chart_source: str | None = None,
) -> list[str]:
    math_data = ai_trade_math(analysis)
    entry = money(math_data["entry"])
    stop = money(math_data["stop"])
    risk = money(math_data["risk"])
    target = money(math_data["target_1"])
    confidence = data_confidence_summary(analysis).get("label", "Verify first")
    signal = ai_signal_light(analysis, chart_source)

    if signal["tone"] == "sell":
        return [
            f"Blue light: price is at the first take-profit area near {target}.",
            "Review a paper sell/trim instead of opening a new buy.",
            "Update the journal with whether the target hit cleanly or reversed.",
        ]
    if signal["tone"] == "danger":
        return [
            f"Red light: {signal['detail']}",
            f"Do not approve a buy. Wait for a clean trigger near {entry} or rebuild the plan.",
            f"Keep the invalidation line visible near {stop} before studying it again.",
        ]
    if signal["tone"] == "ready":
        return [
            f"Green light review: confirm the last candle is holding above {entry}.",
            f"Check the stop at {stop}; planned risk is {risk} per share.",
            f"Approve only if news, spread, volume, and {confidence.lower()} data all make sense.",
        ]

    if label == "Trigger active" or status == "Breakout trigger":
        return [
            f"Confirm the last candle is holding above {entry}.",
            f"Check the stop at {stop}; planned risk is {risk} per share.",
            f"Only approve a paper order if volume, spread, news, and {confidence.lower()} data all make sense.",
        ]
    if label == "In buy zone" or status == "In buy zone":
        return [
            f"Price is in the buy area, but the actual trigger is still {entry}.",
            "Wait for buyers to prove it with a clean candle and stronger volume.",
            f"Target 1 is {target}; skip it if the reward no longer beats the risk.",
        ]
    if status in {"Near buy zone", "Momentum active"}:
        return [
            "Keep it on watch and let the setup come to you.",
            f"Set the mental alert around the buy zone and confirmation over {entry}.",
            "Do not chase a candle that runs too far above the plan.",
        ]
    if label == "Plan invalid" or status == "Below stop":
        return [
            f"The price is under the stop area near {stop}.",
            "Treat this plan as broken until a new base forms.",
            "Rebuild the entry, stop, and targets from fresh candles.",
        ]
    return [
        "Use this as a watchlist idea, not an active setup yet.",
        f"Wait for price to approach the buy zone and confirm over {entry}.",
        "Check news and volume again before approving any paper trade.",
    ]


def ai_cancel_rules(analysis: dict[str, Any]) -> list[str]:
    math_data = ai_trade_math(analysis)
    price = math_data["price"]
    entry = math_data["entry"]
    stop = math_data["stop"]
    rvol = safe_float(analysis.get("RVOL"), 0) or 0
    rules = []
    if stop is not None:
        rules.append(f"Price loses the stop area near {money(stop)}.")
    if entry is not None and price is not None and price > entry * 1.04:
        rules.append("Price is already more than 4% above the trigger and the trade is turning into a chase.")
    if rvol < DEFAULT_RULES["min_rvol"]:
        rules.append(f"RVOL is only {rvol:.1f}x, so momentum may not be strong enough yet.")
    for warning in analysis.get("Warnings", [])[:3]:
        rules.append(str(warning))
    rules.append("News turns negative, a halt appears, or the spread is too wide to paper-trade cleanly.")
    return list(dict.fromkeys(rules))[:5]


def beginner_trade_translation(
    analysis: dict[str, Any],
    label: str,
    signal: dict[str, str] | None = None,
) -> str:
    math_data = ai_trade_math(analysis)
    entry = money(math_data["entry"])
    stop = money(math_data["stop"])
    target = money(math_data["target_1"])
    active_signal = signal or ai_signal_light(analysis)
    if active_signal["tone"] == "sell":
        return f"Plain English: blue means this paper plan is at a profit-taking area near {target}. Do not start a fresh buy here; review a sell or trim."
    if active_signal["tone"] == "ready":
        return f"Plain English: green means the setup is ready to review, not an automatic buy. Entry is around {entry}, stop is {stop}, and target 1 is {target}."
    if active_signal["tone"] == "danger":
        return f"Plain English: red means no buy. The app wants you to wait, verify data, or rebuild the setup before risking even a paper trade."
    if label == "Trigger active":
        return f"Plain English: buyers may be confirming the idea now. The paper entry is around {entry}, the safety line is {stop}, and the first place to take profit is {target}."
    if label == "In buy zone":
        return f"Plain English: the stock is near the area you wanted, but beginners should still wait for confirmation near {entry} before approving anything."
    if label == "Plan invalid":
        return f"Plain English: this setup is broken because price is too close to or under the risk line. Do not reuse this plan until the chart resets."
    return f"Plain English: this is a watchlist idea. The app is telling you to wait for {entry}, know the stop at {stop}, and check that {target} pays enough reward."


def ai_plan_ladder_items(analysis: dict[str, Any], chart_source: str | None = None) -> tuple[list[dict[str, str]], str]:
    label, _ = ai_action_summary(analysis)
    status = live_status(analysis)
    math_data = ai_trade_math(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    passed, total = setup_completion(analysis)
    entry = math_data["entry"]
    stop = math_data["stop"]
    target_1 = math_data["target_1"]
    target_2 = math_data["target_2"]
    rr_1 = math_data["rr_1"]
    distance = math_data["distance"]

    source_tone = "ready" if confidence["score"] >= 65 else "watch" if confidence["score"] >= 45 else "danger"
    setup_tone = "ready" if passed >= max(total - 1, 1) else "watch" if passed >= max(total - 3, 1) else "danger"
    entry_tone = "ready" if status == "Breakout trigger" else "watch" if status in {"In buy zone", "Near buy zone", "Momentum active"} else "danger" if status == "Below stop" else "neutral"
    stop_tone = "danger" if status == "Below stop" else "ready" if stop is not None and entry is not None and stop < entry else "watch"
    target_tone = "ready" if rr_1 is not None and rr_1 >= 1.4 else "watch"

    if status == "Breakout trigger":
        entry_detail = "Trigger is active. Confirm candle strength, spread, volume, and news before any paper approval."
        entry_value = money(entry)
        entry_state = "trigger"
    elif status == "In buy zone":
        entry_detail = f"In the buy area, but beginners still wait for confirmation over {money(entry)}."
        entry_value = "Wait"
        entry_state = "confirm"
    elif status == "Near buy zone":
        entry_detail = f"Close to the planned area. Distance to trigger is {pct(distance) if distance is not None else 'n/a'}."
        entry_value = money(entry)
        entry_state = "watch"
    elif status == "Below stop":
        entry_detail = "The current plan is broken. Do not use this entry until a new setup forms."
        entry_value = "Skip"
        entry_state = "invalid"
    else:
        entry_detail = f"Keep it on watch and wait for price to confirm near {money(entry)}."
        entry_value = money(entry)
        entry_state = "wait"

    rr_text = f"{rr_1:.2f}R" if rr_1 is not None else "n/a"
    source_detail = f"{confidence['label']} ({confidence['score']}/100). Quote age: {confidence['age']}."
    target_detail = f"First trim is {money(target_1)} and runner is {money(target_2)}. Target 1 reward/risk: {rr_text}."
    rule = "Read it in order: verify the data, judge the setup, wait for the trigger, respect the stop, then measure whether the profit target pays enough for the risk."
    if label == "Trigger active" and confidence["score"] >= 65:
        rule = "This is the closest thing to an active paper-trade review: the trigger matters now, but approval still needs news, spread, volume, and risk checks."
    elif status == "Below stop" or label == "Plan invalid":
        rule = "The ladder says stand down: when the stop or invalidation area breaks, the old entry and targets no longer count."

    items = [
        {
            "title": "1. Data check",
            "state": str(confidence["label"]),
            "value": f"{confidence['score']}/100",
            "detail": source_detail,
            "tone": source_tone,
        },
        {
            "title": "2. Setup check",
            "state": "rule fit",
            "value": f"{passed}/{total}",
            "detail": "Price, gap, float, RVOL, trend, risk, and action status are checked before the AI helper gets excited.",
            "tone": setup_tone,
        },
        {
            "title": "3. Entry trigger",
            "state": entry_state,
            "value": entry_value,
            "detail": entry_detail,
            "tone": entry_tone,
        },
        {
            "title": "4. Stop loss",
            "state": "risk line",
            "value": money(stop),
            "detail": "If price loses this area, the paper setup is wrong. Do not average down into a broken plan.",
            "tone": stop_tone,
        },
        {
            "title": "5. Take profit",
            "state": "reward",
            "value": money(target_1),
            "detail": target_detail,
            "tone": target_tone,
        },
    ]
    return items, rule


def render_ai_plan_ladder(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    items, rule = ai_plan_ladder_items(analysis, chart_source)
    parts = ['<div class="msa-plan-ladder">']
    for index, item in enumerate(items, start=1):
        parts.append(
            '<div class="msa-plan-step msa-plan-{tone}">'
            '<div class="msa-plan-top"><div class="msa-plan-number">{index}</div><div class="msa-plan-state">{state}</div></div>'
            '<div class="msa-plan-title">{title}</div>'
            '<div class="msa-plan-value">{value}</div>'
            '<div class="msa-plan-detail">{detail}</div>'
            '</div>'.format(
                tone=html.escape(item["tone"]),
                index=index,
                state=html.escape(item["state"]),
                title=html.escape(item["title"]),
                value=html.escape(item["value"]),
                detail=html.escape(item["detail"]),
            )
        )
    parts.append("</div>")
    render_html("".join(parts))
    render_html(
        '<div class="msa-plan-rule"><b>Beginner rule:</b> {rule}</div>'.format(rule=html.escape(rule)),
    )


def render_html_list(title: str, items: list[str]) -> str:
    parts = [f"<strong>{html.escape(title)}</strong><ul>"]
    for item in items:
        parts.append(f"<li>{html.escape(item)}</li>")
    parts.append("</ul>")
    return "".join(parts)


def render_ai_decision_panel(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    remember_companion_analysis(analysis)
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    math_data = ai_trade_math(analysis)
    _, action, _ = ai_tone(label, status)
    confidence = data_confidence_summary(analysis, chart_source)
    signal = ai_signal_light(analysis, chart_source)
    command_tone = str(signal["tone"])
    command_action = str(signal["action"])
    passed, total = setup_completion(analysis)
    score = safe_float(analysis.get("AI score"), 0) or 0
    rr_1 = f"{math_data['rr_1']:.2f}R" if math_data["rr_1"] is not None else "n/a"
    rr_2 = f"{math_data['rr_2']:.2f}R" if math_data["rr_2"] is not None else "n/a"
    distance = pct(math_data["distance"]) if math_data["distance"] is not None else "wait"
    level_items = [
        ("Current", money(math_data["price"]), status, "neutral"),
        ("Entry", money(math_data["entry"]), "Buy only after trigger", "profit"),
        ("Stop loss", money(math_data["stop"]), "Plan is wrong here", "danger"),
        ("Take profit 1", money(math_data["target_1"]), f"{rr_1} reward/risk", "profit"),
        ("Runner target", money(math_data["target_2"]), f"{rr_2} reward/risk", "profit"),
        ("Risk / share", money(math_data["risk"]), f"To entry: {distance}", "danger"),
    ]
    level_parts = ['<div class="msa-ai-level-grid">']
    for item_label, value, detail, item_tone in level_items:
        level_parts.append(
            '<div class="msa-ai-level msa-ai-level-{tone}">'
            '<div class="msa-ai-level-label">{label}</div>'
            '<div class="msa-ai-level-value">{value}</div>'
            '<div class="msa-ai-level-note">{detail}</div>'
            '</div>'.format(
                tone=html.escape(item_tone),
                label=html.escape(item_label),
                value=html.escape(value),
                detail=html.escape(str(detail)),
            )
        )
    level_parts.append("</div>")

    with st.container(border=True):
        st.markdown("**AI assistant**")
        with st.container(horizontal=True):
            st.badge(str(signal["label"]), icon=":material/radio_button_checked:", color=str(signal["color"]))
            st.badge(label, icon=":material/psychology:", color=str(signal["color"]))
            st.badge(status, icon=":material/candlestick_chart:", color=str(signal["color"]))
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))
            st.badge("Paper approval only", icon=":material/edit_note:", color="blue")

        render_html(
            """
            <div class="msa-ai-command msa-ai-{tone}">
                <div class="msa-ai-header">
                    <div>
                        <div class="msa-ai-topline">
                            <div class="msa-ai-signal-card msa-ai-signal-{signal_tone}">
                                <div class="msa-ai-light"><span></span></div>
                                <div>
                                    <div class="msa-ai-signal-kicker">AI signal light</div>
                                    <div class="msa-ai-signal-action">{signal_action}</div>
                                    <div class="msa-ai-signal-detail">{signal_detail}</div>
                                </div>
                            </div>
                            <div>
                                <div class="msa-ai-kicker">AI command center</div>
                                <div class="msa-ai-title">{action}</div>
                            </div>
                        </div>
                        <div class="msa-ai-detail">{message}</div>
                    </div>
                    <div class="msa-ai-score"><span>Score</span>{score}/100<br><span>Checks</span>{passed}/{total}</div>
                </div>
                {levels}
            </div>
            """.format(
                tone=html.escape(command_tone),
                signal_tone=html.escape(command_tone),
                signal_action=html.escape(command_action),
                signal_detail=html.escape(str(signal["detail"])),
                action=html.escape(command_action if command_tone in {"sell", "ready", "danger"} else action),
                message=html.escape(message),
                score=int(score),
                passed=passed,
                total=total,
                levels="".join(level_parts),
            ),
        )

        render_ai_plan_ladder(analysis, chart_source)

        now_items = ai_now_steps(analysis, label, status, chart_source)
        cancel_items = ai_cancel_rules(analysis)
        left, right = st.columns(2)
        render_html(
            f'<div class="msa-ai-list">{render_html_list("Do this now", now_items)}</div>',
            target=left,
        )
        render_html(
            f'<div class="msa-ai-list">{render_html_list("Cancel or wait if", cancel_items)}</div>',
            target=right,
        )
        render_html(
            f'<div class="msa-ai-plain">{html.escape(beginner_trade_translation(analysis, label, signal))}</div>',
        )
        st.caption("Educational paper-trading decision aid. It does not place real trades and it is not financial advice.")


def render_trade_readiness_panel(analysis: dict[str, Any]) -> None:
    remember_companion_analysis(analysis)
    label, message = ai_action_summary(analysis)
    status = live_status(analysis)
    checks = setup_check_items(analysis)
    passed, total = setup_completion(analysis)
    levels = chart_trade_levels(analysis)
    risk_reward = safe_float(analysis.get("Risk/reward"))
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    distance = ((entry - price) / price * 100) if entry is not None and price else None

    tone = "hold"
    action = "Wait"
    if label == "Plan invalid" or status == "Below stop":
        tone = "danger"
        action = "Stand down"
    elif label == "Trigger active" or status in {"Breakout trigger", "In buy zone"}:
        tone = "ready"
        action = "Review approval"
    elif status in {"Near buy zone", "Momentum active"}:
        tone = "watch"
        action = "Watch closely"

    next_step = wait_coaching(analysis, label)[0] if label in {"Study only", "Watch only", "Plan invalid"} else "Confirm news, spread, volume, and risk before approving any paper order."
    command = [
        '<div class="msa-readiness-command">',
        '<div class="msa-readiness-tile msa-readiness-{tone}"><div class="msa-readiness-kicker">Paper action</div><div class="msa-readiness-primary">{action}</div><div class="msa-readiness-detail">{status}</div></div>'.format(
            tone=html.escape(tone),
            action=html.escape(action),
            status=html.escape(status),
        ),
        '<div class="msa-readiness-tile"><div class="msa-readiness-kicker">AI read</div><div class="msa-readiness-primary">{label}</div><div class="msa-readiness-detail">{message}</div></div>'.format(
            label=html.escape(label),
            message=html.escape(message),
        ),
        '<div class="msa-readiness-tile"><div class="msa-readiness-kicker">Readiness</div><div class="msa-readiness-primary">{passed}/{total}</div><div class="msa-readiness-detail">{next_step}</div></div>'.format(
            passed=passed,
            total=total,
            next_step=html.escape(next_step),
        ),
        "</div>",
    ]

    check_parts = ['<div class="msa-check-grid">']
    for name, ok, detail in checks:
        check_parts.append(
            '<div class="msa-check-card msa-check-{tone}"><div class="msa-check-label">{name}</div><div class="msa-check-value">{detail}</div></div>'.format(
                tone="ok" if ok else "wait",
                name=html.escape(name),
                detail=html.escape(str(detail)),
            )
        )
    check_parts.extend(
        [
            '<div class="msa-check-card"><div class="msa-check-label">To entry</div><div class="msa-check-value">{distance}</div></div>'.format(
                distance=html.escape(pct(distance) if distance is not None else "n/a")
            ),
            '<div class="msa-check-card"><div class="msa-check-label">R/R</div><div class="msa-check-value">{risk_reward}</div></div>'.format(
                risk_reward=html.escape(f"{risk_reward:.2f}R" if risk_reward is not None else "n/a")
            ),
            "</div>",
        ]
    )

    with st.container(border=True):
        st.markdown("**Trade readiness**")
        render_html("".join(command))
        render_html("".join(check_parts))


def render_training_progress_panel() -> None:
    known = len(st.session_state.get("learn_flash_known", []))
    review = len(st.session_state.get("learn_flash_review", []))
    quiz_score = st.session_state.get("learn_quiz_score") if st.session_state.get("learn_quiz_graded") else None
    quiz_set = st.session_state.get("learn_quiz_graded_set", "Not graded") if quiz_score is not None else "Not graded"
    with st.container(border=True):
        st.markdown("**Skill builder**")
        cols = st.columns(3)
        cols[0].metric("Known cards", str(known), border=True)
        cols[1].metric("Review pile", str(review), border=True)
        cols[2].metric("Last quiz", f"{quiz_score}/5" if quiz_score is not None else "n/a", str(quiz_set), border=True)
        st.write("- Use Flashcards for terms before the open.")
        st.write("- Use Quiz before approving paper trades.")
        st.write("- Mark weak topics for review, then check the same idea on Charts.")


def chart_timestamp_label(value: Any) -> str:
    try:
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return "n/a"
        return timestamp.strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return "n/a"


def parse_display_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text or text.lower() in {"n/a", "nan", "none"}:
        return None
    try:
        timestamp = pd.Timestamp(text)
        if pd.isna(timestamp):
            return None
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert(None)
        return timestamp.to_pydatetime().replace(tzinfo=None)
    except Exception:
        return None


def quote_age_minutes(value: Any) -> float | None:
    timestamp = parse_display_timestamp(value)
    if timestamp is None:
        return None
    age = (datetime.now() - timestamp).total_seconds() / 60
    if age < -5:
        return None
    return max(age, 0)


def age_label(minutes: float | None) -> str:
    if minutes is None:
        return "time missing"
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{int(minutes)}m ago"
    if minutes < 1440:
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m ago"
    days = int(minutes // 1440)
    hours = int((minutes % 1440) // 60)
    return f"{days}d {hours}h ago"


def looks_like_last_regular_session(value: Any) -> bool:
    timestamp = parse_display_timestamp(value)
    if timestamp is None:
        return False
    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
    if age_hours < 0 or age_hours > 96:
        return False
    return (timestamp.hour == 13 and timestamp.minute <= 10) or (timestamp.hour == 16 and timestamp.minute <= 10)


def data_confidence_summary(
    analysis: dict[str, Any],
    chart_source: str | None = None,
    chart_diff_pct: float | None = None,
) -> dict[str, Any]:
    source = str(analysis.get("Data source", "n/a"))
    source_text = f"{source} {chart_source or ''}".lower()
    quote_time = analysis.get("Quote time", "n/a")
    market_state = str(analysis.get("Market state", "n/a")).upper()
    age_minutes = quote_age_minutes(quote_time)
    score = 100
    notes: list[str] = []

    if "learning" in source_text:
        return {
            "label": "Practice data",
            "color": "orange",
            "score": 25,
            "age": age_label(age_minutes),
            "detail": "This view includes learning fallback data, so use it for practice only.",
        }

    if "alpaca" in source_text:
        notes.append("Alpaca IEX candle data is available.")
    elif "finnhub" in source_text:
        notes.append("Finnhub live quote is available.")
    elif "yahoo" in source_text:
        score -= 5
        notes.append("Yahoo data is available, but free feeds can be delayed.")
    else:
        score -= 20
        notes.append("The active source is not a recognized live quote feed.")

    if chart_diff_pct is not None:
        if chart_diff_pct > 1.0:
            score -= 30
            notes.append("The chart candle and active quote differ by more than 1%.")
        elif chart_diff_pct > 0.35:
            score -= 8
            notes.append("The chart candle and active quote are close, but not identical.")
        else:
            notes.append("The chart candle and active quote are closely aligned.")

    if age_minutes is None:
        score -= 12
        notes.append("The quote time is missing.")
    elif age_minutes <= 20:
        notes.append("The quote timestamp looks fresh.")
    elif "CLOSED" in market_state or "POST" in market_state or looks_like_last_regular_session(quote_time):
        score -= 5
        notes.append("The quote looks like a last regular-session print, which is normal after hours.")
    elif age_minutes <= 120:
        score -= 12
        notes.append("The quote may be delayed.")
    elif age_minutes <= 1440:
        score -= 22
        notes.append("The quote is older than a normal live check.")
    else:
        score -= 35
        notes.append("The quote is more than a day old.")

    score = max(0, min(100, int(score)))
    if score >= 85:
        label, color = "High confidence", "green"
    elif score >= 65:
        label, color = "Usable for paper", "blue"
    elif score >= 45:
        label, color = "Verify first", "orange"
    else:
        label, color = "Practice only", "red"

    return {
        "label": label,
        "color": color,
        "score": score,
        "age": age_label(age_minutes),
        "detail": " ".join(notes),
    }


def pulse_series(df: pd.DataFrame, column: str, default: Any = "n/a") -> pd.Series:
    if column in df.columns:
        return df[column].fillna(default)
    return pd.Series([default] * len(df), index=df.index)


def pulse_numeric(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([np.nan] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def pulse_stock_label(row: dict[str, Any]) -> str:
    for key in ("Ticker", "Stock", "Symbol"):
        value = str(row.get(key, "") or "").upper().strip()
        if value:
            return value
    return "n/a"


def pulse_confidence_labels(df: pd.DataFrame) -> pd.Series:
    if "Data confidence" in df.columns:
        return df["Data confidence"].fillna("n/a").astype(str)
    labels = [str(data_confidence_summary(row.to_dict()).get("label", "n/a")) for _, row in df.iterrows()]
    return pd.Series(labels, index=df.index)


def market_pulse_snapshot(df: pd.DataFrame, context: str = "market") -> dict[str, Any]:
    if df is None or df.empty:
        return {
            "context": context,
            "headline": "No clean stock rows yet",
            "detail": "Run the scanner, refresh live tracking, or allow learning fallback rows so the app has something to study.",
            "next_title": "Refresh or loosen filters",
            "next_copy": "If live feeds are rate-limited, use fallback rows for practice and verify prices again before any paper approval.",
            "tone": "watch",
            "source_line": "No source rows loaded.",
            "flags": ["No scanner rows are available in this view yet."],
            "stats": [
                {"label": "Data trust", "value": "n/a", "detail": "No rows to grade yet.", "tone": "watch"},
                {"label": "Paper setups", "value": "0", "detail": "No breakout or buy-zone rows.", "tone": "watch"},
                {"label": "Top stock", "value": "n/a", "detail": "Run a scan first.", "tone": "neutral"},
                {"label": "Scan power", "value": "n/a", "detail": "No average RVOL yet.", "tone": "neutral"},
            ],
            "top_stock": "",
        }

    statuses = pulse_series(df, "Status", "Watching").astype(str)
    confidence = pulse_confidence_labels(df)
    confidence_lower = confidence.str.lower()
    sources = pulse_series(df, "Data source", "n/a").astype(str)
    source_lower = sources.str.lower()
    gains = pulse_numeric(df, "Daily gain %")
    rvol = pulse_numeric(df, "RVOL")
    scores = pulse_numeric(df, "AI score")

    active_statuses = {"Breakout trigger", "In buy zone"}
    waiting_statuses = {"Near buy zone", "Momentum active"}
    active_count = int(statuses.isin(active_statuses).sum())
    waiting_count = int(statuses.isin(waiting_statuses).sum())
    below_stop_count = int((statuses == "Below stop").sum())
    no_quote_count = int((statuses == "No quote").sum())
    learning_count = int(source_lower.str.contains("learning|fallback", regex=True).sum())
    trusted_mask = confidence_lower.isin({"high confidence", "usable for paper"})
    weak_mask = confidence_lower.isin({"verify first", "practice only"}) | source_lower.str.contains("learning|fallback", regex=True)
    trusted_count = int(trusted_mask.sum())
    weak_count = int(weak_mask.sum())
    trust_pct = int(round((trusted_count / len(df)) * 100)) if len(df) else 0
    avg_gain = safe_float(gains.mean())
    avg_rvol = safe_float(rvol.mean())

    ranking = df.copy()
    status_rank = {
        "Breakout trigger": 0,
        "In buy zone": 1,
        "Near buy zone": 2,
        "Momentum active": 3,
        "Watching": 4,
        "Below stop": 8,
        "No quote": 9,
    }
    ranking["_pulse_status_rank"] = statuses.map(status_rank).fillna(6)
    ranking["_pulse_score"] = scores.fillna(0)
    ranking["_pulse_gain"] = gains.fillna(-999)
    ranking["_pulse_rvol"] = rvol.fillna(0)
    top_row = ranking.sort_values(
        ["_pulse_status_rank", "_pulse_score", "_pulse_gain", "_pulse_rvol"],
        ascending=[True, False, False, False],
    ).iloc[0].to_dict()
    top_stock = pulse_stock_label(top_row)
    top_status = str(top_row.get("Status", "Watching") or "Watching")
    top_price = safe_float(top_row.get("Price"))
    top_score = safe_float(top_row.get("AI score"))
    top_score_text = f"{int(top_score)}/100" if top_score is not None else "n/a"

    flags: list[str] = []
    if weak_count:
        flags.append(f"{weak_count} row{'s' if weak_count != 1 else ''} need price/source verification.")
    if learning_count:
        flags.append(f"{learning_count} row{'s' if learning_count != 1 else ''} use learning or fallback data.")
    if below_stop_count:
        flags.append(f"{below_stop_count} row{'s' if below_stop_count != 1 else ''} are below the stop area.")
    if no_quote_count:
        flags.append(f"{no_quote_count} row{'s' if no_quote_count != 1 else ''} have no active quote.")
    if avg_rvol is not None and avg_rvol < DEFAULT_RULES["min_rvol"]:
        flags.append("Average RVOL is below the preferred momentum threshold.")
    if active_count == 0 and waiting_count == 0:
        flags.append("No row is in a buy zone, trigger, or near-trigger watch state yet.")
    if not flags:
        flags.append("No major scan-wide blocker from the current rows.")

    if weak_count >= max(1, math.ceil(len(df) * 0.5)):
        headline = "Verify prices before trusting this scan"
        detail = "A lot of the current rows are fallback, stale, or marked verify-first. Treat them as study ideas until another source agrees."
        next_title = "Check source and chart first"
        next_copy = "Open Charts for the leading stock, compare the latest candle with the price audit, and read the news before staging anything."
        tone = "danger" if trusted_count == 0 else "watch"
    elif active_count > 0:
        headline = "Paper setups are forming"
        detail = f"{active_count} stock{'s' if active_count != 1 else ''} are at a breakout trigger or inside the buy zone. Slow down and verify the exact levels."
        next_title = "Open the top chart"
        next_copy = f"Start with {top_stock}. Confirm 1-minute candles, news, entry, stop, and take-profit before any paper approval."
        tone = "ready"
    elif waiting_count > 0:
        headline = "Good watchlist, wait for the trigger"
        detail = f"{waiting_count} stock{'s' if waiting_count != 1 else ''} are close or have momentum, but the clean paper-entry condition is not confirmed yet."
        next_title = "Watch, do not chase"
        next_copy = "Keep the chart open, wait for price to reach the planned area, and skip if reward/risk gets worse."
        tone = "watch"
    elif avg_gain is not None and avg_gain >= DEFAULT_RULES["min_gain_pct"] and avg_rvol is not None and avg_rvol >= DEFAULT_RULES["min_rvol"]:
        headline = "Momentum is active, but entries need work"
        detail = "The list has attention and movement, but the top rows are not clean buy-zone or trigger setups yet."
        next_title = "Build the watchlist"
        next_copy = "Sort by score and RVOL, then inspect the best chart instead of forcing a paper order."
        tone = "watch"
    else:
        headline = "Quiet or mixed scan"
        detail = "This is a better learning moment than a paper-trade moment. Review terms, chart patterns, and news until a cleaner setup appears."
        next_title = "Study or scan another batch"
        next_copy = "Run another market-scan batch, check news, or use Learn to practice the workflow while conditions are quiet."
        tone = "neutral"

    source_counts = sources.value_counts().head(3)
    source_line = "; ".join(f"{source}: {count}" for source, count in source_counts.items()) or "Source mix unavailable."
    trust_tone = "ready" if trust_pct >= 70 else "watch" if trust_pct >= 35 else "danger"
    setup_tone = "ready" if active_count else "watch" if waiting_count else "neutral"
    power_tone = "ready" if avg_rvol is not None and avg_rvol >= DEFAULT_RULES["min_rvol"] else "watch"
    flag_tone = "ready" if flags == ["No major scan-wide blocker from the current rows."] else "watch" if tone != "danger" else "danger"

    return {
        "context": context,
        "headline": headline,
        "detail": detail,
        "next_title": next_title,
        "next_copy": next_copy,
        "tone": tone,
        "source_line": source_line,
        "flags": flags[:4],
        "stats": [
            {
                "label": "Data trust",
                "value": f"{trust_pct}%",
                "detail": f"{trusted_count} of {len(df)} rows are high-confidence or usable for paper.",
                "tone": trust_tone,
            },
            {
                "label": "Paper setups",
                "value": f"{active_count}+{waiting_count}",
                "detail": "Active plus near-trigger rows.",
                "tone": setup_tone,
            },
            {
                "label": "Top stock",
                "value": top_stock,
                "detail": f"{money(top_price)} | {top_status} | score {top_score_text}",
                "tone": setup_tone if top_status in active_statuses | waiting_statuses else "neutral",
            },
            {
                "label": "Scan power",
                "value": f"{avg_rvol:.1f}x" if avg_rvol is not None and not math.isnan(avg_rvol) else "n/a",
                "detail": f"Average RVOL. Average gain {pct(avg_gain)} across {len(df)} rows.",
                "tone": power_tone if avg_rvol is not None else "neutral",
            },
        ],
        "top_stock": top_stock if top_stock != "n/a" else "",
        "flag_tone": flag_tone,
    }


def render_market_pulse(df: pd.DataFrame, context: str = "market", show_actions: bool = True) -> None:
    pulse = market_pulse_snapshot(df, context)
    stats_html = ['<div class="msa-pulse-grid">']
    for stat in pulse["stats"]:
        stats_html.append(
            '<div class="msa-pulse-stat msa-pulse-stat-{tone}">'
            '<div class="msa-pulse-stat-label">{label}</div>'
            '<div class="msa-pulse-stat-value">{value}</div>'
            '<div class="msa-pulse-stat-detail">{detail}</div>'
            '</div>'.format(
                tone=html.escape(str(stat["tone"])),
                label=html.escape(str(stat["label"])),
                value=html.escape(str(stat["value"])),
                detail=html.escape(str(stat["detail"])),
            )
        )
    stats_html.append("</div>")
    flags = " ".join(f"{index}. {item}" for index, item in enumerate(pulse["flags"], start=1))

    render_html(
        """
        <div class="msa-pulse">
          <div class="msa-pulse-head">
            <div>
              <div class="msa-pulse-kicker">Market pulse</div>
              <div class="msa-pulse-title">{headline}</div>
              <div class="msa-pulse-copy">{detail}</div>
            </div>
            <div class="msa-pulse-next msa-pulse-next-{tone}">
              <div class="msa-pulse-kicker">Best next move</div>
              <div class="msa-pulse-title">{next_title}</div>
              <div class="msa-pulse-copy">{next_copy}</div>
            </div>
          </div>
          {stats}
          <div class="msa-pulse-flags"><b>Risk flags:</b> {flags}<br><b>Source mix:</b> {source_line}</div>
        </div>
        """.format(
            headline=html.escape(str(pulse["headline"])),
            detail=html.escape(str(pulse["detail"])),
            tone=html.escape(str(pulse["tone"])),
            next_title=html.escape(str(pulse["next_title"])),
            next_copy=html.escape(str(pulse["next_copy"])),
            stats="".join(stats_html),
            flags=html.escape(flags),
            source_line=html.escape(str(pulse["source_line"])),
        ),
    )

    if show_actions:
        with st.container(horizontal=True):
            st.link_button("Open Charts", "/Charts", icon=":material/candlestick_chart:", width="stretch")
            st.link_button("Run Market Scan", "/Market_Scan", icon=":material/radar:", width="stretch")
            st.link_button("Study Market pulse", "/Learn?track=Market%20pulse", icon=":material/school:", width="stretch")


def price_audit_frame(
    ticker: str,
    history: pd.DataFrame,
    analysis: dict[str, Any],
    chart_source: str,
) -> pd.DataFrame:
    plan_price = safe_float(analysis.get("Price"))
    rows: list[dict[str, Any]] = []

    def add_row(source: str, price: float | None, timestamp: str, notes: str) -> None:
        diff = (price - plan_price) if price is not None and plan_price is not None else None
        diff_pct = (diff / plan_price * 100) if diff is not None and plan_price else None
        rows.append(
            {
                "Source": source,
                "Price": price,
                "Difference": diff,
                "Difference %": diff_pct,
                "Time": timestamp,
                "Notes": notes,
            }
        )

    add_row(
        "Active app price",
        plan_price,
        str(analysis.get("Quote time", "n/a")),
        str(analysis.get("Data source", "n/a")),
    )

    if history is not None and not history.empty:
        last = history.iloc[-1]
        add_row(
            "Chart last candle",
            safe_float(last.get("Close")),
            chart_timestamp_label(history.index[-1]),
            chart_source,
        )

    finnhub_stats = finnhub_quote_stats(ticker)
    if finnhub_stats:
        add_row(
            "Finnhub quote",
            safe_float(finnhub_stats.get("Price")),
            str(finnhub_stats.get("Quote time", "n/a")),
            str(finnhub_stats.get("Market state", "n/a")),
        )

    yahoo_stats = yahoo_quote_stats(ticker)
    if yahoo_stats:
        add_row(
            "Yahoo quote",
            safe_float(yahoo_stats.get("Price")),
            str(yahoo_stats.get("Quote time", "n/a")),
            str(yahoo_stats.get("Market state", "n/a")),
        )

    return pd.DataFrame(rows)


def render_price_audit_panel(
    ticker: str,
    history: pd.DataFrame,
    analysis: dict[str, Any],
    chart_source: str,
) -> None:
    audit = price_audit_frame(ticker, history, analysis, chart_source)
    plan_price = safe_float(analysis.get("Price"))
    chart_price = None
    if history is not None and not history.empty:
        chart_price = safe_float(history.iloc[-1].get("Close"))
    chart_diff_pct = abs((chart_price - plan_price) / plan_price * 100) if chart_price is not None and plan_price else None
    live_rows = audit[audit["Source"].isin(["Finnhub quote", "Yahoo quote"])] if not audit.empty else pd.DataFrame()
    confidence = data_confidence_summary(analysis, chart_source, chart_diff_pct)

    status_label = "Price source unknown"
    status_color = "gray"
    if "learning" in str(chart_source).lower():
        status_label = "Learning fallback"
        status_color = "orange"
    elif plan_price is None:
        status_label = "No active quote"
        status_color = "red"
    elif chart_diff_pct is not None and chart_diff_pct > 1.0:
        status_label = "Price mismatch"
        status_color = "orange"
    elif not live_rows.empty:
        status_label = "Quote checked"
        status_color = "green"

    with st.container(border=True):
        st.markdown("**Price audit**")
        with st.container(horizontal=True):
            st.badge(status_label, icon=":material/price_check:", color=status_color)
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))
            st.badge(str(analysis.get("Data source", "n/a")), icon=":material/database:", color=data_quality_badge(analysis.get("Data source"))[1])
            st.badge(str(chart_source), icon=":material/candlestick_chart:", color=data_quality_badge(chart_source)[1])

        cols = st.columns(4)
        cols[0].metric("Active price", money(plan_price), border=True)
        cols[1].metric("Chart last", money(chart_price), border=True)
        cols[2].metric("Chart difference", pct(chart_diff_pct), border=True)
        cols[3].metric("Quote age", str(confidence["age"]), str(analysis.get("Quote time", "n/a")), border=True)

        st.progress(float(confidence["score"]) / 100)
        st.caption(f"Data confidence: {confidence['score']}/100. {confidence['detail']}")

        if status_label == "Price mismatch":
            st.warning(
                "The chart candle and active quote are not matching closely. This can happen with delayed/free feeds, premarket/after-hours data, or fast-moving stocks.",
                icon=":material/warning:",
            )
        elif status_label == "Learning fallback":
            st.warning(
                "This stock is using learning fallback data. Do not treat these prices as live market prices.",
                icon=":material/school:",
            )
        elif confidence["label"] in {"Verify first", "Practice only"}:
            st.warning(
                "Verify this stock in Charts and with your broker or another quote source before using the plan, even for paper practice.",
                icon=":material/fact_check:",
            )
        else:
            st.caption("Free feeds can still be delayed. Use this panel to verify the source and time before trusting a paper-trade plan.")

        if not audit.empty:
            st.dataframe(
                audit,
                width="stretch",
                hide_index=True,
                column_config={
                    "Source": st.column_config.TextColumn("Source", pinned=True),
                    "Price": st.column_config.NumberColumn("Price", format="$%.4f"),
                    "Difference": st.column_config.NumberColumn("Diff", format="$%.4f"),
                    "Difference %": st.column_config.NumberColumn("Diff %", format="%.3f%%"),
                },
            )


def asset_type_label(analysis: dict[str, Any]) -> str:
    ticker = str(analysis.get("Ticker", "")).upper()
    sector = str(analysis.get("Sector", "")).lower()
    if ticker.startswith("^") or "index" in sector:
        return "market index"
    if ticker in {"SPY", "QQQ", "IWM", "DIA"} or "etf" in sector:
        return "ETF"
    return "stock"


def article_for(label: str) -> str:
    return "an" if label[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def beginner_movement_text(analysis: dict[str, Any], asset_type: str) -> str:
    price = safe_float(analysis.get("Price"))
    gain = safe_float(analysis.get("Daily gain %"))
    previous = safe_float(analysis.get("Previous close"))
    if price is None:
        return f"The app does not have a usable live price for this {asset_type} yet."
    if gain is None:
        return f"It is trading around {money(price)}. The app does not have enough data to explain today's move yet."
    if abs(gain) < 0.15:
        return f"It is trading around {money(price)}, nearly flat versus the last close."
    direction = "up" if gain > 0 else "down"
    pressure = "buyers are pushing it higher" if gain > 0 else "sellers are pressuring it lower"
    previous_text = f" from the previous close near {money(previous)}" if previous else ""
    return f"It is trading around {money(price)}, {direction} {pct(abs(gain))}{previous_text}. In plain English, {pressure} today."


def beginner_attention_text(analysis: dict[str, Any]) -> str:
    rvol = safe_float(analysis.get("RVOL"))
    volume = safe_float(analysis.get("Volume"))
    volume_text = compact_number(volume) if volume is not None else "n/a"
    if rvol is None:
        return f"Volume is {volume_text}, but the app cannot compare it with normal activity yet."
    if rvol >= 5:
        level = "extremely high"
    elif rvol >= 3:
        level = "high"
    elif rvol >= 1.5:
        level = "picking up"
    else:
        level = "quiet"
    return f"Volume is {volume_text}. RVOL is {rvol:.1f}x, which means attention is {level} versus normal trading."


def beginner_float_text(analysis: dict[str, Any], asset_type: str) -> str:
    float_m = safe_float(analysis.get("Float M"))
    if asset_type in {"ETF", "market index"}:
        return f"This is {article_for(asset_type)} {asset_type}, so the small-float scanner rule is mainly market context here."
    if float_m is None:
        return "The app does not have a float estimate yet. That makes small-cap risk harder to judge."
    if float_m <= DEFAULT_RULES["max_float_m"]:
        return f"Float is about {float_m:.1f}M shares, which is low enough to match the app's small-float momentum rule."
    return f"Float is about {float_m:.1f}M shares, above the app's preferred small-float rule. It may move differently than a low-float runner."


def first_readable(items: list[Any] | tuple[Any, ...], fallback: str, limit: int = 2) -> str:
    clean = [str(item).strip() for item in items if str(item).strip()]
    if not clean:
        return fallback
    if len(clean) == 1 or limit == 1:
        return clean[0]
    return "; ".join(clean[:limit])


def stock_fact_sheet_frame(analysis: dict[str, Any], chart_source: str | None = None) -> pd.DataFrame:
    asset_type = asset_type_label(analysis)
    confidence = data_confidence_summary(analysis, chart_source)
    return pd.DataFrame(
        [
            {
                "Fact": "Company/name",
                "Value": str(analysis.get("Company", analysis.get("Ticker", "n/a"))),
                "Beginner meaning": "The business, ETF, or index you are studying.",
            },
            {
                "Fact": "Type",
                "Value": asset_type,
                "Beginner meaning": "Stocks, ETFs, and indexes behave differently. Small-float rules mostly apply to stocks.",
            },
            {
                "Fact": "Exchange",
                "Value": str(analysis.get("Exchange", "n/a")),
                "Beginner meaning": "Where the quote is listed or reported from.",
            },
            {
                "Fact": "Market state",
                "Value": str(analysis.get("Market state", "n/a")),
                "Beginner meaning": "Tells whether the feed is regular, premarket, after-hours, closed, chart-derived, or practice data.",
            },
            {
                "Fact": "Previous close",
                "Value": money(safe_float(analysis.get("Previous close"))),
                "Beginner meaning": "The reference price used to understand today's move.",
            },
            {
                "Fact": "Volume",
                "Value": compact_number(safe_float(analysis.get("Volume"))),
                "Beginner meaning": "How many shares traded in the current feed window.",
            },
            {
                "Fact": "Average volume",
                "Value": compact_number(safe_float(analysis.get("Average volume"))),
                "Beginner meaning": "Normal activity estimate used to calculate RVOL.",
            },
            {
                "Fact": "Float estimate",
                "Value": f"{safe_float(analysis.get('Float M'), 0) or 0:.1f}M",
                "Beginner meaning": "Lower float can move faster, but the estimate may come from a profile source.",
            },
            {
                "Fact": "Float source",
                "Value": str(analysis.get("Float source", "n/a")),
                "Beginner meaning": "Shows whether float came from Yahoo, a shares-outstanding proxy, or a local estimate.",
            },
            {
                "Fact": "Quote source",
                "Value": str(analysis.get("Data source", "n/a")),
                "Beginner meaning": "Where the active price came from.",
            },
            {
                "Fact": "Quote age",
                "Value": str(confidence["age"]),
                "Beginner meaning": "How old the displayed quote time looks from this computer.",
            },
            {
                "Fact": "Confidence",
                "Value": f"{confidence['label']} ({confidence['score']}/100)",
                "Beginner meaning": "Quick trust check based on source, quote age, fallback data, and mismatch risk.",
            },
        ]
    )


def risk_math_frame(analysis: dict[str, Any], paper_risk: float = 25.0) -> pd.DataFrame:
    levels = chart_trade_levels(analysis)
    entry = levels["entry"]
    stop = levels["stop"]
    target_1 = levels["target_1"]
    target_2 = levels["target_2"]
    risk_per_share = (entry - stop) if entry is not None and stop is not None else None
    reward_1 = (target_1 - entry) if target_1 is not None and entry is not None else None
    reward_2 = (target_2 - entry) if target_2 is not None and entry is not None else None
    rr_1 = (reward_1 / risk_per_share) if reward_1 is not None and risk_per_share and risk_per_share > 0 else None
    rr_2 = (reward_2 / risk_per_share) if reward_2 is not None and risk_per_share and risk_per_share > 0 else None
    shares = math.floor(paper_risk / risk_per_share) if risk_per_share and risk_per_share > 0 else None

    return pd.DataFrame(
        [
            {
                "Question": "What is the planned entry?",
                "Answer": money(entry),
                "Beginner meaning": "This is the confirmation price the practice plan waits for.",
            },
            {
                "Question": "What is the planned stop?",
                "Answer": money(stop),
                "Beginner meaning": "This is where the idea is wrong.",
            },
            {
                "Question": "Risk per share",
                "Answer": money(risk_per_share),
                "Beginner meaning": "Entry minus stop. This is the amount at risk on each paper share.",
            },
            {
                "Question": "Reward to take profit 1",
                "Answer": money(reward_1),
                "Beginner meaning": f"About {rr_1:.2f}R if target 1 hits." if rr_1 is not None else "Needs valid entry, stop, and target.",
            },
            {
                "Question": "Reward to runner target",
                "Answer": money(reward_2),
                "Beginner meaning": f"About {rr_2:.2f}R if the runner target hits." if rr_2 is not None else "Needs valid entry, stop, and target.",
            },
            {
                "Question": f"Example with {money(paper_risk)} paper risk",
                "Answer": f"{shares:,} shares" if shares else "n/a",
                "Beginner meaning": "This is practice position-size math, not a real-trade recommendation.",
            },
        ]
    )


def render_beginner_stock_summary(analysis: dict[str, Any], chart_source: str | None = None) -> None:
    ticker = str(analysis.get("Ticker", "Stock"))
    company = str(analysis.get("Company", ticker))
    sector = str(analysis.get("Sector", "n/a"))
    source = str(analysis.get("Data source", "n/a"))
    quote_time = str(analysis.get("Quote time", "n/a"))
    asset_type = asset_type_label(analysis)
    action_label, action_text = ai_action_summary(analysis)
    status = live_status(analysis)
    fit = str(analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score"))))
    data_quality, data_color = data_quality_badge(source)
    levels = chart_trade_levels(analysis)
    warnings = [str(item) for item in analysis.get("Warnings", [])]
    reasons = [str(item) for item in analysis.get("Reasons", [])]
    catalyst = str(analysis.get("Catalyst", "")).strip()
    confidence = data_confidence_summary(analysis, chart_source)

    with st.container(border=True):
        st.markdown("**Plain-English stock guide**")
        with st.container(horizontal=True):
            st.badge(action_label, icon=":material/psychology:", color="green" if action_label in {"Trigger active", "In buy zone"} else "orange")
            st.badge(status, icon=":material/radar:", color="green" if status in {"Breakout trigger", "In buy zone"} else "blue")
            st.badge(fit, icon=":material/filter_alt:", color=playbook_fit_color(fit))
            st.badge(data_quality, icon=":material/database:", color=data_color)
            st.badge(str(confidence["label"]), icon=":material/verified:", color=str(confidence["color"]))

        cols = st.columns(4)
        cols[0].metric("Stock", ticker, company[:34], border=True)
        cols[1].metric("Price now", money(safe_float(analysis.get("Price"))), pct(safe_float(analysis.get("Daily gain %"))), border=True)
        cols[2].metric("Attention", f"{safe_float(analysis.get('RVOL'), 0) or 0:.1f}x RVOL", compact_number(safe_float(analysis.get("Volume"))), border=True)
        cols[3].metric("AI score", f"{int(safe_float(analysis.get('AI score'), 0) or 0)}/100", str(analysis.get("Setup", "n/a")), border=True)

        st.markdown(markdown_text(f"**What it is:** {ticker} is {article_for(asset_type)} {asset_type}. Company/name: {company}. Group: {sector}."))
        st.markdown(markdown_text(f"**What is happening:** {beginner_movement_text(analysis, asset_type)}"))
        st.markdown(markdown_text(f"**Why traders care:** {first_readable(reasons, catalyst or 'The app has not found a strong rule-based reason yet.')}"))
        st.markdown(markdown_text(f"**What the AI helper says:** {action_text}"))

        with st.expander("Stock facts in plain English", expanded=False, icon=":material/fact_check:"):
            st.dataframe(stock_fact_sheet_frame(analysis, chart_source), width="stretch", hide_index=True)

        level_rows = pd.DataFrame(
            [
                {
                    "Level": "Buy zone",
                    "Number": f"{money(levels['buy_low'])} - {money(levels['buy_high'])}",
                    "Beginner meaning": "The practice area where a pullback still looks controlled.",
                },
                {
                    "Level": "Entry trigger",
                    "Number": money(levels["entry"]),
                    "Beginner meaning": "The confirmation price. Beginners should avoid guessing before this.",
                },
                {
                    "Level": "Stop loss",
                    "Number": money(levels["stop"]),
                    "Beginner meaning": "Where the plan is wrong. If this is hit, the practice idea is invalid.",
                },
                {
                    "Level": "Take profit 1",
                    "Number": money(levels["target_1"]),
                    "Beginner meaning": "The first planned area to lock in paper-trade reward.",
                },
                {
                    "Level": "Runner target",
                    "Number": money(levels["target_2"]),
                    "Beginner meaning": "A second planned exit if the move keeps working.",
                },
            ]
        )
        st.dataframe(level_rows, width="stretch", hide_index=True)

        with st.expander("Risk and reward math", expanded=False, icon=":material/calculate:"):
            st.caption("Paper-trade math example. Always adjust risk yourself and never treat the example share size as financial advice.")
            st.dataframe(risk_math_frame(analysis), width="stretch", hide_index=True)

        explain_cols = st.columns(2)
        with explain_cols[0]:
            st.markdown("**Beginner read**")
            st.write(f"- {beginner_attention_text(analysis)}")
            st.write(f"- {beginner_float_text(analysis, asset_type)}")
            st.write("- Entry, stop, and targets are study levels. They are not a guarantee and they are not financial advice.")
        with explain_cols[1]:
            st.markdown("**Data trust check**")
            st.write(f"- Active price source: {source}")
            st.write(f"- Quote time: {quote_time} ({confidence['age']})")
            st.write(f"- Chart candle source: {chart_source or source}")
            st.write(f"- Confidence: {confidence['label']} ({confidence['score']}/100)")
            if "learning" in f"{source} {chart_source}".lower():
                st.warning("This stock is using learning fallback data somewhere in the view. Treat it as practice only.", icon=":material/school:")
            elif warnings:
                st.write(f"- Main caution: {first_readable(warnings, 'No major warning.', limit=1)}")
            else:
                st.write("- No major rule warning from the current model, but still verify news, spread, and risk.")


def chart_trade_levels(analysis: dict[str, Any]) -> dict[str, float | None]:
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    buy_mid = None
    if buy_low is not None and buy_high is not None:
        buy_mid = (buy_low + buy_high) / 2
    return {
        "buy_low": buy_low,
        "buy_high": buy_high,
        "buy_mid": buy_mid,
        "entry": safe_float(analysis.get("Entry trigger price")),
        "stop": safe_float(analysis.get("Stop price")),
        "target_1": safe_float(analysis.get("Target 1 price")),
        "target_2": safe_float(analysis.get("Target 2 price")),
    }


def render_ai_chart_trade_map(analysis: dict[str, Any]) -> None:
    levels = chart_trade_levels(analysis)
    status = live_status(analysis)
    label, _ = ai_action_summary(analysis)
    with st.container(border=True):
        st.markdown("**AI chart trade map**")
        with st.container(horizontal=True):
            st.badge(label, icon=":material/psychology:", color="green" if status in {"Breakout trigger", "In buy zone"} else "orange" if status in {"Near buy zone", "Momentum active"} else "gray")
            st.badge(status, icon=":material/candlestick_chart:", color="green" if status in {"Breakout trigger", "In buy zone"} else "orange" if status == "Near buy zone" else "gray")
            st.badge("Paper-trade only", icon=":material/edit_note:", color="blue")

        cols = st.columns(4)
        cols[0].metric("Watch buy area", analysis.get("Buy zone", "n/a"), border=True)
        cols[1].metric("Buy only after", money(levels["entry"]), border=True)
        cols[2].metric("Stop if wrong", money(levels["stop"]), border=True)
        cols[3].metric("Sell / trim target", money(levels["target_1"]), border=True)
        st.caption(
            "The chart markers show the paper buy area, confirmation trigger, invalidation stop, and sell/trim targets. "
            "They are decision aids, not real trade instructions."
        )


def render_premium_trade_ticket(analysis: dict[str, Any]) -> None:
    levels = chart_trade_levels(analysis)
    price = safe_float(analysis.get("Price"))
    entry = levels["entry"]
    stop = levels["stop"]
    target = levels["target_1"]
    risk = (entry - stop) if entry is not None and stop is not None else None
    reward = (target - entry) if target is not None and entry is not None else None
    risk_reward = (reward / risk) if risk and reward is not None and risk > 0 else None
    distance = ((entry - price) / price * 100) if entry is not None and price else None
    status = live_status(analysis)
    with st.container(border=True):
        st.markdown("**Trade ticket preview**")
        items = [
            ("Current", money(price), status, "neutral"),
            ("Entry trigger", money(entry), "Buy only after confirmation", "profit"),
            ("Stop loss", money(stop), f"Risk per share {money(risk)}" if risk else "Risk defined here", "danger"),
            ("Take profit 1", money(target), f"Reward {money(reward)}" if reward else "First trim target", "profit"),
            ("Take profit 2", money(levels["target_2"]), "Runner target", "profit"),
        ]
        card_parts = ['<div class="msa-level-board">']
        for label, value, detail, tone in items:
            card_parts.append(
                '<div class="msa-level-card msa-level-{tone}">'
                '<div class="msa-level-label">{label}</div>'
                '<div class="msa-level-value">{value}</div>'
                '<div class="msa-level-detail">{detail}</div>'
                '</div>'.format(
                    tone=html.escape(tone),
                    label=html.escape(label),
                    value=html.escape(value),
                    detail=html.escape(str(detail)),
                )
            )
        card_parts.append("</div>")
        render_html("".join(card_parts))
        cols = st.columns(3)
        cols[0].metric("Distance to entry", pct(distance) if distance is not None else "wait", border=True)
        cols[1].metric("Target 1 R:R", f"{risk_reward:.2f}R" if risk_reward is not None else "n/a", border=True)
        cols[2].metric("Playbook fit", str(analysis.get("Playbook fit", "n/a")), border=True)
        st.caption("Paper-trade preview only. Confirm news, spread, volume, and broker rules before any real order.")


def chart_timestamp_seconds(value: Any) -> int:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return int(timestamp.timestamp())


def chart_timeframe_label(chart_df: pd.DataFrame) -> str:
    if chart_df is None or len(chart_df.index) < 2:
        return "chart"
    try:
        index_series = pd.Series(pd.DatetimeIndex(chart_df.index), index=chart_df.index)
        median_step = index_series.diff().dropna().median()
        if pd.isna(median_step):
            return "chart"
        minutes = max(int(round(median_step / pd.Timedelta(minutes=1))), 1)
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h" if hours.is_integer() else f"{hours:.1f}h"
        days = max(int(round(hours / 24)), 1)
        return f"{days}D"
    except Exception:
        return "chart"


def chart_series_points(chart_df: pd.DataFrame, column: str) -> list[dict[str, float | int]]:
    if column not in chart_df.columns:
        return []
    rows: list[dict[str, float | int]] = []
    for _, row in chart_df.dropna(subset=[column]).iterrows():
        value = safe_float(row.get(column))
        if value is None or not math.isfinite(value):
            continue
        rows.append({"time": chart_timestamp_seconds(row["Time"]), "value": round(float(value), 4)})
    return rows


@st.cache_data(show_spinner=False)
def lightweight_charts_script() -> str:
    if LIGHTWEIGHT_CHARTS_FILE.exists():
        try:
            return LIGHTWEIGHT_CHARTS_FILE.read_text(encoding="utf-8").replace("</script", "<\\/script")
        except Exception:
            return ""
    return ""


def lightweight_chart_payload(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    visible_candles: int | None,
) -> dict[str, Any]:
    clean_df = chart_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["Open", "High", "Low", "Close"]).copy()
    candles: list[dict[str, float | int]] = []
    volume: list[dict[str, float | int | str]] = []
    palette = theme_palette()
    up = "#00C805"
    down = "#FF375F"
    show_ema9 = bool(st.session_state.get("chart_layer_ema9", True))
    show_ema20 = bool(st.session_state.get("chart_layer_ema20", True))
    show_vwap = bool(st.session_state.get("chart_layer_vwap", True))
    show_buy_zone = bool(st.session_state.get("chart_layer_buy_zone", True))
    show_plan_levels = bool(st.session_state.get("chart_layer_plan_levels", True))
    show_ai_signals = bool(st.session_state.get("chart_layer_ai_signals", True))

    for _, row in clean_df.iterrows():
        candle_time = chart_timestamp_seconds(row["Time"])
        open_price = float(row["Open"])
        close_price = float(row["Close"])
        candles.append(
            {
                "time": candle_time,
                "open": round(open_price, 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(close_price, 4),
            }
        )
        volume.append(
            {
                "time": candle_time,
                "value": max(float(row.get("Volume", 0) or 0), 0),
                "color": "rgba(0, 200, 5, 0.50)" if close_price >= open_price else "rgba(255, 55, 95, 0.48)",
            }
        )

    active_end_index = len(candles) - 1
    for index in range(len(candles) - 1, -1, -1):
        candle = candles[index]
        vol = safe_float(volume[index].get("value"), 0) if index < len(volume) else 0
        has_range = abs(float(candle["high"]) - float(candle["low"])) > 0.001
        has_body = abs(float(candle["close"]) - float(candle["open"])) > 0.001
        if (vol or 0) > 0 and (has_range or has_body):
            active_end_index = index
            break

    levels = chart_trade_levels(analysis)
    price_lines: list[dict[str, Any]] = []

    def add_price_line(
        label: str,
        value: float | None,
        color: str,
        style: str = "dashed",
        axis_label: bool = True,
    ) -> None:
        if value is not None and math.isfinite(float(value)):
            price_lines.append(
                {
                    "title": label,
                    "price": round(float(value), 4),
                    "color": color,
                    "style": style,
                    "axisLabel": axis_label,
                }
            )

    if show_buy_zone:
        add_price_line("Buy low", levels["buy_low"], palette["cyan"], axis_label=False)
        add_price_line("Buy high", levels["buy_high"], palette["cyan"], axis_label=False)
    if show_plan_levels:
        add_price_line("Buy", levels["entry"], up)
        add_price_line("SL", levels["stop"], down)
        add_price_line("TP", levels["target_1"], up)
        add_price_line("TP2", levels["target_2"], "#86EFAC", axis_label=False)

    markers: list[dict[str, Any]] = []
    if candles:
        last_time = candles[-1]["time"]
        status = live_status(analysis)
        if show_ai_signals and status in {"Breakout trigger", "In buy zone", "Near buy zone"}:
            markers.append(
                {
                    "time": last_time,
                    "position": "belowBar",
                    "color": up,
                    "shape": "arrowUp",
                    "text": "Buy",
                }
            )
        elif show_ai_signals and status == "Below stop":
            markers.append(
                {
                    "time": last_time,
                    "position": "aboveBar",
                    "color": down,
                    "shape": "square",
                    "text": "Stop",
                }
            )

    buy_zone = None
    if show_buy_zone and levels["buy_low"] is not None and levels["buy_high"] is not None:
        buy_zone = {
            "low": round(float(min(levels["buy_low"], levels["buy_high"])), 4),
            "high": round(float(max(levels["buy_low"], levels["buy_high"])), 4),
        }

    def clean_level(value: Any) -> float | None:
        numeric = safe_float(value)
        if numeric is None or not math.isfinite(float(numeric)):
            return None
        return round(float(numeric), 4)

    entry_level = clean_level(levels["entry"])
    stop_level = clean_level(levels["stop"])
    target_1_level = clean_level(levels["target_1"])
    target_2_level = clean_level(levels["target_2"])
    risk_reward = None
    if entry_level is not None and stop_level is not None and target_1_level is not None:
        risk_amount = abs(entry_level - stop_level)
        reward_amount = abs(target_1_level - entry_level)
        if risk_amount > 0:
            risk_reward = round(reward_amount / risk_amount, 2)

    level_summary = [
        {"label": "Buy", "value": money(levels["entry"]), "tone": "up", "detail": "AI entry"},
        {"label": "Stop", "value": money(levels["stop"]), "tone": "down", "detail": "risk line"},
        {"label": "TP1", "value": money(levels["target_1"]), "tone": "up", "detail": "first sell"},
        {"label": "TP2", "value": money(levels["target_2"]), "tone": "up", "detail": "runner"},
    ]
    status = live_status(analysis)
    side_panel = {
        "status": status,
        "setup": str(analysis.get("Setup", "n/a")),
        "confidence": str(analysis.get("Confidence", "n/a")),
        "fit": str(analysis.get("Playbook fit", "n/a")),
        "score": int(safe_float(analysis.get("AI score"), 0) or 0),
        "source": str(analysis.get("Data source", "n/a")),
        "price": money(current_price),
        "riskReward": f"{risk_reward:.2f}R" if risk_reward is not None else "n/a",
    }

    return {
        "ticker": str(analysis.get("Ticker", "Stock")),
        "company": str(analysis.get("Company", analysis.get("Ticker", "Stock"))),
        "exchange": str(analysis.get("Exchange", "")),
        "timeframe": chart_timeframe_label(clean_df),
        "lastColor": up if candles and candles[-1]["close"] >= candles[-1]["open"] else down,
        "candles": candles,
        "volume": volume,
        "ema9": chart_series_points(clean_df, "EMA 9") if show_ema9 else [],
        "ema20": chart_series_points(clean_df, "EMA 20") if show_ema20 else [],
        "vwap": chart_series_points(clean_df, "VWAP") if show_vwap else [],
        "priceLines": price_lines,
        "markers": markers,
        "buyZone": buy_zone,
        "tradeLevels": {
            "entry": entry_level,
            "stop": stop_level,
            "target1": target_1_level,
            "target2": target_2_level,
            "riskReward": risk_reward,
        }
        if show_plan_levels
        else {},
        "levelSummary": level_summary if show_plan_levels else [],
        "visibleCount": int(visible_candles or min(len(candles), 60)),
        "activeEndIndex": int(active_end_index),
        "lastTime": int(candles[active_end_index]["time"]) if candles else None,
        "sidePanel": side_panel,
        "palette": palette,
        "status": status,
    }


def render_lightweight_trading_chart(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    height: int,
    visible_candles: int | None,
) -> bool:
    payload = lightweight_chart_payload(chart_df, analysis, current_price, visible_candles)
    if not payload["candles"]:
        return False

    chart_height = max(height + 260, 750)
    chart_script = lightweight_charts_script()
    chart_loader = (
        f"<script>\n{chart_script}\n</script>"
        if chart_script
        else '<script src="https://unpkg.com/lightweight-charts@4.2.3/dist/lightweight-charts.standalone.production.js"></script>'
    )
    component_html = """
<div class="tw-shell">
  <div class="tw-toolbar">
    <div class="tw-brand">
      <strong id="tw-symbol">__TICKER__</strong>
      <span id="tw-status"></span>
      <a class="tw-credit" href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Lightweight Charts by TradingView</a>
    </div>
    <div class="tw-controls">
      <div class="tw-buttons" aria-label="Chart window buttons">
        <span>Window</span>
        <button data-range="15" title="Show 15 candles">15</button>
        <button data-range="30" title="Show 30 candles">30</button>
        <button data-range="45" title="Show 45 candles">45</button>
        <button data-range="90" title="Show 90 candles">90</button>
        <button data-range="180" title="Show 180 candles">180</button>
        <button data-range="390" title="Show about one full trading day">1 day</button>
        <button data-range="all" title="Fit all loaded candles">Fit</button>
      </div>
      <div class="tw-nav-buttons" aria-label="Chart navigation buttons">
        <button data-action="zoom-out" title="Zoom out">-</button>
        <button data-action="zoom-in" title="Zoom in">+</button>
        <button data-action="back" title="Step back through older candles">Back</button>
        <button data-action="forward" title="Step forward">Forward</button>
        <button data-action="latest" title="Jump to latest candles">Latest</button>
      </div>
    </div>
  </div>
  <div class="tw-subbar">
    <div id="tw-legend" class="tw-legend"></div>
    <div class="tw-hint">Wheel zoom | Drag pan | Double-click reset</div>
  </div>
  <div id="tw-planbar" class="tw-planbar"></div>
  <div class="tw-workspace">
    <div class="tw-stage">
      <div id="tw-chart" class="tw-chart"></div>
      <canvas id="tw-wick-layer" class="tw-wick-layer" aria-hidden="true"></canvas>
      <div class="tw-watermark">__TICKER__</div>
    </div>
    <aside class="tw-side-panel" aria-label="AI trade plan summary">
      <div class="tw-side-head">
        <span>AI plan</span>
        <strong id="tw-side-score"></strong>
      </div>
      <div id="tw-side-body" class="tw-side-body"></div>
    </aside>
  </div>
  <div class="tw-footer">
    <div class="tw-footer-buttons" aria-label="Calendar range buttons">
      <button data-calendar-range="1D" title="Show the latest day available">1D</button>
      <button data-calendar-range="5D" title="Show the latest five days available">5D</button>
      <button data-calendar-range="1M" title="Show the latest month available">1M</button>
      <button data-calendar-range="3M" title="Show the latest three months available">3M</button>
      <button data-calendar-range="6M" title="Show the latest six months available">6M</button>
      <button data-calendar-range="YTD" title="Show year to date">YTD</button>
      <button data-calendar-range="1Y" title="Show the latest year available">1Y</button>
      <button data-calendar-range="5Y" title="Show the latest five years available">5Y</button>
      <button data-calendar-range="All" title="Fit all loaded data">All</button>
    </div>
    <div class="tw-footer-meta">
      <span id="tw-clock" class="tw-footer-pill"></span>
      <span class="tw-footer-pill">RTH</span>
      <span class="tw-footer-pill">ADJ</span>
    </div>
  </div>
</div>
__LIGHTWEIGHT_CHARTS_LOADER__
<script>
(() => {
  const payload = __PAYLOAD__;
  const palette = payload.palette;
  const shell = document.querySelector(".tw-shell");
  const container = document.getElementById("tw-chart");
  const wickCanvas = document.getElementById("tw-wick-layer");
  const wickContext = wickCanvas.getContext("2d");
  const legend = document.getElementById("tw-legend");
  const planbar = document.getElementById("tw-planbar");
  const status = document.getElementById("tw-status");
  const symbol = document.getElementById("tw-symbol");
  const clock = document.getElementById("tw-clock");
  const sideScore = document.getElementById("tw-side-score");
  const sideBody = document.getElementById("tw-side-body");
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
  const fmt = (value) => Number.isFinite(Number(value)) ? "$" + Number(value).toFixed(2) : "n/a";
  const fmtVol = (value) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const fmtTime = (time) => new Date(Number(time) * 1000).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });

  symbol.textContent = payload.ticker;
  status.textContent = [
    payload.company && payload.company !== payload.ticker ? payload.company : "",
    payload.timeframe || "",
    payload.exchange || "",
    payload.status || ""
  ].filter(Boolean).join(" - ");
  if (payload.levelSummary && payload.levelSummary.length) {
    planbar.innerHTML = payload.levelSummary.map((item) =>
      "<div class='tw-level-chip tw-level-" + esc(item.tone) + "'>" +
      "<span>" + esc(item.label) + "</span>" +
      "<strong>" + esc(item.value) + "</strong>" +
      "<em>" + esc(item.detail) + "</em>" +
      "</div>"
    ).join("");
  } else {
    planbar.innerHTML = "<div class='tw-level-chip'><span>Levels</span><strong>Hidden</strong><em>toggle on</em></div>";
  }
  const side = payload.sidePanel || {};
  const statusTone = ["Breakout trigger", "In buy zone"].includes(side.status) ? "ready" :
    ["Near buy zone", "Momentum active", "Watching"].includes(side.status) ? "watch" :
    side.status === "Below stop" ? "danger" : "neutral";
  const nextMove = statusTone === "ready"
    ? "Review spread, news, volume, and paper-order approval before any action."
    : statusTone === "watch"
      ? "Wait for a cleaner trigger. Do not chase a candle that already moved."
      : statusTone === "danger"
        ? "Plan is invalid until price reclaims the setup area."
        : "Keep scanning and compare this stock against stronger setups.";
  sideScore.textContent = Number.isFinite(Number(side.score)) ? Number(side.score) + "/100" : "n/a";
  sideBody.innerHTML =
    "<div class='tw-side-status tw-side-" + statusTone + "'>" +
      "<span>Status</span><strong>" + esc(side.status || "Watching") + "</strong>" +
    "</div>" +
    "<div class='tw-side-grid'>" +
      "<div><span>Price</span><strong>" + esc(side.price || "n/a") + "</strong></div>" +
      "<div><span>R/R</span><strong>" + esc(side.riskReward || "n/a") + "</strong></div>" +
      "<div><span>Setup</span><strong>" + esc(side.setup || "n/a") + "</strong></div>" +
      "<div><span>Trust</span><strong>" + esc(side.confidence || "n/a") + "</strong></div>" +
    "</div>" +
    "<div class='tw-side-note'>" + esc(nextMove) + "</div>" +
    "<div class='tw-side-source'><span>Source</span><strong>" + esc(side.source || "n/a") + "</strong></div>";
  if (!window.LightweightCharts) {
    container.innerHTML = "<div class='tw-error'>The chart library did not load. Switch Chart style to Backup Plotly in Chart controls.</div>";
    return;
  }

  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth,
    height: container.clientHeight,
    layout: {
      background: { type: "solid", color: palette.panel },
      textColor: palette.text,
      fontFamily: "Inter, Arial, sans-serif"
    },
    grid: {
      vertLines: { color: palette.chart_grid || palette.grid },
      horzLines: { color: palette.chart_grid || palette.grid }
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: palette.muted_soft, width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: palette.blue },
      horzLine: { color: palette.muted_soft, width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: palette.blue }
    },
    localization: {
      priceFormatter: fmt,
      timeFormatter: fmtTime
    },
    rightPriceScale: {
      borderColor: palette.border,
      scaleMargins: { top: 0.08, bottom: 0.14 },
      entireTextOnly: true,
      ticksVisible: true,
      minimumWidth: 78
    },
    timeScale: {
      borderColor: palette.border,
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 12,
      barSpacing: 18,
      minBarSpacing: 8,
      fixLeftEdge: false,
      fixRightEdge: false,
      lockVisibleTimeRangeOnResize: true,
      rightBarStaysOnScroll: true,
      shiftVisibleRangeOnNewBar: true
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: true
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      priceScale: true,
      pinch: true
    }
  });

  const ro = new ResizeObserver((entries) => {
    const entry = entries[0];
    if (!entry) return;
    const width = Math.max(Math.floor(entry.contentRect.width), 320);
    const height = Math.max(Math.floor(entry.contentRect.height), 360);
    chart.applyOptions({ width, height });
    requestAnimationFrame(drawWicks);
  });
  ro.observe(container);

  const candleSeries = chart.addCandlestickSeries({
    upColor: "#00C805",
    downColor: "#FF375F",
    borderVisible: true,
    borderUpColor: "#00C805",
    borderDownColor: "#FF375F",
    wickUpColor: "#00C805",
    wickDownColor: "#FF375F",
    wickVisible: true,
    priceFormat: { type: "price", precision: 2, minMove: 0.01 },
    lastValueVisible: true,
    priceLineVisible: true,
    priceLineColor: payload.lastColor || palette.text,
    priceLineWidth: 1,
    priceLineStyle: LightweightCharts.LineStyle.Dotted,
    autoscaleInfoProvider: (original) => {
      const result = original();
      if (!result || !result.priceRange) return result;
      const minValue = Number(result.priceRange.minValue);
      const maxValue = Number(result.priceRange.maxValue);
      if (!Number.isFinite(minValue) || !Number.isFinite(maxValue)) return result;
      const span = Math.max(maxValue - minValue, Math.max(Math.abs(maxValue) * 0.0025, 0.02));
      return {
        priceRange: {
          minValue: minValue - span * 0.16,
          maxValue: maxValue + span * 0.18
        },
        margins: {
          above: 8,
          below: 10
        }
      };
    }
  });
  candleSeries.setData(payload.candles);

  const volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: "volume" },
    priceScaleId: "volume",
    lastValueVisible: false,
    priceLineVisible: false
  });
  volumeSeries.setData(payload.volume);
  chart.priceScale("volume").applyOptions({
    scaleMargins: { top: 0.80, bottom: 0 },
    visible: false
  });

  const addLineSeries = (data, color, title, width) => {
    if (!data.length) return;
    const series = chart.addLineSeries({
      color,
      lineWidth: width,
      title: "",
      priceLineVisible: false,
      lastValueVisible: false,
      autoscaleInfoProvider: () => null
    });
    series.setData(data);
    series.applyOptions({
      priceLineVisible: false,
      lastValueVisible: false,
      title: ""
    });
  };
  addLineSeries(payload.ema9, palette.blue, "EMA 9", 2);
  addLineSeries(payload.ema20, palette.violet, "EMA 20", 2);
  addLineSeries(payload.vwap, palette.orange, "VWAP", 2);

  payload.priceLines.forEach((line) => {
    candleSeries.createPriceLine({
      price: line.price,
      color: line.color,
      lineWidth: line.style === "solid" ? 2 : 1,
      lineStyle: line.style === "solid" ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: line.axisLabel !== false,
      title: line.title
    });
  });

  if (payload.markers.length && candleSeries.setMarkers) {
    candleSeries.setMarkers(payload.markers);
  }

  const resizeWickCanvas = () => {
    const rect = container.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(Math.floor(rect.width), 320);
    const height = Math.max(Math.floor(rect.height), 360);
    wickCanvas.style.width = width + "px";
    wickCanvas.style.height = height + "px";
    if (wickCanvas.width !== Math.floor(width * ratio) || wickCanvas.height !== Math.floor(height * ratio)) {
      wickCanvas.width = Math.floor(width * ratio);
      wickCanvas.height = Math.floor(height * ratio);
    }
    wickContext.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { width, height };
  };

  const visibleSpacing = (size) => {
    const range = chart.timeScale().getVisibleLogicalRange();
    const count = range ? Math.max(range.to - range.from, 1) : Math.max(payload.visibleCount || 90, 1);
    return Math.max(size.width / count, 2);
  };

  const drawBuyZone = (size) => {
    if (!payload.buyZone) return;
    const yHigh = candleSeries.priceToCoordinate(payload.buyZone.high);
    const yLow = candleSeries.priceToCoordinate(payload.buyZone.low);
    if (!Number.isFinite(yHigh) || !Number.isFinite(yLow)) return;
    const top = Math.min(yHigh, yLow);
    const height = Math.max(Math.abs(yLow - yHigh), 2);
    wickContext.fillStyle = "rgba(34, 211, 238, 0.045)";
    wickContext.fillRect(0, top, size.width, height);
    wickContext.strokeStyle = "rgba(34, 211, 238, 0.46)";
    wickContext.lineWidth = 1;
    wickContext.setLineDash([5, 5]);
    wickContext.beginPath();
    wickContext.moveTo(0, Math.round(top) + 0.5);
    wickContext.lineTo(size.width, Math.round(top) + 0.5);
    wickContext.moveTo(0, Math.round(top + height) + 0.5);
    wickContext.lineTo(size.width, Math.round(top + height) + 0.5);
    wickContext.stroke();
    wickContext.setLineDash([]);
  };

  const drawSessionSeparators = (size) => {
    const range = chart.timeScale().getVisibleLogicalRange();
    const from = Math.max(1, Math.floor((range ? range.from : 0) - 4));
    const to = Math.min(payload.candles.length - 1, Math.ceil((range ? range.to : payload.candles.length - 1) + 4));
    wickContext.save();
    wickContext.strokeStyle = palette.chart_grid || palette.grid;
    wickContext.fillStyle = palette.muted_soft;
    wickContext.globalAlpha = 0.72;
    wickContext.lineWidth = 1;
    wickContext.font = "11px Inter, Arial, sans-serif";
    wickContext.textBaseline = "bottom";
    for (let index = from; index <= to; index += 1) {
      const current = payload.candles[index];
      const previous = payload.candles[index - 1];
      if (!current || !previous) continue;
      const currentDay = new Date(Number(current.time) * 1000).toISOString().slice(0, 10);
      const previousDay = new Date(Number(previous.time) * 1000).toISOString().slice(0, 10);
      if (currentDay === previousDay) continue;
      const x = chart.timeScale().timeToCoordinate(current.time);
      if (!Number.isFinite(x) || x < 0 || x > size.width) continue;
      wickContext.beginPath();
      wickContext.moveTo(Math.round(x) + 0.5, 0);
      wickContext.lineTo(Math.round(x) + 0.5, size.height);
      wickContext.stroke();
      const label = new Date(Number(current.time) * 1000).toLocaleDateString([], { month: "short", day: "numeric" });
      wickContext.fillText(label, Math.min(Math.round(x) + 6, size.width - 52), size.height - 18);
    }
    wickContext.restore();
  };

  const drawZoneLabel = (text, x, y, color) => {
    if (!text || !Number.isFinite(x) || !Number.isFinite(y)) return;
    wickContext.save();
    wickContext.font = "11px Inter, Arial, sans-serif";
    wickContext.textBaseline = "middle";
    const width = wickContext.measureText(text).width + 14;
    wickContext.fillStyle = String(palette.panel).toUpperCase() === "#FFFFFF" ? "rgba(255, 255, 255, 0.78)" : "rgba(11, 17, 23, 0.62)";
    wickContext.strokeStyle = color;
    wickContext.lineWidth = 1;
    wickContext.beginPath();
    roundedRectPath(wickContext, x, y - 10, width, 20, 4);
    wickContext.fill();
    wickContext.stroke();
    wickContext.fillStyle = color;
    wickContext.fillText(text, x + 7, y + 0.5);
    wickContext.restore();
  };

  const drawTradePlanCloud = (size) => {
    const levels = payload.tradeLevels || {};
    if (!Number.isFinite(Number(levels.entry)) || !Number.isFinite(Number(levels.stop)) || !Number.isFinite(Number(levels.target1))) return;
    const yEntry = candleSeries.priceToCoordinate(Number(levels.entry));
    const yStop = candleSeries.priceToCoordinate(Number(levels.stop));
    const yTarget = candleSeries.priceToCoordinate(Number(levels.target1));
    if (!Number.isFinite(yEntry) || !Number.isFinite(yStop) || !Number.isFinite(yTarget)) return;
    const width = Math.min(280, Math.max(150, size.width * 0.26));
    const x = Math.max(0, size.width - width - 2);
    const rewardTop = Math.min(yEntry, yTarget);
    const rewardHeight = Math.max(Math.abs(yTarget - yEntry), 3);
    const riskTop = Math.min(yEntry, yStop);
    const riskHeight = Math.max(Math.abs(yStop - yEntry), 3);
    const yVisible = (value) => Number.isFinite(value) && value >= 0 && value <= size.height;
    const entryVisible = yVisible(yEntry);
    const rewardVisible = entryVisible && yVisible(yTarget) && rewardHeight <= size.height * 0.48;
    const riskVisible = entryVisible && yVisible(yStop) && riskHeight <= size.height * 0.48;
    if (!rewardVisible && !riskVisible) {
      if (entryVisible && yTarget < 0) drawZoneLabel("TP1 above", x + 10, 24, "#00C805");
      if (entryVisible && yStop > size.height) drawZoneLabel("Stop below", x + 10, size.height - 38, "#FF375F");
      return;
    }
    wickContext.save();
    wickContext.lineWidth = 1;
    if (rewardVisible) {
      wickContext.fillStyle = "rgba(0, 200, 5, 0.045)";
      wickContext.fillRect(x, rewardTop, width, rewardHeight);
      wickContext.strokeStyle = "rgba(0, 200, 5, 0.20)";
      wickContext.strokeRect(x + 0.5, rewardTop + 0.5, width - 1, rewardHeight);
    }
    if (riskVisible) {
      wickContext.fillStyle = "rgba(255, 55, 95, 0.050)";
      wickContext.fillRect(x, riskTop, width, riskHeight);
      wickContext.strokeStyle = "rgba(255, 55, 95, 0.22)";
      wickContext.strokeRect(x + 0.5, riskTop + 0.5, width - 1, riskHeight);
    }
    wickContext.restore();
    if (rewardVisible && rewardHeight >= 24) {
      const rr = Number.isFinite(Number(levels.riskReward)) ? " " + Number(levels.riskReward).toFixed(2) + "R" : "";
      drawZoneLabel("TP path" + rr, x + 10, rewardTop + rewardHeight / 2, "#00C805");
    }
    if (riskVisible && riskHeight >= 24) {
      drawZoneLabel("Risk zone", x + 10, riskTop + riskHeight / 2, "#FF375F");
    }
    if (entryVisible && !rewardVisible && yTarget < 0) drawZoneLabel("TP1 above", x + 10, 24, "#00C805");
    if (entryVisible && !riskVisible && yStop > size.height) drawZoneLabel("Stop below", x + 10, size.height - 38, "#FF375F");
  };

  const drawSegment = (x, y1, y2, color, width) => {
    if (!Number.isFinite(x) || !Number.isFinite(y1) || !Number.isFinite(y2)) return;
    wickContext.strokeStyle = color;
    wickContext.lineWidth = width;
    wickContext.lineCap = "round";
    wickContext.beginPath();
    wickContext.moveTo(Math.round(x) + 0.5, y1);
    wickContext.lineTo(Math.round(x) + 0.5, y2);
    wickContext.stroke();
  };

  const roundedRectPath = (ctx, x, y, width, height, radius) => {
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, y, width, height, radius);
      return;
    }
    const safeRadius = Math.min(radius, width / 2, height / 2);
    ctx.moveTo(x + safeRadius, y);
    ctx.lineTo(x + width - safeRadius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + safeRadius);
    ctx.lineTo(x + width, y + height - safeRadius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - safeRadius, y + height);
    ctx.lineTo(x + safeRadius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - safeRadius);
    ctx.lineTo(x, y + safeRadius);
    ctx.quadraticCurveTo(x, y, x + safeRadius, y);
  };

  const drawEnhancedBody = (x, openY, closeY, color, spacing) => {
    if (!Number.isFinite(x) || !Number.isFinite(openY) || !Number.isFinite(closeY)) return;
    const bodyWidth = spacing >= 5 ? Math.max(4.2, Math.min(18, spacing * 0.78)) : Math.max(2.6, spacing * 0.86);
    const left = Math.round(x - bodyWidth / 2) + 0.5;
    const top = Math.round(Math.min(openY, closeY)) + 0.5;
    const bodyHeight = Math.max(Math.abs(closeY - openY), 2.8);
    wickContext.shadowColor = "rgba(0, 0, 0, 0.18)";
    wickContext.shadowBlur = 1.2;
    wickContext.fillStyle = color;
    wickContext.strokeStyle = color;
    wickContext.lineWidth = 1;
    wickContext.beginPath();
    roundedRectPath(wickContext, left, top, bodyWidth, bodyHeight, Math.min(2.4, bodyWidth / 2));
    wickContext.fill();
    wickContext.stroke();
  };

  const drawWicks = () => {
    if (!wickContext || !payload.candles.length) return;
    const size = resizeWickCanvas();
    wickContext.clearRect(0, 0, size.width, size.height);
    const spacing = visibleSpacing(size);
    const wickWidth = spacing >= 18 ? 3.2 : spacing >= 10 ? 2.55 : spacing >= 6 ? 2.05 : 1.65;
    drawSessionSeparators(size);
    drawBuyZone(size);
    drawTradePlanCloud(size);
    const range = chart.timeScale().getVisibleLogicalRange();
    const from = Math.max(0, Math.floor((range ? range.from : 0) - 8));
    const to = Math.min(payload.candles.length - 1, Math.ceil((range ? range.to : payload.candles.length - 1) + 8));
    for (let index = from; index <= to; index += 1) {
      const bar = payload.candles[index];
      if (!bar) continue;
      const x = chart.timeScale().timeToCoordinate(bar.time);
      const yHigh = candleSeries.priceToCoordinate(bar.high);
      const yLow = candleSeries.priceToCoordinate(bar.low);
      const yBodyTop = candleSeries.priceToCoordinate(Math.max(bar.open, bar.close));
      const yBodyBottom = candleSeries.priceToCoordinate(Math.min(bar.open, bar.close));
      const yOpen = candleSeries.priceToCoordinate(bar.open);
      const yClose = candleSeries.priceToCoordinate(bar.close);
      const color = bar.close >= bar.open ? "#00C805" : "#FF375F";
      drawSegment(x, yHigh, yLow, color, wickWidth);
      drawEnhancedBody(x, yOpen, yClose, color, spacing);
    }
    wickContext.shadowBlur = 0;
  };

  chart.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(drawWicks));

  const lastBar = payload.candles[payload.candles.length - 1];
  const updateLegend = (bar, time) => {
    if (!bar) return;
    const volume = payload.volume.find((item) => item.time === time);
    const change = ((Number(bar.close) - Number(bar.open)) / Math.max(Number(bar.open), 0.01)) * 100;
    legend.innerHTML =
      "<span>" + fmtTime(time) + "</span>" +
      "<b>O</b> " + fmt(bar.open) +
      "<b>H</b> " + fmt(bar.high) +
      "<b>L</b> " + fmt(bar.low) +
      "<b>C</b> " + fmt(bar.close) +
      "<b>Vol</b> " + fmtVol(volume ? volume.value : 0) +
      "<b class='" + (change >= 0 ? "up" : "down") + "'>" + change.toFixed(2) + "%</b>";
  };
  updateLegend(lastBar, lastBar.time);

  chart.subscribeCrosshairMove((param) => {
    const bar = param && param.seriesData ? param.seriesData.get(candleSeries) : null;
    if (!param || !param.time || !bar) {
      updateLegend(lastBar, lastBar.time);
      return;
    }
    updateLegend(bar, param.time);
  });

  const rangeButtons = Array.from(document.querySelectorAll(".tw-buttons button"));
  const navButtons = Array.from(document.querySelectorAll(".tw-nav-buttons button"));
  const footerButtons = Array.from(document.querySelectorAll(".tw-footer button[data-calendar-range]"));
  let activeRange = String(Math.min(payload.visibleCount || 90, payload.candles.length));
  const maxIndex = () => Math.max(payload.candles.length - 1, 0);
  const markActive = (range) => {
    rangeButtons.forEach((button) => button.classList.toggle("active", button.dataset.range === String(range)));
  };
  const markFooterActive = (range) => {
    footerButtons.forEach((button) => button.classList.toggle("active", button.dataset.calendarRange === String(range)));
  };
  const updateClock = () => {
    if (!clock) return;
    clock.textContent = new Date().toLocaleTimeString("en-US", {
      timeZone: "UTC",
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }) + " UTC";
  };
  const clampLogicalRange = (from, to) => {
    const min = -8;
    const max = maxIndex() + 12;
    const span = Math.max(to - from, 5);
    let nextFrom = Number(from);
    let nextTo = Number(to);
    if (nextFrom < min) {
      nextFrom = min;
      nextTo = nextFrom + span;
    }
    if (nextTo > max) {
      nextTo = max;
      nextFrom = nextTo - span;
    }
    if (nextFrom < min) nextFrom = min;
    return { from: nextFrom, to: nextTo };
  };
  const applyLogicalRange = (from, to) => {
    chart.timeScale().setVisibleLogicalRange(clampLogicalRange(from, to));
    requestAnimationFrame(drawWicks);
  };
  const setRange = (range, anchorValue) => {
    if (range === "all") {
      activeRange = "all";
      chart.timeScale().fitContent();
      chart.timeScale().applyOptions({ barSpacing: 7, minBarSpacing: 3 });
      markActive("all");
      markFooterActive("");
      requestAnimationFrame(drawWicks);
      return;
    }
    const count = Math.max(Number(range) || 90, 10);
    activeRange = String(range);
    const spacing = count <= 15 ? 34 : count <= 30 ? 28 : count <= 45 ? 24 : count <= 90 ? 18 : count <= 180 ? 13 : 9;
    chart.timeScale().applyOptions({ barSpacing: spacing, minBarSpacing: 4 });
    const anchorSeed = anchorValue ?? payload.activeEndIndex ?? payload.candles.length - 1;
    const anchor = Math.min(Math.max(Number(anchorSeed), 0), payload.candles.length - 1);
    const end = anchor + 8;
    const start = Math.max(anchor - count + 1, 0);
    applyLogicalRange(start, end);
    markActive(String(range));
    markFooterActive("");
  };
  const setCalendarRange = (range) => {
    const label = String(range);
    const lastIndex = Math.min(Math.max(Number(payload.activeEndIndex ?? maxIndex()), 0), maxIndex());
    const lastCandle = payload.candles[lastIndex] || payload.candles[maxIndex()];
    const lastTime = Number(lastCandle ? lastCandle.time : payload.lastTime);
    if (!Number.isFinite(lastTime)) return;
    if (label === "All") {
      activeRange = "calendar-All";
      chart.timeScale().fitContent();
      chart.timeScale().applyOptions({ barSpacing: 6, minBarSpacing: 2.5 });
      markActive("");
      markFooterActive(label);
      requestAnimationFrame(drawWicks);
      return;
    }
    const dayMap = { "1D": 1, "5D": 5, "1M": 31, "3M": 93, "6M": 186, "1Y": 365, "5Y": 1825 };
    let cutoffTime = lastTime - Number(dayMap[label] || 1) * 86400;
    if (label === "YTD") {
      const lastDate = new Date(lastTime * 1000);
      cutoffTime = Date.UTC(lastDate.getUTCFullYear(), 0, 1) / 1000;
    }
    let firstIndex = payload.candles.findIndex((bar) => Number(bar.time) >= cutoffTime);
    if (firstIndex < 0) firstIndex = 0;
    const available = Math.max(lastIndex - firstIndex + 1, 1);
    const minimumBars = label === "1D" ? Math.min(90, payload.candles.length) : Math.min(45, payload.candles.length);
    if (available < minimumBars) {
      firstIndex = Math.max(0, lastIndex - minimumBars + 1);
    }
    const span = Math.max(lastIndex - firstIndex + 1, 10);
    const spacing = span <= 45 ? 24 : span <= 90 ? 18 : span <= 250 ? 11 : span <= 700 ? 7 : 4.5;
    chart.timeScale().applyOptions({ barSpacing: spacing, minBarSpacing: span > 700 ? 2.2 : 3 });
    activeRange = "calendar-" + label;
    applyLogicalRange(firstIndex, lastIndex + 8);
    markActive("");
    markFooterActive(label);
  };

  const shiftWindow = (direction) => {
    const range = chart.timeScale().getVisibleLogicalRange();
    if (!range) return;
    const span = Math.max(range.to - range.from, 8);
    const shift = span * 0.72 * Number(direction);
    applyLogicalRange(range.from + shift, range.to + shift);
    markActive("");
    markFooterActive("");
  };
  const zoomWindow = (factor) => {
    const range = chart.timeScale().getVisibleLogicalRange();
    if (!range) return;
    const center = (range.from + range.to) / 2;
    const span = Math.max((range.to - range.from) * factor, 12);
    applyLogicalRange(center - span / 2, center + span / 2);
    markActive("");
    markFooterActive("");
  };
  rangeButtons.forEach((button) => {
    button.addEventListener("click", () => setRange(button.dataset.range));
  });
  navButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "back") shiftWindow(-1);
      if (action === "forward") shiftWindow(1);
      if (action === "zoom-in") zoomWindow(0.72);
      if (action === "zoom-out") zoomWindow(1.32);
      if (action === "latest") {
        if (String(activeRange).startsWith("calendar-")) {
          setCalendarRange(String(activeRange).replace("calendar-", ""));
        } else {
          setRange(activeRange === "all" ? Math.min(payload.visibleCount || 90, payload.candles.length) : activeRange, payload.activeEndIndex);
        }
      }
    });
  });
  footerButtons.forEach((button) => {
    button.addEventListener("click", () => setCalendarRange(button.dataset.calendarRange));
  });
  container.addEventListener("dblclick", () => setRange(Math.min(payload.visibleCount || 90, payload.candles.length)));

  updateClock();
  setInterval(updateClock, 30000);
  setRange(Math.min(payload.visibleCount || 90, payload.candles.length));
  requestAnimationFrame(() => {
    chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    drawWicks();
  });
})();
</script>
<style>
  html, body {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: __PANEL__;
  }
  * {
    box-sizing: border-box;
  }
  .tw-shell {
    height: __CHART_HEIGHT__px;
    display: flex;
    flex-direction: column;
    background: __PANEL__;
    border: 1px solid __BORDER__;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    color: __TEXT__;
    font-family: Inter, Arial, sans-serif;
    box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
  }
  .tw-toolbar {
    flex: 0 0 auto;
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 8px 12px;
    border-bottom: 1px solid __BORDER__;
    background: __PANEL__;
  }
  .tw-brand {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    color: __TEXT__;
  }
  .tw-brand strong {
    font-size: 15px;
    letter-spacing: 0;
  }
  .tw-brand span {
    color: __MUTED__;
    font-size: 12px;
  }
  .tw-credit {
    color: __MUTED__;
    font-size: 11px;
    text-decoration: none;
    border-left: 1px solid __BORDER__;
    padding-left: 8px;
  }
  .tw-credit:hover {
    color: __BLUE__;
  }
  .tw-controls {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 7px 12px;
  }
  .tw-buttons {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }
  .tw-nav-buttons {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }
  .tw-buttons span {
    color: __MUTED__;
    font-size: 12px;
    margin-right: 2px;
  }
  .tw-buttons button,
  .tw-nav-buttons button {
    border: 1px solid __BORDER__;
    background: __PANEL__;
    color: __TEXT__;
    border-radius: 6px;
    padding: 6px 9px;
    cursor: pointer;
    font: inherit;
    font-size: 12px;
  }
  .tw-buttons button:hover,
  .tw-nav-buttons button:hover {
    border-color: __BLUE__;
    color: __BLUE__;
  }
  .tw-buttons button.active {
    border-color: __UP__;
    background: rgba(0, 200, 5, 0.10);
    color: __UP__;
  }
  .tw-legend {
    min-height: 30px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    padding: 6px 12px;
    background: transparent;
    color: __MUTED__;
    font-size: 12px;
  }
  .tw-legend b {
    color: __TEXT__;
    margin-left: 4px;
  }
  .tw-legend .up { color: __UP__; }
  .tw-legend .down { color: __DOWN__; }
  .tw-subbar {
    flex: 0 0 auto;
    min-height: 34px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 1px solid __BORDER__;
    background: __PANEL__;
  }
  .tw-planbar {
    flex: 0 0 auto;
    min-height: 36px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px 12px;
    border-bottom: 1px solid __BORDER__;
    background: __PANEL__;
  }
  .tw-level-chip {
    min-width: 108px;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: baseline;
    gap: 6px;
    border: 1px solid __BORDER__;
    border-radius: 6px;
    background: __PANEL__;
    padding: 4px 8px;
    color: __TEXT__;
  }
  .tw-level-chip span {
    color: __MUTED__;
    font-size: 11px;
    font-weight: 760;
    text-transform: uppercase;
  }
  .tw-level-chip strong {
    font-size: 13px;
    font-weight: 850;
  }
  .tw-level-chip em {
    color: __MUTED__;
    font-size: 11px;
    font-style: normal;
  }
  .tw-level-up strong { color: __UP__; }
  .tw-level-down strong { color: __DOWN__; }
  .tw-hint {
    color: __MUTED__;
    font-size: 12px;
    white-space: nowrap;
    padding-right: 12px;
  }
  .tw-workspace {
    flex: 1 1 0;
    min-height: 420px;
    display: flex;
    background: __PANEL__;
  }
  .tw-stage {
    flex: 1 1 auto;
    position: relative;
    min-width: 0;
    min-height: 420px;
    height: auto;
    background: __PANEL__;
    border-top: 1px solid rgba(148, 163, 184, 0.08);
  }
  .tw-chart {
    height: 100%;
    background: __PANEL__;
    position: relative;
    z-index: 1;
  }
  .tw-wick-layer {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 2;
  }
  .tw-watermark {
    position: absolute;
    left: 22px;
    top: 18px;
    color: __MUTED__;
    opacity: 0.14;
    font-size: clamp(30px, 7vw, 88px);
    font-weight: 800;
    pointer-events: none;
    user-select: none;
    letter-spacing: 0;
    z-index: 0;
  }
  .tw-chart canvas {
    image-rendering: auto;
    transform: translateZ(0);
    backface-visibility: hidden;
  }
  .tw-side-panel {
    flex: 0 0 238px;
    border-left: 1px solid __BORDER__;
    border-top: 1px solid rgba(148, 163, 184, 0.08);
    background: linear-gradient(180deg, __PANEL__ 0%, __PANEL_ALT__ 100%);
    padding: 11px 11px 10px;
    color: __TEXT__;
    overflow: hidden;
  }
  .tw-side-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding-bottom: 9px;
    border-bottom: 1px solid __BORDER__;
  }
  .tw-side-head span {
    color: __MUTED__;
    font-size: 11px;
    font-weight: 820;
    text-transform: uppercase;
  }
  .tw-side-head strong {
    color: __TEXT__;
    font-size: 13px;
    font-weight: 880;
  }
  .tw-side-body {
    display: grid;
    gap: 9px;
    padding-top: 10px;
  }
  .tw-side-status {
    border: 1px solid __BORDER__;
    border-left: 4px solid __BLUE__;
    border-radius: 7px;
    padding: 9px 10px;
    background: __PANEL__;
  }
  .tw-side-ready { border-left-color: __UP__; }
  .tw-side-watch { border-left-color: __BLUE__; }
  .tw-side-danger { border-left-color: __DOWN__; }
  .tw-side-neutral { border-left-color: __MUTED__; }
  .tw-side-status span,
  .tw-side-grid span,
  .tw-side-source span {
    display: block;
    color: __MUTED__;
    font-size: 10px;
    font-weight: 820;
    text-transform: uppercase;
  }
  .tw-side-status strong {
    display: block;
    margin-top: 4px;
    color: __TEXT__;
    font-size: 14px;
    font-weight: 880;
    line-height: 1.1;
  }
  .tw-side-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
  }
  .tw-side-grid div,
  .tw-side-source {
    border: 1px solid __BORDER__;
    border-radius: 7px;
    background: __PANEL__;
    padding: 8px 9px;
    min-width: 0;
  }
  .tw-side-grid strong,
  .tw-side-source strong {
    display: block;
    margin-top: 4px;
    color: __TEXT__;
    font-size: 12px;
    font-weight: 820;
    line-height: 1.15;
    overflow-wrap: anywhere;
  }
  .tw-side-note {
    border: 1px solid __BORDER__;
    border-radius: 7px;
    background: rgba(59, 130, 246, 0.08);
    color: __MUTED__;
    font-size: 12px;
    line-height: 1.34;
    padding: 9px 10px;
  }
  .tw-footer {
    flex: 0 0 auto;
    min-height: 36px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 5px 10px;
    border-top: 1px solid __BORDER__;
    background: __PANEL__;
  }
  .tw-footer-buttons,
  .tw-footer-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 5px;
  }
  .tw-footer button {
    border: 0;
    background: transparent;
    color: __MUTED__;
    border-radius: 5px;
    cursor: pointer;
    font: inherit;
    font-size: 12px;
    font-weight: 760;
    padding: 5px 7px;
  }
  .tw-footer button:hover,
  .tw-footer button.active {
    background: rgba(59, 130, 246, 0.12);
    color: __TEXT__;
  }
  .tw-footer-pill {
    border-left: 1px solid __BORDER__;
    color: __MUTED__;
    font-size: 12px;
    font-weight: 700;
    padding-left: 8px;
    white-space: nowrap;
  }
  @media (max-width: 760px) {
    .tw-toolbar, .tw-subbar, .tw-controls, .tw-footer {
      align-items: flex-start;
      flex-direction: column;
    }
    .tw-controls {
      width: 100%;
    }
    .tw-level-chip {
      min-width: calc(50% - 4px);
    }
    .tw-hint {
      padding: 0 12px 8px;
    }
    .tw-stage {
      min-height: 360px;
    }
    .tw-workspace {
      flex-direction: column;
      min-height: 500px;
    }
    .tw-side-panel {
      flex: 0 0 auto;
      border-left: 0;
      border-top: 1px solid __BORDER__;
    }
    .tw-footer-pill:first-child {
      border-left: 0;
      padding-left: 0;
    }
  }
  .tw-error {
    min-height: 320px;
    display: grid;
    place-items: center;
    color: __MUTED__;
    padding: 24px;
    text-align: center;
  }
</style>
"""
    replacements = {
        "__PAYLOAD__": json.dumps(payload),
        "__LIGHTWEIGHT_CHARTS_LOADER__": chart_loader,
        "__CHART_HEIGHT__": str(chart_height),
        "__TICKER__": html.escape(str(payload["ticker"])),
        "__PANEL__": payload["palette"]["panel"],
        "__PANEL_ALT__": payload["palette"]["panel_alt"],
        "__BORDER__": payload["palette"]["border"],
        "__TEXT__": payload["palette"]["text"],
        "__MUTED__": payload["palette"]["muted_soft"],
        "__BLUE__": payload["palette"]["blue"],
        "__UP__": payload["palette"]["up_bright"],
        "__DOWN__": payload["palette"]["down"],
    }
    for key, value in replacements.items():
        component_html = component_html.replace(key, str(value))

    components.html(component_html, height=chart_height + 6, scrolling=False)
    return True


def rebuild_analysis_from_history(
    ticker: str,
    history: pd.DataFrame,
    source: str,
    prefer_live: bool,
) -> dict[str, Any]:
    live_stats = live_quote_stats(ticker) if prefer_live else None
    stats = latest_market_stats(ticker, history, source, live_stats=live_stats)
    plan = build_trade_plan(stats, history)
    score, setup, confidence, reasons, warnings = score_setup(stats, plan)
    fit = playbook_fit_label(stats, score)
    data_quality, _ = data_quality_badge(stats.get("Data source", source))
    status = live_status({**stats, **plan})
    return {
        **stats,
        **plan,
        "AI score": int(score),
        "Setup": setup,
        "Confidence": confidence,
        "Playbook fit": fit,
        "Data quality": data_quality,
        "Status": status,
        "Reasons": reasons,
        "Warnings": warnings,
        "Plan": (
            f"Watch {stats['Ticker']} for a clean hold inside {plan['Buy zone']} and only consider a "
            f"paper entry after {entry_confirmation_text(plan)}. Keep risk defined near {plan['Stop']}."
        ),
    }


def render_plotly_trading_chart(
    chart_df: pd.DataFrame,
    analysis: dict[str, Any],
    current_price: float,
    height: int,
) -> None:
    if go is None or make_subplots is None:
        return

    chart_height = max(height + 280, 760)
    palette = theme_palette()
    is_light = st.session_state.get("display_mode", "Dark") == "Light"
    chart_bg = palette["app_bg"]
    panel_bg = palette["panel"]
    grid = palette["grid"]
    text = palette["text"]
    muted = palette["muted_soft"]
    up = palette["up_bright"]
    down = palette["down"]
    show_ema9 = bool(st.session_state.get("chart_layer_ema9", True))
    show_ema20 = bool(st.session_state.get("chart_layer_ema20", True))
    show_vwap = bool(st.session_state.get("chart_layer_vwap", True))
    show_buy_zone = bool(st.session_state.get("chart_layer_buy_zone", True))
    show_plan_levels = bool(st.session_state.get("chart_layer_plan_levels", True))
    show_ai_signals = bool(st.session_state.get("chart_layer_ai_signals", True))
    levels = chart_trade_levels(analysis)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.018,
        row_heights=[0.76, 0.24],
    )

    fig.add_trace(
        go.Candlestick(
            x=chart_df["Time"],
            open=chart_df["Open"],
            high=chart_df["High"],
            low=chart_df["Low"],
            close=chart_df["Close"],
            name="Candles",
            increasing=dict(line=dict(color=up, width=1.35), fillcolor=up),
            decreasing=dict(line=dict(color=down, width=1.35), fillcolor=down),
            whiskerwidth=0.65,
        ),
        row=1,
        col=1,
    )

    line_specs = []
    if show_ema9:
        line_specs.append(("EMA 9", palette["blue"], 1.7))
    if show_ema20:
        line_specs.append(("EMA 20", palette["violet"], 1.7))
    if show_vwap:
        line_specs.append(("VWAP", palette["orange"], 2.1))

    for line_name, color, width in line_specs:
        fig.add_trace(
            go.Scatter(
                x=chart_df["Time"],
                y=chart_df[line_name],
                mode="lines",
                line=dict(color=color, width=width),
                name=line_name,
                hovertemplate=f"{line_name}: $%{{y:.2f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    volume_colors = np.where(
        chart_df["Close"] >= chart_df["Open"],
        "rgba(0, 200, 5, 0.58)" if not is_light else "rgba(0, 143, 45, 0.55)",
        "rgba(255, 55, 95, 0.58)" if not is_light else "rgba(217, 45, 32, 0.50)",
    )
    fig.add_trace(
        go.Bar(
            x=chart_df["Time"],
            y=chart_df["Volume"],
            marker_color=volume_colors,
            name="Volume",
            hovertemplate="Volume: %{y:,.0f}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    start_time = chart_df["Time"].iloc[0]
    end_time = chart_df["Time"].iloc[-1]
    buy_low = levels["buy_low"]
    buy_high = levels["buy_high"]
    if show_buy_zone and buy_low is not None and buy_high is not None:
        fig.add_shape(
            type="rect",
            x0=start_time,
            x1=end_time,
            y0=buy_low,
            y1=buy_high,
            fillcolor="rgba(34, 211, 238, 0.14)" if not is_light else "rgba(8, 145, 178, 0.12)",
            line=dict(width=0),
            layer="below",
            row=1,
            col=1,
        )

    def add_level(label: str, value: Any, color: str, dash: str = "dot") -> None:
        price = safe_float(value)
        if price is None:
            return
        fig.add_hline(
            y=price,
            line_color=color,
            line_dash=dash,
            line_width=1.2,
            annotation_text=f"{label} {money(price)}",
            annotation_position="top right",
            annotation_font_color=color,
            annotation_bgcolor="rgba(9, 12, 16, 0.86)" if not is_light else "rgba(255, 255, 255, 0.90)",
            annotation_bordercolor=color,
            row=1,
            col=1,
        )

    if show_plan_levels:
        add_level("Current", current_price, text, "solid")
        add_level("Buy low", levels["buy_low"], palette["cyan"])
        add_level("Buy high", levels["buy_high"], palette["cyan"])
        add_level("Stop", levels["stop"], down)
        add_level("Sell / trim", levels["target_1"], up)
        add_level("Runner target", levels["target_2"], palette["blue"])
        add_level("Previous close", analysis.get("Previous close"), muted)

    if show_ai_signals:
        signal_specs = [
            ("AI buy zone", levels["buy_mid"], palette["cyan"], "triangle-up", "Paper buy area"),
            ("Entry trigger", levels["entry"], up, "triangle-up", "Buy only after confirmation"),
            ("Stop / invalid", levels["stop"], down, "x", "Plan is wrong here"),
            ("Sell / trim T1", levels["target_1"], up, "triangle-down", "First sell/trim target"),
            ("Runner T2", levels["target_2"], palette["blue"], "triangle-down", "Second target"),
        ]
        signal_rows = [
            {"Label": label, "Price": price, "Color": color, "Symbol": symbol, "Note": note}
            for label, price, color, symbol, note in signal_specs
            if price is not None
        ]
        if signal_rows:
            fig.add_trace(
                go.Scatter(
                    x=[end_time for _ in signal_rows],
                    y=[row["Price"] for row in signal_rows],
                    mode="markers+text",
                    marker=dict(
                        color=[row["Color"] for row in signal_rows],
                        symbol=[row["Symbol"] for row in signal_rows],
                        size=15,
                        line=dict(width=1.8, color=panel_bg),
                    ),
                    text=[row["Label"] for row in signal_rows],
                    textposition="middle left",
                    textfont=dict(color=text, size=12),
                    customdata=[[row["Note"]] for row in signal_rows],
                    name="AI trade map",
                    hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>%{customdata[0]}<extra></extra>",
                ),
                row=1,
                col=1,
            )

    fig.update_layout(
        height=chart_height,
        margin=dict(l=8, r=72, t=40, b=8),
        template="plotly_white" if is_light else "plotly_dark",
        paper_bgcolor=chart_bg,
        plot_bgcolor=panel_bg,
        font=dict(color=text, family="Inter, Arial, sans-serif", size=12),
        dragmode="pan",
        hovermode="x unified",
        bargap=0,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(255, 255, 255, 0.78)" if is_light else "rgba(9, 12, 16, 0.70)",
            bordercolor=palette["border"],
            borderwidth=1,
        ),
        hoverlabel=dict(bgcolor=palette["panel"], bordercolor=palette["border"], font_color=text),
        uirevision=f"{analysis.get('Ticker', 'chart')}-trading-chart",
        xaxis_rangeslider_visible=False,
        modebar=dict(bgcolor="rgba(9, 12, 16, 0)" if not is_light else "rgba(255, 255, 255, 0)", color=muted, activecolor=up),
    )
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=muted,
        spikethickness=1,
        showline=True,
        linecolor=palette["border"],
        gridcolor=grid,
        zeroline=False,
        rangeslider_visible=False,
        row=1,
        col=1,
    )
    fig.update_xaxes(
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=muted,
        spikethickness=1,
        showline=True,
        linecolor=palette["border"],
        gridcolor=grid,
        zeroline=False,
        rangeslider_visible=False,
        row=2,
        col=1,
    )
    visible_high = float(chart_df["High"].max())
    visible_low = float(chart_df["Low"].min())
    overlay_values = []
    if show_plan_levels or show_ai_signals:
        overlay_values = [
            value
            for value in [
                levels["buy_low"],
                levels["buy_high"],
                levels["entry"],
                levels["stop"],
                levels["target_1"],
                levels["target_2"],
                safe_float(analysis.get("Previous close")),
            ]
            if value is not None and math.isfinite(float(value))
        ]
    if overlay_values:
        visible_high = max(visible_high, max(overlay_values))
        visible_low = min(visible_low, min(overlay_values))
    pad = max((visible_high - visible_low) * 0.10, max(current_price * 0.004, 0.03))
    volume_max = max(float(chart_df["Volume"].max()), 1.0)
    fig.update_yaxes(
        title_text="Price",
        fixedrange=False,
        side="right",
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        range=[visible_low - pad, visible_high + pad],
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Volume",
        fixedrange=False,
        side="right",
        showgrid=True,
        gridcolor=grid,
        zeroline=False,
        range=[0, volume_max * 1.18],
        row=2,
        col=1,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "doubleClick": "reset+autosize",
            "modeBarButtonsToAdd": ["drawline", "drawrect", "eraseshape"],
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "displaylogo": False,
        },
    )


def render_candlestick_chart(
    history: pd.DataFrame,
    analysis: dict[str, Any],
    height: int = 470,
    max_candles: int | None = 180,
) -> None:
    if history.empty:
        st.info("No chart data available for this stock.")
        return

    chart_engine = st.session_state.get("chart_engine", "TradingView-style")
    if chart_engine == "TradingView-style":
        visible_count = max_candles or min(len(history), 390)
        load_limit = max(int(visible_count), 2600)
        chart_df = history.tail(load_limit).copy()
        flat_zero_volume = (
            (chart_df["Volume"].fillna(0).astype(float) <= 0)
            & ((chart_df["High"].astype(float) - chart_df["Low"].astype(float)).abs() <= 0.001)
            & ((chart_df["Open"].astype(float) - chart_df["Close"].astype(float)).abs() <= 0.001)
        )
        cleaned_chart_df = chart_df.loc[~flat_zero_volume].copy()
        if len(cleaned_chart_df) >= max(20, min(int(visible_count), 90)):
            chart_df = cleaned_chart_df
        active_volume_df = chart_df.loc[chart_df["Volume"].fillna(0).astype(float) > 0].copy()
        if len(active_volume_df) >= max(20, min(int(visible_count), 90)):
            chart_df = active_volume_df
    elif max_candles:
        chart_df = history.tail(max_candles).copy()
    else:
        chart_df = history.tail(900).copy()
    chart_df["EMA 9"] = chart_df["Close"].ewm(span=9, adjust=False).mean()
    chart_df["EMA 20"] = chart_df["Close"].ewm(span=20, adjust=False).mean()
    typical_price = (chart_df["High"] + chart_df["Low"] + chart_df["Close"]) / 3
    vwap_volume = chart_df["Volume"].replace(0, np.nan)
    index_series = pd.Series(chart_df.index, index=chart_df.index)
    median_step = index_series.diff().dropna().median() if len(index_series) > 1 else pd.NaT
    is_intraday = pd.notna(median_step) and median_step < pd.Timedelta(hours=20)
    if is_intraday:
        session_key = pd.Series(pd.DatetimeIndex(chart_df.index).date, index=chart_df.index)
        cumulative_price_volume = (typical_price * chart_df["Volume"]).groupby(session_key).cumsum()
        cumulative_volume = vwap_volume.groupby(session_key).cumsum()
    else:
        cumulative_price_volume = (typical_price * chart_df["Volume"]).cumsum()
        cumulative_volume = vwap_volume.cumsum()
    chart_df["VWAP"] = cumulative_price_volume / cumulative_volume
    chart_df["VWAP"] = chart_df["VWAP"].ffill().bfill()
    chart_df["Time"] = chart_df.index
    chart_df["Direction"] = np.where(chart_df["Close"] >= chart_df["Open"], "Up", "Down")
    chart_df["Body low"] = chart_df[["Open", "Close"]].min(axis=1)
    chart_df["Body high"] = chart_df[["Open", "Close"]].max(axis=1)
    chart_df["Volume color"] = chart_df["Direction"]

    last = chart_df.iloc[-1]
    candle_delta = ((float(last["Close"]) - float(last["Open"])) / max(float(last["Open"]), 0.01)) * 100
    range_high = float(chart_df["High"].max())
    range_low = float(chart_df["Low"].min())
    current_price = float(last["Close"])
    latest_vwap = float(last["VWAP"]) if math.isfinite(float(last["VWAP"])) else current_price

    def render_chart_stats() -> None:
        stats = [
            ("Last candle", money(current_price), pct(candle_delta), "up" if candle_delta >= 0 else "down"),
            ("Loaded high", money(range_high), f"{len(chart_df):,} candles", "neutral"),
            ("Loaded low", money(range_low), "drag left to review", "neutral"),
            ("VWAP", money(latest_vwap), "intraday control line", "neutral"),
        ]
        parts = ['<div class="msa-chart-stat-strip">']
        for label, value, detail, tone in stats:
            parts.append(
                '<div class="msa-chart-stat-card msa-chart-stat-{tone}">'
                '<div class="msa-chart-stat-label">{label}</div>'
                '<div class="msa-chart-stat-value">{value}</div>'
                '<div class="msa-chart-stat-detail">{detail}</div>'
                "</div>".format(
                    tone=html.escape(tone),
                    label=html.escape(label),
                    value=html.escape(value),
                    detail=html.escape(detail),
                )
            )
        parts.append("</div>")
        render_html("".join(parts))

    candle_size = 16 if len(chart_df) <= 90 else 12 if len(chart_df) <= 180 else 8 if len(chart_df) <= 390 else 4
    if chart_engine == "TradingView-style":
        rendered = render_lightweight_trading_chart(chart_df, analysis, current_price, height, max_candles)
        if rendered:
            render_chart_stats()
            return

    if go is not None and make_subplots is not None:
        render_plotly_trading_chart(chart_df, analysis, current_price, height)
        render_chart_stats()
        return

    base = alt.Chart(chart_df).encode(
        x=alt.X("Time:T", title="Time"),
        color=alt.Color(
            "Direction:N",
            scale=alt.Scale(domain=["Up", "Down"], range=["#059669", "#dc2626"]),
            legend=None,
        ),
    )
    tooltip = [
        alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
        alt.Tooltip("Open:Q", title="Open", format="$,.2f"),
        alt.Tooltip("High:Q", title="High", format="$,.2f"),
        alt.Tooltip("Low:Q", title="Low", format="$,.2f"),
        alt.Tooltip("Close:Q", title="Close", format="$,.2f"),
        alt.Tooltip("VWAP:Q", title="VWAP", format="$,.2f"),
        alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
    ]

    wick = base.mark_rule(strokeWidth=1.2).encode(
        y=alt.Y("Low:Q", title="Price"),
        y2="High:Q",
        tooltip=tooltip,
    )
    candle = base.mark_bar(size=candle_size).encode(
        y="Body low:Q",
        y2="Body high:Q",
        tooltip=tooltip,
    )

    overlay_frame = chart_df[["Time", "EMA 9", "EMA 20", "VWAP"]].melt("Time", var_name="Line", value_name="Price")
    ema_chart = (
        alt.Chart(overlay_frame)
        .mark_line(strokeWidth=1.7)
        .encode(
            x="Time:T",
            y="Price:Q",
            color=alt.Color(
                "Line:N",
                scale=alt.Scale(domain=["EMA 9", "EMA 20", "VWAP"], range=["#2563eb", "#7c3aed", "#f59e0b"]),
            ),
            tooltip=[
                alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
                alt.Tooltip("Line:N", title="Line"),
                alt.Tooltip("Price:Q", title="Price", format="$,.2f"),
            ],
        )
    )

    start_time = chart_df["Time"].min()
    end_time = chart_df["Time"].max()
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    band = alt.Chart(pd.DataFrame())
    if buy_low is not None and buy_high is not None:
        band = (
            alt.Chart(pd.DataFrame([{"Start": start_time, "End": end_time, "Low": buy_low, "High": buy_high}]))
            .mark_rect(color="#0891b2", opacity=0.11)
            .encode(x="Start:T", x2="End:T", y="Low:Q", y2="High:Q")
        )

    levels = pd.DataFrame(
        [
            {"Level": "Buy low", "Price": analysis.get("Buy low")},
            {"Level": "Buy high", "Price": analysis.get("Buy high")},
            {"Level": "Stop", "Price": analysis.get("Stop price")},
            {"Level": "Target 1", "Price": analysis.get("Target 1 price")},
            {"Level": "Current", "Price": current_price},
            {"Level": "Previous close", "Price": analysis.get("Previous close")},
        ]
    ).dropna()
    levels["Start"] = start_time
    levels["End"] = end_time
    level_chart = (
        alt.Chart(levels)
        .mark_rule(strokeDash=[5, 4], strokeWidth=1.2)
        .encode(
            y="Price:Q",
            color=alt.Color(
                "Level:N",
                scale=alt.Scale(
                    domain=["Buy low", "Buy high", "Stop", "Target 1", "Current", "Previous close"],
                    range=["#0891b2", "#0891b2", "#dc2626", "#16a34a", "#111827", "#6b7280"],
                ),
            ),
            tooltip=[alt.Tooltip("Level:N"), alt.Tooltip("Price:Q", format="$,.2f")],
        )
    )

    price_chart = (band + wick + candle + ema_chart + level_chart).properties(height=height).interactive()
    price_chart = price_chart.resolve_scale(color="independent")
    st.altair_chart(price_chart, width="stretch")

    volume_chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X("Time:T", title="Time"),
            y=alt.Y("Volume:Q", title="Volume"),
            color=alt.Color(
                "Volume color:N",
                scale=alt.Scale(domain=["Up", "Down"], range=["#34d399", "#f87171"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Time:T", title="Time", format="%b %d, %I:%M %p"),
                alt.Tooltip("Volume:Q", title="Volume", format=",.0f"),
                alt.Tooltip("Close:Q", title="Close", format="$,.2f"),
            ],
        )
        .properties(height=170)
    )
    st.altair_chart(volume_chart, width="stretch")
    render_chart_stats()


def render_chart_panel(
    ticker: str,
    period: str,
    interval: str,
    prefer_live: bool,
    max_candles: int | None = 180,
) -> None:
    history, source = load_history(ticker, period=period, interval=interval, prefer_live=prefer_live)
    if prefer_live and source == "Learning data":
        try:
            live_history = yahoo_chart_api_history(ticker, period=period, interval=interval, prepost=True)
            if not live_history.empty and len(live_history) >= 5:
                history = live_history
                source = f"Yahoo Finance API {interval}"
                print(f"[chart-panel] direct live retry recovered {ticker} {period}/{interval}: {len(history)} bars", flush=True)
            else:
                print(f"[chart-panel] direct live retry returned no usable bars for {ticker} {period}/{interval}", flush=True)
        except Exception as exc:
            print(f"[chart-panel] direct live retry failed for {ticker} {period}/{interval}: {exc}", flush=True)

    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=prefer_live)
    remember_companion_analysis(analysis)

    chart_quality, chart_color = data_quality_badge(source)
    st.badge(f"Chart source: {chart_quality}", icon=":material/candlestick_chart:", color=chart_color)
    if prefer_live and source == "Learning data":
        st.warning(
            "The live chart feed did not return enough candles, so this view is showing learning fallback data.",
            icon=":material/wifi_off:",
        )

    render_setup_command_strip(analysis, source, context="charts")
    render_candlestick_chart(history, analysis, max_candles=max_candles)
    st.caption(
        f"Chart source: {source}. Last screen refresh: {datetime.now().strftime('%I:%M:%S %p')}. "
        "Free market data can be real-time or delayed depending on source, exchange, and availability."
    )
    render_source_brief(analysis, source)
    render_workflow_cockpit(analysis, source, context="charts")
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_trade_readiness_panel(analysis)
    render_premium_trade_ticket(analysis)
    render_ai_decision_panel(analysis, source)
    render_ai_chart_trade_map(analysis)
    render_plan_card(analysis)
    render_lazy_news_expander(
        f"Latest {ticker.upper()} news",
        lambda: finnhub_company_news(ticker, days=5, limit=5),
    )


@st.fragment(run_every=f"{LIVE_REFRESH_SECONDS}s")
def auto_refresh_chart_panel(
    ticker: str,
    period: str,
    interval: str,
    prefer_live: bool,
    max_candles: int | None = 180,
) -> None:
    render_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)


def live_status(analysis: dict[str, Any]) -> str:
    price = safe_float(analysis.get("Price"))
    buy_low = safe_float(analysis.get("Buy low"))
    buy_high = safe_float(analysis.get("Buy high"))
    entry = safe_float(analysis.get("Entry trigger price"))
    stop = safe_float(analysis.get("Stop price"))
    gain = safe_float(analysis.get("Daily gain %"), 0) or 0
    rvol = safe_float(analysis.get("RVOL"), 0) or 0

    if price is None:
        return "No quote"
    if stop is not None and price <= stop:
        return "Below stop"
    if entry is not None and price >= entry:
        return "Breakout trigger"
    if buy_low is not None and buy_high is not None and buy_low <= price <= buy_high:
        return "In buy zone"
    if buy_low is not None and price < buy_low and ((buy_low - price) / max(buy_low, 0.01)) <= 0.03:
        return "Near buy zone"
    if gain >= 10 and rvol >= 3:
        return "Momentum active"
    return "Watching"


def tracker_row(analysis: dict[str, Any], track_type: str) -> dict[str, Any]:
    price = safe_float(analysis.get("Price"))
    entry = safe_float(analysis.get("Entry trigger price"))
    stop = safe_float(analysis.get("Stop price"))
    target = safe_float(analysis.get("Target 1 price"))
    data_quality, _ = data_quality_badge(analysis.get("Data source"))
    return {
        "Track": track_type,
        "Ticker": analysis.get("Ticker"),
        "Status": live_status(analysis),
        "Playbook fit": analysis.get("Playbook fit", playbook_fit_label(analysis, analysis.get("AI score"))),
        "Price": price,
        "Daily gain %": safe_float(analysis.get("Daily gain %"), 0) or 0,
        "RVOL": safe_float(analysis.get("RVOL"), 0) or 0,
        "Volume": safe_float(analysis.get("Volume"), 0) or 0,
        "Float M": safe_float(analysis.get("Float M"), 0) or 0,
        "Entry": entry,
        "Stop": stop,
        "Target 1": target,
        "Distance to entry %": ((entry - price) / price * 100) if entry and price else None,
        "Risk to stop %": ((price - stop) / price * 100) if stop and price else None,
        "Data quality": data_quality,
        "Data confidence": analysis.get("Data confidence") or data_confidence_summary(analysis).get("label", "n/a"),
        "Data source": analysis.get("Data source", "n/a"),
        "Quote time": analysis.get("Quote time", "n/a"),
    }


@st.cache_data(ttl=20, max_entries=50, show_spinner=False)
def live_tracker_frame(tickers: tuple[str, ...], include_scan: bool = True) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    if include_scan:
        scan = run_scan(
            DEFAULT_RULES["min_price"],
            DEFAULT_RULES["max_price"],
            DEFAULT_RULES["min_gain_pct"],
            DEFAULT_RULES["max_float_m"],
            DEFAULT_RULES["min_rvol"],
            prefer_live=True,
            include_learning=False,
        )
        for item in scan.head(20).to_dict("records"):
            ticker = str(item.get("Ticker", "")).upper()
            if ticker:
                rows.append(tracker_row(item, "Scanner"))
                seen.add(ticker)

    for ticker in tickers:
        clean_ticker = normalize_user_symbol(ticker)
        if not clean_ticker:
            continue
        analysis = analyze_ticker(clean_ticker, period="5d", interval="5m", prefer_live=True)
        track_type = "Scanner + Watchlist" if clean_ticker in seen else "Watchlist"
        rows.append(tracker_row(analysis, track_type))

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    status_rank = {
        "Breakout trigger": 0,
        "In buy zone": 1,
        "Near buy zone": 2,
        "Momentum active": 3,
        "Watching": 4,
        "Below stop": 5,
        "No quote": 6,
    }
    df["_rank"] = df["Status"].map(status_rank).fillna(9)
    return df.sort_values(["_rank", "Daily gain %", "RVOL"], ascending=[True, False, False]).drop(columns=["_rank"])


def clear_live_market_caches() -> None:
    live_cache_functions = (
        live_tracker_frame,
        run_scan,
        broad_market_scan,
        default_scan,
        analyze_ticker,
        load_history,
        live_quote_stats,
        finnhub_quote_stats,
        yahoo_quote_stats,
        biggest_stock_news,
        finnhub_company_news,
        finnhub_market_news,
    )
    for cached_function in live_cache_functions:
        clear = getattr(cached_function, "clear", None)
        if clear is not None:
            clear()


def show_tracker_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No live rows returned yet. Free data may be rate-limiting or the current filters may be too tight.")
        return

    st.caption("Select a row to make that stock active in Charts, AI Coach, and Trade Desk.")
    event = st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        key="live_tracker_table",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Ticker": st.column_config.TextColumn("Stock", pinned=True),
            "Status": st.column_config.TextColumn("Status"),
            "Playbook fit": st.column_config.TextColumn("Fit"),
            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "Daily gain %": st.column_config.NumberColumn("Gain", format="%.1f%%"),
            "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
            "Volume": st.column_config.NumberColumn("Volume", format="compact"),
            "Float M": st.column_config.NumberColumn("Float", format="%.1fM"),
            "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
            "Target 1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
            "Distance to entry %": st.column_config.NumberColumn("To entry", format="%.2f%%"),
            "Risk to stop %": st.column_config.NumberColumn("Risk", format="%.2f%%"),
        },
    )
    remember_selected_ticker(df, event)


def render_live_tracker_body(tickers: tuple[str, ...], include_scan: bool, fragment_mode: bool = False) -> None:
    if st.button(":material/refresh: Refresh now", key="live_tracker_refresh"):
        clear_live_market_caches()
        if fragment_mode:
            st.rerun(scope="fragment")
        else:
            st.rerun()

    df = live_tracker_frame(tickers, include_scan=include_scan)
    scanner_hits = int((df["Track"].astype(str).str.contains("Scanner")).sum()) if not df.empty else 0
    trigger_hits = int((df["Status"] == "Breakout trigger").sum()) if not df.empty else 0
    buy_zone_hits = int((df["Status"] == "In buy zone").sum()) if not df.empty else 0

    status_cards(
        [
            ("Tracked names", str(len(df)), "calm"),
            ("Scanner hits", str(scanner_hits), "good"),
            ("Breakout triggers", str(trigger_hits), "hot"),
            ("In buy zone", str(buy_zone_hits), "good"),
        ]
    )
    render_market_pulse(df, context="live_tracker")
    render_action_queue(df, key="live_tracker_action_queue")
    render_data_health_summary(df)

    st.caption(
        f"Auto-refresh target: every {LIVE_REFRESH_SECONDS} seconds. "
        f"Last refresh: {datetime.now().strftime('%I:%M:%S %p')}. Free market data may be delayed or rate-limited."
    )
    show_tracker_table(df)


@st.fragment(run_every=f"{LIVE_REFRESH_SECONDS}s")
def auto_refresh_live_tracker(tickers: tuple[str, ...], include_scan: bool) -> None:
    render_live_tracker_body(tickers, include_scan, fragment_mode=True)


def page_live_tracker() -> None:
    header("Live Tracker", "Auto-refresh the scanner and your watchlist while you study setups.")
    watchlist = tuple(read_watchlist())
    cols = st.columns([1, 1, 2])
    include_scan = cols[0].toggle("Include live scanner", value=True, key="tracker_include_scan")
    auto_refresh = cols[1].toggle("Auto-refresh", value=True, key="tracker_auto_refresh")
    cols[2].caption(
        f"Free mode uses Alpaca IEX, Finnhub, and Yahoo-style fallbacks with a {LIVE_REFRESH_SECONDS}-second refresh target. "
        "It can be delayed or rate-limited, but it is enough for paper-trading practice."
    )
    render_data_stack_panel(compact=True)

    if auto_refresh:
        auto_refresh_live_tracker(watchlist, include_scan)
    else:
        render_live_tracker_body(watchlist, include_scan)


def page_dashboard() -> None:
    dashboard_hero()
    st.caption(
        "Educational paper-trading tool. Verify live data, news, float, halts, and risk before making real trades. "
        "This is not financial advice."
    )
    control_cols = st.columns([1, 1, 2])
    prefer_live = control_cols[0].toggle("Use live data", value=True, key="dashboard_live")
    control_cols[1].badge(
        "Alpaca + Finnhub connected" if alpaca_enabled() and finnhub_enabled() else "Check data keys",
        icon=":material/key:",
        color="green" if alpaca_enabled() and finnhub_enabled() else "orange",
    )
    control_cols[2].caption("Home base: scanner candidates, AI plan, market clocks, and the latest news.")

    with st.skeleton(height=240):
        df = default_scan(prefer_live=prefer_live)
    best = df.iloc[0].to_dict()

    status_cards(
        [
            ("Candidates", str(len(df)), "calm"),
            ("Top stock", str(best["Ticker"]), "good"),
            ("Top score", f"{int(best['AI score'])}/100", "hot"),
            ("Top gain", pct(best["Daily gain %"]), "good"),
            ("Top RVOL", f"{best['RVOL']:.1f}x", "calm"),
        ]
    )
    render_companion_showcase(best, context="dashboard")
    render_market_pulse(df, context="dashboard")
    render_workflow_cockpit(best, str(best.get("Data source", "n/a")), context="dashboard")
    render_action_queue(df, key="dashboard_action_queue")

    news_symbols = tuple(unique_symbols([str(item) for item in df["Ticker"].head(10).tolist()] + read_watchlist() + CORE_MARKET_TICKERS[:8]))
    news_col, main_col, right_col = st.columns([0.95, 1.35, 0.85], vertical_alignment="top")
    with news_col:
        render_big_news_rail(news_symbols)
    with main_col:
        st.subheader("Primary watch")
        render_ai_decision_panel(best)
        render_beginner_stock_summary(best, str(best.get("Data source", "n/a")))
        render_trade_readiness_panel(best)
        render_plan_card(best)
    with right_col:
        render_data_stack_panel(compact=True)
        render_data_health_summary(df)
        with st.container(border=True):
            st.markdown("**Market clocks**")
            st.dataframe(market_clock_frame(), width="stretch", hide_index=True)
        with st.container(border=True):
            st.markdown("**What to check next**")
            st.write("- Open Charts for 1-minute candles and AI buy/sell levels.")
            st.write("- Read the news before approving any paper plan.")
            st.write("- Use Journal even when the best decision is no trade.")
        with st.container(border=True):
            st.markdown("**New trader path**")
            st.write("1. Learn: read Start here and Glossary.")
            st.write("2. Dashboard: find the main watch.")
            st.write("3. Charts: check candles, entry, stop, profit.")
            st.write("4. Trade Desk: approve paper trades only.")
            st.write("5. Journal: save what happened.")
        render_training_progress_panel()

    st.subheader("Scanner candidates")
    show_scan_table(df, key="dashboard_scan_table")


def page_daily_gameplan() -> None:
    header("Daily Gameplan", "Your default scan: $2 to $20, gain over 10%, float under 10M, RVOL over 3x.")
    prefer_live = st.toggle("Use live data", value=True, key="gameplan_live")
    render_data_stack_panel(compact=True)
    df = default_scan(prefer_live=prefer_live)
    best = df.iloc[0].to_dict()

    status_cards(
        [
            ("Primary watch", str(best["Ticker"]), "good"),
            ("Score", f"{int(best['AI score'])}/100", "hot"),
            ("Gain", pct(best["Daily gain %"]), "good"),
            ("RVOL", f"{best['RVOL']:.1f}x", "calm"),
        ]
    )
    render_market_pulse(df, context="daily_gameplan")
    render_workflow_cockpit(best, str(best.get("Data source", "n/a")), context="daily_gameplan")
    render_action_queue(df, key="gameplan_action_queue")
    render_data_health_summary(df)

    st.subheader("Primary watch")
    render_ai_decision_panel(best)
    render_plan_card(best)

    st.subheader("Watchlist for the session")
    show_scan_table(df, key="gameplan_scan_table")

    with st.container(border=True):
        st.markdown("**Risk rules**")
        st.write("- Paper trade first. Do not chase a candle far above the entry trigger.")
        st.write("- Keep every idea invalidated at the stop before entering.")
        st.write("- Skip anything with halted news, unclear float, or spreads too wide to manage.")


def page_scanner() -> None:
    header("Scanner", "Find stocks matching your momentum criteria.")
    with st.form("scanner_rules"):
        cols = st.columns(5)
        min_price = cols[0].number_input("Min price", 0.1, 200.0, DEFAULT_RULES["min_price"], step=0.5)
        max_price = cols[1].number_input("Max price", 0.1, 500.0, DEFAULT_RULES["max_price"], step=0.5)
        min_gain = cols[2].number_input("Min gain %", 0.0, 200.0, DEFAULT_RULES["min_gain_pct"], step=1.0)
        max_float = cols[3].number_input("Max float M", 0.1, 500.0, DEFAULT_RULES["max_float_m"], step=1.0)
        min_rvol = cols[4].number_input("Min RVOL", 0.1, 100.0, DEFAULT_RULES["min_rvol"], step=0.5)
        options = st.columns([1, 1, 3])
        prefer_live = options[0].toggle("Use live data", value=True)
        include_learning = options[1].toggle("Fallback rows", value=True)
        submitted = st.form_submit_button("Run scan", type="primary")

    if submitted or "scanner_df" not in st.session_state:
        st.session_state.scanner_df = run_scan(
            min_price,
            max_price,
            min_gain,
            max_float,
            min_rvol,
            prefer_live=prefer_live,
            include_learning=include_learning,
        )

    df = st.session_state.scanner_df
    if not df.empty:
        top = df.iloc[0].to_dict()
        status_cards(
            [
                ("Matches", str(len(df)), "calm"),
                ("Best stock", str(top["Ticker"]), "good"),
                ("Best gain", pct(top["Daily gain %"]), "good"),
                ("Best score", f"{int(top['AI score'])}/100", "hot"),
            ]
        )
        render_market_pulse(df, context="scanner")
        render_workflow_cockpit(top, str(top.get("Data source", "n/a")), context="scanner")
        render_action_queue(df, key="scanner_action_queue")
        render_data_health_summary(df)
    show_scan_table(df, key="scanner_results_table")


def page_market_scan() -> None:
    header("Market Scan", "Track core movers, S&P 500 names, global ETFs, crypto, and the full US stock universe in batches.")

    render_data_stack_panel(compact=True)

    clock_df = market_clock_frame()
    with st.container(border=True):
        st.markdown("**Market clocks**")
        st.dataframe(clock_df, width="stretch", hide_index=True)

    with st.form("market_scan_form"):
        preset_options = ["Core movers", "S&P 500", "All US stocks", "Watchlist", "United States", "Europe", "Asia", "Crypto"]
        presets = st.pills(
            "Preset lists",
            preset_options,
            default=["Core movers", "S&P 500", "All US stocks", "Watchlist"],
            selection_mode="multi",
        )
        custom = st.text_area(
            "Add stocks",
            value="",
            height=80,
            placeholder="Example stocks: NVDA, SPY, TSM, BTC-USD",
        )
        cols = st.columns([1, 1, 1, 1])
        batch_size = cols[0].number_input("Batch size", 5, 250, DEFAULT_MARKET_SCAN_BATCH, step=5)
        start_at = cols[1].number_input(
            "Start row",
            0,
            50000,
            int(st.session_state.get("market_scan_start", 0)),
            step=DEFAULT_MARKET_SCAN_BATCH,
        )
        include_etfs = cols[2].toggle("Include ETFs", value=True)
        include_news = cols[3].toggle("Show market news", value=True)
        st.caption("All US stocks can be thousands of names. Use Scan next batch to keep moving through the full list without freezing the app.")
        submitted = st.form_submit_button("Run market scan", type="primary", icon=":material/radar:")

    button_cols = st.columns([1, 1, 3])
    next_batch = button_cols[0].button("Scan next batch", icon=":material/skip_next:")
    reset_progress = button_cols[1].button("Reset progress", icon=":material/restart_alt:")
    button_cols[2].caption("Results are accumulated and de-duplicated as you scan more batches.")

    selected_presets = list(presets or [])
    tickers = market_scan_universe(selected_presets, custom, include_etfs=include_etfs)
    full_source = "Selected lists"
    full_count = 0
    if "All US stocks" in selected_presets:
        full_symbols, full_source = full_us_market_universe(include_etfs=include_etfs, api_marker=finnhub_key_marker())
        full_count = len(full_symbols)

    if reset_progress:
        st.session_state.market_scan_df = pd.DataFrame()
        st.session_state.market_scan_start = 0
        st.session_state.market_scan_batch_tickers = []

    should_scan = submitted or next_batch or "market_scan_df" not in st.session_state
    if should_scan:
        if submitted:
            scan_start = int(start_at)
            accumulated = pd.DataFrame()
        elif next_batch:
            prior_start = int(st.session_state.get("market_scan_start", 0))
            prior_size = int(st.session_state.get("market_scan_batch_size", batch_size))
            scan_start = next_batch_start(prior_start, prior_size, len(tickers))
            accumulated = st.session_state.get("market_scan_df", pd.DataFrame())
        else:
            scan_start = int(st.session_state.get("market_scan_start", start_at))
            accumulated = st.session_state.get("market_scan_df", pd.DataFrame())

        batch_tickers = ticker_batch(tickers, scan_start, int(batch_size))
        st.session_state.market_scan_tickers = tickers
        st.session_state.market_scan_start = scan_start
        st.session_state.market_scan_batch_size = int(batch_size)
        st.session_state.market_scan_batch_tickers = batch_tickers
        st.session_state.market_scan_next_start = next_batch_start(scan_start, int(batch_size), len(tickers))
        with st.skeleton(height=260):
            batch_df = broad_market_scan(tuple(batch_tickers), max_names=len(batch_tickers))
            st.session_state.market_scan_df = merge_market_scan_results(accumulated, batch_df)

    df = st.session_state.get("market_scan_df", pd.DataFrame())
    tickers = st.session_state.get("market_scan_tickers", tickers)
    batch_tickers = st.session_state.get("market_scan_batch_tickers", [])
    scan_start = int(st.session_state.get("market_scan_start", 0))
    next_start = int(st.session_state.get("market_scan_next_start", 0))

    if "All US stocks" in selected_presets:
        st.caption(f"Full universe source: {full_source}. Full-universe symbols loaded: {full_count:,}.")

    current_range = "n/a"
    if tickers and batch_tickers:
        current_range = f"{scan_start + 1:,}-{min(scan_start + len(batch_tickers), len(tickers)):,}"

    status_cards(
        [
            ("Universe queued", f"{len(tickers):,}", "calm"),
            ("Current batch", current_range, "good"),
            ("Rows kept", str(len(df)), "good"),
            ("Next start", f"{next_start:,}", "calm"),
            ("Top mover", str(df.iloc[0]["Ticker"]) if not df.empty else "n/a", "hot"),
            ("Best gain", pct(df.iloc[0]["Daily gain %"]) if not df.empty else "n/a", "good"),
        ]
    )
    render_market_pulse(df, context="market_scan")
    if not df.empty:
        top_scan = df.iloc[0].to_dict()
        render_workflow_cockpit(top_scan, str(top_scan.get("Data source", "n/a")), context="market_scan")
    render_action_queue(df, key="market_scan_action_queue")
    render_data_health_summary(df)

    show_broad_market_table(df)

    if include_news:
        render_lazy_news_expander(
            "General market news",
            lambda: finnhub_market_news("general", limit=8),
            "No general market news returned yet.",
            icon=":material/newspaper:",
        )


def page_charts() -> None:
    compact_header("Charts", "Chart the stock, trend, volume, and paper-trade levels.")
    selected_from_scan = normalize_user_symbol(st.session_state.get("selected_ticker", ""))
    tickers = [row["ticker"] for row in DEMO_PROFILES] + list(INDEX_PROFILES) + read_watchlist()
    if selected_from_scan:
        tickers.append(selected_from_scan)
    ticker_options = sorted(set(tickers))
    selected_index = ticker_options.index(selected_from_scan) if selected_from_scan in ticker_options else 0

    with st.container(border=True):
        control_top = st.columns([1.05, 1.05, 2.0, 0.75], vertical_alignment="bottom")
        selected_ticker = control_top[0].selectbox("Stock", ticker_options, index=selected_index)
        custom_ticker = normalize_user_symbol(control_top[1].text_input("Custom stock", value=""))
        interval = control_top[2].segmented_control(
            "Candle size",
            ["1m", "2m", "5m", "15m", "30m", "60m", "1d"],
            default="1m",
            key="chart_interval",
        )
        interval = str(interval or "1m")

        if interval == "1m":
            period_options = ["1d", "5d"]
        elif interval in {"2m", "5m", "15m", "30m", "60m"}:
            period_options = ["1d", "5d", "1mo", "3mo"]
        else:
            period_options = ["1mo", "3mo", "6mo", "1y", "2y"]

        period = control_top[3].segmented_control(
            "Chart range",
            period_options,
            default="5d" if interval == "1m" and "5d" in period_options else period_options[0],
            key=f"chart_period_{interval}",
        )
        period = str(period or period_options[0])

        candle_windows = {
            "15": 15,
            "30": 30,
            "45": 45,
            "90": 90,
            "180": 180,
            "390": 390,
            "All": None,
        }
        control_bottom = st.columns([1.75, 1.85, 0.62, 0.72, 0.62, 0.62, 0.68], vertical_alignment="bottom")
        default_window = "45" if interval == "1m" else "180"
        window_label = control_bottom[0].segmented_control(
            "Visible candles",
            list(candle_windows),
            default=default_window,
            key=f"chart_visible_candles_{interval}",
        )
        default_engine_label = "TradingView" if st.session_state.get("chart_engine", "TradingView-style") == "TradingView-style" else "Backup"
        engine_label = control_bottom[1].segmented_control(
            "Chart style",
            ["TradingView", "Backup"],
            default=default_engine_label,
            key="chart_engine_label",
        )
        chart_engine = "TradingView-style" if str(engine_label or "TradingView") == "TradingView" else "Backup Plotly"
        st.session_state.chart_engine = chart_engine
        live_toggle = control_bottom[2].toggle("Live", value=True, key="chart_live_enabled")
        auto_refresh = control_bottom[3].toggle("Refresh", value=True, key="chart_auto_refresh_enabled")
        control_bottom[4].toggle("EMAs", value=False, key="chart_layer_emas")
        control_bottom[5].toggle("VWAP", value=True, key="chart_layer_vwap")
        control_bottom[6].toggle("Levels", value=True, key="chart_layer_ai_signals")
        provisional_prefer_live = bool(live_toggle) or interval in {"1m", "2m", "5m", "15m", "30m", "60m"}
        st.caption(
            f"Wheel zoom, drag pan, double-click reset. Data mode: {'live intraday' if provisional_prefer_live else 'learning'}. "
            "1-minute charts load multiple days when available; use 45/90/180/390 for readable candle width, then drag left to review older candles."
        )
    render_data_stack_panel(compact=True)

    st.session_state.chart_layer_ema9 = bool(st.session_state.get("chart_layer_emas", False))
    st.session_state.chart_layer_ema20 = bool(st.session_state.get("chart_layer_emas", False))
    st.session_state.chart_layer_buy_zone = bool(st.session_state.get("chart_layer_ai_signals", True))
    st.session_state.chart_layer_plan_levels = bool(st.session_state.get("chart_layer_ai_signals", True))

    ticker = normalize_user_symbol(custom_ticker or selected_ticker)
    st.session_state.selected_ticker = ticker
    max_candles = candle_windows[window_label]
    prefer_live = bool(live_toggle) or interval in {"1m", "2m", "5m", "15m", "30m", "60m"}

    if prefer_live and auto_refresh:
        auto_refresh_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)
    else:
        render_chart_panel(ticker, period, interval, prefer_live, max_candles=max_candles)


def page_ai_coach() -> None:
    header("AI Coach", "Turn a stock into a structured paper-trade plan.")
    cols = st.columns([1, 1, 2])
    ticker = normalize_user_symbol(cols[0].text_input("Stock", value=st.session_state.get("selected_ticker", "SOUN")))
    period = cols[1].selectbox("Lookback", ["1mo", "3mo", "6mo", "1y"], index=1)
    prefer_live = cols[2].toggle("Use live data", value=True, key="ai_live")

    history, source = load_history(ticker, period=period, interval="1d", prefer_live=prefer_live)
    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=prefer_live)
    render_source_brief(analysis, source)
    render_setup_command_strip(analysis, source, context="ai_coach")
    render_workflow_cockpit(analysis, source, context="ai_coach")
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_ai_decision_panel(analysis, source)
    render_plan_card(analysis)
    render_lazy_news_expander(
        f"News catalyst for {analysis.get('Ticker', ticker)}",
        lambda: finnhub_company_news(str(analysis.get("Ticker", ticker)), days=5, limit=5),
    )

    with st.container(border=True):
        st.markdown("**Paper-trade checklist**")
        st.checkbox("Price is between \\$2 and \\$20", value=2 <= analysis["Price"] <= 20)
        st.checkbox("Daily gain is at least 10%", value=analysis["Daily gain %"] >= 10)
        st.checkbox("Float is under 10M shares", value=analysis["Float M"] <= 10)
        st.checkbox("RVOL is at least 3x", value=analysis["RVOL"] >= 3)
        st.checkbox("Entry, stop, and target are written before entry", value=True)


def page_watchlist() -> None:
    header("Watchlist", "Keep the names you and your friends are studying.")
    watchlist = read_watchlist()
    prefer_live = st.toggle("Use live data", value=True, key="watchlist_live")

    with st.form("add_watchlist"):
        cols = st.columns([1, 3])
        new_ticker = normalize_user_symbol(cols[0].text_input("Stock"))
        add = cols[1].form_submit_button("Add stock", type="primary")
        if add and new_ticker:
            watchlist.append(new_ticker)
            write_watchlist(watchlist)
            st.rerun()

    analyses = [analyze_ticker(ticker, prefer_live=prefer_live) for ticker in watchlist]
    render_action_queue(pd.DataFrame(analyses), key="watchlist_action_queue")

    for analysis in analyses:
        ticker = str(analysis.get("Ticker", ""))
        data_quality, data_color = data_quality_badge(analysis.get("Data source"))
        with st.container(border=True):
            cols = st.columns([1, 1, 1, 1, 1])
            cols[0].metric(ticker, analysis["Setup"])
            cols[1].metric("Price", money(analysis["Price"]), pct(analysis["Daily gain %"]))
            cols[2].metric("RVOL", f"{analysis['RVOL']:.1f}x")
            cols[3].metric("AI score", f"{analysis['AI score']}/100")
            with st.container(horizontal=True):
                st.badge(data_quality, icon=":material/database:", color=data_color)
                st.badge(f"Quote {analysis.get('Quote time', 'n/a')}", icon=":material/schedule:", color="gray")
            st.caption(
                markdown_text(
                    f"Beginner read: {beginner_movement_text(analysis, asset_type_label(analysis))} "
                    f"{beginner_attention_text(analysis)}"
                )
            )
            if cols[4].button("Study", key=f"study_{ticker}"):
                st.session_state.selected_ticker = ticker
                st.session_state.watchlist_study_ticker = ticker
            if cols[4].button("Remove", key=f"remove_{ticker}"):
                write_watchlist([item for item in watchlist if item != ticker])
                st.rerun()

    study_ticker = st.session_state.get("watchlist_study_ticker")
    if study_ticker:
        st.subheader(f"{study_ticker} study plan")
        study_analysis = analyze_ticker(study_ticker, prefer_live=prefer_live)
        render_setup_command_strip(study_analysis, str(study_analysis.get("Data source", "n/a")), context="watchlist")
        render_beginner_stock_summary(study_analysis, str(study_analysis.get("Data source", "n/a")))
        render_plan_card(study_analysis)
        render_lazy_news_expander(
            f"Latest {study_ticker} news",
            lambda: finnhub_company_news(study_ticker, days=5, limit=5),
        )


def page_trade_desk() -> None:
    header("Trade Desk", "Stage AI trade plans, approve them manually, and record paper orders.")
    render_data_stack_panel(compact=True)
    st.warning(
        "This page records approved paper orders only. Real broker execution needs a separate broker connection and another explicit approval step.",
        icon=":material/warning:",
    )

    cols = st.columns([1, 1, 1, 1])
    ticker = normalize_user_symbol(cols[0].text_input("Stock", value=st.session_state.get("selected_ticker", "NVDA")))
    risk_dollars = cols[1].number_input("Max paper risk $", min_value=1.0, max_value=10000.0, value=25.0, step=5.0)
    period = cols[2].selectbox("Lookback", ["1d", "5d", "1mo", "3mo"], index=1)
    interval = cols[3].selectbox("Candle", ["1m", "5m", "15m", "1d"], index=1)

    history, source = load_history(ticker, period=period, interval=interval, prefer_live=True)
    analysis = rebuild_analysis_from_history(ticker, history, source, prefer_live=True)
    render_source_brief(analysis, source)
    render_setup_command_strip(analysis, source, context="trade_desk")
    render_workflow_cockpit(analysis, source, context="trade_desk")
    render_price_audit_panel(ticker, history, analysis, source)
    render_beginner_stock_summary(analysis, source)
    render_ai_decision_panel(analysis, source)

    order = stage_order_from_analysis(analysis, risk_dollars=risk_dollars)
    with st.container(border=True):
        st.markdown("**Staged order**")
        st.dataframe(
            order_display_frame(pd.DataFrame([order])),
            width="stretch",
            hide_index=True,
            column_config=order_column_config(),
        )
        approval_ready = render_paper_approval_gate(analysis, order, source, risk_dollars)
        confirm = st.checkbox(
            "I approve this paper trade plan and understand it is not financial advice.",
            key=f"approve_{ticker}_{order['Entry']}_{order['Stop']}",
            disabled=not approval_ready,
        )
        if st.button("Approve paper order", type="primary", icon=":material/check_circle:", disabled=not (approval_ready and confirm)):
            approve_paper_order(order)
            st.success("Approved paper order saved to Trade Desk and Journal.")
            st.rerun()

    st.subheader("Recent approved paper orders")
    orders = read_orders()
    if orders.empty:
        st.info("No approved paper orders yet.")
    else:
        order_history = order_display_frame(orders).sort_values("Created", ascending=False)
        st.dataframe(
            order_history,
            width="stretch",
            hide_index=True,
            column_config=order_column_config(),
        )


def page_journal() -> None:
    header("Trade Journal", "Track paper trades, wins, losses, and notes.")
    df = read_journal()
    stats = journal_stats(df)
    cols = st.columns(4)
    cols[0].metric("Trades", stats["trades"])
    cols[1].metric("Win rate", pct(stats["win_rate"]))
    cols[2].metric("Total P/L", money(stats["total_pl"]))
    cols[3].metric("Average R", f"{stats['avg_r']:.2f}R")

    render_journal_review_panel(df)

    with st.form("journal_entry"):
        top = st.columns([1, 1, 2])
        trade_date = top[0].date_input("Date", value=date.today())
        ticker = normalize_user_symbol(top[1].text_input("Stock", value=st.session_state.get("selected_ticker", "SOUN")))
        setup = top[2].text_input("Setup", value="Momentum gapper")

        nums = st.columns(4)
        entry = nums[0].number_input("Entry", min_value=0.0, value=5.00, step=0.05)
        exit_price = nums[1].number_input("Exit", min_value=0.0, value=5.40, step=0.05)
        stop = nums[2].number_input("Stop", min_value=0.0, value=4.75, step=0.05)
        shares = nums[3].number_input("Shares", min_value=1, value=100, step=10)
        notes = st.text_area("Notes", height=90)
        submitted = st.form_submit_button("Save paper trade", type="primary")

    if submitted:
        pl = (exit_price - entry) * shares
        pl_pct = ((exit_price - entry) / entry * 100) if entry else 0
        risk = max(entry - stop, entry * 0.01)
        r_multiple = (exit_price - entry) / risk
        append_journal(
            {
                "Date": trade_date.isoformat(),
                "Ticker": ticker,
                "Setup": setup,
                "Entry": entry,
                "Exit": exit_price,
                "Stop": stop,
                "Shares": shares,
                "P/L $": round(pl, 2),
                "P/L %": round(pl_pct, 2),
                "R multiple": round(r_multiple, 2),
                "Notes": notes,
            }
        )
        st.success("Paper trade saved.")
        st.rerun()

    if df.empty:
        st.info("No journal entries yet.")
    else:
        display_df = journal_display_frame(df)
        with st.container(border=True):
            st.markdown("**Journal entries**")
            filter_cols = st.columns([1, 1, 1.4], vertical_alignment="bottom")
            stocks = ["All", *sorted(display_df["Ticker"].dropna().astype(str).unique().tolist())]
            stock_filter = filter_cols[0].selectbox("Stock filter", stocks, key="journal_stock_filter")
            result_filter = filter_cols[1].segmented_control(
                "Result",
                ["All", "Wins", "Losses", "Flat"],
                default="All",
                key="journal_result_filter",
            )
            query = filter_cols[2].text_input(
                "Search notes/setup",
                value="",
                placeholder="Try chase, stop, news, spread, setup",
                key="journal_note_search",
            )
            filtered_df = display_df.copy()
            if stock_filter != "All":
                filtered_df = filtered_df[filtered_df["Ticker"].astype(str) == str(stock_filter)]
            if result_filter == "Wins":
                filtered_df = filtered_df[pd.to_numeric(filtered_df["P/L $"], errors="coerce").fillna(0) > 0]
            elif result_filter == "Losses":
                filtered_df = filtered_df[pd.to_numeric(filtered_df["P/L $"], errors="coerce").fillna(0) < 0]
            elif result_filter == "Flat":
                filtered_df = filtered_df[pd.to_numeric(filtered_df["P/L $"], errors="coerce").fillna(0) == 0]
            query_text = str(query or "").strip().lower()
            if query_text:
                searchable = (
                    filtered_df["Setup"].fillna("").astype(str)
                    + " "
                    + filtered_df["Notes"].fillna("").astype(str)
                ).str.lower()
                filtered_df = filtered_df[searchable.str.contains(query_text, regex=False, na=False)]

            st.caption(f"Showing {len(filtered_df)} of {len(display_df)} journal rows.")
            st.dataframe(
                filtered_df.sort_values("Date", ascending=False),
                width="stretch",
                hide_index=True,
                column_config=journal_column_config(),
            )


def page_backtester() -> None:
    header("Backtester", "Test the momentum-gap rule on recent history.")
    with st.form("backtester_form"):
        cols = st.columns(5)
        ticker = normalize_user_symbol(cols[0].text_input("Stock", value="SOUN"))
        period = cols[1].selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)
        min_gap = cols[2].number_input("Min gap %", 1.0, 50.0, 10.0, step=1.0)
        min_rvol = cols[3].number_input("Min RVOL", 0.5, 20.0, 3.0, step=0.5)
        hold_days = cols[4].number_input("Hold days", 1, 10, 3, step=1)
        prefer_live = st.toggle("Use live data", value=True, key="backtest_live")
        run = st.form_submit_button("Run backtest", type="primary")

    if run or "backtest_result" not in st.session_state:
        st.session_state.backtest_result = backtest_strategy(ticker, period, prefer_live, min_gap, min_rvol, hold_days)

    result = st.session_state.backtest_result
    summary = result["summary"]
    cols = st.columns(4)
    cols[0].metric("Trades", summary["Trades"])
    cols[1].metric("Win rate", pct(summary["Win rate"]))
    cols[2].metric("Average gain", pct(summary["Average gain %"]))
    cols[3].metric("Average R", f"{summary['Average R']:.2f}R")

    render_backtest_review_panel(result)

    trades = result["trades"]
    if trades.empty:
        st.info("No completed backtest trades matched those settings.")
    else:
        trades = trades.copy()
        trades["Date"] = pd.to_datetime(trades["Date"], errors="coerce")
        st.dataframe(
            trades,
            width="stretch",
            hide_index=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
                "Entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
                "Exit": st.column_config.NumberColumn("Exit", format="$%.2f"),
                "Stop": st.column_config.NumberColumn("Stop", format="$%.2f"),
                "Gain %": st.column_config.NumberColumn("Gain", format="%.2f%%"),
                "R multiple": st.column_config.NumberColumn("R", format="%.2f"),
                "RVOL": st.column_config.NumberColumn("RVOL", format="%.1fx"),
                "Gap %": st.column_config.NumberColumn("Gap", format="%.1f%%"),
            },
        )
    st.caption(f"Backtest source: {result['source']}. Backtests are simplified and for learning only.")


def page_learn() -> None:
    header("Learn", "A practical day-trading study guide for the scanner, charts, news, risk, and journaling.")

    track_options = [
        "Start here",
        "Place a paper trade",
        "Order ticket",
        "Playbook",
        "Routine",
        "Chart reading",
        "Risk",
        "Workflow cockpit",
        "Market pulse",
        "AI ladder",
        "Data sources",
        "News",
        "Flashcards",
        "Quiz",
        "Practice",
        "Glossary",
        "iPad",
    ]
    requested_track = str(st.query_params.get("track", "") or "").replace("_", " ").strip()
    requested_match = next((option for option in track_options if option.lower() == requested_track.lower()), "Start here")
    track = st.selectbox(
        "Learning track",
        track_options,
        index=track_options.index(requested_match),
        width="stretch",
    )
    track = track or "Start here"

    if track == "Start here":
        st.warning(
            "Begin in paper trading. Do not place real orders until you understand order types, broker rules, risk, and how fast losses can happen.",
            icon=":material/warning:",
        )
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**1. Learn the screen**")
                st.write("- Dashboard shows the best current study idea.")
                st.write("- Market Scan checks big lists like S&P 500 and all US stocks in batches.")
                st.write("- Scanner focuses on the low-priced momentum rules.")
                st.write("- Charts shows candles, VWAP, EMAs, news, and plan levels.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**2. Learn the plan**")
                st.write("- Buy zone is where a pullback still looks controlled.")
                st.write("- Entry trigger is the level where buyers confirm strength.")
                st.write("- Stop is where the idea is wrong.")
                st.write("- Target is where reward starts to justify the risk.")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**3. Practice the workflow**")
                st.write("- Pick one stock from Scanner or Market Scan.")
                st.write("- Open Charts and check trend, volume, news, and levels.")
                st.write("- Open Trade Desk and stage a paper order.")
                st.write("- Save the result in Journal after the trade is done.")

        with st.container(border=True):
            st.markdown("**The app workflow for a brand-new trader**")
            st.write("1. Go to Market Scan to see what the broad market and big names are doing.")
            st.write("2. Go to Scanner for small-cap momentum candidates that match the app rules.")
            st.write("3. Click a stock row, then open Charts to inspect the candle trend and plan levels.")
            st.write("4. Read the AI decision. If it says Study only or Watch only, do not force a trade.")
            st.write("5. Open Trade Desk, set your max paper risk, review the staged order, and only approve if every checklist item makes sense.")
            st.write("6. Open Journal and record what happened, even if you skipped the trade.")

        with st.container(border=True):
            st.markdown("**How to read any stock page**")
            reading_guide = pd.DataFrame(
                [
                    {"Field": "Price now", "What it means": "Where the stock is trading right now.", "Beginner move": "Compare it with entry, stop, and target before doing anything."},
                    {"Field": "Daily move", "What it means": "How far price moved from the previous close.", "Beginner move": "A big green number means attention, not an automatic buy."},
                    {"Field": "RVOL", "What it means": "Today's volume compared with normal volume.", "Beginner move": "The app wants high attention, usually 3x or more for this playbook."},
                    {"Field": "Float", "What it means": "Roughly how many shares can trade publicly.", "Beginner move": "Low float can move fast, but it can also reverse fast."},
                    {"Field": "Price audit", "What it means": "The app checks source, time, and whether price feeds disagree.", "Beginner move": "If it says mismatch or fallback, use the stock for study only."},
                    {"Field": "Data confidence", "What it means": "A quick trust label based on source, quote age, fallback data, and feed agreement.", "Beginner move": "High confidence is cleaner for paper practice. Verify first means slow down and check another source."},
                    {"Field": "Market pulse", "What it means": "The app reads the whole scan and summarizes data trust, active setups, top stock, and risk flags.", "Beginner move": "Use it to decide whether to chart the leader, wait, verify data, or scan another batch."},
                    {"Field": "AI score", "What it means": "A checklist score based on the app's rules.", "Beginner move": "Use it to focus your study, not as a profit promise."},
                    {"Field": "Workflow cockpit", "What it means": "The panel that tells you the next best page/action based on the current stock.", "Beginner move": "Use it as your map: scan, verify, chart, plan, approve, journal."},
                    {"Field": "AI ladder", "What it means": "A step-by-step read of data, setup, entry, stop, and take-profit levels.", "Beginner move": "Read the ladder in order before staging any paper order."},
                    {"Field": "Entry trigger", "What it means": "The confirmation price.", "Beginner move": "Avoid guessing early. Wait for confirmation on the chart."},
                    {"Field": "Stop loss", "What it means": "Where the idea is wrong.", "Beginner move": "If this loss feels too big, reduce paper size or skip."},
                    {"Field": "Take profit", "What it means": "A planned exit where reward starts to pay for risk.", "Beginner move": "Know the reward before the entry."},
                ]
            )
            st.dataframe(reading_guide, width="stretch", hide_index=True)
            st.caption("Data confidence labels: High confidence is cleaner for paper practice, Usable for paper is acceptable for learning, Verify first means check another source, and Practice data means do not treat it as live.")

        with st.container(border=True):
            st.markdown("**What the app levels mean**")
            level_guide = pd.DataFrame(
                [
                    {"Level": "Current", "Plain English": "Where the stock is trading now.", "Beginner rule": "Do not buy just because this number is moving."},
                    {"Level": "Entry trigger", "Plain English": "The price that confirms buyers are showing strength.", "Beginner rule": "Paper buy only after confirmation, not before."},
                    {"Level": "Stop loss", "Plain English": "The price where the idea is wrong.", "Beginner rule": "If you cannot accept this planned loss, the trade is too big."},
                    {"Level": "Take profit 1", "Plain English": "The first planned sell/trim area.", "Beginner rule": "This is where reward starts paying for the risk."},
                    {"Level": "Runner target", "Plain English": "A second target if the move keeps working.", "Beginner rule": "Do not hold a runner without a written exit plan."},
                ]
            )
            st.dataframe(level_guide, width="stretch", hide_index=True)

        with st.container(border=True):
            st.markdown("**Beginner roadmap**")
            st.write("1. Learn the words: use Glossary until the order ticket terms make sense.")
            st.write("2. Learn the levels: current price, entry trigger, stop loss, take profit 1, runner target.")
            st.write("3. Learn the scanner: price, gap, float, RVOL, volume, catalyst.")
            st.write("4. Learn the chart: candles, VWAP, EMAs, support, resistance, breakout, pullback.")
            st.write("5. Paper trade only: approve practice orders and journal every result.")
            st.write("6. Review mistakes: missed entry, chase, bad stop, bad news read, oversized risk.")
            st.write("7. Repeat until you can explain every trade idea without guessing.")

        with st.container(border=True):
            st.markdown("**Study tools inside Learn**")
            tool_cols = st.columns(3)
            with tool_cols[0]:
                st.markdown("**Flashcards**")
                st.write("Practice the words until entry, stop loss, take profit, RVOL, VWAP, and spread feel natural.")
            with tool_cols[1]:
                st.markdown("**Quiz**")
                st.write("Grade yourself on the most common beginner mistakes before approving a paper trade.")
            with tool_cols[2]:
                st.markdown("**Practice drill**")
                st.write("Pick a real stock, read the AI plan, and complete the checklist without risking money.")

        render_training_progress_panel()

        with st.container(border=True):
            st.markdown("**Beginner safety rules**")
            st.write("- A stock moving fast is not automatically a good trade.")
            st.write("- A plan has entry, stop, target, share size, and a reason before the order is placed.")
            st.write("- Market orders can fill at a worse price than expected in fast stocks.")
            st.write("- Limit and stop orders still need care; different brokers support different instructions.")
            st.write("- Real day trading can trigger broker, margin, tax, and pattern day trader rules.")

    elif track == "Place a paper trade":
        st.info(
            "This section teaches the paper-trade process. It is a practice workflow, not a recommendation to buy or sell any stock.",
            icon=":material/school:",
        )
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before you stage the order**")
                st.write("1. Pick a stock from Scanner or Market Scan.")
                st.write("2. Open Charts and confirm the 1-minute or 5-minute candle trend.")
                st.write("3. Check that price is not far above the buy zone.")
                st.write("4. Check news, volume, RVOL, float, and spread risk.")
                st.write("5. Decide your max paper risk before thinking about shares.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Inside Trade Desk**")
                st.write("1. Enter the stock symbol.")
                st.markdown(markdown_text("2. Set Max paper risk, like $10, $25, or $50."))
                st.write("3. Choose the lookback and candle size.")
                st.write("4. Read the AI decision and setup checks.")
                st.write("5. Complete the approval checklist.")
                st.write("6. Review Entry, Stop, Target, Shares, and Reason before approval.")

        with st.container(border=True):
            st.markdown("**Position size in plain English**")
            st.markdown(markdown_text("If entry is $5.00 and stop is $4.75, the risk is $0.25 per share."))
            st.markdown(markdown_text("If max paper risk is $25, then $25 / $0.25 = 100 shares."))
            st.write("If the stop is farther away, share size should be smaller. If you cannot accept the loss at the stop, the trade is too large.")

        with st.container(border=True):
            st.markdown("**What to do after approval**")
            st.write("- Paper order approved: the app saves it to Trade Desk and Journal.")
            st.write("- If price reaches the stop: mark the paper trade as invalid and record the planned loss.")
            st.write("- If price reaches target 1: record what happened and whether the plan was followed.")
            st.write("- If price never triggers: write 'no trade' in your notes. Skipping is part of trading.")
            st.write("- If the checklist blocks approval: treat that as a saved lesson, not a failure.")

        with st.container(border=True):
            st.markdown("**Do not approve if...**")
            st.write("- You cannot explain why the stock is moving.")
            st.write("- The AI says Study only, Watch only, or Plan invalid.")
            st.write("- The approval checklist is not complete.")
            st.write("- The entry is far above the buy zone and you would be chasing.")
            st.write("- The spread is wide, candles are erratic, or news is unclear.")
            st.write("- You are increasing size because you want to make back a loss.")

    elif track == "Order ticket":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Common broker ticket fields**")
                st.write("- Symbol: the stock symbol, like NVDA or SOUN.")
                st.write("- Side: buy, sell, sell short, or buy to cover.")
                st.write("- Quantity: how many shares.")
                st.write("- Order type: market, limit, stop, or stop-limit.")
                st.write("- Time in force: how long the order stays active.")
                st.write("- Review: final confirmation before sending.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Order types for beginners**")
                st.write("- Market order: tries to fill immediately, but the final price can be different from what you saw.")
                st.write("- Limit order: sets the worst price you are willing to accept.")
                st.write("- Stop order: triggers after a stop price is reached, then can become a market order.")
                st.write("- Stop-limit order: triggers after a stop price, but only fills inside your limit.")
                st.write("- Not every broker supports every order instruction the same way.")

        with st.container(border=True):
            st.markdown("**How the app's staged paper order maps to a broker ticket**")
            mapping = pd.DataFrame(
                [
                    {"App field": "Stock", "Broker ticket field": "Symbol", "Beginner meaning": "The stock you are practicing."},
                    {"App field": "Side", "Broker ticket field": "Action", "Beginner meaning": "Usually Buy for this paper long setup."},
                    {"App field": "Shares", "Broker ticket field": "Quantity", "Beginner meaning": "Calculated from max paper risk and stop distance."},
                    {"App field": "Entry", "Broker ticket field": "Stop or limit price", "Beginner meaning": "The confirmation level, not a guarantee."},
                    {"App field": "Stop", "Broker ticket field": "Stop-loss plan", "Beginner meaning": "Where the idea is wrong."},
                    {"App field": "Target 1", "Broker ticket field": "Target/exit plan", "Beginner meaning": "Where reward begins to pay for the risk."},
                ]
            )
            st.dataframe(mapping, width="stretch", hide_index=True)

        with st.container(border=True):
            st.markdown("**Real-order caution**")
            st.write("- The app records paper trades. It does not place real broker orders by itself.")
            st.write("- Before real trading, confirm your broker's order types, margin rules, fees, and day-trading restrictions.")
            st.write("- Always review the broker confirmation screen before sending any real order.")

    elif track == "Playbook":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**The setup this app is built around**")
                st.markdown(markdown_text("- Price: $2 to $20 for the small-account momentum style."))
                st.write("- Daily gain: at least 10%, usually found through top-gapper scans.")
                st.write("- Float: preferably under 10M shares, because small supply can move faster.")
                st.write("- RVOL: at least 3x, showing today is much more active than normal.")
                st.write("- Chart: price should hold above VWAP/EMAs instead of fading immediately.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**What the AI plan is trying to do**")
                st.write("- Buy zone: where a pullback still looks controlled.")
                st.write("- Entry trigger: the price that confirms buyers are stepping in.")
                st.write("- Stop: the level where the idea is wrong.")
                st.write("- Targets: where the reward starts to justify the risk.")
                st.write("- Confidence: a study score, not a promise.")

        with st.container(border=True):
            st.markdown("**Daily routine**")
            st.write("1. Check the Market Scan for broad market strength and big-name leaders.")
            st.write("2. Run the Scanner for low-priced momentum candidates.")
            st.write("3. Open Charts and confirm 1-minute/5-minute trend, VWAP, volume, and news catalyst.")
            st.write("4. Write the entry, stop, and target before any paper trade.")
            st.write("5. Save the result in Journal and review what happened.")

        with st.container(border=True):
            st.markdown("**Scanner labels**")
            st.write("- Playbook fit: price, gain, float, RVOL, and score are all lined up.")
            st.write("- Developing setup: most rules are close, but it still needs confirmation.")
            st.write("- Wait for confirmation: do not chase; wait for the buy zone or trigger.")
            st.write("- Market context: useful for SPY, QQQ, NVDA, and leaders, but not the small-float playbook.")
            st.write("- Study only: good for learning, not a primary paper-trade idea right now.")

    elif track == "Routine":
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before the open**")
                st.write("- Build a short watchlist instead of chasing every mover.")
                st.write("- Check news, float, relative volume, and whether the stock is easy to borrow or has special risk.")
                st.write("- Mark the levels where the idea works and where it is wrong.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**During the open**")
                st.write("- Wait for the first clean setup instead of buying the first candle.")
                st.write("- Prefer entries near planned levels with volume confirmation.")
                st.write("- If the spread is wide or candles are chaotic, stand aside.")
        with cols[2]:
            with st.container(border=True):
                st.markdown("**After the session**")
                st.write("- Journal the plan, result, and whether you followed the rules.")
                st.write("- Review screenshots of entries you skipped and entries you took.")
                st.write("- Improve one rule at a time instead of changing everything.")

        with st.container(border=True):
            st.markdown("**Review questions**")
            st.write("- Was the trade actually part of the scanner playbook?")
            st.write("- Did the entry happen near the buy zone or after a clean trigger?")
            st.write("- Did news and volume support the move?")
            st.write("- Was the risk small enough to repeat the setup many times?")

    elif track == "Chart reading":
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**VWAP**")
                st.write("VWAP is the average price weighted by volume. Above VWAP often means buyers are in control; below VWAP means caution.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**EMA 9 / EMA 20**")
                st.write("The 9 EMA tracks fast momentum. The 20 EMA is slower. Strong intraday trends often respect these lines.")
        with cols[2]:
            with st.container(border=True):
                st.markdown("**Volume**")
                st.write("Volume confirms interest. A breakout without volume is easier to fail. A pullback with lighter volume can be healthier.")

        with st.container(border=True):
            st.markdown("**Common chart states**")
            st.write("- Opening push: big candles and high volume after the bell.")
            st.write("- Controlled pullback: price dips but holds VWAP/EMA support.")
            st.write("- Breakout trigger: price clears the plan level with volume.")
            st.write("- Failed setup: price loses VWAP, loses the stop, or spreads widen.")

    elif track == "Risk":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Before entry**")
                st.write("- Know the stop before the entry.")
                st.write("- Make sure target 1 is at least 1.5R away.")
                st.write("- Avoid chasing far above the trigger.")
                st.write("- Skip halted stocks, huge spreads, and unclear news.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**Position sizing example**")
                st.markdown(markdown_text("If a paper account risks $25 and the entry is $5.00 with a $4.75 stop, risk is $0.25/share."))
                st.markdown(markdown_text("$25 / $0.25 = 100 shares."))
                st.write("This app helps write the plan, but you still approve every trade idea.")

        with st.container(border=True):
            st.markdown("**Loss rules**")
            st.write("- One planned loss is tuition. A chased loss is a habit problem.")
            st.write("- If the setup breaks the stop, the idea is invalid.")
            st.write("- If you miss the entry, wait for the next clean setup.")

    elif track == "Workflow cockpit":
        st.info(
            "The workflow cockpit is the app's map. It shows what to do next so a beginner does not jump straight from a moving candle into a trade idea.",
            icon=":material/route:",
        )
        sample_analysis = analyze_ticker("SOUN", prefer_live=False)
        render_workflow_cockpit(sample_analysis, str(sample_analysis.get("Data source", "Learning")), context="learn_workflow")

        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**Read the top box first**")
                st.write("- Recommended next step tells you where to go now.")
                st.write("- Green means review carefully.")
                st.write("- Orange means wait or verify.")
                st.write("- Red means stand down or rebuild.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**Read the six workflow tiles**")
                st.write("- Stock found")
                st.write("- Data verified")
                st.write("- Setup rules")
                st.write("- Chart status")
                st.write("- Risk/reward")
                st.write("- Paper workflow")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**Use the buttons**")
                st.write("- Open Charts to inspect candles.")
                st.write("- Open Trade Desk only when the setup is clean.")
                st.write("- Open Journal after every paper decision.")
                st.write("- Study the ladder when the terms feel unclear.")

        with st.container(border=True):
            st.markdown("**Beginner rule**")
            st.write("If the cockpit says verify, wait, stand down, or keep scanning, that is still a decision. The best beginner trade is often no trade.")

    elif track == "Market pulse":
        st.info(
            "Market pulse is the fast read before you stare at individual candles. It tells you whether the scan is clean enough to study seriously or whether you should verify, wait, or keep scanning.",
            icon=":material/monitoring:",
        )
        sample_df = default_scan(prefer_live=False)
        render_market_pulse(sample_df, context="learn_market_pulse", show_actions=False)

        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**1. Start with data trust**")
                st.write("- High confidence or usable for paper means the row is cleaner for practice.")
                st.write("- Verify first means compare another source before trusting levels.")
                st.write("- Practice data means learning only, not live trading truth.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**2. Read setup pressure**")
                st.write("- Active means breakout trigger or buy zone.")
                st.write("- Waiting means near buy zone or momentum active.")
                st.write("- Quiet means keep scanning or study instead of forcing trades.")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**3. Respect risk flags**")
                st.write("- Fallback rows, no quotes, below-stop rows, and low RVOL slow you down.")
                st.write("- A risk flag is a reason to verify, not a reason to panic.")
                st.write("- The best next move box tells you the page to open next.")

        with st.container(border=True):
            st.markdown("**How to use market pulse during the day**")
            pulse_steps = pd.DataFrame(
                [
                    {"Pulse says": "Paper setups are forming", "Do this": "Open Charts for the top stock and verify candles, news, entry, stop, and target.", "Do not do this": "Approve a paper order without reading the ladder."},
                    {"Pulse says": "Good watchlist, wait for the trigger", "Do this": "Keep the chart open and wait for price to reach the planned level.", "Do not do this": "Buy early because the stock feels strong."},
                    {"Pulse says": "Verify prices before trusting this scan", "Do this": "Compare the price audit, source time, broker quote, and news.", "Do not do this": "Assume free data is perfect."},
                    {"Pulse says": "Quiet or mixed scan", "Do this": "Scan another batch, read news, or study Learn.", "Do not do this": "Force a paper trade just to be active."},
                ]
            )
            st.dataframe(pulse_steps, width="stretch", hide_index=True)

        with st.container(border=True):
            st.markdown("**Beginner rule**")
            st.write("Market pulse answers one question: is this a chart-review moment, a wait moment, a verify moment, or a study moment?")

    elif track == "AI ladder":
        st.info(
            "The AI ladder is the easiest way to slow down before a paper order. Read every step in order.",
            icon=":material/stairs:",
        )
        sample_analysis = analyze_ticker("SOUN", prefer_live=False)
        render_ai_plan_ladder(sample_analysis, str(sample_analysis.get("Data source", "Learning")))

        ladder_cards = [
            ("1. Data check", "Ask: can I trust this price enough for paper practice?", "If it says Verify first or Practice data, slow down and compare another source."),
            ("2. Setup check", "Ask: do the scanner rules actually line up?", "Price, gap, float, RVOL, trend, risk, and action status should mostly agree."),
            ("3. Entry trigger", "Ask: what exact price proves buyers are showing up?", "Do not buy early just because the stock is moving."),
            ("4. Stop loss", "Ask: where is the idea wrong?", "If the stop feels too far away, reduce size or skip."),
            ("5. Take profit", "Ask: does the reward pay enough for the risk?", "Target 1 should usually offer at least about 1.5R for this practice style."),
        ]
        top_cards = st.columns(3)
        bottom_cards = st.columns(2)
        for col, (title, question, rule_text) in zip(list(top_cards) + list(bottom_cards), ladder_cards):
            with col:
                with st.container(border=True, height="stretch"):
                    st.markdown(f"**{title}**")
                    st.write(question)
                    st.caption(rule_text)

        with st.container(border=True):
            st.markdown("**How to use it on Charts or Trade Desk**")
            st.write("1. If Data check is weak, treat the stock as study only until another source agrees.")
            st.write("2. If Setup check is weak, do not force a trade just because one candle looks strong.")
            st.write("3. If Entry trigger says Wait, do not approve a paper order yet.")
            st.write("4. If Stop loss says invalid or price is below the stop, rebuild the plan from fresh candles.")
            st.write("5. If Take profit does not pay enough reward, skip or wait for a cleaner setup.")

        with st.container(border=True):
            st.markdown("**Beginner translation**")
            st.write("The ladder is not telling you to buy. It is telling you what must be true before a paper trade idea is even worth reviewing.")

    elif track == "Data sources":
        render_data_stack_panel(compact=False)
        cols = st.columns(3)
        with cols[0]:
            with st.container(border=True, height="stretch"):
                st.markdown("**What live means**")
                st.write("- Live data can still be exchange-limited, delayed, or missing for some symbols.")
                st.write("- The app shows source and confidence so you know when to slow down.")
                st.write("- Free feeds are good for learning and paper-trading practice, not perfect execution truth.")
        with cols[1]:
            with st.container(border=True, height="stretch"):
                st.markdown("**How to read confidence**")
                st.write("- High confidence: source and time look cleaner.")
                st.write("- Usable for paper: acceptable for practice, still verify.")
                st.write("- Verify first: check another source before trusting the idea.")
                st.write("- Practice data: learning fallback, not live market data.")
        with cols[2]:
            with st.container(border=True, height="stretch"):
                st.markdown("**When to double-check**")
                st.write("- Price is moving very fast.")
                st.write("- The chart and quote differ.")
                st.write("- The spread is wide.")
                st.write("- News dropped in premarket or after-hours.")
                st.write("- You are about to approve a paper order.")

        with st.container(border=True):
            st.markdown("**Beginner rule**")
            st.write("If the app says verify first, treat the stock as a study idea until another quote source agrees with the chart and the news.")

    elif track == "News":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Catalysts that can move small caps**")
                st.write("- Earnings or guidance")
                st.write("- Contract wins")
                st.write("- FDA, patent, or regulatory headlines")
                st.write("- Analyst upgrades")
                st.write("- Sector sympathy, like AI/quantum/space momentum")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**News checks**")
                st.write("- Is the news fresh today?")
                st.write("- Is it real company news or just social hype?")
                st.write("- Is volume confirming the headline?")
                st.write("- Did the move already exhaust before you found it?")

        with st.container(border=True):
            st.markdown("**How to use the Dashboard news rail**")
            st.write("- Biggest news dropped ranks headlines by freshness, catalyst words, risk words, and symbols the app is already scanning.")
            st.write("- Impact is not a buy signal. It means the headline deserves attention before you stage a paper trade.")
            st.write("- Risk headlines like offerings, halts, lawsuits, investigations, or delisting warnings should slow you down.")
            st.write("- Good news still needs chart confirmation: volume, VWAP/EMA hold, clean entry, written stop, and enough reward.")

        with st.container(border=True):
            st.markdown("**Live market news**")
            render_news_items(finnhub_market_news("general", limit=6), "Add your Finnhub key or try again later for live news.")

    elif track == "Flashcards":
        cards = [
            {"term": "Entry trigger", "category": "Risk", "answer": "The price that confirms buyers are stepping in. You wait for this instead of guessing early.", "example": "If the plan says entry above $5.12, a beginner waits for that confirmation."},
            {"term": "Stop loss", "category": "Risk", "answer": "The level where the setup is wrong. It defines the planned loss before entry.", "example": "If entry is $5.12 and stop is $4.92, the risk is $0.20 per share."},
            {"term": "Take profit 1", "category": "Risk", "answer": "The first planned area to sell or trim because reward is starting to pay for the risk.", "example": "A first target near 1.5R to 2R lets you measure reward before entering."},
            {"term": "Runner target", "category": "Risk", "answer": "A second target for any remaining shares if the move keeps working.", "example": "A runner still needs a written exit instead of hoping."},
            {"term": "R multiple", "category": "Risk", "answer": "Reward or loss measured against the planned risk.", "example": "If you risk $20 and make $40, that is +2R."},
            {"term": "RVOL", "category": "Scanner", "answer": "Relative volume. It compares today's volume with normal volume and shows whether attention is unusual.", "example": "A 5x RVOL stock is trading far more activity than normal."},
            {"term": "Market pulse", "category": "Scanner", "answer": "The scan-wide summary that shows data trust, active setups, top stock, scan power, and risk flags.", "example": "If pulse says verify first, a beginner checks the chart and another quote before trusting levels."},
            {"term": "Float", "category": "Scanner", "answer": "Shares available for public trading. Lower float can move faster, but it can also be more dangerous.", "example": "A 7M float stock can move sharply when demand spikes."},
            {"term": "Gapper", "category": "Scanner", "answer": "A stock trading much higher than yesterday's close.", "example": "The app looks for at least a 10% daily move in the small-cap playbook."},
            {"term": "Liquidity", "category": "Scanner", "answer": "How easy it is to buy or sell without moving the price too much.", "example": "Thin liquidity can make exits ugly even if the chart looked good."},
            {"term": "VWAP", "category": "Charts", "answer": "Volume-weighted average price. Many intraday traders use it as a control line.", "example": "A stock holding above VWAP is often healthier than one fading below it."},
            {"term": "EMA 9", "category": "Charts", "answer": "A fast moving average that helps show short-term momentum.", "example": "Strong trends often ride the 9 EMA instead of breaking below it."},
            {"term": "Support", "category": "Charts", "answer": "A price area where buyers recently defended the stock.", "example": "A pullback holding support can be cleaner than buying straight up."},
            {"term": "Resistance", "category": "Charts", "answer": "A price area where sellers recently stopped the stock.", "example": "Breakouts need to clear resistance with volume."},
            {"term": "Spread", "category": "Orders", "answer": "The gap between bid and ask. Wide spreads make entries and exits harder.", "example": "A $5.00 bid and $5.18 ask is expensive for a beginner setup."},
            {"term": "Limit order", "category": "Orders", "answer": "An order that sets the worst price you are willing to accept. It may not fill.", "example": "A buy limit at $5.10 will not intentionally pay above $5.10."},
            {"term": "Market order", "category": "Orders", "answer": "An order that tries to fill immediately. It can slip badly in fast stocks.", "example": "A market order in a fast small cap may fill far away from the price you saw."},
            {"term": "Stop order", "category": "Orders", "answer": "An order that activates after a stop price is reached.", "example": "Some stop orders become market orders after triggering."},
            {"term": "Time in force", "category": "Orders", "answer": "How long an order stays active.", "example": "A day order expires after the session; a GTC order can stay open longer."},
            {"term": "Offering", "category": "News", "answer": "A company sells more shares. This can pressure price because supply increases.", "example": "An offering headline can quickly break a momentum move."},
            {"term": "Dilution", "category": "News", "answer": "Existing shares represent a smaller slice after new shares are issued.", "example": "Small caps can reverse fast when dilution risk appears."},
            {"term": "Halt", "category": "News", "answer": "A temporary pause in trading. A halted stock can reopen far above or below the last price.", "example": "New traders should be careful around halt risk."},
            {"term": "Catalyst", "category": "News", "answer": "The reason traders are paying attention today.", "example": "Earnings, FDA news, contracts, and upgrades can all be catalysts."},
        ]
        deck_options = ["All", "Orders", "Risk", "Charts", "Scanner", "News"]
        deck = st.segmented_control("Deck", deck_options, default="All", key="learn_flash_deck")
        deck = str(deck or "All")
        filtered_cards = [card for card in cards if deck == "All" or card["category"] == deck]
        st.session_state.learn_flash_index = int(st.session_state.get("learn_flash_index", 0)) % len(filtered_cards)
        index = st.session_state.learn_flash_index
        card = filtered_cards[index]
        term = str(card["term"])
        known_terms = set(st.session_state.get("learn_flash_known", []))
        review_terms = set(st.session_state.get("learn_flash_review", []))

        stat_cols = st.columns(4)
        stat_cols[0].metric("Deck", deck, border=True)
        stat_cols[1].metric("Cards", str(len(filtered_cards)), border=True)
        stat_cols[2].metric("Known", str(len(known_terms)), border=True)
        stat_cols[3].metric("Review", str(len(review_terms)), border=True)

        with st.container(border=True):
            st.markdown("**Flashcard deck**")
            st.progress((index + 1) / len(filtered_cards))
            st.caption(f"Card {index + 1} of {len(filtered_cards)} | {card['category']}")
            st.markdown(f"### {term}")
            safe_deck = deck.lower().replace(" ", "_")
            if st.toggle("Show answer", key=f"flash_show_{safe_deck}_{index}"):
                st.write(card["answer"])
                st.caption(f"Example: {card['example']}")
            cols = st.columns([1, 1, 1, 1, 1.2])
            if cols[0].button("Previous", icon=":material/chevron_left:"):
                st.session_state.learn_flash_index = (index - 1) % len(filtered_cards)
                st.rerun()
            if cols[1].button("Next", icon=":material/chevron_right:", type="primary"):
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[2].button("I knew it", icon=":material/check_circle:"):
                known_terms.add(term)
                review_terms.discard(term)
                st.session_state.learn_flash_known = sorted(known_terms)
                st.session_state.learn_flash_review = sorted(review_terms)
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[3].button("Review", icon=":material/replay:"):
                review_terms.add(term)
                known_terms.discard(term)
                st.session_state.learn_flash_known = sorted(known_terms)
                st.session_state.learn_flash_review = sorted(review_terms)
                st.session_state.learn_flash_index = (index + 1) % len(filtered_cards)
                st.rerun()
            if cols[4].button("Reset", icon=":material/restart_alt:"):
                st.session_state.learn_flash_index = 0
                st.session_state.learn_flash_known = []
                st.session_state.learn_flash_review = []
                st.rerun()

        with st.container(border=True):
            st.markdown("**How to study these**")
            st.write("- Say the answer out loud before revealing it.")
            st.write("- Use Charts after every few cards and point to the same concept on the live chart.")
            st.write("- Mark fuzzy words for Review, then come back after reading Glossary.")

    elif track == "Quiz":
        quiz_bank = {
            "Beginner basics": [
                {"question": "What should happen before a beginner paper-buys a momentum setup?", "options": ["Price confirms the entry trigger", "Price is moving fast", "Someone online likes it"], "answer": "Price confirms the entry trigger", "why": "The trigger is confirmation. Moving fast alone can lead to chasing."},
                {"question": "What does the stop loss define?", "options": ["Where the idea is wrong", "Where to add more shares", "Where news is best"], "answer": "Where the idea is wrong", "why": "The stop is the invalidation point and planned risk line."},
                {"question": "Why does RVOL matter?", "options": ["It shows unusual trading attention", "It guarantees profit", "It replaces the need for news"], "answer": "It shows unusual trading attention", "why": "High RVOL means today is more active than normal, but it never guarantees a win."},
                {"question": "What should you do if a stock is far above the planned entry?", "options": ["Avoid chasing and wait for a new setup", "Buy because it is strong", "Remove the stop loss"], "answer": "Avoid chasing and wait for a new setup", "why": "Chasing ruins risk/reward and makes the stop harder to respect."},
                {"question": "What belongs in a complete paper-trade plan?", "options": ["Entry, stop, target, size, and reason", "Only the stock symbol", "Only the biggest news headline"], "answer": "Entry, stop, target, size, and reason", "why": "A plan needs a reason and defined risk before the order is staged."},
            ],
            "Order ticket": [
                {"question": "Which order gives price control but may not fill?", "options": ["Limit order", "Market order", "Stop order"], "answer": "Limit order", "why": "A limit order controls worst acceptable price, but price may move away."},
                {"question": "What does quantity mean on a broker ticket?", "options": ["How many shares", "The stock's float", "The daily gain"], "answer": "How many shares", "why": "Quantity is share count. The app estimates paper shares from max risk and stop distance."},
                {"question": "Why can a market order be dangerous in a fast small-cap stock?", "options": ["It can fill at a worse price than expected", "It always waits for your exact price", "It removes all risk"], "answer": "It can fill at a worse price than expected", "why": "Fast candles and wide spreads can create slippage."},
                {"question": "What does time in force control?", "options": ["How long the order stays active", "The company's float", "The chart candle color"], "answer": "How long the order stays active", "why": "A forgotten open order can create surprises if you do not understand duration."},
                {"question": "What should happen before any real broker order is sent?", "options": ["Review the confirmation screen and broker rules", "Ignore the spread", "Skip the stop plan"], "answer": "Review the confirmation screen and broker rules", "why": "The app is a paper-trade planner. Real orders require careful broker review."},
            ],
            "Charts and risk": [
                {"question": "What does VWAP help you judge?", "options": ["Intraday control and price location", "The company's exact cash balance", "Whether profit is guaranteed"], "answer": "Intraday control and price location", "why": "VWAP is a useful intraday reference, but it is only one piece of context."},
                {"question": "What is usually healthier after a big push?", "options": ["A controlled pullback holding support", "A huge chase far above the trigger", "Removing the stop"], "answer": "A controlled pullback holding support", "why": "Better entries often come from controlled pullbacks or clean breakouts, not chasing."},
                {"question": "Why should target 1 be checked before entry?", "options": ["To confirm reward is worth the risk", "To avoid reading news", "To make the candle bigger"], "answer": "To confirm reward is worth the risk", "why": "If reward is too small compared with risk, the setup is not worth forcing."},
                {"question": "Why are offering and dilution headlines risky?", "options": ["They can add share supply and pressure price", "They always make stocks go up", "They remove all volatility"], "answer": "They can add share supply and pressure price", "why": "New share supply can hurt momentum, especially in small caps."},
                {"question": "What should you journal after a skipped setup?", "options": ["Why it was skipped and what happened next", "Nothing because no trade happened", "Only the highest price"], "answer": "Why it was skipped and what happened next", "why": "Skipped trades teach discipline and help you learn which filters worked."},
            ],
        }
        quiz_set = st.segmented_control("Quiz set", list(quiz_bank), default="Beginner basics", key="learn_quiz_set")
        quiz_set = str(quiz_set or "Beginner basics")
        questions = quiz_bank[quiz_set]
        quiz_slug = quiz_set.lower().replace(" ", "_").replace("/", "_")
        with st.container(border=True):
            st.markdown(f"**{quiz_set} quiz**")
            st.caption("Answer each question, then grade it. This is for learning, not certification.")
            answers: list[str] = []
            for index, question in enumerate(questions):
                choice = st.radio(
                    question["question"],
                    question["options"],
                    key=f"learn_quiz_{quiz_slug}_{index}",
                    horizontal=False,
                )
                answers.append(str(choice))
            if st.button("Grade quiz", type="primary", icon=":material/check_circle:"):
                score = sum(answer == question["answer"] for answer, question in zip(answers, questions))
                st.session_state.learn_quiz_score = score
                st.session_state.learn_quiz_graded = True
                st.session_state.learn_quiz_graded_set = quiz_set
            if st.button("Reset answers", icon=":material/restart_alt:"):
                st.session_state.learn_quiz_graded = False
                st.session_state.learn_quiz_score = 0
                st.rerun()

        if st.session_state.get("learn_quiz_graded") and st.session_state.get("learn_quiz_graded_set") == quiz_set:
            score = int(st.session_state.get("learn_quiz_score", 0))
            st.success(f"You scored {score}/{len(questions)}.")
            for index, question in enumerate(questions):
                selected = st.session_state.get(f"learn_quiz_{quiz_slug}_{index}")
                passed = selected == question["answer"]
                with st.container(border=True):
                    st.badge("Correct" if passed else "Review", color="green" if passed else "orange")
                    st.markdown(f"**{question['question']}**")
                    st.write(f"Your answer: {selected}")
                    st.write(f"Best answer: {question['answer']}")
                    st.caption(question["why"])

    elif track == "Practice":
        with st.container(border=True):
            st.markdown("**Paper-trade drill**")
            drill_ticker = normalize_user_symbol(st.text_input("Practice stock", value=st.session_state.get("selected_ticker", "NVDA")))
            analysis = analyze_ticker(drill_ticker, period="5d", interval="5m", prefer_live=True)
            render_plan_card(analysis)

        with st.container(border=True):
            st.markdown("**Before you mark this as tradable**")
            checks = [
                "I can explain the catalyst.",
                "Price is near the buy zone or waiting for the trigger.",
                "The stop is written down.",
                "Target 1 gives enough reward for the risk.",
                "I am paper trading and journaling the result.",
            ]
            completed = 0
            for index, check in enumerate(checks):
                if st.checkbox(check, key=f"learn_check_{index}"):
                    completed += 1
            st.progress(completed / len(checks))
            st.caption(f"{completed} of {len(checks)} practice checks complete.")

    elif track == "Glossary":
        terms = pd.DataFrame(
            [
                {"Term": "Paper trade", "Meaning": "A practice trade that records the plan without risking real money.", "Why it matters": "New traders can learn the process before using real capital."},
                {"Term": "Order ticket", "Meaning": "The broker screen where symbol, side, quantity, order type, and prices are entered.", "Why it matters": "Most costly mistakes happen when the ticket is rushed or misunderstood."},
                {"Term": "Approval checklist", "Meaning": "The Trade Desk review that must be completed before saving a paper order.", "Why it matters": "It slows beginners down before they accept risk, stale data, or a bad setup."},
                {"Term": "Market order", "Meaning": "An order that tries to fill right away at the available market price.", "Why it matters": "It can fill at a different price than expected in fast stocks."},
                {"Term": "Limit order", "Meaning": "An order that sets the worst price you are willing to accept.", "Why it matters": "It gives price control, but it may not fill."},
                {"Term": "Stop order", "Meaning": "An order that activates after a stop price is reached.", "Why it matters": "Some stop orders can become market orders after triggering."},
                {"Term": "Stop-limit order", "Meaning": "A stop order that becomes a limit order after the stop price is reached.", "Why it matters": "It controls price but can miss the fill if price moves too fast."},
                {"Term": "Bid", "Meaning": "The highest displayed price buyers are currently offering.", "Why it matters": "Sellers often transact near the bid."},
                {"Term": "Ask", "Meaning": "The lowest displayed price sellers are currently offering.", "Why it matters": "Buyers often transact near the ask."},
                {"Term": "Spread", "Meaning": "The gap between bid and ask.", "Why it matters": "Wide spreads make entries and exits more expensive and harder to control."},
                {"Term": "Time in force", "Meaning": "How long an order stays active, such as day-only or good-till-canceled.", "Why it matters": "A forgotten open order can create surprises."},
                {"Term": "IEX feed", "Meaning": "A market data feed from the Investors Exchange.", "Why it matters": "Alpaca's free stock candles can use IEX, which is useful but not the full consolidated market tape."},
                {"Term": "SIP feed", "Meaning": "A consolidated exchange data feed across major US markets.", "Why it matters": "It is closer to full professional real-time data, but it usually costs money because exchanges charge fees."},
                {"Term": "Delayed quote", "Meaning": "A price that may be behind the current market.", "Why it matters": "A delayed quote can make entries, stops, and targets look safer than they really are."},
                {"Term": "Data confidence", "Meaning": "The app's trust label based on source, quote age, fallback data, and price mismatch risk.", "Why it matters": "It tells beginners when to slow down and verify before using a setup."},
                {"Term": "Market pulse", "Meaning": "The scan-wide read of data trust, active setups, top stock, scan power, and risk flags.", "Why it matters": "It helps beginners decide whether to chart the leader, wait, verify data, or scan another batch."},
                {"Term": "Workflow cockpit", "Meaning": "The app's guided next-step panel for moving from scan to chart to plan to journal.", "Why it matters": "It keeps beginners from skipping verification and risk checks."},
                {"Term": "AI ladder", "Meaning": "The app's step-by-step paper-trade review: data, setup, entry, stop, and take profit.", "Why it matters": "It gives beginners an order to follow instead of reacting emotionally to candles."},
                {"Term": "Setup check", "Meaning": "A quick count of how many scanner rules are lining up.", "Why it matters": "A strong candle is not enough if the full setup is weak."},
                {"Term": "Data check", "Meaning": "The first ladder step that checks source, quote age, and confidence.", "Why it matters": "Bad or stale data can make a paper plan look cleaner than it really is."},
                {"Term": "Premarket", "Meaning": "Trading before the regular market open.", "Why it matters": "Moves can be fast, spreads can be wide, and volume can be thinner."},
                {"Term": "After-hours", "Meaning": "Trading after the regular market close.", "Why it matters": "News often drops after the bell, but fills can be less predictable."},
                {"Term": "Gapper", "Meaning": "A stock opening or trading far above the prior close.", "Why it matters": "It can reveal fresh demand, but late entries can fade fast."},
                {"Term": "Float", "Meaning": "Shares available for public trading.", "Why it matters": "Lower float can move faster because there is less supply."},
                {"Term": "RVOL", "Meaning": "Relative volume compared with normal trading volume.", "Why it matters": "High RVOL shows unusual attention today."},
                {"Term": "Liquidity", "Meaning": "How easy it is to buy or sell without moving price too much.", "Why it matters": "Low liquidity can make exits harder."},
                {"Term": "Slippage", "Meaning": "The difference between the price you expected and the price you actually get.", "Why it matters": "Fast stocks and market orders can slip badly."},
                {"Term": "VWAP", "Meaning": "Volume-weighted average price.", "Why it matters": "Many traders use it as an intraday control line."},
                {"Term": "Support", "Meaning": "A price area where buyers have recently defended the stock.", "Why it matters": "Pullbacks often need support to hold before a safe plan forms."},
                {"Term": "Resistance", "Meaning": "A price area where sellers have recently stopped the stock.", "Why it matters": "Breakouts usually need to clear resistance with volume."},
                {"Term": "Breakout", "Meaning": "Price pushes above a watched level with momentum.", "Why it matters": "The app's entry trigger is a breakout confirmation idea."},
                {"Term": "Pullback", "Meaning": "A controlled dip after a move up.", "Why it matters": "Better entries often come from controlled pullbacks, not chasing highs."},
                {"Term": "Consolidation", "Meaning": "Price pauses in a tighter range after moving.", "Why it matters": "A clean range can create a clearer trigger and stop."},
                {"Term": "Entry trigger", "Meaning": "The level that confirms buyers are stepping in.", "Why it matters": "It helps avoid buying only because price is moving."},
                {"Term": "Stop", "Meaning": "The level where the idea is invalid.", "Why it matters": "It defines risk before the trade."},
                {"Term": "Target", "Meaning": "A planned exit area for taking profit.", "Why it matters": "Targets make reward measurable before entry."},
                {"Term": "Trim", "Meaning": "Selling part of a position at a target while keeping some open.", "Why it matters": "It can lock in a partial result while still leaving room for a runner."},
                {"Term": "Runner", "Meaning": "The remaining shares kept after a partial exit.", "Why it matters": "A runner needs a written exit plan too."},
                {"Term": "R multiple", "Meaning": "Reward or loss measured against the planned risk.", "Why it matters": "It lets you compare trades fairly."},
                {"Term": "Halt", "Meaning": "A temporary pause in trading by an exchange.", "Why it matters": "Halts can reopen far above or below the last price."},
                {"Term": "Offering", "Meaning": "A company sells more shares to raise money.", "Why it matters": "Offerings can pressure price because supply increases."},
                {"Term": "Dilution", "Meaning": "Existing shares represent a smaller slice after new shares are issued.", "Why it matters": "Small-cap momentum can reverse quickly on dilution news."},
                {"Term": "Short interest", "Meaning": "Shares borrowed and sold by traders betting price will fall.", "Why it matters": "High short interest can add volatility, but it is not automatically bullish."},
                {"Term": "Easy to borrow", "Meaning": "A broker label showing shares may be available to short.", "Why it matters": "Borrow status can affect short-side trading and squeeze risk."},
                {"Term": "Margin account", "Meaning": "A brokerage account that can borrow from the broker under rules.", "Why it matters": "Margin can increase risk and trigger pattern day trader rules."},
                {"Term": "Cash account", "Meaning": "A brokerage account using settled cash instead of margin.", "Why it matters": "Cash accounts have settlement rules that can limit how often funds are reused."},
                {"Term": "Settlement", "Meaning": "The process where cash and shares officially exchange after a trade.", "Why it matters": "Using unsettled funds incorrectly can create broker restrictions."},
                {"Term": "Pattern day trader rule", "Meaning": "A broker/margin-account rule that can apply to frequent day trading.", "Why it matters": "Real traders must check broker rules before day trading with margin."},
            ]
        )
        order_terms = {"Order ticket", "Market order", "Limit order", "Stop order", "Stop-limit order", "Bid", "Ask", "Spread", "Time in force"}
        data_terms = {"IEX feed", "SIP feed", "Delayed quote", "Data confidence", "Data check"}
        workflow_terms = {"Paper trade", "Approval checklist", "Market pulse", "Workflow cockpit", "AI ladder", "Setup check"}
        scanner_terms = {"Premarket", "After-hours", "Gapper", "Float", "RVOL", "Liquidity", "Slippage"}
        chart_terms = {"VWAP", "Support", "Resistance", "Breakout", "Pullback", "Consolidation", "Entry trigger", "Stop", "Target", "Trim", "Runner", "R multiple"}
        news_terms = {"Halt", "Offering", "Dilution", "Short interest", "Easy to borrow"}
        account_terms = {"Margin account", "Cash account", "Settlement", "Pattern day trader rule"}

        def glossary_category(term: str) -> str:
            if term in order_terms:
                return "Orders"
            if term in data_terms:
                return "Data"
            if term in workflow_terms:
                return "Workflow"
            if term in scanner_terms:
                return "Scanner"
            if term in chart_terms:
                return "Charts"
            if term in news_terms:
                return "News"
            if term in account_terms:
                return "Accounts"
            return "Basics"

        terms.insert(0, "Category", terms["Term"].map(glossary_category))
        categories = ["All", "Basics", "Orders", "Data", "Workflow", "Scanner", "Charts", "News", "Accounts"]
        with st.container(border=True):
            st.markdown("**Glossary search**")
            cols = st.columns([1, 1.4], vertical_alignment="bottom")
            category = cols[0].segmented_control("Category", categories, default="All", key="learn_glossary_category")
            query = cols[1].text_input(
                "Search terms",
                value="",
                placeholder="Try stop, VWAP, spread, PDT, data, risk",
                key="learn_glossary_search",
            )
            filtered_terms = terms.copy()
            if category and category != "All":
                filtered_terms = filtered_terms[filtered_terms["Category"] == str(category)]
            query_text = str(query or "").strip().lower()
            if query_text:
                searchable = (
                    filtered_terms["Term"].astype(str)
                    + " "
                    + filtered_terms["Meaning"].astype(str)
                    + " "
                    + filtered_terms["Why it matters"].astype(str)
                ).str.lower()
                filtered_terms = filtered_terms[searchable.str.contains(query_text, regex=False, na=False)]

            focus_source = filtered_terms if not filtered_terms.empty else terms
            focus_index = datetime.now().timetuple().tm_yday % len(focus_source)
            focus = focus_source.iloc[focus_index]
            focus_cols = st.columns([.42, .58])
            with focus_cols[0]:
                st.metric("Terms shown", str(len(filtered_terms)), f"{len(terms)} total", border=True)
                st.badge(str(focus["Category"]), icon=":material/category:", color="blue")
            with focus_cols[1]:
                st.markdown(f"**Focus term: {focus['Term']}**")
                st.write(str(focus["Meaning"]))
                st.caption(str(focus["Why it matters"]))

            if filtered_terms.empty:
                render_html('<div class="msa-glossary-empty">No terms matched that search. Try a shorter word like stop, order, data, news, or risk.</div>')
            else:
                st.dataframe(
                    filtered_terms,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Category": st.column_config.TextColumn("Category", pinned=True),
                        "Term": st.column_config.TextColumn("Term"),
                        "Meaning": st.column_config.TextColumn("Plain-English meaning"),
                        "Why it matters": st.column_config.TextColumn("Why it matters"),
                    },
                )

    elif track == "iPad":
        cols = st.columns(2)
        with cols[0]:
            with st.container(border=True):
                st.markdown("**Use it like an iPad app**")
                st.write("1. Deploy or host the app so it has a web link.")
                st.write("2. Open the link in Safari on your iPad.")
                st.write("3. Tap Share.")
                st.write("4. Tap Add to Home Screen.")
                st.write("5. Open it from the icon like a normal app.")
        with cols[1]:
            with st.container(border=True):
                st.markdown("**True App Store app**")
                st.write("A real downloadable App Store app needs a mobile wrapper or rebuild, Apple Developer account, signing, review, and broker/data compliance checks.")
                st.write("The fastest no-cost path is the Home Screen web app. It still feels app-like once hosted.")


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon=":material/monitoring:", layout="wide")
    mode = str(st.session_state.get("display_mode", "Dark"))
    apply_style(mode)
    render_sidebar_brand()
    display_mode_control()
    pages = [
        st.Page(page_dashboard, title="Dashboard", icon=":material/dashboard:"),
        st.Page(page_daily_gameplan, title="Daily Gameplan", icon=":material/event_note:", url_path="Daily_Gameplan"),
        st.Page(page_live_tracker, title="Live Tracker", icon=":material/monitoring:", url_path="Live_Tracker"),
        st.Page(page_scanner, title="Scanner", icon=":material/search:", url_path="Scanner"),
        st.Page(page_market_scan, title="Market Scan", icon=":material/radar:", url_path="Market_Scan"),
        st.Page(page_charts, title="Charts", icon=":material/candlestick_chart:", url_path="Charts"),
        st.Page(page_ai_coach, title="AI Coach", icon=":material/psychology:", url_path="AI"),
        st.Page(page_watchlist, title="Watchlist", icon=":material/star:", url_path="Watchlist"),
        st.Page(page_trade_desk, title="Trade Desk", icon=":material/order_approve:", url_path="Trade_Desk"),
        st.Page(page_journal, title="Journal", icon=":material/edit_note:", url_path="Journal"),
        st.Page(page_backtester, title="Backtester", icon=":material/query_stats:", url_path="Backtester"),
        st.Page(page_learn, title="Learn", icon=":material/school:", url_path="Learn"),
    ]
    navigation = st.navigation(pages, position="sidebar")
    navigation.run()
    render_floating_companion()


if __name__ == "__main__":
    main()
