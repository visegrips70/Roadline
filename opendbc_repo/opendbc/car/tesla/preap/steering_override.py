"""Pre-AP takeover effort: low-speed allowance and restored legacy HSO."""
import math
from opendbc.car.tesla.values import STEER_THRESHOLD


def takeover_torque_threshold(speed_mps, city_turn=False):
  speed_mph = speed_mps * 2.236936
  if not math.isfinite(speed_mph):
    return STEER_THRESHOLD
  if 0.0 <= speed_mph < 15.0:
    return 5.0
  return 3.0 if city_turn else STEER_THRESHOLD


def hands_on_override(level, torque, threshold=STEER_THRESHOLD):
  if not math.isfinite(torque) or not math.isfinite(threshold):
    return True
  # Restore the older level-3 bypass. Lighter contact does not bypass torque.
  return level >= 3 or abs(torque) > threshold


def steering_takeover_requested(level, torque, speed_mps, blinker_on, steering_pressed=False):
  """Use the same takeover detection in the cruise FSM and actuator controller."""
  if steering_pressed or level >= 3:
    return True
  if not math.isfinite(speed_mps) or not math.isfinite(torque):
    return True
  # Preserve the existing effort thresholds and highway filter. Direct
  # signaled/low-speed takeover must cancel cruise even before that filter trips.
  return ((speed_mps * 2.236936 < 15.0 or blinker_on)
          and hands_on_override(level, torque, takeover_torque_threshold(speed_mps, city_turn=blinker_on)))
