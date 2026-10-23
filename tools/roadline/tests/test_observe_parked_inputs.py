"""Read-only observation tests with wire bytes and simulated live state."""
from types import SimpleNamespace

import pytest

from openpilot.tools.roadline.observe_parked_inputs import Capture, DISABLED, require_parked


def test_missing_messages_never_report_parser_defaults_as_observations():
  summary = Capture().summary(10)
  assert len(summary) == 4
  for record in summary.values():
    assert record['received'] == 0
    assert record['age_seconds'] is None
    assert all(v is None for v in record['signals'].values())


def test_recorded_pedal_feedback_reports_fault_and_advancing_counter():
  capture = Capture()
  for i, raw in enumerate(('01dd00ea5271', '01d300ea5368', '01cd00e75460')):
    capture.feed(10_000_000_000 + i * 10_000_000, [(0x552, bytes.fromhex(raw), 2)])
  record = capture.summary(10.03)['GAS_SENSOR bus 2 (0x552)']
  assert record['received'] == 3
  assert record['bad_checksum'] == 0
  assert record['age_seconds'] == .01
  assert record['signals']['STATE']['observed'] == [5]
  assert record['signals']['IDX']['observed'] == [2, 3, 4]
  assert record['signals']['IDX']['consecutive_steps'] == 2
  assert record['signals']['IDX']['other_steps'] == 0


def test_brake_uses_raw_status_and_ignores_wrong_bus():
  capture = Capture()
  capture.feed(10_000_000_000, [(0x20a, bytes([4]) + bytes(7), 0),
                              (0x20a, bytes([8]) + bytes(7), 0),
                              (0x20a, bytes([12]) + bytes(7), 2)])
  record = capture.summary(10)['BrakeMessage bus 0 (0x20a)']
  assert record['received'] == 2
  assert record['bad_checksum'] is None
  assert record['checksum_validation'] == 'not_defined_in_dbc'
  assert record['signals']['driverBrakeStatus']['observed'] == [1, 2]


def test_steering_and_factory_pedal_decode_using_runtime_dbc():
  from opendbc.can import CANPacker
  packer = CANPacker('tesla_preap')
  frames = []
  for name, fields in [('EPAS_sysStatus', {'EPAS_torsionBarTorque': 2.0, 'EPAS_internalSAS': 15.0,
                                          'EPAS_handsOnLevel': 2}), ('DI_torque1', {'DI_pedalPos': 20.0})]:
    address, data, bus = packer.make_can_msg(name, 0, fields)
    if name == 'EPAS_sysStatus':
      data = data[:-1] + bytes([((address & 255) + (address >> 8) + sum(data[:-1])) & 255])
    frames.append((address, data, bus))
  capture = Capture()
  capture.feed(10_000_000_000, frames)
  result = capture.summary(10)
  assert result['EPAS_sysStatus bus 0 (0x370)']['signals']['EPAS_torsionBarTorque']['last'] == 2.0
  assert result['EPAS_sysStatus bus 0 (0x370)']['signals']['EPAS_internalSAS']['last'] == pytest.approx(15.0, abs=.001)
  assert result['DI_torque1 bus 0 (0x108)']['signals']['DI_pedalPos']['last'] == 20.0
  assert result['DI_torque1 bus 0 (0x108)']['checksum_validation'] == 'not_verified'


def test_recorded_factory_pedal_format_is_observed_without_false_checksum_failure():
  capture = Capture()
  # Received 0x108 data from the earlier capture; the additive residual is 7,
  # not the 9 assumed by the old address-sum check. No vehicle identifiers.
  frames = [bytes.fromhex(raw) for raw in ('14401400eeff005c', '14601400eeff007c', '14801400eeff009c')]
  capture.feed(10_000_000_000, [(0x108, data, 0) for data in frames])
  result = capture.summary(10)['DI_torque1 bus 0 (0x108)']
  assert result['bad_checksum'] is None
  assert result['checksum_validation'] == 'not_verified'
  assert result['checksum_additive_residuals'] == {'0x07': 3}
  assert result['signals']['DI_pedalPos']['samples'] == 3
  assert result['signals']['DI_pedalPos']['last'] == 0


def test_unknown_factory_checksum_residual_is_reported_without_claiming_integrity():
  capture = Capture()
  data = bytearray.fromhex('14401400eeff005c')
  data[-1] ^= 1
  capture.feed(10_000_000_000, [(0x108, bytes(data), 0)])
  result = capture.summary(10)['DI_torque1 bus 0 (0x108)']
  assert result['checksum_validation'] == 'not_verified'
  assert result['bad_checksum'] is None
  assert result['checksum_additive_residuals'] == {'0x08': 1}


def test_bad_steering_checksum_still_rejected():
  capture = Capture()
  capture.feed(10_000_000_000, [(0x370, bytes(8), 0)])
  result = capture.summary(10)['EPAS_sysStatus bus 0 (0x370)']
  assert result['bad_checksum'] == 1
  assert result['checksum_validation'] == 'address_sum'
  assert result['signals']['EPAS_torsionBarTorque'] is None


@pytest.mark.parametrize('raw,field', [('01dd00ea5270', 'bad_checksum'), ('01dd00ea52', 'bad_length')])
def test_bad_pedal_frames_are_counted_without_becoming_measurements(raw, field):
  capture = Capture()
  capture.feed(10_000_000_000, [(0x552, bytes.fromhex(raw), 2)])
  result = capture.summary(10)['GAS_SENSOR bus 2 (0x552)']
  assert result[field] == 1
  assert result['age_seconds'] is None
  assert result['signals']['STATE'] is None


class FakeSM(dict):
  def __init__(self):
    super().__init__(carState=SimpleNamespace(gearShifter='park', canValid=True, canTimeout=False, vEgo=0., vEgoRaw=0.),
                     pandaStates=[SimpleNamespace(safetyModel='noOutput', controlsAllowed=False,
                                                   faultStatus='none', faults=[], heartbeatLost=False)])
    self.seen = dict.fromkeys(self, True)
    self.valid = dict.fromkeys(self, True)
    self.logMonoTime = dict.fromkeys(self, 10_000_000_000)


@pytest.fixture
def safe(tmp_path):
  for key in DISABLED:
    (tmp_path / key).write_text('0')
  return FakeSM(), tmp_path


def test_valid_parked_no_output_state_is_accepted(safe):
  sm, params = safe
  require_parked(sm, params, 10.1)


@pytest.mark.parametrize('key', DISABLED)
@pytest.mark.parametrize('missing', [False, True])
def test_enabled_or_missing_setting_stops_capture(safe, key, missing):
  sm, params = safe
  if missing:
    (params / key).unlink()
  else:
    (params / key).write_text('1')
  with pytest.raises(ValueError, match=key):
    require_parked(sm, params, 10.1)


@pytest.mark.parametrize('case', ['missing', 'stale', 'invalid', 'gear', 'speed', 'nan_speed',
                                 'can_timeout', 'no_panda', 'active_safety', 'allowed', 'fault', 'heartbeat'])
def test_live_state_changes_stop_capture(safe, case):
  sm, params = safe
  if case == 'missing':
    sm.seen['pandaStates'] = False
  elif case == 'stale':
    sm.logMonoTime['carState'] = 1
  elif case == 'invalid':
    sm.valid['carState'] = False
  elif case == 'gear':
    sm['carState'].gearShifter = 'drive'
  elif case == 'speed':
    sm['carState'].vEgo = .1
  elif case == 'nan_speed':
    sm['carState'].vEgoRaw = float('nan')
  elif case == 'can_timeout':
    sm['carState'].canTimeout = True
  elif case == 'no_panda':
    sm['pandaStates'] = []
  elif case == 'active_safety':
    sm['pandaStates'][0].safetyModel = 'teslaPreap'
  elif case == 'allowed':
    sm['pandaStates'][0].controlsAllowed = True
  elif case == 'fault':
    sm['pandaStates'][0].faults = ['fault']
  elif case == 'heartbeat':
    sm['pandaStates'][0].heartbeatLost = True
  with pytest.raises(ValueError):
    require_parked(sm, params, 10.1)
