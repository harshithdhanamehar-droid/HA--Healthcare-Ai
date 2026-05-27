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
    loadAppointments();
  } catch (err) {
    alert(`Failed to cancel: ${err.message}`);
  } finally {
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
