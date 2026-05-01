/**
 * ui.js — all DOM building and visual state
 * No business logic here — only "how things look"
 */

const STATUS_ICON = { success: '', error: '', need_input: '🔔', partial_success: '⚠️' };
const STATUS_LABEL = { success: 'Success', error: 'Error', need_input: 'Input needed', partial_success: 'Partial success' };

const CHIPS_HTML = `
  <div class="chip" onclick="sendSuggestion('What can I do?')">❓ What can I do?</div>
  <div class="chip" onclick="sendSuggestion('Add user Jay with id 101')">➕ Add user</div>
  <div class="chip" onclick="sendSuggestion('Enroll user 5 on door 1')">👤 Enroll user</div>
  <div class="chip" onclick="sendSuggestion('Get access setting')">🔑 Get access setting</div>
  <div class="chip" onclick="sendSuggestion('Get panel details')">📊 Panel details</div>
`;

// ── Utilities ────────────────────────────────────────────────────────────────

function esc(t) {
  return String(t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function time() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function scrollBottom() {
  const w = document.getElementById('chatWrap');
  w.scrollTop = w.scrollHeight;
}

function resize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ── Welcome screen ────────────────────────────────────────────────────────────

function hideWelcome() {
  const w = document.getElementById('welcome');
  if (w) w.remove();
}

function showWelcome() {
  const inner = document.getElementById('chatInner');
  const w = document.createElement('div');
  w.className = 'welcome';
  w.id = 'welcome';
  w.innerHTML = `
    <img class="welcome-side-logo" src="./public/side_logo.png" alt="CoSec" />
    <div class="welcome-title">COSEC Copilot</div>
    <div class="welcome-desc">
      Control your COSEC access devices using natural language.
      Type a command below or use the sidebar for quick access.
    </div>
    <div class="chips">${CHIPS_HTML}</div>`;
  inner.appendChild(w);
}

// ── Message builders ─────────────────────────────────────────────────────────

function appendUserMsg(text) {
  hideWelcome();
  const row = document.createElement('div');
  row.className = 'msg-row user';
  row.innerHTML = `
    <div class="av user">You</div>
    <div class="msg-body">
      <div class="bubble user">${esc(text)}</div>
      <div class="ts">${time()}</div>
    </div>`;
  document.getElementById('chatInner').appendChild(row);
  scrollBottom();
}

function appendBotMsg(text, status, details) {
  hideWelcome();
  const row = document.createElement('div');
  row.className = 'msg-row bot';

  const isChatbotHelp = details && details.type === 'chatbot_help';
  const icon = STATUS_ICON[status] || '';
  const extra = buildExtra(status, details);

  // chatbot_help responses arrive as trusted HTML from our own backend — render directly.
  const msgContent = isChatbotHelp
    ? text
    : `<span>${icon} ${esc(text)}</span>`;

  row.innerHTML = `
    <div class="av bot"><img class="av-img" src="./public/side_logo.png" alt="" /></div>
    <div class="msg-body">
      <div class="bubble bot ${esc(status)}">
        ${msgContent}
        ${extra}
      </div>
      <div class="ts">${time()} · ${STATUS_LABEL[status] || status}</div>
    </div>`;
  document.getElementById('chatInner').appendChild(row);
  scrollBottom();
}

function buildExtra(_status, details) {
  if (!details) return '';
  let html = '';

  const successes = details.successes || [];
  successes.forEach(s => { html += buildResponsePanel(s); });

  const missing = details.missing_fields || [];
  if (missing.length > 0) {
    const tags = missing.map(f => `<span class="field-tag">${esc(f)}</span>`).join('');
    html += `<div class="missing-row"><span class="missing-label">Missing:</span>${tags}</div>`;
  }

  return html;
}

function buildResponsePanel(s) {
  if (!s.url) return '';

  const isMock = s.mock;
  const typeCls = isMock ? 'mock' : 'real';
  const typeLabel = isMock ? ' Mock' : '🌐 API';

  let html = `<div class="resp-panel ${typeCls}">`;

  // Header: badge + URL + optional HTTP status code
  html += `<div class="resp-header">
    <span class="resp-badge ${typeCls}">${typeLabel}</span>
    <span class="resp-url">${esc(s.url)}</span>`;

  if (s.device_status) {
    const ok = s.device_status >= 200 && s.device_status < 300;
    html += `<span class="resp-status ${ok ? 'ok' : 'err'}">${s.device_status}</span>`;
  }

  html += `</div>`;

  // Response body
  const respText = formatResponse(s.response);
  if (respText !== null) {
    html += `<div class="resp-body" data-resp="${esc(respText)}">
      <div class="resp-toolbar">
        <span class="resp-label">Response</span>
        <button class="copy-btn" onclick="copyResponse(this)">📋 Copy</button>
      </div>
      <pre class="resp-pre">${esc(respText)}</pre>
    </div>`;
  }

  html += `</div>`;
  return html;
}

function formatResponse(resp) {
  if (resp === undefined || resp === null) return null;
  if (typeof resp === 'object') return JSON.stringify(resp, null, 2);
  const s = String(resp);
  try { return JSON.stringify(JSON.parse(s), null, 2); } catch { return s; }
}

function copyResponse(btn) {
  const body = btn.closest('.resp-body');
  if (!body) return;
  navigator.clipboard.writeText(body.dataset.resp).then(() => {
    const prev = btn.textContent;
    btn.textContent = ' Copied';
    setTimeout(() => { btn.textContent = prev; }, 1800);
  }).catch(() => { });
}

// ── Typing indicator ─────────────────────────────────────────────────────────

function showTyping() {
  const row = document.createElement('div');
  row.className = 'typing-row';
  row.id = 'typing';
  row.innerHTML = `
    <div class="av bot"><img class="av-img" src="./public/side_logo.png" alt="" /></div>
    <div class="typing-bubble">
      <div class="tdot"></div><div class="tdot"></div><div class="tdot"></div>
    </div>`;
  document.getElementById('chatInner').appendChild(row);
  scrollBottom();
}

function hideTyping() {
  const t = document.getElementById('typing');
  if (t) t.remove();
}

// ── Pending follow-up state ───────────────────────────────────────────────────

function setPending(val) {
  document.getElementById('pendingBanner').classList.toggle('visible', val);
  document.getElementById('pendingBadge').style.display = val ? 'flex' : 'none';
  document.getElementById('inputBox').placeholder = val
    ? 'Type your answer…'
    : "Type a command…  e.g. 'Add user Jay with id 101'";
}

// ── Clear / reset ─────────────────────────────────────────────────────────────

function clearChat() {
  document.getElementById('chatInner').innerHTML = '';
  showWelcome();
  setPending(false);
}

// ── Theme toggle ──────────────────────────────────────────────────────────────

function toggleTheme() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  document.documentElement.setAttribute('data-theme', isLight ? 'dark' : 'light');
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = isLight ? '☀️' : '🌙';
}

// ── API status badge (no-op — badge removed from UI) ─────────────────────────

function setApiStatus(_online) {
  // API status badge was removed from the header; this is intentionally a no-op.
}
