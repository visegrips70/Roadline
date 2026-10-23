#!/usr/bin/env python3
"""Read-only prebuilt-download gate. Never installs, runs the stack, or publishes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct

SHA = re.compile(r"^[0-9a-f]{40}$")
LFS = b"version https://git-lfs.github.com/spec/"
MEDIA = {
  "logo.png": "3fee5eb04a58371404db18a6a33ff936d2846d04a8d125b1b7189aac92749dd7",
  "startup.mp4": "eee01080bd398f53688b08bed490b55addfdfb22f2a9d03a39b742a83b976265",
  "startup_still.png": "23f593fe4fa7a9d81effbdcf3449af9454c91ad20fd69359317c8ed4bb894425",
}
REQUIRED = (
  "LICENSE", "PROVENANCE.md", "launch_openpilot.sh", "launch_chffrplus.sh", "launch_env.sh",
  "system/manager/manager.py", "selfdrive/ui/ui.py", "system/ui/roadline_spinner.py",
  "system/ui/lib/roadline_video.py", "selfdrive/assets/roadline/manifest.json",
  "selfdrive/ui/layouts/home.py", "selfdrive/ui/layouts/settings/nap.py",
  "selfdrive/monitoring/dmonitoringd.py", "selfdrive/controls/radard.py",
  "opendbc_repo/opendbc/car/tesla/preap/interface.py",
  "opendbc_repo/opendbc/safety/modes/tesla_preap.h",
  "opendbc_repo/opendbc/dbc/tesla_radar_bosch_generated.dbc",
  "server/server_v21.py", "server/nap_sentry.py",
  "selfdrive/modeld/models/driving_vision_metadata.pkl",
  "selfdrive/modeld/models/driving_policy_metadata.pkl",
  "selfdrive/modeld/models/dmonitoring_model_metadata.pkl",
  "panda/board/obj/panda_h7.bin.signed", "panda/board/obj/bootstub.panda_h7.bin",
)
BINARIES = ("system/camerad/camerad", "system/loggerd/loggerd", "system/loggerd/encoderd")
CHECKS = ("desktop_ci", "comma3x_build", "bench_boot", "splash_playback", "settings_backup_restore", "rollback")
OLD_ASSETS = (
  "system/ui/phillyfork_spinner.py", "selfdrive/assets/images/phillyfork_offroad_road.png",
  "selfdrive/assets/images/phillyfork_road.png", "selfdrive/assets/images/spinner_comma.png",
)
# These are obvious private-file checks, not a comprehensive secret scanner.
PRIVATE_NAMES = {"id_rsa", "id_ed25519", ".pairing-key", "nap_params.json", "credentials.json", "token.json"}


def digest(path):
  h = hashlib.sha256()
  with path.open("rb") as f:
    for block in iter(lambda: f.read(1024 * 1024), b""):
      h.update(block)
  return h.hexdigest()


def safe_file(root, relative):
  path = root / relative
  try:
    return path.is_file() and path.resolve().is_relative_to(root)
  except (OSError, RuntimeError):
    return False


def elf_is_aarch64(header):
  return (len(header) >= 20 and header[:6] == b"\x7fELF\x02\x01"
          and struct.unpack_from("<H", header, 18)[0] == 183)


def model_errors(root):
  errors = []
  for name in ("driving_vision", "driving_policy", "dmonitoring_model"):
    rel = f"selfdrive/modeld/models/{name}_tinygrad.pkl"
    manifest = rel + ".chunkmanifest"
    if safe_file(root, manifest):
      try:
        count = int((root / manifest).read_text())
        if not 1 <= count <= 99:
          raise ValueError("invalid chunk count")
        chunks = [f"{rel}.chunk{i:02d}of{count:02d}" for i in range(1, count + 1)]
        if not all(safe_file(root, c) for c in chunks) or sum((root / c).stat().st_size for c in chunks) == 0:
          errors.append(f"Compiled model chunks missing or empty: {name}")
      except (ValueError, OSError):
        errors.append(f"Invalid compiled model chunk manifest: {name}")
    elif not safe_file(root, rel) or (root / rel).stat().st_size == 0:
      errors.append(f"Compiled QCOM model missing: {name}")
  for size in ("1928x1208", "1344x760"):
    for prefix in ("warp", "dm_warp"):
      rel = f"selfdrive/modeld/models/{prefix}_{size}_tinygrad.pkl"
      if not safe_file(root, rel) or (root / rel).stat().st_size == 0:
        errors.append(f"Compiled camera warp missing: {rel}")
  return errors


def evidence_errors(evidence, revision, payload_sha256):
  errors = []
  if not isinstance(evidence, dict):
    return ["Evidence must be a JSON object."]
  if evidence.get("source_revision") != revision:
    errors.append("Evidence source revision does not match the release source.")
  if evidence.get("payload_sha256") != payload_sha256:
    errors.append("Evidence payload hash does not match the exact prepared tree.")
  if evidence.get("target") != {"model": "comma tizi", "architecture": "aarch64", "agnos": "17.2"}:
    errors.append("Evidence target must be comma 3X / aarch64 / AGNOS 17.2.")
  checks = evidence.get("checks")
  if not isinstance(checks, dict):
    checks = {}
  for name in CHECKS:
    item = checks.get(name)
    reference = item.get("reference") if isinstance(item, dict) else None
    if (not isinstance(item, dict) or item.get("status") != "pass"
        or not isinstance(reference, str) or not reference.strip()):
      errors.append(f"Missing passing evidence with a reference: {name}")
  return errors


def inspect_tree(root, evidence=None):
  root = Path(root).resolve()
  issues, files = [], []
  payload = hashlib.sha256()
  if not root.is_dir():
    return {"schema_version": 1, "status": "BLOCKED", "eligible_for_publication_review": False,
            "road_ready": False, "blockers": ["Release directory does not exist."]}

  def walk_error(exc):
    issues.append(f"Cannot enumerate release directory ({type(exc).__name__}).")

  for parent, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
    dirs[:] = sorted(d for d in dirs if d != ".git")
    entries = sorted(names + [d for d in dirs if (Path(parent) / d).is_symlink()])
    for name in entries:
      path = Path(parent) / name
      rel = path.relative_to(root).as_posix()
      try:
        if path.is_symlink():
          target = os.readlink(path)
          try:
            portable = not os.path.isabs(target) and path.resolve().is_relative_to(root) and path.exists()
          except (OSError, RuntimeError):
            portable = False
          if not portable:
            issues.append(f"Nonportable or broken symlink: {rel}")
          record = [rel, "symlink", target]
        elif path.is_file():
          if name == ".git":
            issues.append(f"Submodule Git metadata remains: {rel}")
            continue
          mode = path.stat().st_mode
          with path.open("rb") as f:
            head = f.read(256)
          if head.startswith(LFS):
            issues.append(f"Unresolved Git LFS pointer: {rel}")
          if name in PRIVATE_NAMES or name == ".env" or (name.startswith(".env.") and not name.endswith(("example", "sample"))):
            issues.append(f"Private/configuration file needs removal or explicit review: {rel}")
          if b"PRIVATE KEY-----" in head:
            issues.append(f"Private-key material detected: {rel}")
          if head.startswith(b"\x7fELF") and rel.startswith(("system/", "selfdrive/", "common/", "cereal/", "msgq_repo/")):
            if not elf_is_aarch64(head):
              issues.append(f"Non-aarch64 runtime binary: {rel}")
          file_hash = digest(path)
          record = [rel, "file", bool(mode & stat.S_IXUSR), file_hash]
          files.append({"path": rel, "sha256": file_hash, "bytes": path.stat().st_size})
        else:
          issues.append(f"Unsupported filesystem object: {rel}")
          continue
        payload.update((json.dumps(record, separators=(",", ":")) + "\n").encode())
      except (OSError, RuntimeError) as exc:
        issues.append(f"Unreadable entry: {rel} ({type(exc).__name__})")

  for rel in REQUIRED + BINARIES:
    if not safe_file(root, rel) or (root / rel).stat().st_size == 0:
      issues.append(f"Missing required release file: {rel}")
  for rel in BINARIES:
    if safe_file(root, rel):
      with (root / rel).open("rb") as f:
        if not elf_is_aarch64(f.read(64)):
          issues.append(f"Required executable is not aarch64 ELF: {rel}")
      if not (root / rel).stat().st_mode & stat.S_IXUSR:
        issues.append(f"Required executable has no execute bit: {rel}")
  for rel in ("launch_openpilot.sh", "launch_chffrplus.sh"):
    if safe_file(root, rel) and not (root / rel).stat().st_mode & stat.S_IXUSR:
      issues.append(f"Launcher has no execute bit: {rel}")
  for rel in OLD_ASSETS:
    if (root / rel).exists() or (root / rel).is_symlink():
      issues.append(f"Superseded branding asset still present: {rel}")
  for name, expected in MEDIA.items():
    rel = "selfdrive/assets/roadline/" + name
    if not safe_file(root, rel) or digest(root / rel) != expected:
      issues.append(f"Approved green-and-white media missing or changed: {rel}")
  for rel in ("selfdrive/ui/layouts/home.py", "system/ui/spinner.py"):
    if safe_file(root, rel):
      text = (root / rel).read_text(errors="replace")
      if re.search(r"philly[ _-]*fork", text, re.I):
        issues.append(f"Active old branding remains: {rel}")
      if "roadline" not in text.lower():
        issues.append(f"Roadline branding is not integrated: {rel}")
    else:
      issues.append(f"Missing active branding module: {rel}")
  if not safe_file(root, "prebuilt"):
    issues.append("Prebuilt marker missing; source snapshots are not prebuilt downloads.")
  if (root / ".gitmodules").exists():
    issues.append("Release must flatten pinned submodules, not depend on a later submodule fetch.")
  if safe_file(root, "launch_env.sh") and not re.search(r'AGNOS_VERSION=[\"\x27]17\.2[\"\x27]', (root / "launch_env.sh").read_text()):
    issues.append("Launcher AGNOS version is not the reviewed 17.2 target.")
  revision = (root / "git_src_commit").read_text().strip() if safe_file(root, "git_src_commit") else ""
  if not SHA.fullmatch(revision):
    issues.append("Missing valid 40-character git_src_commit source provenance.")
  issues.extend(model_errors(root))
  payload_sha256 = payload.hexdigest()
  if evidence is None:
    issues.append("No exact-payload validation evidence supplied; publication is blocked.")
  else:
    issues.extend(evidence_errors(evidence, revision, payload_sha256))
  return {"schema_version": 1, "status": "BLOCKED" if issues else "REVIEW_REQUIRED",
          "eligible_for_publication_review": not issues, "road_ready": False,
          "source_revision": revision or None, "payload_sha256": payload_sha256,
          "target": {"model": "comma tizi", "architecture": "aarch64", "agnos": "17.2"},
          "files_checked": len(files), "blockers": issues,
          "limitations": ["Evidence references are maintainer assertions, not authenticated attestations.",
                          "Does not establish model inference, CAN health, vehicle safety, or installer operation.",
                          "No installer URL is generated or enabled by this tool."], "files": files}


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("release_tree", type=Path)
  parser.add_argument("--evidence", type=Path, help="Reviewed evidence JSON outside the release tree")
  args = parser.parse_args()
  try:
    if args.evidence and args.evidence.resolve().is_relative_to(args.release_tree.resolve()):
      raise ValueError("Keep validation evidence outside the hashed release tree.")
    evidence = json.loads(args.evidence.read_text()) if args.evidence else None
    report = inspect_tree(args.release_tree, evidence)
  except (OSError, ValueError, RuntimeError) as exc:
    print(json.dumps({"status": "BLOCKED", "error": str(exc), "road_ready": False}))
    return 2
  print(json.dumps(report, indent=2))
  return 0 if report["eligible_for_publication_review"] else 2


if __name__ == "__main__":
  raise SystemExit(main())
