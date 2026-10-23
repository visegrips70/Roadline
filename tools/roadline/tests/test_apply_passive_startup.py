"""File transactions use real temporary files; services and device facts are simulated."""
import json
from pathlib import Path
import subprocess

import pytest

from openpilot.tools.roadline import apply_passive_startup as update


@pytest.fixture
def device(tmp_path, monkeypatch):
  monkeypatch.setattr(update, 'DATA', tmp_path)
  monkeypatch.setattr(update, 'VERSION', tmp_path / 'VERSION')
  monkeypatch.setattr(update, 'MODEL', tmp_path / 'MODEL')
  update.VERSION.write_text('17.2\n')
  update.MODEL.write_bytes(b'comma tizi\0')
  root, recovery, target, backup, receipt = update.locations()
  target.parent.mkdir(parents=True)
  recovery.mkdir(mode=0o700)
  original = b'def startup(self, cp_bytes):\n' + update.MARKER
  changed = original.replace(update.MARKER, update.MARKER + update.ADDITION)
  monkeypatch.setattr(update, 'OLD_SHA', update.sha(original))
  monkeypatch.setattr(update, 'NEW_SHA', update.sha(changed))
  firmware = b'synthetic-firmware'
  monkeypatch.setattr(update, 'PANDA_SHA', update.sha(firmware))
  panda = root / 'panda/board/obj/panda_h7.bin.signed'
  panda.parent.mkdir(parents=True)
  panda.write_bytes(firmware)
  target.write_bytes(original)
  target.chmod(0o755)
  (tmp_path / 'openpilot').symlink_to(root)
  release = dict(source_revision=update.BASE, road_ready=False)
  (root / 'roadline_release.json').write_text(json.dumps(release))
  (recovery / 'state.json').write_text(json.dumps(dict(revision=update.BASE, phase='running')))
  params = tmp_path / 'params/d'
  params.mkdir(parents=True)
  for key, value in dict(IsOnroad='0', DisableUpdates='1', **dict.fromkeys(update.DISABLED, '0'),
                         NAPPedalCalibDone='1', NAPPedalCalibFactor='0.9').items():
    (params / key).write_text(value)
  calls = []
  monkeypatch.setattr(update, 'run', lambda *args: calls.append(args))
  return dict(root=root, recovery=recovery, target=target, backup=backup, receipt=receipt,
              original=original, changed=changed, params=params, calls=calls, panda=panda)


def test_apply_preserves_calibration_firmware_metadata_and_file_mode(device):
  d = device
  before = {p.name: p.read_bytes() for p in d['params'].iterdir()}
  release_before = (d['root'] / 'roadline_release.json').read_bytes()
  update.update('apply')
  assert d['target'].read_bytes() == d['changed']
  assert d['backup'].read_bytes() == d['original']
  assert d['target'].stat().st_mode & 0o777 == 0o755
  assert d['backup'].stat().st_mode & 0o777 == 0o600
  assert {p.name: p.read_bytes() for p in d['params'].iterdir()} == before
  assert d['panda'].read_bytes() == b'synthetic-firmware'
  assert (d['root'] / 'roadline_release.json').read_bytes() == release_before
  assert d['receipt'].read_bytes() == update.receipt_bytes()
  assert d['calls'] == [('systemctl', 'stop', 'comma.service'), ('systemctl', 'start', 'comma.service')]
  update.update('apply')
  assert len(d['calls']) == 2


def test_rollback_restores_original_file_and_removes_only_our_receipt(device):
  update.update('apply')
  update.update('rollback')
  assert device['target'].read_bytes() == device['original']
  assert device['backup'].read_bytes() == device['original']
  assert not device['receipt'].exists()


@pytest.mark.parametrize('key', ['IsOnroad', *update.DISABLED])
@pytest.mark.parametrize('missing', [False, True])
def test_unsafe_or_missing_state_blocks_before_backup_or_service_stop(device, key, missing):
  path = device['params'] / key
  if missing:
    path.unlink()
  else:
    path.write_text('1')
  with pytest.raises((ValueError, FileNotFoundError)):
    update.update('apply')
  assert device['target'].read_bytes() == device['original']
  assert not device['backup'].exists()
  assert device['calls'] == []


@pytest.mark.parametrize('file', ['target', 'panda', 'backup', 'receipt'])
def test_unknown_files_are_never_overwritten(device, file):
  device[file].write_bytes(b'unknown contents')
  with pytest.raises((ValueError, FileNotFoundError)):
    update.update('apply')
  assert device[file].read_bytes() == b'unknown contents'
  assert device['calls'] == []


def test_failed_service_restart_restores_prior_contents(device, monkeypatch):
  def run(*args):
    device['calls'].append(args)
    if args[1] == 'start' and len(device['calls']) == 2:
      raise subprocess.CalledProcessError(1, args)
  monkeypatch.setattr(update, 'run', run)
  with pytest.raises(subprocess.CalledProcessError):
    update.update('apply')
  assert device['target'].read_bytes() == device['original']
  assert not device['receipt'].exists()
  assert device['calls'][-1] == ('systemctl', 'start', 'comma.service')


def test_interruption_after_file_swap_can_be_completed_with_verified_backup(device):
  device['backup'].write_bytes(device['original'])
  device['target'].write_bytes(device['changed'])
  update.update('apply')
  assert device['receipt'].read_bytes() == update.receipt_bytes()
  assert device['backup'].read_bytes() == device['original']


def test_patched_file_without_backup_is_not_accepted(device):
  device['target'].write_bytes(device['changed'])
  with pytest.raises(ValueError, match='no verified backup'):
    update.update('apply')
  assert device['calls'] == []


def test_vehicle_waking_during_stop_blocks_write_and_restart(device, monkeypatch):
  def run(*args):
    device['calls'].append(args)
    if args[1] == 'stop':
      (device['params'] / 'IsOnroad').write_text('1')
  monkeypatch.setattr(update, 'run', run)
  with pytest.raises(RuntimeError, match='automatic restart was blocked'):
    update.update('apply')
  assert device['target'].read_bytes() == device['original']
  assert device['calls'] == [('systemctl', 'stop', 'comma.service')]


def test_external_edit_during_service_stop_is_preserved(device, monkeypatch):
  def run(*args):
    device['calls'].append(args)
    if args[1] == 'stop':
      device['target'].write_bytes(b'external edit')
  monkeypatch.setattr(update, 'run', run)
  with pytest.raises(RuntimeError, match='automatic restart was blocked'):
    update.update('apply')
  assert device['target'].read_bytes() == b'external edit'
  assert device['calls'] == [('systemctl', 'stop', 'comma.service')]


def test_incorrect_generated_checksum_blocks_before_service_stop(device, monkeypatch):
  monkeypatch.setattr(update, 'NEW_SHA', '0' * 64)
  with pytest.raises(ValueError, match='checksum'):
    update.update('apply')
  assert device['target'].read_bytes() == device['original']
  assert device['calls'] == []


def test_system_paths_are_not_followed_from_an_unexpected_active_link(device):
  active = update.DATA / 'openpilot'
  active.unlink()
  active.symlink_to(Path('/tmp'))
  with pytest.raises(ValueError, match='candidate symlink'):
    update.update('apply')
  assert device['calls'] == []
