#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 mao1ix
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
YTM_HOME="${YTM_HOME:-$HOME/.local/share/ytm}"
TARGET="opencode"

usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Options:
  --opencode     Install the skill + /music command for OpenCode (default)
  --claude       Install the skill for Claude Code
  --all          Install for both OpenCode and Claude Code
  --no-skill     Install only the ytm CLI
  -h, --help     Show this help

Environment:
  YTM_HOME       Data/install directory (default: ~/.local/share/ytm)
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --opencode) TARGET="opencode" ;;
    --claude) TARGET="claude" ;;
    --all) TARGET="all" ;;
    --no-skill) TARGET="none" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

missing=0
for cmd in python3 mpv yt-dlp; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing dependency: $cmd" >&2
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  cat >&2 <<'EOF'

Install the missing tools first:
  Arch Linux:      sudo pacman -S python mpv yt-dlp ffmpeg
  Debian/Ubuntu:   sudo apt install python3 python3-venv mpv yt-dlp ffmpeg
  Fedora:          sudo dnf install python3 mpv yt-dlp ffmpeg
  macOS (Homebrew): brew install python mpv yt-dlp ffmpeg

Then rerun ./install.sh
EOF
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Note: ffmpeg is not installed; most audio formats still work, but some may not." >&2
fi

echo "Installing ytm into $YTM_HOME ..."
mkdir -p "$YTM_HOME"
chmod 700 "$YTM_HOME"
if [ ! -x "$YTM_HOME/venv/bin/python" ]; then
  if ! python3 -m venv "$YTM_HOME/venv"; then
    echo "Could not create a Python virtual environment." >&2
    echo "On Debian/Ubuntu install python3-venv, then rerun." >&2
    exit 1
  fi
fi

"$YTM_HOME/venv/bin/python" -m pip install --quiet --upgrade pip
"$YTM_HOME/venv/bin/python" -m pip install --quiet -r "$REPO_DIR/requirements.txt"
install -m 755 "$REPO_DIR/ytm.py" "$YTM_HOME/ytm.py"

mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/ytm" <<EOF
#!/usr/bin/env bash
YTM_HOME="\${YTM_HOME:-$YTM_HOME}"
exec "\$YTM_HOME/venv/bin/python" "\$YTM_HOME/ytm.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/ytm"

install_opencode() {
  local config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
  install -d "$config_dir/skills/youtube-music"
  install -m 644 "$REPO_DIR/SKILL.md" "$config_dir/skills/youtube-music/SKILL.md"
  install -d "$config_dir/command"
  install -m 644 "$REPO_DIR/commands/music.md" "$config_dir/command/music.md"
  echo "Installed OpenCode skill: $config_dir/skills/youtube-music"
  echo "Installed OpenCode command: $config_dir/command/music.md"
}

install_claude() {
  local claude_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  install -d "$claude_dir/skills/youtube-music"
  install -m 644 "$REPO_DIR/SKILL.md" "$claude_dir/skills/youtube-music/SKILL.md"
  echo "Installed Claude Code skill: $claude_dir/skills/youtube-music"
}

case "$TARGET" in
  opencode) install_opencode ;;
  claude) install_claude ;;
  all) install_opencode; install_claude ;;
  none) ;;
esac

echo
echo "Installed: $HOME/.local/bin/ytm"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "Add ~/.local/bin to PATH to use the short 'ytm' command." ;;
esac
echo "Try: ytm doctor && ytm play \"Tame Impala\""
