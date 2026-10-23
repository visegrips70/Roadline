import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('inspection', Path(__file__).with_name('inspect_bench.py'))
inspection = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspection)


class InspectTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
    self.root = Path(self.tmp.name) / 'runtime'; self.root.mkdir()
    (self.root / 'program.py').write_bytes(b'print("original")\n')
    (self.root / 'program.py').chmod(0o755)
    (self.root / 'alias').symlink_to('program.py')
    self.report = self.root.parent / 'report.json'
    self.report.write_text(json.dumps({'files': [{'path':'program.py', 'bytes':18,
                                                'sha256':inspection.file_hash(self.root / 'program.py')}]}))
    self.report_hash = inspection.file_hash(self.report)
    self.mode_hash = hashlib.sha256(b'["program.py",true]\n').hexdigest()

  def inspect(self):
    return inspection.compare_payload(self.root, self.report, self.report_hash, self.mode_hash, {'alias':'program.py'})

  def test_generated_files_do_not_hide_modified_originals_or_expose_credentials(self):
    (self.root / '__pycache__').mkdir()
    (self.root / '__pycache__/program.pyc').write_bytes(b'cache')
    key = self.root / 'server/phone_navigation/.pairing-key'; key.parent.mkdir(parents=True)
    key.write_text('DO_NOT_PRINT_OR_READ_THIS_CREDENTIAL')
    (self.root / '.git').mkdir(); (self.root / '.git/config').write_text('PRIVATE_GIT_CONFIGURATION')
    original_open = Path.open
    def read_only_open(path, mode='r', *args, **kwargs):
      if path == key or '.git' in path.parts or mode != 'rb':
        raise AssertionError('Unexpected file access: ' + str(path))
      return original_open(path, mode, *args, **kwargs)
    with patch.object(Path, 'open', read_only_open): result = self.inspect()
    self.assertTrue(result['original_files_and_execute_bits_and_links_match'])
    self.assertEqual(result['added_python_cache_count'], 1)
    self.assertTrue(result['local_navigation_key_present'])
    self.assertFalse(result['used_runtime_is_a_release_artifact'])
    self.assertNotIn('DO_NOT_PRINT', json.dumps(result))
    self.assertNotIn('PRIVATE_GIT', json.dumps(result))
    (self.root / 'program.py').write_bytes(b'print("modified")\n')
    self.assertEqual(self.inspect()['changed_original_files'], ['program.py'])

  def test_original_execute_bit_change_is_detected(self):
    (self.root / 'program.py').chmod(0o644)
    result = self.inspect()
    self.assertFalse(result['execute_bits_match'])
    self.assertFalse(result['original_files_and_execute_bits_and_links_match'])

  def test_original_file_replaced_by_external_link_is_not_read(self):
    outside = self.root.parent / 'private'; outside.write_text('PRIVATE_CONTENT')
    p = self.root / 'program.py'; p.unlink(); p.symlink_to(outside)
    result = self.inspect()
    self.assertEqual(result['changed_original_types'], ['program.py'])
    self.assertNotIn('PRIVATE_CONTENT', json.dumps(result))

  def test_symlink_target_and_missing_file_changes_are_detected(self):
    (self.root / 'alias').unlink(); (self.root / 'alias').symlink_to('missing')
    (self.root / 'program.py').unlink()
    result = self.inspect()
    self.assertEqual(result['changed_symlinks'], ['alias'])
    self.assertEqual(result['missing_original_files'], ['program.py'])

  def test_changed_report_is_rejected(self):
    self.report.write_text('{"files":[]}')
    with self.assertRaisesRegex(ValueError, 'original package report differs'): self.inspect()

  def recovery_fixture(self):
    state = self.root.parent / 'state'; state.mkdir()
    saved = state / 'params-before'; saved.mkdir()
    params = self.root.parent / 'params'; params.mkdir()
    for parent in (saved, params):
      (parent / 'NAPPedalCalibDone').write_bytes(b'1')
      (parent / 'CalibrationParams').write_bytes(b'calibration')
    (saved / 'OpenpilotEnabledToggle').write_bytes(b'1')
    (params / 'OpenpilotEnabledToggle').write_bytes(b'0')
    (params / 'DisableUpdates').write_bytes(b'1')
    launcher = self.root.parent / 'continue.sh'; launcher.write_text('original launcher\n'); launcher.chmod(0o755)
    (state / 'continue-before.sh').write_bytes(launcher.read_bytes())
    info = launcher.stat()
    (state / 'state.json').write_text(json.dumps({
      'phase':'returned', 'start_time':1, 'returned_on_boot':True, 'previous':str(self.root),
      'launcher':{'sha256':inspection.file_hash(launcher), 'mode':0o755, 'uid':info.st_uid, 'gid':info.st_gid}}))
    active = self.root.parent / 'openpilot'; active.symlink_to(self.root)
    return state, active, launcher, params

  def test_recovery_confirms_launcher_and_settings_without_reenabling_assistance(self):
    state, active, launcher, params = self.recovery_fixture()
    result = inspection.recovery_details(state, active, launcher, params)
    self.assertTrue(result['returned_on_boot'])
    self.assertTrue(result['startup_launcher_restored'])
    self.assertTrue(result['startup_launcher_backup_matches'])
    self.assertTrue(result['settings']['matches'])
    self.assertTrue(result['assistance_disabled'])
    self.assertEqual((params / 'OpenpilotEnabledToggle').read_bytes(), b'0')
    (params / 'NAPPedalCalibDone').write_bytes(b'0')
    self.assertEqual(inspection.compare_settings(state, params)['differing_key_names'], ['NAPPedalCalibDone'])

  def test_inspection_refuses_a_running_test(self):
    state, active, launcher, params = self.recovery_fixture()
    (state / 'state.json').write_text('{"phase":"running"}')
    with self.assertRaisesRegex(ValueError, 'Wait until'): inspection.recovery_details(state, active, launcher, params)


if __name__ == '__main__': unittest.main()
