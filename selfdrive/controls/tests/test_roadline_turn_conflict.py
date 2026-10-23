"""Direction veto and full cancellation, including actual CAN output."""
from types import SimpleNamespace as N

import pytest
from cereal import log
from opendbc.car.tesla.preap.turn_safety import TurnDirectionGuard, turn_direction_conflict
from openpilot.selfdrive.controls.lib.turn_steering_gate import TurnSteeringGate
from openpilot.selfdrive.selfdrived.selfdrived import SelfdriveD
from openpilot.selfdrive.selfdrived.events import Events, ET
from openpilot.selfdrive.selfdrived.state import StateMachine
from openpilot.selfdrive.controls.tests.test_roadline_driver_takeover import (
  interface, wire_controller, wire_tick,
)


def car_state(left=True, right=False, mph=7.0):
  return N(leftBlinker=left, rightBlinker=right, vEgo=mph * .44704,
           cruiseState=N(enabled=True))


@pytest.mark.parametrize('left,right,curvature', [
  (True, False, .02555), (True, False, .13542),
  (False, True, -.02555), (False, True, -.13542),
])
@pytest.mark.parametrize('probabilities', [[], [1., 0., 0.], [0., .4, .4]])
def test_opposite_sharp_request_blocked_without_model_turn_label(left, right, curvature, probabilities):
  cs = car_state(left, right)
  model = N(action=N(desiredCurvature=curvature), meta=N(desireState=probabilities))
  assert turn_direction_conflict(cs, curvature)
  assert not TurnSteeringGate().allowed(cs, model)


@pytest.mark.parametrize('left,right,mph,curvature', [
  (True, False, 7., -.03), (False, True, 7., .03),
  (True, False, 7., .019), (False, False, 7., .14),
  (True, True, 7., .14), (True, False, 26., .03),
])
def test_matching_turns_small_corrections_and_unsignaled_bends_are_unchanged(left, right, mph, curvature):
  assert not turn_direction_conflict(car_state(left, right, mph), curvature)


def test_bad_numeric_input_blocks_and_threshold_is_inclusive():
  cs = car_state(mph=25.)
  assert turn_direction_conflict(cs, .02)
  for value in (float('nan'), float('inf'), None):
    assert turn_direction_conflict(cs, value)
  cs.vEgo = float('nan')
  assert turn_direction_conflict(cs, 0.)


def test_signal_release_or_good_prediction_cannot_clear_latch():
  cs, guard = car_state(), TurnDirectionGuard()
  assert guard.update(cs, [.03], enabled=True, cruise_enabled=True)
  cs.leftBlinker = False
  for enabled, cruise in ((True, True), (False, True), (True, False)):
    assert guard.update(cs, [0.], enabled=enabled, cruise_enabled=cruise)
  assert not guard.update(cs, [0.], enabled=False, cruise_enabled=False)
  assert not guard.update(cs, [0.], enabled=True, cruise_enabled=True)


@pytest.mark.parametrize('raw,command', [(.03, 0.), (0., .03)])
def test_supervisor_reports_immediate_disable_and_blocks_reentry(raw, command):
  obj = SelfdriveD.__new__(SelfdriveD)
  obj.CP = N(carFingerprint="TESLA_MODEL_S_PREAP")
  obj.enabled = True
  obj.events = Events()
  obj.sm = {'modelV2': N(action=N(desiredCurvature=raw)),
            'carControl': N(latActive=True, actuators=N(curvature=command))}
  cs = car_state()
  obj._update_turn_conflict(cs)
  assert obj.events.contains(ET.IMMEDIATE_DISABLE)
  assert obj.events.contains(ET.NO_ENTRY)
  machine = StateMachine()
  machine.state = log.SelfdriveState.OpenpilotState.enabled
  assert machine.update(obj.events) == (False, False)
  obj.events.add(log.OnroadEvent.EventName.pcmEnable)
  assert machine.update(obj.events) == (False, False)


def test_packed_commands_cancel_both_axes_on_direction_conflict(wire_controller):
  ci = wire_controller
  assert wire_tick(ci) == (True, True)
  assert wire_tick(ci, curvature=.03) == (False, False)
  ci.CS.out.leftBlinker = False
  for _ in range(60):
    assert wire_tick(ci) == (False, False)
  ci.CS.cruiseEnabled = ci.CS.enableLongControl = False
  assert wire_tick(ci, enabled=False, lat=False, long=False) == (False, False)
  ci.CS.cruiseEnabled = ci.CS.enableLongControl = True
  assert wire_tick(ci) == (True, True)
