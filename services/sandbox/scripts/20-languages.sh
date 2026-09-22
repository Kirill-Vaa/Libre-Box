#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
source /etc/profile.d/10-toolchains.sh
source /tmp/versions.env

apt-get update
apt-get install -y --no-install-recommends \
    python3 python3-dev python3-venv python3-pip pipx \
    ruby-full php-cli php-curl php-mbstring perl lua5.4 luarocks r-base \
    openjdk-${JAVA_VERSION}-jdk maven gradle
rm -rf /var/lib/apt/lists/*

curl -fsSL https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/opt/cargo/bin sh
pipx install poetry
git clone --depth 1 https://github.com/pyenv/pyenv.git "$PYENV_ROOT"
git clone --depth 1 https://github.com/rbenv/rbenv.git /opt/rbenv

curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tgz
rm -rf /opt/go && tar -C /opt -xzf /tmp/go.tgz && rm -f /tmp/go.tgz
mkdir -p /opt/gopath/bin

curl -fsSL https://sh.rustup.rs | sh -s -- -y --no-modify-path --default-toolchain "$RUST_CHANNEL"
/opt/cargo/bin/cargo install cargo-binstall --root /opt/cargo || true

curl -fsSL https://fnm.vercel.app/install | env SHELL=bash bash -s -- --install-dir /opt/fnm --skip-shell
export PATH="/opt/fnm:$PATH"
eval "$(/opt/fnm/fnm env --shell bash)"
/opt/fnm/fnm install "$NODE_VERSION"
/opt/fnm/fnm default "$NODE_VERSION"
ln -sfn "$(/opt/fnm/fnm exec --using="$NODE_VERSION" which node | xargs dirname | xargs dirname)" /opt/node
/opt/node/bin/npm install -g pnpm yarn

curl -fsSL https://bun.sh/install | env BUN_INSTALL=/opt/bun bash
ln -sf /opt/bun/bin/bun /opt/node/bin/bun || true
curl -fsSL https://deno.land/install.sh | env DENO_INSTALL=/opt/deno sh
ln -sf /opt/deno/bin/deno /usr/local/bin/deno || true

curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
bash /tmp/dotnet-install.sh --channel "$DOTNET_CHANNEL" --install-dir /opt/dotnet && rm -f /tmp/dotnet-install.sh

curl -fsSL "https://github.com/PowerShell/PowerShell/releases/download/v${POWERSHELL_VERSION}/powershell-${POWERSHELL_VERSION}-linux-x64.tar.gz" -o /tmp/pwsh.tgz
mkdir -p /opt/pwsh && tar -xzf /tmp/pwsh.tgz -C /opt/pwsh && rm -f /tmp/pwsh.tgz && ln -sf /opt/pwsh/pwsh /usr/local/bin/pwsh

curl -fsSL "https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_VERSION%.*}/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" -o /tmp/julia.tgz
mkdir -p /opt/julia && tar -xzf /tmp/julia.tgz -C /opt/julia --strip-components=1 && rm -f /tmp/julia.tgz

/opt/node/bin/npm cache clean --force
rm -rf /opt/cargo/registry /opt/cargo/git /opt/state/cache/pip /opt/state/cache/uv