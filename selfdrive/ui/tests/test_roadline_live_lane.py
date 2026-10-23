"""Exercise actual HUD preference callbacks without a display."""
from types import SimpleNamespace as N
from unittest.mock import Mock

import pytest
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad import hud_renderer as hud


@pytest.fixture
def controls(mocker):
  params = Params()
  params.put("NAPLaneCentering", True)
  params.put("RoadlineLaneOffsetCm", 0)
  mocker.patch.object(hud, "_params", params)
  mocker.patch.object(hud, "ui_state", N(CP=N(carFingerprint="TESLA_MODEL_S_PREAP")))
  clock = mocker.patch.object(hud.time, "monotonic", return_value=100.)
  obj = hud.HudRenderer.__new__(hud.HudRenderer)
  obj._last_lane_change = -float("inf")
  obj.lane_offset_cm = 0
  return obj, params, clock


def test_left_right_center_and_debounce(controls):
  obj, params, clock = controls
  obj._set_lane_position(-1)
  assert params.get("RoadlineLaneOffsetCm") == -1
  obj._set_lane_position(-1)
  assert params.get("RoadlineLaneOffsetCm") == -1
  clock.return_value += .3
  obj._set_lane_position(1)
  assert params.get("RoadlineLaneOffsetCm") == 0
  params.put("RoadlineLaneOffsetCm", 15)
  clock.return_value += .3
  obj._set_lane_position()
  assert params.get("RoadlineLaneOffsetCm") == obj.lane_offset_cm == 0


@pytest.mark.parametrize("initial,change,expected", [(30, 1, 30), (-30, -1, -30), (-2, 1, -1)])
def test_bounds_and_latest_persistent_value(controls, initial, change, expected):
  obj, params, _ = controls
  params.put("RoadlineLaneOffsetCm", initial)
  obj._set_lane_position(change)
  assert params.get("RoadlineLaneOffsetCm") == obj.lane_offset_cm == expected


def test_disabled_centering_or_wrong_vehicle_cannot_edit(controls, mocker):
  obj, params, clock = controls
  params.put("NAPLaneCentering", False)
  obj._set_lane_position(1)
  assert params.get("RoadlineLaneOffsetCm") == 0
  params.put("NAPLaneCentering", True)
  mocker.patch.object(hud, "ui_state", N(CP=N(carFingerprint="OTHER")))
  clock.return_value += 1.
  obj._set_lane_position(1)
  assert params.get("RoadlineLaneOffsetCm") == 0


def test_failed_write_does_not_claim_saved_value(controls, mocker):
  obj, params, _ = controls
  failed = Mock(wraps=params)
  failed.put.side_effect = OSError("read only")
  mocker.patch.object(hud, "_params", failed)
  obj._set_lane_position(1)
  assert obj.lane_offset_cm == 0
  assert params.get("RoadlineLaneOffsetCm") == 0
