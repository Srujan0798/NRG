#!/bin/bash
# ==============================================================================
# wait-for-it.sh - Wait for service availability
# Source: https://github.com/vishnubob/wait-for-it
# ==============================================================================

TIMEOUT=15
QUIET=0

usage() {
    echo "Usage: $0 host:port [-t timeout] [-q]"
    echo "  timeout  : wait timeout in seconds (default: 15)"
    echo "  quiet     : suppress output"
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

HOST_PORT="$1"
shift

while [ $# -gt 0 ]; do
    case "$1" in
        -t)
            TIMEOUT="$2"
            shift 2
            ;;
        -q)
            QUIET=1
            shift
            ;;
        *)
            usage
            ;;
    esac
done

HOST=$(echo "$HOST_PORT" | cut -d: -f1)
PORT=$(echo "$HOST_PORT" | cut -d: -f2)

wait_for() {
    local count=0
    while [ $count -lt $TIMEOUT ]; do
        if nc -z "$HOST" "$PORT" 2>/dev/null; then
            [ $QUIET -eq 0 ] && echo "[wait-for] $HOST:$PORT is available"
            return 0
        fi
        count=$((count + 1))
        [ $QUIET -eq 0 ] && echo "[wait-for] waiting for $HOST:$PORT ($count/$TIMEOUT)"
        sleep 1
    done
    echo "[wait-for] timeout occurred after $TIMEOUT seconds waiting for $HOST:$PORT"
    return 1
}

wait_for