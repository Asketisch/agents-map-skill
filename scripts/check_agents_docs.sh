#!/usr/bin/env bash
# Usage: check_agents_docs.sh [repo_root]; requires Python 3.
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/check_agents_docs.py" "$@"
