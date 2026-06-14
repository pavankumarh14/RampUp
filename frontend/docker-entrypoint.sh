#!/bin/sh

# Escape slashes and other special characters for sed
ESCAPED_API_URL=$(printf '%s' "${VITE_API_URL:-}" | sed -e 's/[\/&]/\\&/g')

# Replace window.RAMPUP_CONFIG with actual values
cat > /tmp/config.js <<EOF
  window.RAMPUP_CONFIG = {
    VITE_API_URL: "$ESCAPED_API_URL"
  };
EOF

# Replace the placeholder config block in index.html
# Use | as sed delimiter since URL contains /
sed -i.bak -e '/window\.RAMPUP_CONFIG = {/,/};/c\'"$(cat /tmp/config.js)' /usr/share/nginx/html/index.html
rm -f /usr/share/nginx/html/index.html.bak

# Cleanup
rm /tmp/config.js

# Start nginx
exec nginx -g 'daemon off;'
