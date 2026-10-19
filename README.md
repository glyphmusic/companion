# Glyph companion

Runs [glyph-server](https://github.com/glyphmusic/server) with
[r-dlp](https://github.com/glyphmusic/r-dlp) as its native audio resolver and yt-dlp
companion of the Glyph Cloudflare Worker. A Worker cannot start programs, so
YouTube search and audio go from the Worker to this machine:

```
app -> Worker (api.glyph.my) -> Cloudflare Tunnel -> companion (yt-dlp) -> YouTube
```

Best on a machine at home: YouTube blocks data-centre IPs far more often than
home connections. No port has to be opened; the tunnel connects out.

## What is in here

- `Dockerfile`: glyph-server built from the public repos, plus yt-dlp, ffmpeg
  and Deno. yt-dlp updates itself on every start.
- `docker-compose.yml`: the companion, `cloudflared` and Watchtower (pulls new
  images).
- `.github/workflows/image.yml`: checks upstream source commits every 15 minutes,
  builds changed sources, and refreshes the runtime every Monday. Images pass a
  smoke test before publication. Watchtower checks for images every five minutes.

## Setup

1. **Tunnel.** Cloudflare dashboard > Networking > Tunnels > Create a tunnel
   (cloudflared). Copy its token. Under Routes add a published application,
   e.g. `ytdlp.glyph.my`, service `http://companion:8787`.
2. **Token.** Make a random secret of at least 32 characters, e.g.
   `openssl rand -hex 32`.
3. **This machine** (Docker installed, starts with the system):
   ```bash
   git clone https://github.com/glyphmusic/companion.git
   cd companion
   cp .env.example .env   # fill in YTDLP_SERVICE_TOKEN and TUNNEL_TOKEN
   docker compose up -d
   ```
4. **Worker** (in `glyph-server/crates/glyph-server-worker`):
   ```bash
   npx wrangler secret put YTDLP_SERVICE_URL     # https://ytdlp.glyph.my
   npx wrangler secret put YTDLP_SERVICE_TOKEN   # the same secret as in .env
   ```
5. **Check:** `https://ytdlp.glyph.my/v1/health` answers; a YouTube search in
   the app returns YouTube results.

The companion installs r-dlp as a release dependency on every startup: it checks
the latest stable GitHub release, selects the Linux asset for the CPU, validates
SHA-256 and the executable version, then atomically installs it in
`/cache/tools/r-dlp`. The cache volume retains it across container replacements.
Offline startup uses the verified cached executable or the bundled v0.1.1 copy.
Restart only the companion to pick up a new r-dlp release:
`docker compose restart companion`. Set `GLYPH_RDLP_VERSION=0.1.1` to pin a
version or `GLYPH_RDLP_AUTO_UPDATE=0` to keep the verified local copy without
checking GitHub. An explicit `GLYPH_RDLP_PATH` override bypasses this updater.

Three native
workers are started in advance and reuse HTTP connections and visitor context.
yt-dlp remains installed for searches, metadata and extraction fallback. To
temporarily use the original Python worker backend, override `GLYPH_RDLP_PATH`
with an empty value in Compose and recreate the companion service.

The companion keeps a bounded cache of resolved YouTube URLs in memory and
streams audio ranges without keeping a persistent audio library here. Three
prestarted native processes resolve different songs concurrently; duplicate
requests for the same video share one lookup. Audio and metadata work have
separate capacity limits.

The Worker caches search results and can keep audio in the R2 bucket
`glyph-covers` (prefix `audio/`). Cached audio can play while this machine is
off; uncached YouTube requests still need the companion.

If the machine is off, only YouTube is missing: the Worker answers 503 for it
and every other source keeps working.

## Switch it off and on

From any computer, through the Worker's admin API (needs the Worker secret
`ADMIN_PASSWORD_HASH`):

```bash
glyph-server remote login https://api.glyph.my
glyph-server remote companion off
glyph-server remote companion on
```

The Worker then stops calling the companion at once. Directly on this
machine instead:

YouTube can be paused without stopping anything: while the companion is off
it answers every Worker request with 403 Forbidden, and the app simply shows
no YouTube results. It takes effect at once and survives restarts (the switch
is a file in the cache volume).

```bash
docker compose exec companion glyph-server companion status
docker compose exec companion glyph-server companion off
docker compose exec companion glyph-server companion on
```

Run them in this folder (`C:\glyph-companion` on PC0373).

## Update

Nothing to do: Watchtower pulls the weekly image. By hand:
`docker compose pull && docker compose up -d`.
