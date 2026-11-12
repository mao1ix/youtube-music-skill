#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 mao1ix
"""ytm — a tiny YouTube Music CLI for agents and humans.

Search YouTube Music, play audio through mpv, and control playback.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

VERSION = "0.1.2"

try:
    import ytmusicapi
    from ytmusicapi import YTMusic
except ImportError:
    print(json.dumps({
        "error": "ytmusicapi is not installed. Run ./install.sh or pip install ytmusicapi.",
    }))
    sys.exit(1)

try:
    from ytmusicapi import setup_oauth
except ImportError:  # older ytmusicapi releases
    setup_oauth = None

BASE = Path(os.environ.get("YTM_HOME", Path.home() / ".local/share/ytm")).expanduser()
AUTH = BASE / "oauth.json"
LOG = BASE / "mpv.log"


def socket_path() -> Path:
    override = os.environ.get("YTM_SOCKET")
    if override:
        return Path(override).expanduser()
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return Path(runtime) / "ytm-mpv.sock"
    # Keep the fallback socket inside the user-owned data directory rather
    # than a predictable path in a world-writable directory.
    return BASE / "ytm-mpv.sock"


SOCKET = socket_path()


def die(msg: str, code: int = 1):
    print(json.dumps({"error": msg}, ensure_ascii=False, indent=2))
    sys.exit(code)


def get_yt() -> YTMusic:
    if AUTH.exists():
        return YTMusic(str(AUTH))
    return YTMusic()


def artist_names(item: dict) -> str:
    artists = item.get("artists") or []
    names = []
    for artist in artists:
        if isinstance(artist, dict):
            if artist.get("name"):
                names.append(artist["name"])
        elif artist:
            names.append(str(artist))
    return ", ".join(names)


def album_name(item: dict):
    album = item.get("album")
    if isinstance(album, dict):
        return album.get("name")
    return album


def compact(item: dict) -> dict:
    browse = item.get("browseId") or ""
    playlist_id = item.get("playlistId")
    if not playlist_id and browse.startswith("VL"):
        playlist_id = browse[2:]
    video_id = item.get("videoId")
    out = {
        "title": item.get("title"),
        "artist": artist_names(item),
        "album": album_name(item),
        "duration": item.get("duration"),
        "duration_seconds": item.get("duration_seconds"),
        "videoId": video_id,
        "url": f"https://music.youtube.com/watch?v={video_id}" if video_id else None,
        "playlistId": playlist_id,
        "browseId": item.get("browseId"),
        "resultType": item.get("resultType"),
        "year": item.get("year"),
    }
    return {key: value for key, value in out.items() if value not in (None, "")}


def do_search(query: str, kind: str, limit: int) -> list[dict]:
    results = get_yt().search(query, filter=kind, limit=limit) or []
    return [compact(result) for result in results][:limit]


def ipc(command: list, timeout: float = 3.0):
    """Send one command to mpv's JSON IPC socket and return its response."""
    if not SOCKET.exists():
        return None
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(SOCKET))
        request = {"command": command, "request_id": 1}
        sock.sendall((json.dumps(request) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        for line in buf.splitlines():
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("request_id") == 1:
                return obj
        return None
    except (OSError, ValueError):
        return None
    finally:
        sock.close()


def get_prop(name: str):
    response = ipc(["get_property", name])
    if response and response.get("error") == "success":
        return response.get("data")
    return None


def set_prop(name: str, value):
    return ipc(["set_property", name, value])


def mpv_running() -> bool:
    return SOCKET.exists() and ipc(["get_property", "idle-active"]) is not None


def stop_mpv():
    if SOCKET.exists():
        ipc(["quit"])
        for _ in range(30):
            if not SOCKET.exists():
                break
            time.sleep(0.1)
        try:
            SOCKET.unlink()
        except FileNotFoundError:
            pass


def start_mpv(urls: list[str]):
    stop_mpv()
    if shutil.which("mpv") is None:
        die("mpv not found. Install mpv, then run `ytm doctor`.")
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        BASE.chmod(0o700)
    except OSError:
        pass
    LOG.touch(mode=0o600, exist_ok=True)
    try:
        LOG.chmod(0o600)
    except OSError:
        pass
    command = [
        "mpv",
        "--no-video",
        "--force-window=no",
        "--really-quiet",
        "--no-terminal",
        f"--input-ipc-server={SOCKET}",
        "--ytdl-raw-options=extractor-args=youtube:player_client=android",
        "--ytdl-format=bestaudio/best",
    ]
    ao = os.environ.get("YTM_AO")
    if ao:
        command.append(f"--ao={ao}")
    command.extend(urls)
    with LOG.open("ab") as log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
        )
    for _ in range(200):
        if SOCKET.exists():
            return process
        if process.poll() is not None:
            break
        time.sleep(0.1)
    die(f"mpv did not start; see {LOG}")


def status() -> dict:
    if not SOCKET.exists():
        return {"running": False}
    idle = get_prop("idle-active")
    if idle is None:
        return {"running": False}
    metadata = get_prop("metadata") or {}
    return {
        "running": True,
        "idle": bool(idle),
        "paused": bool(get_prop("pause")),
        "title": get_prop("media-title"),
        "artist": metadata.get("Artist") or metadata.get("artist"),
        "album": metadata.get("Album") or metadata.get("album"),
        "position": get_prop("time-pos"),
        "duration": get_prop("duration"),
        "volume": get_prop("volume"),
        "playlist_position": get_prop("playlist-pos"),
        "playlist_count": get_prop("playlist-count"),
    }


def wait_for_playback(timeout: float = 6.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = status()
        if state.get("running") and not state.get("idle") and state.get("duration"):
            return state
        time.sleep(0.2)
    return status()


def play_urls(urls: list[str], meta: dict | None = None):
    if mpv_running():
        ipc(["loadfile", urls[0], "replace"])
        for url in urls[1:]:
            ipc(["loadfile", url, "append"])
    else:
        start_mpv(urls)
    state = wait_for_playback()
    if meta is None:
        meta = {
            key: state.get(key)
            for key in ("title", "artist", "album", "duration")
            if state.get(key)
        }
    return {"now_playing": meta, "status": state}


def song_url(video_id: str) -> str:
    return f"https://music.youtube.com/watch?v={video_id}"


def play_query(query: str):
    songs = do_search(query, "songs", 5)
    if not songs:
        songs = do_search(query, "videos", 5)
    for song in songs:
        if song.get("videoId"):
            return play_urls([song_url(song["videoId"])], song)
    die(f"no playable results for: {query}")


def playlist_urls(playlist_id: str, limit: int) -> tuple[list[str], list[dict]]:
    playlist = get_yt().get_playlist(playlist_id, limit=limit)
    tracks = playlist.get("tracks") or []
    urls, metas = [], []
    for track in tracks:
        video_id = track.get("videoId")
        if not video_id:
            continue
        urls.append(song_url(video_id))
        metas.append(compact(track))
    return urls, metas


def album_urls(browse_id: str) -> tuple[list[str], list[dict]]:
    album = get_yt().get_album(browse_id)
    tracks = album.get("tracks") or []
    urls, metas = [], []
    for track in tracks:
        video_id = track.get("videoId")
        if not video_id:
            continue
        urls.append(song_url(video_id))
        metas.append(compact(track))
    return urls, metas


def doctor() -> dict:
    return {
        "version": VERSION,
        "dependencies": {
            name: shutil.which(name)
            for name in ("python3", "mpv", "yt-dlp", "ffmpeg")
        },
        "ytmusicapi": getattr(ytmusicapi, "__version__", "unknown"),
        "ytm_home": str(BASE),
        "oauth": AUTH.exists(),
        "socket": str(SOCKET),
        "mpv_running": mpv_running(),
    }


def main():
    parser = argparse.ArgumentParser(prog="ytm", description="YouTube Music CLI")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    search = sub.add_parser("search", help="search YouTube Music")
    search.add_argument("query")
    search.add_argument(
        "--type",
        default="songs",
        choices=[
            "songs", "videos", "albums", "artists", "playlists",
            "community_playlists", "featured_playlists", "uploads",
        ],
    )
    search.add_argument("--limit", type=int, default=10)

    play = sub.add_parser("play", help="search and play the first matching song")
    play.add_argument("query")

    play_url = sub.add_parser("play-url", help="play a URL")
    play_url.add_argument("url")

    play_playlist = sub.add_parser("play-playlist", help="queue a playlist")
    play_playlist.add_argument("playlist_id")
    play_playlist.add_argument("--limit", type=int, default=50)

    play_album = sub.add_parser("play-album", help="queue an album")
    play_album.add_argument("browse_id")

    sub.add_parser("pause", help="pause playback")
    sub.add_parser("resume", help="resume playback")
    sub.add_parser("toggle", help="toggle pause")
    sub.add_parser("next", help="next track")
    sub.add_parser("prev", help="previous track")
    sub.add_parser("stop", help="stop playback")
    sub.add_parser("status", help="show what is playing")

    volume = sub.add_parser("volume", help="set mpv volume (0-130)")
    volume.add_argument("level", type=float)

    seek = sub.add_parser("seek", help="seek to an absolute position in seconds")
    seek.add_argument("seconds", type=float)

    sub.add_parser("auth", help="set up OAuth for your personal library")
    sub.add_parser("doctor", help="check dependencies and playback state")

    args = parser.parse_args()

    try:
        if args.cmd == "search":
            print(json.dumps(do_search(args.query, args.type, args.limit),
                             ensure_ascii=False, indent=2))
        elif args.cmd == "play":
            print(json.dumps(play_query(args.query), ensure_ascii=False, indent=2))
        elif args.cmd == "play-url":
            print(json.dumps(play_urls([args.url]), ensure_ascii=False, indent=2))
        elif args.cmd == "play-playlist":
            urls, metas = playlist_urls(args.playlist_id, args.limit)
            if not urls:
                die("playlist has no playable tracks")
            meta = {"playlist": args.playlist_id, "tracks": len(urls), "first": metas[0]}
            print(json.dumps(play_urls(urls, meta), ensure_ascii=False, indent=2))
        elif args.cmd == "play-album":
            urls, metas = album_urls(args.browse_id)
            if not urls:
                die("album has no playable tracks")
            meta = {"album": args.browse_id, "tracks": len(urls), "first": metas[0]}
            print(json.dumps(play_urls(urls, meta), ensure_ascii=False, indent=2))
        elif args.cmd == "pause":
            set_prop("pause", True)
            print(json.dumps({"paused": bool(get_prop("pause"))}))
        elif args.cmd == "resume":
            set_prop("pause", False)
            print(json.dumps({"paused": bool(get_prop("pause"))}))
        elif args.cmd == "toggle":
            current = bool(get_prop("pause"))
            set_prop("pause", not current)
            print(json.dumps({"paused": not current}))
        elif args.cmd == "next":
            ipc(["playlist-next"])
            time.sleep(0.5)
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.cmd == "prev":
            ipc(["playlist-prev"])
            time.sleep(0.5)
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.cmd == "stop":
            stop_mpv()
            print(json.dumps({"stopped": True}))
        elif args.cmd == "status":
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.cmd == "volume":
            set_prop("volume", max(0, min(130, args.level)))
            print(json.dumps({"volume": get_prop("volume")}))
        elif args.cmd == "seek":
            ipc(["seek", args.seconds, "absolute"])
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.cmd == "doctor":
            print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        elif args.cmd == "auth":
            client_id = os.environ.get("YT_CLIENT_ID")
            client_secret = os.environ.get("YT_CLIENT_SECRET")
            if not setup_oauth:
                die("this ytmusicapi version does not support setup_oauth; upgrade ytmusicapi")
            if not client_id or not client_secret:
                die(
                    "OAuth needs a Google Cloud OAuth client. "
                    "Set YT_CLIENT_ID and YT_CLIENT_SECRET, then rerun `ytm auth`."
                )
            BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
            setup_oauth(client_id, client_secret, filepath=str(AUTH), open_browser=True)
            try:
                AUTH.chmod(0o600)
            except OSError:
                pass
            print(json.dumps({"authenticated": str(AUTH)}))
    except Exception as exc:
        die(f"{type(exc).__name__}: {exc}"[:1000])


if __name__ == "__main__":
    main()
