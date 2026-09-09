#!/usr/bin/env bash
# ============================================================
# TECHIE SaaS — Cloud Agent environment install script
# Idempotent: creates a per-service Python virtualenv, installs
# dependencies, and downloads the Playwright Chromium browser
# used by コトミガキ (aio2-main).
# ============================================================
set -euo pipefail

# Always run from the repository root (this file lives in <repo>/.cursor).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Installing system packages (OpenCV / WeasyPrint / fonts / venv)"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  python3-venv python3-dev build-essential \
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
  libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev libcairo2 shared-mime-info \
  fonts-noto-cjk

# Create a virtualenv and install a service's deps + the shared module deps.
install_service() {
  local svc="$1"
  echo "==> [$svc] creating virtualenv and installing dependencies"
  python3 -m venv "$svc/.venv"
  "$svc/.venv/bin/pip" install --upgrade --quiet pip wheel setuptools
  "$svc/.venv/bin/pip" install --quiet -r "$svc/requirements.txt" -r shared/requirements.txt
}

install_service notecode
install_service kotomegane
install_service aio2-main

echo "==> [aio2-main] installing Playwright system deps + Chromium"
# stdin redirected from /dev/null so the driver never blocks on a TTY.
sudo "$REPO_ROOT/aio2-main/.venv/bin/playwright" install-deps chromium </dev/null
"$REPO_ROOT/aio2-main/.venv/bin/playwright" install chromium </dev/null

echo "==> Install complete"
