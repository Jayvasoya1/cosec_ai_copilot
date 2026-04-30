/**
 * ui.js — all DOM building and visual state
 * No business logic here — only "how things look"
 */

const STATUS_ICON  = { success: '✅', error: '❌', need_input: '🔔', partial_success: '⚠️' };
const STATUS_LABEL = { success: 'Success', error: 'Error', need_input: 'Input needed', partial_success: 'Partial success' };

const CHIPS_HTML = `
  <div class="chip" onclick="sendSuggestion('Add user Jay with id 101')">➕ Add user</div>
  <div class="chip" onclick="sendSuggestion('Delete user with id 5')">🗑 Delete user</div>
  <div class="chip" onclick="sendSuggestion('Get enroll options')">📋 Get enroll options</div>
  <div class="chip" onclick="sendSuggestion('Set enroll finger count to 3')">✏️ Set enroll options</div>
  <div class="chip" onclick="sendSuggestion('Get access setting')">🔑 Get access setting</div>
  <div class="chip" onclick="sendSuggestion('Set access setting work start at 9 00')">⏰ Set access time</div>
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
    <div class="welcome-icon">🔒</div>
    <div class="welcome-title">CoSec AI Copilot</div>
    <div class="welcome-desc">
      Control your COSEC access devices using natural language.
      Type a command below or pick a suggestion.
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

  const icon  = STATUS_ICON[status]  || 'ℹ️';
  const extra = buildExtra(status, details);

  row.innerHTML = `
    <div class="av bot">🔒</div>
    <div class="msg-body">
      <div class="bubble bot ${esc(status)}">
        <span>${icon} ${esc(text)}</span>
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

  const isMock    = s.mock;
  const typeCls   = isMock ? 'mock' : 'real';
  const typeLabel = isMock ? '🧪 Mock' : '🌐 API';

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
    btn.textContent = '✅ Copied';
    setTimeout(() => { btn.textContent = prev; }, 1800);
  }).catch(() => {});
}

// ── Typing indicator ─────────────────────────────────────────────────────────

function showTyping() {
  const row = document.createElement('div');
  row.className = 'typing-row';
  row.id = 'typing';
  row.innerHTML = `
    <div class="av bot">🔒</div>
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

// ── API status badge ──────────────────────────────────────────────────────────

function setApiStatus(online) {
  document.getElementById('apiDot').className  = online ? 'dot pulse' : 'dot offline';
  document.getElementById('apiText').textContent = online ? 'API Online' : 'API Offline';
}
