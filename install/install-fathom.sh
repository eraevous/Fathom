#!/bin/sh
# Fathom per-user installer for macOS and Linux (spec 031). No admin rights needed.
# Usage: sh install-fathom.sh [--dry-run | --uninstall] [--extras stats,exports]
here=$(cd "$(dirname "$0")" && pwd)
for candidate in python3.14 python3.13 python3.12 python3.11 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 python3; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    exec "$candidate" "$here/fathom_install.py" "$@"
  fi
done
echo "Fathom needs Python 3.11 or newer, and none was found."
echo "macOS: install it from https://www.python.org/downloads/macos/ (that installer asks for an"
echo "administrator password; ask IT if you have none). Linux: use your distribution's python3.11+ package."
exit 1
