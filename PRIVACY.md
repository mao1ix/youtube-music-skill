# Privacy

`ytm` is a local-first command-line tool. It has no project-operated servers, telemetry, analytics, accounts, or advertising. The maintainers do not receive data about your usage.

## Data stored on your machine

Depending on how you use it, `ytm` stores:

- **OAuth credentials** at `$YTM_HOME/oauth.json` if you run `ytm auth`. This file is sensitive and is excluded from git. The CLI sets it to owner-only permissions where the platform supports that.
- **Playback logs** at `$YTM_HOME/mpv.log`. Logs may contain media titles, URLs, file paths, and error messages.
- **A local IPC socket** at `$XDG_RUNTIME_DIR/ytm-mpv.sock`, or at `$YTM_HOME/ytm-mpv.sock` when `XDG_RUNTIME_DIR` is unavailable. The socket is used to control the local `mpv` process.

The default `YTM_HOME` is `~/.local/share/ytm`. You can change it with the `YTM_HOME` environment variable.

## Network connections

`ytm` connects directly to:

- YouTube Music through `ytmusicapi`, for search and metadata;
- Google OAuth endpoints, if you run `ytm auth`;
- YouTube media and content-delivery endpoints through `mpv` and `yt-dlp`, for playback.

Those third parties have their own privacy practices. `ytm` does not proxy your traffic through a project server and does not send usage data to the maintainers.

## Third-party tools

`mpv`, `yt-dlp`, FFmpeg, `ytmusicapi`, Python, and your operating system may collect or process data according to their own policies. Review their documentation if that matters to you. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Revoking access and deleting data

To stop playback and remove local credentials:

```bash
ytm stop
rm -f "${YTM_HOME:-$HOME/.local/share/ytm}/oauth.json"
```

You can also revoke the app's access from your Google Account's third-party app permissions. Deleting `oauth.json` removes the local copy; it does not by itself revoke the grant on Google's side.

To remove logs, delete `$YTM_HOME/mpv.log`.

## GitHub

The project is hosted on GitHub. GitHub's own terms and privacy policy apply to repository hosting, issues, and other GitHub features. The project does not control GitHub's data practices.
