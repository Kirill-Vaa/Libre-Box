#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
    nmap ncat masscan hydra medusa john hashcat sqlmap nikto whatweb wafw00f \
    dnsutils whois tcpdump tshark termshark ngrep socat netcat-openbsd rlwrap \
    proxychains4 tor torsocks iproute2 net-tools nftables iptables \
    arp-scan arping fping hping3 ethtool mtr-tiny \
    radare2 binwalk foremost scalpel xxd hexedit steghide outguess \
    sleuthkit ssdeep fcrackzip pdfcrack openssl \
    gdb ltrace upx-ucl \
    bettercap ettercap-text-only

KALI="-t kali-rolling -y --no-install-recommends"
for pkg in \
    metasploit-framework responder enum4linux-ng smbmap \
    wpscan wfuzz dirsearch commix dnsrecon dnsenum fierce recon-ng theharvester \
    ncrack patator cewl crunch hashid seclists wordlists \
    volatility3 stegseek zsteg exploitdb rustscan feroxbuster gobuster \
    evil-winrm impacket-scripts bloodhound.py netexec; do
    apt-get install $KALI "$pkg" || echo "kali: skipped $pkg"
done

rm -rf /var/lib/apt/lists/*