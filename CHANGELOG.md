# Changelog

## 0.4.0 - 2026-10-21

### Changed

- Includes Glyph Server 0.5.0: live jams, device control between your apps and lighter jam updates.
- Builds from the renamed `glyphmusic/apps` repository.
- `docker-compose.yml` uses a fixed project name, so the data volume stays the same whatever the folder is called.

## 0.3.0 - 2026-10-19

### Added

- r-dlp is downloaded and checked automatically at startup, with an offline fallback built in.
- You can pin versions or turn off automatic update checks without rebuilding the container.

### Changed

- Includes everything from Glyph Server 0.3.0: faster streaming and secure management commands.
- Faster YouTube lookups thanks to HTTP/2.

## 0.2.5 - 2026-10-19

### Fixed

- Lyrics broke when the lyrics service rate-limited the server. Your companion now fetches them instead.

## 0.2.4 - 2026-10-19

### Changed

- r-dlp is now the default YouTube resolver; yt-dlp stays as a fallback.
- Includes the "Only YouTube" option and server-side downloads from Glyph Server 0.2.5.

## 0.2.3 - 2026-10-19

### Fixed

- Songs stuck on a 30-second preview, and searches that gave up after a temporary YouTube error.
- Wrong artists for videos uploaded by a different channel.

## 0.2.2 - 2026-10-18

### Added

- Automatic updates: new images are built, tested and published on their own, and Watchtower installs them within five minutes.

### Changed

- Several songs are looked up in parallel, and seeking reuses what was already found.
