"""Stationary startup guards and cleanup, without hardware or CAN publication."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest

from openpilot.tools.roadline import parked_startup_check as check


def frame(address, payload, bus):
  checksum = ((address & 255) + (address >> 8) + sum(payload)) & 255
  return address, bytes(payload) + bytes([checksum]), bus


def test_disabled_requests_accept_wire_format_and_reject_bad_checksum():
  wire = check.WireObservation()
  messages = [frame(0x551, [0, 0, 0, 0, 15], 2), frame(0x488, [1, 2, 3], 0), frame(0x214, [1, 0], 0)]
  wire.sendcan(messages)
  assert sum(wire.tx.values()) == 3
  address, data, bus = messages[0]
  with pytest.raises(ValueError, match='malformed'):
    wire.sendcan([(address, data[:-1] + bytes([data[-1] ^ 1]), bus)])


@pytest.mark.parametrize('message', [
  frame(0x551, [0, 0, 0, 0, 128], 2),  # enable bit
  frame(0x551, [0, 1, 0, 0, 0], 2),  # primary channel nonzero
  frame(0x551, [0, 0, 0, 1, 0], 2),  # redundant channel nonzero
  frame(0x551, [0, 0, 0, 0, 0], 0),  # wrong pedal bus
  frame(0x488, [1, 2, 64], 0),  # steering enabled
  frame(0x214, [3, 0], 0),  # unexpected EPAS mode
  frame(0x45, [2] * 7, 0),  # no spoofed stalk request is accepted
  frame(0x2b9, [0] * 7, 0),
  frame(0x64b, [0] * 7, 0),
])
def test_non_disabled_requests_abort(message):
  with pytest.raises(ValueError):
    check.WireObservation().sendcan([message])


def test_pedal_timeout_to_zero_and_counter_wrap_are_observations_not_health_claims():
  wire = check.WireObservation()
  wire.can(1_000_000_000, [frame(0x552, [1, 20, 1, 20, 0x5f], 2)])
  wire.can(1_010_000_000, [frame(0x552, [1, 20, 1, 20, 0x00], 2)])
  report = wire.report(1.01)
  assert report['pedal_states'] == {5: 1, 0: 1}
  assert report['pedal_counter_gaps'] == 0
  assert report['epas_age'] is None
  wire.can(1_020_000_000, [frame(0x552, [1, 20, 1, 20, 0x03], 2)])
  assert wire.counter_gaps == 1


def test_corrupt_feedback_is_not_decoded():
  wire = check.WireObservation()
  wire.can(1_000_000_000, [(0x552, bytes(6), 2), (0x370, bytes(8), 0)])
  assert wire.bad_feedback == 2
  assert not wire.pedal_states and not wire.epas


def car_state(**changes):
  return NS(**(dict(gearShifter='park', canValid=True, canTimeout=False,
                   cruiseState=NS(enabled=False), vEgo=0.0, vEgoRaw=0.0, gasPressed=False) | changes))


@pytest.mark.parametrize('changes', [dict(gearShifter='drive'), dict(canValid=False), dict(canTimeout=True),
  dict(vEgo=.1), dict(vEgoRaw=.1), dict(vEgo=float('nan')), dict(vEgoRaw=float('inf')),
  dict(cruiseState=NS(enabled=True)), dict(gasPressed=True)])
def test_park_guard_rejects_motion_missing_can_engagement_and_pedal_input(changes):
  with pytest.raises(ValueError):
    check.park_guard(car_state(**changes))


@pytest.mark.parametrize('name', ['enabled', 'latActive', 'longActive'])
def test_either_axis_or_engagement_aborts(name):
  cc = NS(enabled=False, latActive=False, longActive=False)
  setattr(cc, name, True)
  with pytest.raises(ValueError):
    check.control_guard(cc)


class State(dict):
  def __init__(self):
    super().__init__(pandaStates=[NS(safetyModel='noOutput', controlsAllowed=False, heartbeatLost=False,
                     faults=[], faultStatus='none', safetyParam=0, safetyRxChecksInvalid=False, spiErrorCount=1)],
                     carState=car_state(), carControl=NS(enabled=False, latActive=False, longActive=False),
                     deviceState=NS(started=False), managerState=NS(processes=[]))
    self.seen = dict.fromkeys(self, True)
    self.valid = dict.fromkeys(self, True)
    self.logMonoTime = dict.fromkeys(self, 10_000_000_000)
    self.clock = 10.0

  def update(self, _timeout):
    self.clock += .25
    self.logMonoTime = dict.fromkeys(self, int(self.clock * 1e9))


@pytest.mark.parametrize('changes', [dict(controlsAllowed=True), dict(safetyModel='allOutput'), dict(heartbeatLost=True),
  dict(faults=['relayMalfunction']), dict(faultStatus='faultTemp'), dict(safetyModel='teslaPreap', safetyParam=3),
  dict(safetyModel='teslaPreap', safetyParam=1, safetyRxChecksInvalid=True)])
def test_panda_guard_blocks_permissions_faults_and_radar_safety(changes):
  sm = State()
  for key, value in changes.items():
    setattr(sm['pandaStates'][0], key, value)
  with pytest.raises(ValueError):
    check.panda_guard(sm, 10.0, {'noOutput', 'teslaPreap'})


@pytest.mark.parametrize('age', [-.1, 1.6])
def test_stale_or_future_panda_aborts(age):
  with pytest.raises(ValueError):
    check.panda_guard(State(), 10 + age, {'noOutput'})


@pytest.fixture
def device(tmp_path, monkeypatch):
  for name, value in dict(DATA=tmp_path, ROOT=tmp_path/'runtime', RECOVERY=tmp_path/'recovery',
                          PARAMS=tmp_path/'params', MARKER=tmp_path/'pending',
                          VERSION=tmp_path/'VERSION', MODEL=tmp_path/'model').items():
    monkeypatch.setattr(check, name, value)
  check.ROOT.mkdir()
  check.RECOVERY.mkdir()
  check.PARAMS.mkdir()
  check.VERSION.write_text('17.2')
  check.MODEL.write_bytes(b'comma tizi\0')
  (tmp_path/'openpilot').symlink_to(check.ROOT)
  (check.ROOT/'roadline_release.json').write_text(json.dumps(dict(source_revision=check.BASE, road_ready=False)))
  monkeypatch.setattr(check, 'PINNED', {'controller.py': hashlib.sha256(b'reviewed').hexdigest()})
  (check.ROOT/'controller.py').write_bytes(b'reviewed')
  for relative, attr in [('selfdrive/car/card.py', 'CARD_SHA'), ('panda/board/obj/panda_h7.bin.signed', 'PANDA_SHA')]:
    p = check.ROOT/relative
    p.parent.mkdir(parents=True)
    p.write_bytes(b'reviewed')
    monkeypatch.setattr(check, attr, check.digest(p))
  control = check.RECOVERY/'control.py'
  control.write_bytes(b'recovery')
  monkeypatch.setattr(check, 'RECOVERY_SHA', check.digest(control))
  original = b'#!/usr/bin/env bash\ncd /data/openpilot\nexec ./launch_openpilot.sh\n'
  (check.RECOVERY/'continue-before.sh').write_bytes(original)
  (tmp_path/'continue.sh').write_bytes(b'#!/usr/bin/env bash\n# Roadline staging first-start recovery\n' +
    f'sudo -n /usr/bin/python3 "{check.RECOVERY}/control.py" boot-check || exit $?\n'.encode() + original)
  for key, value in dict(IsOnroad='0', DisableUpdates='1', NAPPedalCanBus='2', NAPPedalCalibDone='1',
                         NAPForcePreAP='1', **dict.fromkeys(check.DISABLED, '0')).items():
    (check.PARAMS/key).write_text(value)
  for key in check.CALIBRATION[2:]:
    (check.PARAMS/key).write_text('1.0')
  settings = {key: base64.b64encode((check.PARAMS/key).read_bytes()).decode() for key in check.CALIBRATION}
  (check.RECOVERY/'settings-before.json').write_text(json.dumps(settings))
  (check.RECOVERY/'state.json').write_text(json.dumps(dict(revision=check.BASE, phase='running',
    launcher_sha256=hashlib.sha256(original).hexdigest(), settings_sha256=check.digest(check.RECOVERY/'settings-before.json'))))
  calls = []
  def run(*args):
    calls.append(args)
    return 'active'
  monkeypatch.setattr(check, 'run', run)
  monkeypatch.setattr(check.pwd, 'getpwnam', lambda _: NS(pw_uid=check.os.getuid(), pw_gid=check.os.getgid()))
  return calls


def test_valid_install_and_calibration_are_read_only(device):
  before = {p: p.read_bytes() for p in check.PARAMS.iterdir()}
  check.validate_install()
  assert before == {p: p.read_bytes() for p in check.PARAMS.iterdir()}
  assert device == [('systemctl', 'is-active', 'comma.service')]


@pytest.mark.parametrize('name', ['OpenpilotEnabledToggle', 'NAPPedalEnabled', 'NAPRadarEnabled', 'NAPiBoosterEnabled',
  'NAPNavigationManeuvers', 'NAPMapDrivingAssist', 'IsOnroad', 'NAPParkedSignalTest', 'NAPScriptRunning', 'DoReboot'])
def test_wrong_entry_state_cannot_enable_settings(device, name):
  (check.PARAMS/name).write_text('1')
  with pytest.raises(ValueError):
    check.validate_install()
  assert not check.MARKER.exists()


@pytest.mark.parametrize('relative', ['controller.py', 'selfdrive/car/card.py', 'panda/board/obj/panda_h7.bin.signed'])
def test_altered_runtime_refused(device, relative):
  (check.ROOT/relative).write_bytes(b'changed')
  with pytest.raises(ValueError):
    check.validate_install()


def test_changed_calibration_or_launcher_refused(device):
  (check.PARAMS/'NAPPedalCalibFactor').write_text('99')
  with pytest.raises(ValueError, match='calibration'):
    check.validate_install()


def test_cleanup_stops_before_disabling_and_never_restores_enabled_settings(device):
  check.MARKER.write_text('pending')
  (check.PARAMS/'OpenpilotEnabledToggle').write_text('1')
  (check.PARAMS/'NAPPedalEnabled').write_text('1')
  calibration = {k: (check.PARAMS/k).read_bytes() for k in check.CALIBRATION}
  check.cleanup()
  assert device == [('systemctl', 'stop', 'comma.service'), ('systemctl', '--no-block', 'start', 'comma.service')]
  assert not check.MARKER.exists()
  assert all((check.PARAMS/k).read_bytes() == b'0' for k in check.DISABLED)
  assert calibration == {k: (check.PARAMS/k).read_bytes() for k in check.CALIBRATION}
  check.cleanup()
  assert len(device) == 2


def test_failed_disable_leaves_service_stopped_and_marker_for_retry(device, monkeypatch):
  check.MARKER.write_text('pending')
  def fail(*_args):
    raise OSError('disk full')
  monkeypatch.setattr(check, 'put', fail)
  with pytest.raises(RuntimeError, match='Cleanup incomplete'):
    check.cleanup()
  assert check.MARKER.exists()
  assert device == [('systemctl', 'stop', 'comma.service')]


@pytest.mark.parametrize('failure', ['observe', 'first_put', 'second_put'])
def test_transaction_failure_disables_and_preserves_calibration(device, monkeypatch, failure):
  sm = State()
  monkeypatch.setitem(sys.modules, 'cereal', NS(messaging=NS(SubMaster=lambda _services: sm)))
  monkeypatch.setattr(check.time, 'monotonic', lambda: sm.clock)
  monkeypatch.setattr(check, 'validate_supervisor', lambda: None)
  def observe(*_args):
    raise ValueError('injected observer failure')
  monkeypatch.setattr(check, 'observe', observe)
  original_put = check.put
  writes = []
  def put(key, value):
    writes.append((key, value))
    assert check.MARKER.exists()
    if value == b'1' and ((failure == 'first_put' and key == 'NAPPedalEnabled') or
                        (failure == 'second_put' and key == 'OpenpilotEnabledToggle')):
      raise OSError('injected setting failure')
    original_put(key, value)
  monkeypatch.setattr(check, 'put', put)
  with pytest.raises((ValueError, OSError)):
    check.check()
  assert all((check.PARAMS/k).read_bytes() == b'0' for k in check.DISABLED)
  assert not check.MARKER.exists()
  assert device[-2:] == [('systemctl', 'stop', 'comma.service'), ('systemctl', '--no-block', 'start', 'comma.service')]


def test_supervisor_missing_cleanup_refused(monkeypatch):
  monkeypatch.setenv('INVOCATION_ID', 'synthetic')
  monkeypatch.setattr(check, 'HELPER', Path(check.__file__).resolve())
  monkeypatch.setattr(check, 'run', lambda *_args: f'MainPID={check.os.getpid()}\nRuntimeMaxUSec=3min\nExecStopPost=')
  with pytest.raises(ValueError, match='cleanup'):
    check.validate_supervisor()


def test_failed_service_stop_does_not_start_another_stack(device, monkeypatch):
  check.MARKER.write_text('pending')
  calls = []
  def fail(*args):
    calls.append(args)
    raise subprocess.TimeoutExpired(args, 20)
  monkeypatch.setattr(check, 'run', fail)
  with pytest.raises(RuntimeError, match='Cleanup incomplete'):
    check.cleanup()
  assert check.MARKER.exists()
  assert calls == [('systemctl', 'stop', 'comma.service')]
  assert all((check.PARAMS/k).read_bytes() == b'0' for k in check.DISABLED)


def test_faulted_feedback_aborts(device):
  from opendbc.can import CANPacker
  packer = CANPacker('tesla_preap')
  for signals in [dict(EPAS_eacStatus=2), dict(EPAS_eacStatus=3), dict(EPAS_steeringFault=1), dict(EPAS_steeringReduced=1)]:
    address, data, bus = packer.make_can_msg('EPAS_sysStatus', 0, signals)
    with pytest.raises(ValueError, match='EPAS'):
      check.WireObservation().can(1_000_000_000, [frame(address, data[:-1], bus)])
  with pytest.raises(ValueError, match='Pedal'):
    check.WireObservation().can(1_000_000_000, [frame(0x552, [1, 20, 1, 20, 0x60], 2)])


@pytest.mark.parametrize('scenario', ['normal', 'no_wake', 'no_initialize', 'lost_control_stream', 'engagement', 'drive', 'unexpected_tx'])
def test_observation_deadlines_and_continuous_guards(device, monkeypatch, scenario):
  from opendbc.can import CANPacker
  packer = CANPacker('tesla_preap')
  address, data, bus = packer.make_can_msg('EPAS_sysStatus', 0, dict(EPAS_eacStatus=1))
  epas = frame(address, data[:-1], bus)
  sm = State()
  monkeypatch.setattr(check.time, 'monotonic', lambda: sm.clock)
  check.put('OpenpilotEnabledToggle', b'1')
  check.put('NAPPedalEnabled', b'1')
  ordinary_update = sm.update
  def update(timeout):
    ordinary_update(timeout)
    if scenario != 'no_wake':
      (check.PARAMS/'IsOnroad').write_text('1')
      sm['pandaStates'][0].safetyModel = 'elm327' if scenario == 'no_initialize' else 'teslaPreap'
      sm['pandaStates'][0].safetyParam = 1
    if sm.clock >= 11:
      if scenario == 'lost_control_stream':
        sm.seen['carControl'] = False
      elif scenario == 'engagement':
        sm['carControl'].enabled = True
      elif scenario == 'drive':
        sm['carState'].gearShifter = 'drive'
  sm.update = update
  def drain(sock):
    if sock == 'can':
      frames = [frame(0x552, [1, 20, 1, 20, int(sm.clock * 4) % 16], 2), epas]
    else:
      frames = [frame(0x551, [0, 0, 0, 0, 0], 2), frame(0x488, [1, 2, 3], 0), frame(0x214, [1, 0], 0)]
      if scenario == 'unexpected_tx':
        frames.append(frame(0x45, [0] * 7, 0))
    return [NS(logMonoTime=int(sm.clock * 1e9), **{sock: [NS(address=a, dat=d, src=b) for a, d, b in frames]})]
  messaging = NS(sub_sock=lambda name: name, drain_sock=drain)
  if scenario == 'normal':
    check.observe(sm, messaging)
    report = json.loads((check.DATA/'roadline-parked-startup-result.json').read_text())
    assert report['road_ready'] is False
    assert report['pedal_states']['0'] > 50
    assert report['disabled_outgoing_requests']['0x551 bus 2'] > 50
    assert 25 <= sm.clock < 26
  else:
    with pytest.raises(ValueError):
      check.observe(sm, messaging)
    assert sm.clock <= 56


def test_successful_transaction_returns_to_passive(device, monkeypatch, capsys):
  sm = State()
  monkeypatch.setitem(sys.modules, 'cereal', NS(messaging=NS(SubMaster=lambda _services: sm)))
  monkeypatch.setattr(check.time, 'monotonic', lambda: sm.clock)
  monkeypatch.setattr(check, 'validate_supervisor', lambda: None)
  def observe(*_args):
    check.require_settings(armed=True)
  monkeypatch.setattr(check, 'observe', observe)
  check.check()
  assert 'LIVE noOutput RESTORED' in capsys.readouterr().out
  check.require_settings()
  assert sm.clock >= 18


def test_correct_supervisor_is_required(monkeypatch):
  monkeypatch.setenv('INVOCATION_ID', 'synthetic')
  monkeypatch.setattr(check, 'HELPER', Path(check.__file__).resolve())
  good = (f'MainPID={check.os.getpid()}\nRuntimeMaxUSec=3min\n' +
          f'ExecStopPost={{ path={check.PYTHON} ; argv[]={check.PYTHON} {check.HELPER} cleanup ; ignore_errors=no ; }}')
  monkeypatch.setattr(check, 'run', lambda *_args: good)
  check.validate_supervisor()
  for bad in [good.replace('3min', 'infinity'), good.replace(str(check.os.getpid()), '99999999')]:
    monkeypatch.setattr(check, 'run', lambda *_args, response=bad: response)
    with pytest.raises(ValueError):
      check.validate_supervisor()
