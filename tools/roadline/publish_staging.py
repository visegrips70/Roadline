#!/usr/bin/env python3
"""Assemble the reviewed native build and publish an installation-test channel.

Run by the one-time publication workflow. Never runs the installer or vehicle
software. Source files and uploaded native chunks must match the reviewed tree.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

from download_release import inspect_tree
from verify_install_url import check_url, inspect_payload

SOURCE = "2fbfa0c654230ead83596e2f6a474f8a8692f464"
PAYLOAD = "a93bec8362161c117c36139842c253cbb32bfb7135ac0bc3c7bb7137babdecea"
INSTALLER = "e2cdbe18ee902534c0b97ad898f604d884f76c77d86a578bd5333694cb623f61"
REPO = "https://github.com/visegrips70/Roadline.git"
RUNTIME_BRANCH = "roadline-release-staging"
INSTALLER_BRANCH = "roadline-installers"
URL = "https://raw.githubusercontent.com/visegrips70/Roadline/roadline-installers/installer"


def blob_sha(data):
  return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def relative(name):
  path = PurePosixPath(name)
  if not name or path.is_absolute() or any(p in ("", ".", "..", ".git") for p in name.split("/")):
    raise ValueError("Unsafe manifest path")
  return path


def assemble(source, inputs, output, manifest):
  if output.exists():
    raise ValueError("Assembly output must be new")
  records = manifest["entries"]
  names = [r["path"] for r in records]
  if len(set(names)) != len(names):
    raise ValueError("Duplicate manifest path")
  for name in names:
    relative(name)
  output.mkdir(parents=True)
  # Create symlinks last so no destination writes can traverse one.
  for record in sorted(records, key=lambda r: r["mode"] == "120000"):
    name, mode = record["path"], record["mode"]
    if record.get("type") != "blob" or mode not in ("100644", "100755", "120000"):
      raise ValueError("Unsupported tree entry")
    if record.get("from_source"):
      path = source / relative(name)
      if not path.resolve().is_relative_to(source.resolve()):
        raise ValueError("Source path leaves checkout")
      if mode == "120000":
        if not path.is_symlink():
          raise ValueError("Source symlink is missing")
        data = os.readlink(path).encode()
      else:
        if path.is_symlink():
          raise ValueError("Source file became a symlink")
        data = path.read_bytes()
    else:
      pieces = []
      for part in record["parts"]:
        if not re.fullmatch(r"parts/[0-9a-f]{40}", part):
          raise ValueError("Invalid part name")
        path = inputs / part
        if path.is_symlink() or not path.resolve().is_relative_to(inputs.resolve()):
          raise ValueError("Part leaves input directory")
        piece = path.read_bytes()
        if blob_sha(piece) != part.split("/")[1]:
          raise ValueError("Part checksum mismatch")
        pieces.append(piece)
      data = b"".join(pieces)
    if blob_sha(data) != record["sha"]:
      raise ValueError("File checksum mismatch: " + name)
    dest = output / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if mode == "120000":
      target = data.decode()
      if os.path.isabs(target) or not (dest.parent / target).resolve().is_relative_to(output.resolve()):
        raise ValueError("Symlink leaves runtime")
      dest.symlink_to(target)
    else:
      dest.write_bytes(data)
      dest.chmod(0o755 if mode == "100755" else 0o644)


def git(path, *args, env=None):
  return subprocess.check_output(["git", "-C", str(path), "-c", "core.hooksPath=/dev/null",
                                  "-c", "core.autocrlf=false", *args], text=True, env=env).strip()


def commit_tree(path, branch, message):
  git(path, "init", "-q")
  git(path, "symbolic-ref", "HEAD", "refs/heads/" + branch)
  git(path, "config", "user.name", "Roadline release workflow")
  git(path, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
  git(path, "add", "--force", "--all")
  git(path, "commit", "-q", "-m", message)
  return git(path, "rev-parse", "HEAD")


def publish(runtime, installer, summary):
  if os.environ.get("GITHUB_REPOSITORY") != "visegrips70/Roadline" or os.environ.get("GITHUB_REF") != "refs/heads/roadline-staging-publication":
    raise ValueError("Publishing is limited to the reviewed repository workflow")
  token = os.environ.get("GH_TOKEN")
  if not token:
    raise ValueError("Workflow token missing")
  env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_COUNT="1",
             GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
             GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + token).encode()).decode())
  # No credential values are put in files, subprocess arguments, or output.
  runtime_sha = commit_tree(runtime, RUNTIME_BRANCH, "Roadline 2fbfa0c installation-test runtime; assistance disabled")
  with tempfile.TemporaryDirectory(prefix="roadline-installer-") as folder:
    repo = Path(folder)
    (repo / "installer").write_bytes(installer)
    (repo / "README.md").write_text(
      "# Roadline installation test\n\n"
      "For comma 3X / AGNOS 17.2 bench installation testing. Not driving-ready.\n"
      "Assistance and automatic updates start disabled. Clean setup verification remains pending.\n"
      "Known cosmetic issue: registered prebuilt startup may skip the animation.\n\n"
      "Based on NAP by Philip and comma.ai openpilot; see the runtime's LICENSE and PROVENANCE.md.\n\n"
      f"Source: {SOURCE}\n\nRuntime commit: {runtime_sha}\n\nInstaller SHA-256: {INSTALLER}\n")
    installer_sha = commit_tree(repo, INSTALLER_BRANCH, "Publish reviewed Roadline staging installer")
    git(runtime, "fetch", str(repo), installer_sha)
    # Both refs must be absent. A retry cannot overwrite an existing channel.
    git(runtime, "push", "--atomic", "--force-with-lease=refs/heads/" + RUNTIME_BRANCH + ":",
        "--force-with-lease=refs/heads/" + INSTALLER_BRANCH + ":", REPO,
        runtime_sha + ":refs/heads/" + RUNTIME_BRANCH,
        installer_sha + ":refs/heads/" + INSTALLER_BRANCH, env=env)
  public_env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TERMINAL_PROMPT="0")
  for key in list(public_env):
    if key.startswith("GIT_CONFIG_") and key not in ("GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL"):
      del public_env[key]
    if key in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS"):
      del public_env[key]
  refs = git(runtime, "-c", "credential.helper=", "ls-remote", REPO,
             "refs/heads/" + RUNTIME_BRANCH, "refs/heads/" + INSTALLER_BRANCH, env=public_env)
  if not all(sha in refs for sha in (runtime_sha, installer_sha)):
    raise ValueError("Anonymous branch verification failed after publication")
  transport = check_url(URL, INSTALLER)
  summary.write_text(json.dumps({"source_revision": SOURCE, "payload_sha256": PAYLOAD,
                                "runtime_commit": runtime_sha, "installer_commit": installer_sha,
                                "installer_url": URL, "transport": transport,
                                "clean_setup_verified": False, "road_ready": False}, indent=2) + "\n")
  print(summary.read_text())


def main():
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument("source", type=Path)
  p.add_argument("inputs", type=Path)
  p.add_argument("output", type=Path)
  p.add_argument("--publish", action="store_true")
  args = p.parse_args()
  source, inputs = args.source.resolve(), args.inputs.resolve()
  manifest = json.loads((inputs / "payload.json").read_text())
  if (manifest["source_revision"], manifest["payload_sha256"], manifest["installer_sha256"]) != (SOURCE, PAYLOAD, INSTALLER):
    raise ValueError("Unreviewed publication inputs")
  if git(source, "rev-parse", "HEAD") != SOURCE:
    raise ValueError("Source checkout does not match the native build")
  output = args.output.resolve()
  assemble(source, inputs, output / "runtime", manifest)
  evidence = json.loads((inputs / "evidence.json").read_text())
  report = inspect_tree(output / "runtime", evidence)
  (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
  if not report["eligible_for_publication_review"] or report["payload_sha256"] != PAYLOAD:
    raise ValueError("Assembled runtime failed the exact-payload review")
  installer = (inputs / "installer").read_bytes()
  inspect_payload(installer, INSTALLER)
  print("Exact reviewed runtime and ARM64 installer verified; no vehicle software was executed.")
  if args.publish:
    publish(output / "runtime", installer, output / "publication.json")


if __name__ == "__main__":
  main()
