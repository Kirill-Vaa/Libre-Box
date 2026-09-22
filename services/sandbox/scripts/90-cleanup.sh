#!/usr/bin/env bash
set -euo pipefail

rm -rf /var/lib/apt/lists/* /root/.cache /root/.npm /opt/cargo/registry /opt/cargo/git /opt/gopath/pkg/mod /opt/state/cache
find /opt/pipx /opt/pytools -name '__pycache__' -type d -prune -exec rm -rf {} +