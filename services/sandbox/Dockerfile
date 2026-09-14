FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    TZ=UTC \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rust \
    GOROOT=/opt/go \
    GOPATH=/opt/gopath \
    PYENV_ROOT=/opt/pyenv \
    PIPX_HOME=/opt/pipx \
    PIPX_BIN_DIR=/opt/pipx/bin \
    XDG_CACHE_HOME=/opt/state/cache \
    HISTFILE=/opt/state/bash_history

ENV PATH="/opt/pytools/bin:/opt/pipx/bin:/opt/cargo/bin:/opt/go/bin:/opt/gopath/bin:/opt/node/bin:/opt/dotnet:/opt/julia/bin:${PATH}"

RUN mkdir -p /opt/state /root/data /root/.box/logs

COPY config/profile.d/10-toolchains.sh /etc/profile.d/10-toolchains.sh
COPY config/versions.env /tmp/versions.env
COPY scripts/ /tmp/scripts/
RUN chmod +x /tmp/scripts/*.sh

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked /tmp/scripts/00-apt-core.sh
RUN /tmp/scripts/10-repos.sh
RUN /tmp/scripts/04-fonts.sh
RUN /tmp/scripts/05-cli.sh
RUN /tmp/scripts/20-languages.sh
RUN /tmp/scripts/21-python-libs.sh
RUN /tmp/scripts/22-python-clis.sh
RUN /tmp/scripts/23-node-globals.sh
RUN /tmp/scripts/25-cargo-tools.sh
RUN /tmp/scripts/30-docs.sh
RUN /tmp/scripts/40-media.sh
RUN /tmp/scripts/50-databases.sh
RUN /tmp/scripts/60-cloud.sh
RUN /tmp/scripts/70-sec-apt.sh
RUN /tmp/scripts/71-sec-go.sh
RUN /tmp/scripts/72-sec-pipx.sh
RUN /tmp/scripts/73-sec-manual.sh
RUN /tmp/scripts/74-sec-wordlists.sh
RUN /opt/node/bin/npm install -g repomix && /opt/pipx/bin/pipx install files-to-prompt llm ttok || true
RUN /tmp/scripts/90-cleanup.sh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /root/data

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD test -f /root/.box/ready || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]