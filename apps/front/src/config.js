// Runtime configuration for the static frontend.
//
// In Docker, this file is regenerated at container startup from the
// API_BASE environment variable (see docker-entrypoint.d/40-api-base.sh).
// This committed version is the default used for local development.
//
// Empty string  -> same-origin relative /api/* requests, proxied by Nginx
//                  (the default behavior — no CORS, no hardcoded host).
// Absolute URL  -> e.g. "https://api.example.com", requests go straight
//                  to that host (the API must allow CORS).
window.API_BASE = "";
