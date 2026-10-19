import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import update_rdlp as updater


def archive(version):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w:gz') as package:
        member = tarfile.TarInfo('./r-dlp')
        member.size = len(version)
        package.addfile(member, io.BytesIO(version.encode()))
    return data.getvalue()


class Updates(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cached = Path(self.directory.name) / 'tools' / 'r-dlp'
        self.bundled = Path(self.directory.name) / 'bundled'
        self.bundled.write_text('0.1.0')
        self.version = patch.object(updater, 'version', side_effect=lambda path: Path(path).read_text())
        self.version.start()
        self.addCleanup(self.version.stop)
        env = patch.dict(os.environ, {'GLYPH_RDLP_VERSION': 'latest', 'GLYPH_RDLP_AUTO_UPDATE': '1'})
        env.start()
        self.addCleanup(env.stop)

    def downloads(self, payload, desired='0.1.1', checksum=None):
        checksum = checksum or hashlib.sha256(payload).hexdigest()
        return patch.object(updater, 'fetch', side_effect=[
            json.dumps({'tag_name': 'v' + desired}).encode(),
            f'{checksum}  r-dlp-{desired}-x86_64-unknown-linux-gnu.tar.gz\n'.encode(),
            payload,
        ])

    @patch.object(updater, 'target', return_value='x86_64-unknown-linux-gnu')
    def test_checked_release_replaces_bundled_fallback(self, _):
        with self.downloads(archive('0.1.1')):
            self.assertEqual(updater.update(self.cached, self.bundled), '0.1.1')
        self.assertEqual(updater.cached_version(self.cached), '0.1.1')

    @patch.object(updater, 'target', return_value='x86_64-unknown-linux-gnu')
    def test_bad_checksum_preserves_verified_copy(self, _):
        with self.downloads(archive('0.1.1'), checksum='0' * 64):
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                updater.update(self.cached, self.bundled)
        self.assertEqual(updater.cached_version(self.cached), '0.1.0')

    @patch.object(updater, 'target', return_value='x86_64-unknown-linux-gnu')
    def test_wrong_executable_version_is_not_installed(self, _):
        with self.downloads(archive('0.0.9')):
            with self.assertRaisesRegex(ValueError, 'version mismatch'):
                updater.update(self.cached, self.bundled)
        self.assertEqual(updater.cached_version(self.cached), '0.1.0')

    def test_offline_start_preserves_fallback(self):
        with patch.object(updater, 'fetch', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                updater.update(self.cached, self.bundled)
        self.assertEqual(updater.cached_version(self.cached), '0.1.0')

    def test_disabled_updates_never_access_network(self):
        with patch.dict(os.environ, {'GLYPH_RDLP_AUTO_UPDATE': '0'}), patch.object(updater, 'fetch') as fetch:
            self.assertEqual(updater.update(self.cached, self.bundled), '0.1.0')
            fetch.assert_not_called()

    def test_latest_never_downgrades(self):
        with patch.object(updater, 'fetch', return_value=b'{"tag_name":"v0.0.9"}') as fetch:
            self.assertEqual(updater.update(self.cached, self.bundled), '0.1.0')
            self.assertEqual(fetch.call_count, 1)

    def test_corrupted_cache_is_replaced_before_execution(self):
        updater.install(b'0.1.1', self.cached, '0.1.1')
        self.cached.write_text('tampered')
        with patch.dict(os.environ, {'GLYPH_RDLP_AUTO_UPDATE': '0'}):
            self.assertEqual(updater.update(self.cached, self.bundled), '0.1.0')
        self.assertEqual(updater.cached_version(self.cached), '0.1.0')

    def test_archive_links_are_rejected(self):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:gz') as package:
            member = tarfile.TarInfo('./r-dlp')
            member.type = tarfile.SYMTYPE
            member.linkname = '/outside'
            package.addfile(member)
        with self.assertRaises(ValueError):
            updater.unpack(data.getvalue())

    def test_cpu_asset_selection(self):
        with patch.object(updater.platform, 'system', return_value='Linux'), patch.object(updater.platform, 'machine', return_value='aarch64'):
            self.assertEqual(updater.target(), 'aarch64-unknown-linux-gnu')


if __name__ == '__main__':
    unittest.main()
