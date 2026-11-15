import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import patch


class InstallerTests(unittest.TestCase):
    def invoke(self, root, out):
        release = root / 'releases/audit'
        release.mkdir(parents=True, exist_ok=True)
        (release / 'patch.json').write_text(json.dumps({
            'model': 'OM-5 Mark II', 'firmware': '1.1', 'camera_tested': False,
            'stock': {'file': 'stock.bin'},
        }))
        (release / 'LOOKS.BIN').write_bytes(b'starter')
        (root / 'stock.bin').write_bytes(b'stock')
        args = ['patch.py', '--release', 'audit', '--stock', str(root / 'stock.bin'),
                '--out', str(out), '--i-accept-untested']
        with mock.patch.object(patch, 'HERE', root), mock.patch.object(sys, 'argv', args), \
             mock.patch.object(patch, 'build', return_value=b'patched'), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            patch.main()
        return output.getvalue()

    def test_rerun_preserves_custom_looks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / 'card'
            (out / 'OM5MOD').mkdir(parents=True)
            (out / 'OM5MOD/LOOKS.BIN').write_bytes(b'my custom looks')
            self.invoke(root, out)
            self.assertEqual((out / 'OM5MOD/LOOKS.BIN').read_bytes(), b'my custom looks')
            self.assertEqual((out / 'DCOLYMP/E1489999.BIN').read_bytes(), b'patched')
            self.assertEqual((out / 'restore/DCOLYMP/E1489999.BIN').read_bytes(), b'stock')

    def test_fresh_output_includes_starter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.invoke(root, root / 'card')
            self.assertEqual((root / 'card/OM5MOD/LOOKS.BIN').read_bytes(), b'starter')

    def test_failed_flush_preserves_existing_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'E1489999.BIN'
            path.write_bytes(b'previous complete image')
            with mock.patch.object(patch.os, 'fsync', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    patch.atomic_write(path, b'new image')
            self.assertEqual(path.read_bytes(), b'previous complete image')
            self.assertEqual(list(Path(tmp).iterdir()), [path])

    def test_failed_restore_prevents_install_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / 'card'
            real_replace = os.replace

            def fail_restore(source, target):
                if 'restore' in Path(target).parts:
                    raise OSError('restore destination unavailable')
                return real_replace(source, target)

            with mock.patch.object(patch.os, 'replace', side_effect=fail_restore):
                with self.assertRaises(SystemExit) as error:
                    self.invoke(root, out)
            self.assertEqual(error.exception.code, 1)
            self.assertFalse((out / 'DCOLYMP/E1489999.BIN').exists())
            self.assertEqual(list(out.rglob('*.tmp')), [])

    def test_unusable_restore_directory_prevents_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / 'card'
            out.mkdir()
            (out / 'restore').write_bytes(b'not a directory')
            with self.assertRaises(SystemExit) as error:
                self.invoke(root, out)
            self.assertEqual(error.exception.code, 1)
            self.assertFalse((out / 'DCOLYMP/E1489999.BIN').exists())


if __name__ == '__main__':
    unittest.main()
