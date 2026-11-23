#!/bin/sh
# Double-click in Finder to install or upgrade Fathom for this user (spec 031).
sh "$(dirname "$0")/install-fathom.sh" "$@"
status=$?
echo
echo "You can close this window."
exit $status
