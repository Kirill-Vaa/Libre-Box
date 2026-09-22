#!/usr/bin/env bash
set -euo pipefail
source /etc/profile.d/10-toolchains.sh
export GOBIN=/opt/gopath/bin
GO=/opt/go/bin/go

install_go() { "$GO" install "$1" || echo "go: skipped $1"; }

install_go github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
install_go github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
install_go github.com/projectdiscovery/httpx/cmd/httpx@latest
install_go github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
install_go github.com/projectdiscovery/dnsx/cmd/dnsx@latest
install_go github.com/projectdiscovery/katana/cmd/katana@latest
install_go github.com/ffuf/ffuf/v2@latest
install_go github.com/OJ/gobuster/v3@latest
install_go github.com/tomnomnom/assetfinder@latest
install_go github.com/tomnomnom/waybackurls@latest
install_go github.com/lc/gau/v2/cmd/gau@latest
install_go github.com/hakluke/hakrawler@latest
install_go github.com/owasp-amass/amass/v4/...@master

mv /opt/gopath/bin/httpx /opt/gopath/bin/httpx-pd 2>/dev/null || true

"$GO" clean -cache -modcache