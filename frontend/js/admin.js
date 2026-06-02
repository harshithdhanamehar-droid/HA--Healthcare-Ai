/* ═══════════════════════════════════════════════════════════════
   HA! Healthcare AI — Admin Dashboard Logic
   ═══════════════════════════════════════════════════════════════ */

"use strict";

// ── Admin credentials (stored in localStorage after login) ────────
const ADMIN_PIN = "admin2024";       // change this to your preferred PIN
const ADMIN_KEY = "ha_admin_auth";

// ── State ─────────────────────────────────────────────────────────
let allUsers = [];
let allChats = [];
let userSearchTerm = "";
let chatSearchTerm = "";

// ── Boot ──────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  if (!isAdminAuthed()) {
    showLoginGate();
    return;
  }
  initDashboard();
});

// ── Admin Auth ────────────────────────────────────────────────────
function isAdminAuthed() {
  return sessionStorage.getItem(ADMIN_KEY) === "true";
}

function showLoginGate() {
  document.getElementById("admin-login-overlay").style.display = "flex";
  document.getElementById("admin-dashboard").style.display    = "none";
  document.getElementById("admin-pin").focus();
}

function hideDashboard() {
  document.getElementById("admin-login-overlay").style.display = "flex";
  document.getElementById("admin-dashboard").style.display    = "none";
}

function submitAdminLogin() {
  const pin = document.getElementById("admin-pin").value.trim();
  const errorEl = document.getElementById("login-error");

  if (pin === ADMIN_PIN) {
    sessionStorage.setItem(ADMIN_KEY, "true");
    document.getElementById("admin-login-overlay").style.display = "none";
    document.getElementById("admin-dashboard").style.display    = "flex";
    errorEl.textContent = "";
    initDashboard();
  } else {
    errorEl.textContent = "Incorrect PIN. Please try again.";
    document.getElementById("admin-pin").value = "";
    document.getElementById("admin-pin").focus();
  }
}

function handlePinKeydown(e) {
  if (e.key === "Enter") submitAdminLogin();
}

function adminLogout() {
  sessionStorage.removeItem(ADMIN_KEY);
  localStorage.removeItem("ha_logged_in");
  localStorage.removeItem("ha_name");
  localStorage.removeItem("ha_phone");
  localStorage.removeItem("ha_location");
  window.location.replace("index.html");
}

// ── Dashboard Init ────────────────────────────────────────────────
function initDashboard() {
  // Populate sidebar user info
  const name = localStorage.getItem("ha_name") || "Admin";
  const nameEl = document.getElementById("admin-user-name");
  const avatarEl = document.getElementById("admin-avatar");
  if (nameEl)   nameEl.textContent   = name;
  if (avatarEl) avatarEl.textContent = name.charAt(0).toUpperCase();

  loadAll();
}

// ── Load Everything ───────────────────────────────────────────────
async function loadAll() {
  setRefreshing(true);
  await Promise.all([loadStats(), loadUsers(), loadChats()]);
  setRefreshing(false);
}

function setRefreshing(on) {
  const btn = document.getElementById("btn-refresh");
  if (!btn) return;
  btn.disabled = on;
  btn.querySelector(".refresh-label").textContent = on ? "Refreshing…" : "Refresh";
}

// ── Stats ─────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const data = await apiGet("/admin/stats");
    animateCount("stat-total-users",  data.total_users  || 0);
    animateCount("stat-total-chats",  data.total_chats  || 0);
    animateCount("stat-active-users", data.active_users || 0);
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const step  = Math.max(1, Math.ceil(target / 30));
  const tick  = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current.toLocaleString();
    if (current >= target) clearInterval(tick);
  }, 30);
}

// ── Users ─────────────────────────────────────────────────────────
async function loadUsers() {
  setTableLoading("users-tbody", 5);
  try {
    const data = await apiGet("/admin/users");
    allUsers = data.users || [];
    document.getElementById("users-count").textContent = allUsers.length;
    renderUsers();
  } catch (err) {
    setTableError("users-tbody", 5, err.message);
  }
}

function renderUsers() {
  const term    = userSearchTerm.toLowerCase();
  const filtered = allUsers.filter(u =>
    u.phone.toLowerCase().includes(term) ||
    u.name.toLowerCase().includes(term)
  );

  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  document.getElementById("users-count").textContent = filtered.length;

  if (filtered.length === 0) {
    tbody.innerHTML = emptyRow(5, "No users found");
    return;
  }

  tbody.innerHTML = filtered.map(u => `
    <tr>
      <td>
        <div class="cell-name">
          <div class="cell-avatar">${u.name.charAt(0).toUpperCase()}</div>
          <span class="cell-name-text">${escHtml(u.name)}</span>
        </div>
      </td>
      <td><span class="badge-phone">${escHtml(u.phone)}</span></td>
      <td>${escHtml(u.location || "—")}</td>
      <td class="cell-date">${formatDate(u.created_at)}</td>
    </tr>
  `).join("");
}

function onUserSearch(e) {
  userSearchTerm = e.target.value.trim();
  renderUsers();
}

// ── Chats ─────────────────────────────────────────────────────────
async function loadChats() {
  setTableLoading("chats-tbody", 5);
  try {
    const data = await apiGet("/admin/chats");
    allChats = data.chats || [];
    document.getElementById("chats-count").textContent = allChats.length;
    renderChats();
  } catch (err) {
    setTableError("chats-tbody", 5, err.message);
  }
}

function renderChats() {
  const term     = chatSearchTerm.toLowerCase();
  const filtered = allChats.filter(c =>
    c.user_phone.toLowerCase().includes(term)
  );

  const tbody = document.getElementById("chats-tbody");
  if (!tbody) return;

  document.getElementById("chats-count").textContent = filtered.length;

  if (filtered.length === 0) {
    tbody.innerHTML = emptyRow(5, "No chats found");
    return;
  }

  tbody.innerHTML = filtered.map(c => `
    <tr>
      <td><span class="badge-phone">${escHtml(c.user_phone)}</span></td>
      <td><span class="cell-chat-id" title="${escHtml(c.chat_id)}">${escHtml(c.chat_id)}</span></td>
      <td><span class="badge-count">${c.message_count}</span></td>
      <td class="cell-message">${escHtml(c.first_message || "—")}</td>
      <td class="cell-date">${formatDate(c.created_at)}</td>
    </tr>
  `).join("");
}

function onChatSearch(e) {
  chatSearchTerm = e.target.value.trim();
  renderChats();
}

// ── CSV Export ────────────────────────────────────────────────────
function exportUsersCSV() {
  const headers = ["ID", "Name", "Phone", "Location", "Registration Date"];
  const rows = allUsers.map(u => [
    u.id,
    u.name,
    u.phone,
    u.location || "",
    new Date(u.created_at).toLocaleString("en-IN")
  ]);

  const csv = [headers, ...rows]
    .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\r\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `ha_users_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ── Helpers ───────────────────────────────────────────────────────
function setTableLoading(tbodyId, cols) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = `
    <tr>
      <td colspan="${cols}" class="table-state">
        <div class="loading-dots"><span></span><span></span><span></span></div>
        <p style="margin-top:10px">Loading…</p>
      </td>
    </tr>
  `;
}

function setTableError(tbodyId, cols, msg) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  tbody.innerHTML = `
    <tr>
      <td colspan="${cols}" class="table-state">
        <p style="color:var(--accent-red)">Error: ${escHtml(msg)}</p>
      </td>
    </tr>
  `;
}

function emptyRow(cols, label) {
  return `
    <tr>
      <td colspan="${cols}" class="table-state">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" display="block" style="margin:0 auto 10px">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <p>${label}</p>
      </td>
    </tr>
  `;
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDate(isoStr) {
  if (!isoStr) return "—";
  return new Date(isoStr).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric"
  });
}

// ── Mobile sidebar toggle ─────────────────────────────────────────
function toggleAdminSidebar() {
  document.getElementById("admin-sidebar").classList.toggle("open");
}

document.addEventListener("click", (e) => {
  const sidebar  = document.getElementById("admin-sidebar");
  const hamburger = document.querySelector(".hamburger-admin");
  if (
    sidebar &&
    sidebar.classList.contains("open") &&
    !sidebar.contains(e.target) &&
    !hamburger?.contains(e.target)
  ) {
    sidebar.classList.remove("open");
  }
});
