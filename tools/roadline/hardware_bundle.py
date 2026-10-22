#!/usr/bin/env python3
"""Inventory built Panda/radar assets using files only; never opens USB or CAN."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[2]
APP = "panda/board/obj/panda_h7.bin.signed"
BOOTSTUB = "panda/board/obj/bootstub.panda_h7.bin"
REQUIRED = (
  APP, BOOTSTUB,
  "opendbc_repo/opendbc/safety/modes/tesla_preap.h",
  "opendbc_repo/opendbc/car/tesla/preap/interface.py",
  "opendbc_repo/opendbc/car/tesla/preap/pedal_feedback.py",
  "opendbc_repo/opendbc/car/tesla/radar_interface.py",
  "opendbc_repo/opendbc/dbc/tesla_radar_bosch_generated.dbc",
  "selfdrive/controls/radard.py",
  "selfdrive/pandad/pandad.py",
  "selfdrive/ui/layouts/settings/nap.py",
  "selfdrive/ui/layouts/settings/nap_content.py",
  "scripts/nap/calibrate_pedal.py",
  "scripts/nap/calibrate_radar.py",
  "scripts/nap/test_radar.py",
  "scripts/nap/extract_epas.py",
  "scripts/nap/flash_epas.py",
  "scripts/nap/restore_epas.py",
  "scripts/nap/firmware/epas-bootloader-0x3ff7000-0x3ffacbd.bin",
)
MAX_ASSET_BYTES = 8 * 1024 * 1024


def read_asset(path, limit=MAX_ASSET_BYTES):
  try:
    with path.open("rb") as handle:
      data = handle.read(limit + 1)
    if not data or len(data) > limit or data.startswith(b"version https://git-lfs.github.com/spec/"):
      return None
    return data
  except OSError:
    return None


def collect(checkout=ROOT, params=None):
  assets = {}
  blockers = []
  signature = None
  for relative in REQUIRED:
    data = read_asset(checkout / relative)
    if data is None:
      blockers.append(f"Missing, empty, oversized or unhydrated asset: {relative}")
      assets[relative] = None
      continue
    assets[relative] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if relative == APP:
      # This is the SETLEN layout in panda/board/crypto/sign.py. Structure
      # checks are not RSA verification or proof that this binary is running.
      if (len(data) < 140 or struct.unpack_from("<I", data)[0] != len(data) - 128
          or data[-136:-132] != b"VERS"):
        blockers.append("Panda H7 image does not have the expected signed-image layout.")
      else:
        signature = data[-128:]

  observed = None
  if params is not None:
    reported = read_asset(params / "PandaSignatures", 128)
    observed = {
      "record_present": reported is not None and len(reported) == 128,
      "matches_bundle": (reported == signature) if reported is not None and len(reported) == 128 and signature is not None else None,
      "live_health_verified": False,
      "note": "PandaSignatures is a cached startup record; it can be stale. A match does not establish current firmware or CAN health.",
    }
  return {
    "report_version": 1,
    "scope": "File inventory only. No USB/CAN access, firmware installation, settings changes or vehicle commands.",
    "assets": assets,
    "panda_signature_hex": signature.hex() if signature else None,
    "last_reported_panda": observed,
    "blockers": blockers,
    "bundle_files_complete": not blockers,
    "road_ready": False,
  }


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkout", type=Path, default=ROOT)
  parser.add_argument("--params", type=Path, help="Optionally compare an existing PandaSignatures file; never writes params.")
  args = parser.parse_args()
  report = collect(args.checkout, args.params)
  print(json.dumps(report, indent=2))
  return 2 if report["blockers"] else 0


if __name__ == "__main__":
  raise SystemExit(main())
