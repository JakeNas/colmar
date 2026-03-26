#!/usr/bin/env bash
# Setup script for the daily news email digest.
# Run this once on your machine to install and activate the 6am daily job.
#
# Prerequisites:
#   1. Python 3.8+
#   2. A free NewsAPI key from https://newsapi.org
#   3. A Gmail App Password (not your regular password):
#      Google Account → Security → 2-Step Verification → App passwords

set -euo pipefail

SERVICE_FILE="$HOME/.config/systemd/user/daily-news-email.service"
TIMER_FILE="$HOME/.config/systemd/user/daily-news-email.timer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Collect credentials ────────────────────────────────────────────────────────
echo ""
echo "=== Daily News Email Setup ==="
echo ""

read -rp "Gmail address (sender + recipient): " GMAIL_USER
read -rsp "Gmail App Password: " GMAIL_APP_PASS; echo ""
read -rp "NewsAPI key (get one free at https://newsapi.org): " NEWSAPI_KEY

# ── Install systemd units ──────────────────────────────────────────────────────
mkdir -p "$HOME/.config/systemd/user"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Daily News Email Digest

[Service]
Type=oneshot
ExecStart=/usr/bin/env python3 ${SCRIPT_DIR}/daily_news_email.py
StandardOutput=journal
StandardError=journal
Environment="GMAIL_USER=${GMAIL_USER}"
Environment="GMAIL_APP_PASSWORD=${GMAIL_APP_PASS}"
Environment="NEWSAPI_KEY=${NEWSAPI_KEY}"
EOF

cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Run Daily News Email Digest at 6am

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# ── Enable timer ───────────────────────────────────────────────────────────────
systemctl --user daemon-reload
systemctl --user enable --now daily-news-email.timer

echo ""
echo "✓ Timer enabled. Next run:"
systemctl --user list-timers daily-news-email.timer --no-pager

echo ""
echo "To send a test email right now, run:"
echo "  systemctl --user start daily-news-email.service"
echo ""
echo "To view logs:"
echo "  journalctl --user -u daily-news-email.service -f"
