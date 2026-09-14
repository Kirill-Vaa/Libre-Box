#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
    build-essential gcc g++ make cmake pkg-config \
    ca-certificates curl wget gnupg lsb-release apt-transport-https software-properties-common \
    git git-lfs openssh-client rsync \
    unzip zip xz-utils zstd bzip2 \
    procps psmisc lsof strace file less nano \
    locales tzdata bash-completion tmux tini \
    ripgrep jq

sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen || true
locale-gen en_US.UTF-8 || true

rm -rf /var/lib/apt/lists/*