import os
from pathlib import Path

import pytest

from openpilot.tools.roadline.navigation_setup import ensure_pairing, read_key


@pytest.fixture
def layout(tmp_path, monkeypatch):
  monkeypatch.delenv("NAP_PHONE_TOKEN", raising=False)
  root, data = tmp_path / "candidate", tmp_path / "data"
  (root / "server/phone_navigation").mkdir(parents=True)
  return root, data


def test_first_boot_creates_private_persistent_key_and_is_idempotent(layout):
  root, data = layout
  saved = ensure_pairing(root, data)
  key = read_key(saved)
  assert len(key) == 64
  assert key == read_key(root / "server/phone_navigation/.pairing-key")
  assert saved.stat().st_mode & 0o777 == 0o600
  assert ensure_pairing(root, data) == saved
  assert read_key(saved) == key


def test_existing_pairing_survives_checkout_change(layout, tmp_path):
  root, data = layout
  old = root / "server/phone_navigation/.pairing-key"
  old.write_text("existing-browser-token-1234567890\n")
  saved = ensure_pairing(root, data)
  new_root = tmp_path / "second-candidate"
  (new_root / "server/phone_navigation").mkdir(parents=True)
  ensure_pairing(new_root, data)
  assert read_key(new_root / "server/phone_navigation/.pairing-key") == read_key(old)
  assert read_key(saved) == read_key(old)


def test_conflicting_keys_are_preserved(layout):
  root, data = layout
  saved = ensure_pairing(root, data)
  before = saved.read_bytes()
  legacy = root / "server/phone_navigation/.pairing-key"
  legacy.write_text("different-browser-token-1234567890")
  with pytest.raises(ValueError, match="disagree"):
    ensure_pairing(root, data)
  assert saved.read_bytes() == before
  assert legacy.read_text() == "different-browser-token-1234567890"


@pytest.mark.parametrize("bad", ["", "short", "x" * 513, "token with spaces is not valid"])
def test_corrupt_key_does_not_silently_rotate(layout, bad):
  root, data = layout
  legacy = root / "server/phone_navigation/.pairing-key"
  legacy.write_text(bad)
  with pytest.raises(ValueError):
    ensure_pairing(root, data)
  assert legacy.read_text() == bad
  assert not (data / "roadline/navigation-pairing-key").exists()


def test_configured_environment_token_and_symlinks(layout, monkeypatch, tmp_path):
  root, data = layout
  monkeypatch.setenv("NAP_PHONE_TOKEN", "configured-browser-token-1234567890")
  saved = ensure_pairing(root, data)
  assert read_key(saved) == os.environ["NAP_PHONE_TOKEN"]
  legacy = root / "server/phone_navigation/.pairing-key"
  legacy.unlink()
  legacy.symlink_to(saved)
  with pytest.raises(ValueError, match="regular file"):
    ensure_pairing(root, data)


def test_missing_submodule_is_reported(tmp_path):
  with pytest.raises(ValueError, match="submodule"):
    ensure_pairing(tmp_path, tmp_path / "data")
