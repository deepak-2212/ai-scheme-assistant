// --- DOM Elements ---
const navBrowse = document.getElementById('nav-browse');
const navChat = document.getElementById('nav-chat');
const sectionBrowse = document.getElementById('browse-section');
const sectionChat = document.getElementById('chat-section');

const schemesGrid = document.getElementById('schemes-grid');
const chatContainer = document.getElementById('chat-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const langToggle = document.getElementById('lang-toggle');
const typingIndicator = document.getElementById('typing-indicator');

// Modal Elements
const modalOverlay = document.getElementById('scheme-modal');
const modalClose = document.getElementById('modal-close');
const modalCategory = document.getElementById('modal-category');
const modalTitle = document.getElementById('modal-title');
const modalDesc = document.getElementById('modal-desc');
const modalEligibility = document.getElementById('modal-eligibility');
const modalBenefits = document.getElementById('modal-benefits');
const modalDocs = document.getElementById('modal-docs');
const modalApply = document.getElementById('modal-apply');

// State
let isEnglish = true;
let schemesDB = [];

// --- Navigation ---
function switchTab(tab) {
    if (tab === 'browse') {
        navBrowse.classList.add('active');
        navChat.classList.remove('active');
        sectionBrowse.classList.add('active');
        sectionChat.classList.remove('active');
    } else {
        navChat.classList.add('active');
        navBrowse.classList.remove('active');
        sectionChat.classList.add('active');
        sectionBrowse.classList.remove('active');
        scrollToBottom();
    }
}
navBrowse.onclick = () => switchTab('browse');
navChat.onclick = () => switchTab('chat');

// --- Load Schemes from Backend ---
async function loadSchemes() {
    try {
        const res = await fetch(`${BASE_URL}/schemes`);
        schemesDB = await res.json();
        renderBrowseGrid();
    } catch (err) {
        console.error("Error loading schemes:", err);
    }
}

// --- Render Grid ---
function renderBrowseGrid() {
    schemesGrid.innerHTML = schemesDB.map(s => `
        <div class="scheme-card">
            <span class="badge">${s.category}</span>
            <h3>${s.scheme_name}</h3>
            <p class="short-desc">${s.benefits.summary}</p>
            <button onclick="openModal('${s.scheme_id}')">
                ${isEnglish ? 'View Details' : 'विवरण देखें'}
            </button>
        </div>
    `).join('');
}

// --- Modal ---
function openModal(id) {
    const s = schemesDB.find(x => x.scheme_id === id);
    if (!s) return;

    modalCategory.textContent = s.category;
    modalTitle.textContent = s.scheme_name;
    modalDesc.textContent = s.benefits.summary;

    modalEligibility.innerHTML = `
        <li>Gender: ${s.eligibility.gender}</li>
        <li>Income Limit: ${s.eligibility.annual_income_limit || 'No limit'}</li>
    `;

    modalBenefits.innerHTML = `
        <li>${s.benefits.summary}</li>
    `;

    modalDocs.innerHTML = s.documents_required.map(d => `<li>${d}</li>`).join('');

    modalApply.href = s.application.apply_url || s.official_url;

    modalOverlay.classList.add('open');
}

modalClose.onclick = () => modalOverlay.classList.remove('open');
modalOverlay.onclick = e => {
    if (e.target === modalOverlay) modalOverlay.classList.remove('open');
};

// --- Chat Functions ---
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `<div class="bubble"><p>${text}</p></div>`;
    chatContainer.insertBefore(div, typingIndicator);
}

function appendAIMessage(text) {
    const div = document.createElement('div');
    div.className = 'message ai';
    div.innerHTML = `
        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bubble"><p>${text}</p></div>
    `;
    chatContainer.insertBefore(div, typingIndicator);
}

// --- Chat API ---
async function handleSend() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendUserMessage(text);
    chatInput.value = '';

    typingIndicator.style.display = 'flex';
    scrollToBottom();

    try {
        const res = await fetch(`${BASE_URL}/chat?query=${encodeURIComponent(text)}`);
        const data = await res.json();

        typingIndicator.style.display = 'none';
        appendAIMessage(data.response);

    } catch (err) {
        typingIndicator.style.display = 'none';
        appendAIMessage("Server error. Please try again.");
    }
}

// --- Voice ---
micBtn.addEventListener('click', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);

    let chunks = [];
    recorder.start();

    micBtn.classList.add('recording');

    recorder.ondataavailable = e => chunks.push(e.data);

    setTimeout(() => recorder.stop(), 3000);

    recorder.onstop = async () => {
        micBtn.classList.remove('recording');

        const blob = new Blob(chunks, { type: 'audio/wav' });
        const form = new FormData();
        form.append("file", blob);

        const res = await fetch(`${BASE_URL}/voice`, {
            method: "POST",
            body: form
        });

        const data = await res.json();

        appendUserMessage(data.transcribed_text);
        appendAIMessage(data.response);
    };
});

// --- Events ---
sendBtn.onclick = handleSend;
chatInput.addEventListener('keypress', e => {
    if (e.key === 'Enter') handleSend();
});

// --- Language Toggle ---
langToggle.onclick = () => {
    isEnglish = !isEnglish;
    renderBrowseGrid();
};

// --- Init ---
loadSchemes();