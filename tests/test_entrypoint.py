import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


@unittest.skipIf(os.name == 'nt', 'container entrypoint requires POSIX')
class Entrypoint(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name, body in [('python3', 'exit 1'), ('timeout', 'exit 0'),
                           ('glyph-server', 'printf "%s\\n" "$@"')]:
            path = self.bin / name
            path.write_text('#!/bin/sh\n' + body + '\n')
            path.chmod(0o755)
        self.config = self.root / 'server.toml'

    def tearDown(self):
        self.temp.cleanup()

    def start(self):
        env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'],
                   GLYPH_CONFIG=str(self.config))
        return subprocess.run(['sh', str(Path(__file__).resolve().parents[1] / 'entrypoint.sh'),
                               'serve', '--bind', '127.0.0.1:8787'], env=env,
                              text=True, capture_output=True, timeout=5)

    def test_new_volume_gets_private_config_and_forwards_arguments(self):
        result = self.start()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)
        self.assertEqual(result.stdout.splitlines(), ['serve', '--bind', '127.0.0.1:8787'])

    def test_existing_configuration_is_preserved(self):
        self.config.write_text('# Existing operator configuration\n')
        self.config.chmod(0o640)
        self.assertEqual(self.start().returncode, 0)
        self.assertEqual(self.config.read_text(), '# Existing operator configuration\n')
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)

    def test_dangling_symlink_is_not_followed(self):
        target = self.root / 'unrelated.toml'
        self.config.symlink_to(target)
        self.assertNotEqual(self.start().returncode, 0)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
