#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
source /tmp/versions.env

apt-get update
apt-get install -y --no-install-recommends \
    pandoc texlive-full latexmk libreoffice \
    poppler-utils qpdf ghostscript img2pdf mupdf-tools pdftk-java \
    wkhtmltopdf google-chrome-stable graphviz plantuml
rm -rf /var/lib/apt/lists/*

cat > /usr/local/bin/chrome-no-sandbox <<'WRAPPER'
#!/usr/bin/env bash
exec /usr/bin/google-chrome-stable --no-sandbox --disable-dev-shm-usage "$@"
WRAPPER
chmod +x /usr/local/bin/chrome-no-sandbox

curl -fsSL https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz -o /tmp/typst.txz
tar -xf /tmp/typst.txz -C /tmp && mv /tmp/typst-*/typst /usr/local/bin/typst && rm -rf /tmp/typst*

curl -fsSL "https://github.com/terrastruct/d2/releases/download/v${D2_VERSION}/d2-v${D2_VERSION}-linux-amd64.tar.gz" -o /tmp/d2.tgz
tar -xzf /tmp/d2.tgz -C /tmp && mv /tmp/d2-*/bin/d2 /usr/local/bin/d2 && rm -rf /tmp/d2*