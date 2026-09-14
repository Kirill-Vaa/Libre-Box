#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
source /tmp/versions.env

apt-get update
apt-get install -y --no-install-recommends \
    fd-find bat fzf tree htop btop ncdu neovim vim zsh fish direnv \
    parallel pv entr moreutils shellcheck jq gnupg \
    httpie aria2 tmux bash-completion universal-ctags \
    git-delta zoxide eza

ln -sf "$(command -v fdfind)" /usr/local/bin/fd || true
ln -sf "$(command -v batcat)" /usr/local/bin/bat || true

curl -fsSL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -o /usr/local/bin/yq && chmod +x /usr/local/bin/yq
curl -fsSL https://github.com/TomWright/dasel/releases/latest/download/dasel_linux_amd64 -o /usr/local/bin/dasel && chmod +x /usr/local/bin/dasel
curl -fsSL "https://github.com/muesli/duf/releases/download/v${DUF_VERSION}/duf_${DUF_VERSION}_linux_amd64.deb" -o /tmp/duf.deb && apt-get install -y /tmp/duf.deb && rm -f /tmp/duf.deb
curl -fsSL "https://github.com/mvdan/sh/releases/download/v${SHFMT_VERSION}/shfmt_v${SHFMT_VERSION}_linux_amd64" -o /usr/local/bin/shfmt && chmod +x /usr/local/bin/shfmt

rm -rf /var/lib/apt/lists/*