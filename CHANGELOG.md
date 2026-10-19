# Changelog

## 0.2.3 — 2026-10-19

- Build the companion from server v0.2.4 and desktop protocol v0.2.3, with independent release references.
- Retry full-source searches before using cached Deezer previews and recover from empty or failed YouTube searches.
- Recognize artists in video titles even when the upload channel differs, and accept nullable channel metadata.
- Include the server resolver and performance fixes from v0.2.4.

## 0.2.2 â€” 2026-10-18

- Resolve different songs with three prestarted yt-dlp processes, share duplicate lookups, and reserve separate audio and metadata capacity.
- Reuse resolved audio URLs in bounded memory for seeks and refills.
- Check upstream source commits every 15 minutes and publish smoke-tested images automatically. Watchtower applies new images every five minutes.
- Publish a versioned container image alongside the source-specific and latest tags.
