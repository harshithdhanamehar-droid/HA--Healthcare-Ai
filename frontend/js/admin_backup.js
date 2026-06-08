/* ═══════════════════════════════════════════════════════════════
   HA! Healthcare AI — Premium Admin Dashboard v2
   Self-contained: no dependency on app.js routing/auth guard
   ═══════════════════════════════════════════════════════════════ */
"use strict";

/* ── Config ───────────────────────────────────────────────────── */
const ADMIN_PIN       = "admin2024";
const ADMIN_KEY       = "ha_admin_v2";
const REFRESH_INTERVAL = 30000;          // ms
const PAGE_SIZE        = 10;

/* ── API Base ─────────────────────────────────────────────────── */
const API = "https://ha-healthcare-ai.onrender.com";

/* ── State ────────────────────────────────────────────────────── */
const S = {
  activeSection : "overview",
  users         : [],
  chats         : [],
  stats         : {},
  userPage      : 1,
  chatPage      : 1,
  userSearch    : "",
  chatSearch    : "",
  refreshTimer  : null,
  newUserCount  : 0,
  lastRefresh   : null,
  prevUserCount : null,
  settings: {
    pin             : ADMIN_PIN,
    refreshInterval : 30,
    theme           : "dark",
  }
};

/* ═══════════════════════════════════════════════════════════════
   BOOT
═══════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  if (sessionStorage.getItem(ADMIN_KEY) === "true") {
    showDashboard();
  } else {
    showLoginGate();
  }
});

/* ═══════════════════════════════════════════════════════════════
   AUTH
═══════════════════════════════════════════════════════════════ */
function showLoginGate() {
  document.getElementById("login-gate").style.display  = "flex";
  document.getElementById("admin-shell").style.display = "none";
  setTimeout(() => document.getElementById("admin-pin").focus(), 100);
}

function showDashboard() {
  document.getElementById("login-gate").style.display  = "none";
  document.getElementById("admin-shell").style.display = "flex";
  initDashboard();
}

function submitLogin() {
  const pin = (document.getElementById("admin-pin").value || "").trim();
  const err = document.getElementById("login-error");
  if (pin === S.settings.pin || pin === ADMIN_PIN) {
    sessionStorage.setItem(ADMIN_KEY, "true");
    err.textContent = "";
    showDashboard();
  } else {
    err.textContent = "Incorrect PIN. Please try again.";
    document.getElementById("admin-pin").value = "";
    document.getElementById("admin-pin").focus();
  }
}

function handlePinKey(e) { if (e.key === "Enter") submitLogin(); }

function adminLogout() {
  sessionStorage.removeItem(ADMIN_KEY);
  clearInterval(S.refreshTimer);
  window.location.href = "index.html";
}

/* ═══════════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════════ */
function initDashboard() {
  const name = localStorage.getItem("ha_name") || "Admin";
  setEl("sb-user-name", name);
  setEl("sb-avatar", name.charAt(0).toUpperCase());
  setEl("topbar-section", "Overview");

  navTo("overview");
  loadAll();

  // Auto-refresh
  clearInterval(S.refreshTimer);
  S.refreshTimer = setInterval(silentRefresh, REFRESH_INTERVAL);

  // Mobile sidebar close on overlay click
  document.addEventListener("click", (e) => {
    const sb = document.getElementById("admin-sidebar");
    const hb = document.querySelector(".hamburger-btn");
    if (sb && sb.classList.contains("open") && !sb.contains(e.target) && !hb?.contains(e.target)) {
      sb.classList.remove("open");
    }
  });
}

function toggleSidebar() {
  document.getElementById("admin-sidebar").classList.toggle("open");
}

/* ═══════════════════════════════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════════════════════════════ */
function navTo(section) {
  S.activeSection = section;

  // Toggle sections
  document.querySelectorAll(".adm-section").forEach(el => el.classList.remove("active"));
  const sec = document.getElementById("sec-" + section);
  if (sec) sec.classList.add("active");

  // Sidebar active state
  document.querySelectorAll(".sb-item").forEach(el => {
    el.classList.toggle("active", el.dataset.section === section);
  });

  // Topbar title map
  const titles = {
    overview : "Overview",
    users    : "Users",
    chats    : "Chat Sessions",
    analytics: "Analytics",
    settings : "Settings"
  };
  setEl("topbar-section", titles[section] || "Dashboard");

  // Close mobile sidebar
  document.getElementById("admin-sidebar")?.classList.remove("open");

  // Clear new user badge when visiting users
  if (section === "users") {
    S.newUserCount = 0;
    updateNotifBadge(0);
  }
}

/* ═══════════════════════════════════════════════════════════════
   DATA LOADING
═══════════════════════════════════════════════════════════════ */
async function loadAll() {
  setBtnRefreshing(true);
  await Promise.all([loadStats(), loadUsers(), loadChats()]);
  setBtnRefreshing(false);
  S.lastRefresh = new Date();
  updateLastRefreshedLabel();
}

async function silentRefresh() {
  await Promise.all([loadStats(), loadUsers(), loadChats()]);
  S.lastRefresh = new Date();
  updateLastRefreshedLabel();
}

function setBtnRefreshing(on) {
  const btn = document.getElementById("btn-refresh");
  if (!btn) return;
  btn.classList.toggle("spinning", on);
  btn.disabled = on;
}

function updateLastRefreshedLabel() {
  const el = document.getElementById("last-refreshed");
  if (el && S.lastRefresh) {
    el.textContent = "Updated " + S.lastRefresh.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
}

/* ── Stats ───────────────────────────────────────────────────── */
async function loadStats() {
  try {
    const d = await apiFetch("/admin/stats");
    S.stats = d;

    // Detect new users
    if (S.prevUserCount !== null && d.total_users > S.prevUserCount) {
      const diff = d.total_users - S.prevUserCount;
      S.newUserCount += diff;
      updateNotifBadge(S.newUserCount);
      if (S.prevUserCount !== null) toast("info", `${diff} new user${diff>1?"s":""} registered`);
    }
    S.prevUserCount = d.total_users;

    animateCount("sv-users",  d.total_users  || 0);
    animateCount("sv-chats",  d.total_chats  || 0);
    animateCount("sv-active", d.active_users || 0);
    animateCount("sv-today",  d.today_users  || 0);

    // Remove skeleton class
    document.querySelectorAll(".s-card.loading").forEach(c => c.classList.remove("loading"));
  } catch(e) { console.error("Stats error:", e); }
}

function updateNotifBadge(n) {
  const badge = document.getElementById("notif-badge");
  if (!badge) return;
  badge.textContent = n > 99 ? "99+" : n;
  badge.classList.toggle("show", n > 0);
}

/* ── Users ───────────────────────────────────────────────────── */
async function loadUsers() {
  skeletonTable("users-tbody", 4);
  try {
    const d = await apiFetch("/admin/users");
    S.users = d.users || [];
    S.userPage = 1;
    renderUsers();
  } catch(e) { errorTable("users-tbody", 4, e.message); }
}

function renderUsers() {
  const term = S.userSearch.toLowerCase();
  const filtered = S.users.filter(u =>
    u.name.toLowerCase().includes(term) ||
    u.phone.toLowerCase().includes(term) ||
    (u.location||"").toLowerCase().includes(term)
  );
  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  S.userPage = Math.min(S.userPage, pages);
  const slice = filtered.slice((S.userPage-1)*PAGE_SIZE, S.userPage*PAGE_SIZE);

  setEl("users-count", total);
  setEl("ov-users-count", S.users.length);

  const tbody = document.getElementById("users-tbody");
  if (!tbody) return;

  if (slice.length === 0) {
    tbody.innerHTML = emptyRowHtml(4, "No users found", "👤");
    renderPagination("users-pg", 0, 1, 1);
    return;
  }

  tbody.innerHTML = slice.map(u => `
    <tr>
      <td>
        <div class="c-name">
          <div class="c-av">${esc(u.name.charAt(0).toUpperCase())}</div>
          <span class="c-nm">${esc(u.name)}</span>
        </div>
      </td>
      <td><span class="badge phone">${esc(u.phone)}</span></td>
      <td>${esc(u.location||"—")}</td>
      <td class="c-date">${fmtDate(u.created_at)}</td>
      <td class="c-date">${fmtDate(u.created_at)}</td>
    </tr>
  `).join("");
  renderPagination("users-pg", total, S.userPage, pages);
}

function onUserSearch(e) { S.userSearch = e.target.value; S.userPage = 1; renderUsers(); }

/* ── Chats ───────────────────────────────────────────────────── */
async function loadChats() {
  skeletonTable("chats-tbody", 5);
  try {
    const d = await apiFetch("/admin/chats");
    S.chats = d.chats || [];
    S.chatPage = 1;
    renderChats();
  } catch(e) { errorTable("chats-tbody", 5, e.message); }
}

function renderChats() {
  const term = S.chatSearch.toLowerCase();
  const filtered = S.chats.filter(c =>
    c.user_phone.toLowerCase().includes(term) ||
    c.chat_id.toLowerCase().includes(term)
  );
  const total = filtered.length;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  S.chatPage = Math.min(S.chatPage, pages);
  const slice = filtered.slice((S.chatPage-1)*PAGE_SIZE, S.chatPage*PAGE_SIZE);

  setEl("chats-count", total);
  setEl("ov-chats-count", S.chats.length);

  const tbody = document.getElementById("chats-tbody");
  if (!tbody) return;

  if (slice.length === 0) {
    tbody.innerHTML = emptyRowHtml(5, "No chat sessions found", "💬");
    renderPagination("chats-pg", 0, 1, 1);
    return;
  }

  tbody.innerHTML = slice.map(c => `
    <tr>
      <td><span class="badge phone">${esc(c.user_phone)}</span></td>
      <td><span class="c-mono" title="${esc(c.chat_id)}">${esc(c.chat_id)}</span></td>
      <td><span class="badge count">${c.message_count}</span></td>
      <td class="c-msg">${esc(c.first_message||"—")}</td>
      <td class="c-date">${fmtDate(c.created_at)}</td>
      <td><button class="c-btn" onclick="viewChat('${esc(c.chat_id)}')">View</button></td>
    </tr>
  `).join("");
  renderPagination("chats-pg", total, S.chatPage, pages);
}

function onChatSearch(e) { S.chatSearch = e.target.value; S.chatPage = 1; renderChats(); }

/* ── Pagination ──────────────────────────────────────────────── */
function renderPagination(containerId, total, current, pages) {
  const el = document.getElementById(containerId);
  if (!el) return;

  const start = total === 0 ? 0 : (current-1)*PAGE_SIZE+1;
  const end   = Math.min(current*PAGE_SIZE, total);

  let btns = `<button class="pg-btn" onclick="changePage('${containerId}',${current-1})" ${current===1?"disabled":""}>‹</button>`;
  const range = getPgRange(current, pages);
  range.forEach(p => {
    if (p === "…") btns += `<span class="pg-btn" style="cursor:default;border:none">…</span>`;
    else btns += `<button class="pg-btn ${p===current?"active":""}" onclick="changePage('${containerId}',${p})">${p}</button>`;
  });
  btns += `<button class="pg-btn" onclick="changePage('${containerId}',${current+1})" ${current===pages?"disabled":""}>›</button>`;

  el.innerHTML = `<span>Showing ${start}–${end} of ${total}</span><div class="pg-btns">${btns}</div>`;
}

function getPgRange(cur, total) {
  if (total <= 7) return Array.from({length:total},(_,i)=>i+1);
  if (cur <= 4) return [1,2,3,4,5,"…",total];
  if (cur >= total-3) return [1,"…",total-4,total-3,total-2,total-1,total];
  return [1,"…",cur-1,cur,cur+1,"…",total];
}

function changePage(containerId, page) {
  if (containerId === "users-pg") { S.userPage = page; renderUsers(); }
  if (containerId === "chats-pg") { S.chatPage = page; renderChats(); }
}

/* ═══════════════════════════════════════════════════════════════
   ANALYTICS
═══════════════════════════════════════════════════════════════ */
function renderAnalytics() {
  renderBarChart("reg-chart", getRegistrationData());
  renderBarChart("chat-chart", getChatActivityData());
  renderTopUsers("top-users-list");
}

function getRegistrationData() {
  // Group users by day (last 7 days)
  const days = {};
  const now = new Date();
  for (let i=6; i>=0; i--) {
    const d = new Date(now); d.setDate(d.getDate()-i);
    const k = d.toLocaleDateString("en-IN",{month:"short",day:"numeric"});
    days[k] = 0;
  }
  S.users.forEach(u => {
    const k = new Date(u.created_at).toLocaleDateString("en-IN",{month:"short",day:"numeric"});
    if (k in days) days[k]++;
  });
  return Object.entries(days).map(([label,val])=>({label,val}));
}

function getChatActivityData() {
  const days = {};
  const now = new Date();
  for (let i=6; i>=0; i--) {
    const d = new Date(now); d.setDate(d.getDate()-i);
    const k = d.toLocaleDateString("en-IN",{month:"short",day:"numeric"});
    days[k] = 0;
  }
  S.chats.forEach(c => {
    const k = new Date(c.created_at).toLocaleDateString("en-IN",{month:"short",day:"numeric"});
    if (k in days) days[k]++;
  });
  return Object.entries(days).map(([label,val])=>({label,val}));
}

function renderBarChart(id, data) {
  const el = document.getElementById(id);
  if (!el) return;
  const max = Math.max(...data.map(d=>d.val), 1);
  el.innerHTML = data.map((d,i) => `
    <div class="bar-wrap">
      <div class="bar ${i%2===0?"c1":"c2"}" style="height:${Math.max(4,(d.val/max)*100)}%"
           data-val="${d.val}"></div>
      <span class="bar-lbl">${d.label}</span>
    </div>
  `).join("");
}

function renderTopUsers(id) {
  const el = document.getElementById(id);
  if (!el) return;
  // Count messages per user
  const counts = {};
  S.chats.forEach(c => {
    counts[c.user_phone] = (counts[c.user_phone]||0) + c.message_count;
  });
  const sorted = Object.entries(counts)
    .sort((a,b)=>b[1]-a[1]).slice(0,5);

  if (!sorted.length) { el.innerHTML = `<div class="empty-state"><p>No data yet</p></div>`; return; }

  el.innerHTML = sorted.map(([phone,msgs],i) => {
    const user = S.users.find(u=>u.phone===phone);
    const name = user?.name || phone;
    return `
      <div class="top-item">
        <span class="top-rank">#${i+1}</span>
        <div class="c-av sm">${name.charAt(0).toUpperCase()}</div>
        <div class="top-info">
          <div class="top-name">${esc(name)}</div>
          <div class="top-phone">${esc(phone)}</div>
        </div>
        <span class="top-msgs">${msgs} msgs</span>
      </div>
    `;
  }).join("");
}

/* ═══════════════════════════════════════════════════════════════
   CHAT DETAIL MODAL
═══════════════════════════════════════════════════════════════ */
async function viewChat(chatId) {
  openModal("chat-modal");
  const list = document.getElementById("chat-modal-msgs");
  list.innerHTML = `<div style="text-align:center;padding:40px;color:var(--t4)">Loading…</div>`;
  setEl("chat-modal-title", "Chat: " + chatId.slice(0,20));
  try {
    const d = await apiFetch(`/chat/session/${chatId}`);
    list.innerHTML = d.messages.map(m => `
      <div class="modal-msg ${m.role}">
        <div class="modal-msg-role">${m.role}</div>
        <div>${esc(m.message)}</div>
      </div>
    `).join("");
  } catch(e) {
    list.innerHTML = `<div style="color:var(--red);padding:20px">${esc(e.message)}</div>`;
  }
}

/* ═══════════════════════════════════════════════════════════════
   SETTINGS
═══════════════════════════════════════════════════════════════ */
function savePin() {
  const newPin = (document.getElementById("new-pin").value||"").trim();
  const confirm = (document.getElementById("confirm-pin").value||"").trim();
  if (!newPin) { toast("error","PIN cannot be empty"); return; }
  if (newPin !== confirm) { toast("error","PINs do not match"); return; }
  S.settings.pin = newPin;
  sessionStorage.setItem(ADMIN_KEY, "true");
  document.getElementById("new-pin").value = "";
  document.getElementById("confirm-pin").value = "";
  toast("success","Admin PIN updated successfully");
}

function saveRefreshInterval() {
  const val = parseInt(document.getElementById("refresh-interval").value)||30;
  S.settings.refreshInterval = val;
  clearInterval(S.refreshTimer);
  S.refreshTimer = setInterval(silentRefresh, val * 1000);
  toast("success","Auto-refresh set to " + val + " seconds");
}

function exportDatabase() {
  showConfirm("Export Database", "Export all users and chats as separate CSV files?", () => {
    exportUsersCSV();
    exportChatsCSV();
    toast("success", "Database exported as CSV files");
  });
}

function exportUsersCSV() {
  const headers = ["ID","Name","Phone","Location","Registration Date"];
  const rows = S.users.map(u => [u.id, u.name, u.phone, u.location||"", fmtDate(u.created_at)]);
  downloadCSV(headers, rows, `ha_users_${isoDate()}.csv`);
}

function exportChatsCSV() {
  const headers = ["User Phone","Chat ID","Messages","First Message","Created Date"];
  const rows = S.chats.map(c => [c.user_phone, c.chat_id, c.message_count, c.first_message||"", fmtDate(c.created_at)]);
  downloadCSV(headers, rows, `ha_chats_${isoDate()}.csv`);
}

function downloadCSV(headers, rows, filename) {
  const csv = [headers, ...rows]
    .map(row => row.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(","))
    .join("\r\n");
  const a = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(new Blob([csv], {type:"text/csv;charset=utf-8;"})),
    download: filename
  });
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}

/* ═══════════════════════════════════════════════════════════════
   MODALS
═══════════════════════════════════════════════════════════════ */
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

let _confirmCb = null;
function showConfirm(title, msg, onConfirm) {
  setEl("confirm-title", title);
  setEl("confirm-msg",   msg);
  _confirmCb = onConfirm;
  openModal("confirm-modal");
}
function confirmYes() { closeModal("confirm-modal"); if(_confirmCb) _confirmCb(); _confirmCb=null; }
function confirmNo()  { closeModal("confirm-modal"); _confirmCb = null; }

/* ═══════════════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════════════ */
function toast(type, msg, duration=3500) {
  const area = document.getElementById("toast-area");
  if (!area) return;
  const icons = { success:"✅", error:"❌", info:"ℹ️" };
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type]||"ℹ️"}</span><span>${esc(msg)}</span>`;
  area.appendChild(t);
  setTimeout(() => { t.classList.add("out"); setTimeout(()=>t.remove(), 300); }, duration);
}

/* ═══════════════════════════════════════════════════════════════
   API
═══════════════════════════════════════════════════════════════ */
async function apiFetch(endpoint) {
  const res = await fetch(API + endpoint);
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return res.json();
}

/* ═══════════════════════════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════════════════════════ */
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const step = Math.max(1, Math.ceil(target / 30));
  const t = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = current.toLocaleString();
    if (current >= target) clearInterval(t);
  }, 28);
}

function esc(str) {
  return String(str ?? "")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"});
}

function isoDate() { return new Date().toISOString().slice(0,10); }

function skeletonTable(tbodyId, cols) {
  const el = document.getElementById(tbodyId);
  if (!el) return;
  const skelRow = `<tr class="skel-row">${Array(cols).fill(`<td><div class="skel" style="width:${60+Math.random()*30|0}%"></div></td>`).join("")}</tr>`;
  el.innerHTML = [skelRow,skelRow,skelRow].join("");
}

function errorTable(tbodyId, cols, msg) {
  const el = document.getElementById(tbodyId);
  if (!el) return;
  el.innerHTML = `<tr><td colspan="${cols}" style="padding:40px;text-align:center;color:var(--red);font-size:13px">Error: ${esc(msg)}</td></tr>`;
}

function emptyRowHtml(cols, label, icon="📭") {
  return `<tr><td colspan="${cols}"><div class="empty-state"><div class="empty-icon">${icon}</div><h4>${label}</h4><p>No data to display</p></div></td></tr>`;
}

/* ═══════════════════════════════════════════════════════════════
   OVERVIEW MINI TABLES
═══════════════════════════════════════════════════════════════ */
function renderOverviewTables() {
  // Recent 5 users
  const recentUsers = [...S.users].slice(0, 5);
  const uTbody = document.getElementById("ov-users-tbody");
  if (uTbody) {
    uTbody.innerHTML = recentUsers.length === 0
      ? `<tr><td colspan="3"><div class="empty-state" style="padding:24px"><p>No users yet</p></div></td></tr>`
      : recentUsers.map(u => `
        <tr>
          <td><div class="c-name"><div class="c-av sm">${esc(u.name.charAt(0).toUpperCase())}</div><span class="c-nm" style="font-size:13px">${esc(u.name)}</span></div></td>
          <td><span class="badge phone" style="font-size:11px">${esc(u.phone)}</span></td>
          <td class="c-date">${fmtDate(u.created_at)}</td>
        </tr>`).join("");
  }

  // Recent 5 chats
  const recentChats = [...S.chats].slice(0, 5);
  const cTbody = document.getElementById("ov-chats-tbody");
  if (cTbody) {
    cTbody.innerHTML = recentChats.length === 0
      ? `<tr><td colspan="3"><div class="empty-state" style="padding:24px"><p>No chats yet</p></div></td></tr>`
      : recentChats.map(c => `
        <tr>
          <td><span class="badge phone" style="font-size:11px">${esc(c.user_phone)}</span></td>
          <td><span class="badge count">${c.message_count}</span></td>
          <td class="c-date">${fmtDate(c.created_at)}</td>
        </tr>`).join("");
  }
}

/* ── Analytics derived metrics ───────────────────────────────── */
function renderAnalyticsMetrics() {
  const totalMsgs = S.chats.reduce((s,c)=>s+c.message_count,0);
  const avgMsgs   = S.chats.length ? (totalMsgs/S.chats.length).toFixed(1) : "0";
  const avgChats  = S.users.length ? (S.chats.length/S.users.length).toFixed(1) : "0";
  setEl("av-avg-msgs",   avgMsgs);
  setEl("av-chats-user", avgChats);
}

// Trigger analytics + overview render when section becomes visible
const _origNavTo = navTo;
window.navTo = function(section) {
  _origNavTo(section);
  if (section === "analytics") { renderAnalytics(); renderAnalyticsMetrics(); }
  if (section === "overview")  { renderOverviewTables(); }
};

// Also render after data loads
const _origLoadAll = loadAll;
window.loadAll = async function() {
  setBtnRefreshing(true);
  await Promise.all([loadStats(), loadUsers(), loadChats()]);
  setBtnRefreshing(false);
  S.lastRefresh = new Date();
  updateLastRefreshedLabel();
  renderOverviewTables();
  if (S.activeSection === "analytics") { renderAnalytics(); renderAnalyticsMetrics(); }
};
