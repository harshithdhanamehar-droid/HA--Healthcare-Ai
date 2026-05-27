/* ═══════════════════════════════════════════════════════════════
   HA! — Symptom Checker Logic
   ═══════════════════════════════════════════════════════════════ */

let symptoms = [];

function addSymptomOnEnter(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    addSymptom();
  }
}

function addSymptom() {
  const input = document.getElementById("symptom-input");
  const value = input.value.trim();
  if (!value) return;
  if (symptoms.includes(value)) {
    input.value = "";
    return;
  }
  symptoms.push(value);
  renderTags();
  input.value = "";
  input.focus();
}

function addCommonSymptom(sym) {
  if (!symptoms.includes(sym)) {
    symptoms.push(sym);
    renderTags();
  }
}

function removeSymptom(sym) {
  symptoms = symptoms.filter((s) => s !== sym);
  renderTags();
}

function renderTags() {
  const container = document.getElementById("symptom-tags");
  container.innerHTML = symptoms
    .map(
      (s) => `
      <span class="symptom-tag">
        ${escapeHtml(s)}
        <button class="tag-remove" onclick="removeSymptom('${escapeHtml(s)}')" aria-label="Remove ${escapeHtml(s)}">×</button>
      </span>`
    )
    .join("");
}

async function analyzeSymptoms() {
  if (symptoms.length === 0) {
    alert("Please add at least one symptom.");
    return;
  }

  const btn = document.getElementById("analyze-btn");
  const age = document.getElementById("sym-age").value;
  const gender = document.getElementById("sym-gender").value;

  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="display:block;"></div> Analyzing...`;

  try {
    const data = await apiPost("/symptom-check", {
      symptoms,
      age: age ? parseInt(age) : null,
      gender: gender || null,
    });

    const resultEl = document.getElementById("analysis-result");
    const bodyEl   = document.getElementById("result-body");

    const formatted =
      typeof marked !== "undefined"
        ? marked.parse(data.analysis)
        : data.analysis.replace(/\n/g, "<br>");

    bodyEl.innerHTML = formatted;
    resultEl.style.display = "block";
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    alert(`Error: ${err.message}\n\nMake sure the backend is running.`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      Analyze Symptoms`;
  }
}

function clearAnalysis() {
  symptoms = [];
  renderTags();
  document.getElementById("analysis-result").style.display = "none";
  document.getElementById("sym-age").value = "";
  document.getElementById("sym-gender").value = "";
  document.getElementById("symptom-input").focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
