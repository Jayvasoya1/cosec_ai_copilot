/**
 * app.js — orchestration: wires UI + API together
 * Event handlers, send flow, health polling
 */

let isPending = false;

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
    const data = await chatRequest(text);
    hideTyping();
    appendBotMsg(data.message, data.status, data.details);
    isPending = data.status === 'need_input';
    setPending(isPending);

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
