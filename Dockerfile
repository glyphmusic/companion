# glyph-server as the Worker's yt-dlp companion: the native server plus
# yt-dlp, ffmpeg and Deno (yt-dlp needs a JS runtime for YouTube).
# Sources come straight from the public repos, so this repo holds no code.
FROM rust:1-slim-trixie AS build
ARG SERVER_REF=v0.2.4
ARG DESKTOP_REF=v0.2.3
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /src
# glyph-server expects the app repo next to it (glyph-protocol, site icons).
RUN git init glyph-server \
    && git -C glyph-server fetch --depth 1 https://github.com/glyphmusic/server.git "$SERVER_REF" \
    && git -C glyph-server checkout --detach FETCH_HEAD \
    && git init glyph \
    && git -C glyph fetch --depth 1 --filter=blob:none https://github.com/glyphmusic/desktop.git "$DESKTOP_REF" \
    && git -C glyph checkout --detach FETCH_HEAD \
    && git -C glyph sparse-checkout set crates/glyph-protocol assets/icons \
    && awk '/^\[workspace.package\]/{p=1;print;next} p && /^\[/{exit} p{print}' glyph/Cargo.toml > /tmp/glyph-package \
    && printf '[workspace]\nresolver = "2"\nmembers = ["crates/glyph-protocol"]\n\n' > glyph/Cargo.toml \
    && cat /tmp/glyph-package >> glyph/Cargo.toml
# (Only glyph-protocol is built from the app repo. The app's root manifest
# lists members the sparse checkout leaves out, so it is replaced by one that
# keeps just the fields glyph-protocol inherits.)
WORKDIR /src/glyph-server
RUN cargo build --release -p glyph-server-native

FROM debian:trixie-slim
ARG SERVER_REF
ARG DESKTOP_REF
LABEL io.glyph.server-revision=$SERVER_REF io.glyph.desktop-revision=$DESKTOP_REF
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
