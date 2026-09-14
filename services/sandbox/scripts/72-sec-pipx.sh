#!/usr/bin/env bash
set -euo pipefail
export PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/opt/pipx/bin

for tool in \
    impacket certipy-ad coercer lsassy pypykatz \
    ldapdomaindump name-that-hash arjun \
    scoutsuite prowler checkov \
    sherlock-project maigret holehe \
    droopescan sublist3r \
    frida-tools; do
    pipx install "$tool" || echo "pipx-sec: skipped $tool"
done