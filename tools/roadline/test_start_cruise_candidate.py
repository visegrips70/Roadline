"""First-start transaction tests use temporary files and simulated services only."""
# ruff: noqa: TID251 -- stdlib-only recovery tests run on hosts without pytest.
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cruise_start', Path(__file__).with_name('start_cruise_candidate.py'))
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class PowerLoss(BaseException):
  pass


class FirstStartTests(unittest.TestCase):
  def setUp(self):
    tmp = tempfile.TemporaryDirectory()
    self.addCleanup(tmp.cleanup)
    self.root = Path(tmp.name)
    for name in ('DATA', 'ACTIVE', 'PACKAGE', 'RUNTIME', 'PREVIOUS', 'STATE', 'CONTINUE', 'PARAMS', 'LOCK', 'VERSION', 'MODEL'):
      value = self.root if name == 'DATA' else self.root / name
      p = patch.object(helper, name, value)
      p.start()
      self.addCleanup(p.stop)
    helper.PARAMS.mkdir()
    for name, value in {'IsOnroad': '0', 'OpenpilotEnabledToggle': '0', 'NAPPedalEnabled': '0',
                        'DisableUpdates': '1', 'NAPPedalCalibDone': '1', 'NAPPedalCanBus': '2',
                        'NAPPedalCalibFactor': '0.8', 'NAPRadarEnabled': '0', 'GitCommit': 'original'}.items():
      (helper.PARAMS / name).write_text(value)
    helper.VERSION.write_text('17.2\n')
    helper.MODEL.write_bytes(b'comma tizi\0')
    helper.CONTINUE.write_bytes(b'#!/usr/bin/env bash\n\ncd /data/openpilot\nexec ./launch_openpilot.sh\n')
    helper.CONTINUE.chmod(0o755)
    self.original_launcher = helper.CONTINUE.read_bytes()
    helper.ACTIVE.mkdir()
    self.make_runtime(helper.ACTIVE, helper.OLD_REVISION, b'old-panda')
    source = helper.PACKAGE / 'runtime'
    source.mkdir(parents=True)
    self.make_runtime(source, helper.REVISION, b'new-panda')
    for name, value in [('OLD_PANDA', helper.digest(helper.ACTIVE / helper.PANDA)),
                        ('NEW_PANDA', helper.digest(source / helper.PANDA)),
                        ('PAYLOAD', helper.tree_hash(source))]:
      p = patch.object(helper, name, value)
      p.start()
      self.addCleanup(p.stop)
    (helper.PACKAGE / 'report.json').write_text(json.dumps({
      'source_revision': helper.REVISION, 'payload_sha256': helper.PAYLOAD,
      'blockers': ['No exact-payload validation evidence supplied; publication is blocked.']}))
    p = patch.object(helper, 'comma_owner', return_value=(os.getuid(), os.getgid()))
    p.start()
    self.addCleanup(p.stop)
    command = patch.object(helper, 'run', side_effect=self.fake_run)
    self.command = command.start()
    self.addCleanup(command.stop)
    self.stopped = False

  def make_runtime(self, root, revision, firmware):
    (root / 'roadline_release.json').write_text(json.dumps({
      'source_revision': revision, 'channel': 'staging', 'road_ready': False,
      'target': {'model': 'comma tizi', 'architecture': 'aarch64', 'agnos': '17.2'}}))
    (root / helper.PANDA).parent.mkdir(parents=True)
    (root / helper.PANDA).write_bytes(firmware)
    (root / 'prebuilt').touch()
    (root / 'launch_openpilot.sh').write_text('original launcher')
    (root / 'launch_openpilot.sh').chmod(0o755)
    (root / 'openpilot').symlink_to('.')

  def fake_run(self, *args, **kwargs):
    if args == ('systemctl', 'stop', 'comma.service'):
      self.stopped = True
    if args == ('systemctl', 'start', 'comma.service'):
      self.stopped = False
    return subprocess.CompletedProcess(args, 0, 'active\n', '')

  def assert_disabled(self):
    for key in helper.DISABLED:
      self.assertEqual((helper.PARAMS / key).read_bytes(), b'0')
    self.assertEqual((helper.PARAMS / 'DisableUpdates').read_bytes(), b'1')

  def assert_returned(self):
    self.assertFalse(helper.ACTIVE.is_symlink())
    self.assertEqual(helper.digest(helper.ACTIVE / helper.PANDA), helper.OLD_PANDA)
    self.assertEqual(helper.CONTINUE.read_bytes(), self.original_launcher)
    self.assert_disabled()
    self.assertEqual((helper.PARAMS / 'NAPPedalCalibFactor').read_bytes(), b'0.8')

  def test_success_preserves_package_installation_settings_and_reboot_selection(self):
    helper.start()
    self.assertEqual(helper.ACTIVE.resolve(), helper.RUNTIME)
    self.assertEqual(helper.tree_hash(helper.PACKAGE / 'runtime'), helper.PAYLOAD)
    self.assertEqual(helper.digest(helper.PREVIOUS / helper.PANDA), helper.OLD_PANDA)
    self.assertEqual(helper.read_state()['phase'], 'running')
    self.assert_disabled()
    self.assertEqual(helper.STATE.stat().st_mode & 0o777, 0o700)
    (helper.PARAMS / 'NAPPedalEnabled').write_text('1')
    helper.boot_check()
    self.assert_disabled()
    self.assertEqual(helper.ACTIVE.resolve(), helper.RUNTIME)
    self.assertFalse(any(c.args[0] == 'systemd-run' for c in self.command.call_args_list))

  def test_rollback_restores_directory_and_settings_without_enabling_controls(self):
    helper.start()
    (helper.PARAMS / 'NAPPedalCalibFactor').write_text('99')
    (helper.PARAMS / 'NAPNewDefault').write_text('1')
    (helper.PARAMS / 'GitCommit').write_text('candidate')
    helper.rollback()
    self.assert_returned()
    self.assertFalse((helper.PARAMS / 'NAPNewDefault').exists())
    self.assertEqual((helper.PARAMS / 'GitCommit').read_text(), 'candidate')
    self.assertTrue(helper.RUNTIME.exists())
    self.assertEqual(helper.read_state()['phase'], 'returned')
    self.command.reset_mock()
    helper.rollback()
    self.command.assert_not_called()

  def test_repeated_start_refuses_before_commands_or_backup_overwrite(self):
    helper.start()
    before = (helper.STATE / 'settings-before.json').read_bytes()
    self.command.reset_mock()
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()
    self.assertEqual(before, (helper.STATE / 'settings-before.json').read_bytes())

  def test_onroad_rejected_before_copy_or_service_change(self):
    (helper.PARAMS / 'IsOnroad').write_text('1')
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()
    self.assertFalse(helper.RUNTIME.exists())

  def test_assistance_enabled_or_updates_enabled_rejected(self):
    for key, value, restore in [('OpenpilotEnabledToggle', '1', '0'), ('NAPPedalEnabled', '1', '0'), ('DisableUpdates', '0', '1')]:
      (helper.PARAMS / key).write_text(value)
      with self.assertRaises(ValueError):
        helper.start()
      (helper.PARAMS / key).write_text(restore)
    self.command.assert_not_called()

  def test_payload_bytes_and_execute_mode_tamper_rejected(self):
    p = helper.PACKAGE / 'runtime/launch_openpilot.sh'
    p.chmod(0o644)
    with self.assertRaises(ValueError):
      helper.start()
    p.chmod(0o755)
    p.write_text('modified')
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()

  def test_external_package_symlink_rejected(self):
    (helper.PACKAGE / 'runtime/escape').symlink_to('/etc/passwd')
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()

  def test_unknown_active_symlink_rejected(self):
    helper.ACTIVE.rename(self.root / 'other')
    helper.ACTIVE.symlink_to(self.root / 'other')
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()

  def test_unexpected_launcher_rejected(self):
    helper.CONTINUE.write_text('unexpected startup')
    with self.assertRaises(ValueError):
      helper.start()
    self.command.assert_not_called()

  def test_snapshot_failure_restarts_original_without_switch(self):
    with patch.object(helper, 'save_settings', side_effect=OSError('disk full')):
      with self.assertRaises(OSError):
        helper.start()
    self.assertFalse(self.stopped)
    self.assertFalse(helper.ACTIVE.is_symlink())
    self.assertFalse(helper.PREVIOUS.exists())
    self.assertEqual(helper.CONTINUE.read_bytes(), self.original_launcher)

  def test_service_start_failure_rolls_back(self):
    starts = 0
    def fake(*args, **kwargs):
      nonlocal starts
      if args == ('systemctl', 'start', 'comma.service'):
        starts += 1
        if starts == 1:
          raise subprocess.CalledProcessError(1, args)
      return self.fake_run(*args, **kwargs)
    self.command.side_effect = fake
    with self.assertRaises(subprocess.CalledProcessError):
      helper.start()
    self.assert_returned()
    self.assertEqual(starts, 2)

  def test_power_loss_after_directory_rename_recovers_on_boot(self):
    original_rename = os.rename
    def rename(source, destination):
      original_rename(source, destination)
      if source == helper.ACTIVE:
        raise PowerLoss()
    with patch.object(helper.os, 'rename', side_effect=rename):
      with self.assertRaises(PowerLoss):
        helper.start()
    self.assertFalse(helper.ACTIVE.exists())
    self.command.reset_mock()
    helper.boot_check()
    self.command.assert_not_called()
    self.assert_returned()

  def test_power_loss_after_link_switch_recovers_on_boot(self):
    install = helper.install_link
    def interrupted():
      install()
      raise PowerLoss()
    with patch.object(helper, 'install_link', side_effect=interrupted):
      with self.assertRaises(PowerLoss):
        helper.start()
    self.assertEqual(helper.ACTIVE.resolve(), helper.RUNTIME)
    helper.boot_check()
    self.assert_returned()

  def test_power_loss_during_rollback_gap_recovers_on_boot(self):
    helper.start()
    rename = os.rename
    def interrupted(source, destination):
      if source == helper.PREVIOUS:
        raise PowerLoss()
      rename(source, destination)
    with patch.object(helper.os, 'rename', side_effect=interrupted):
      with self.assertRaises(PowerLoss):
        helper.rollback()
    self.assertFalse(helper.ACTIVE.exists())
    helper.boot_check()
    self.assert_returned()

  def test_unknown_active_path_blocks_rollback_before_service_stop(self):
    helper.start()
    helper.ACTIVE.unlink()
    helper.ACTIVE.symlink_to(self.root / 'unrelated')
    self.command.reset_mock()
    with self.assertRaises(ValueError):
      helper.rollback()
    self.command.assert_not_called()
    self.assertTrue(helper.PREVIOUS.exists())

  def test_corrupt_snapshot_or_launcher_blocks_rollback(self):
    helper.start()
    snapshot = helper.STATE / 'settings-before.json'
    original = snapshot.read_bytes()
    snapshot.write_text('{}')
    self.command.reset_mock()
    with self.assertRaises(ValueError):
      helper.rollback()
    self.command.assert_not_called()
    snapshot.write_bytes(original)
    helper.CONTINUE.write_text('externally modified')
    with self.assertRaises(ValueError):
      helper.rollback()
    self.command.assert_not_called()

  def test_onroad_rollback_refuses_before_service_stop(self):
    helper.start()
    (helper.PARAMS / 'IsOnroad').write_text('1')
    self.command.reset_mock()
    with self.assertRaises(ValueError):
      helper.rollback()
    self.command.assert_not_called()

  def test_failed_manager_missing_onroad_parameter_does_not_block_recovery(self):
    helper.start()
    (helper.PARAMS / 'IsOnroad').unlink()
    helper.rollback()
    self.assert_returned()

  def test_runtime_metadata_uses_real_local_git_and_keeps_payload_unchanged(self):
    def command(*args, **kwargs):
      if args[:5] == ('sudo', '-n', '-u', 'comma', 'git'):
        return subprocess.run(args[4:], capture_output=True, text=True, check=True,
                              env={**os.environ, 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_NOSYSTEM': '1'})
      return self.fake_run(*args, **kwargs)
    self.command.side_effect = command
    helper.start()
    self.assertTrue((helper.RUNTIME / '.git').is_dir())
    branch = subprocess.check_output(['git', '-C', str(helper.RUNTIME), 'branch', '--show-current'], text=True)
    self.assertEqual(branch.strip(), 'roadline-cruise-staging')
    self.assertEqual(helper.tree_hash(helper.RUNTIME), helper.PAYLOAD)


if __name__ == '__main__':
  unittest.main()
