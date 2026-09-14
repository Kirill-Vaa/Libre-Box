#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
    ffmpeg imagemagick graphicsmagick libvips-tools \
    tesseract-ocr tesseract-ocr-eng tesseract-ocr-rus tesseract-ocr-osd \
    libimage-exiftool-perl librsvg2-bin potrace inkscape \
    optipng jpegoptim pngquant gifsicle webp sox libsndfile1

rm -rf /var/lib/apt/lists/*