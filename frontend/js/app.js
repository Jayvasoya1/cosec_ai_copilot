/**
 * app.js — orchestration: wires UI + API together.
 *
 * Session isolation:
 *   Each browser tab generates a UUID stored in sessionStorage.
 *   It is sent with every /chat request as session_id so the backend
 *   (LangGraph MemorySaver) keeps that tab's conversation context
 *   completely separate from every other tab or user.
 *   Closing and re-opening the tab starts a fresh session.
 */

// ── Session ID ───────────────────────────────────────────────────────────────

function getSessionId() {
  let id = sessionStorage.getItem('cosec_session_id');
  if (!id) {
    id = 'sess_' + crypto.randomUUID();
    sessionStorage.setItem('cosec_session_id', id);
  }
  return id;
}

const SESSION_ID = getSessionId();

// ── Send message ─────────────────────────────────────────────────────────────

async function sendMessage() {
  const box  = document.getElementById('inputBox');
  const text = box.value.trim();
  if (!text) return;

  box.value = '';
  resize(box);
  document.getElementById('charCount').textContent = '';
  document.getElementById('sendBtn').disabled = true;

  appendUserMsg(text);
  showTyping();

  try {
    const data = await chatRequest(text, SESSION_ID);
    hideTyping();
    appendBotMsg(data.message, data.status, data.details);
    setPending(data.status === 'need_input');

  } catch (err) {
    hideTyping();
    appendBotMsg(
      `Connection error — is the server running at ${CONFIG.API_BASE}?`,
      'error',
      null
    );
    setPending(false);
    console.error(err);
  }

  document.getElementById('sendBtn').disabled = false;
  box.focus();
}

// ── Suggestion chips ─────────────────────────────────────────────────────────

function sendSuggestion(text) {
  const box = document.getElementById('inputBox');
  box.value = text;
  resize(box);
  sendMessage();
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Health check ─────────────────────────────────────────────────────────────

function checkHealth() {
  healthRequest()
    .then(() => setApiStatus(true))
    .catch(() => setApiStatus(false));
}

// ── Init ─────────────────────────────────────────────────────────────────────

document.getElementById('inputBox').addEventListener('input', function () {
  const n = this.value.length;
  document.getElementById('charCount').textContent = n > 0 ? `${n} / ${CONFIG.MAX_CHARS}` : '';
});

checkHealth();
setInterval(checkHealth, CONFIG.HEALTH_INTERVAL_MS);
document.getElementById('inputBox').focus();
