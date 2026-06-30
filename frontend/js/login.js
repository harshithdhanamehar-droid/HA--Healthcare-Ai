/* ═══════════════════════════════════════════════════════════════
   HA! — Login Logic  (rewritten)
   Flow:
     Patient:  email + password  → login
               email (no pw)     → send OTP  → verify OTP → login
     Both:     if needs_profile  → profile modal → chat.html
   ═══════════════════════════════════════════════════════════════ */
"use strict";

// ── API base ──────────────────────────────────────────────────────
const API_BASE = (
  window.location.protocol === "file:" ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
)
  ? "http://127.0.0.1:8000"
  : "https://ha-healthcare-ai.onrender.com";

// ── State ─────────────────────────────────────────────────────────
let _pendingEmail   = "";   // email used when OTP was sent
let _pendingUserId  = "";   // filled after OTP verify, used for profile setup
let _googleClientId = "";
let _googleReady    = false;

// ── DOM ready ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  console.log("=== LOGIN PAGE INITIALIZED ===");
  
  // Tab switching
  document.querySelectorAll(".auth-tab").forEach(tab => {
    tab.addEventListener("click", () => switchAuthTab(tab.dataset.tab));
  });

  // Enter key bindings — credentials step
  ["userEmail", "userPassword"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("keydown", e => { 
        if (e.key === "Enter") {
          console.log(`Enter pressed on ${id}`);
          handlePatientLogin();
        }
      });
    }
  });
  const otpInput = document.getElementById("otpCode");
  if (otpInput) {
    otpInput.addEventListener("keydown", e => { 
      if (e.key === "Enter") {
        console.log("Enter pressed on otpCode");
        verifyPatientOtp();
      }
    });
  }

  // Doctor + admin Enter bindings
  ["doctorEmail", "doctorPassword"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("keydown", e => { if (e.key === "Enter") doctorLogin(); });
  });
  const adminPin = document.getElementById("adminPin");
  if (adminPin) adminPin.addEventListener("keydown", e => { if (e.key === "Enter") adminLogin(); });

  // Google OAuth — check backend configuration first
  const googleBtn = document.getElementById("googleLoginBtn");
  if (googleBtn) {
    googleBtn.addEventListener("click", handleGoogleLogin);
    initGoogleLogin();
  }
});

// ── Tab switching ─────────────────────────────────────────────────
function switchAuthTab(tabName) {
  document.querySelectorAll(".auth-tab").forEach(t => t.classList.remove("active"));
  document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");

  document.querySelectorAll(".auth-method").forEach(f => {
    f.classList.remove("active");
    f.style.display = "none";
  });
  const form = document.getElementById(`${tabName}Form`);
  if (form) { form.classList.add("active"); form.style.display = ""; }

  // Clear all errors
  ["error-msg","otp-error-msg","doctor-error-msg","doctor-otp-error-msg","admin-error-msg"]
    .forEach(id => { const el = document.getElementById(id); if (el) el.textContent = ""; });
}

// ── Helpers ───────────────────────────────────────────────────────
function setError(id, msg, color = "var(--accent-red, #ef4444)") {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.style.color = color; }
}
function clearError(id) { setError(id, ""); }

function togglePasswordVisibility(inputId) {
  const el = document.getElementById(inputId);
  if (el) el.type = el.type === "password" ? "text" : "password";
}

function setBtnLoading(btnId, textId, loaderId, loading) {
  const btn  = document.getElementById(btnId);
  const text = document.getElementById(textId);
  const spin = document.getElementById(loaderId);
  if (btn)  btn.disabled = loading;
  if (text) text.style.display = loading ? "none" : "";
  if (spin) spin.style.display = loading ? "inline-block" : "none";
}

function saveSession(data) {
  localStorage.setItem("ha_logged_in",    "true");
  localStorage.setItem("ha_user_id",      data.user_id  || "");
  localStorage.setItem("ha_email",        data.email    || "");
  localStorage.setItem("ha_name",         data.name     || "");
  localStorage.setItem("ha_phone",        data.phone    || "");
  localStorage.setItem("ha_location",     data.location || "");
  localStorage.setItem("ha_role",         data.role     || "user");
  if (data.token) localStorage.setItem("ha_auth_token", data.token);
}

async function apiPost(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const raw = await res.text();
  const json = raw ? JSON.parse(raw) : {};
  if (!res.ok) {
    const err = new Error(json.detail || json.message || `HTTP ${res.status}`);
    err.status = res.status;
    err.body = json;
    err.rawBody = raw;
    throw err;
  }
  return json;
}

function apiErrorMessage(err, fallback = "Request failed. Please try again.") {
  if (err?.body?.detail) return err.body.detail;
  if (err?.body?.message) return err.body.message;
  if (err?.message) return err.message;
  return fallback;
}

// ── After successful login: route to profile setup or chat ────────
function afterLogin(data) {
  saveSession(data);

  if (data.needs_profile) {
    // Store pending user id for profile submit
    _pendingUserId = data.user_id;
    // Pre-fill what we know
    const nameEl = document.getElementById("profile-name");
    if (nameEl && data.name) nameEl.value = data.name;
    // Show modal
    const modal = document.getElementById("profile-modal");
    if (modal) modal.style.display = "flex";
  } else {
    window.location.href = "chat.html";
  }
}

// ── OTP Countdown Timer ───────────────────────────────────────────
let _otpCountdownTimer = null;

function startOtpCountdown() {
  let seconds = 60;
  const resendBtn = document.getElementById("resendOtpBtn");
  const countdown = document.getElementById("otp-countdown");
  if (resendBtn) resendBtn.disabled = true;
  if (countdown) countdown.style.display = "";

  clearInterval(_otpCountdownTimer);
  _otpCountdownTimer = setInterval(() => {
    seconds--;
    if (countdown) countdown.textContent = `Resend OTP in ${seconds}s`;
    if (seconds <= 0) {
      clearInterval(_otpCountdownTimer);
      if (resendBtn) resendBtn.disabled = false;
      if (countdown) countdown.style.display = "none";
    }
  }, 1000);
}

function stopOtpCountdown() {
  clearInterval(_otpCountdownTimer);
  const resendBtn = document.getElementById("resendOtpBtn");
  const countdown = document.getElementById("otp-countdown");
  if (resendBtn) resendBtn.disabled = false;
  if (countdown) countdown.style.display = "none";
}

// ── Resend OTP ────────────────────────────────────────────────────
async function resendPatientOtp() {
  clearError("otp-error-msg");
  console.log("=== RESEND OTP START ===");
  console.log("_pendingEmail:", _pendingEmail);
  
  if (!_pendingEmail) { 
    console.log("No _pendingEmail - showing error");
    setError("otp-error-msg", "No email to resend OTP to."); 
    return; 
  }

  const resendBtn = document.getElementById("resendOtpBtn");
  if (resendBtn) resendBtn.disabled = true;

  try {
    console.log("Calling /auth/user/otp/resend for:", _pendingEmail);
    const data = await apiPost("/auth/user/otp/resend", { email: _pendingEmail, purpose: "login" });
    if (data.success === false) {
      setError("otp-error-msg", data.message || "Failed to resend OTP.");
      return;
    }

    // Clear old OTP input
    const otpInput = document.getElementById("otpCode");
    if (otpInput) otpInput.value = "";
    
    console.log("OTP resent successfully");
    setError("otp-error-msg", "New OTP sent to your email.", "var(--accent-green, #10b981)");

    // Restart countdown
    startOtpCountdown();
  } catch (err) {
    console.error("Resend OTP error:", err.message);
    setError("otp-error-msg", err.message || "Failed to resend OTP.");
  } finally {
    if (resendBtn) resendBtn.disabled = false;
  }
}

// ── Google Login ──────────────────────────────────────────────────
async function initGoogleLogin() {
  const googleBtn = document.getElementById("googleLoginBtn");
  if (!googleBtn) return;

  googleBtn.disabled = true;
  googleBtn.title = "Checking Google login...";

  try {
    const res = await fetch(`${API_BASE}/auth/google/status`);
    const data = await res.json().catch(() => ({}));
    console.log("Google OAuth status:", { status: res.status, body: data });

    if (!res.ok || !data.configured || !data.client_id) {
      googleBtn.disabled = true;
      googleBtn.title = "Google login is not configured.";
      return;
    }

    // Google is configured — initialize Google Identity Services
    _googleClientId = data.client_id;
    googleBtn.disabled = false;
    googleBtn.title = "Continue with Google";
    initGoogleIdentity();
  } catch (err) {
    console.warn("Google OAuth status check failed:", err);
    googleBtn.disabled = true;
    googleBtn.title = "Google login is unavailable.";
  }
}

function initGoogleIdentity() {
  if (_googleReady) return true;
  if (!_googleClientId) return false;
  if (typeof google === "undefined" || !google.accounts?.id) return false;

  google.accounts.id.initialize({
    client_id: _googleClientId,
    callback: handleGoogleCredential,
    auto_select: false,
    use_fedcm_for_prompt: false,
  });
  _googleReady = true;
  return true;
}

async function handleGoogleLogin() {
  clearError("error-msg");
  const googleBtn = document.getElementById("googleLoginBtn");

  if (!_googleClientId) {
    setError("error-msg", "Google login is not configured. Please use email/OTP login.");
    return;
  }

  if (!initGoogleIdentity()) {
    setError("error-msg", "Google Sign-In is still loading. Please try again.");
    return;
  }

  if (googleBtn) googleBtn.disabled = true;
  google.accounts.id.prompt();
  setTimeout(() => { if (googleBtn) googleBtn.disabled = false; }, 1000);
}

// ── Google credential callback ────────────────────────────────────
async function handleGoogleCredential(response) {
  clearError("error-msg");
  try {
    const data = await apiPost("/auth/google/login", {
      token: response.credential,
    });
    console.log("Google login backend response:", data);
    afterLogin(data);
  } catch (err) {
    setError("error-msg", "Google sign-in failed: " + apiErrorMessage(err));
  }
}


async function handlePatientLogin() {
  const email    = (document.getElementById("userEmail")?.value    || "").trim();
  const password = (document.getElementById("userPassword")?.value || "").trim();
  clearError("error-msg");

  console.log("=== PATIENT LOGIN START ===");
  console.log("Email:", email);
  console.log("Has password:", !!password);
  console.log("Has _pendingEmail:", !!_pendingEmail);

  if (!email || !email.includes("@")) {
    setError("error-msg", "Please enter a valid email address.");
    document.getElementById("userEmail")?.focus();
    return;
  }

  setBtnLoading("continueBtn", "btn-text", "loader", true);

  try {
    if (password) {
      // ── Password login ────────────────────────────────────────
      console.log("Attempting password login");
      const data = await apiPost("/auth/user/login", { email, password });
      setBtnLoading("continueBtn", "btn-text", "loader", false);
      afterLogin(data);
    } else {
      // ── OTP login — send OTP ──────────────────────────────────
      console.log("No password - requesting OTP");
      const data = await apiPost("/auth/user/otp/request", { email, purpose: "login" });
      setBtnLoading("continueBtn", "btn-text", "loader", false);

      if (data.success === false) {
        setError("error-msg", data.message || "Failed to send OTP. Check email or try again.");
        return;
      }

      _pendingEmail = email;
      console.log("OTP requested, _pendingEmail set to:", email);

      // Show OTP step
      document.getElementById("step-credentials").style.display = "none";
      document.getElementById("step-otp").style.display = "";
      const sentEl = document.getElementById("otp-sent-email");
      if (sentEl) sentEl.textContent = email;
      document.getElementById("otpCode")?.focus();

      // Start countdown timer for resend
      startOtpCountdown();

      // Dev mode: show OTP inline
      if (data.dev_otp) {
        setError("otp-error-msg", `[Dev] OTP: ${data.dev_otp}`, "var(--accent, #00d4aa)");
      }
    }
  } catch (err) {
    setBtnLoading("continueBtn", "btn-text", "loader", false);
    console.error("handlePatientLogin error:", err.message);
    setError("error-msg", err.message);
  }
}

// ── Patient — verify OTP ──────────────────────────────────────────
async function verifyPatientOtp() {
  const otp = (document.getElementById("otpCode")?.value || "").trim();
  const email = _pendingEmail || (document.getElementById("userEmail")?.value || "").trim();
  clearError("otp-error-msg");

  console.log("=== VERIFY OTP START ===");
  console.log("_pendingEmail:", _pendingEmail);
  console.log("email input value:", document.getElementById("userEmail")?.value);
  console.log("final email:", email);

  if (!email) {
    setError("otp-error-msg", "Email session expired. Please request a new OTP.");
    resetToCredentials();
    return;
  }

  if (!otp || otp.length !== 6) {
    setError("otp-error-msg", "Enter the 6-digit OTP from your email.");
    return;
  }

  const otpLoader = document.getElementById("otp-loader");
  const otpBtn    = otpLoader?.closest("button");
  if (otpBtn)    otpBtn.disabled = true;
  if (otpLoader) otpLoader.style.display = "inline-block";

  try {
    const payload = { email, otp_code: otp };
    console.log("=== OTP VERIFY REQUEST ===");
    console.log("Payload:", payload);
    console.log("Endpoint:", `${API_BASE}/auth/user/otp/verify`);

    const res = await fetch(`${API_BASE}/auth/user/otp/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const rawBody = await res.text();
    const data = rawBody ? JSON.parse(rawBody) : {};

    console.log("=== OTP VERIFY RESPONSE ===");
    console.log("Status:", res.status);
    console.log("OK:", res.ok);
    console.log("Raw body:", rawBody);
    console.log("Parsed data:", data);

    if (!res.ok) {
      console.log("Response NOT OK - throwing error");
      throw Object.assign(
        new Error(data.detail || data.message || `OTP verification failed (HTTP ${res.status})`),
        { status: res.status, body: data, rawBody }
      );
    }

    if (otpBtn)    otpBtn.disabled = false;
    if (otpLoader) otpLoader.style.display = "none";

    // CLEAR _pendingEmail after successful verification to prevent reuse
    _pendingEmail = "";
    // Clear email and OTP fields for security
    const emailField = document.getElementById("userEmail");
    const otpField = document.getElementById("otpCode");
    if (emailField) emailField.value = "";
    if (otpField) otpField.value = "";
    
    stopOtpCountdown();
    console.log("OTP verification succeeded - calling afterLogin");
    afterLogin(data);
  } catch (err) {
    console.log("=== OTP VERIFY CATCH BLOCK ===");
    console.log("Error message:", err.message);
    console.log("Error status:", err.status);
    console.log("Error response:", err.body);
    console.log("NOT calling any OTP request function from here");
    
    if (otpBtn)    otpBtn.disabled = false;
    if (otpLoader) otpLoader.style.display = "none";
    console.error("Patient OTP verify failed:", {
      status: err.status || null,
      response: err.rawBody || err.body || err.message,
    });
    setError("otp-error-msg", apiErrorMessage(err, "Invalid or expired OTP. Please request a new one."));
    console.log("=== VERIFY OTP END (ERROR) ===");
  }
}

// ── Patient — back to credentials step ───────────────────────────
function resetToCredentials() {
  document.getElementById("step-credentials").style.display = "";
  document.getElementById("step-otp").style.display = "none";
  clearError("error-msg");
  clearError("otp-error-msg");
  if (document.getElementById("otpCode")) document.getElementById("otpCode").value = "";
  stopOtpCountdown();
}

// ═══════════════════════════════════════════════════════════════
// PROFILE SETUP MODAL
// ═══════════════════════════════════════════════════════════════
async function submitProfileSetup() {
  const name     = (document.getElementById("profile-name")?.value     || "").trim();
  const phone    = (document.getElementById("profile-phone")?.value    || "").trim();
  const location = (document.getElementById("profile-location")?.value || "").trim();
  clearError("profile-error");

  if (!name) { setError("profile-error", "Please enter your name."); return; }
  if (!phone || !/^[6-9][0-9]{9}$/.test(phone)) {
    setError("profile-error", "Enter a valid 10-digit Indian mobile number.");
    return;
  }
  if (!location) { setError("profile-error", "Please enter your city / location."); return; }

  const btnText = document.getElementById("profile-btn-text");
  const loader  = document.getElementById("profile-loader");
  if (btnText) btnText.style.display = "none";
  if (loader)  loader.style.display  = "inline-block";
  const saveBtn = loader?.closest("button");
  if (saveBtn) saveBtn.disabled = true;

  try {
    await apiPost("/auth/user/profile-setup", {
      user_id: _pendingUserId,
      name, phone, location,
    });

    // Update localStorage with new profile
    localStorage.setItem("ha_name",     name);
    localStorage.setItem("ha_phone",    phone);
    localStorage.setItem("ha_location", location);

    window.location.href = "chat.html";
  } catch (err) {
    if (btnText) btnText.style.display = "";
    if (loader)  loader.style.display  = "none";
    if (saveBtn) saveBtn.disabled = false;
    setError("profile-error", err.message);
  }
}

// ═══════════════════════════════════════════════════════════════
// DOCTOR LOGIN
// ═══════════════════════════════════════════════════════════════
async function doctorLogin() {
  const email    = (document.getElementById("doctorEmail")?.value    || "").trim();
  const password = (document.getElementById("doctorPassword")?.value || "");
  const errEl    = document.getElementById("doctor-error-msg");
  if (errEl) errEl.textContent = "";

  if (!email)    { if (errEl) errEl.textContent = "Email required.";    return; }
  if (!password) { if (errEl) errEl.textContent = "Password required."; return; }

  const btn  = document.querySelector("#doctorForm .login-btn");
  const text = document.querySelector("#doctorForm .doctor-btn-text");
  const spin = document.querySelector("#doctorForm .doctor-loader");
  if (btn)  btn.disabled = true;
  if (text) text.style.display = "none";
  if (spin) spin.style.display = "inline-block";

  try {
    const res = await fetch(`${API_BASE}/auth/doctor/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json().catch(() => ({}));

    if (res.ok) {
      localStorage.setItem("ha_logged_in",    "true");
      localStorage.setItem("ha_role",         "doctor");
      localStorage.setItem("ha_email",        email);
      localStorage.setItem("ha_auth_token",   data.token || "");
      localStorage.setItem("ha_user_id",      data.user_id || "");
      setTimeout(() => { window.location.href = "chat.html"; }, 600);
    } else {
      if (errEl) errEl.textContent = data.detail || "Invalid credentials.";
    }
  } catch {
    if (errEl) errEl.textContent = "Network error. Please try again.";
  } finally {
    if (btn)  btn.disabled = false;
    if (text) text.style.display = "";
    if (spin) spin.style.display = "none";
  }
}

// ── Doctor OTP ────────────────────────────────────────────────────
function showDoctorOtpForm() {
  const sec = document.getElementById("doctorOtpSection");
  if (sec) sec.style.display = "block";
  document.getElementById("doctorOtpEmail")?.focus();
}

async function requestDoctorOtp() {
  const email = (document.getElementById("doctorOtpEmail")?.value || "").trim();
  const errEl = document.getElementById("doctor-otp-error-msg");
  if (errEl) errEl.textContent = "";
  if (!email) { if (errEl) errEl.textContent = "Email required."; return; }

  const btn = document.getElementById("doctorRequestOtpBtn");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/auth/user/otp/request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, purpose: "login" }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success !== false) {
      document.getElementById("doctorOtpCodeGroup").style.display = "block";
      document.getElementById("doctorRequestOtpBtn").style.display = "none";
      document.getElementById("doctorVerifyOtpBtn").style.display  = "block";
      document.getElementById("doctorOtp")?.focus();
      if (errEl) { errEl.textContent = `OTP sent to ${email}.`; errEl.style.color = "var(--accent)"; }
      if (data.dev_otp && errEl) { errEl.textContent += `  [Dev OTP: ${data.dev_otp}]`; }
    } else {
      if (errEl) errEl.textContent = data.detail || data.message || "Failed to send OTP.";
    }
  } catch {
    if (errEl) errEl.textContent = "Network error.";
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function verifyDoctorOtp() {
  const email = (document.getElementById("doctorOtpEmail")?.value || "").trim();
  const otp   = (document.getElementById("doctorOtp")?.value      || "").trim();
  const errEl = document.getElementById("doctor-otp-error-msg");
  if (errEl) errEl.textContent = "";
  if (!otp || otp.length !== 6) { if (errEl) errEl.textContent = "Enter 6-digit OTP."; return; }

  const btn = document.getElementById("doctorVerifyOtpBtn");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/auth/doctor/otp/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp_code: otp }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok) {
      localStorage.setItem("ha_logged_in",  "true");
      localStorage.setItem("ha_role",       "doctor");
      localStorage.setItem("ha_email",      email);
      localStorage.setItem("ha_auth_token", data.token || "");
      setTimeout(() => { window.location.href = "chat.html"; }, 600);
    } else {
      if (errEl) errEl.textContent = data.detail || "Invalid OTP.";
    }
  } catch {
    if (errEl) errEl.textContent = "Network error.";
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ═══════════════════════════════════════════════════════════════
// ADMIN LOGIN
// ═══════════════════════════════════════════════════════════════
async function adminLogin() {
  const pin   = (document.getElementById("adminPin")?.value || "").trim();
  const errEl = document.getElementById("admin-error-msg");
  if (errEl) errEl.textContent = "";
  if (!pin) { if (errEl) errEl.textContent = "Admin password required."; return; }

  const btn  = document.querySelector(".admin-login-btn");
  const text = document.querySelector(".admin-btn-text");
  const spin = document.querySelector(".admin-loader");
  if (btn)  btn.disabled = true;
  if (text) text.style.display = "none";
  if (spin) spin.style.display = "inline-block";

  try {
    const res = await fetch(`${API_BASE}/auth/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin }),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok) {
      localStorage.setItem("ha_logged_in",  "true");
      localStorage.setItem("ha_role",       "admin");
      localStorage.setItem("ha_auth_token", data.token || "");
      localStorage.setItem("ha_user_id",    data.user_id || "admin");
      setTimeout(() => { window.location.href = "admin.html"; }, 600);
    } else {
      if (errEl) errEl.textContent = data.detail || "Invalid password.";
    }
  } catch {
    if (errEl) errEl.textContent = "Network error.";
  } finally {
    if (btn)  btn.disabled = false;
    if (text) text.style.display = "";
    if (spin) spin.style.display = "none";
  }
}
