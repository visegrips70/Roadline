#!/usr/bin/env python3
"""Apply or undo the pinned Python-only passive-startup correction offroad.

Does not write settings, firmware, the original package, launcher or prior install.
The running c79c68f candidate gets a local-change receipt; it is not a new release.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

DATA = Path('/data')
VERSION = Path('/VERSION')
MODEL = Path('/sys/firmware/devicetree/base/model')
BASE = 'c79c68fe5dac6d9668aadb6a64ee7b0557e89599'
FIX = '99f383b43ecd7c97a976ef9ec4dae40231d645f0'
OLD_SHA = 'b85a8af7062b9a6b7ea0ea44398eb022ea7df0433021c1dd8eb2980ac10d06fd'
NEW_SHA = '669311aa4175bf1e391da2f3aa537f52552a0c609efc0565f0aad505d46625cc'
PANDA_SHA = '8ece3dee9a1fb90f8d048272ea26a7bf26f6646e18e0100802b77bbec8eb0fc0'
RELATIVE = Path('selfdrive/car/card.py')
DISABLED = ('OpenpilotEnabledToggle', 'NAPPedalEnabled', 'NAPRadarEnabled',
            'NAPiBoosterEnabled', 'NAPNavigationManeuvers', 'NAPMapDrivingAssist')
MARKER = b'    self.params.put("CarParams", cp_bytes)\n'
ADDITION = (b'    if self.CP.passive:\n' +
            b'      # Passive mode never calls controls_update/CI.init. Its persisted safety\n' +
            b'      # configuration is noOutput, so let pandad finish diagnostic mode now.\n' +
            b'      self.params.put_bool("ControlsReady", True)\n')


def sha(data):
  return hashlib.sha256(data).hexdigest()


def atomic(path, data, mode=0o600, owner=None):
  fd, name = tempfile.mkstemp(prefix='.roadline-passive-', dir=path.parent)
  try:
    with os.fdopen(fd, 'wb') as f:
      f.write(data)
      os.fchmod(f.fileno(), mode)
      if owner is not None:
        os.fchown(f.fileno(), *owner)
      f.flush()
      os.fsync(f.fileno())
    os.replace(name, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory)
    finally:
      os.close(directory)
  finally:
    Path(name).unlink(missing_ok=True)


def run(*args):
  subprocess.run(args, check=True, timeout=60, capture_output=True, text=True)


def locations():
  root = DATA / 'roadline-runtime-c79c68f'
  recovery = DATA / 'roadline-cruise-recovery-c79c68f'
  return root, recovery, root / RELATIVE, recovery / 'card-before-passive-fix.py', root / 'roadline_local_changes.json'


def validate():
  root, recovery, target, backup, receipt = locations()
  if VERSION.read_text().strip() != '17.2' or MODEL.read_bytes().rstrip(b'\0') != b'comma tizi':
    raise ValueError('Expected Comma 3X on AGNOS 17.2.')
  active = DATA / 'openpilot'
  if root.is_symlink() or not active.is_symlink() or active.resolve() != root:
    raise ValueError('Expected the active c79c68f candidate symlink.')
  if target.is_symlink() or target.resolve() != target or not target.is_file():
    raise ValueError('Unexpected car daemon path.')
  if recovery.is_symlink() or not recovery.is_dir():
    raise ValueError('Expected first-start recovery directory.')
  state = json.loads((recovery / 'state.json').read_text())
  if state.get('phase') != 'running' or state.get('revision') != BASE:
    raise ValueError('Expected the running c79c68f recovery state.')
  release = json.loads((root / 'roadline_release.json').read_text())
  if release.get('source_revision') != BASE or release.get('road_ready') is not False:
    raise ValueError('Unexpected base release.')
  if sha((root / 'panda/board/obj/panda_h7.bin.signed').read_bytes()) != PANDA_SHA:
    raise ValueError('Panda firmware differs; no firmware changes are allowed here.')
  params = DATA / 'params/d'
  for key, value in [('IsOnroad', b'0'), ('DisableUpdates', b'1'), *[(k, b'0') for k in DISABLED]]:
    if (params / key).read_bytes().strip() != value:
      raise ValueError(f'{key} must be {value.decode()}; keep the car off and assistance disabled.')
  for key in ('DoReboot', 'DoShutdown', 'DoUninstall', 'NAPScriptRunning'):
    path = params / key
    if path.exists() and path.read_bytes().strip() not in (b'', b'0'):
      raise ValueError('Pending device action: ' + key)
  # Native Git checkouts can retain group write permission (umask 0002).
  # The operator verified 0775 in both the installed and pristine c79 package.
  mode = stat.S_IMODE(target.stat().st_mode)
  if mode not in (0o755, 0o775):
    raise ValueError(f'Unexpected car daemon permissions: {mode:04o}; expected 0755 or 0775.')
  if sha(target.read_bytes()) not in (OLD_SHA, NEW_SHA):
    raise ValueError('Car daemon contents differ from the reviewed files.')
  if backup.is_symlink() or (backup.exists() and sha(backup.read_bytes()) != OLD_SHA):
    raise ValueError('Existing file backup differs; it will not be overwritten.')
  if receipt.is_symlink():
    raise ValueError('Unexpected local-change receipt symlink.')
  if receipt.exists() and receipt.read_bytes() != receipt_bytes():
    raise ValueError('Other local changes are recorded; inspect before updating.')


def receipt_bytes():
  return (json.dumps(dict(schema_version=1, base_source_revision=BASE, road_ready=False,
                         changes=[dict(path=str(RELATIVE), source_revision=FIX, sha256=NEW_SHA)]), indent=2) + '\n').encode()


def update(action):
  validate()
  root, recovery, target, backup, receipt = locations()
  current = target.read_bytes()
  before_receipt = receipt.read_bytes() if receipt.exists() else None
  info = target.stat()
  mode = stat.S_IMODE(info.st_mode)
  owner = (info.st_uid, info.st_gid)
  if sha(current) == NEW_SHA and not backup.is_file():
    raise ValueError('Patched file has no verified backup; inspect before continuing.')
  original = backup.read_bytes() if backup.exists() else current
  if sha(original) != OLD_SHA or original.count(MARKER) != 1:
    raise ValueError('Original file does not match the patch baseline.')
  changed = original.replace(MARKER, MARKER + ADDITION, 1)
  if sha(changed) != NEW_SHA:
    raise ValueError('Generated correction failed checksum validation.')
  compile(changed, str(target), 'exec')
  desired = changed if action == 'apply' else original
  wanted_receipt = receipt_bytes() if action == 'apply' else None
  if current == desired and before_receipt == wanted_receipt:
    print('Requested file state already present; service was not restarted.')
    return
  if not backup.exists():
    atomic(backup, original)
  validate()
  run('systemctl', 'stop', 'comma.service')
  try:
    validate()
    if target.read_bytes() != current or stat.S_IMODE(target.stat().st_mode) != mode:
      raise ValueError('Car daemon changed during service stop.')
    atomic(target, desired, mode=mode, owner=owner)
    if target.read_bytes() != desired or stat.S_IMODE(target.stat().st_mode) != mode:
      raise ValueError('Car daemon readback failed.')
    if wanted_receipt is None:
      receipt.unlink(missing_ok=True)
    else:
      atomic(receipt, wanted_receipt, mode=0o644, owner=owner)
    run('systemctl', 'start', 'comma.service')
  except Exception:
    # Restore only our known file contents; never overwrite an external change.
    try:
      if sha(target.read_bytes()) not in (OLD_SHA, NEW_SHA) or stat.S_IMODE(target.stat().st_mode) != mode:
        raise ValueError('Car daemon changed externally.')
      atomic(target, current, mode=mode, owner=owner)
      if before_receipt is None:
        receipt.unlink(missing_ok=True)
      else:
        atomic(receipt, before_receipt, mode=0o644, owner=owner)
      validate()
      run('systemctl', 'start', 'comma.service')
    except Exception as recovery_error:
      raise RuntimeError('Update did not complete and automatic restart was blocked; ' +
                         'keep assistance disabled and inspect before restarting.') from recovery_error
    raise
  print('PASSIVE STARTUP FIX ' + ('APPLIED' if action == 'apply' else 'REMOVED'))
  print('Car daemon SHA256: ' + sha(target.read_bytes()))
  print(f'Car daemon permissions preserved: {mode:04o}')
  print('Backup: ' + str(backup))
  print('Service restart requested; live noOutput verification remains required.')
  print('Base release remains c79c68f; firmware files and calibration settings were not edited.')
  print('Assistance remains disabled. This is not a road-ready release.')


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('action', choices=('apply', 'rollback'))
  args = parser.parse_args()
  if os.geteuid() != 0:
    parser.error('Run using sudo -n /usr/bin/python3.')
  with (DATA / 'roadline-cruise-first-start.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    update(args.action)


if __name__ == '__main__':
  main()
