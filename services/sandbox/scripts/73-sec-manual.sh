#!/usr/bin/env bash
set -euo pipefail
source /tmp/versions.env
mkdir -p /opt/tools

curl -fsSL "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/ghidra_${GHIDRA_VERSION}_PUBLIC_${GHIDRA_DATE}.zip" -o /tmp/ghidra.zip
unzip -q /tmp/ghidra.zip -d /opt && mv "/opt/ghidra_${GHIDRA_VERSION}_PUBLIC" /opt/ghidra && rm -f /tmp/ghidra.zip
ln -sf /opt/ghidra/ghidraRun /usr/local/bin/ghidra

curl -fsSL "https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip" -o /tmp/jadx.zip
mkdir -p /opt/jadx && unzip -q /tmp/jadx.zip -d /opt/jadx && ln -sf /opt/jadx/bin/jadx /usr/local/bin/jadx && rm -f /tmp/jadx.zip

curl -fsSL "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" -o /opt/tools/apktool.jar
printf '#!/usr/bin/env bash\njava -jar /opt/tools/apktool.jar "$@"\n' > /usr/local/bin/apktool && chmod +x /usr/local/bin/apktool

curl -fsSL "https://github.com/BishopFox/sliver/releases/download/v${SLIVER_VERSION}/sliver-client_linux-amd64" -o /usr/local/bin/sliver-client && chmod +x /usr/local/bin/sliver-client
curl -fsSL "https://github.com/BishopFox/sliver/releases/download/v${SLIVER_VERSION}/sliver-server_linux-amd64" -o /usr/local/bin/sliver-server && chmod +x /usr/local/bin/sliver-server
curl -fsSL "https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_linux_amd64.gz" -o /tmp/chisel.gz && gunzip -f /tmp/chisel.gz && mv /tmp/chisel /usr/local/bin/chisel && chmod +x /usr/local/bin/chisel
curl -fsSL "https://github.com/nicocha30/ligolo-ng/releases/download/v${LIGOLO_NG_VERSION}/ligolo-ng_agent_${LIGOLO_NG_VERSION}_linux_amd64.tar.gz" -o /tmp/ligolo.tgz && tar -xzf /tmp/ligolo.tgz -C /usr/local/bin agent && mv /usr/local/bin/agent /usr/local/bin/ligolo-agent && rm -f /tmp/ligolo.tgz

curl -fsSL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
curl -fsSL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
curl -fsSL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" -o /tmp/gl.tgz && tar -xzf /tmp/gl.tgz -C /usr/local/bin gitleaks && rm -f /tmp/gl.tgz