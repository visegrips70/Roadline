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

  def test_reject_sensitive_or_nonportable_input(self):
    for kind in ('private_name', 'private_content', 'outside_link'):
      with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
        root = Path(d); src = root / 'source'; src.mkdir()
        if kind == 'private_name': (src / 'id_ed25519').write_text('secret')
        if kind == 'private_content': (src / 'something').write_text('-----BEGIN OPENSSH PRIVATE KEY-----')
        if kind == 'outside_link': (src / 'outside').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError): copy_runtime(src.resolve(), root / 'out')

if __name__ == '__main__': unittest.main()
