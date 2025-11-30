#!/bin/bash
set -e

VERSION="0.1.0"
REPO="r-seize/filegen"

echo "[INFO] Installing FileGen v${VERSION}"

if command -v pip3 &> /dev/null; then
    pip3 install --user "https://github.com/${REPO}/archive/v${VERSION}.tar.gz"
    echo "[OK] FileGen installed!"
    echo "[INFO] Make sure ~/.local/bin is in your PATH"
    echo "      Add to ~/.bashrc or ~/.zshrc:"
    echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
else
    echo "[ERROR] pip3 not found. Please install Python 3"
    exit 1
fi
