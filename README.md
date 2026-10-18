# Glyph companion

Runs [glyph-server](https://github.com/glyphmusic/server) as the yt-dlp
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
- `.github/workflows/image.yml`: builds `ghcr.io/glyphmusic/companion` on push
  and every Monday.

## Setup

1. **Tunnel.** Cloudflare dashboard > Zero Trust > Networks > Tunnels >
   Create a tunnel (cloudflared). Copy its token. Add a public hostname,
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

If the machine is off, only YouTube is missing: the Worker answers 503 for it
and every other source keeps working.

## Switch it off and on

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
