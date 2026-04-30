/**
 * api.js — all HTTP calls to the backend
 *
 * CONTRACT (what the backend expects and returns):
 *
 * POST /chat
 *   Request  : { "text": string, "session_id": string }
 *   Response : {
 *     "status":  "success" | "error" | "need_input" | "partial_success",
 *     "message": string,
 *     "details": {
 *       "successes":      [{ "url": string, "mock": boolean }],
 *       "missing_fields": [string],
 *       "reason":         string
 *     }
 *   }
 *
 * GET /health
 *   Response : { "status": "healthy", "service": "...", "version": "..." }
 *
 * session_id:
 *   Generated once per browser tab (see app.js → getSessionId).
 *   The backend uses it as a LangGraph thread_id so each tab has
 *   completely isolated multi-turn conversation state.
 */

async function chatRequest(text, sessionId) {
  const res = await fetch(`${CONFIG.API_BASE}/chat`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ text, session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function healthRequest() {
  const res = await fetch(`${CONFIG.API_BASE}/health`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
