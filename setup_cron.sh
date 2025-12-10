#!/bin/bash

# Setup cron job for Odoo health monitoring
# Runs health check every 15 minutes and sends email alerts if offline/error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
HEALTH_MONITOR="$BACKEND_DIR/health_monitor.py"
LOG_FILE="$BACKEND_DIR/health_monitor.log"

echo "========================================"
echo "Odoo Health Monitor - Cron Setup"
echo "========================================"

# Check if health_monitor.py exists
if [ ! -f "$HEALTH_MONITOR" ]; then
    echo "Error: health_monitor.py not found at $HEALTH_MONITOR"
    exit 1
fi

# Check if .env exists
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "Warning: .env file not found at $BACKEND_DIR/.env"
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp $BACKEND_DIR/.env.example $BACKEND_DIR/.env"
    echo ""
fi

# Find uv path (cron doesn't have user's PATH)
UV_PATH=$(which uv 2>/dev/null)
if [ -z "$UV_PATH" ]; then
    # Common locations
    if [ -f "$HOME/.local/bin/uv" ]; then
        UV_PATH="$HOME/.local/bin/uv"
    elif [ -f "/usr/local/bin/uv" ]; then
        UV_PATH="/usr/local/bin/uv"
    else
        echo "Error: uv not found. Please install uv first."
        exit 1
    fi
fi

echo "Found uv at: $UV_PATH"

# Create the cron job command with full path to uv
CRON_CMD="*/15 * * * * cd $BACKEND_DIR && $UV_PATH run python health_monitor.py >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "health_monitor.py"; then
    echo "Cron job already exists. Updating..."
    # Remove existing health_monitor cron job
    crontab -l 2>/dev/null | grep -v "health_monitor.py" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "Cron job installed successfully!"
echo ""
echo "Details:"
echo "  Schedule: Every 15 minutes"
echo "  Script:   $HEALTH_MONITOR"
echo "  Log file: $LOG_FILE"
echo "  UV path:  $UV_PATH"
echo ""
echo "Current cron jobs:"
crontab -l | grep "health_monitor"
echo ""
echo "To remove this cron job, run:"
echo "  crontab -l | grep -v 'health_monitor.py' | crontab -"
echo ""
echo "To test the health monitor manually:"
echo "  cd $BACKEND_DIR && $UV_PATH run python health_monitor.py"
