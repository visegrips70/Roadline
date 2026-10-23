"""Veto contradictory low-speed turn requests; never choose a replacement path."""
import math

TURN_SPEED_MAX = 25.0 * 0.44704
TIGHT_TURN_CURVATURE = 0.02


def turn_direction_conflict(cs, curvature):
  """Model curvature is positive right; the indicator supplies intent only.

  A signal does not authorize steering. This rejects a sharp opposite request,
  even when model desire classification or navigation decision data is absent.
  Small road-following corrections and unsignaled road bends are unaffected.
  """
  try:
    speed = float(cs.vEgo)
    curvature = float(curvature)
    if not math.isfinite(speed) or not math.isfinite(curvature):
      return True
    if not 0.0 <= speed <= TURN_SPEED_MAX:
      return False
    left, right = bool(cs.leftBlinker), bool(cs.rightBlinker)
    if left == right or abs(curvature) < TIGHT_TURN_CURVATURE:
      return False
    return (left and curvature > 0.0) or (right and curvature < 0.0)
  except (AttributeError, TypeError, ValueError, OverflowError):
    return True


class TurnDirectionGuard:
  """Hold the fault through signal release until full disengagement is observed."""
  def __init__(self):
    self.blocked = False

  def update(self, cs, curvatures, *, enabled, cruise_enabled):
    if not enabled and not cruise_enabled:
      self.blocked = False
    if any(turn_direction_conflict(cs, curvature) for curvature in curvatures):
      self.blocked = True
    return self.blocked
