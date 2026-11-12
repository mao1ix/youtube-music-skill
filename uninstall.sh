#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 mao1ix
set -euo pipefail

YTM_HOME="${YTM_HOME:-$HOME/.local/share/ytm}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

rm -rf "$YTM_HOME"
rm -f "$HOME/.local/bin/ytm"
rm -rf "$CONFIG_DIR/skills/youtube-music"
rm -f "$CONFIG_DIR/command/music.md"
rm -rf "$CLAUDE_DIR/skills/youtube-music"

echo "Removed ytm, its data, and the installed skill/command."
echo "mpv and yt-dlp were left untouched."
