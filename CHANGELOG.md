# Changelog

## 0.3.0 - 2026-10-19

- Build from Glyph Server and desktop protocol v0.3.0, including streaming and resolver performance improvements and authenticated management endpoints.

- Install r-dlp's matching GitHub release at startup as a checked runtime dependency, with a persistent cache and bundled offline fallback.
- Support version pins and disabling automatic release checks without rebuilding the container.
- Pin r-dlp v0.1.1 in automated image builds and verify its version before publication.
- Include HTTP/2 negotiation and a shared resolution deadline in the native audio resolver.

## 0.2.5 - 2026-10-19

- Serve lyrics for the Worker from this machine (`POST /internal/lyrics`), so LRCLIB's rate limit on data-centre addresses no longer breaks lyrics.
- Build from server v0.2.6 and desktop protocol v0.2.5, including the degraded lyrics and empty-radio answers.
- Keep pinning and labelling all three source revisions, and smoke-test native resolver startup before image publication.

## 0.2.4 - 2026-10-19

- Enable r-dlp v0.1.0 as the default prestarted audio resolver; keep yt-dlp for search, metadata and extraction fallback.
- Build from server v0.2.5 and desktop protocol v0.2.4, including forced YouTube search and server-based downloads.
- Pin and label all three source revisions, and smoke-test native resolver startup before image publication.

## 0.2.3 — 2026-10-19

- Build the companion from server v0.2.4 and desktop protocol v0.2.3, with independent release references.
- Retry full-source searches before using cached Deezer previews and recover from empty or failed YouTube searches.
- Recognize artists in video titles even when the upload channel differs, and accept nullable channel metadata.
- Include the server resolver and performance fixes from v0.2.4.

## 0.2.2 — 2026-10-18

- Resolve different songs with three prestarted yt-dlp processes, share duplicate lookups, and reserve separate audio and metadata capacity.
- Reuse resolved audio URLs in bounded memory for seeks and refills.
- Check upstream source commits every 15 minutes and publish smoke-tested images automatically. Watchtower applies new images every five minutes.
- Publish a versioned container image alongside the source-specific and latest tags.
