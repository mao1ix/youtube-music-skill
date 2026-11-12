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
IPC_BUFFER_SIZE = 65536
MPV_START_POLLS = 200
STOP_WAIT_POLLS = 30
MAX_VOLUME = 130
MAX_ERROR_LEN = 1000
ALLOWED_URL_SCHEMES = ("http://", "https://", "ytdl://")

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
    if limit < 1:
        die("--limit must be at least 1")
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
        while True:
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("request_id") == 1:
                    return obj
            chunk = sock.recv(IPC_BUFFER_SIZE)
            if not chunk:
                return None
            buf += chunk
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


def require_running():
    if not mpv_running():
        die("mpv is not running")


def stop_mpv():
    if SOCKET.exists():
        ipc(["quit"])
        for _ in range(STOP_WAIT_POLLS):
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
    command.append("--")
    command.extend(urls)
    with LOG.open("ab") as log:
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
        )
    for _ in range(MPV_START_POLLS):
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


def validate_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned.startswith(ALLOWED_URL_SCHEMES):
        die("URL must start with https://, http://, or ytdl://")
    return cleaned


def play_urls(urls: list[str], meta: dict | None = None):
    if not urls:
        die("no playable URLs provided")
    if mpv_running():
        ipc(["loadfile", urls[0], "replace"])
        for url in urls[1:]:
            ipc(["loadfile", url, "append"])
        set_prop("pause", False)
        time.sleep(0.3)
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
    if limit < 1:
        die("--limit must be at least 1")
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


def run_auth():
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
    return {"authenticated": str(AUTH)}


def build_parser() -> argparse.ArgumentParser:
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

    for name, help_text in (
        ("pause", "pause playback"),
        ("resume", "resume playback"),
        ("toggle", "toggle pause"),
        ("next", "next track"),
        ("prev", "previous track"),
        ("stop", "stop playback"),
        ("status", "show what is playing"),
        ("auth", "set up OAuth for your personal library"),
        ("doctor", "check dependencies and playback state"),
    ):
        sub.add_parser(name, help=help_text)

    volume = sub.add_parser("volume", help=f"set mpv volume (0-{MAX_VOLUME})")
    volume.add_argument("level", type=float)

    seek = sub.add_parser("seek", help="seek to an absolute position in seconds")
    seek.add_argument("seconds", type=float)
    return parser


def handle_playback_command(args) -> dict:
    if args.cmd == "stop":
        stop_mpv()
        return {"stopped": True}
    if args.cmd == "status":
        return status()
    require_running()
    if args.cmd == "pause":
        set_prop("pause", True)
        return {"paused": bool(get_prop("pause"))}
    if args.cmd == "resume":
        set_prop("pause", False)
        return {"paused": bool(get_prop("pause"))}
    if args.cmd == "toggle":
        current = bool(get_prop("pause"))
        set_prop("pause", not current)
        return {"paused": not current}
    if args.cmd in ("next", "prev"):
        ipc(["playlist-next" if args.cmd == "next" else "playlist-prev"])
        time.sleep(0.5)
        return status()
    if args.cmd == "volume":
        set_prop("volume", max(0, min(MAX_VOLUME, args.level)))
        return {"volume": get_prop("volume")}
    ipc(["seek", max(0.0, args.seconds), "absolute"])
    return status()


def dispatch(args):
    if args.cmd == "search":
        return do_search(args.query, args.type, args.limit)
    if args.cmd == "play":
        return play_query(args.query)
    if args.cmd == "play-url":
        return play_urls([validate_url(args.url)])
    if args.cmd == "play-playlist":
        urls, metas = playlist_urls(args.playlist_id, args.limit)
        if not urls:
            die("playlist has no playable tracks")
        return play_urls(urls, {"playlist": args.playlist_id, "tracks": len(urls), "first": metas[0]})
    if args.cmd == "play-album":
        urls, metas = album_urls(args.browse_id)
        if not urls:
            die("album has no playable tracks")
        return play_urls(urls, {"album": args.browse_id, "tracks": len(urls), "first": metas[0]})
    if args.cmd == "doctor":
        return doctor()
    if args.cmd == "auth":
        return run_auth()
    return handle_playback_command(args)


def main():
    args = build_parser().parse_args()
    try:
        print(json.dumps(dispatch(args), ensure_ascii=False, indent=2))
    except Exception as exc:
        die(f"{type(exc).__name__}: {exc}"[:MAX_ERROR_LEN])


if __name__ == "__main__":
    main()
