# Security policy

## Supported versions

Security fixes ship on `main`, in the latest release tag, and in the latest
`ghcr.io/glyphmusic/companion` container image.

| Version | Supported |
| --- | --- |
| Latest release (`0.5.x`) / `main` / `ghcr.io/glyphmusic/companion:latest` | Yes |
| Older releases | No — update to the latest release or image |

## Reporting a vulnerability

Report security vulnerabilities privately through
**[GitHub Security Advisories](https://github.com/glyphmusic/companion/security/advisories/new)**
or the contact in [glyph.my/.well-known/security.txt](https://glyph.my/.well-known/security.txt).

Do **not** open a public issue or pull request for a security problem.

Please include:

- the image tag or commit hash,
- the request or configuration that triggers the issue,
- what an attacker can access or execute.

## Scope

### In scope

- Signature, checksum or version verification bypasses in the `r-dlp` release updater (`release-key.pub`, `SHA256SUMS.txt.minisig`)
- Authentication or HMAC verification bypasses on Worker-to-companion requests (`YTDLP_SERVICE_TOKEN`, `GLYPH_COMPANION_SIGNED_ONLY`) or admin endpoints (`COMPANION_ADMIN_TOKEN`)
- Command injection, container escape or unintended network access in the companion container or image build workflow

### Out of scope

- Deployments exposed without `YTDLP_SERVICE_TOKEN` or with weak secrets contrary to the setup instructions in [README.md](README.md)
