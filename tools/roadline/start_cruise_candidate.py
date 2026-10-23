#!/usr/bin/env python3
"""Pinned, reversible first start of the c79c68f Comma 3X staging package.

Requires disconnected vehicle wiring and stable bench power. Normal pandad
startup may flash the internal Panda. This helper never enables assistance,
pedal control, radar, navigation maneuvers, or automatic updates.
"""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile

REVISION = 'c79c68fe5dac6d9668aadb6a64ee7b0557e89599'
OLD_REVISION = '2fbfa0c654230ead83596e2f6a474f8a8692f464'
PAYLOAD = '44a6e1ea33f500395653002ad0b1062186f8501532f2ed05eae70c5e0e4c9986'
NEW_PANDA = '8ece3dee9a1fb90f8d048272ea26a7bf26f6646e18e0100802b77bbec8eb0fc0'
OLD_PANDA = 'f7bf640b313124d9520657ebe736ae878eacb5a4d33624247a89fd8ad65f4fe5'
DATA = Path('/data')
ACTIVE = DATA / 'openpilot'
PACKAGE = DATA / ('roadline-package-' + REVISION)
RUNTIME = DATA / 'roadline-runtime-c79c68f'
PREVIOUS = DATA / 'roadline-before-cruise-c79c68f'
STATE = DATA / 'roadline-cruise-recovery-c79c68f'
CONTINUE = DATA / 'continue.sh'
PARAMS = DATA / 'params/d'
LOCK = DATA / 'roadline-cruise-first-start.lock'
VERSION = Path('/VERSION')
MODEL = Path('/sys/firmware/devicetree/base/model')
PANDA = 'panda/board/obj/panda_h7.bin.signed'
DISABLED = ('OpenpilotEnabledToggle', 'NAPPedalEnabled', 'NAPRadarEnabled',
            'NAPiBoosterEnabled', 'NAPNavigationManeuvers', 'NAPMapDrivingAssist')
SETTINGS = {'CalibrationParams', 'LiveParameters', 'LiveTorqueParameters',
            'LaneOffsetCm', 'PreAPLaneCentering', 'DisableUpdates', *DISABLED}
CALIBRATION = ('NAPPedalCanBus', 'NAPPedalCalibDone', 'NAPPedalCalibMin',
               'NAPPedalCalibMax', 'NAPPedalCalibZero', 'NAPPedalCalibFactor')


def run(*args, timeout=60, check=True):
  return subprocess.run(args, check=check, capture_output=True, text=True, timeout=timeout)


def digest(path):
  h = hashlib.sha256()
  with path.open('rb') as f:
    for data in iter(lambda: f.read(1024 * 1024), b''):
      h.update(data)
  return h.hexdigest()


def fsync_dir(path):
  fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
  try:
    os.fsync(fd)
  finally:
    os.close(fd)


def atomic(path, data, mode=0o600, owner=None):
  fd, name = tempfile.mkstemp(prefix='.roadline-', dir=path.parent)
  tmp = Path(name)
  try:
    with os.fdopen(fd, 'wb') as f:
      f.write(data)
      f.flush()
      os.fchmod(f.fileno(), mode)
      if owner is not None:
        os.fchown(f.fileno(), *owner)
      os.fsync(f.fileno())
    os.replace(tmp, path)
    fsync_dir(path.parent)
  finally:
    tmp.unlink(missing_ok=True)


def comma_owner():
  user = pwd.getpwnam('comma')
  return user.pw_uid, user.pw_gid


def put_param(name, value):
  atomic(PARAMS / name, value, owner=comma_owner())
  if (PARAMS / name).read_bytes() != value:
    raise ValueError('Parameter readback failed: ' + name)


def disable_controls():
  for name in DISABLED:
    put_param(name, b'0')
  put_param('DisableUpdates', b'1')


def offroad(allow_missing=False):
  try:
    value = (PARAMS / 'IsOnroad').read_bytes().strip()
  except FileNotFoundError:
    if allow_missing:
      return
    raise
  if value != b'0':
    raise ValueError('Keep the vehicle off; IsOnroad must be 0.')


def require_disabled():
  offroad()
  for key, value in [('OpenpilotEnabledToggle', b'0'), ('NAPPedalEnabled', b'0'), ('DisableUpdates', b'1')]:
    if (PARAMS / key).read_bytes().strip() != value:
      raise ValueError('Required setting differs: ' + key)


def tree_hash(root):
  h = hashlib.sha256()
  def walk_error(error):
    raise error
  for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
    dirs[:] = sorted(d for d in dirs if d != '.git')
    for name in sorted(files + [d for d in dirs if (Path(parent) / d).is_symlink()]):
      path = Path(parent) / name
      rel = path.relative_to(root).as_posix()
      if path.is_symlink():
        target = os.readlink(path)
        if os.path.isabs(target) or not path.resolve().is_relative_to(root.resolve()) or not path.exists():
          raise ValueError('Invalid package symlink: ' + rel)
        record = [rel, 'symlink', target]
      elif path.is_file() and name != '.git':
        record = [rel, 'file', bool(path.stat().st_mode & 0o100), digest(path)]
      else:
        raise ValueError('Unsupported package entry: ' + rel)
      h.update((json.dumps(record, separators=(',', ':')) + '\n').encode())
  return h.hexdigest()


def release_matches(root, revision):
  meta = json.loads((root / 'roadline_release.json').read_text())
  return (meta.get('source_revision') == revision and meta.get('road_ready') is False
          and meta.get('channel') == 'staging'
          and meta.get('target') == {'model': 'comma tizi', 'architecture': 'aarch64', 'agnos': '17.2'})


def validate_launcher():
  if CONTINUE.is_symlink() or not CONTINUE.is_file() or not CONTINUE.stat().st_mode & 0o100:
    raise ValueError('Expected a regular executable startup launcher.')
  original = CONTINUE.read_bytes()
  lines = [line.strip() for line in original.decode().splitlines()
           if line.strip() and not line.lstrip().startswith('#')]
  if b'\r' in original or lines != ['cd /data/openpilot', 'exec ./launch_openpilot.sh']:
    raise ValueError('Startup launcher differs; inspect before switching.')


def launcher_wrapper(original):
  return ('#!/usr/bin/env bash\n# Roadline staging first-start recovery\n' +
          f'sudo -n /usr/bin/python3 "{STATE}/control.py" boot-check || exit $?\n').encode() + original


def selected(name):
  return name.startswith(('NAP', 'Roadline')) or name in SETTINGS


def save_state(state):
  atomic(STATE / 'state.json', (json.dumps(state, indent=2) + '\n').encode())


def read_state():
  state = json.loads((STATE / 'state.json').read_text())
  if state.get('revision') != REVISION or state.get('payload_sha256') != PAYLOAD:
    raise ValueError('Unexpected recovery record.')
  return state


def save_settings():
  settings = {}
  for p in PARAMS.iterdir():
    if selected(p.name):
      if p.is_symlink() or not p.is_file():
        raise ValueError('Unexpected settings entry: ' + p.name)
      settings[p.name] = base64.b64encode(p.read_bytes()).decode('ascii')
  atomic(STATE / 'settings-before.json', (json.dumps(settings, sort_keys=True) + '\n').encode())
  return digest(STATE / 'settings-before.json')


def saved_settings(state):
  path = STATE / 'settings-before.json'
  if digest(path) != state['settings_sha256']:
    raise ValueError('Saved settings checksum differs; refusing restore.')
  settings = json.loads(path.read_text())
  if any(not selected(k) or '/' in k or k in ('.', '..') for k in settings):
    raise ValueError('Invalid saved setting name.')
  return {k: base64.b64decode(v, validate=True) for k, v in settings.items()}


def saved_launcher(state):
  path = STATE / 'continue-before.sh'
  if digest(path) != state['launcher_sha256']:
    raise ValueError('Saved launcher checksum differs.')
  original = path.read_bytes()
  if CONTINUE.is_symlink() or CONTINUE.read_bytes() not in (original, launcher_wrapper(original)):
    raise ValueError('Startup launcher changed externally.')
  return original


def restore_settings(settings):
  for p in PARAMS.iterdir():
    if selected(p.name) and p.name not in settings:
      if p.is_symlink() or not p.is_file():
        raise ValueError('Unexpected settings entry: ' + p.name)
      p.unlink()
  for name, data in settings.items():
    if name not in DISABLED and name != 'DisableUpdates':
      put_param(name, data)
  disable_controls()


def prepare_runtime():
  # Keep the verified package pristine: boot only a separate disposable copy.
  shutil.copytree(PACKAGE / 'runtime', RUNTIME, symlinks=True)
  if tree_hash(RUNTIME) != PAYLOAD:
    raise ValueError('Copied runtime does not match the package.')
  uid, gid = comma_owner()
  os.chown(RUNTIME, uid, gid)
  for parent, dirs, files in os.walk(RUNTIME, followlinks=False):
    for name in dirs + files:
      os.chown(Path(parent) / name, uid, gid, follow_symlinks=False)
  prefix = ('sudo', '-n', '-u', 'comma', 'git', '-C', str(RUNTIME))
  run(*prefix, 'init', '-b', 'roadline-cruise-staging')
  run(*prefix, 'add', '--force', '--all', timeout=180)
  run(*prefix, '-c', 'user.name=Roadline local staging', '-c', 'user.email=roadline@localhost',
      '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', 'commit',
      '-m', 'Local staging runtime from source ' + REVISION, timeout=180)
  run(*prefix, 'remote', 'add', 'origin', 'https://github.com/visegrips70/Roadline.git')
  if tree_hash(RUNTIME) != PAYLOAD:
    raise ValueError('Runtime changed while preparing metadata.')
  # Ensure copied files, Git metadata and directory operations reach storage.
  os.sync()


def validate_start():
  if STATE.exists() or STATE.is_symlink() or PREVIOUS.exists() or PREVIOUS.is_symlink() or RUNTIME.exists() or RUNTIME.is_symlink():
    raise ValueError('First-start paths already exist. Use status; do not repeat start.')
  if VERSION.read_text().strip() != '17.2' or MODEL.read_bytes().rstrip(b'\0') != b'comma tizi':
    raise ValueError('This package requires Comma 3X with AGNOS 17.2.')
  require_disabled()
  if ACTIVE.is_symlink() or not ACTIVE.is_dir() or not release_matches(ACTIVE, OLD_REVISION):
    raise ValueError('Expected the original 2fbfa0c clean-install directory.')
  if digest(ACTIVE / PANDA) != OLD_PANDA:
    raise ValueError('Previous Panda firmware differs from the recovery baseline.')
  source = PACKAGE / 'runtime'
  if PACKAGE.is_symlink() or source.is_symlink() or not source.is_dir():
    raise ValueError('Unexpected package path.')
  report = json.loads((PACKAGE / 'report.json').read_text())
  expected_blocker = 'No exact-payload validation evidence supplied; publication is blocked.'
  if (report.get('source_revision') != REVISION or report.get('payload_sha256') != PAYLOAD
      or report.get('blockers') != [expected_blocker]):
    raise ValueError('Unexpected package report.')
  if not release_matches(source, REVISION) or tree_hash(source) != PAYLOAD or digest(source / PANDA) != NEW_PANDA:
    raise ValueError('Package contents, file modes or firmware differ from the reviewed build.')
  if not (source / 'prebuilt').is_file() or (source / '.git').exists() or (source / '.overlay_init').exists():
    raise ValueError('Expected an unused packaged runtime.')
  validate_launcher()
  for key in ('DoUninstall', 'DoReboot', 'DoShutdown', 'NAPScriptRunning'):
    path = PARAMS / key
    if path.exists() and path.read_bytes().strip() not in (b'', b'0'):
      raise ValueError('Pending device action: ' + key)
  if shutil.disk_usage(DATA).free < 2 * 1024 ** 3:
    raise ValueError('At least 2 GiB free is required.')


def install_link():
  if ACTIVE.exists() or ACTIVE.is_symlink() or not PREVIOUS.is_dir():
    raise ValueError('Unexpected active or backup path during switch.')
  tmp = DATA / '.roadline-cruise-active-link'
  if tmp.exists() or tmp.is_symlink():
    raise ValueError('Temporary switch path exists; inspect before continuing.')
  tmp.symlink_to(RUNTIME)
  try:
    os.replace(tmp, ACTIVE)
    fsync_dir(DATA)
  finally:
    tmp.unlink(missing_ok=True)


def start():
  validate_start()
  prepare_runtime()
  # Recheck after the potentially slow copy, before touching the active service.
  require_disabled()
  validate_launcher()
  if ACTIVE.is_symlink() or not release_matches(ACTIVE, OLD_REVISION) or digest(ACTIVE / PANDA) != OLD_PANDA:
    raise ValueError('Active installation changed during candidate preparation.')
  STATE.mkdir(mode=0o700)
  fsync_dir(DATA)
  atomic(STATE / 'control.py', Path(__file__).read_bytes())
  original = CONTINUE.read_bytes()
  info = CONTINUE.stat()
  atomic(STATE / 'continue-before.sh', original)
  state = {'revision': REVISION, 'payload_sha256': PAYLOAD, 'phase': 'prepared',
           'launcher_sha256': digest(STATE / 'continue-before.sh'),
           'launcher_mode': info.st_mode & 0o777, 'launcher_owner': [info.st_uid, info.st_gid]}
  service_stopped = False
  try:
    run('systemctl', 'stop', 'comma.service')
    service_stopped = True
    require_disabled()
    state['settings_sha256'] = save_settings()
    save_state(state)
    atomic(CONTINUE, launcher_wrapper(original), mode=state['launcher_mode'], owner=state['launcher_owner'])
    disable_controls()
    state['phase'] = 'switching'
    save_state(state)
    os.rename(ACTIVE, PREVIOUS)
    fsync_dir(DATA)
    install_link()
    state['phase'] = 'running'
    save_state(state)
    run('systemctl', 'start', 'comma.service')
  except Exception:
    if (STATE / 'state.json').is_file():
      rollback(on_boot=False, require_offroad=False)
    elif service_stopped:
      run('systemctl', 'start', 'comma.service')
    raise
  print('FIXED ROADLINE START REQUESTED: ' + REVISION)
  print('Assistance, pedal control and automatic updates remain disabled.')
  print('Normal startup may update the internal Panda firmware. Keep stable bench power.')
  print('The candidate stays selected across normal reboots; no timed return is scheduled.')
  print('Previous installation and settings are preserved at: ' + str(PREVIOUS) + ' and ' + str(STATE))


def recovery_location():
  if ACTIVE.is_symlink():
    if ACTIVE.resolve() != RUNTIME or not PREVIOUS.is_dir() or PREVIOUS.is_symlink():
      raise ValueError('Unknown active link or missing backup; refusing rollback.')
    return 'candidate'
  if ACTIVE.is_dir() and not PREVIOUS.exists():
    if not release_matches(ACTIVE, OLD_REVISION):
      raise ValueError('Active installation changed externally.')
    return 'previous'
  if not ACTIVE.exists() and PREVIOUS.is_dir() and not PREVIOUS.is_symlink():
    return 'gap'
  raise ValueError('Ambiguous installation paths; refusing rollback.')


def rollback(on_boot=False, require_offroad=True):
  state = read_state()
  if state['phase'] == 'returned':
    print('Previous installation is already restored.')
    return
  if require_offroad and not on_boot:
    # Failed manager startup may clear this transient parameter. The CLI still
    # requires physically disconnected vehicle wiring; an explicit 1 blocks.
    offroad(allow_missing=True)
  location = recovery_location()
  backup = ACTIVE if location == 'previous' else PREVIOUS
  if not release_matches(backup, OLD_REVISION) or digest(backup / PANDA) != OLD_PANDA:
    raise ValueError('Previous installation or firmware changed; refusing rollback.')
  settings = saved_settings(state)
  original = saved_launcher(state)
  if not on_boot:
    run('systemctl', 'stop', 'comma.service')
  state['phase'] = 'returning'
  save_state(state)
  disable_controls()
  if location == 'candidate':
    ACTIVE.unlink()
    fsync_dir(DATA)
  if location in ('candidate', 'gap'):
    os.rename(PREVIOUS, ACTIVE)
    fsync_dir(DATA)
  restore_settings(settings)
  atomic(CONTINUE, original, mode=state['launcher_mode'], owner=state['launcher_owner'])
  state['phase'] = 'returned'
  save_state(state)
  if not on_boot:
    run('systemctl', 'start', 'comma.service')
  print('Previous Roadline restored; assistance and pedal control remain disabled.')
  print('Its normal Panda startup must complete before hardware health can be assessed.')


def boot_check():
  state = read_state()
  if state['phase'] in ('prepared', 'switching', 'returning'):
    rollback(on_boot=True)
  elif state['phase'] == 'running':
    if not ACTIVE.is_symlink() or ACTIVE.resolve() != RUNTIME or not release_matches(RUNTIME, REVISION):
      raise ValueError('Candidate startup path changed.')
    # Until a separately reviewed promotion, every boot stays assistance-disabled.
    disable_controls()
  elif state['phase'] != 'returned':
    raise ValueError('Unknown first-start phase.')


def status():
  state = read_state() if (STATE / 'state.json').is_file() else {}
  print('FIRST-START STATE:', state.get('phase', 'not started'))
  print('ACTIVE PATH:', ACTIVE.resolve())
  print('ACTIVE SOURCE:', json.loads((ACTIVE / 'roadline_release.json').read_text()).get('source_revision'))
  print('SERVICE:', run('systemctl', 'is-active', 'comma.service', check=False).stdout.strip())
  for key in ('IsOnroad', *DISABLED, 'DisableUpdates', 'NAPPedalCanBus', 'NAPPedalCalibDone'):
    p = PARAMS / key
    print(key + ':', p.read_text().strip() if p.is_file() else 'not set')
  print('PREVIOUS INSTALLATION PRESERVED:', PREVIOUS.is_dir())
  if 'settings_sha256' in state:
    saved = saved_settings(state)
    matches = all((PARAMS / k).read_bytes() == saved[k] if k in saved else not (PARAMS / k).exists() for k in CALIBRATION)
    print('SAVED PEDAL CALIBRATION MATCH:', matches)
  cached = PARAMS / 'PandaSignatures'
  signature = (ACTIVE / PANDA).read_bytes()[-128:]
  print('CACHED PANDA SIGNATURE MATCH:', cached.is_file() and cached.read_bytes() == signature)
  print('Cached signature and service state do not establish live CAN/actuator health.')


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('action', choices=['start', 'status', 'rollback', 'boot-check'])
  parser.add_argument('--vehicle-disconnected', action='store_true')
  args = parser.parse_args()
  if os.geteuid() != 0:
    parser.error('Run using sudo -n /usr/bin/python3.')
  if args.action in ('start', 'rollback') and not args.vehicle_disconnected:
    parser.error('Disconnect vehicle wiring, use stable bench power, then pass --vehicle-disconnected.')
  with LOCK.open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    {'start': start, 'status': status, 'rollback': rollback, 'boot-check': boot_check}[args.action]()


if __name__ == '__main__':
  try:
    main()
  except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
    raise SystemExit('STOP: ' + str(error)) from error
