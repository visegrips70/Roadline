import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_native_release import copy_runtime

class CopyTests(unittest.TestCase):
  def test_flatten_and_preserve(self):
    with tempfile.TemporaryDirectory() as d:
      root = Path(d); src = root / 'source'; dst = root / 'out'
      src.mkdir(); (src / 'dependency').mkdir()
      (src / 'dependency/.git').write_text('gitdir: elsewhere')
      (src / 'dependency/LICENSE').write_text('upstream')
      (src / 'program').write_bytes(b'compiled'); (src / 'program').chmod(0o755)
      (src / 'alias').symlink_to('program')
      (src / 'build').mkdir(); (src / 'build/log').write_text('private build output')
      copy_runtime(src.resolve(), dst)
      self.assertEqual((dst / 'dependency/LICENSE').read_text(), 'upstream')
      self.assertFalse((dst / 'dependency/.git').exists())
      self.assertFalse((dst / 'build').exists())
      self.assertTrue((dst / 'program').stat().st_mode & 0o100)
      self.assertEqual((dst / 'alias').read_bytes(), b'compiled')

  def test_exclude_panda_signing_key_but_preserve_firmware_and_public_keys(self):
    with tempfile.TemporaryDirectory() as d:
      src = Path(d) / 'source'; dst = Path(d) / 'out'
      certs = src / 'panda/board/certs'; certs.mkdir(parents=True)
      key = certs / 'debug'
      key.write_text('-----BEGIN RSA PRIVATE KEY-----\nsynthetic fixture\n')
      for name in ('debug.pub', 'release.pub'):
        (certs / name).write_text('public key fixture')
      obj = src / 'panda/board/obj'; obj.mkdir()
      for name in ('panda_h7.bin.signed', 'bootstub.panda_h7.bin'):
        (obj / name).write_bytes(b'signed firmware fixture')
      copy_runtime(src.resolve(), dst)
      self.assertTrue(key.is_file(), 'build source must retain its key')
      self.assertFalse((dst / 'panda/board/certs/debug').exists())
      for name in ('debug.pub', 'release.pub'):
        self.assertEqual((dst / 'panda/board/certs' / name).read_bytes(), (certs / name).read_bytes())
      for name in ('panda_h7.bin.signed', 'bootstub.panda_h7.bin'):
        self.assertEqual((dst / 'panda/board/obj' / name).read_bytes(), (obj / name).read_bytes())

  def test_private_key_elsewhere_is_not_exempted(self):
    with tempfile.TemporaryDirectory() as d:
      src = Path(d) / 'source'; src.mkdir()
      (src / 'debug').write_text('-----BEGIN RSA PRIVATE KEY-----\nsynthetic fixture\n')
      with self.assertRaises(ValueError):
        copy_runtime(src.resolve(), Path(d) / 'out')

  def test_reject_sensitive_or_nonportable_input(self):
    for kind in ('private_name', 'private_content', 'outside_link'):
      with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
        root = Path(d); src = root / 'source'; src.mkdir()
        if kind == 'private_name': (src / 'id_ed25519').write_text('secret')
        if kind == 'private_content': (src / 'something').write_text('-----BEGIN OPENSSH PRIVATE KEY-----')
        if kind == 'outside_link': (src / 'outside').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError): copy_runtime(src.resolve(), root / 'out')

if __name__ == '__main__': unittest.main()
