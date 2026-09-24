#!/usr/bin/env bash
# Checks for Docker (Linux/macOS) and installs it if missing or not running.
#
# Unlike scripts/start.sh, this DOES modify your system: it installs
# packages (Linux: Docker's official install script; macOS: Homebrew cask),
# may enable/start a system service, and on Linux may add your user to the
# `docker` group. Installing Docker Engine on Linux needs sudo; Docker
# Desktop on macOS cannot be started headlessly and needs a manual first
# launch (license acceptance).
set -euo pipefail

# shellcheck source=scripts/_lib.sh
source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"

usage() {
    cat <<'USAGE'
usage: _install-docker.sh

Installs Docker if it is missing, or starts it if it is installed and not
running. Called by install.sh; run directly only when that is what you want.

  Linux   Docker Engine through Docker's official install script (curl | sudo sh),
          the service enabled and started, your user added to the `docker` group
  macOS   Docker Desktop through Homebrew (a manual first launch is still needed)

This is the one script here that modifies the machine and needs sudo. It takes
no arguments: `--help` prints this and installs nothing.
USAGE
}

# Parsed BEFORE anything runs. Without this, `--help` executed the script -- and
# on a Linux host without Docker that meant `curl | sudo sh` in answer to a
# question (found by the 2026-09-08 audit).
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") ;;
    *) echo "error: unknown argument: $1" >&2; usage >&2; exit 2 ;;
esac

os_name="$(uname -s)"

docker_working() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

if docker_working; then
    echo "Docker is already installed and running."
    exit 0
fi

if command -v docker >/dev/null 2>&1; then
    echo "Docker is installed but the daemon is not running/reachable."
    case "$os_name" in
        Linux)
            echo "Starting the Docker service (requires sudo)..."
            sudo systemctl enable --now docker
            ;;
        Darwin)
            echo "Docker Desktop can't be started headlessly on macOS."
            echo "Open it manually (Applications > Docker, or 'open -a Docker'), wait for it to finish starting, then re-run this script."
            exit 1
            ;;
        *)
            echo "Unsupported OS: $os_name. Start Docker manually."
            exit 1
            ;;
    esac
else
    echo "Docker not found. Installing..."
    case "$os_name" in
        Linux)
            echo "Installing Docker Engine via Docker's official install script (requires sudo)."
            curl -fsSL https://get.docker.com | sudo sh
            sudo systemctl enable --now docker
            # Captured before it is judged: `groups | grep -q` read a `groups` that
            # failed as "not a member", and a word match needs no pipe at all.
            user_groups="$(id -nG "$USER")"
            if [[ " $user_groups " != *" docker "* ]]; then
                sudo usermod -aG docker "$USER"
                echo "Added $USER to the 'docker' group — log out and back in (or run 'newgrp docker') for this to take effect without sudo."
            fi
            ;;
        Darwin)
            if command -v brew >/dev/null 2>&1; then
                echo "Installing Docker Desktop via Homebrew..."
                brew install --cask docker
                echo "Docker Desktop installed. Open it (Applications > Docker, or 'open -a Docker'), accept its terms, wait for it to finish starting, then re-run this script to verify."
                exit 0
            else
                echo "error: Homebrew not found, cannot install automatically."
                echo "Download Docker Desktop manually: https://www.docker.com/products/docker-desktop/"
                exit 1
            fi
            ;;
        *)
            echo "error: unsupported OS: $os_name. Install Docker manually: https://docs.docker.com/get-docker/"
            exit 1
            ;;
    esac
fi

echo "Verifying..."
if docker_working; then
    echo "Docker is installed and running."
else
    echo "Docker was installed/started, but is not yet usable in this shell."
    echo "On Linux, this is usually the docker-group change above — log out and back in (or run 'newgrp docker'), then re-run this script."
    exit 1
fi
