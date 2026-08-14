#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -n "${PYTHON:-}" ]; then
    PYTHON_COMMAND=$PYTHON
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_COMMAND=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_COMMAND=python
else
    echo "Python 3 is required; no audit was run." >&2
    exit 2
fi

exec "$PYTHON_COMMAND" "$SCRIPT_DIR/sanitize.py" "$@"
