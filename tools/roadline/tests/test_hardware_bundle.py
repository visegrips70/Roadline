import hashlib
import json
import struct

import pytest

from tools.roadline.hardware_bundle import APP, REQUIRED, collect, read_asset


def make_bundle(root):
  for relative in REQUIRED:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fixture asset")
  payload = struct.pack("<I", 1032) + bytes(1020) + b"VERS" + struct.pack("<I", 2)
  (root / APP).write_bytes(payload + b"s" * 128)
  return root


def test_complete_bundle_is_inventory_only_and_does_not_change_files(tmp_path):
  root = make_bundle(tmp_path)
  params = root / "params"
  params.mkdir()
  (params / "PandaSignatures").write_bytes(b"s" * 128)
  (params / "GitToken").write_text("never-report-this")
  before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
  result = collect(root, params)
  assert result["bundle_files_complete"] and result["blockers"] == []
  assert result["assets"][APP]["sha256"] == hashlib.sha256(before[root / APP]).hexdigest()
  assert result["last_reported_panda"]["matches_bundle"] is True
  assert not result["last_reported_panda"]["live_health_verified"]
  assert not result["road_ready"]
  assert "never-report-this" not in json.dumps(result)
  assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("relative", REQUIRED)
def test_each_required_asset_is_checked(tmp_path, relative):
  root = make_bundle(tmp_path)
  (root / relative).unlink()
  result = collect(root)
  assert not result["bundle_files_complete"]
  assert any(relative in blocker for blocker in result["blockers"])


@pytest.mark.parametrize("content", [b"", b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\n", b"bad image" * 32])
def test_invalid_firmware_blocks_bundle(tmp_path, content):
  root = make_bundle(tmp_path)
  (root / APP).write_bytes(content)
  result = collect(root)
  assert result["blockers"] and result["panda_signature_hex"] is None


@pytest.mark.parametrize("signature,match", [(None, None), (b"s" * 127, None), (b"s" * 129, None), (b"x" * 128, False)])
def test_unavailable_or_mismatched_cached_signature_is_not_a_pass(tmp_path, signature, match):
  root = make_bundle(tmp_path)
  params = root / "params"
  params.mkdir()
  if signature is not None:
    (params / "PandaSignatures").write_bytes(signature)
  result = collect(root, params)
  assert result["last_reported_panda"]["matches_bundle"] is match
  assert not result["road_ready"]


def test_asset_read_has_a_size_limit(tmp_path):
  path = tmp_path / "large"
  path.write_bytes(b"x" * 17)
  assert read_asset(path, limit=16) is None
