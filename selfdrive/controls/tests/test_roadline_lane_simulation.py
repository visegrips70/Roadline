"""Idealized straight-road bicycle simulation, NOT a real driving-model replay."""

from collections import deque
import math
from openpilot.selfdrive.controls.lib.lane_centering import LaneCenteringAssist
from openpilot.selfdrive.controls.tests.test_lane_centering import model


class TestLaneSimulation:
  def test_straight_road_convergence_with_delay(self):
    for speed in (12.0, 20.0, 28.0):
      for delay in (0.1, 0.3, 0.5):
        for cm in (-10, 0, 10):
          assist = LaneCenteringAssist()
          commands = deque([0.0] * round(delay / 0.01))
          lateral, yaw, applied = (-0.25, 0.0, 0.0)
          maximum = abs(lateral)
          for _ in range(4000):
            md = model(0)
            for index, edge in ((1, -1.8), (2, 1.8)):
              line = md.laneLines[index]
              line.y = [edge - lateral - math.tan(yaw) * x for x in line.x]
            commands.append(assist.update(md, speed, 0, enabled=True, active=True, healthy=True, overriding=False, offset_cm=cm))
            applied += 0.01 / (0.1 + 0.01) * (commands.popleft() - applied)
            yaw += speed * applied * 0.01
            lateral += speed * math.sin(yaw) * 0.01
            maximum = max(maximum, abs(lateral))
          assert abs(lateral - cm / 100.0) < 0.045
          assert maximum < 0.4
