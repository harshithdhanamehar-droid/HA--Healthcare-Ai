/* ═══════════════════════════════════════════════════════════════
   HA! — Shared App Utilities
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = "https://ha-healthcare-ai.onrender.com";

// ── Auth Guard ────────────────────────────────────────────────────
(function authGuard() {
  const publicPages = ["index.html", "/", ""];
  const currentPage = window.location.pathname.split("/").pop();
  const isLoggedIn = localStorage.getItem("ha_logged_in") === "true";

  if (!isLoggedIn && !publicPages.includes(currentPage)) {
    window.location.href = "index.html";
  }
})();

// ── Load User Info ────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const name     = localStorage.getItem("ha_name") || "Patient";
  const location = localStorage.getItem("ha_location") || "—";

  const nameEl     = document.getElementById("display-name");
  const locationEl = document.getElementById("display-location");
  const avatarEl   = document.getElementById("user-avatar-sidebar");

  if (nameEl)     nameEl.textContent     = name;
  if (locationEl) locationEl.textContent = location;
  if (avatarEl)   avatarEl.textContent   = name.charAt(0).toUpperCase();
});

// ── Logout ────────────────────────────────────────────────────────
function logout() {
  localStorage.removeItem("ha_logged_in");
  localStorage.removeItem("ha_name");
  localStorage.removeItem("ha_phone");
  localStorage.removeItem("ha_location");
  window.location.href = "index.html";
}

// ── Sidebar Toggle (mobile) ───────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.toggle("open");
}

// Close sidebar when clicking outside on mobile
document.addEventListener("click", (e) => {
  const sidebar = document.getElementById("sidebar");
  const hamburger = document.querySelector(".hamburger");
  if (
    sidebar &&
    sidebar.classList.contains("open") &&
    !sidebar.contains(e.target) &&
    e.target !== hamburger
  ) {
    sidebar.classList.remove("open");
  }
});

// ── API Helper ────────────────────────────────────────────────────
async function apiPost(endpoint, body) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function apiDelete(endpoint) {
  const response = await fetch(`${API_BASE}${endpoint}`, { method: "DELETE" });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// ── Format Date ───────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function formatTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}
