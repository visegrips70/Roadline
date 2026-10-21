#!/usr/bin/env bash
# Build an inactive, pinned checkout on a bench-powered Comma 3X.
# Does not replace /data/openpilot, start manager/pandad, or update AGNOS.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
fail() { echo "Roadline build stopped: $*" >&2; exit 2; }

[[ $# -eq 1 && "$1" =~ ^[0-9a-f]{40}$ ]] || fail "supply the reviewed 40-character candidate commit."
[[ -f /TICI && -f /AGNOS && "$(uname -m)" == aarch64 ]] || fail "this command requires the actual Comma 3X."
[[ -r /sys/firmware/devicetree/base/model ]] || fail "hardware model is unavailable."
MODEL="$(tr -d '\0' < /sys/firmware/devicetree/base/model)"
[[ "$MODEL" == "comma tizi" ]] || fail "unsupported hardware: $MODEL"
[[ "$(cat /VERSION)" == 17.2 ]] || fail "AGNOS 17.2 required; no OS update will be attempted."
[[ -r /data/params/d/IsOnroad && "$(cat /data/params/d/IsOnroad)" == 0 ]] || fail "off-road state is not confirmed."
[[ "$ROOT" != "$(readlink -f /data/openpilot)" ]] || fail "build in a separate candidate checkout."
[[ "$ROOT" == /data/* ]] || fail "candidate must be in a separate directory under /data."
cd "$ROOT"
[[ "$(git rev-parse HEAD)" == "$1" ]] || fail "checkout does not match the reviewed commit."
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || fail "tracked source or submodules have local changes."
[[ ! -e prebuilt ]] || fail "use the source checkout, without a prebuilt marker."
SUBMODULES="$(git submodule status --recursive)"
if printf '%s\n' "$SUBMODULES" | grep -q '^[+U-]'; then
  fail "one or more pinned submodules is missing or mismatched."
fi
git lfs fsck --objects --pointers
git lfs ls-files --long | awk '$2 == "-" { missing=1 } END { exit missing ? 1 : 0 }' \
  || fail "model or other LFS assets have not been downloaded."
PYTHON=/usr/local/venv/bin/python
[[ -x "$PYTHON" ]] || fail "AGNOS Python environment is missing."
"$PYTHON" -c 'import sys; assert (3, 12, 3) <= sys.version_info < (3, 13)' \
  || fail "candidate requires Python 3.12.3 or newer within Python 3.12."
mkdir -p build/roadline-device
export PYTHONPATH="$ROOT:$ROOT/server"
export PATH="/usr/local/venv/bin:$PATH"
"$PYTHON" -m SCons -j2 --minimal 2>&1 | tee build/roadline-device/build.log
printf '%s\n' "$1" > build/roadline-device/built_commit.txt
echo "Device compilation completed. The active installation has not been switched."
echo "Boot, CAN, override, disengagement, monitoring and rollback checks remain."
