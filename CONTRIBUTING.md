# Contributing

Thanks for considering a contribution.

## Ground rules

- Keep the project unofficial. Do not add Google or YouTube logos, branding, or claims of endorsement.
- Do not contribute music, video, artwork, credentials, or other media.
- Do not contribute code whose purpose is to bypass DRM, paywalls, or access controls.
- Do not commit `oauth.json`, API keys, tokens, or other secrets.
- Keep the legal and privacy documentation accurate if you change data handling or network behavior.

## License of contributions

By submitting a pull request, you agree that your contribution is licensed under the repository's MIT License (inbound = outbound). You confirm that you have the right to submit the work.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m py_compile ytm.py
python ytm.py --help
```

For manual testing without sound:

```bash
export YTM_HOME="$(mktemp -d)"
YTM_AO=null python ytm.py play "Tame Impala"
python ytm.py status
python ytm.py stop
```

Do not use real credentials in tests.
