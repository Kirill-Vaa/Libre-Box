#!/usr/bin/env bash
set -euo pipefail
mkdir -p /usr/share

[ -d /usr/share/seclists ] || git clone --depth 1 https://github.com/danielmiessler/SecLists.git /usr/share/seclists
[ -d /usr/share/payloads ] || git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings.git /usr/share/payloads
[ -d /usr/share/fuzzdb ] || git clone --depth 1 https://github.com/fuzzdb-project/fuzzdb.git /usr/share/fuzzdb
[ -f /usr/share/wordlists/rockyou.txt.gz ] && gunzip -k /usr/share/wordlists/rockyou.txt.gz || true

find /usr/share/seclists /usr/share/payloads /usr/share/fuzzdb -name .git -type d -prune -exec rm -rf {} + 2>/dev/null || true