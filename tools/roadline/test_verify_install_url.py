"""Synthetic HTTP/ELF tests. No internet requests and no installer execution."""
import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location("verify", Path(__file__).with_name("verify_install_url.py"))
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def fixture():
  data = bytearray(256)
  data[:7] = b"\x7fELF\x02\x01\x01"
  struct.pack_into("<HH", data, 16, 3, 183)
  return bytes(data)


class Response(io.BytesIO):
  status = 200
  def __init__(self, data, headers=None, url="https://roadline.invalid/install"):
    super().__init__(data)
    self.headers = headers or {}
    self.url = url

  def geturl(self):
    return self.url


class Client:
  def __init__(self, response):
    self.response = response
    self.request = None

  def open(self, req, timeout):
    self.request = req
    assert timeout == 20
    return self.response


class URLTests(unittest.TestCase):
  def setUp(self):
    self.data = fixture()
    self.sha = hashlib.sha256(self.data).hexdigest()

  def test_complete_header_checksum_pass_does_not_claim_installation(self):
    result = verify.inspect_payload(self.data, self.sha)
    self.assertFalse(result["executed"])
    self.assertFalse(result["installation_verified"])
    self.assertEqual(result["transport_and_header_check"], "pass")

  def test_unreviewed_hash_rejected(self):
    with self.assertRaises(ValueError):
      verify.inspect_payload(self.data, "0" * 64)

  def test_malformed_hash_rejected_before_network(self):
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", "nope", object())

  def test_invalid_content_rejected(self):
    for data in (b"<html>login</html>" * 12, b"PK" + bytes(254), b"#!/bin/sh\n" + bytes(246)):
      with self.subTest(data=data[:10]), self.assertRaises(ValueError):
        verify.inspect_payload(data, hashlib.sha256(data).hexdigest())

  def test_other_elf_architecture_rejected(self):
    data = bytearray(self.data)
    struct.pack_into("<H", data, 18, 62)
    with self.assertRaises(ValueError):
      verify.inspect_payload(data, hashlib.sha256(data).hexdigest())

  def test_relocatable_elf_rejected(self):
    data = bytearray(self.data)
    struct.pack_into("<H", data, 16, 1)
    with self.assertRaises(ValueError):
      verify.inspect_payload(data, hashlib.sha256(data).hexdigest())

  def test_insecure_or_tokenized_urls_rejected(self):
    for url in ("http://host/install", "https://a:b@host/install", "https://host/install?token=x",
                "https://host/install#x", "file:///etc/passwd", "https://host/a b", "https://host/\nx"):
      with self.subTest(url=url), self.assertRaises(ValueError):
        verify.validate_url(url)

  def test_transport_success(self):
    client = Client(Response(self.data, {"Content-Length": str(len(self.data))}))
    result = verify.check_url("https://roadline.invalid/install", self.sha, client)
    self.assertEqual(result["bytes"], len(self.data))
    self.assertIn("AGNOSSetup", client.request.get_header("User-agent"))
    self.assertIsNone(client.request.get_header("Authorization"))

  def test_https_redirect_downgrade_rejected(self):
    redirect = verify.SecureRedirect()
    with self.assertRaises(ValueError):
      redirect.redirect_request(None, None, 302, "Found", {}, "http://host/file")

  def test_response_final_url_checked(self):
    client = Client(Response(self.data, url="http://host/file"))
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", self.sha, client)

  def test_error_status_rejected(self):
    response = Response(self.data)
    response.status = 503
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", self.sha, Client(response))

  def test_declared_oversize_rejected(self):
    response = Response(self.data, {"Content-Length": str(verify.MAX_INSTALLER_BYTES + 1)})
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", self.sha, Client(response))

  def test_undeclared_oversize_rejected(self):
    response = Response(b"X" * (verify.MAX_INSTALLER_BYTES + 1))
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", self.sha, Client(response))

  def test_truncated_content_rejected(self):
    response = Response(self.data, {"Content-Length": str(len(self.data) + 1)})
    with self.assertRaises(ValueError):
      verify.check_url("https://roadline.invalid/install", self.sha, Client(response))


if __name__ == "__main__":
  unittest.main()
