/* ═══════════════════════════════════════════════════════════════
   HA! — Doctors & Booking Logic
   ═══════════════════════════════════════════════════════════════ */

let allDoctors = [];
let selectedDoctor = null;
let selectedSlot = null;
let currentSpecialty = "all";

// ── Load Doctors ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await apiGet("/doctors");
    allDoctors = data.doctors;
    renderDoctors(allDoctors);
  } catch (err) {
    document.getElementById("doctors-grid").innerHTML = `
      <div class="loading-state">
        <p>⚠️ Could not load doctors. Make sure the backend is running.</p>
        <p style="font-size:13px;color:var(--text-muted);margin-top:8px;">${err.message}</p>
      </div>`;
  }
});

function renderDoctors(doctors) {
  const grid = document.getElementById("doctors-grid");
  if (doctors.length === 0) {
    grid.innerHTML = `<div class="loading-state"><p>No doctors found for this specialty.</p></div>`;
    return;
  }
  grid.innerHTML = doctors.map(doctorCard).join("");
}

function doctorCard(doc) {
  const initial = doc.name.split(" ").slice(1).join(" ").charAt(0) || doc.name.charAt(0);
  const stars = "⭐".repeat(Math.round(doc.rating));
  return `
    <div class="doctor-card">
      <div class="doctor-card-top">
        <div class="doctor-avatar">${initial}</div>
        <div class="doctor-info">
          <div class="doctor-name">${escapeHtml(doc.name)}</div>
          <div class="doctor-specialty">${escapeHtml(doc.specialty)}</div>
          <div class="doctor-hospital">🏥 ${escapeHtml(doc.hospital)}</div>
        </div>
      </div>
      <div class="doctor-meta">
        <div class="meta-item">
          <span class="meta-icon">🩺</span>
          <span>${escapeHtml(doc.experience)}</span>
        </div>
        <div class="doctor-rating">
          ⭐ ${doc.rating}
        </div>
        <div class="meta-item">
          <span class="meta-icon">🌐</span>
          <span>${doc.languages.join(", ")}</span>
        </div>
      </div>
      <div class="doctor-fee">Consultation Fee: <strong>₹${doc.fee}</strong></div>
      <button class="book-btn" onclick="openBookingModal('${doc.id}')">
        📅 Book Appointment
      </button>
    </div>`;
}

// ── Filter ────────────────────────────────────────────────────────
function filterDoctors() {
  const query = document.getElementById("doctor-search").value.toLowerCase();
  const filtered = allDoctors.filter((d) => {
    const matchSearch =
      d.name.toLowerCase().includes(query) ||
      d.specialty.toLowerCase().includes(query) ||
      d.hospital.toLowerCase().includes(query);
    const matchSpec =
      currentSpecialty === "all" ||
      d.specialty.toLowerCase().includes(currentSpecialty.toLowerCase());
    return matchSearch && matchSpec;
  });
  renderDoctors(filtered);
}

function filterBySpecialty(specialty, btn) {
  currentSpecialty = specialty;
  document.querySelectorAll(".spec-filter").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  filterDoctors();
}

// ── Booking Modal ─────────────────────────────────────────────────
function openBookingModal(doctorId) {
  selectedDoctor = allDoctors.find((d) => d.id === doctorId);
  if (!selectedDoctor) return;
  selectedSlot = null;

  // Set min date to today
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("apt-date").min = today;
  document.getElementById("apt-date").value = "";
  document.getElementById("apt-reason").value = "";
  document.getElementById("booking-error").textContent = "";

  // Doctor mini card
  const initial = selectedDoctor.name.split(" ").slice(1).join(" ").charAt(0) || selectedDoctor.name.charAt(0);
  document.getElementById("modal-doctor-info").innerHTML = `
    <div class="mini-avatar">${initial}</div>
    <div class="mini-info">
      <div class="mini-name">${escapeHtml(selectedDoctor.name)}</div>
      <div class="mini-spec">${escapeHtml(selectedDoctor.specialty)}</div>
      <div class="mini-fee">Fee: ₹${selectedDoctor.fee}</div>
    </div>`;

  // Time slots
  const slotsEl = document.getElementById("time-slots");
  slotsEl.innerHTML = selectedDoctor.available_slots
    .map(
      (slot) =>
        `<button class="time-slot-btn" onclick="selectSlot('${slot}', this)">${slot}</button>`
    )
    .join("");

  document.getElementById("booking-modal").style.display = "flex";
  document.body.style.overflow = "hidden";
}

function selectSlot(slot, btn) {
  selectedSlot = slot;
  document.querySelectorAll(".time-slot-btn").forEach((b) => b.classList.remove("selected"));
  btn.classList.add("selected");
}

function closeModal() {
  document.getElementById("booking-modal").style.display = "none";
  document.body.style.overflow = "";
  selectedDoctor = null;
  selectedSlot = null;
}

async function confirmBooking() {
  const date   = document.getElementById("apt-date").value;
  const reason = document.getElementById("apt-reason").value.trim();
  const errEl  = document.getElementById("booking-error");
  const btn    = document.getElementById("confirm-btn");

  errEl.textContent = "";

  if (!date) { errEl.textContent = "Please select a date."; return; }
  if (!selectedSlot) { errEl.textContent = "Please select a time slot."; return; }

  const patientName  = localStorage.getItem("ha_name")  || "Patient";
  const patientPhone = localStorage.getItem("ha_phone") || "0000000000";

  btn.disabled = true;
  btn.textContent = "Booking...";

  try {
    const data = await apiPost("/appointments/book", {
      patient_name:  patientName,
      patient_phone: patientPhone,
      doctor_id:     selectedDoctor.id,
      date,
      time_slot:     selectedSlot,
      reason,
    });

    closeModal();
    showSuccessModal(data.appointment);
  } catch (err) {
    errEl.textContent = `Booking failed: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Confirm Booking";
  }
}

// ── Success Modal ─────────────────────────────────────────────────
function showSuccessModal(apt) {
  document.getElementById("success-details").innerHTML = `
    <div class="success-detail-row">
      <span class="label">Appointment ID</span>
      <span class="value apt-id">${apt.id}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Doctor</span>
      <span class="value">${escapeHtml(apt.doctor_name)}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Specialty</span>
      <span class="value">${escapeHtml(apt.specialty)}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Hospital</span>
      <span class="value">${escapeHtml(apt.hospital)}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Date</span>
      <span class="value">${formatDate(apt.date)}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Time</span>
      <span class="value">${apt.time_slot}</span>
    </div>
    <div class="success-detail-row">
      <span class="label">Fee</span>
      <span class="value">₹${apt.fee}</span>
    </div>`;

  document.getElementById("success-modal").style.display = "flex";
  document.body.style.overflow = "hidden";
}

function closeSuccessModal() {
  document.getElementById("success-modal").style.display = "none";
  document.body.style.overflow = "";
}

// ── Helpers ───────────────────────────────────────────────────────
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
