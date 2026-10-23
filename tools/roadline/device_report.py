#!/usr/bin/env python3
"""Read-only Comma compatibility report. Never imports car code or opens CAN."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

EXPECTED_AGNOS = "17.2"
PARAM_KEYS = (
  "IsOnroad", "OpenpilotEnabledToggle", "ExperimentalMode", "LongitudinalPersonality",
  "NAPPedalEnabled", "NAPPedalCanBus", "NAPPedalProfile", "NAPPedalCalibDone",
  "NAPPedalCalibMin", "NAPPedalCalibMax", "NAPPedalCalibZero", "NAPPedalCalibFactor",
  "NAPRadarEnabled", "NAPRadarBehindNosecone", "NAPRadarOffset", "NAPForcePreAP",
  "NAPiBoosterEnabled", "NAPBrakeThrottleResume", "NAPAdaptiveAccel", "NAPFollowDistance",
  "NAPLaneCentering", "NAPLaneCenteringStrength", "RoadlineLaneOffsetCm",
  "NAPCityTurns", "NAPWideLowSpeedTurns", "NAPLowSpeedSteeringRate",
  "NAPNavigationManeuvers", "NAPMapDrivingAssist", "NAPCornerAssist", "NapTapLaneChange",
)
LEGACY_KEYS = (
  "use_pedal", "pedal_calibrated", "pedal_can_zero", "pedal_profile", "pedal_min",
  "pedal_max", "pedal_calib_min", "pedal_calib_max", "pedal_calib_zero",
  "pedal_calib_factor", "radar_enabled", "radar_behind_nosecone", "radar_offset",
)


def read_text(path, limit=4096):
  try:
    with path.open("rb") as handle:
      data = handle.read(limit + 1)
    if len(data) > limit:
      return None
    return data.decode("utf-8").strip().rstrip("\0")
  except (OSError, UnicodeError):
    return None


def read_scalar(path):
  text = read_text(path, 256)
  if text is None:
    return None
  try:
    value = json.loads(text)
  except ValueError:
    return text
  if isinstance(value, float) and not math.isfinite(value):
    return None
  return value if isinstance(value, (bool, int, float, str)) else None


def git_value(path, *args):
  try:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                            text=True, timeout=5, check=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    return result.stdout.strip()
  except (OSError, subprocess.SubprocessError):
    return None


def collect(root=Path("/"), installed=Path("/data/openpilot")):
  data = root / "data"
  params_dir = data / "params/d"
  settings = {key: read_scalar(params_dir / key) for key in PARAM_KEYS}
  try:
    legacy_raw = json.loads(read_text(data / "nap_params.json", 65536) or "{}")
    legacy = {key: legacy_raw[key] for key in LEGACY_KEYS
              if isinstance(legacy_raw, dict) and key in legacy_raw
              and isinstance(legacy_raw[key], (str, int, float, bool))
              and not (isinstance(legacy_raw[key], float) and not math.isfinite(legacy_raw[key]))}
  except ValueError:
    legacy = {}
  device_model = read_text(root / "sys/firmware/devicetree/base/model")
  agnos = read_text(root / "VERSION")
  blockers = []
  if not device_model or not re.search(r"\b(?:tizi|3X)\b", device_model, re.IGNORECASE):
    blockers.append("Comma 3X hardware identity has not been established.")
  if not (root / "AGNOS").is_file() or agnos != EXPECTED_AGNOS:
    blockers.append("Candidate requires AGNOS 17.2; review OS compatibility before activation.")
  if settings["IsOnroad"] != 0:
    blockers.append("Off-road state is not confirmed. Do not stage or activate an update.")
  if settings["NAPiBoosterEnabled"] in (True, 1):
    blockers.append("iBooster is configured; this candidate has no validated iBooster integration.")
  if settings["NAPPedalEnabled"] in (True, 1):
    if settings["NAPPedalCalibDone"] not in (True, 1):
      blockers.append("Pedal is enabled but calibration completion is not confirmed.")
    if settings["NAPPedalCanBus"] not in (0, 2):
      blockers.append("Pedal CAN bus is missing or unexpected.")
  try:
    free_bytes = shutil.disk_usage(data).free
  except OSError:
    free_bytes = None
  commit = git_value(installed, "rev-parse", "HEAD")
  if not commit:
    blockers.append("Installed NAP revision could not be read.")
  return {
    "report_version": 1,
    "scope": "Read-only inventory; no installation, firmware flash, CAN access, or driving approval.",
    "device": {"model": device_model, "agnos": agnos, "architecture": platform.machine(),
               "report_python": platform.python_version(), "data_free_bytes": free_bytes},
    "installed_software": {"commit": commit, "branch": git_value(installed, "branch", "--show-current")},
    "settings": settings,
    "legacy_nap_settings": legacy,
    "calibration_files_present": {key: (params_dir / key).is_file()
                                  for key in ("CalibrationParams", "LiveParameters", "LiveTorqueParameters")},
    "blockers": blockers,
    "next_gate": "Review this report, preserve rollback/settings, then build on the disconnected Comma 3X.",
    "road_ready": False,
  }


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--installed", type=Path, default=Path("/data/openpilot"))
  args = parser.parse_args()
  report = collect(installed=args.installed)
  print(json.dumps(report, indent=2, allow_nan=False))
  return 2 if report["blockers"] else 0


if __name__ == "__main__":
  sys.exit(main())
