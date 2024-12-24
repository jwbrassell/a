#!/bin/bash

PID_FILE="vault.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No PID file found. Is Vault running?"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "No Vault process found with PID $PID"
    rm -f "$PID_FILE"
    exit 1
fi

echo "Stopping Vault process (PID: $PID)..."
kill "$PID"

# Wait for process to stop
for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Vault stopped successfully"
        rm -f "$PID_FILE"
        exit 0
    fi
    echo "Waiting for Vault to stop..."
    sleep 1
done

echo "Vault did not stop gracefully, forcing..."
kill -9 "$PID"
rm -f "$PID_FILE"
