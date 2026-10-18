# Changelog

## 0.2.2 — 2026-10-18

- Resolve different songs with three prestarted yt-dlp processes, share duplicate lookups, and reserve separate audio and metadata capacity.
- Reuse resolved audio URLs in bounded memory for seeks and refills.
- Check upstream source commits every 15 minutes and publish smoke-tested images automatically. Watchtower applies new images every five minutes.
- Publish a versioned container image alongside the source-specific and latest tags.
