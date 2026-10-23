#!/bin/sh
set -eu

# An explicit GLYPH_CONFIG must exist, including on the first container start.
# Never replace an existing configuration or follow a dangling symlink.
: "${GLYPH_CONFIG:=/cache/server.toml}"
export GLYPH_CONFIG
if [ ! -e "$GLYPH_CONFIG" ]; then
    (umask 077; set -C; printf '# Glyph companion configuration\n' > "$GLYPH_CONFIG")
fi

python3 /usr/local/lib/glyph/update_rdlp.py || export GLYPH_RDLP_PATH=/usr/local/bin/r-dlp
timeout 20s yt-dlp -U >/dev/null 2>&1 || true
exec glyph-server "$@"
