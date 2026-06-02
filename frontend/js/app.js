/* ═══════════════════════════════════════════════════════════════
   HA! — Shared App Utilities
   Rules:
   - NEVER inject sidebar, nav, or layout HTML
   - ONLY read/write existing DOM elements by ID
   - ALL layout exists statically in each page's HTML file
   ═══════════════════════════════════════════════════════════════ */

"use strict";

// ── API base URL — auto-detected by environment ───────────────────
// file:// or localhost  →  local backend at 127.0.0.1:8000
// Vercel / any HTTPS   →  production Render backend
const API_BASE = (
  window.location.protocol === "file:" ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
)
  ? "http://127.0.0.1:8000"
  : "https://ha-healthcare-ai.onrender.com";

// ── Auth Guard ────────────────────────────────────────────────────
// Runs immediately. Redirects to login if not authenticated.
// Public pages (index.html) are exempt.
(function authGuard() {
  const page      = window.location.pathname.split("/").pop();
  const isPublic  = page === "index.html" || page === "" || page === "/" || page === "admin.html";
  const loggedIn  = localStorage.getItem("ha_logged_in") === "true";

  if (!loggedIn && !isPublic) {
    window.location.replace("index.html");
  }
}());

// ── Populate user info into existing DOM elements ─────────────────
// Writes name/location/avatar into elements that already exist in HTML.
// Does NOT create or inject any new elements.
document.addEventListener("DOMContentLoaded", () => {
  const name     = localStorage.getItem("ha_name")     || "Patient";
  const location = localStorage.getItem("ha_location") || "—";

  const nameEl     = document.getElementById("display-name");
  const locationEl = document.getElementById("display-location");
  const avatarEl   = document.getElementById("user-avatar-sidebar");

  if (nameEl)     nameEl.textContent   = name;
  if (locationEl) locationEl.textContent = location;
  if (avatarEl)   avatarEl.textContent = name.charAt(0).toUpperCase();
});

// ── Logout ────────────────────────────────────────────────────────
function logout() {
  localStorage.removeItem("ha_logged_in");
  localStorage.removeItem("ha_name");
  localStorage.removeItem("ha_phone");
  localStorage.removeItem("ha_location");
  window.location.replace("index.html");
}

// ── Sidebar toggle (mobile only) ──────────────────────────────────
// Adds/removes .open class on the existing #sidebar element.
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.toggle("open");
}

// Close sidebar when tapping outside it on mobile
document.addEventListener("click", (e) => {
  const sidebar   = document.getElementById("sidebar");
  const hamburger = document.querySelector(".hamburger");
  if (
    sidebar &&
    sidebar.classList.contains("open") &&
    !sidebar.contains(e.target) &&
    e.target !== hamburger &&
    !hamburger?.contains(e.target)
  ) {
    sidebar.classList.remove("open");
  }
});

// ── API helpers ───────────────────────────────────────────────────
async function apiPost(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiGet(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiDelete(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Date / time formatters ────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function formatTime(isoStr) {
  if (!isoStr) return "";
  return new Date(isoStr).toLocaleTimeString("en-IN", {
    hour: "2-digit", minute: "2-digit",
  });
}
