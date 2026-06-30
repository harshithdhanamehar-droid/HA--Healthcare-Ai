/* ═══════════════════════════════════════════════════════════════
   HA! — Appointments Page Logic
   ═══════════════════════════════════════════════════════════════ */

let cancelTargetId = null;

document.addEventListener("DOMContentLoaded", loadAppointments);

async function loadAppointments() {
  const phone = localStorage.getItem("ha_phone") || "";
  const container = document.getElementById("appointments-container");

  try {
    const data = await apiGet(`/appointments/${encodeURIComponent(phone)}`);
    renderAppointments(data.appointments);
  } catch (err) {
    container.innerHTML = `
      <div class="loading-state">
        <p>⚠️ Could not load appointments.</p>
        <p style="font-size:13px;color:var(--text-muted);margin-top:8px;">${err.message}</p>
      </div>`;
  }
}

function renderAppointments(appointments) {
  const container = document.getElementById("appointments-container");

  if (!appointments || appointments.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📅</div>
        <h3>No Appointments Yet</h3>
        <p>You haven't booked any appointments. Find a doctor and book your first one!</p>
        <a href="doctors.html" class="btn-primary">👨‍⚕️ Find Doctors</a>
      </div>`;
    return;
  }

  // Sort: upcoming first
  const sorted = [...appointments].sort(
    (a, b) => new Date(b.booked_at) - new Date(a.booked_at)
  );

  container.innerHTML = `
    <div class="appointments-list">
      ${sorted.map(appointmentCard).join("")}
    </div>`;
}

function appointmentCard(apt) {
  const isCancelled = apt.status === "cancelled";
  return `
    <div class="appointment-card">
      <div class="apt-status-bar ${isCancelled ? "cancelled" : ""}"></div>
      <div class="apt-body">
        <div class="apt-header">
          <div>
            <div class="apt-doctor-name">${escapeHtml(apt.doctor_name)}</div>
            <div class="apt-specialty">${escapeHtml(apt.specialty)}</div>
          </div>
          <span class="apt-badge ${isCancelled ? "cancelled" : "confirmed"}">
            ${isCancelled ? "Cancelled" : "Confirmed"}
          </span>
        </div>
        <div class="apt-details">
          <div class="apt-detail">📅 <span>${formatDate(apt.date)}</span></div>
          <div class="apt-detail">🕐 <span>${escapeHtml(apt.time_slot)}</span></div>
          <div class="apt-detail">🏥 <span>${escapeHtml(apt.hospital)}</span></div>
          <div class="apt-detail">💰 <span>₹${apt.fee}</span></div>
        </div>
        ${apt.reason ? `<div class="apt-detail" style="margin-bottom:12px;">📝 <span style="color:var(--text-muted)">${escapeHtml(apt.reason)}</span></div>` : ""}
        <div class="apt-id-display">ID: ${apt.id}</div>
        ${
          !isCancelled
            ? `<div class="apt-actions">
                <button class="cancel-apt-btn" onclick="openCancelModal('${apt.id}')">
                  ✕ Cancel Appointment
                </button>
               </div>`
            : ""
        }
      </div>
    </div>`;
}

// ── Cancel Modal ──────────────────────────────────────────────────
function openCancelModal(appointmentId) {
  cancelTargetId = appointmentId;
  document.getElementById("cancel-modal").style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeCancelModal() {
  cancelTargetId = null;
  document.getElementById("cancel-modal").style.display = "none";
  document.body.style.overflow = "";
}

async function confirmCancel() {
  if (!cancelTargetId) return;
  const btn = document.getElementById("confirm-cancel-btn");
  btn.disabled = true;
  btn.textContent = "Cancelling...";

  try {
    await apiDelete(`/appointments/${cancelTargetId}`);
    closeCancelModal();
    
    // Show success toast
    showToast("✅ Appointment cancelled successfully", "success");
    
    // Reload appointments after a brief delay to show toast
    setTimeout(() => loadAppointments(), 1500);
  } catch (err) {
    // Show error toast instead of alert
    showToast(`❌ Failed to cancel: ${err.message}`, "error");
    btn.disabled = false;
    btn.textContent = "Yes, Cancel";
  }
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Toast notification system
function showToast(message, type = "success") {
  // Create toast container if it doesn't exist
  let toastContainer = document.getElementById("toast-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-container";
    toastContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toast = document.createElement("div");
  const bgColor = type === "success" ? "#10b981" : "#ef4444";
  const textColor = "#ffffff";
  
  toast.style.cssText = `
    background: ${bgColor};
    color: ${textColor};
    padding: 14px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease;
    max-width: 400px;
    pointer-events: all;
    cursor: pointer;
  `;
  
  toast.textContent = message;
  toastContainer.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.animation = "slideOut 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);

  // Click to dismiss
  toast.onclick = () => {
    toast.style.animation = "slideOut 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  };
}

// Add CSS animations for toast
if (!document.getElementById("toast-styles")) {
  const style = document.createElement("style");
  style.id = "toast-styles";
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(400px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(400px); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
}
