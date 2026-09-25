#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec "$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/source/fpga_console.py"




