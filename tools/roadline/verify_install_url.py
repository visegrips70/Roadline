#!/usr/bin/env python3
"""Download and inspect an installer without executing it or modifying a device."""
import argparse
import hashlib
import json
import re
import struct
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_INSTALLER_BYTES = 8 * 1024 * 1024


def validate_url(url):
  parsed = urlsplit(url)
  if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
      or parsed.password is not None or parsed.fragment or parsed.query):
    raise ValueError("Use a permanent HTTPS installer URL without credentials, query tokens, or fragments.")
  if any(c.isspace() or ord(c) < 32 for c in url):
    raise ValueError("Whitespace and control characters are not allowed in the installer URL.")
  return url


class SecureRedirect(HTTPRedirectHandler):
  def redirect_request(self, req, fp, code, msg, headers, newurl):
    validate_url(newurl)
    return super().redirect_request(req, fp, code, msg, headers, newurl)


def inspect_payload(data, expected_sha256):
  if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
    raise ValueError("Expected SHA-256 must contain exactly 64 lowercase hexadecimal characters.")
  if not 64 <= len(data) <= MAX_INSTALLER_BYTES:
    raise ValueError("Installer length is outside the supported bounds.")
  if (data[:7] != b"\x7fELF\x02\x01\x01" or struct.unpack_from("<H", data, 18)[0] != 183
      or struct.unpack_from("<H", data, 16)[0] not in (2, 3)):
    raise ValueError("URL must serve an ARM64 ELF installer, not a ZIP, HTML page, shell script, or desktop binary.")
  actual = hashlib.sha256(data).hexdigest()
  if actual != expected_sha256:
    raise ValueError("Installer checksum differs from the reviewed artifact.")
  return {"transport_and_header_check": "pass", "bytes": len(data), "sha256": actual,
          "executed": False, "installation_verified": False,
          "note": "Header and checksum only; this does not establish bootability, installation, or vehicle safety."}


def check_url(url, expected_sha256, opener=None):
  validate_url(url)
  if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
    raise ValueError("Expected SHA-256 must contain exactly 64 lowercase hexadecimal characters.")
  client = opener or build_opener(SecureRedirect())
  req = Request(url, headers={"User-Agent": "AGNOSSetup-roadline-verifier", "Accept-Encoding": "identity"})
  with client.open(req, timeout=20) as response:
    validate_url(response.geturl())
    if response.status != 200:
      raise ValueError("Installer endpoint did not return HTTP 200.")
    length = response.headers.get("Content-Length")
    if length is not None and not 64 <= int(length) <= MAX_INSTALLER_BYTES:
      raise ValueError("Installer response length is outside the supported bounds.")
    chunks, size = [], 0
    while True:
      chunk = response.read(min(65536, MAX_INSTALLER_BYTES + 1 - size))
      if not chunk:
        break
      chunks.append(chunk)
      size += len(chunk)
      if size > MAX_INSTALLER_BYTES:
        raise ValueError("Installer response exceeds the size limit.")
    if length is not None and int(length) != size:
      raise ValueError("Installer response was incomplete.")
  return inspect_payload(b"".join(chunks), expected_sha256)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("url")
  parser.add_argument("--sha256", required=True)
  args = parser.parse_args()
  try:
    report = check_url(args.url, args.sha256)
  except (OSError, ValueError) as exc:
    # Do not echo exception URLs, which may contain server-supplied tokens.
    print(json.dumps({"status": "BLOCKED", "error_type": type(exc).__name__, "executed": False}))
    return 2
  print(json.dumps(report, indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
