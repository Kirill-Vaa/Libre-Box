#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
    fontconfig \
    fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji fonts-noto-extra \
    fonts-dejavu fonts-liberation fonts-liberation2 fonts-freefont-ttf fonts-firacode fonts-jetbrains-mono

fc-cache -f || true

rm -rf /var/lib/apt/lists/*