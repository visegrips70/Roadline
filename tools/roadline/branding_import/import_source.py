#!/usr/bin/env python3
"""One-time import of the reviewed branding TEXT changes into a draft branch.

No binary media are embedded here. This must never be used as an install release.
"""
import base64
import hashlib
import os
from pathlib import Path
import subprocess
import zlib

BRANCH = "roadline-branding-upload"
PATCH_SHA256 = "f593e312cb2584022680c439db6e0d9a7a8bafc652396932cad248e358e5cf63"
TEXT_PATHS = [
  ".gitattributes", ".gitignore", "docs/roadline/BRANDING.md",
  "selfdrive/assets/roadline/manifest.json", "selfdrive/ui/layouts/home.py",
  "selfdrive/ui/layouts/onboarding.py", "selfdrive/ui/layouts/settings/nap.py",
  "selfdrive/ui/layouts/settings/settings.py", "selfdrive/ui/ui.py",
  "system/ui/lib/roadline_video.py", "system/ui/roadline_spinner.py",
  "system/ui/spinner.py", "tools/roadline/test_branding.py",
]
OLD_IMAGES = {
  "selfdrive/assets/images/phillyfork_offroad_road.png": "d1a35e74b99e51363ef3136ef4663b15fc8119023250e2a7ba9ebb348439918c",
  "selfdrive/assets/images/phillyfork_road.png": "d1a35e74b99e51363ef3136ef4663b15fc8119023250e2a7ba9ebb348439918c",
  "selfdrive/assets/images/spinner_comma.png": "8de9f10bdbf5fcfcb8116d3d41c2c00e0e9c43b32e3ab49979c270e201695de66",
}


def run(*args, **kwargs):
  return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout.strip()


def main():
  if os.environ.get("GITHUB_REPOSITORY") != "visegrips70/Roadline" or os.environ.get("GITHUB_REF_NAME") != BRANCH:
    raise SystemExit("This one-time import is restricted to the draft branding upload branch.")
  expected = os.environ["GITHUB_SHA"]
  if run("git", "rev-parse", "HEAD") != expected:
    raise SystemExit("Unexpected checkout revision.")
  remote = run("git", "ls-remote", "origin", f"refs/heads/{BRANCH}").split()[0]
  if remote != expected:
    raise SystemExit("Draft branch changed; refusing to overwrite concurrent work.")
  folder = Path(__file__).parent
  chunks = [(folder / f"patch.{i:02d}.b64").read_text().strip() for i in (1, 2, 3)]
  # Repair one identified transport transcription before verifying the complete original payload.
  chunks[0] = chunks[0].replace("rsgkb7Cvs", "rsgkb5gb7Cvs")
  data = zlib.decompress(base64.b64decode("".join(chunks), validate=True))
  if hashlib.sha256(data).hexdigest() != PATCH_SHA256:
    raise SystemExit("Branding text payload checksum mismatch; nothing will be applied.")
  patch = data.decode("utf-8")
  allowed = set(TEXT_PATHS) | {"system/ui/phillyfork_spinner.py"}
  headers = [line[6:] for line in patch.splitlines() if line.startswith(("--- a/", "+++ b/"))]
  if not headers or not set(headers).issubset(allowed):
    raise SystemExit("Unexpected path in branding patch.")
  run("git", "apply", "--check", "-", input=patch)
  for path, digest in OLD_IMAGES.items():
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
      raise SystemExit(f"Old image changed before import: {path}")
  run("git", "apply", "-", input=patch)
  run("git", "rm", "--", *OLD_IMAGES)

  notice = """# Draft source upload: media pending

The branding Python source and text changes are uploaded on this development branch.
The exact approved binary assets have NOT been transferred to GitHub. Do not merge
this draft into an install branch or use it as a device-ready build.

Required directory: `selfdrive/assets/roadline/`

| Missing file | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| logo.png | 748335 | 3fee5eb04a58371404db18a6a33ff936d2846d04a8d125b1b7189aac92749dd7 |
| startup.mp4 | 620473 | eee01080bd398f53688b08bed490b55addfdfb22f2a9d03a39b742a83b976265 |
| startup_still.png | 470156 | 23f593fe4fa7a9d81effbdcf3449af9454c91ad20fd69359317c8ed4bb894425 |

These are the unchanged approved files in the downloadable branding kit and
combined Roadline development stack. Upload the actual bytes, not LFS pointers,
links, regenerated artwork, or base64 text saved with PNG/MP4 extensions.

The full local source package with all three media files passed 28 branding tests,
38 release-gate tests, and 14 URL-verifier tests before this source upload. Those
are synthetic local tests, not comma hardware tests. The media/hash tests cannot
pass in this GitHub draft until the missing files are uploaded. The import checks
only source syntax and the 52 preparation-tool tests on GitHub.

After all three files are present, run `python3 tools/roadline/test_branding.py`,
then the complete development build and the remaining native/bench release gates.
No installer URL, publication, firmware flash, device update, or driving approval
is enabled by this draft. Main, the install branch, and first-drive fixes are
not modified. Internal NAP compatibility names and licensing are preserved.
"""
  Path("docs/roadline/BRANDING_UPLOAD_STATUS.md").write_text(notice)
  branding = Path("docs/roadline/BRANDING.md")
  branding.write_text("**GitHub draft: approved binary media are still missing.** See [upload status](BRANDING_UPLOAD_STATUS.md).\n\n" + branding.read_text())
  readme = Path("README.md")
  readme.write_text("# Draft branding upload — not installable\n\nThe branding source is uploaded, but the approved PNG/MP4 files are not yet in GitHub. See [pending media and checks](docs/roadline/BRANDING_UPLOAD_STATUS.md).\n\n" + readme.read_text())
  direct = Path("docs/roadline/DIRECT_DOWNLOAD.md")
  direct.write_text("**Draft upload update:** Branding source is now on this branch; the three exact binary assets remain pending. See [upload status](BRANDING_UPLOAD_STATUS.md). The installer is still disabled.\n\n" + direct.read_text())

  for path in TEXT_PATHS:
    if path.endswith(".py"):
      compile(Path(path).read_text(), path, "exec")
  print(run("python3", "tools/roadline/test_download_release.py"))
  print(run("python3", "tools/roadline/test_verify_install_url.py"))
  run("git", "add", "--", *TEXT_PATHS, "system/ui/phillyfork_spinner.py", "README.md",
      "docs/roadline/BRANDING_UPLOAD_STATUS.md", "docs/roadline/DIRECT_DOWNLOAD.md")
  run("git", "rm", "-r", "--", "tools/roadline/branding_import", ".github/workflows/roadline-import-branding.yml")
  run("git", "diff", "--cached", "--check")
  run("git", "config", "user.name", "github-actions[bot]")
  run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
  run("git", "commit", "-m", "Upload approved Roadline branding source; explicitly track missing binary media")
  remote = run("git", "ls-remote", "origin", f"refs/heads/{BRANCH}").split()[0]
  if remote != expected:
    raise SystemExit("Draft branch moved during import; no push attempted.")
  print(run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}"))
  print("Uploaded source commit:", run("git", "rev-parse", "HEAD"))
  print("Binary media are still missing. This is a draft source upload, not a release.")


if __name__ == "__main__":
  main()
