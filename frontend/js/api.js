/**
 * api.js — all HTTP calls to the backend
 *
 * CONTRACT (what the backend expects and returns):
 *
 * POST /chat
 *   Request  : { "text": string }          (1–5000 chars)
 *   Response : {
 *     "status":  "success" | "error" | "need_input" | "partial_success",
 *     "message": string,                   (human-readable)
 *     "details": {
 *       "successes":      [{ "url": string, "mock": boolean }],
 *       "missing_fields": [string],         (only when status = need_input)
 *       "reason":         string            (only when status = error)
 *     }
 *   }
 *
 * GET /health
 *   Response : { "status": "healthy", "service": "CoSec AI Copilot" }
 */

async function chatRequest(text) {
  const res = await fetch(`${CONFIG.API_BASE}/chat`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function healthRequest() {
  const res = await fetch(`${CONFIG.API_BASE}/health`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
