#!/usr/bin/env bash
set -euo pipefail

rm -rf /var/lib/apt/lists/* /root/.cache /tmp/* 2>/dev/null || true
find / -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find /opt -name '*.a' -delete 2>/dev/null || true