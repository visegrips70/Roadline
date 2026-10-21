"""Exercise real settings callbacks and typed Params without a display server."""

from types import SimpleNamespace as N

from openpilot.common.params import Params
from openpilot.selfdrive.ui.layouts.settings import nap


def layout(text='0'):
  obj = nap.NAPLayout.__new__(nap.NAPLayout)
  obj._params = Params()
  obj._lane_position_keyboard = N(text=text)
  return obj


def test_old_preference_is_read_without_rewriting_calibration():
  obj = layout()
  obj._params.put('NAPLaneCenterOffset', 2)
  assert obj._lane_position_cm() == 23
  assert obj._params.get('RoadlineLaneOffsetCm') is None
  obj._params.put('RoadlineLaneOffsetCm', 0)
  assert obj._lane_position_label() == 'Center'


def test_save_cm_uses_typed_params(mocker):
  obj = layout('2')
  mocker.patch.object(nap, 'ui_state', N(is_offroad=True))
  obj._on_lane_position_submit(nap.DialogResult.CONFIRM)
  assert obj._params.get('RoadlineLaneOffsetCm') == 2
  assert obj._lane_position_label() == 'Right 2 cm'


def test_onroad_transition_and_cancel_do_not_write(mocker):
  obj = layout('10')
  obj._params.put('RoadlineLaneOffsetCm', -2)
  mocker.patch.object(nap, 'ui_state', N(is_offroad=False))
  obj._on_lane_position_submit(nap.DialogResult.CONFIRM)
  obj._on_centering_strength(2)
  assert obj._params.get('RoadlineLaneOffsetCm') == -2
  assert obj._params.get('NAPLaneCenteringStrength', return_default=True) == 1
  mocker.patch.object(nap, 'ui_state', N(is_offroad=True))
  obj._on_lane_position_submit(nap.DialogResult.CANCEL)
  assert obj._params.get('RoadlineLaneOffsetCm') == -2


def test_invalid_entry_leaves_last_value_and_explains_error(mocker):
  obj = layout('31')
  obj._params.put('RoadlineLaneOffsetCm', 3)
  mocker.patch.object(nap, 'ui_state', N(is_offroad=True))
  app = mocker.patch.object(nap, 'gui_app')
  mocker.patch.object(nap, 'ConfirmDialog')
  obj._on_lane_position_submit(nap.DialogResult.CONFIRM)
  app.push_widget.assert_called_once()
  assert obj._params.get('RoadlineLaneOffsetCm') == 3
