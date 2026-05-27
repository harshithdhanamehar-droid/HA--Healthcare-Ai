/* --- LOGIN LOGIC --- */
function login() {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const location = document.getElementById("location").value.trim();
    
    const btnText = document.getElementById("btn-text");
    const loader = document.getElementById("loader");
    const errorMsg = document.getElementById("error-msg");

    // Regex Rules:
    // Name: Letters and spaces only
    // Phone: Numbers only
    // Location: Letters and spaces only
    const nameRegex = /^[A-Za-z\s]+$/;
    const phoneRegex = /^[0-9]+$/;
    const locationRegex = /^[A-Za-z\s]+$/;

    errorMsg.innerText = "";

    if (!nameRegex.test(name)) {
        errorMsg.innerText = "Name must contain characters only.";
        return;
    }
    if (!phoneRegex.test(phone)) {
        errorMsg.innerText = "Mobile Number must contain numbers only.";
        return;
    }
    if (!locationRegex.test(location)) {
        errorMsg.innerText = "Location must contain characters only.";
        return;
    }

    // Show loading spinner
    btnText.style.display = "none";
    loader.style.display = "block";

    // Save details and redirect
    setTimeout(() => {
        localStorage.setItem("username", name);
        window.location.href = "chat.html";
    }, 1200);
}

/* --- CHAT LOGIC --- */

// If we are on the chat page, load the username
document.addEventListener("DOMContentLoaded", () => {
    const displayNameEl = document.getElementById("display-name");
    if (displayNameEl) {
        displayNameEl.innerText = localStorage.getItem("username") || "Guest";
    }
});

// Trigger send on 'Enter' key
function handleEnter(e) {
    if (e.key === "Enter") sendMessage();
}

async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const message = inputField.value.trim();
    const username = localStorage.getItem("username") || "Guest";

    if (!message) return;

    // Add User Message to UI
    appendMessage("user", message);
    inputField.value = "";

    // Show "Thinking..." indicator
    const loadingId = appendMessage("ai", "Thinking...", true);

    try {
        // Send to FastAPI Backend
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: username, message: message })
        });

        const data = await response.json();
        
        // Remove loading and show AI Response
        const loadingElement = document.getElementById(loadingId);
        if(loadingElement) loadingElement.remove();
        
        appendMessage("ai", data.response);

    } catch (error) {
        console.error(error);
        const loadingElement = document.getElementById(loadingId);
        if(loadingElement) loadingElement.innerHTML = `<div class="text" style="color:#ef4444;">Error: Backend not connected. Is FastAPI running?</div>`;
    }
}

// Function to add messages to the UI
function appendMessage(sender, text, isLoading = false) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message-row ${sender}`;
    const uniqueId = "msg-" + Date.now();
    
    // Use marked.js to format AI text properly, keep user text plain
    const formattedText = (sender === "ai" && !isLoading) ? marked.parse(text) : `<p>${text}</p>`;

    msgDiv.innerHTML = `
        <div class="message-content" id="${uniqueId}">
            <div class="avatar ${sender}">${sender === 'user' ? 'U' : 'AI'}</div>
            <div class="text">${formattedText}</div>
        </div>
    `;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return uniqueId;
}