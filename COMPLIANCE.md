# Open-source license compliance review

Reviewed: 2026-11-12
Review method: `open-source-license` skill (Skala Legal Skills, Apache-2.0)
Scope: this repository's source code and declared dependencies.

This is a compliance review, not legal advice. See [DISCLAIMER.md](DISCLAIMER.md). If you plan to redistribute a bundle that includes third-party binaries, have a lawyer review the distribution.

## Outbound license

- **Project license:** MIT
- **Copyright holder:** mao1ix
- **License file:** [LICENSE](LICENSE)
- **SPDX headers:** `ytm.py`, `install.sh`, and `uninstall.sh` carry `SPDX-License-Identifier: MIT`

## Inventory

| Component | Relationship | License | Bundled? |
| --- | --- | --- | --- |
| `ytm` | This project | MIT | Yes (source) |
| `ytmusicapi` | Python dependency | MIT | No; installed by pip |
| `mpv` | Runtime executable | GPL-2.0-or-later and LGPL-2.1-or-later, depending on build | No; installed by user |
| `yt-dlp` | Runtime executable | Unlicense | No; installed by user |
| FFmpeg | Optional runtime dependency used by mpv | GPL or LGPL depending on build; Arch package is GPL-3.0-only | No; installed by user |
| Python | Runtime | PSF-2.0 | No; installed by user |

## Compatibility analysis

- **MIT outbound license:** permissive; compatible with the MIT-licensed `ytmusicapi` dependency.
- **Copyleft tools:** `mpv` and FFmpeg may be GPL/LGPL, but `ytm` invokes them as separate executables over a process boundary. This repository does not link, embed, or redistribute their code. That separation avoids imposing their copyleft obligations on `ytm`'s MIT source.
- **If you bundle tools:** if you redistribute `mpv`, FFmpeg, or `yt-dlp` together with `ytm`, you must comply with their licenses, including license-text, notice, and source-offer requirements where applicable. This repository does not do that.
- **No AGPL components** are declared or bundled.
- **No Apache-2.0 dependency** currently requires preservation of an upstream NOTICE file. A project NOTICE is included anyway for attribution.

## Attribution and notices

- [x] Root `LICENSE` contains the canonical MIT text.
- [x] Third-party inventory is documented in [THIRD_PARTY.md](THIRD_PARTY.md).
- [x] Short attribution summary is in [NOTICE](NOTICE).
- [x] Source files carry SPDX and copyright headers.
- [x] No third-party source code or binaries are vendored.
- [x] `oauth.json`, logs, and local data are excluded from git.

## Gaps and follow-up

- [ ] If the project later bundles `mpv`, FFmpeg, or `yt-dlp`, add their full license texts and any required source/notice information.
- [ ] Re-run this review when adding dependencies or changing the outbound license.
- [ ] Keep the trademark/ToS disclaimers accurate; license compliance does not address YouTube's platform terms.

## Residual risks outside this review

This review covers open-source copyright licensing only. It does not cover:

- YouTube's Terms of Service or API terms;
- copyright in the media you play;
- trademark exposure from the project name;
- privacy or consumer-protection law;
- your local jurisdiction.

Those risks are addressed separately in [DISCLAIMER.md](DISCLAIMER.md) and [PRIVACY.md](PRIVACY.md). They cannot be eliminated by a repository disclaimer.
