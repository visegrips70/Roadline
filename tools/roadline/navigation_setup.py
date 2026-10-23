#!/usr/bin/env python3
"""Keep the dashboard pairing credential across Roadline checkout changes."""
import argparse
import os
from pathlib import Path
import secrets
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def read_key(path):
  if path.is_symlink():
    raise ValueError("Navigation key must be a regular file")
  try:
    with path.open() as stream:
      key = stream.read(513).strip()
  except FileNotFoundError:
    return None
  if not 16 <= len(key) <= 512 or not key.isascii() or any(c.isspace() for c in key):
    raise ValueError("Existing navigation key is invalid; preserve it for recovery")
  return key


def create_if_missing(path, key):
  """Publish a complete, private file without overwriting a concurrent writer."""
  path.parent.mkdir(parents=True, exist_ok=True)
  fd, name = tempfile.mkstemp(prefix=".navigation-", dir=path.parent)
  try:
    with os.fdopen(fd, "w") as stream:
      stream.write(key + "\n")
      stream.flush()
      os.fsync(stream.fileno())
    try:
      os.link(name, path)
    except FileExistsError:
      pass
  finally:
    os.unlink(name)
  return read_key(path)


def ensure_pairing(root=ROOT, data=Path("/data")):
  legacy = root / "server/phone_navigation/.pairing-key"
  persistent = data / "roadline/navigation-pairing-key"
  if not legacy.parent.is_dir():
    raise ValueError("Navigation server submodule is missing")
  old = read_key(legacy)
  saved = read_key(persistent)
  configured = os.environ.get("NAP_PHONE_TOKEN", "").strip()
  if configured and (not 16 <= len(configured) <= 512 or not configured.isascii()
                     or any(c.isspace() for c in configured)):
    raise ValueError("Configured navigation token is invalid")
  candidates = [value for value in (old, saved, configured) if value is not None and value != ""]
  if len(set(candidates)) > 1:
    raise ValueError("Navigation keys disagree; existing keys were not replaced")
  key = saved or old or configured or secrets.token_hex(32)
  key = create_if_missing(persistent, key)
  if create_if_missing(legacy, key) != key:
    raise ValueError("Navigation key changed during setup; existing key was preserved")
  os.chmod(persistent, 0o600)
  os.chmod(legacy, 0o600)
  return persistent


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--root", type=Path, default=ROOT)
  parser.add_argument("--data", type=Path, default=Path("/data"))
  args = parser.parse_args()
  try:
    ensure_pairing(args.root, args.data)
  except (OSError, ValueError) as exc:
    print(f"Navigation pairing setup failed: {exc}")
    return 1
  print("Navigation pairing is configured. Open the comma's port 7070 /phone-nav page.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
