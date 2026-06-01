/* ═══════════════════════════════════════════════════════════════
   HA! — Login Logic
   ═══════════════════════════════════════════════════════════════ */

// ── API base URL — auto-detected by environment ───────────────────
const API_BASE = (
  window.location.protocol === "file:" ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
)
  ? "http://127.0.0.1:8000"
  : "https://ha-healthcare-ai.onrender.com";

async function login() {
  const name     = document.getElementById("name").value.trim();
  const phone    = document.getElementById("phone").value.trim();
  const location = document.getElementById("location").value.trim();

  const btnText  = document.getElementById("btn-text");
  const loader   = document.getElementById("loader");
  const errorMsg = document.getElementById("error-msg");

  errorMsg.textContent = "";

  // ── Validation ──────────────────────────────────────────────────
  const nameRegex     = /^[A-Za-z\s]{2,50}$/;
  const phoneRegex    = /^[6-9][0-9]{9}$/;
  const locationRegex = /^[A-Za-z\s,.-]{2,60}$/;

  if (!name) {
    errorMsg.textContent = "Please enter your full name.";
    document.getElementById("name").focus();
    return;
  }
  if (!nameRegex.test(name)) {
    errorMsg.textContent = "Name must contain letters only (2–50 characters).";
    return;
  }
  if (!phone) {
    errorMsg.textContent = "Please enter your mobile number.";
    document.getElementById("phone").focus();
    return;
  }
  if (!phoneRegex.test(phone)) {
    errorMsg.textContent = "Enter a valid 10-digit Indian mobile number.";
    return;
  }
  if (!location) {
    errorMsg.textContent = "Please enter your location.";
    document.getElementById("location").focus();
    return;
  }
  if (!locationRegex.test(location)) {
    errorMsg.textContent = "Location must contain letters only.";
    return;
  }

  // ── Show Loader ──────────────────────────────────────────────────
  btnText.style.display = "none";
  loader.style.display  = "block";

  try {
    // Register with backend
    await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, location }),
    });
  } catch (_) {
    // Backend offline — still allow login (offline-first)
  }

  // Save to localStorage
  localStorage.setItem("ha_logged_in", "true");
  localStorage.setItem("ha_name",      name);
  localStorage.setItem("ha_phone",     phone);
  localStorage.setItem("ha_location",  location);

  // Redirect
  setTimeout(() => {
    window.location.href = "chat.html";
  }, 800);
}

// Allow Enter key to submit
document.addEventListener("DOMContentLoaded", () => {
  ["name", "phone", "location"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter") login();
      });
    }
  });
});
