#!/usr/bin/env python3
"""Bounded, unengaged startup observation of the pinned c79c68f candidate.

Run from an offroad device with the vehicle in Park, using the systemd unit
specified below. Temporarily selects the normal controller/pedal configuration;
the normal manager, card and pandad own all hardware. No direct CAN publisher,
Panda handle, firmware flash command or engagement request is used here.
"""
import argparse
import base64
from collections import Counter
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import subprocess
import tempfile
import time

DATA = Path('/data')
VERSION = Path('/VERSION')
MODEL = Path('/sys/firmware/devicetree/base/model')
ROOT = DATA / 'roadline-runtime-c79c68f'
RECOVERY = DATA / 'roadline-cruise-recovery-c79c68f'
PARAMS = DATA / 'params/d'
MARKER = DATA / 'roadline-parked-startup.pending'
UNIT = 'roadline-parked-startup-check.service'
HELPER = DATA / 'roadline-parked-startup-check.py'
PYTHON = '/usr/local/venv/bin/python'
BASE = 'c79c68fe5dac6d9668aadb6a64ee7b0557e89599'
CARD_SHA = '669311aa4175bf1e391da2f3aa537f52552a0c609efc0565f0aad505d46625cc'
PANDA_SHA = '8ece3dee9a1fb90f8d048272ea26a7bf26f6646e18e0100802b77bbec8eb0fc0'
DISABLED = ('OpenpilotEnabledToggle', 'NAPPedalEnabled', 'NAPRadarEnabled',
            'NAPiBoosterEnabled', 'NAPNavigationManeuvers', 'NAPMapDrivingAssist')
CALIBRATION = ('NAPPedalCanBus', 'NAPPedalCalibDone', 'NAPPedalCalibMin',
               'NAPPedalCalibMax', 'NAPPedalCalibZero', 'NAPPedalCalibFactor')
PINNED = {
  'opendbc_repo/opendbc/car/tesla/carcontroller.py': '192ffb6966dd843f12fceefba4ecec420f06873a5c4f49fc6727cbfead402700',
  'opendbc_repo/opendbc/car/tesla/carstate.py': '6c3b163a8d745faacd88800ef990b5de5773741e16e29e1e7514dea81ff58d07',
  'opendbc_repo/opendbc/car/tesla/interface.py': '1fbf96bca5f95ae5246e3bf42e5a26feddc80e9a2948f98113b27898b2b62df3',
  'opendbc_repo/opendbc/car/tesla/preap/carcontroller.py': 'f0b8913ff9f5a5e2988441f35da1cce6f339c81f715babd87c355d552d3e1913',
  'opendbc_repo/opendbc/car/tesla/preap/carstate.py': 'd4832df15c13737a10a36c7d22a7fca90ddb7d43405ba5d3cf51e1509b1e4a5c',
  'opendbc_repo/opendbc/car/tesla/preap/engagement.py': '600305b083b632bf98e96389278fec00d263e6a6699f3e811bc6c104988695f3',
  'opendbc_repo/opendbc/car/tesla/preap/stock_cc_spoofer.py': '1de79c406a4eb8550a0df72db3ec3aedfef92b3b974235d716d5d761890133ad',
  'opendbc_repo/opendbc/car/tesla/preap/interface.py': 'a462bac3ae16f74816a4ba12c2dec3b20b62dfd380b341e502214d859aa8f1d1',
  'opendbc_repo/opendbc/car/tesla/preap/nap_conf.py': '37e2220bf571dee1fb055e5ec7075e9940bef513d04f1ccd60c684e68e9bbab8',
  'opendbc_repo/opendbc/car/tesla/preap/teslacan.py': 'fbe011109cda10341af11b841423cacdf7006df7c02d1fb565d70b693f9f43a2',
  'opendbc_repo/opendbc/dbc/tesla_preap.dbc': '1f4d751872063295781bcbae7f005330859fa12d44ab6d012ee4c05fb05059d3',
  'system/manager/manager.py': '35592602231c762489babf6700759210603a3441293f8235a6a85c84d5068c77',
}
RECOVERY_SHA = '17fe962cc218256eb2dbc101034de406834438df4ef4526f8c0dff65f5d52223'


def digest(path):
  return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
  return subprocess.run(args, check=True, capture_output=True, text=True, timeout=20).stdout.strip()


def atomic(path, value, owner=None):
  fd, name = tempfile.mkstemp(prefix='.roadline-parked-', dir=path.parent)
  try:
    with os.fdopen(fd, 'wb') as f:
      f.write(value)
      os.fchmod(f.fileno(), 0o600)
      if owner is not None:
        os.fchown(f.fileno(), *owner)
      f.flush()
      os.fsync(f.fileno())
    os.replace(name, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
      os.fsync(fd)
    finally:
      os.close(fd)
  finally:
    Path(name).unlink(missing_ok=True)


def put(key, value):
  user = pwd.getpwnam('comma')
  atomic(PARAMS / key, value, (user.pw_uid, user.pw_gid))
  if (PARAMS / key).read_bytes() != value:
    raise ValueError('Setting readback failed: ' + key)


def require_settings(armed=False):
  values = dict.fromkeys(DISABLED, b'0')
  values.update(DisableUpdates=b'1', NAPPedalCanBus=b'2', NAPPedalCalibDone=b'1', NAPForcePreAP=b'1')
  if armed:
    values.update(OpenpilotEnabledToggle=b'1', NAPPedalEnabled=b'1')
  for key, value in values.items():
    if (PARAMS / key).read_bytes().strip() != value:
      raise ValueError('Unexpected setting: ' + key)
  for key in ('NAPParkedSignalTest', 'DoReboot', 'DoShutdown', 'DoUninstall', 'NAPScriptRunning'):
    path = PARAMS / key
    if path.exists() and path.read_bytes().strip() not in (b'', b'0'):
      raise ValueError('Turn off conflicting action: ' + key)
  if (DATA / 'nap_airride_enabled').exists():
    raise ValueError('Airride endpoint is enabled; this check does not cover it.')


def validate_install():
  if VERSION.read_text().strip() != '17.2' or MODEL.read_bytes().rstrip(b'\0') != b'comma tizi':
    raise ValueError('Expected Comma 3X / AGNOS 17.2.')
  active = DATA / 'openpilot'
  if ROOT.is_symlink() or not active.is_symlink() or active.resolve() != ROOT:
    raise ValueError('Active installation differs.')
  release = json.loads((ROOT / 'roadline_release.json').read_text())
  state = json.loads((RECOVERY / 'state.json').read_text())
  if release.get('source_revision') != BASE or release.get('road_ready') is not False:
    raise ValueError('Base release differs.')
  if state.get('revision') != BASE or state.get('phase') != 'running':
    raise ValueError('Recovery state differs.')
  for rel, expected in PINNED.items():
    path = ROOT / rel
    if path.is_symlink() or path.resolve() != path or digest(path) != expected:
      raise ValueError('Reviewed file differs: ' + rel)
  if digest(ROOT / 'selfdrive/car/card.py') != CARD_SHA or digest(ROOT / 'panda/board/obj/panda_h7.bin.signed') != PANDA_SHA:
    raise ValueError('Car daemon or firmware differs.')
  if digest(RECOVERY / 'control.py') != RECOVERY_SHA:
    raise ValueError('Recovery control differs.')
  original = (RECOVERY / 'continue-before.sh').read_bytes()
  wrapper = (b'#!/usr/bin/env bash\n# Roadline staging first-start recovery\n' +
             f'sudo -n /usr/bin/python3 "{RECOVERY}/control.py" boot-check || exit $?\n'.encode() + original)
  if hashlib.sha256(original).hexdigest() != state['launcher_sha256'] or (DATA / 'continue.sh').read_bytes() != wrapper:
    raise ValueError('Recovery boot launcher differs.')
  settings_path = RECOVERY / 'settings-before.json'
  if digest(settings_path) != state['settings_sha256']:
    raise ValueError('Saved settings checksum differs.')
  saved = json.loads(settings_path.read_text())
  for key in CALIBRATION:
    if (PARAMS / key).read_bytes() != base64.b64decode(saved[key], validate=True):
      raise ValueError('Saved pedal calibration differs: ' + key)
  if run('systemctl', 'is-active', 'comma.service') != 'active':
    raise ValueError('Normal comma service must be active.')
  require_settings()
  if (PARAMS / 'IsOnroad').read_bytes().strip() != b'0':
    raise ValueError('Turn the car off first; leave the Comma powered and connected.')


def validate_supervisor():
  # Refuse a plain SSH invocation that could lose its cleanup on disconnect.
  if not os.environ.get('INVOCATION_ID') or Path(__file__).resolve() != HELPER:
    raise ValueError('Use the documented systemd command and installed helper path.')
  props = dict(line.split('=', 1) for line in run('systemctl', 'show', UNIT, '--no-pager',
               '-p', 'MainPID', '-p', 'RuntimeMaxUSec', '-p', 'ExecStopPost').splitlines())
  if props.get('MainPID') != str(os.getpid()) or props.get('RuntimeMaxUSec') != '3min':
    raise ValueError('Expected the bounded 180-second test unit.')
  expected = f'argv[]={PYTHON} {HELPER} cleanup ;'
  if expected not in props.get('ExecStopPost', ''):
    raise ValueError('Independent cleanup is not configured.')


def fresh(sm, name, now, age=1.5):
  return sm.seen[name] and sm.valid[name] and 0 <= now - sm.logMonoTime[name] / 1e9 <= age


def panda_guard(sm, now, allowed):
  if not fresh(sm, 'pandaStates', now):
    raise ValueError('Panda telemetry is missing or stale.')
  pandas = sm['pandaStates']
  if len(pandas) != 1:
    raise ValueError('Expected one internal Panda.')
  p = pandas[0]
  if str(p.safetyModel) not in allowed or p.controlsAllowed or p.heartbeatLost or len(p.faults) or str(p.faultStatus) != 'none':
    raise ValueError('Unexpected Panda permission, mode or fault.')
  if str(p.safetyModel) == 'teslaPreap' and (p.safetyParam not in (1, 5) or p.safetyRxChecksInvalid):
    raise ValueError('Pedal-only Pre-AP safety configuration / RX checks failed.')
  return p


def park_guard(cs):
  if (str(cs.gearShifter) != 'park' or not cs.canValid or cs.canTimeout or cs.cruiseState.enabled
      or any(not math.isfinite(v) or abs(v) > .05 for v in (cs.vEgo, cs.vEgoRaw))):
    raise ValueError('Vehicle must remain stationary in Park with cruise disengaged.')
  if cs.gasPressed:
    raise ValueError('Release the accelerator; this check requires no pedal inputs.')


def control_guard(cc):
  if cc.enabled or cc.latActive or cc.longActive:
    raise ValueError('Unexpected engagement request; ending the check.')


class WireObservation:
  def __init__(self):
    from opendbc.can import CANParser
    self.parser = CANParser('tesla_preap', [('EPAS_sysStatus', 0)], 0)
    self.tx = Counter()
    self.pedal_states = Counter()
    self.epas = Counter()
    self.last_pedal = self.last_epas = None
    self.last_idx = None
    self.counter_gaps = 0
    self.bad_feedback = 0

  def sendcan(self, frames):
    # Observe the application's requests; this is not proof of bus delivery.
    for address, data, bus in frames:
      if address == 0x551 and bus == 2:
        okay = len(data) == 6 and data[:4] == bytes(4) and data[4] < 16
      elif address == 0x488 and bus == 0:
        okay = len(data) == 4 and (data[2] >> 6) == 0
      elif address == 0x214 and bus == 0:
        okay = len(data) == 3 and (data[0] & 7) == 1
      else:
        raise ValueError(f'Unexpected outgoing request: bus {bus}, {address:#x}.')
      if not okay or data[-1] != ((address & 255) + (address >> 8) + sum(data[:-1])) & 255:
        raise ValueError(f'Enabled, nonzero or malformed outgoing request: {address:#x}.')
      self.tx[f'{address:#x} bus {bus}'] += 1

  def can(self, timestamp, frames):
    for address, data, bus in frames:
      if (address, bus) not in ((0x552, 2), (0x370, 0)):
        continue
      size = 6 if address == 0x552 else 8
      if len(data) != size or data[-1] != ((address & 255) + (address >> 8) + sum(data[:-1])) & 255:
        self.bad_feedback += 1
        continue
      if address == 0x552:
        state, idx = data[4] >> 4, data[4] & 15
        self.pedal_states[state] += 1
        if state not in (0, 5):
          raise ValueError(f'Pedal reported fault state {state}.')
        if self.last_idx is not None and idx != (self.last_idx + 1) % 16:
          self.counter_gaps += 1
        self.last_idx = idx
        self.last_pedal = timestamp / 1e9
      else:
        self.parser.update([(timestamp, [(address, data, bus)])])
        msg = self.parser.vl['EPAS_sysStatus']
        self.epas[(int(msg['EPAS_eacStatus']), int(msg['EPAS_eacErrorCode']),
                   int(msg['EPAS_steeringFault']), int(msg['EPAS_steeringReduced']))] += 1
        self.last_epas = timestamp / 1e9
        if msg['EPAS_eacStatus'] not in (0, 1) or msg['EPAS_steeringFault'] or msg['EPAS_steeringReduced']:
          raise ValueError('EPAS unexpectedly active or reporting a steering fault/reduction.')

  def report(self, now):
    return dict(disabled_outgoing_requests=dict(self.tx), pedal_states=dict(self.pedal_states),
                pedal_counter_gaps=self.counter_gaps, bad_feedback_frames=self.bad_feedback,
                epas_status_error_fault_reduced={str(k): v for k, v in self.epas.items()},
                pedal_age=None if self.last_pedal is None else round(now - self.last_pedal, 3),
                epas_age=None if self.last_epas is None else round(now - self.last_epas, 3))


def cleanup():
  if not MARKER.exists():
    return
  # Stop the active stack before returning settings to passive. Never restore an
  # enabled setting from a snapshot. The existing boot-check also forces these off.
  failures = []
  try:
    run('systemctl', 'stop', 'comma.service')
  except (OSError, subprocess.SubprocessError) as error:
    failures.append('service stop: ' + str(error))
  for key, value in [*[(key, b'0') for key in DISABLED], ('DisableUpdates', b'1')]:
    try:
      put(key, value)
    except (OSError, ValueError) as error:
      failures.append(key + ': ' + str(error))
  if failures:
    raise RuntimeError('Cleanup incomplete; no restart requested. Stay in Park. ' + '; '.join(failures))
  run('systemctl', '--no-block', 'start', 'comma.service')
  MARKER.unlink()
  print('ASSISTANCE AND PEDAL SETTINGS DISABLED; normal service restart requested.', flush=True)


def observe(sm, messaging):
  wire = WireObservation()
  can = messaging.sub_sock('can')
  tx = messaging.sub_sock('sendcan')
  start = time.monotonic()
  ready_since = None
  wake_since = None
  first_spi = last_spi = None
  try:
    print('WAKE THE VEHICLE NOW, remaining in Park. Do not touch the cruise stalk, accelerator or steering.', flush=True)
    while time.monotonic() - start < 90:
      sm.update(100)
      now = time.monotonic()
      require_settings(armed=True)
      p = panda_guard(sm, now, {'noOutput', 'elm327', 'teslaPreap'})
      last_spi = p.spiErrorCount
      if first_spi is None:
        first_spi = last_spi
      for event in messaging.drain_sock(can):
        wire.can(event.logMonoTime, [(f.address, bytes(f.dat), f.src) for f in event.can])
      for event in messaging.drain_sock(tx):
        wire.sendcan([(f.address, bytes(f.dat), f.src) for f in event.sendcan])
      awake = (PARAMS / 'IsOnroad').read_bytes().strip() == b'1'
      if awake and wake_since is None:
        wake_since = now
      if not awake and wake_since is not None:
        raise ValueError('Vehicle went offroad during the check.')
      car_ready = fresh(sm, 'carState', now)
      if car_ready:
        park_guard(sm['carState'])
      if fresh(sm, 'carControl', now):
        control_guard(sm['carControl'])
      active = str(p.safetyModel) == 'teslaPreap'
      if active:
        if not car_ready or not fresh(sm, 'carControl', now):
          raise ValueError('Fresh Park/control telemetry required in Pre-AP mode.')
        if ready_since is None:
          ready_since = now
          print('Normal Pre-AP safety initialized, controls disallowed. Observing for 15 seconds; stay in Park.', flush=True)
        if now - ready_since >= 15:
          if not all(wire.tx[k] for k in ('0x551 bus 2', '0x488 bus 0', '0x214 bus 0')):
            raise ValueError('Expected disabled controller requests were not all observed.')
          if wire.last_pedal is None or wire.last_epas is None or now - min(wire.last_pedal, wire.last_epas) > .5:
            raise ValueError('Pedal or EPAS feedback is missing/stale.')
          return
      elif ready_since is not None:
        raise ValueError('Safety mode changed after initialization.')
      if wake_since is None and now - start > 45:
        raise ValueError('Wake-up timed out; settings will be disabled.')
      if wake_since is not None and ready_since is None and now - wake_since > 30:
        raise ValueError('Normal controller initialization timed out.')
    raise ValueError('Observation timed out.')
  finally:
    report = wire.report(time.monotonic())
    report.update(spi_counter_first=first_spi, spi_counter_last=last_spi, road_ready=False)
    atomic(DATA / 'roadline-parked-startup-result.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps(report, indent=2), flush=True)


def check():
  from cereal import messaging
  validate_supervisor()
  if MARKER.exists():
    raise ValueError('An earlier test needs cleanup; run the cleanup action first.')
  with (DATA / 'roadline-cruise-first-start.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    validate_install()
    sm = messaging.SubMaster(['pandaStates', 'carState', 'carControl', 'deviceState', 'managerState'])
    until = time.monotonic() + 5
    while time.monotonic() < until:
      sm.update(100)
    now = time.monotonic()
    panda_guard(sm, now, {'noOutput'})
    if not fresh(sm, 'deviceState', now) or sm['deviceState'].started:
      raise ValueError('The device must be offroad before configuration.')
    if not fresh(sm, 'managerState', now) or any(p.running and p.name in ('card', 'controlsd', 'selfdrived') for p in sm['managerState'].processes):
      raise ValueError('Wait for the onroad processes to stop.')
    validate_install()
    # Durable intent precedes the first mutation. ExecStopPost handles process
    # death; loss of power uses the unchanged, verified recovery boot launcher.
    atomic(MARKER, b'parked initialization only\n')
    try:
      put('NAPPedalEnabled', b'1')
      put('OpenpilotEnabledToggle', b'1')
      observe(sm, messaging)
    finally:
      cleanup()
  # The recovery launcher can now acquire its lock and start passive mode.
  restored_at = time.monotonic()
  stable_since = None
  until = restored_at + 30
  while time.monotonic() < until:
    sm.update(200)
    now = time.monotonic()
    require_settings()
    if fresh(sm, 'pandaStates', now) and sm.logMonoTime['pandaStates'] / 1e9 >= restored_at:
      p = sm['pandaStates'][0] if len(sm['pandaStates']) == 1 else None
      passive = p is not None and str(p.safetyModel) == 'noOutput' and not p.controlsAllowed and not p.heartbeatLost and not len(p.faults)
      stable_since = (now if stable_since is None else stable_since) if passive else None
      if stable_since is not None and now - stable_since >= 3:
        print('LIVE noOutput RESTORED. This checked unengaged startup only; driving and disengagement remain unvalidated.', flush=True)
        return
    else:
      stable_since = None
  raise ValueError('Disabled settings restored, but live noOutput was not confirmed within 30 seconds.')


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('action', choices=('run', 'cleanup'))
  options = parser.parse_args()
  if os.geteuid() != 0:
    parser.error('Run through sudo and the documented transient systemd unit.')
  if options.action == 'cleanup':
    cleanup()
  else:
    check()


if __name__ == '__main__':
  try:
    main()
  except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
    raise SystemExit('STOP: ' + str(error)) from error
