/* ═══════════════════════════════════════════════════════════════
   HA! — Chat Page Logic
   Rules:
   - NEVER inject sidebar, user profile, or welcome screen HTML
   - NEVER use innerHTML to rebuild layout sections
   - ONLY append message bubbles into #chat-box
   - ALL layout already exists statically in chat.html
   ═══════════════════════════════════════════════════════════════ */

"use strict";

let isWaiting = false;

// ── New Chat ──────────────────────────────────────────────────────
// Clears messages and shows the static welcome screen that already
// exists in the DOM — does NOT re-inject any HTML.
function newChat() {
  const chatBox       = document.getElementById("chat-box");
  const welcomeScreen = document.getElementById("welcome-screen");

  // Remove every message row that was appended during the session
  chatBox.querySelectorAll(".message-row").forEach((el) => el.remove());

  // Reveal the static welcome screen (hidden when first message sent)
  if (welcomeScreen) {
    welcomeScreen.style.display = "";
  }

  // Reset textarea
  const input = document.getElementById("user-input");
  if (input) {
    input.value = "";
    input.style.height = "auto";
  }
}

// ── Quick Prompt ──────────────────────────────────────────────────
// Fills the textarea and sends — no DOM injection.
function quickPrompt(text) {
  const input = document.getElementById("user-input");
  if (!input) return;
  input.value = text;
  autoResize(input);
  sendMessage();
}

// ── Keyboard handler ──────────────────────────────────────────────
function handleEnter(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Textarea auto-resize ──────────────────────────────────────────
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 180) + "px";
}

// ── Send Message ──────────────────────────────────────────────────
async function sendMessage() {
  if (isWaiting) return;

  const inputEl  = document.getElementById("user-input");
  const sendBtn  = document.querySelector(".send-btn");
  const message  = inputEl ? inputEl.value.trim() : "";
  const username = localStorage.getItem("ha_name") || "Patient";

  if (!message) return;

  // Hide the static welcome screen on first message
  const welcomeScreen = document.getElementById("welcome-screen");
  if (welcomeScreen) welcomeScreen.style.display = "none";

  // Append user bubble
  appendMessage("user", message);

  // Clear input
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
    appendMessage(
      "ai",
      `⚠️ **Connection Error**\n\nCould not reach the HA! backend.\n\n*${err.message}*`
    );
  } finally {
    isWaiting = false;
    if (sendBtn) sendBtn.disabled = false;
    if (inputEl) inputEl.focus();
  }
}

// ── Append a chat message bubble ──────────────────────────────────
// Appends ONE .message-row into #chat-box.
// Matches the exact CSS structure in chat.css:
//   .message-row > .message-content > .avatar + div > .msg-text + .msg-time
function appendMessage(role, text) {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;

  const isAI    = role === "ai";
  const username = localStorage.getItem("ha_name") || "You";
  const initial  = username.charAt(0).toUpperCase();
  const now      = new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  // Format text: markdown for AI, plain escaped text for user
  const formattedText = isAI
    ? (typeof marked !== "undefined"
        ? marked.parse(text)
        : text.replace(/\n/g, "<br>"))
    : escapeHtml(text).replace(/\n/g, "<br>");

  // Build elements — no innerHTML on existing DOM nodes
  const row = document.createElement("div");
  row.className = `message-row ${isAI ? "ai" : "user"}`;

  const content = document.createElement("div");
  content.className = "message-content";

  const avatar = document.createElement("div");
  avatar.className = `avatar ${isAI ? "ai" : "user"}`;
  avatar.textContent = isAI ? "AI" : initial;

  const textWrap = document.createElement("div");

  const msgText = document.createElement("div");
  msgText.className = "msg-text";
  msgText.innerHTML = formattedText; // safe: AI text is markdown, user text is escaped

  const msgTime = document.createElement("div");
  msgTime.className = "msg-time";
  msgTime.textContent = now;

  // Assemble
  textWrap.appendChild(msgText);
  textWrap.appendChild(msgTime);
  content.appendChild(avatar);
  content.appendChild(textWrap);
  row.appendChild(content);
  chatBox.appendChild(row);

  // Scroll to latest message
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ── Append thinking indicator ─────────────────────────────────────
// Appends a temporary .message-row with animated dots.
function appendThinking() {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return null;

  const id = "thinking-" + Date.now();

  const row = document.createElement("div");
  row.className = "message-row ai";
  row.id = id;

  const content = document.createElement("div");
  content.className = "message-content";

  const avatar = document.createElement("div");
  avatar.className = "avatar ai";
  avatar.textContent = "AI";

  const textWrap = document.createElement("div");

  const msgText = document.createElement("div");
  msgText.className = "msg-text";

  const dots = document.createElement("div");
  dots.className = "thinking-dots";
  dots.innerHTML = "<span></span><span></span><span></span>";

  msgText.appendChild(dots);
  textWrap.appendChild(msgText);
  content.appendChild(avatar);
  content.appendChild(textWrap);
  row.appendChild(content);
  chatBox.appendChild(row);

  chatBox.scrollTop = chatBox.scrollHeight;
  return id;
}

// ── Remove element by id ──────────────────────────────────────────
function removeElement(id) {
  if (!id) return;
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── HTML escape (user input only) ────────────────────────────────
function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
