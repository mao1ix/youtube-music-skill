# Security policy

## Supported versions

Security fixes are applied to the latest `0.1.x` release.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private vulnerability reporting for this repository if it is available (Security tab → Report a vulnerability), or open a minimal public issue asking for a private contact channel without including exploit details.

Useful reports include:

- command injection or unsafe shell handling;
- credential or OAuth-token leakage;
- insecure file or socket permissions;
- a way for another local user to control your `mpv` instance;
- dependency or supply-chain concerns.

## OAuth token safety

Never commit `oauth.json` or any Google client secret. The repository's `.gitignore` excludes `oauth.json`, but you should still check `git status` before committing.

If a token is exposed:

1. Revoke the app's access in your Google Account's third-party app permissions.
2. Delete `$YTM_HOME/oauth.json`.
3. Re-run `ytm auth` if you still want authenticated features.

## Scope

`ytm` runs locally and has no project-operated backend. Reports about YouTube's service, `mpv`, `yt-dlp`, FFmpeg, or `ytmusicapi` should go to those projects unless the issue is caused by `ytm`'s integration code.
