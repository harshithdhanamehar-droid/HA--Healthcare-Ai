/* ═══════════════════════════════════════════════════════════════
   HA! — Emergency SOS Logic
   ═══════════════════════════════════════════════════════════════ */

let selectedEmergencyType = "";

function selectEmergency(type, btn) {
  selectedEmergencyType = type;
  document.querySelectorAll(".emg-type-btn").forEach((b) => b.classList.remove("selected"));
  btn.classList.add("selected");

  // Pre-fill condition textarea
  const conditionEl = document.getElementById("emg-condition");
  if (!conditionEl.value) {
    conditionEl.value = type;
  }
}

async function getEmergencyGuide() {
  const conditionEl = document.getElementById("emg-condition");
  const condition   = conditionEl.value.trim() || selectedEmergencyType;

  if (!condition) {
    alert("Please select an emergency type or describe the situation.");
    return;
  }

  const btn = document.getElementById("emg-btn");
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="display:block;"></div> Getting Instructions...`;

  const patientName = localStorage.getItem("ha_name")     || "Patient";
  const location    = localStorage.getItem("ha_location") || "Unknown";

  try {
    const data = await apiPost("/emergency/alert", {
      patient_name: patientName,
      location,
      condition,
    });

    const resultEl  = document.getElementById("emergency-result");
    const bodyEl    = document.getElementById("emg-result-body");
    const alertIdEl = document.getElementById("alert-id-display");

    const formatted =
      typeof marked !== "undefined"
        ? marked.parse(data.instructions)
        : data.instructions.replace(/\n/g, "<br>");

    bodyEl.innerHTML = formatted;
    alertIdEl.textContent = `Alert ID: ${data.alert_id}`;
    resultEl.style.display = "block";
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    alert(`Error: ${err.message}\n\nMake sure the backend is running.`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🚨 Get Immediate Instructions";
  }
}

function clearEmergency() {
  selectedEmergencyType = "";
  document.querySelectorAll(".emg-type-btn").forEach((b) => b.classList.remove("selected"));
  document.getElementById("emg-condition").value = "";
  document.getElementById("emergency-result").style.display = "none";
  window.scrollTo({ top: 0, behavior: "smooth" });
}
