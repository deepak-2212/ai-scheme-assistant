// ===============================
// GLOBALS
// ===============================
const chatFeed = document.getElementById("chat-feed");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");


// ===============================
// SEND MESSAGE FUNCTION
// ===============================
function sendMessage() {
    const message = input.value.trim();

    if (!message) return;

    addUserMessage(message);
    input.value = "";

    // Loading indicator
    const loaderDiv = document.createElement("div");
    loaderDiv.className = "message ai-message loading-msg";
    loaderDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="message-content">
            <p class="text-bubble"><i class="fa-solid fa-ellipsis fa-fade"></i> Processing...</p>
        </div>
    `;
    chatFeed.appendChild(loaderDiv);
    scrollToBottom();

    fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: message,
            session_id: "user1"
        })
    })
        .then(res => res.json())
        .then(data => {
            chatFeed.removeChild(loaderDiv); // Remove loader
            addBotMessage(data.text);

            if (data.schemes && data.schemes.length > 0) {
                renderSchemeCards(data.schemes);
            }
        })
        .catch(err => {
            console.error(err);
            chatFeed.removeChild(loaderDiv);
            addBotMessage("⚠️ Server error. Please try again.");
        });
}


// ===============================
// EVENT LISTENERS (FIXED)
// ===============================

// Send button click
sendBtn.addEventListener("click", sendMessage);

// Enter key press
input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }
});


// ===============================
// USER MESSAGE UI
// ===============================
function addUserMessage(text) {
    const div = document.createElement("div");
    div.className = "message user-message";

    div.innerHTML = `
        <div class="message-content">
            <p class="text-bubble">${text}</p>
        </div>
    `;

    chatFeed.appendChild(div);
    scrollToBottom();
}


// ===============================
// BOT MESSAGE UI
// ===============================
function addBotMessage(text) {
    const div = document.createElement("div");
    div.className = "message ai-message";

    div.innerHTML = `
        <div class="message-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="message-content">
            <p class="text-bubble">${text}</p>
        </div>
    `;

    chatFeed.appendChild(div);
    scrollToBottom();
}


// ===============================
// SCHEME CARDS (FINAL)
// ===============================
function renderSchemeCards(schemes) {
    const container = document.createElement("div");
    container.className = "schemes-container";

    schemes.forEach(s => {
        const card = document.createElement("div");
        card.className = "scheme-card";

        card.innerHTML = `
            <div class="card-header">
                <div class="scheme-icon"><i class="fa-solid fa-file-contract"></i></div>
                <h3 class="scheme-title">${s.name}</h3>
            </div>

            <div class="card-body">
                <p><b>Benefits:</b> ${s.benefit}</p>

                ${s.documents && s.documents.length > 0 ? `
                    <div class="docs-section">
                        <b>Documents Required:</b>
                        <ul>
                            ${s.documents.map(doc => `<li>${doc}</li>`).join("")}
                        </ul>
                    </div>
                ` : ""}

                ${s.steps && s.steps.length > 0 ? `
                    <div class="steps-section">
                        <b>How to Apply:</b>
                        <ol>
                            ${s.steps.map(step => `<li>${step}</li>`).join("")}
                        </ol>
                    </div>
                ` : ""}

                <div class="eligibility-tag">
                    <i class="fa-solid fa-check-circle"></i> ${s.reason}
                </div>
            </div>

            <div class="card-footer">
                <a href="${s.apply}" target="_blank" class="apply-btn">
                    Apply Now <i class="fa-solid fa-arrow-right" style="margin-left: 5px;"></i>
                </a>
            </div>
        `;

        container.appendChild(card);
    });

    chatFeed.appendChild(container);
    scrollToBottom();
}


// ===============================
// SCROLL FIX
// ===============================
function scrollToBottom() {
    chatFeed.scrollTop = chatFeed.scrollHeight;
}