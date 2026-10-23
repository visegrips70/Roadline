#!/usr/bin/env python3
"""One timed, vehicle-disconnected bench boot of the reviewed 2fbfa0c package."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import time

ACTIVE = Path('/data/openpilot')
PREVIOUS = Path('/data/roadline-candidate-5de8b00')
RUNTIME = Path('/data/roadline-repackage.qhnsNW/output/runtime')
STATE = Path('/data/roadline-bench-2fbfa0c')
PARAMS = Path('/data/params/d')
NAP_BACKUP = Path('/data/nap-before-roadline-e99f4dc')
VERSION_PATH = Path('/VERSION')
MODEL_PATH = Path('/sys/firmware/devicetree/base/model')
BOOT_ID_PATH = Path('/proc/sys/kernel/random/boot_id')
PAYLOAD = 'a93bec8362161c117c36139842c253cbb32bfb7135ac0bc3c7bb7137babdecea'
GUARD = 'roadline-bench-recover.service'
TIMER = 'roadline-bench-return-2fbfa0c'
DURATION = 180


def run(*args, check=True, timeout=60):
  return subprocess.run(args, check=check, capture_output=True, text=True, timeout=timeout)


def atomic(path, data, mode=0o600, owner=None):
  tmp = path.with_name('.roadline-tmp-' + path.name)
  fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
  try:
    with os.fdopen(fd, 'wb') as f:
      f.write(data); f.flush(); os.fsync(f.fileno())
    if owner is not None:
      os.chown(tmp, owner.pw_uid, owner.pw_gid)
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
  finally:
    tmp.unlink(missing_ok=True)


def set_param(name, value):
  atomic(PARAMS / name, value, owner=pwd.getpwnam('comma'))


def tree_hash(root):
  digest = hashlib.sha256()
  for parent, dirs, files in os.walk(root, followlinks=False):
    dirs[:] = sorted(d for d in dirs if d != '.git')
    entries = sorted(files + [d for d in dirs if (Path(parent) / d).is_symlink()])
    for name in entries:
      p = Path(parent) / name
      rel = p.relative_to(root).as_posix()
      if p.is_symlink():
        if os.path.isabs(os.readlink(p)) or not p.resolve().is_relative_to(root) or not p.exists():
          raise ValueError('Nonportable runtime link: ' + rel)
        record = [rel, 'symlink', os.readlink(p)]
      elif p.is_file():
        h = hashlib.sha256()
        with p.open('rb') as f:
          for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
        record = [rel, 'file', bool(p.stat().st_mode & 0o100), h.hexdigest()]
      else:
        raise ValueError('Unsupported runtime entry: ' + rel)
      digest.update((json.dumps(record, separators=(',', ':')) + '\n').encode())
  return digest.hexdigest()


def replace_link(active, target, permitted):
  if not active.is_symlink() or active.resolve() not in permitted:
    raise ValueError('Active installation changed unexpectedly; refusing to replace it.')
  temporary = active.with_name('.roadline-bench-link')
  if temporary.exists() or temporary.is_symlink():
    raise ValueError('Temporary switch path already exists.')
  temporary.symlink_to(target)
  try: os.replace(temporary, active)
  finally: temporary.unlink(missing_ok=True)
  fd = os.open(active.parent, os.O_RDONLY | os.O_DIRECTORY)
  try: os.fsync(fd)
  finally: os.close(fd)


def save_state(state):
  atomic(STATE / 'state.json', (json.dumps(state, indent=2) + '\n').encode())


def snapshot_params():
  staging = STATE / 'params-copying'
  shutil.copytree(PARAMS.resolve(), staging, symlinks=True)
  for parent, _, files in os.walk(staging, topdown=False):
    for name in files:
      path = Path(parent) / name
      if path.is_file() and not path.is_symlink():
        with path.open('rb') as f: os.fsync(f.fileno())
    fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
  os.replace(staging, STATE / 'params-before')
  fd = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY)
  try: os.fsync(fd)
  finally: os.close(fd)


def boot_id():
  return BOOT_ID_PATH.read_text().strip()


def state_requires_boot_recovery(state, current_boot):
  return state.get('phase') != 'returned' and state['boot_id'] != current_boot


def install_recovery():
  helper = STATE / 'control.py'
  unit = ('[Unit]\nDescription=Restore Roadline bench test after reboot\n'
          'After=local-fs.target\nBefore=comma.service\n'
          '[Service]\nType=oneshot\nRemainAfterExit=yes\n'
          f'ExecStart=/usr/bin/python3 {helper} boot-recover\n'
          '[Install]\nWantedBy=multi-user.target\n')
  dropin = Path('/etc/systemd/system/comma.service.d/roadline-bench.conf')
  dropin.parent.mkdir(parents=True, exist_ok=True)
  if dropin.exists() or Path('/etc/systemd/system', GUARD).exists():
    raise ValueError('A bench recovery service already exists; review it before another test.')
  atomic(Path('/etc/systemd/system', GUARD), unit.encode(), mode=0o644)
  atomic(dropin, ('[Unit]\nRequires=' + GUARD + '\nAfter=' + GUARD + '\n').encode(), mode=0o644)
  run('systemctl', 'daemon-reload')
  run('systemctl', 'enable', GUARD)


def start():
  if STATE.exists(): raise ValueError('A bench test record already exists; run status or rollback.')
  if VERSION_PATH.read_text().strip() != '17.2': raise ValueError('AGNOS 17.2 required.')
  if MODEL_PATH.read_bytes().rstrip(b'\x00') != b'comma tizi':
    raise ValueError('This helper is only for comma 3X.')
  if (PARAMS / 'IsOnroad').read_text().strip() != '0': raise ValueError('Off-road state required.')
  if not ACTIVE.is_symlink() or ACTIVE.resolve() != PREVIOUS or not PREVIOUS.is_dir():
    raise ValueError('The active installation is not the verified previous Roadline checkout.')
  if not NAP_BACKUP.is_dir(): raise ValueError('NAP backup is missing.')
  if (RUNTIME / '.overlay_init').exists(): raise ValueError('Unexpected updater overlay marker.')
  if (RUNTIME / '.git').exists(): raise ValueError('Runtime already has Git metadata; review before retrying.')
  if not (RUNTIME / 'prebuilt').is_file() or tree_hash(RUNTIME) != PAYLOAD:
    raise ValueError('Runtime contents or modes differ from the verified package.')
  for name in ('DoUninstall', 'DoReboot', 'DoShutdown'):
    p = PARAMS / name
    if p.exists() and p.read_text().strip() not in ('', '0'): raise ValueError('Pending device action: ' + name)
  run('sudo', '-n', '-u', 'comma', 'git', '-C', str(RUNTIME), 'init', '-b', 'roadline-bench')
  run('sudo', '-n', '-u', 'comma', 'git', '-C', str(RUNTIME), 'add', '--all')
  run('sudo', '-n', '-u', 'comma', 'git', '-C', str(RUNTIME), '-c', 'user.name=Roadline bench',
      '-c', 'user.email=roadline@localhost', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
      'commit', '-m', 'Local bench metadata for source 2fbfa0c', timeout=180)
  run('sudo', '-n', '-u', 'comma', 'git', '-C', str(RUNTIME), 'remote', 'add', 'origin',
      'https://github.com/visegrips70/Roadline.git')
  STATE.mkdir(mode=0o700)
  shutil.copy2(Path(__file__), STATE / 'control.py')
  state = {'phase': 'prepared', 'boot_id': boot_id(), 'payload_sha256': PAYLOAD,
           'previous': str(PREVIOUS), 'runtime': str(RUNTIME), 'duration_seconds': DURATION}
  save_state(state)
  try:
    install_recovery()
    run('systemd-run', '--unit=' + TIMER, '--on-active=180s', '--timer-property=AccuracySec=1s',
        '/usr/bin/python3', str(STATE / 'control.py'), 'rollback')
    run('systemctl', 'is-active', '--quiet', TIMER + '.timer')
    if (PARAMS / 'IsOnroad').read_text().strip() != '0': raise ValueError('Car became on-road; test aborted.')
    run('systemctl', 'stop', 'comma.service')
    snapshot_params()
    set_param('OpenpilotEnabledToggle', b'0')
    set_param('DisableUpdates', b'1')
    state['phase'] = 'armed'; save_state(state)
    replace_link(ACTIVE, RUNTIME, {PREVIOUS})
    state['phase'] = 'running'; state['start_time'] = time.time(); save_state(state)
    run('systemctl', 'start', 'comma.service')
  except Exception:
    rollback()
    raise
  print('BENCH TEST STARTED. Assistance and automatic updates are disabled.')
  print('Automatic return to the previous installation is scheduled in about three minutes.')
  print('Keep the vehicle disconnected. Observe the startup animation and home screen.')


def restore_saved_settings():
  saved = STATE / 'params-before'
  if saved.is_dir():
    # Preserve the full local snapshot for review. Restore driving settings and
    # calibration, not transient manager state, access tokens, or process PIDs.
    names = {'CalibrationParams', 'LiveParameters', 'LiveTorqueParameters',
             'LaneOffsetCm', 'PreAPLaneCentering', 'DisableUpdates'}
    for name in {p.name for p in saved.iterdir()} | {p.name for p in PARAMS.iterdir()}:
      if name.startswith(('NAP', 'Roadline')) or name in names:
        p = saved / name
        if p.is_file() and not p.is_symlink():
          set_param(name, p.read_bytes())
        elif not p.exists() and not p.is_symlink():
          # Also undo defaults introduced by the candidate during first boot.
          (PARAMS / name).unlink(missing_ok=True)
  # Never re-enable assistance automatically, even if it was on before testing.
  set_param('OpenpilotEnabledToggle', b'0')
  set_param('DisableUpdates', b'1')


def rollback(on_boot=False):
  state = json.loads((STATE / 'state.json').read_text())
  if state['phase'] == 'returned': return
  if not ACTIVE.is_symlink() or ACTIVE.resolve() not in {PREVIOUS, RUNTIME}:
    raise ValueError('Active path changed externally; refusing an unsafe rollback.')
  if not on_boot:
    # Diagnostics must never prevent recovery if a log command fails.
    try:
      capture = run('sudo', '-n', '-u', 'comma', 'tmux', 'capture-pane', '-p', '-t', 'comma', '-S', '-250', check=False, timeout=10)
      journal = run('journalctl', '--no-pager', '-u', 'comma.service', '-n', '250', check=False, timeout=10)
      atomic(STATE / 'service-log.txt', (capture.stdout + journal.stdout).encode())
    except (OSError, subprocess.SubprocessError):
      pass
    run('systemctl', 'stop', 'comma.service')
  if ACTIVE.resolve() == RUNTIME: replace_link(ACTIVE, PREVIOUS, {RUNTIME})
  restore_saved_settings()
  state['phase'] = 'returned'; state['returned_at'] = time.time(); state['returned_on_boot'] = on_boot
  save_state(state)
  if not on_boot: run('systemctl', 'start', 'comma.service')
  print('Previous Roadline installation restored. Assistance remains disabled. NAP backup is untouched.')


def status():
  state = json.loads((STATE / 'state.json').read_text()) if (STATE / 'state.json').exists() else {}
  print('TEST STATE:', state.get('phase', 'not started'))
  print('ACTIVE PATH:', ACTIVE.resolve())
  print('SERVICE:', run('systemctl', 'is-active', 'comma.service', check=False).stdout.strip())
  for name in ('IsOnroad', 'OpenpilotEnabledToggle', 'DisableUpdates'):
    p = PARAMS / name
    print(name + ':', p.read_text().strip() if p.is_file() else 'not set')
  print('SETTINGS SNAPSHOT:', (STATE / 'params-before').is_dir())
  print('NAP BACKUP:', NAP_BACKUP.is_dir())
  print('Startup, graphics and recovery still require the operator\'s observations.')


def main():
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument('action', choices=['start', 'status', 'rollback', 'boot-recover'])
  p.add_argument('--vehicle-disconnected', action='store_true')
  a = p.parse_args()
  if os.geteuid() != 0: raise ValueError('Run this helper using sudo -n.')
  if a.action == 'start' and not a.vehicle_disconnected:
    raise ValueError('Disconnect the vehicle harness and use stable bench power, then pass --vehicle-disconnected.')
  if a.action == 'boot-recover':
    if not (STATE / 'state.json').exists(): return
    state = json.loads((STATE / 'state.json').read_text())
    # On the same boot this runs before comma.service while start holds its lock.
    if not state_requires_boot_recovery(state, boot_id()): return
  with open('/data/roadline-bench-2fbfa0c.lock', 'a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    if a.action == 'start': start()
    elif a.action == 'status': status()
    elif a.action == 'rollback': rollback()
    else: rollback(on_boot=True)


if __name__ == '__main__':
  try: main()
  except (OSError, ValueError, subprocess.SubprocessError) as e:
    raise SystemExit('STOP: ' + str(e))
