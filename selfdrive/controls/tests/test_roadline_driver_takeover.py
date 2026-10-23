"""Regressions from the first Roadline drive: takeover and cruise selection.

Exercises the real Pre-AP state update and engagement FSM. No car connection.
"""
import io
from unittest.mock import patch

import pytest

from opendbc.car import Bus
from opendbc.car.tesla.preap.engagement import PreAPEngagement
from opendbc.car.tesla.preap.carstate import update_preap
from opendbc.car.tesla.preap.tests import test_preap_carstate as _carstate_fixture


def step(eng, button=0, previous=0, t=1000, speed=14.2, units='MPH'):
  return eng.process_buttons(button, previous, t, speed, units, True, True, True, False)


@pytest.mark.parametrize('speed,units,expected', [(14.2, 'MPH', 32 * 1.609344), (6.2, 'MPH', 14 * 1.609344),
                                                 (14.2, 'KPH', 51), (0., 'MPH', 0.)])
def test_double_pull_captures_current_speed_despite_speed_limit_feed(speed, units, expected):
  eng = PreAPEngagement(True, 400)
  with patch('os.path.exists', return_value=True), patch('builtins.open', return_value=io.StringIO(str(60 / 2.236936))):
    step(eng, 2, 0, 1000, speed, units)
    step(eng, 0, 2, 1050, speed, units)
    step(eng, 2, 0, 1250, speed, units)
  assert eng.enableLongControl
  assert eng.pedal_speed_kph == pytest.approx(expected)


def test_speed_limit_feed_cannot_change_selected_speed_after_engagement():
  eng = PreAPEngagement(False, 400)
  with patch('os.path.exists', return_value=False):
    step(eng, 2, speed=14.2)
  selected = eng.pedal_speed_kph
  for mph in (60, 75, 30, 60):
    with patch('os.path.exists', return_value=True), patch('builtins.open', return_value=io.StringIO(str(mph / 2.236936))):
      step(eng, t=2000)
    assert eng.pedal_speed_kph == selected


def test_manual_stalk_speed_adjustments_remain_available():
  eng = PreAPEngagement(False, 400)
  step(eng, 2, speed=14.2)
  original = eng.pedal_speed_kph
  step(eng, 16, 0, 2000, speed=14.2)
  assert eng.pedal_speed_kph == pytest.approx(original + 1.609344)
  step(eng, 32, 0, 3000, speed=14.2)
  assert eng.pedal_speed_kph == pytest.approx(original)


def test_override_blocks_stalk_until_release_then_requires_fresh_gesture():
  eng = PreAPEngagement(True, 400)
  step(eng, 2, 0, 1000)
  step(eng, 2, 0, 1250)
  eng.handle_steering_disengage(True)
  assert not eng.cruiseEnabled and not eng.enableLongControl
  # Both pulls while the driver still owns steering must be rejected.
  step(eng, 2, 0, 2000)
  step(eng, 0, 2, 2050)
  step(eng, 2, 0, 2250)
  assert not eng.cruiseEnabled and not eng.enableLongControl
  eng.handle_steering_disengage(False)
  step(eng, 0, 2, 2300)
  assert not eng.cruiseEnabled
  step(eng, 2, 0, 2350)
  assert eng.cruiseEnabled and not eng.enableLongControl
  step(eng, 0, 2, 2400)
  step(eng, 2, 0, 2600)
  assert eng.enableLongControl


@pytest.fixture
def interface():
  ci = _carstate_fixture.TestPreAPCarStateUpdate()._make_interface()
  ci.update([])
  ci.can_parsers[Bus.chassis].vl['DI_torque2']['DI_gear'] = 4
  return ci


@pytest.mark.parametrize('level,status,error,disengage,fault', [
  (0, 1, 0, False, False), (2, 1, 0, False, False), (3, 1, 0, True, False),
  (0, 0, 6, True, True), (0, 0, 7, True, True), (0, 0, 8, True, True), (0, 0, 9, True, True),
  (0, 1, 6, False, False),
])
def test_panda_takeover_conditions_are_reported_by_real_carstate(interface, level, status, error, disengage, fault):
  ci = interface
  epas = ci.can_parsers[Bus.chassis].vl['EPAS_sysStatus']
  epas['EPAS_handsOnLevel'] = level
  epas['EPAS_eacStatus'] = status
  epas['EPAS_eacErrorCode'] = error
  ci.CS.engagement.cruiseEnabled = ci.CS.engagement.enableLongControl = True
  with patch.object(ci.CS, 'update_speed_kf', return_value=(15., 0.)):
    state = update_preap(ci.CS, ci.can_parsers)
  assert state.steeringDisengage == disengage
  assert state.steerFaultTemporary == fault
  if disengage:
    assert not ci.CS.engagement.cruiseEnabled
    assert not ci.CS.engagement.enableLongControl
    assert not state.cruiseState.enabled


def test_filtered_manual_steering_cancels_and_does_not_quietly_hand_back(interface):
  ci = interface
  epas = ci.can_parsers[Bus.chassis].vl['EPAS_sysStatus']
  epas['EPAS_eacStatus'] = 1
  epas['EPAS_handsOnLevel'] = 1
  epas['EPAS_torsionBarTorque'] = 6.0
  ci.CS.engagement.cruiseEnabled = ci.CS.engagement.enableLongControl = True
  with patch.object(ci.CS, 'update_speed_kf', return_value=(5., 0.)):
    for _ in range(5):
      state = update_preap(ci.CS, ci.can_parsers)
    assert state.steeringPressed
    assert not state.cruiseState.enabled
    epas['EPAS_torsionBarTorque'] = 0.
    for _ in range(110):
      state = update_preap(ci.CS, ci.can_parsers)
    assert not state.steeringPressed
    assert not state.cruiseState.enabled


def test_legacy_dashboard_offset_cannot_raise_pedal_cruise_target(interface):
  ci = interface
  ci.CS.engagement.cruiseEnabled = ci.CS.engagement.enableLongControl = True
  ci.CS.engagement.pedal_speed_kph = 32 * 1.609344
  from opendbc.car.tesla.preap.nap_conf import NAPConf
  from unittest.mock import PropertyMock
  real_open = open
  def fake_open(path, *args, **kwargs):
    if str(path) == '/data/nap_settings.json':
      return io.StringIO('{"speed_offset":true,"speed_trim":10}')
    return real_open(path, *args, **kwargs)
  with patch.object(NAPConf, 'use_pedal', new_callable=PropertyMock, return_value=True), \
       patch.object(ci.CS, 'update_speed_kf', return_value=(14.2, 0.)), \
       patch('os.path.exists', return_value=False), \
       patch('builtins.open', side_effect=fake_open):
    state = update_preap(ci.CS, ci.can_parsers)
  assert state.cruiseState.speed * 2.236936 == pytest.approx(32, abs=.01)


@pytest.mark.parametrize('long_active', [False, True])
def test_disabled_system_never_sends_enabled_pedal_hold(long_active):
  from types import SimpleNamespace as N
  from unittest.mock import MagicMock
  from opendbc.car.tesla.preap import carcontroller as module
  from openpilot.selfdrive.controls.tests.test_integration_repair import pedal_cs
  controller = module.PreAPLongController()
  controller.vdas = MagicMock()
  can = MagicMock()
  can.create_pedal_command.side_effect = lambda cmd, enable: dict(cmd=cmd, enable=enable)
  control = N(enabled=False, longActive=long_active, actuators=N(accel=1.), orientationNED=[])
  with patch.object(module, 'nap_conf', N(use_pedal=True, pedal_factor=1., di_to_pedal=lambda d: d)), \
       patch.object(module, 'get_zero_torque') as zero:
    zero.return_value.get.return_value = 4.
    sends = controller.update(control, pedal_cs(), 0, can, 0)
  assert sends[-1]['enable'] == 0
  controller.vdas.update.assert_not_called()


def test_signaled_takeover_cancels_before_the_filtered_pressed_flag(interface):
  ci = interface
  chassis = ci.can_parsers[Bus.chassis]
  chassis.vl['GTW_carState']['BC_indicatorLStatus'] = 1
  chassis.vl['EPAS_sysStatus']['EPAS_eacStatus'] = 1
  chassis.vl['EPAS_sysStatus']['EPAS_handsOnLevel'] = 1
  chassis.vl['EPAS_sysStatus']['EPAS_torsionBarTorque'] = 3.5
  ci.CS.engagement.cruiseEnabled = ci.CS.engagement.enableLongControl = True
  with patch.object(ci.CS, 'update_speed_kf', return_value=(18 * .44704, 0.)):
    state = update_preap(ci.CS, ci.can_parsers)
  assert not state.steeringPressed  # Existing 50-frame display filter at this speed.
  assert not state.cruiseState.enabled
  assert not ci.CS.enableLongControl


@pytest.fixture
def wire_controller(interface):
  from types import SimpleNamespace as N
  from unittest.mock import MagicMock
  from opendbc.car.tesla.preap import carcontroller as module
  ci = interface
  ci.CC.CP.openpilotLongitudinalControl = True
  ci.CC.preap_long.vdas = MagicMock()
  ci.CC.preap_long.vdas.update.return_value = 6.
  ci.CS.cruiseEnabled = ci.CS.enableLongControl = True
  ci.CS.pedal_timeout = False
  ci.CS.pedal_interceptor_value = 6.
  ci.CS.out.vEgo = ci.CS.out.vEgoRaw = 5.
  ci.CS.out.canValid = True
  ci.CS.out.leftBlinker = True
  ci.CS.out.steeringAngleDeg = 25.
  ci.CS.hands_on_level = 0
  ci.CC.params = N(get_bool=lambda _: False)
  ci.CC.tap_params = None
  with patch.object(module, 'nap_conf', N(use_pedal=True, pedal_factor=1., di_to_pedal=lambda x: x)), \
       patch.object(module, 'get_zero_torque') as zero:
    zero.return_value.get.return_value = 4.
    yield ci


def wire_tick(ci, enabled=True, lat=True, long=True, curvature=0.):
  from opendbc.car import structs
  from opendbc.can import CANParser
  from opendbc.car.tesla.values import CANBUS
  control = structs.CarControl()
  control.enabled, control.latActive, control.longActive = enabled, lat, long
  control.actuators.steeringAngleDeg = 30.
  control.actuators.curvature = curvature
  control.actuators.accel = .4
  # These routing checks assume fresh pedal feedback. Empty input CAN in
  # update_preap otherwise sets timeout, which throttles idle heartbeats to 1 Hz.
  # Pedal feedback parsing/timeouts are covered by the existing pedal tests.
  ci.CS.pedal_timeout = False
  # Both parity slots are exercised; command messages are emitted every other tick.
  frames = []
  for _ in range(2):
    _, sends = ci.CC._update_preap(control.as_reader(), ci.CS)
    frames.extend(sends)
  parser = CANParser('tesla_preap', [('DAS_steeringControl', 0), ('EPB_epasControl', 0)], CANBUS.party)
  parser.update([(1000000000 + ci.CC.frame * 10000000, frames)])
  pedal = [data for addr, data, _ in frames if addr == 0x551]
  assert pedal
  assert parser.vl['EPB_epasControl']['EPB_epasEACAllow'] == 1  # Preserve normal power steering.
  return bool(parser.vl['DAS_steeringControl']['DAS_steeringControlType']), bool(pedal[-1][4] & 0x80)


@pytest.mark.parametrize('mph,signal,trigger', [
  (8., True, 'pressed'), (18., True, 'torque'), (40., False, 'level'),
  (60., False, 'pressed'), (0., False, 'level'), (8., True, 'epas'),
])
def test_packed_commands_stay_disabled_after_steering_release(wire_controller, mph, signal, trigger):
  ci = wire_controller
  ci.CS.out.vEgo = ci.CS.out.vEgoRaw = mph * .44704
  ci.CS.out.leftBlinker = signal
  assert wire_tick(ci) == (True, True)
  ci.CS.out.steeringPressed = trigger == 'pressed'
  ci.CS.out.steeringTorque = 3.5 if trigger == 'torque' else 0.
  ci.CS.hands_on_level = 3 if trigger == 'level' else 0
  ci.CS.out.steeringDisengage = trigger == 'epas'
  assert wire_tick(ci) == (False, False)
  ci.CS.out.steeringPressed = False
  ci.CS.out.steeringTorque = 0.
  ci.CS.hands_on_level = 0
  ci.CS.out.steeringDisengage = False
  # Deliberately stale enabled/cruise flags must not cause timed reacquisition.
  for _ in range(60):
    assert wire_tick(ci) == (False, False)
  ci.CS.cruiseEnabled = ci.CS.enableLongControl = False
  assert wire_tick(ci, enabled=False, lat=False, long=False) == (False, False)
  assert wire_tick(ci, enabled=False, lat=False, long=False) == (False, False)
  # The FSM tests separately require a fresh stalk gesture to raise these flags.
  ci.CS.cruiseEnabled = ci.CS.enableLongControl = True
  assert wire_tick(ci) == (True, True)


@pytest.mark.parametrize('enabled,cruise', [(False, True), (True, False), (False, False)])
def test_packed_commands_require_application_and_cruise_enable(wire_controller, enabled, cruise):
  ci = wire_controller
  ci.CS.cruiseEnabled = cruise
  assert wire_tick(ci, enabled=enabled) == (False, False)


def test_brake_preserves_steering_but_disables_pedal_commands(wire_controller):
  from unittest.mock import PropertyMock
  from opendbc.car.tesla.preap.nap_conf import NAPConf
  ci = wire_controller
  ci.CS.engagement.cruiseEnabled = ci.CS.engagement.enableLongControl = True
  ci.CS.engagement.pedal_speed_kph = 40.
  chassis = ci.can_parsers[Bus.chassis]
  chassis.vl['EPAS_sysStatus']['EPAS_eacStatus'] = 1
  chassis.vl['BrakeMessage']['driverBrakeStatus'] = 2
  with patch.object(NAPConf, 'use_pedal', new_callable=PropertyMock, return_value=True), \
       patch.object(ci.CS, 'update_speed_kf', return_value=(5., 0.)):
    ci.CS.out = update_preap(ci.CS, ci.can_parsers)
  assert ci.CS.out.brake == 1.
  assert ci.CS.out.cruiseState.enabled
  assert not ci.CS.enableLongControl
  # Even a stale longActive request cannot keep the pedal enabled after braking.
  assert wire_tick(ci, long=True) == (True, False)
  # Steering takeover while braking still cancels both axes.
  chassis.vl['EPAS_sysStatus']['EPAS_torsionBarTorque'] = 6.
  with patch.object(NAPConf, 'use_pedal', new_callable=PropertyMock, return_value=True), \
       patch.object(ci.CS, 'update_speed_kf', return_value=(5., 0.)):
    ci.CS.out = update_preap(ci.CS, ci.can_parsers)
    assert not ci.CS.out.cruiseState.enabled
    assert wire_tick(ci) == (False, False)
    chassis.vl['EPAS_sysStatus']['EPAS_torsionBarTorque'] = 0.
    chassis.vl['BrakeMessage']['driverBrakeStatus'] = 1
    for _ in range(5):
      ci.CS.out = update_preap(ci.CS, ci.can_parsers)
    assert wire_tick(ci) == (False, False)
  assert not ci.CS.engagement.process_brake_resume(5000, 0., False, True, True, True, True, True)
  assert not ci.CS.engagement.cruiseEnabled
  assert not ci.CS.engagement.enableLongControl
