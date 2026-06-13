#!/bin/sh
# Regenerate config.js from the API_BASE environment variable at container
# startup. The nginx image runs every executable *.sh here before launching.
#
#   API_BASE unset/empty -> same-origin relative /api/* (proxied by Nginx).
#   API_BASE=https://...  -> frontend calls that host directly (needs CORS).
set -eu

: "${API_BASE:=}"

cat > /usr/share/nginx/html/config.js <<EOF
// Generated at container startup from the API_BASE environment variable.
window.API_BASE = "${API_BASE}";
EOF

echo "config.js rendered with API_BASE=\"${API_BASE}\""
