/**
 * config.js — single source of truth for frontend settings
 *
 * Frontend team: change API_BASE to point at your device or server.
 * Examples:
 *   'http://127.0.0.1:8000'          — local dev
 *   'http://192.168.1.100:8000'       — company LAN server
 */
const CONFIG = {
  API_BASE:           'http://127.0.0.1:8000',
  HEALTH_INTERVAL_MS: 30_000,
  MAX_CHARS:          5_000,
};
