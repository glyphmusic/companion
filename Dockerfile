# glyph-server as the Worker's yt-dlp companion: the native server plus
# yt-dlp, ffmpeg and Deno (yt-dlp needs a JS runtime for YouTube).
# Server sources come from the public repos; r-dlp uses checked release assets.
FROM rust:1-slim-trixie AS build
ARG SERVER_REF=v0.3.0
ARG DESKTOP_REF=v0.3.0
ARG RDLP_REF=v0.1.1
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

FROM debian:trixie-slim AS rdlp-build
ARG RDLP_VERSION=0.1.1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /rdlp
RUN set -eu; \
    case "$(dpkg --print-architecture)" in amd64) arch=x86_64;; arm64) arch=aarch64;; *) exit 1;; esac; \
    asset="r-dlp-${RDLP_VERSION}-${arch}-unknown-linux-gnu.tar.gz"; \
    base="https://github.com/glyphmusic/r-dlp/releases/download/v${RDLP_VERSION}"; \
    curl --connect-timeout 10 --max-time 60 --retry 2 -fsSL "$base/$asset" -o "$asset"; \
    curl --connect-timeout 10 --max-time 60 --retry 2 -fsSL "$base/SHA256SUMS.txt" -o SHA256SUMS.txt; \
    grep " $asset$" SHA256SUMS.txt | sha256sum -c -; \
    tar -xzf "$asset" ./r-dlp; \
    test "$(./r-dlp --version)" = "$RDLP_VERSION"

FROM debian:trixie-slim
ARG SERVER_REF
ARG DESKTOP_REF
ARG RDLP_REF
LABEL io.glyph.server-revision=$SERVER_REF io.glyph.desktop-revision=$DESKTOP_REF io.glyph.rdlp-revision=$RDLP_REF
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates ffmpeg python3 curl unzip \
    && curl -fsSL https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && curl -fsSL https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip -o /tmp/deno.zip \
    && unzip -q /tmp/deno.zip -d /usr/local/bin && rm /tmp/deno.zip \
    && chmod a+rx /usr/local/bin/yt-dlp /usr/local/bin/deno \
    && apt-get purge -y unzip && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* \
    && useradd -r -u 10001 -m glyph && chown glyph /usr/local/bin/yt-dlp     && mkdir /cache && chown glyph /cache
COPY --from=build /src/glyph-server/target/release/glyph-server /usr/local/bin/glyph-server
COPY --from=rdlp-build /rdlp/r-dlp /usr/local/bin/r-dlp
COPY update_rdlp.py /usr/local/lib/glyph/update_rdlp.py
USER glyph
EXPOSE 8787
ENV GLYPH_BIND=0.0.0.0:8787
ENV GLYPH_RDLP_PATH=/cache/tools/r-dlp
HEALTHCHECK --start-period=60s --interval=60s --timeout=5s CMD curl -fsS http://127.0.0.1:8787/v1/health >/dev/null || exit 1
# Resolve the latest checked release dependency before starting native workers.
# Offline startup uses a verified persistent copy or the bundled resolver.
ENTRYPOINT ["sh", "-c", "python3 /usr/local/lib/glyph/update_rdlp.py || export GLYPH_RDLP_PATH=/usr/local/bin/r-dlp; timeout 20s yt-dlp -U >/dev/null 2>&1 || true; exec glyph-server \"$@\"", "--"]
