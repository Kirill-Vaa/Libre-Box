#!/usr/bin/env bash
set -euo pipefail
export PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/opt/pipx/bin

for tool in \
    csvkit visidata yt-dlp ocrmypdf weasyprint \
    ttok llm files-to-prompt \
    yamllint ansible-lint; do
    pipx install "$tool" || echo "pipx: skipped $tool"
done

pipx install --include-deps ansible || echo "pipx: skipped ansible"

rm -rf /opt/state/cache/pip
find /opt/pipx -name '__pycache__' -type d -prune -exec rm -rf {} +