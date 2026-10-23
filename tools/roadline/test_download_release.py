"""Synthetic fixtures only: these tests never operate a comma or install software."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("download_release", Path(__file__).with_name("download_release.py"))
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
REV = "5" * 40


def elf(machine=183, bits=2, endian=1):
  data = bytearray(64)
  data[:6] = b"\x7fELF" + bytes((bits, endian))
  struct.pack_into("<H", data, 18, machine)
  return bytes(data)


class ReleaseGateTests(unittest.TestCase):
  def setUp(self):
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.root = Path(self.temp.name) / "release"
    self.root.mkdir()
    for rel in gate.REQUIRED:
      self.write(rel, b"fixture")
    self.write("system/ui/spinner.py", b"from roadline_spinner import RoadlineSpinner")
    self.write("selfdrive/ui/layouts/home.py", b"Roadline")
    self.write("launch_env.sh", b'export AGNOS_VERSION="17.2"\n')
    self.write("git_src_commit", REV.encode())
    self.write("prebuilt", b"")
    for rel in gate.BINARIES:
      self.write(rel, elf())
      (self.root / rel).chmod(0o755)
    for rel in ("launch_openpilot.sh", "launch_chffrplus.sh"):
      (self.root / rel).chmod(0o755)
    media = {}
    for name in gate.MEDIA:
      data = ("synthetic-" + name).encode()
      self.write("selfdrive/assets/roadline/" + name, data)
      media[name] = hashlib.sha256(data).hexdigest()
    self.media_patch = patch.object(gate, "MEDIA", media)
    self.media_patch.start()
    self.addCleanup(self.media_patch.stop)
    for name in ("driving_vision", "driving_policy", "dmonitoring_model"):
      self.write(f"selfdrive/modeld/models/{name}_tinygrad.pkl", b"synthetic-model")
    for size in ("1928x1208", "1344x760"):
      for prefix in ("warp", "dm_warp"):
        self.write(f"selfdrive/modeld/models/{prefix}_{size}_tinygrad.pkl", b"synthetic-warp")

  def write(self, rel, data):
    path = self.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

  def evidence(self):
    report = gate.inspect_tree(self.root)
    return {"source_revision": REV, "payload_sha256": report["payload_sha256"], "target": report["target"],
            "checks": {name: {"status": "pass", "reference": "synthetic://test-only"} for name in gate.CHECKS}}

  def blockers(self):
    return gate.inspect_tree(self.root, self.evidence())["blockers"]

  def assertBlocked(self, text):
    self.assertTrue(any(text in item for item in self.blockers()), self.blockers())

  def test_complete_fixture_requires_review_not_driving_approval(self):
    report = gate.inspect_tree(self.root, self.evidence())
    self.assertEqual(report["blockers"], [])
    self.assertEqual(report["status"], "REVIEW_REQUIRED")
    self.assertFalse(report["road_ready"])

  def test_no_evidence_blocks(self):
    self.assertFalse(gate.inspect_tree(self.root)["eligible_for_publication_review"])

  def test_stale_revision_blocks(self):
    evidence = self.evidence()
    evidence["source_revision"] = "6" * 40
    self.assertTrue(gate.evidence_errors(evidence, REV, evidence["payload_sha256"]))

  def test_changed_payload_invalidates_evidence(self):
    evidence = self.evidence()
    self.write("system/manager/manager.py", b"changed")
    self.assertIn("Evidence payload hash does not match the exact prepared tree.", gate.inspect_tree(self.root, evidence)["blockers"])

  def test_each_missing_evidence_check_blocks(self):
    for name in gate.CHECKS:
      with self.subTest(name=name):
        evidence = self.evidence()
        del evidence["checks"][name]
        self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"])

  def test_false_pass_boolean_rejected(self):
    evidence = self.evidence()
    evidence["checks"]["bench_boot"]["status"] = True
    self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"])

  def test_reference_required(self):
    evidence = self.evidence()
    evidence["checks"]["rollback"]["reference"] = ""
    self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"])

  def test_cosmetic_deferral_only_for_documented_staging_installation_test(self):
    evidence = self.evidence()
    evidence.update(channel="staging", purpose="installation-test")
    evidence["checks"]["splash_playback"] = {"status": "deferred", "reference": "synthetic://known-issue",
                                             "reason": "Registered prebuilt boot skips the startup spinner."}
    report = gate.inspect_tree(self.root, evidence)
    self.assertEqual(report["blockers"], [])
    self.assertFalse(report["road_ready"])
    self.assertEqual(report["deferred_cosmetic_checks"], ["splash_playback"])
    for key, value in (("channel", "stable"), ("purpose", "driving")):
      changed = dict(evidence, **{key: value})
      self.assertTrue(gate.inspect_tree(self.root, changed)["blockers"])
    evidence["checks"]["splash_playback"].pop("reason")
    self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"])

  def test_staging_cannot_defer_boot_build_settings_or_recovery(self):
    for name in gate.CHECKS:
      if name == "splash_playback":
        continue
      evidence = self.evidence()
      evidence.update(channel="staging", purpose="installation-test")
      evidence["checks"][name] = {"status": "deferred", "reference": "synthetic://test", "reason": "unfinished"}
      self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"], name)

  def test_wrong_device_evidence_rejected(self):
    evidence = self.evidence()
    evidence["target"]["model"] = "comma tici"
    self.assertTrue(gate.inspect_tree(self.root, evidence)["blockers"])

  def test_malformed_evidence_rejected(self):
    self.assertTrue(gate.evidence_errors([], REV, "hash"))

  def test_all_required_files_are_enforced(self):
    for rel in gate.REQUIRED:
      with self.subTest(path=rel):
        path = self.root / rel
        content = path.read_bytes()
        path.unlink()
        self.assertBlocked("Missing required release file: " + rel)
        path.write_bytes(content)
        if rel.startswith("launch_"):
          path.chmod(0o755)

  def test_each_approved_media_hash_is_enforced(self):
    for name in gate.MEDIA:
      with self.subTest(name=name):
        self.write("selfdrive/assets/roadline/" + name, b"wrong")
        self.assertBlocked("Approved green-and-white media missing or changed")

  def test_lfs_pointer_anywhere_blocks(self):
    self.write("extra.bin", gate.LFS + b"v1\n")
    self.assertBlocked("Unresolved Git LFS pointer: extra.bin")

  def test_source_snapshot_without_prebuilt_blocks(self):
    (self.root / "prebuilt").unlink()
    self.assertBlocked("Prebuilt marker missing")

  def test_submodule_declaration_blocks(self):
    self.write(".gitmodules", b"fixture")
    self.assertBlocked("flatten pinned submodules")

  def test_submodule_gitfile_blocks(self):
    self.write("server/.git", b"gitdir: ../.git/modules/server")
    self.assertBlocked("Submodule Git metadata remains")

  def test_wrong_agnos_blocks(self):
    self.write("launch_env.sh", b'AGNOS_VERSION="16.0"')
    self.assertBlocked("Launcher AGNOS version")

  def test_wrong_runtime_architecture_blocks(self):
    self.write(gate.BINARIES[0], elf(machine=62))
    self.assertBlocked("Non-aarch64 runtime binary")

  def test_elf_format_rejections(self):
    for data in (b"<html>error</html>", b"#!/bin/bash", elf(62), elf(bits=1), elf(endian=2), b"\x7fELF"):
      with self.subTest(header=data[:20]):
        self.assertFalse(gate.elf_is_aarch64(data))
    self.assertTrue(gate.elf_is_aarch64(elf()))

  def test_nonexecutable_binary_blocks(self):
    (self.root / gate.BINARIES[0]).chmod(0o644)
    self.assertBlocked("Required executable has no execute bit")

  def test_nonexecutable_launcher_blocks(self):
    (self.root / "launch_openpilot.sh").chmod(0o644)
    self.assertBlocked("Launcher has no execute bit")

  def test_philly_display_text_blocks(self):
    self.write("selfdrive/ui/layouts/home.py", b"Roadline THE PHILLY FORK")
    self.assertBlocked("Active old branding remains")

  def test_old_asset_blocks(self):
    self.write(gate.OLD_ASSETS[0], b"old")
    self.assertBlocked("Superseded branding asset")

  def test_missing_roadline_integration_blocks(self):
    self.write("system/ui/spinner.py", b"old_spinner")
    self.assertBlocked("Roadline branding is not integrated")

  def test_absolute_symlink_blocks(self):
    (self.root / "bad-link").symlink_to("/etc/passwd")
    self.assertBlocked("Nonportable or broken symlink")

  def test_escaping_relative_symlink_blocks(self):
    (self.root / "bad-link").symlink_to("../outside")
    self.assertBlocked("Nonportable or broken symlink")

  def test_symlink_cycle_blocks(self):
    (self.root / "a").symlink_to("b")
    (self.root / "b").symlink_to("a")
    self.assertBlocked("Nonportable or broken symlink")

  def test_internal_symlink_is_portable(self):
    (self.root / "openpilot").symlink_to(".", target_is_directory=True)
    self.assertEqual(self.blockers(), [])

  def test_private_names_block(self):
    for name in ("id_rsa", ".pairing-key", ".env", "nap_params.json"):
      with self.subTest(name=name):
        self.write(name, b"private fixture")
        self.assertBlocked("Private/configuration file")
        (self.root / name).unlink()

  def test_private_key_under_different_name_blocks(self):
    self.write("oops.txt", b"-----BEGIN OPENSSH PRIVATE KEY-----\n")
    self.assertBlocked("Private-key material detected")

  def test_env_example_allowed(self):
    self.write(".env.example", b"KEY=")
    self.assertEqual(self.blockers(), [])

  def test_missing_model_blocks(self):
    (self.root / "selfdrive/modeld/models/driving_vision_tinygrad.pkl").unlink()
    self.assertBlocked("Compiled QCOM model missing")

  def test_chunked_model_supported_without_deserialization(self):
    rel = "selfdrive/modeld/models/driving_vision_tinygrad.pkl"
    (self.root / rel).unlink()
    self.write(rel + ".chunkmanifest", b"2")
    self.write(rel + ".chunk01of02", b"synthetic")
    self.write(rel + ".chunk02of02", b"")
    self.assertEqual(self.blockers(), [])

  def test_missing_model_chunk_blocks(self):
    rel = "selfdrive/modeld/models/driving_vision_tinygrad.pkl"
    (self.root / rel).unlink()
    self.write(rel + ".chunkmanifest", b"2")
    self.write(rel + ".chunk01of02", b"synthetic")
    self.assertBlocked("Compiled model chunks missing")

  def test_invalid_model_chunk_manifest_blocks(self):
    rel = "selfdrive/modeld/models/driving_vision_tinygrad.pkl"
    self.write(rel + ".chunkmanifest", b"-1")
    self.assertBlocked("Invalid compiled model chunk manifest")

  def test_missing_camera_warp_blocks(self):
    (self.root / "selfdrive/modeld/models/warp_1928x1208_tinygrad.pkl").unlink()
    self.assertBlocked("Compiled camera warp missing")

  def test_missing_root_blocks(self):
    self.assertFalse(gate.inspect_tree(self.root / "absent")["eligible_for_publication_review"])

  def test_invalid_source_provenance_blocks(self):
    self.write("git_src_commit", b"main")
    self.assertBlocked("40-character git_src_commit")

  def test_repeated_inspection_does_not_mutate_payload(self):
    before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
    gate.inspect_tree(self.root, self.evidence())
    after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
    self.assertEqual(before, after)


if __name__ == "__main__":
  unittest.main()
