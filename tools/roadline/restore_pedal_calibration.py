#!/usr/bin/env python3
"""Restore a known same-pedal calibration with assistance and pedal control off.

Reads only an allowlisted calibration object from stdin. This tool never opens
CAN, runs the calibrator, flashes firmware, restarts a service, or enables control.
"""

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile


CALIBRATION_KEYS = (
  "NAPPedalCanBus", "NAPPedalCalibMin", "NAPPedalCalibMax",
  "NAPPedalCalibZero", "NAPPedalCalibFactor", "NAPPedalCalibDone",
)
DISABLED = (
  "OpenpilotEnabledToggle", "NAPPedalEnabled", "NAPRadarEnabled",
  "NAPiBoosterEnabled", "NAPNavigationManeuvers", "NAPMapDrivingAssist",
)


def validate_calibration(values):
  if not isinstance(values, dict) or set(values) != set(CALIBRATION_KEYS):
    raise ValueError("Supply exactly the six saved calibration keys.")
  if values["NAPPedalCalibDone"] is not True:
    raise ValueError("Backup must record a completed calibration.")
  if type(values["NAPPedalCanBus"]) is not int or values["NAPPedalCanBus"] not in (0, 2):
    raise ValueError("Saved pedal bus must be 0 or 2.")
  result = dict(values)
  for key in CALIBRATION_KEYS[1:5]:
    if type(values[key]) not in (float, int) or not math.isfinite(values[key]):
      raise ValueError("Calibration values must be finite numbers.")
    result[key] = float(values[key])
  low, high, zero, factor = (result[key] for key in CALIBRATION_KEYS[1:5])
  if not low <= zero < high or factor <= 0:
    raise ValueError("Calibration limits or factor are invalid.")
  if not math.isclose(factor, 100.0 / (high - zero), rel_tol=1e-6):
    raise ValueError("Saved factor does not match the saved range.")
  return result


def require_disabled_offroad(params):
  if params.get("IsOnroad") is not False:
    raise RuntimeError("IsOnroad must be explicitly 0; keep the vehicle off.")
  if params.get("OpenpilotEnabledToggle") is not False:
    raise RuntimeError("Assistance must already be disabled.")
  if params.get("NAPPedalEnabled") not in (None, False):
    raise RuntimeError("Pedal control must already be disabled.")


def save_file(path, data):
  fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
  with os.fdopen(fd, "wb") as handle:
    handle.write(data)
    handle.flush()
    os.fsync(handle.fileno())


def restore(params, values, expected_source, *, installed=Path("/data/openpilot"), data=Path("/data")):
  values = validate_calibration(values)
  if not re.fullmatch(r"[0-9a-f]{40}", expected_source):
    raise ValueError("Expected source must be a complete commit SHA.")
  manifest = json.loads((installed / "roadline_release.json").read_text())
  if manifest.get("source_revision") != expected_source:
    raise RuntimeError("Installed source revision does not match; nothing restored.")
  if manifest.get("channel") != "staging" or manifest.get("road_ready") is not False:
    raise RuntimeError("This helper is for the Roadline staging installation.")
  if Path(params.get_param_path()).resolve() != (data / "params/d").resolve():
    raise RuntimeError("Unexpected Params location.")
  require_disabled_offroad(params)

  # Save exact original bytes (including absent-key information), before writes.
  backup = Path(tempfile.mkdtemp(prefix="roadline-pedal-before-restore-", dir=data))
  missing = []
  keys = tuple(dict.fromkeys((*CALIBRATION_KEYS, *DISABLED, "DisableUpdates")))
  for key in keys:
    try:
      original = Path(params.get_param_path(key)).read_bytes()
    except FileNotFoundError:
      missing.append(key)
    else:
      save_file(backup / key, original)
  save_file(backup / "snapshot.json", (json.dumps({
    "source_revision": expected_source, "missing_keys": missing,
    "scope": "Selected settings only; restored calibration is not a live hardware test.",
  }, indent=2) + "\n").encode())
  for directory in (backup, data):
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(fd)
    finally:
      os.close(fd)

  def put_checked(key, value):
    require_disabled_offroad(params)
    params.put(key, value)
    # Params.put's binding does not expose the C++ return code. Read it back.
    if params.get(key) != value:
      raise RuntimeError(f"Write verification failed: {key}")

  expected = {key: False for key in DISABLED}
  expected["DisableUpdates"] = True
  expected.update(values)
  try:
    put_checked("NAPPedalEnabled", False)
    put_checked("NAPPedalCalibDone", False)
    for key in DISABLED:
      put_checked(key, False)
    put_checked("DisableUpdates", True)
    for key in CALIBRATION_KEYS[:-1]:
      put_checked(key, values[key])
    # Completion is restored only after all four values and bus are verified.
    put_checked("NAPPedalCalibDone", True)
    require_disabled_offroad(params)
    if any(params.get(key) != value for key, value in expected.items()):
      raise RuntimeError("Settings changed during restore; verification failed.")
  except BaseException:
    for key in ("NAPPedalCalibDone", "NAPPedalEnabled", "OpenpilotEnabledToggle"):
      try:
        params.put(key, False)
      except Exception:
        pass
    print(f"Restore interrupted. Original settings snapshot: {backup}", file=sys.stderr)
    raise
  return backup, expected


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--expected-source", required=True)
  parser.add_argument("--unchanged-pedal", action="store_true",
                      help="Confirm this is the same pedal hardware/firmware as the backup.")
  args = parser.parse_args()
  if not args.unchanged_pedal:
    parser.error("Confirm the pedal hardware/firmware is unchanged before restoring its calibration.")
  if os.environ.get("OPENPILOT_PREFIX", "d") != "d":
    parser.error("Custom Params prefixes are unsupported.")
  from openpilot.common.params import Params

  try:
    values = json.loads(sys.stdin.read(4097))
    backup, expected = restore(Params(), values, args.expected_source)
  except (OSError, ValueError, RuntimeError) as exc:
    print(f"STOP: {exc}", file=sys.stderr)
    return 1
  print("SAVED PEDAL CALIBRATION RESTORED AND READ BACK")
  print(f"Previous settings snapshot: {backup}")
  for key, value in expected.items():
    print(f"{key}: {int(value) if type(value) is bool else value}")
  print("Assistance and pedal control remain disabled. Live hardware checks remain outstanding.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
