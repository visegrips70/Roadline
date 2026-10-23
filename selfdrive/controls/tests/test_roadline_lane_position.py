import math
import random
import pytest
from openpilot.common.lane_position import offset_label, parse_offset_cm, resolve_offset_cm
from openpilot.selfdrive.controls.lib.lane_centering import LaneCenteringAssist
from openpilot.selfdrive.controls.tests.test_lane_centering import curve, model, step


class TestLanePreference:
  def test_persistence_migration_and_explicit_center(self):
    for old, cm in ((-3, -30), (-2, -23), (-1, -15), (0, 0), (1, 15), (2, 23), (3, 30)):
      assert resolve_offset_cm(None, old) == cm
      assert resolve_offset_cm(0, old) == 0
    assert resolve_offset_cm(None, 99) == 0

  def test_input_validation(self):
    for value in (True, False, 1.5, math.inf, math.nan, [], {}, '', '1.0', 'nan', '31', '-31', '--1', b'\xff'):
      with pytest.raises((ValueError, UnicodeError)):
        parse_offset_cm(value)
      assert resolve_offset_cm(value, 3) == 0
    assert parse_offset_cm(' +2 ') == 2
    assert parse_offset_cm(b'-2') == -2
    assert offset_label(-2) == 'Left 2 cm'
    assert offset_label(2) == 'Right 2 cm'
    assert offset_label(0) == 'Center'

  def test_preference_sign_and_fine_steps(self):
    outputs = []
    for cm in range(-10, 11):
      a = LaneCenteringAssist()
      for _ in range(300):
        output = step(a, model(0.2), offset_cm=cm)
      outputs.append(output)
    assert all((b > a for a, b in zip(outputs, outputs[1:], strict=False)))
    for cm in (-15, 15):
      a = LaneCenteringAssist()
      for _ in range(300):
        output = step(a, model(0), offset_cm=cm)
      assert output * cm > 0

  def test_narrow_lane_bounds_target(self):
    md = model(0)
    md.laneLines[1], md.laneLines[2] = (curve(-1.3), curve(1.3))
    for sign in (-1, 1):
      a, b = (LaneCenteringAssist(), LaneCenteringAssist())
      assert a._target(md, 15, 1, 0, sign * 30) == pytest.approx(b._target(md, 15, 1, 0, sign * 5))

  def test_limit_and_override_properties(self):
    rng = random.Random(20261021)
    for _ in range(120):
      a = LaneCenteringAssist()
      speed = rng.uniform(11.2, 25.0)
      cm = rng.randint(-30, 30)
      md = model(rng.uniform(-0.25, 0.25))
      prev = 0.0
      for _ in range(120):
        out = a.update(md, speed, 0, enabled=True, active=True, healthy=True, overriding=False, offset_cm=cm, strength=3)
        accel = out * speed**2
        assert math.isfinite(out)
        assert abs(accel) <= a.MAX_ACCEL + 1e-09
        assert abs(accel - prev) <= a.MAX_JERK * 0.01 + 1e-09
        prev = accel
      assert a.update(md, speed, 0, enabled=True, active=True, healthy=True, overriding=True, offset_cm=cm) == 0

  def test_new_key_does_not_relax_curve_or_confidence_gates(self):
    for cm in (-30, 0, 30):
      for speed, curvature in ((5, 0), (35, 0), (15, 0.005)):
        assert LaneCenteringAssist().update(model(), speed, curvature, enabled=True, active=True, healthy=True, overriding=False, offset_cm=cm) == 0
      md = model()
      md.laneLineProbs[2] = 0.5
      assert step(LaneCenteringAssist(), md, offset_cm=cm) == 0


def test_live_preference_reversal_and_center_preserve_output_limits():
  assist = LaneCenteringAssist()
  md = model(0.)
  speed = 15.
  previous = 0.
  # Exercise full-range preference changes during continuous active control.
  # The production output slew limit, not the UI tap cadence, bounds actuation.
  for preference in (-30, 30, 0, -10, 10, 0):
    for _ in range(400):
      curvature = assist.update(md, speed, 0., enabled=True, active=True,
                                healthy=True, overriding=False, strength=3,
                                offset_cm=preference, dt=.01)
      accel = curvature * speed ** 2
      assert abs(accel) <= assist.MAX_ACCEL + 1e-9
      assert abs(accel - previous) <= assist.MAX_JERK * .01 + 1e-9
      previous = accel
  assert abs(previous) < 1e-9
