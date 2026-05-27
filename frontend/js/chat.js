/* ═══════════════════════════════════════════════════════════════
   HA! — Chat Page Logic
   ═══════════════════════════════════════════════════════════════ */

let isWaiting = false;

function newChat() {
  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML = `
    <div class="welcome-screen" id="welcome-screen">
      <div class="welcome-logo"><span class="logo-ha">HA</span><span class="logo-exclaim">!</span></div>
      <h2>How can I help you today?</h2>
      <p>Ask me anything about your health, symptoms, medications, or wellness.</p>
      <div class="quick-prompts">
        <button class="quick-btn" onclick="quickPrompt('I have a headache and fever. What should I do?')">🤒 Headache & Fever</button>
        <button class="quick-btn" onclick="quickPrompt('What are the symptoms of diabetes?')">🩸 Diabetes Symptoms</button>
        <button class="quick-btn" onclick="quickPrompt('Give me tips for better sleep.')">😴 Sleep Tips</button>
        <button class="quick-btn" onclick="quickPrompt('How do I manage stress and anxiety?')">🧘 Stress Management</button>
      </div>
    </div>`;
}

function quickPrompt(text) {
  const input = document.getElementById("user-input");
  input.value = text;
  sendMessage();
}

function handleEnter(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

async function sendMessage() {
  if (isWaiting) return;

  const inputEl  = document.getElementById("user-input");
  const chatBox  = document.getElementById("chat-box");
  const sendBtn  = document.querySelector(".send-btn");
  const message  = inputEl.value.trim();
  const username = localStorage.getItem("ha_name") || "Patient";

  if (!message) return;

  // Hide welcome screen
  const welcome = document.getElementById("welcome-screen");
  if (welcome) welcome.remove();

  // Append user message
  appendMessage("user", message);
  inputEl.value = "";
  inputEl.style.height = "auto";

  // Show thinking indicator
  const thinkingId = appendThinking();
  isWaiting = true;
  if (sendBtn) sendBtn.disabled = true;

  try {
    const data = await apiPost("/chat", { message, username });
    removeElement(thinkingId);
    appendMessage("ai", data.response);
  } catch (err) {
    removeElement(thinkingId);
    appendMessage("ai", `⚠️ **Connection Error**\n\nCould not reach the HA! backend. Please make sure the server is running:\n\n\`uvicorn main:app --reload\`\n\n*Error: ${err.message}*`);
  } finally {
    isWaiting = false;
    if (sendBtn) sendBtn.disabled = false;
    inputEl.focus();
  }
}

function appendMessage(role, text) {
  const chatBox = document.getElementById("chat-box");
  const id = "msg-" + Date.now() + Math.random().toString(36).slice(2, 6);
  const isAI = role === "ai";
  const username = localStorage.getItem("ha_name") || "You";
  const initial = username.charAt(0).toUpperCase();

  const formattedText = isAI
    ? (typeof marked !== "undefined" ? marked.parse(text) : text.replace(/\n/g, "<br>"))
    : escapeHtml(text).replace(/\n/g, "<br>");

  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  const div = document.createElement("div");
  div.className = `message-row ${isAI ? "ai" : "user"}`;
  div.id = id;
  div.innerHTML = `
    <div class="message-content">
      <div class="avatar ${isAI ? "ai" : "user"}">${isAI ? "AI" : initial}</div>
      <div>
        <div class="msg-text">${formattedText}</div>
        <div class="msg-time">${now}</div>
      </div>
    </div>`;

  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return id;
}

function appendThinking() {
  const chatBox = document.getElementById("chat-box");
  const id = "thinking-" + Date.now();
  const div = document.createElement("div");
  div.className = "message-row ai";
  div.id = id;
  div.innerHTML = `
    <div class="message-content">
      <div class="avatar ai">AI</div>
      <div class="msg-text">
        <div class="thinking-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  return id;
}

function removeElement(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
