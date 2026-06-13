/* ═══════════════════════════════════════════════════════════════
   HA! — Login Logic with Multi-Role Auth
   ═══════════════════════════════════════════════════════════════ */

// ── API base URL — auto-detected by environment ───────────────────
const API_BASE = (
  window.location.protocol === "file:" ||
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
)
  ? "http://127.0.0.1:8000"
  : "https://ha-healthcare-ai.onrender.com";

// ── Storage keys ──────────────────────────────────────────────────
const STORAGE_KEYS = {
  TOKEN: 'ha_auth_token',
  USER_ID: 'ha_user_id',
  ROLE: 'ha_user_role',
  EXPIRES_IN: 'ha_token_expires',
};

// ── Utility: Show loading state ───────────────────────────────────
function showLoading(btnId) {
  // If it's a form ID, find the button inside
  let btn = document.querySelector(`#${btnId}`);
  
  if (!btn) {
    // Try to find a button in the form
    const form = document.getElementById(btnId);
    if (form && form.tagName === 'FORM') {
      btn = form.querySelector('.login-btn');
    }
  }
  
  if (btn) {
    // Disable all buttons in the form
    const form = btn.closest('form');
    if (form) {
      form.querySelectorAll('button').forEach(b => b.disabled = true);
    }
    btn.disabled = true;
    
    // Hide text, show spinner
    const textSpan = btn.querySelector('span:not(.spinner)');
    const spinner = btn.querySelector('.spinner');
    if (textSpan) textSpan.style.display = 'none';
    if (spinner) spinner.style.display = 'inline-block';
  }
}

function hideLoading(btnId) {
  // If it's a form ID, find the button inside
  let btn = document.querySelector(`#${btnId}`);
  
  if (!btn) {
    // Try to find a button in the form
    const form = document.getElementById(btnId);
    if (form && form.tagName === 'FORM') {
      btn = form.querySelector('.login-btn');
    }
  }
  
  if (btn) {
    // Enable all buttons
    const form = btn.closest('form');
    if (form) {
      form.querySelectorAll('button').forEach(b => b.disabled = false);
    }
    btn.disabled = false;
    
    // Show text, hide spinner
    const textSpan = btn.querySelector('span:not(.spinner)');
    const spinner = btn.querySelector('.spinner');
    if (textSpan) textSpan.style.display = 'inline';
    if (spinner) spinner.style.display = 'none';
  }
}

// ── Utility: Show error ───────────────────────────────────────────
function showError(msgId, message) {
  const el = document.getElementById(msgId);
  if (el) {
    el.textContent = message;
  }
}

// ── Utility: Clear error ──────────────────────────────────────────
function clearError(msgId) {
  const el = document.getElementById(msgId);
  if (el) {
    el.textContent = '';
  }
}

// ── Utility: Save auth token ──────────────────────────────────────
function saveAuthToken(token, userId, role, expiresIn) {
  localStorage.setItem(STORAGE_KEYS.TOKEN, token);
  localStorage.setItem(STORAGE_KEYS.USER_ID, userId);
  localStorage.setItem(STORAGE_KEYS.ROLE, role);
  localStorage.setItem(STORAGE_KEYS.EXPIRES_IN, Date.now() + expiresIn * 1000);
}

// ── Utility: Toggle password visibility ───────────────────────────
function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === 'password' ? 'text' : 'password';
}

// ─────────────────────────────────────────────────────────────────
// AUTH TAB SWITCHING
// ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  console.log('🔧 Initializing login page...');
  
  // Set up auth tab switching
  const tabs = document.querySelectorAll('.auth-tab');
  console.log(`✓ Found ${tabs.length} auth tabs`);
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tabName = tab.getAttribute('data-tab');
      console.log(`Clicked tab: ${tabName}`);
      switchAuthTab(tabName);
    });
  });

  // Verify all forms exist
  const forms = ['patientForm', 'doctorForm', 'adminForm'];
  forms.forEach(formId => {
    const form = document.getElementById(formId);
    if (form) {
      console.log(`✓ Form found: ${formId}`);
    } else {
      console.error(`✗ Form NOT found: ${formId}`);
    }
  });

  // Set patient as default active form
  const patientForm = document.getElementById('patientForm');
  if (patientForm) {
    patientForm.classList.add('active');
    console.log('✓ Patient form set as default active');
  }
});

function switchAuthTab(tabName) {
  // Update active tab
  document.querySelectorAll('.auth-tab').forEach(tab => {
    tab.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

  // Update active form - remove active class from all first
  document.querySelectorAll('.auth-method').forEach(form => {
    form.classList.remove('active');
    form.style.display = 'none'; // Ensure it's hidden
  });

  // Then add active class and show the selected form
  const selectedForm = document.getElementById(`${tabName}Form`);
  if (selectedForm) {
    selectedForm.classList.add('active');
    selectedForm.style.display = 'block'; // Ensure it's visible
    console.log(`✓ Switched to ${tabName} tab`);
  } else {
    console.error(`✗ Form not found: ${tabName}Form`);
  }

  // Clear errors
  clearError('error-msg');
  clearError('otp-error-msg');
  clearError('doctor-error-msg');
  clearError('doctor-otp-error-msg');
  clearError('admin-error-msg');
}

// ─────────────────────────────────────────────────────────────────
// PATIENT LOGIN
// ─────────────────────────────────────────────────────────────────

async function login() {
  const name     = document.getElementById("name").value.trim();
  const phone    = document.getElementById("phone").value.trim();
  const location = document.getElementById("location").value.trim();
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
  const btnText  = document.getElementById("btn-text");
  const loader   = document.getElementById("loader");
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

// ─────────────────────────────────────────────────────────────────
// PATIENT OTP LOGIN
// ─────────────────────────────────────────────────────────────────

function showOtpForm() {
  document.getElementById('otpSection').style.display = 'block';
  document.getElementById('userEmail').focus();
}

async function requestPatientOtp() {
  const email = document.getElementById('userEmail').value.trim();
  const errorMsg = document.getElementById('otp-error-msg');
  errorMsg.textContent = '';

  if (!email) {
    errorMsg.textContent = 'Please enter your email address.';
    return;
  }

  showLoading('requestOtpBtn');

  try {
    const response = await fetch(`${API_BASE}/auth/user/otp/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        purpose: 'verification',
      }),
    });

    const data = await response.json();
    hideLoading('requestOtpBtn');

    if (response.ok) {
      // Show OTP input field
      document.getElementById('otpCodeGroup').style.display = 'block';
      document.getElementById('requestOtpBtn').style.display = 'none';
      document.getElementById('verifyOtpBtn').style.display = 'block';
      document.getElementById('userOtp').focus();
      errorMsg.textContent = `OTP sent to ${email}. Check your email.`;
      errorMsg.style.color = 'var(--accent)';
    } else {
      errorMsg.textContent = data.detail || 'Failed to send OTP.';
    }
  } catch (error) {
    hideLoading('requestOtpBtn');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

async function verifyPatientOtp() {
  const email = document.getElementById('userEmail').value.trim();
  const otp = document.getElementById('userOtp').value.trim();
  const errorMsg = document.getElementById('otp-error-msg');
  errorMsg.textContent = '';

  if (!otp || otp.length !== 6) {
    errorMsg.textContent = 'Please enter a valid 6-digit OTP.';
    return;
  }

  showLoading('verifyOtpBtn');

  try {
    const response = await fetch(`${API_BASE}/auth/user/otp/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        otp_code: otp,
      }),
    });

    const data = await response.json();
    hideLoading('verifyOtpBtn');

    if (response.ok) {
      saveAuthToken(data.token, data.user_id, data.role, data.expires_in);
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_name', email.split('@')[0]);
      localStorage.setItem('ha_phone', email);
      localStorage.setItem('ha_location', 'Not provided');

      setTimeout(() => {
        window.location.href = 'chat.html';
      }, 800);
    } else {
      errorMsg.textContent = data.detail || 'Invalid OTP. Please try again.';
    }
  } catch (error) {
    hideLoading('verifyOtpBtn');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

// ─────────────────────────────────────────────────────────────────
// DOCTOR LOGIN
// ─────────────────────────────────────────────────────────────────

async function doctorLogin() {
  const email = document.getElementById('doctorEmail').value.trim();
  const password = document.getElementById('doctorPassword').value;
  const errorMsg = document.getElementById('doctor-error-msg');
  errorMsg.textContent = '';

  if (!email) {
    errorMsg.textContent = 'Please enter your email.';
    document.getElementById('doctorEmail').focus();
    return;
  }

  if (!password) {
    errorMsg.textContent = 'Please enter your password.';
    document.getElementById('doctorPassword').focus();
    return;
  }

  showLoading('doctorForm');

  try {
    const response = await fetch(`${API_BASE}/auth/doctor/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    });

    const data = await response.json();
    hideLoading('doctorForm');

    if (response.ok) {
      saveAuthToken(data.token, data.user_id, data.role, data.expires_in);
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_email', email);
      localStorage.setItem('ha_role', 'doctor');

      setTimeout(() => {
        window.location.href = 'chat.html';
      }, 800);
    } else {
      // Show specific error message from backend
      errorMsg.textContent = data.detail || 'Invalid credentials.';
    }
  } catch (error) {
    hideLoading('doctorForm');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

// ─────────────────────────────────────────────────────────────────
// DOCTOR OTP LOGIN
// ─────────────────────────────────────────────────────────────────

function showDoctorOtpForm() {
  document.getElementById('doctorOtpSection').style.display = 'block';
  document.getElementById('doctorOtpEmail').focus();
}

async function requestDoctorOtp() {
  const email = document.getElementById('doctorOtpEmail').value.trim();
  const errorMsg = document.getElementById('doctor-otp-error-msg');
  errorMsg.textContent = '';

  if (!email) {
    errorMsg.textContent = 'Please enter your email address.';
    return;
  }

  showLoading('doctorRequestOtpBtn');

  try {
    const response = await fetch(`${API_BASE}/auth/user/otp/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        purpose: 'doctor_verification',
      }),
    });

    const data = await response.json();
    hideLoading('doctorRequestOtpBtn');

    if (response.ok) {
      document.getElementById('doctorOtpCodeGroup').style.display = 'block';
      document.getElementById('doctorRequestOtpBtn').style.display = 'none';
      document.getElementById('doctorVerifyOtpBtn').style.display = 'block';
      document.getElementById('doctorOtp').focus();
      errorMsg.textContent = `OTP sent to ${email}. Check your email.`;
      errorMsg.style.color = 'var(--accent)';
    } else {
      errorMsg.textContent = data.detail || 'Failed to send OTP.';
    }
  } catch (error) {
    hideLoading('doctorRequestOtpBtn');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

async function verifyDoctorOtp() {
  const email = document.getElementById('doctorOtpEmail').value.trim();
  const otp = document.getElementById('doctorOtp').value.trim();
  const errorMsg = document.getElementById('doctor-otp-error-msg');
  errorMsg.textContent = '';

  if (!otp || otp.length !== 6) {
    errorMsg.textContent = 'Please enter a valid 6-digit OTP.';
    return;
  }

  showLoading('doctorVerifyOtpBtn');

  try {
    const response = await fetch(`${API_BASE}/auth/doctor/otp/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        otp_code: otp,
      }),
    });

    const data = await response.json();
    hideLoading('doctorVerifyOtpBtn');

    if (response.ok) {
      saveAuthToken(data.token, email, 'doctor', 3600);
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_name', email);
      localStorage.setItem('ha_role', 'doctor');

      setTimeout(() => {
        window.location.href = 'chat.html';
      }, 800);
    } else {
      errorMsg.textContent = data.detail || 'Invalid OTP. Please try again.';
    }
  } catch (error) {
    hideLoading('doctorVerifyOtpBtn');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

// ─────────────────────────────────────────────────────────────────
// ADMIN LOGIN
// ─────────────────────────────────────────────────────────────────

async function adminLogin() {
  const pin = document.getElementById('adminPin').value.trim();
  const errorMsg = document.getElementById('admin-error-msg');
  errorMsg.textContent = '';

  if (!pin || pin.length < 1) {
    errorMsg.textContent = 'Please enter your admin password.';
    document.getElementById('adminPin').focus();
    return;
  }

  showLoading('adminForm');

  try {
    const response = await fetch(`${API_BASE}/auth/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin: pin }),
    });

    const data = await response.json();
    hideLoading('adminForm');

    if (response.ok) {
      saveAuthToken(data.token, data.user_id, data.role, data.expires_in);
      localStorage.setItem('ha_logged_in', 'true');
      localStorage.setItem('ha_role', 'admin');

      setTimeout(() => {
        window.location.href = 'admin.html';
      }, 800);
    } else {
      errorMsg.textContent = data.detail || 'Invalid password.';
    }
  } catch (error) {
    hideLoading('adminForm');
    errorMsg.textContent = 'Network error. Please try again.';
  }
}

// ─────────────────────────────────────────────────────────────────
// GOOGLE OAUTH (Placeholder for future integration)
// ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const googleBtn = document.getElementById('googleLoginBtn');
  if (googleBtn) {
    googleBtn.addEventListener('click', () => {
      alert('Google OAuth will be enabled after configuring Google Cloud credentials.');
    });
  }
});

// ─────────────────────────────────────────────────────────────────
// KEYBOARD SHORTCUTS
// ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Patient form — Enter key
  ['name', 'phone', 'location'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') login();
      });
    }
  });

  // Doctor form — Enter key
  ['doctorEmail', 'doctorPassword'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doctorLogin();
      });
    }
  });

  // Admin form — Enter key
  const adminPin = document.getElementById('adminPin');
  if (adminPin) {
    adminPin.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') adminLogin();
    });
  }
});

