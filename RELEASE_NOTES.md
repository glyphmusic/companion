# Glyph Companion 0.2.5

- Serve lyrics for the Worker from this machine (`POST /internal/lyrics`), so LRCLIB's rate limit on data-centre addresses no longer breaks lyrics.
- Build from server v0.2.6 and desktop protocol v0.2.5, including the degraded lyrics and empty-radio answers.
- Keep pinning and labelling all three source revisions, and smoke-test native resolver startup before image publication.

Container: `ghcr.io/glyphmusic/companion:0.2.5`.
