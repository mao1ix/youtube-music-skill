---
name: youtube-music
description: Search and play music on YouTube Music, control playback (pause/resume/next/previous/volume/seek), queue albums and playlists, and check what is currently playing. Use when the user asks to play, search for, or control music, especially "YouTube Music", "YTM", "song", "album", or "playlist".
---

# YouTube Music

## Overview

`ytm` is a local CLI that wraps `ytmusicapi` for YouTube Music search/metadata and `mpv` + `yt-dlp` for background audio playback over a local JSON IPC socket.

If `ytm` is not on `PATH`, run `~/.local/bin/ytm`. If it was installed to a custom directory, set `YTM_HOME` accordingly.

## When to Use

- Searching YouTube Music for songs, videos, albums, artists, or playlists
- Playing a track, URL, album (`browseId`), or playlist (`playlistId`) in the background
- Controlling active playback (`status`, `pause`, `resume`, `toggle`, `next`, `prev`, `volume`, `seek`, `stop`)
- Checking local dependencies and playback state with `ytm doctor`

## Quick Start

```bash
# Search
ytm search "query" --limit 10
ytm search "query" --type songs|videos|albums|artists|playlists

# Play
ytm play "song or artist query"      # search songs, play the first match
ytm play-url "https://..."           # play an http(s) or ytdl:// URL
ytm play-playlist PLAYLIST_ID        # queue up to 50 tracks
ytm play-album BROWSE_ID             # queue a full album

# Control playback
ytm status
ytm pause
ytm resume
ytm toggle
ytm next
ytm prev
ytm volume 65
ytm seek 42
ytm stop

# Diagnostics
ytm doctor
```

## Workflow

1. For direct song requests (`"play Tame Impala"`), run `ytm play "<query>"`.
2. For albums or playlists, run `ytm search "<query>" --type albums` (or `playlists`), grab `browseId` (or `playlistId`), and pass it to `ytm play-album` (or `ytm play-playlist`).
3. Confirm playback state or current track metadata with `ytm status`.

## Output Format

All commands output JSON (`now_playing`, `status`, search result arrays, or `{"error": "..."}` on failure).
Search results include `title`, `artist`, `album`, `duration`, `videoId`, `url`, `playlistId`, and `browseId` when available.
`status` returns `running`, `idle`, `paused`, `title`, `artist`, `album`, `position`, `duration`, `volume`, `playlist_position`, and `playlist_count`.

## Anti-Patterns

- Do not start playback unless the user asks to play something; searching or answering a question about a song should not trigger audio.
- Do not pass raw search text to `play-album` or `play-playlist`; look up `browseId` or `playlistId` with `ytm search` first.
- Do not use this project to download media or bypass access controls; it is an unofficial local player and users must follow YouTube's Terms of Service.

## Notes

- Search and public playback work anonymously. For personal library and private playlists, set `YT_CLIENT_ID` and `YT_CLIENT_SECRET` and run `ytm auth`.
- Playback logs are written to `$YTM_HOME/mpv.log` (default `~/.local/share/ytm/mpv.log`).
- The IPC socket is `$XDG_RUNTIME_DIR/ytm-mpv.sock` when available, otherwise `$YTM_HOME/ytm-mpv.sock`.
- Set `YTM_AO=null` to test playback silently.
