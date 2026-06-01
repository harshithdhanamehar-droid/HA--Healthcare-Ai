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
let currentChatId = null;

// ── Helper: always read phone fresh from localStorage ─────────────
// Never cache userPhone in a variable — localStorage is the source
// of truth. Reading it inline prevents stale-null bugs.
function getUserPhone() {
  return localStorage.getItem("ha_phone") || null;
}

// ── Initialize on page load ───────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Generate new chat ID for this session
  currentChatId = generateChatId();

  const phone = getUserPhone();
  console.log("HA! Chat init — ha_phone:", phone, "| chat_id:", currentChatId);

  if (phone) {
    loadChatHistory();
  } else {
    console.warn("HA! Chat init — ha_phone is null. Log out and log in again.");
  }
});

// ── Generate unique chat ID ───────────────────────────────────────
function generateChatId() {
  return "chat_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
}

// ── Load Chat History ─────────────────────────────────────────────
async function loadChatHistory() {
  const phone = getUserPhone();

  console.log("loadChatHistory: started, phone =", phone);

  if (!phone) {
    console.warn("loadChatHistory: no phone in localStorage, aborting");
    return;
  }

  try {
    console.log("loadChatHistory: calling GET /chat/history/" + phone);
    const data = await apiGet(`/chat/history/${phone}`);
    console.log("loadChatHistory: API response =", data);
    console.log("loadChatHistory: sessions count =", data.sessions ? data.sessions.length : 0);
    displayChatHistory(data.sessions || []);
  } catch (err) {
    console.error("loadChatHistory: API call failed —", err.message);
  }
}

// ── Display Chat History ──────────────────────────────────────────
function displayChatHistory(sessions) {
  console.log("displayChatHistory: called with", sessions ? sessions.length : 0, "sessions");

  const historyList  = document.getElementById("history-list");
  const historyEmpty = document.getElementById("history-empty");

  if (!historyList) {
    console.error("displayChatHistory: #history-list element NOT FOUND in DOM");
    return;
  }

  // Remove only previously rendered history items — leave #history-empty in place
  historyList.querySelectorAll(".history-item").forEach(el => el.remove());

  if (!sessions || sessions.length === 0) {
    console.log("displayChatHistory: no sessions — showing empty state");
    if (historyEmpty) historyEmpty.style.display = "flex";
    return;
  }

  // Hide the empty-state placeholder
  if (historyEmpty) historyEmpty.style.display = "none";

  console.log("displayChatHistory: rendering", sessions.length, "session(s)");

  sessions.forEach((session, index) => {
    console.log("displayChatHistory: session[" + index + "] =", session.chat_id, "|", session.preview);

    const item = document.createElement("div");
    item.className = "history-item";
    item.dataset.chatId = session.chat_id;

    const content = document.createElement("div");
    content.className = "history-content";
    content.onclick = () => loadChatSession(session.chat_id);

    const icon = document.createElement("div");
    icon.className = "history-icon";
    icon.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

    const text = document.createElement("div");
    text.className = "history-text";

    const preview = document.createElement("div");
    preview.className = "history-preview";
    preview.textContent = session.preview || "New conversation";

    const time = document.createElement("div");
    time.className = "history-time";
    time.textContent = formatChatTime(session.created_at);

    text.appendChild(preview);
    text.appendChild(time);
    content.appendChild(icon);
    content.appendChild(text);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "history-delete";
    deleteBtn.setAttribute("aria-label", "Delete chat");
    deleteBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>';
    deleteBtn.onclick = (e) => {
      e.stopPropagation();
      deleteChatSession(session.chat_id);
    };

    item.appendChild(content);
    item.appendChild(deleteBtn);

    // Append at the end of the list (before the hidden empty-state node)
    historyList.appendChild(item);
  });

  console.log("displayChatHistory: done — DOM now has",
    historyList.querySelectorAll(".history-item").length, "item(s)");
}

// ── Load Chat Session ─────────────────────────────────────────────
async function loadChatSession(chatId) {
  try {
    const data = await apiGet(`/chat/session/${chatId}`);
    
    // Clear current chat
    const chatBox = document.getElementById("chat-box");
    const welcomeScreen = document.getElementById("welcome-screen");
    
    chatBox.querySelectorAll(".message-row").forEach(el => el.remove());
    if (welcomeScreen) welcomeScreen.style.display = "none";
    
    // Set current chat ID
    currentChatId = chatId;
    
    // Display all messages
    data.messages.forEach(msg => {
      appendMessage(msg.role === "user" ? "user" : "ai", msg.message, false);
    });
    
    // Highlight active chat in history
    document.querySelectorAll(".history-item").forEach(item => {
      item.classList.toggle("active", item.dataset.chatId === chatId);
    });
    
  } catch (err) {
    console.error("Failed to load chat session:", err);
    alert("Failed to load chat session");
  }
}

// ── Delete Chat Session ───────────────────────────────────────────
async function deleteChatSession(chatId) {
  if (!confirm("Delete this chat? This action cannot be undone.")) return;
  
  try {
    await apiDelete(`/chat/session/${chatId}`);
    
    // If deleted chat was active, start new chat
    if (currentChatId === chatId) {
      newChat();
    }
    
    // Reload history
    loadChatHistory();
    
  } catch (err) {
    console.error("[HA! Chat] Failed to delete chat session:", err);
    alert("Failed to delete chat session");
  }
}

// ── Format Chat Time ──────────────────────────────────────────────
function formatChatTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString("en-IN", { month: "short", day: "numeric" });
}

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
  
  // Generate new chat ID
  currentChatId = generateChatId();
  
  // Remove active state from all history items
  document.querySelectorAll(".history-item").forEach(item => {
    item.classList.remove("active");
  });
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

  // Always read phone fresh — never use a cached variable
  const phone = getUserPhone();

  // Always ensure a chat ID exists before sending
  if (!currentChatId) {
    currentChatId = generateChatId();
  }

  if (!message) return;

  // Build the exact payload that will be sent to POST /chat
  const payload = {
    message:    message,
    username:   username,
    user_phone: phone,
    chat_id:    currentChatId,
  };

  // Log the full payload so it is visible in DevTools → Console
  console.log("Chat payload:", payload);

  if (!phone) {
    console.warn("user_phone is null — chat will NOT be saved. Log out and log in again.");
  }

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
    const data = await apiPost("/chat", payload);
    removeElement(thinkingId);
    appendMessage("ai", data.response);

    // Reload history sidebar so the new session appears immediately
    if (phone) {
      loadChatHistory();
    }
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
function appendMessage(role, text, scroll = true) {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;

  const isAI    = role === "ai" || role === "assistant";
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
  if (scroll) {
    chatBox.scrollTop = chatBox.scrollHeight;
  }
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
