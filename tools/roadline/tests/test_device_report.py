import json
from unittest.mock import patch

from tools.roadline.device_report import collect, read_text


def make_device(tmp_path):
  for name, value in {
    "AGNOS": "", "VERSION": "17.2\n",
    "sys/firmware/devicetree/base/model": "comma tizi\0",
    "data/params/d/IsOnroad": "0", "data/params/d/NAPPedalEnabled": "1",
    "data/params/d/NAPPedalCalibDone": "1", "data/params/d/NAPPedalCanBus": "2",
    "data/params/d/GitToken": "do-not-report", "data/params/d/CarVin": "do-not-report",
  }.items():
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
  return tmp_path


def report(root):
  with patch("tools.roadline.device_report.git_value", return_value="test-revision"):
    return collect(root, root / "data/openpilot")


def test_report_is_allowlisted_and_does_not_change_files(tmp_path):
  root = make_device(tmp_path)
  legacy = root / "data/nap_params.json"
  legacy.write_text(json.dumps({"pedal_calib_factor": 2.5, "password": "do-not-report", "radar_offset": float('nan')}))
  before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
  result = report(root)
  assert result["blockers"] == []
  assert result["road_ready"] is False
  assert "do-not-report" not in json.dumps(result)
  json.dumps(result, allow_nan=False)
  assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_unknown_or_onroad_state_blocks(tmp_path):
  root = make_device(tmp_path)
  state = root / "data/params/d/IsOnroad"
  for value in ("1", "unknown"):
    state.write_text(value)
    assert any("Off-road" in b for b in report(root)["blockers"])
  state.unlink()
  assert any("Off-road" in b for b in report(root)["blockers"])


def test_wrong_hardware_and_os_block(tmp_path):
  root = make_device(tmp_path)
  (root / "sys/firmware/devicetree/base/model").write_text("comma tici")
  (root / "VERSION").write_text("16.0")
  assert len(report(root)["blockers"]) == 2


def test_missing_pedal_configuration_and_ibooster_block(tmp_path):
  root = make_device(tmp_path)
  (root / "data/params/d/NAPPedalCalibDone").unlink()
  (root / "data/params/d/NAPPedalCanBus").write_text("1")
  (root / "data/params/d/NAPiBoosterEnabled").write_text("1")
  assert len(report(root)["blockers"]) == 3


def test_missing_and_oversized_files_are_unknown(tmp_path):
  assert read_text(tmp_path / "missing") is None
  (tmp_path / "large").write_text("x" * 4097)
  assert read_text(tmp_path / "large") is None
