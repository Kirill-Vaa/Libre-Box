#!/usr/bin/env bash
set -euo pipefail
source /etc/profile.d/10-toolchains.sh

for crate in xh hyperfine du-dust procs tealdeer jwt-cli websocat; do
    /opt/cargo/bin/cargo-binstall --no-confirm --install-path /opt/cargo/bin "$crate" \
        || /opt/cargo/bin/cargo install "$crate" --root /opt/cargo \
        || echo "cargo: skipped $crate"
done

rm -rf /opt/cargo/registry /opt/cargo/git