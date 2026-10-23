"""Decode wire bytes independently of CANPacker, including captured fault frames."""
import math
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from opendbc.can import CANParser
from opendbc.car.tesla.preap.pedal_feedback import PedalFeedback


def sensor_frame(state, counter):
  # Fixed synthetic sensor values; firmware encodes status in the high nibble.
  data = bytearray.fromhex('01f400fa0000')
  data[4] = (state << 4) | counter
  data[5] = (0x05 + 0x52 + sum(data[:5])) & 255
  return bytes(data)


def parser(bus=2):
  return CANParser('tesla_preap', [('GAS_SENSOR', math.nan)], bus)


def feed(cp, feedback, raw, t, bus=2):
  cp.update([(int(t * 1e6), [(0x552, raw, bus)])])
  with patch('opendbc.car.tesla.preap.pedal_feedback.nap_conf') as conf:
    conf.pedal_to_di.side_effect = float
    feedback.update(cp.vl['GAS_SENSOR'], t)
  return cp.vl['GAS_SENSOR']


@pytest.mark.parametrize('bus', [0, 2])
def test_wire_status_and_counter_are_independent(bus):
  cp, feedback = parser(bus), PedalFeedback()
  # Establish a moving counter first; an unchanging parser default is not
  # evidence of live hardware and must not be treated as available.
  feed(cp, feedback, sensor_frame(0, 15), 990, bus)
  for state in range(16):
    for counter in range(16):
      value = feed(cp, feedback, sensor_frame(state, counter), 1000 + 10 * (state * 16 + counter), bus)
      assert value['STATE'] == state
      assert value['IDX'] == counter
      assert feedback.available == (state == 0)


def test_recorded_timeout_frames_do_not_look_healthy_or_frozen():
  cp, feedback = parser(), PedalFeedback()
  # Five consecutive feedback frames from the reported recording, with no
  # identifiers, location, or calibration data. Low nibble advances 2..6.
  frames = ['01dd00ea5271', '01d300ea5368', '01cd00e75460', '01eb00e7557f', '01e900ef5686']
  for counter, frame in enumerate(frames, start=2):
    value = feed(cp, feedback, bytes.fromhex(frame), 1000 + counter * 10)
    assert value['STATE'] == 5
    assert value['IDX'] == counter
    assert not feedback.timeout
    assert not feedback.available


def test_healthy_counter_wrap_stale_stream_and_fault_recovery():
  cp, feedback = parser(), PedalFeedback()
  for counter, t in [(14, 1000), (15, 1010), (0, 1020), (1, 1030)]:
    feed(cp, feedback, sensor_frame(0, counter), t)
    assert feedback.available
  feed(cp, feedback, sensor_frame(0, 1), 1540)
  assert feedback.timeout and not feedback.available
  feed(cp, feedback, sensor_frame(5, 2), 1550)
  assert not feedback.timeout and not feedback.available
  feed(cp, feedback, sensor_frame(0, 3), 1560)
  assert feedback.available


@pytest.mark.parametrize('timeout', [False, True])
def test_faulted_or_stale_feedback_only_sends_disabled_pedal(timeout):
  from opendbc.car.tesla.preap.carcontroller import PreAPLongController
  cs = SimpleNamespace(
    cruiseEnabled=True, enableLongControl=True, pedal_interceptor_value=0.0,
    cruise_buttons=0, prev_cruise_buttons=0, pedal_timeout=timeout,
    pedal=SimpleNamespace(available=False, torque_level=0.0),
    out=SimpleNamespace(vEgo=10.0, aEgo=0.0, gasPressed=False, canValid=True),
  )
  cc = SimpleNamespace(enabled=True, longActive=True, actuators=SimpleNamespace(accel=1.0))
  with patch('opendbc.car.tesla.preap.carcontroller.nap_conf') as conf, \
       patch('opendbc.car.tesla.preap.carcontroller.get_zero_torque') as zero, \
       patch('opendbc.car.tesla.preap.carcontroller.TeslaCANPreAP') as can:
    conf.use_pedal = True
    conf.pedal_factor = 1.0
    conf.di_to_pedal.side_effect = float
    zero.return_value.get.return_value = 0.0
    controller = PreAPLongController()
    controller.update(cc, cs, 100, can, 2)
    assert can.create_pedal_command.call_count == 1
    assert can.create_pedal_command.call_args.kwargs['enable'] == 0


def test_carstate_cancels_faulted_speed_request_without_auto_resume():
  from opendbc.car import Bus
  from opendbc.car.tesla.interface import CarInterface
  from opendbc.car.tesla.preap.carstate import update_preap

  cp = CarInterface.get_params('TESLA_MODEL_S_PREAP', {i: {} for i in range(8)}, [],
                               alpha_long=False, is_release=False, docs=False)
  ci = CarInterface(cp)
  chassis = ci.can_parsers[Bus.chassis]
  chassis.vl['DI_torque2']['DI_gear'] = 4
  for key in ('DOOR_STATE_FL', 'DOOR_STATE_FR', 'DOOR_STATE_RL', 'DOOR_STATE_RR', 'DOOR_STATE_FrontTrunk', 'BOOT_STATE'):
    chassis.vl['GTW_carState'][key] = 0
  chassis.vl['EPAS_sysStatus']['EPAS_torsionBarTorque'] = 0.0
  sensor = ci.can_parsers[Bus.ap_party].vl['GAS_SENSOR']
  sensor.update(STATE=0, IDX=1, INTERCEPTOR_GAS=0.0, INTERCEPTOR_GAS2=0.0)
  with patch('opendbc.car.tesla.preap.carstate.nap_conf') as conf, \
       patch('opendbc.car.tesla.preap.carstate._current_time_millis', return_value=1000), \
       patch('opendbc.car.tesla.preap.pedal_feedback.nap_conf') as feedback_conf:
    conf.use_pedal = True
    conf.pedal_factor = 1.0
    feedback_conf.pedal_to_di.side_effect = float
    ci.CS.engagement.cruiseEnabled = True
    ci.CS.engagement.enableLongControl = True
    ci.CS.engagement.pedal_speed_kph = 40.0
    assert update_preap(ci.CS, ci.can_parsers).pedalLongActive
    sensor.update(STATE=5, IDX=2)
    state = update_preap(ci.CS, ci.can_parsers)
    assert state.cruiseState.enabled
    assert not state.pedalLongActive
    assert not ci.CS.enableLongControl
    sensor.update(STATE=0, IDX=3)
    state = update_preap(ci.CS, ci.can_parsers)
    assert ci.CS.pedal.available
    assert not state.pedalLongActive
    assert not ci.CS.enableLongControl
