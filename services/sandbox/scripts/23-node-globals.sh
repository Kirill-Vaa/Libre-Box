#!/usr/bin/env bash
set -euo pipefail
source /etc/profile.d/10-toolchains.sh

/opt/node/bin/npm install -g \
    @mermaid-js/mermaid-cli @marp-team/marp-cli decktape repomix \
    typescript ts-node prettier eslint