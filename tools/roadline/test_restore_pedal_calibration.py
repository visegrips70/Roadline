import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.roadline import restore_pedal_calibration as restore


SOURCE = "a" * 40
# Synthetic calibration; never a vehicle-specific default.
SAVED = {
  "NAPPedalCanBus": 2, "NAPPedalCalibMin": 1.0,
  "NAPPedalCalibMax": 125.0, "NAPPedalCalibZero": 5.0,
  "NAPPedalCalibFactor": 100.0 / 120.0, "NAPPedalCalibDone": True,
}
BOOLS = set(restore.DISABLED) | {"IsOnroad", "DisableUpdates", "NAPPedalCalibDone"}


class FileParams:
  def __init__(self, path):
    self.path = path
    self.writes = []
    self.ignore_key = None
    self.after_put = None

  def get_param_path(self, key=""):
    return str(self.path / key)

  def get(self, key):
    try:
      value = (self.path / key).read_text()
    except FileNotFoundError:
      return None
    if key in BOOLS:
      return {"0": False, "1": True}.get(value, value)
    if key == "NAPPedalCanBus":
      return int(value)
    return float(value)

  def put(self, key, value):
    self.writes.append((key, value))
    if key != self.ignore_key:
      text = str(int(value)) if type(value) is bool else str(value)
      (self.path / key).write_text(text)
    if self.after_put:
      self.after_put(key, value)


class RestoreTests(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.data = Path(self.tmp.name)
    self.installed = self.data / "openpilot"
    self.installed.mkdir()
    (self.installed / "roadline_release.json").write_text(json.dumps({
      "source_revision": SOURCE, "channel": "staging", "road_ready": False,
    }))
    self.path = self.data / "params/d"
    self.path.mkdir(parents=True)
    self.params = FileParams(self.path)
    for key, value in {
      "IsOnroad": "0", "OpenpilotEnabledToggle": "0", "DisableUpdates": "1",
      "NAPPedalCanBus": "2", "NAPPedalCalibMin": "-3.0",
      "NAPPedalCalibMax": "99.6", "NAPPedalCalibZero": "0.0",
      "NAPPedalCalibFactor": "1.0", "NAPNavigationManeuvers": "1",
      "PrivateToken": "must-not-be-copied",
    }.items():
      (self.path / key).write_text(value)

  def run_restore(self, values=None, source=SOURCE):
    return restore.restore(self.params, SAVED if values is None else values, source,
                           installed=self.installed, data=self.data)

  def test_restore_preserves_exact_snapshot_and_keeps_control_disabled(self):
    before = {path.name: path.read_bytes() for path in self.path.iterdir()}
    backup, expected = self.run_restore()
    for key, value in expected.items():
      self.assertEqual(self.params.get(key), value)
    self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
    meta = json.loads((backup / "snapshot.json").read_text())
    self.assertIn("NAPPedalCalibDone", meta["missing_keys"])
    self.assertNotIn("PrivateToken", {path.name for path in backup.iterdir()})
    for path in backup.iterdir():
      self.assertEqual(path.stat().st_mode & 0o777, 0o600)
      if path.name in before:
        self.assertEqual(path.read_bytes(), before[path.name])
    self.assertEqual(self.params.writes[-1], ("NAPPedalCalibDone", True))
    self.assertFalse(any(key in restore.DISABLED and value for key, value in self.params.writes))

  def test_missing_onroad_or_assistance_state_blocks_before_backup(self):
    for key in ("IsOnroad", "OpenpilotEnabledToggle"):
      with self.subTest(key=key):
        (self.path / key).unlink()
        with self.assertRaises(RuntimeError):
          self.run_restore()
        self.assertEqual(self.params.writes, [])
        self.assertEqual(list(self.data.glob("roadline-pedal-before-restore-*")), [])
        (self.path / key).write_text("0")

  def test_enabled_or_unknown_states_block(self):
    for key in ("IsOnroad", "OpenpilotEnabledToggle", "NAPPedalEnabled"):
      for value in ("1", "unknown"):
        with self.subTest(key=key, value=value):
          (self.path / key).write_text(value)
          with self.assertRaises(RuntimeError):
            self.run_restore()
          self.assertEqual(self.params.writes, [])
          (self.path / key).write_text("0")

  def test_wrong_source_or_params_location_blocks(self):
    with self.assertRaises(RuntimeError):
      self.run_restore(source="b" * 40)
    with patch.object(self.params, "get_param_path", return_value=str(self.data / "elsewhere")):
      with self.assertRaises(RuntimeError):
        self.run_restore()
    self.assertEqual(self.params.writes, [])

  def test_invalid_calibration_is_rejected_before_mutations(self):
    changes = [
      {"NAPPedalCalibDone": False}, {"NAPPedalCalibDone": 1},
      {"NAPPedalCanBus": 1}, {"NAPPedalCanBus": False},
      {"NAPPedalCalibFactor": float("nan")}, {"NAPPedalCalibMax": float("inf")},
      {"NAPPedalCalibZero": True}, {"NAPPedalCalibFactor": 0.0},
      {"NAPPedalCalibFactor": 2.0}, {"NAPPedalCalibMax": 5.0},
      {"NAPPedalCalibMin": 6.0}, {"OtherKey": 42},
    ]
    for change in changes:
      with self.subTest(change=change), self.assertRaises(ValueError):
        self.run_restore(SAVED | change)
    self.assertEqual(self.params.writes, [])

  def test_snapshot_failure_performs_no_param_writes(self):
    with patch.object(restore, "save_file", side_effect=OSError("disk full")):
      with self.assertRaises(OSError):
        self.run_restore()
    self.assertEqual(self.params.writes, [])

  def test_silent_write_failure_invalidates_calibration(self):
    self.params.ignore_key = "NAPPedalCalibFactor"
    with self.assertRaisesRegex(RuntimeError, "Write verification failed"):
      self.run_restore()
    self.assertFalse(self.params.get("NAPPedalCalibDone"))
    self.assertFalse(self.params.get("NAPPedalEnabled"))
    self.assertFalse(self.params.get("OpenpilotEnabledToggle"))

  def test_ignition_transition_aborts_before_completion(self):
    def transition(key, value):
      if key == "NAPPedalCalibMin":
        (self.path / "IsOnroad").write_text("1")
    self.params.after_put = transition
    with self.assertRaisesRegex(RuntimeError, "IsOnroad"):
      self.run_restore()
    self.assertFalse(self.params.get("NAPPedalCalibDone"))
    self.assertNotIn(("NAPPedalCalibDone", True), self.params.writes)

  def test_interruption_invalidates_calibration(self):
    def interrupt(key, value):
      if key == "NAPPedalCalibMin":
        raise KeyboardInterrupt()
    self.params.after_put = interrupt
    with self.assertRaises(KeyboardInterrupt):
      self.run_restore()
    self.assertFalse(self.params.get("NAPPedalCalibDone"))
    self.assertFalse(self.params.get("OpenpilotEnabledToggle"))

  def test_concurrent_change_is_detected_and_invalidated(self):
    def change(key, value):
      if key == "NAPPedalCalibDone" and value:
        (self.path / "NAPPedalCalibFactor").write_text("1.0")
    self.params.after_put = change
    with self.assertRaisesRegex(RuntimeError, "Settings changed"):
      self.run_restore()
    self.assertFalse(self.params.get("NAPPedalCalibDone"))

  def test_repeat_restore_does_not_overwrite_previous_snapshot(self):
    first, _ = self.run_restore()
    second, _ = self.run_restore()
    self.assertNotEqual(first, second)
    self.assertEqual((first / "NAPPedalCalibMin").read_text(), "-3.0")
    self.assertEqual((second / "NAPPedalCalibMin").read_text(), str(SAVED["NAPPedalCalibMin"]))


if __name__ == "__main__":
  unittest.main()
