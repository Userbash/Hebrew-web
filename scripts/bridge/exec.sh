#!/bin/bash

# Secure Bridge Executor
# This script enforces the whitelist of allowed host commands.

WHITELIST_FILE="$(dirname "$0")/whitelist.txt"

# Default whitelist if none exists
if [ ! -f "$WHITELIST_FILE" ]; then
    cat <<EOF > "$WHITELIST_FILE"
git
podman
docker
systemctl
npm
node
ls
which
cat
EOF
fi

COMMAND=$1
shift

if grep -Fxq "$COMMAND" "$WHITELIST_FILE"; then
    # Run the command through the bridge
    "$(dirname "$0")/bridge.sh" "$COMMAND" "$@"
else
    echo "--------------------------------------------------------"
    echo "Access Denied: Command '$COMMAND' is not in the bridge whitelist."
    echo "This IDE environment is isolated for security."
    echo ""
    echo "To grant access, run the following command on the HOST:"
    echo "echo '$COMMAND' >> /var/home/sanya/Hebrew-web/scripts/bridge/whitelist.txt"
    echo "--------------------------------------------------------"
    exit 1
fi
