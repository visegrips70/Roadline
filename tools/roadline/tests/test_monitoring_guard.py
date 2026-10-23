"""Prevent this fork from silently restoring the inherited one-hour timeout."""
import pytest

from openpilot.selfdrive.monitoring.helpers import DRIVER_MONITOR_SETTINGS


@pytest.mark.parametrize('device_type', ['tici', 'tizi'])
def test_attention_timeouts_match_nap_baseline(device_type):
  settings = DRIVER_MONITOR_SETTINGS(device_type)
  assert settings._DISTRACTED_TIME == 11.
  assert settings._AWARENESS_TIME == 30.
  assert 0 < settings._DISTRACTED_PROMPT_TIME_TILL_TERMINAL < settings._DISTRACTED_PRE_TIME_TILL_TERMINAL < settings._DISTRACTED_TIME
