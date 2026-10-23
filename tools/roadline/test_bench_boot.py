import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bench', Path(__file__).with_name('bench_boot.py'))
bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)


class BenchTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
    self.root = Path(self.tmp.name)
    for name in ('PREVIOUS', 'RUNTIME', 'PARAMS', 'NAP_BACKUP'):
      path = self.root / name; path.mkdir()
      patcher = patch.object(bench, name, path); patcher.start(); self.addCleanup(patcher.stop)
    for name in ('ACTIVE', 'STATE', 'VERSION_PATH', 'MODEL_PATH', 'BOOT_ID_PATH', 'CONTINUE', 'LOCK'):
      patcher = patch.object(bench, name, self.root / name); patcher.start(); self.addCleanup(patcher.stop)
    bench.ACTIVE.symlink_to(bench.PREVIOUS)
    bench.VERSION_PATH.write_text('17.2\n'); bench.MODEL_PATH.write_bytes(b'comma tizi\0')
    bench.BOOT_ID_PATH.write_text('boot-a')
    (bench.PARAMS / 'IsOnroad').write_text('0')
    (bench.PARAMS / 'OpenpilotEnabledToggle').write_text('1')
    (bench.RUNTIME / 'prebuilt').touch()
    bench.CONTINUE.write_bytes(b'#!/usr/bin/env bash\ncd /data/openpilot\nexec ./launch_openpilot.sh\n')
    bench.CONTINUE.chmod(0o755)

  def test_switch_does_not_replace_real_directory(self):
    bench.ACTIVE.unlink(); bench.ACTIVE.mkdir()
    (bench.ACTIVE / 'keep').write_text('original')
    with self.assertRaises(ValueError): bench.replace_link(bench.ACTIVE, bench.RUNTIME, {bench.PREVIOUS})
    self.assertEqual((bench.ACTIVE / 'keep').read_text(), 'original')

  def test_switch_rejects_unknown_link(self):
    other = self.root / 'other'; other.mkdir()
    bench.ACTIVE.unlink(); bench.ACTIVE.symlink_to(other)
    with self.assertRaises(ValueError): bench.replace_link(bench.ACTIVE, bench.RUNTIME, {bench.PREVIOUS})
    self.assertEqual(bench.ACTIVE.resolve(), other)

  def test_switch_preserves_both_installations(self):
    (bench.PREVIOUS / 'keep').write_text('old')
    bench.replace_link(bench.ACTIVE, bench.RUNTIME, {bench.PREVIOUS})
    self.assertEqual(bench.ACTIVE.resolve(), bench.RUNTIME)
    self.assertEqual((bench.PREVIOUS / 'keep').read_text(), 'old')
    bench.replace_link(bench.ACTIVE, bench.PREVIOUS, {bench.RUNTIME})
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)

  def test_payload_changes_are_detected_but_git_metadata_is_excluded(self):
    (bench.RUNTIME / 'file').write_text('original')
    before = bench.tree_hash(bench.RUNTIME)
    (bench.RUNTIME / '.git').mkdir(); (bench.RUNTIME / '.git/config').write_text('metadata')
    self.assertEqual(before, bench.tree_hash(bench.RUNTIME))
    (bench.RUNTIME / 'file').chmod(0o755)
    self.assertNotEqual(before, bench.tree_hash(bench.RUNTIME))

  def test_external_symlink_rejected(self):
    (bench.RUNTIME / 'bad').symlink_to('/etc/passwd')
    with self.assertRaises(ValueError): bench.tree_hash(bench.RUNTIME)

  def test_onroad_rejected_before_service_or_git_commands(self):
    (bench.PARAMS / 'IsOnroad').write_text('1')
    with patch.object(bench, 'run') as run, self.assertRaises(ValueError): bench.start()
    run.assert_not_called(); self.assertFalse(bench.STATE.exists())

  def test_changed_package_rejected_before_service_or_git_commands(self):
    with patch.object(bench, 'run') as run, self.assertRaises(ValueError): bench.start()
    run.assert_not_called(); self.assertFalse(bench.STATE.exists())

  def test_reboot_guard_only_recovers_pending_test_on_new_boot(self):
    self.assertFalse(bench.state_requires_boot_recovery({'phase':'running','boot_id':'a'}, 'a'))
    self.assertTrue(bench.state_requires_boot_recovery({'phase':'armed','boot_id':'a'}, 'b'))
    self.assertTrue(bench.state_requires_boot_recovery({'phase':'prepared','boot_id':'a'}, 'b'))
    self.assertFalse(bench.state_requires_boot_recovery({'phase':'returned','boot_id':'a'}, 'b'))

  def prepare_running(self):
    bench.STATE.mkdir(); saved = bench.STATE / 'params-before'; saved.mkdir()
    (saved / 'NAPPedalCalibDone').write_bytes(b'1')
    (saved / 'OpenpilotEnabledToggle').write_bytes(b'1')
    (saved / 'CalibrationParams').write_bytes(b'calibration')
    (saved / 'AthenadPid').write_bytes(b'123')
    (bench.PARAMS / 'AthenadPid').write_bytes(b'999')
    bench.save_state({'phase':'running','boot_id':'a'})
    bench.replace_link(bench.ACTIVE, bench.RUNTIME, {bench.PREVIOUS})

  def fake_param(self, key, data):
    (bench.PARAMS / key).write_bytes(data)

  def test_timer_rollback_preserves_calibration_and_keeps_assistance_off(self):
    self.prepare_running()
    with patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', return_value=subprocess.CompletedProcess([],0,'log','')) as run:
      bench.rollback()
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)
    self.assertEqual((bench.PARAMS / 'NAPPedalCalibDone').read_bytes(), b'1')
    self.assertEqual((bench.PARAMS / 'CalibrationParams').read_bytes(), b'calibration')
    self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')
    self.assertEqual((bench.PARAMS / 'DisableUpdates').read_bytes(), b'1')
    self.assertEqual((bench.PARAMS / 'AthenadPid').read_bytes(), b'999')
    self.assertEqual(json.loads((bench.STATE / 'state.json').read_text())['phase'], 'returned')
    self.assertIn(('systemctl','stop','comma.service'), [c.args for c in run.call_args_list])
    self.assertEqual(run.call_args_list[-1].args, ('systemctl','start','comma.service'))

  def test_boot_recovery_does_not_reenter_service_start(self):
    self.prepare_running()
    with patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run') as run:
      bench.rollback(on_boot=True)
    run.assert_not_called()
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)

  def test_rollback_removes_driving_defaults_absent_from_snapshot(self):
    self.prepare_running()
    (bench.PARAMS / 'NAPNewSetting').write_bytes(b'1')
    (bench.PARAMS / 'RoadlineLaneOffsetCm').write_bytes(b'5')
    with patch.object(bench, 'set_param', side_effect=self.fake_param):
      bench.rollback(on_boot=True)
    self.assertFalse((bench.PARAMS / 'NAPNewSetting').exists())
    self.assertFalse((bench.PARAMS / 'RoadlineLaneOffsetCm').exists())
    self.assertEqual((bench.PARAMS / 'NAPPedalCalibDone').read_bytes(), b'1')

  def test_incomplete_snapshot_is_not_used_for_recovery(self):
    bench.STATE.mkdir()
    bench.save_state({'phase':'prepared','boot_id':'a'})
    (bench.PARAMS / 'NAPPedalCalibDone').write_bytes(b'1')
    def interrupted_copy(src, dest, **kwargs):
      dest.mkdir()
      (dest / 'NAPPedalCalibDone').write_bytes(b'')
      raise OSError('interrupted copy')
    with patch.object(bench.shutil, 'copytree', side_effect=interrupted_copy):
      with self.assertRaises(OSError): bench.snapshot_params()
    self.assertFalse((bench.STATE / 'params-before').exists())
    with patch.object(bench, 'set_param', side_effect=self.fake_param):
      bench.rollback(on_boot=True)
    self.assertEqual((bench.PARAMS / 'NAPPedalCalibDone').read_bytes(), b'1')
    self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')

  def test_log_capture_failure_does_not_block_recovery(self):
    self.prepare_running()
    def command(*args, **kwargs):
      if args[0] == 'sudo': raise subprocess.TimeoutExpired(args, 10)
      return subprocess.CompletedProcess(args, 0, '', '')
    with patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', side_effect=command):
      bench.rollback()
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)
    self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')

  def test_failed_service_start_returns_to_previous_installation(self):
    starts = 0
    def command(*args, **kwargs):
      nonlocal starts
      if args == ('systemctl', 'start', 'comma.service'):
        starts += 1
        if starts == 1:
          self.assertEqual(bench.ACTIVE.resolve(), bench.RUNTIME)
          self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')
          raise subprocess.CalledProcessError(1, args)
      return subprocess.CompletedProcess(args, 0, '', '')
    with patch.object(bench, 'tree_hash', return_value=bench.PAYLOAD), patch.object(bench, 'install_recovery'), \
         patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', side_effect=command):
      with self.assertRaises(subprocess.CalledProcessError): bench.start()
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)
    self.assertEqual(starts, 2)
    self.assertEqual(json.loads((bench.STATE / 'state.json').read_text())['phase'], 'returned')
    self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')

  def test_completed_rollback_is_idempotent(self):
    self.prepare_running()
    with patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', return_value=subprocess.CompletedProcess([],0,'','')):
      bench.rollback()
    with patch.object(bench, 'run') as run, patch.object(bench,'set_param') as put:
      bench.rollback()
    run.assert_not_called(); put.assert_not_called()

  def test_recovery_uses_data_launcher_and_restores_exact_bytes(self):
    bench.STATE.mkdir()
    bench.save_state({'phase':'prepared', 'boot_id':'a'})
    original = bench.CONTINUE.read_bytes()
    real_atomic = bench.atomic
    def writable_data_only(path, *args, **kwargs):
      if path != bench.CONTINUE and not path.is_relative_to(bench.STATE):
        raise OSError(30, 'Read-only file system', str(path))
      return real_atomic(path, *args, **kwargs)
    with patch.object(bench, 'run') as run, patch.object(bench, 'atomic', side_effect=writable_data_only):
      bench.install_recovery()
      self.assertEqual((bench.STATE / 'continue-before.sh').read_bytes(), original)
      self.assertEqual(bench.CONTINUE.read_bytes(), bench.recovery_launcher(original))
      self.assertEqual(bench.CONTINUE.stat().st_mode & 0o777, 0o755)
      bench.restore_launcher(json.loads((bench.STATE / 'state.json').read_text()))
    run.assert_not_called()  # No systemctl enable or root filesystem changes.
    self.assertEqual(bench.CONTINUE.read_bytes(), original)

  def test_unknown_launcher_rejected_without_mutations(self):
    bench.CONTINUE.write_text('#!/bin/bash\nexec /data/other-program\n')
    with patch.object(bench, 'tree_hash', return_value=bench.PAYLOAD), patch.object(bench, 'run') as run:
      with self.assertRaisesRegex(ValueError, 'Unexpected /data/continue.sh'): bench.start()
    run.assert_not_called()
    self.assertFalse(bench.STATE.exists())

  def test_external_launcher_edit_is_not_overwritten(self):
    bench.STATE.mkdir(); bench.save_state({'phase':'prepared', 'boot_id':'a'})
    bench.install_recovery()
    bench.CONTINUE.write_bytes(b'changed by someone else')
    with self.assertRaisesRegex(ValueError, 'changed externally'):
      bench.restore_launcher(json.loads((bench.STATE / 'state.json').read_text()))
    self.assertEqual(bench.CONTINUE.read_bytes(), b'changed by someone else')

  def test_reboot_entry_restores_launcher_and_path_without_service_recursion(self):
    self.prepare_running()
    original = bench.CONTINUE.read_bytes()
    bench.install_recovery()
    bench.BOOT_ID_PATH.write_text('new-boot')
    with patch('sys.argv', ['control.py', 'boot-recover']), patch.object(bench.os, 'geteuid', return_value=0), \
         patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run') as run:
      bench.main()
    run.assert_not_called()
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)
    self.assertEqual(bench.CONTINUE.read_bytes(), original)
    self.assertEqual((bench.PARAMS / 'OpenpilotEnabledToggle').read_bytes(), b'0')

  def test_same_boot_guard_does_not_wait_for_start_lock(self):
    self.prepare_running()
    bench.BOOT_ID_PATH.write_text('a')
    with patch('sys.argv', ['control.py', 'boot-recover']), patch.object(bench.os, 'geteuid', return_value=0), \
         patch.object(bench.fcntl, 'flock', side_effect=AssertionError('would deadlock')):
      bench.main()
    self.assertEqual(bench.ACTIVE.resolve(), bench.RUNTIME)

  def test_failed_recovery_guard_blocks_original_launch(self):
    fake_bin = self.root / 'bin'; fake_bin.mkdir()
    sudo = fake_bin / 'sudo'; sudo.write_text('#!/bin/sh\nexit 42\n'); sudo.chmod(0o755)
    wrapper = self.root / 'wrapper.sh'
    wrapper.write_bytes(bench.recovery_launcher(b'echo SHOULD_NOT_START\n'))
    result = subprocess.run(['/bin/bash', str(wrapper)], capture_output=True, text=True,
                            env={**os.environ, 'PATH': str(fake_bin) + ':' + os.environ['PATH']})
    self.assertEqual(result.returncode, 42)
    self.assertNotIn('SHOULD_NOT_START', result.stdout)

  def make_failed_preflight(self):
    bench.STATE.mkdir()
    bench.save_state({'phase':'returned', 'boot_id':'a', 'payload_sha256':bench.PAYLOAD,
                      'previous':str(bench.PREVIOUS), 'runtime':str(bench.RUNTIME)})
    (bench.RUNTIME / '.git').mkdir()

  def test_retry_archives_proven_unstarted_attempt_and_reuses_git(self):
    self.make_failed_preflight()
    def command(*args, **kwargs):
      if args[-3:] == ('symbolic-ref', '--short', 'HEAD'): out = 'roadline-bench\n'
      elif args[-3:] == ('remote', 'get-url', 'origin'): out = 'https://github.com/visegrips70/Roadline.git\n'
      elif args[-3:] == ('log', '-1', '--format=%s'): out = 'Local bench metadata for source 2fbfa0c\n'
      else: out = ''
      return subprocess.CompletedProcess(args, 0, out, '')
    with patch.object(bench, 'tree_hash', return_value=bench.PAYLOAD), \
         patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', side_effect=command) as run:
      bench.start(retry_unstarted=True)
    self.assertTrue(bench.STATE.with_name(bench.STATE.name + '-before-rofs-fix').is_dir())
    self.assertEqual(bench.ACTIVE.resolve(), bench.RUNTIME)
    self.assertTrue((bench.STATE / 'params-before').is_dir())
    state = json.loads((bench.STATE / 'state.json').read_text())
    self.assertIn('launcher', state)
    self.assertIn('start_time', state)
    self.assertFalse(any('init' in c.args for c in run.call_args_list))
    self.assertFalse(any('enable' in c.args or 'daemon-reload' in c.args for c in run.call_args_list))

  def test_retry_refuses_a_previously_started_candidate(self):
    self.make_failed_preflight()
    state = json.loads((bench.STATE / 'state.json').read_text()); state['start_time'] = 123
    bench.save_state(state)
    with self.assertRaisesRegex(ValueError, 'pre-switch failure'): bench.retry_record()
    self.assertTrue(bench.STATE.is_dir())

  def test_retry_refuses_changed_payload_before_archiving_failure_record(self):
    self.make_failed_preflight()
    with patch.object(bench, 'run') as run:
      with self.assertRaisesRegex(ValueError, 'Runtime contents'): bench.start(retry_unstarted=True)
    run.assert_not_called()
    self.assertTrue(bench.STATE.is_dir())
    self.assertFalse(bench.STATE.with_name(bench.STATE.name + '-before-rofs-fix').exists())

  def test_retry_refuses_unknown_git_metadata_without_archiving(self):
    self.make_failed_preflight()
    with patch.object(bench, 'tree_hash', return_value=bench.PAYLOAD), \
         patch.object(bench, 'run', return_value=subprocess.CompletedProcess([], 0, 'other-branch\n', '')):
      with self.assertRaisesRegex(ValueError, 'Git metadata differs'): bench.start(retry_unstarted=True)
    self.assertTrue(bench.STATE.is_dir())
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)

  def test_failed_timer_restores_launcher_without_switching(self):
    original = bench.CONTINUE.read_bytes()
    def command(*args, **kwargs):
      if args[0] == 'systemd-run': raise subprocess.CalledProcessError(1, args)
      return subprocess.CompletedProcess(args, 0, '', '')
    with patch.object(bench, 'tree_hash', return_value=bench.PAYLOAD), \
         patch.object(bench, 'set_param', side_effect=self.fake_param), patch.object(bench, 'run', side_effect=command):
      with self.assertRaises(subprocess.CalledProcessError): bench.start()
    self.assertEqual(bench.CONTINUE.read_bytes(), original)
    self.assertEqual(bench.ACTIVE.resolve(), bench.PREVIOUS)
    self.assertFalse((bench.STATE / 'params-before').exists())
    self.assertNotIn('start_time', json.loads((bench.STATE / 'state.json').read_text()))

if __name__ == '__main__': unittest.main()
