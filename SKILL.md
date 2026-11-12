---
name: YouTube Music
description: Search and play music on YouTube Music, control playback (pause/resume/next/previous/volume/seek), queue albums and playlists, and check what is currently playing. Use when the user asks to play, search for, or control music, especially "YouTube Music", "YTM", "song", "album", or "playlist".
---

# YouTube Music

A local CLI named `ytm` wraps `ytmusicapi` for search and `mpv` + `yt-dlp` for audio playback. It runs in the background and is controlled over mpv's IPC socket.

If `ytm` is not on PATH, use `~/.local/bin/ytm`; if the install lives elsewhere, set `YTM_HOME` to its directory.

All commands print JSON.

## Search

```bash
ytm search "query" --limit 10
ytm search "query" --type songs|videos|albums|artists|playlists
```

Results include `title`, `artist`, `album`, `duration`, `videoId`, `url`, `playlistId`, and `browseId` when available. Use `playlistId` for `play-playlist`, and `browseId` for `play-album`.

## Play

```bash
ytm play "song or artist query"      # search songs, play the first match
ytm play-url "https://..."           # play any URL mpv/yt-dlp supports
ytm play-playlist PLAYLIST_ID        # queue up to 50 tracks
ytm play-album BROWSE_ID             # queue a full album
```

Playback is audio-only and runs in the background. Only start playback when the user asks; don't play something just because they mentioned a song.

## Control

```bash
ytm status
ytm pause
ytm resume
ytm toggle
ytm next
ytm prev
ytm stop
ytm volume 65
ytm seek 42
```

`status` returns `running`, `idle`, `paused`, `title`, `artist`, `album`, `position`, `duration`, `volume`, `playlist_position`, and `playlist_count`.

## Diagnostics

```bash
ytm doctor
```

Checks `python3`, `mpv`, `yt-dlp`, `ffmpeg`, the `ytmusicapi` version, the data directory, OAuth state, and the IPC socket.

## Notes

- Search works anonymously. Personal library and private playlists need OAuth: set `YT_CLIENT_ID` and `YT_CLIENT_SECRET` (a Google Cloud OAuth client), then run `ytm auth`.
- A yt-dlp compatibility extractor option is enabled by default; update `yt-dlp` if YouTube changes its behavior.
- Playback diagnostics are logged to `$YTM_HOME/mpv.log` (default `~/.local/share/ytm/mpv.log`).
- The IPC socket is `$XDG_RUNTIME_DIR/ytm-mpv.sock` when available, otherwise `$YTM_HOME/ytm-mpv.sock`.
- Set `YTM_AO=null` to test playback silently without touching the speakers.
- This is an unofficial client. Use it only for lawful, personal playback and respect YouTube's Terms of Service.
