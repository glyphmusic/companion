"""Install the GitHub release dependency before the server starts."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request

BUNDLED = Path('/usr/local/bin/r-dlp')
CACHED = Path('/cache/tools/r-dlp')
REPO = 'https://github.com/glyphmusic/r-dlp'
VERSION = re.compile(r'v?(\d+\.\d+\.\d+)')


def version(path):
    result = subprocess.run([str(path), '--version'], capture_output=True,
                            text=True, timeout=5, check=True)
    value = result.stdout.strip()
    if not VERSION.fullmatch(value):
        raise ValueError('Invalid executable version')
    return value.removeprefix('v')


def fetch(url, limit, deadline):
    def remaining():
        seconds = deadline - time.monotonic()
        if seconds <= 0:
            raise TimeoutError('Dependency download budget exhausted')
        return min(6, seconds)
    request = urllib.request.Request(url, headers={'User-Agent': 'glyph-companion-rdlp-updater'})
    with urllib.request.urlopen(request, timeout=remaining()) as response:
        chunks = bytearray()
        while True:
            remaining()
            chunk = response.read(min(65536, limit + 1 - len(chunks)))
            chunks.extend(chunk)
            if len(chunks) > limit:
                raise ValueError('Dependency download too large')
            if not chunk:
                return bytes(chunks)


def target():
    arch = {'x86_64': 'x86_64', 'amd64': 'x86_64', 'aarch64': 'aarch64', 'arm64': 'aarch64'}.get(platform.machine().lower())
    if platform.system() != 'Linux' or not arch:
        raise ValueError('Unsupported dependency platform')
    return arch + '-unknown-linux-gnu'


def unpack(archive):
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as package:
        files = [member for member in package.getmembers() if member.name in ('r-dlp', './r-dlp')]
        if len(files) != 1 or not files[0].isfile() or not 0 < files[0].size <= 32 * 1024 * 1024:
            raise ValueError('Invalid dependency archive')
        # Read only the named regular file; never extract paths or links.
        return package.extractfile(files[0]).read()


def atomic_write(path, data, executable=False):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as staged:
        temporary = Path(staged.name)
        try:
            staged.write(data)
            staged.flush()
            if executable:
                os.chmod(temporary, 0o755)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install(binary, destination, expected):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        candidate = Path(staging) / 'r-dlp'
        candidate.write_bytes(binary)
        candidate.chmod(0o755)
        if version(candidate) != expected:
            raise ValueError('Dependency executable version mismatch')
        metadata = {'version': expected, 'sha256': hashlib.sha256(binary).hexdigest()}
        # A crash between these replacements leaves an invalid cache, which
        # the next startup replaces with the trusted bundled fallback.
        atomic_write(destination.with_suffix('.json'), json.dumps(metadata).encode())
        os.replace(candidate, destination)


def cached_version(destination):
    try:
        metadata = json.loads(destination.with_suffix('.json').read_text())
        if hashlib.sha256(destination.read_bytes()).hexdigest() != metadata['sha256']:
            return None
        actual = version(destination)
        return actual if actual == metadata['version'] else None
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return None


def update(destination=CACHED, bundled=BUNDLED):
    current = cached_version(destination)
    if not current:
        current = version(bundled)
        install(bundled.read_bytes(), destination, current)
    if os.environ.get('GLYPH_RDLP_AUTO_UPDATE', '1') == '0':
        return current
    deadline = time.monotonic() + 20
    requested = os.environ.get('GLYPH_RDLP_VERSION', 'latest')
    latest = requested == 'latest'
    if requested == 'latest':
        release = json.loads(fetch('https://api.github.com/repos/glyphmusic/r-dlp/releases/latest', 256 * 1024, deadline))
        if release.get('draft') or release.get('prerelease'):
            raise ValueError('Expected a stable dependency release')
        requested = release['tag_name']
    match = VERSION.fullmatch(requested)
    if not match:
        raise ValueError('Invalid dependency release version')
    desired = match.group(1)
    if desired == current:
        return current
    if latest:
        if tuple(map(int, desired.split('.'))) < tuple(map(int, current.split('.'))):
            return current
    asset = f'r-dlp-{desired}-{target()}.tar.gz'
    base = f'{REPO}/releases/download/v{desired}'
    checksums = fetch(base + '/SHA256SUMS.txt', 65536, deadline).decode('ascii')
    expected = [line.split()[0] for line in checksums.splitlines()
                if len(line.split()) == 2 and line.split()[1].lstrip('*') == asset]
    if len(expected) != 1 or not re.fullmatch('[0-9a-fA-F]{64}', expected[0]):
        raise ValueError('Missing dependency checksum')
    archive = fetch(base + '/' + asset, 20 * 1024 * 1024, deadline)
    if hashlib.sha256(archive).hexdigest() != expected[0].lower():
        raise ValueError('Dependency archive checksum mismatch')
    install(unpack(archive), destination, desired)
    return desired


def main():
    configured = os.environ.get('GLYPH_RDLP_PATH', str(CACHED))
    if configured != str(CACHED):
        return 0  # Respect custom executables and the empty Python-backend override.
    try:
        selected = update()
        print(f'r-dlp dependency ready: {selected}', file=sys.stderr)
        return 0
    except Exception as error:
        # Do not log request URLs or tokens. Offline startup uses verified cache.
        if cached_version(CACHED):
            print(f'r-dlp update unavailable ({type(error).__name__}); using verified cache', file=sys.stderr)
            return 0
        print(f'r-dlp cache unavailable ({type(error).__name__}); using bundled resolver', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
