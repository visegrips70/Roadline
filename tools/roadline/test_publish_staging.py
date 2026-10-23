"""Assembly tests never contact GitHub, run native binaries, or change a device."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import publish_staging as pub


class AssemblyTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.root = Path(self.tmp.name)
    self.source, self.inputs, self.out = [self.root / x for x in ('source', 'inputs', 'output')]
    self.source.mkdir()
    (self.inputs / 'parts').mkdir(parents=True)

  def source_entry(self, path, data, mode='100644'):
    p = self.source / path
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == '120000': p.symlink_to(data.decode())
    else: p.write_bytes(data)
    return dict(path=path, mode=mode, type='blob', sha=pub.blob_sha(data), from_source=True)

  def part_entry(self, path, pieces, mode='100644'):
    names = []
    for data in pieces:
      name = 'parts/' + pub.blob_sha(data)
      (self.inputs / name).write_bytes(data)
      names.append(name)
    return dict(path=path, mode=mode, type='blob', sha=pub.blob_sha(b''.join(pieces)), parts=names)

  def assemble(self, records):
    pub.assemble(self.source, self.inputs, self.out, {'entries': records})

  def test_reassembles_binary_modes_empty_file_and_exact_symlink(self):
    records = [self.source_entry('dir/file', b'source'),
               self.source_entry('link', b'dir/', '120000'),
               self.part_entry('program', [b'\x7fELF\x00', b'\xff\x01'], '100755'),
               self.part_entry('prebuilt', [b''])]
    self.assemble(records)
    self.assertEqual((self.out / 'program').read_bytes(), b'\x7fELF\x00\xff\x01')
    self.assertEqual((self.out / 'program').stat().st_mode & 0o777, 0o755)
    self.assertEqual(os.readlink(self.out / 'link'), 'dir/')
    self.assertEqual((self.out / 'prebuilt').read_bytes(), b'')

  def test_corrupt_source_rejected(self):
    e = self.source_entry('file', b'original')
    (self.source / 'file').write_bytes(b'changed')
    with self.assertRaisesRegex(ValueError, 'File checksum'): self.assemble([e])

  def test_corrupt_part_rejected(self):
    e = self.part_entry('file', [b'one', b'two'])
    (self.inputs / e['parts'][1]).write_bytes(b'bad')
    with self.assertRaisesRegex(ValueError, 'Part checksum'): self.assemble([e])

  def test_reordered_parts_rejected(self):
    e = self.part_entry('file', [b'one', b'two'])
    e['parts'].reverse()
    with self.assertRaisesRegex(ValueError, 'File checksum'): self.assemble([e])

  def test_unsafe_and_duplicate_paths_rejected(self):
    for name in ('../escape', '/absolute', '.git/config', 'a//b', 'a/./b'):
      with self.subTest(name=name), self.assertRaises(ValueError): pub.relative(name)
    e = self.part_entry('file', [b'ok'])
    with self.assertRaisesRegex(ValueError, 'Duplicate'): self.assemble([e, e])

  def test_escaping_symlink_rejected(self):
    e = self.part_entry('link', [b'../outside'], '120000')
    with self.assertRaisesRegex(ValueError, 'Symlink leaves'): self.assemble([e])

  def test_source_replaced_with_symlink_rejected(self):
    e = self.source_entry('file', b'ok')
    (self.root / 'private').write_bytes(b'ok')
    (self.source / 'file').unlink()
    (self.source / 'file').symlink_to('../private')
    with self.assertRaisesRegex(ValueError, 'Source path leaves'): self.assemble([e])

  def test_no_existing_output_overwrite(self):
    self.out.mkdir()
    (self.out / 'keep').write_bytes(b'keep')
    with self.assertRaisesRegex(ValueError, 'must be new'): self.assemble([])
    self.assertEqual((self.out / 'keep').read_bytes(), b'keep')

  def test_publish_refuses_non_workflow_environment_before_git(self):
    with patch.dict(os.environ, {}, clear=True), patch.object(pub, 'git') as git:
      with self.assertRaisesRegex(ValueError, 'limited'): pub.publish(self.out, b'', self.root / 'summary')
      git.assert_not_called()


if __name__ == '__main__':
  unittest.main()
