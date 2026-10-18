# glyph-server as the Worker's yt-dlp companion: the native server plus
# yt-dlp, ffmpeg and Deno (yt-dlp needs a JS runtime for YouTube).
# Sources come straight from the public repos, so this repo holds no code.
FROM rust:1-slim AS build
ARG SERVER_REF=main
ARG DESKTOP_REF=main
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
# glyph-server expects the app repo next to it (glyph-protocol, site icons).
RUN git clone --depth 1 --branch "$SERVER_REF" https://github.com/glyphmusic/server.git glyph-server \
    && git clone --depth 1 --branch "$DESKTOP_REF" --filter=blob:none --sparse https://github.com/glyphmusic/desktop.git glyph \
    && git -C glyph sparse-checkout set crates/glyph-protocol assets/icons \
    && printf '[workspace]\nresolver = "2"\nmembers = ["crates/glyph-protocol"]\n\n[workspace.package]\nversion = "0.1.0"\nedition = "2021"\nlicense = "MIT OR Apache-2.0"\n' > glyph/Cargo.toml
# (Only glyph-protocol is built from the app repo. The app's root manifest
# lists members the sparse checkout leaves out, so it is replaced by one that
# keeps just the fields glyph-protocol inherits.)
WORKDIR /src/glyph-server
RUN cargo build --release -p glyph-server-native

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ffmpeg python3 curl unzip \
    && curl -fsSL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && curl -fsSL https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip -o /tmp/deno.zip \
    && unzip -q /tmp/deno.zip -d /usr/local/bin && rm /tmp/deno.zip \
    && chmod a+rx /usr/local/bin/yt-dlp /usr/local/bin/deno \
    && apt-get purge -y unzip && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
    && useradd -r -u 10001 -m glyph && chown glyph /usr/local/bin/yt-dlp     && mkdir /cache && chown glyph /cache
COPY --from=build /src/glyph-server/target/release/glyph-server /usr/local/bin/glyph-server
USER glyph
EXPOSE 8787
ENV GLYPH_BIND=0.0.0.0:8787
HEALTHCHECK --interval=60s --timeout=5s CMD curl -fsS http://127.0.0.1:8787/v1/health >/dev/null || exit 1
# YouTube changes often: yt-dlp updates itself on every start.
ENTRYPOINT ["sh", "-c", "yt-dlp -U >/dev/null 2>&1; exec glyph-server \"$@\"", "--"]
