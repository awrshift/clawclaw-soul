#!/bin/sh
# Soul Oracle — OpenClaw entrypoint
# 1. Read Docker secrets → export as env vars
# 2. Set up undici proxy agent for Node.js fetch()
# 3. Start the application

set -e

# --- Secrets injection ---
# Docker Compose secrets are mounted as files in /run/secrets/
if [ -f /run/secrets/anthropic_api_key ]; then
    export ANTHROPIC_API_KEY=$(cat /run/secrets/anthropic_api_key)
fi

if [ -f /run/secrets/telegram_bot_token ]; then
    export TELEGRAM_BOT_TOKEN=$(cat /run/secrets/telegram_bot_token)
fi

# --- Proxy setup for Node.js ---
# Node.js native fetch() does NOT respect HTTP_PROXY env vars.
# We inject undici's EnvHttpProxyAgent as the global dispatcher.
if [ -n "$HTTPS_PROXY" ] || [ -n "$HTTP_PROXY" ]; then
    export NODE_OPTIONS="${NODE_OPTIONS} --require /usr/local/lib/node_modules/undici/lib/env-http-proxy-agent.js"
    echo "[entrypoint] Proxy configured: ${HTTPS_PROXY:-$HTTP_PROXY}"
fi

# --- Start application ---
exec "$@"
