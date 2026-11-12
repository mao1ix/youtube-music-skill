# ytm — an unofficial YouTube Music CLI for AI agents

A tiny, local, unofficial YouTube Music CLI + agent skill. Search, play, and control music from your terminal.

`ytm` uses [`ytmusicapi`](https://github.com/sigma67/ytmusicapi) for search and metadata, and `mpv` + `yt-dlp` for audio playback. Everything is controlled over a local IPC socket, and every command prints JSON, so it works nicely for both humans and AI coding agents.

```
$ ytm play "The Less I Know the Better"
{
  "now_playing": {
    "title": "The Less I Know the Better",
    "artist": "Tame Impala",
    "album": "Currents",
    "duration": "3:36"
  },
  "status": {
    "running": true,
    "paused": false,
    "position": 1.2,
    "volume": 100
  }
}
```

## Features

- Search songs, videos, albums, artists, and playlists
- Play a song by search query, URL, playlist ID, or album ID
- Pause, resume, skip, seek, set volume, and stop
- Queue full playlists and albums (up to 50 tracks by default)
- Audio-only playback in the background
- JSON output for scripting and agents
- Optional OAuth for your personal library and private playlists
- Installs as an OpenCode skill, a Claude Code skill, or just a plain CLI

## Requirements

- Linux or macOS
- Python 3.10+
- [`mpv`](https://mpv.io/)
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
- `ffmpeg` (recommended; some formats need it)

These are separate projects and are not bundled with `ytm`. Their licenses and terms apply; see [THIRD_PARTY.md](THIRD_PARTY.md).

Install the system dependencies:

```bash
# Arch Linux
sudo pacman -S python mpv yt-dlp ffmpeg

# Debian / Ubuntu
sudo apt install python3 python3-venv mpv yt-dlp ffmpeg

# Fedora
sudo dnf install python3 mpv yt-dlp ffmpeg

# macOS (Homebrew)
brew install python mpv yt-dlp ffmpeg
```

## Install

```bash
git clone https://github.com/mao1ix/youtube-music-skill.git
cd youtube-music-skill
./install.sh
```

By default this installs the CLI to `~/.local/bin/ytm`, its data to `~/.local/share/ytm`, and the skill + `/music` command for OpenCode.

Other targets:

```bash
./install.sh --claude     # Claude Code skill
./install.sh --all        # OpenCode + Claude Code
./install.sh --no-skill   # CLI only
```

Use a custom data directory:

```bash
YTM_HOME="$HOME/.ytm" ./install.sh
```

Make sure `~/.local/bin` is on your `PATH`, then check the install:

```bash
ytm doctor
```

## Quick start

```bash
# Search
ytm search "Suki Waterhouse" --limit 5
ytm search "Currents" --type albums

# Play the first matching song
ytm play "Good Looking"

# Play a URL, playlist, or album
ytm play-url "https://music.youtube.com/watch?v=..."
ytm play-playlist PLAYLIST_ID
ytm play-album BROWSE_ID

# Control playback
ytm status
ytm pause
ytm resume
ytm next
ytm prev
ytm volume 65
ytm seek 42
ytm stop
```

`search` returns `playlistId` for playlists and `browseId` for albums, so you can feed those IDs directly into `play-playlist` and `play-album`.

## Use with AI agents

### OpenCode

`./install.sh` installs:

- `~/.config/opencode/skills/youtube-music/SKILL.md`
- `~/.config/opencode/command/music.md`

Then ask your agent to play something, or use:

```
/music play some Tame Impala
/music what's playing?
```

### Claude Code

```bash
./install.sh --claude
```

This installs the skill to `~/.claude/skills/youtube-music/SKILL.md`.

The skill tells the agent when to use `ytm`, how to search, and how to control playback. It also tells the agent not to start music unless you actually ask for it.

## How it works

```
ytm search  ->  ytmusicapi  ->  YouTube Music
ytm play    ->  mpv + yt-dlp  ->  audio
ytm status  ->  mpv JSON IPC  ->  playback state
```

- Playback runs as a detached `mpv` process.
- The IPC socket is `$XDG_RUNTIME_DIR/ytm-mpv.sock`, or `$YTM_HOME/ytm-mpv.sock` when `XDG_RUNTIME_DIR` is unavailable.
- `mpv` is started with YouTube's `android` client through `yt-dlp` to reduce bot checks.
- Logs go to `$YTM_HOME/mpv.log` (default `~/.local/share/ytm/mpv.log`).
- `YTM_AO=null` makes playback silent, which is useful for testing.

## Optional: personal library / OAuth

Search and public playback work anonymously. For your library, private playlists, and personalized results, create a Google Cloud OAuth client and run:

```bash
export YT_CLIENT_ID="your-client-id"
export YT_CLIENT_SECRET="your-client-secret"
ytm auth
```

The OAuth token is stored at `$YTM_HOME/oauth.json` and is git-ignored. Treat it like a password.

## Troubleshooting

**No sound**

```bash
ytm doctor
ytm status
tail -n 50 ~/.local/share/ytm/mpv.log
```

Check that `mpv` can play audio outside `ytm`:

```bash
mpv --no-video "https://music.youtube.com/watch?v=..."
```

**mpv exits immediately or YouTube asks for a bot check**

Update `yt-dlp` first:

```bash
yt-dlp -U
# or, with a package manager:
sudo pacman -S yt-dlp
```

Then run `ytm stop` and try again. A yt-dlp compatibility extractor option is enabled by default; update `yt-dlp` if YouTube changes its behavior.

**`ytm` command not found**

Add `~/.local/bin` to your `PATH`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Test without making noise**

```bash
YTM_AO=null ytm play "Tame Impala"
```

## Uninstall

```bash
./uninstall.sh
```

This removes the CLI, its data, and the installed skills/command. It does not remove `mpv`, `yt-dlp`, or `ffmpeg`.

## AI assistance

This project was built with AI assistance. An AI coding assistant drafted the code, documentation, and commit messages; the maintainer directed the work and is responsible for the final result.

## Legal

This is an **unofficial** project. It is not affiliated with, endorsed by, sponsored by, or approved by Google LLC, YouTube, or the `ytmusicapi` project. "YouTube", "YouTube Music", and related marks are trademarks of Google LLC. The repository contains no music, video, or OAuth credentials.

Use `ytm` only for lawful, personal playback of content you are entitled to access. You are responsible for complying with YouTube's Terms of Service, copyright law, and the licenses and terms of the third-party tools you install.

Read the full [Disclaimer and acceptable use](DISCLAIMER.md), [Privacy](PRIVACY.md), [Third-party notices](THIRD_PARTY.md), [license compliance review](COMPLIANCE.md), [attribution notice](NOTICE), and [Security policy](SECURITY.md).

This documentation is not legal advice. If you plan to commercialize or redistribute this project, consult a qualified lawyer in your jurisdiction.

## License

MIT. See [LICENSE](LICENSE).
