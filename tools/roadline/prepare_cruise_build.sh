#!/usr/bin/env bash
# Build and package an inactive candidate. Never switch installations or flash CAN hardware.
set -euo pipefail
fail() { echo "STOP: $*" >&2; exit 1; }
revision="${1:-}"
[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || fail "Supply the full reviewed source revision."
[[ -f /TICI && -f /AGNOS && "$(uname -m)" == aarch64 ]] || fail "Run this on the Comma 3X."
[[ "$(cat /VERSION)" == 17.2 ]] || fail "AGNOS 17.2 is required."
[[ "$(tr -d '\0' < /sys/firmware/devicetree/base/model)" == 'comma tizi' ]] || fail "Wrong hardware model."
[[ "$(cat /data/params/d/IsOnroad)" == 0 ]] || fail "Keep the car off and the Comma powered."

if [[ "${2:-}" != --worker ]]; then
  [[ "$0" == /data/roadline-prepare-cruise-build.sh ]] || fail "Save this helper at /data/roadline-prepare-cruise-build.sh."
  # The separate tmux server survives an SSH/Wi-Fi interruption and cannot
  # replace the running comma service's session. Reconnect to the same build.
  exec tmux -L roadline-build -f /dev/null new-session -A -s "cruise-${revision:0:7}" \
    "bash /data/roadline-prepare-cruise-build.sh '$revision' --worker; result=\$?; printf '\nBUILD EXIT CODE: %s\n' \"\$result\"; exec bash"
fi

cd /data/openpilot
PYTHONPATH=/data/openpilot /usr/local/venv/bin/python - <<'PY'
from openpilot.common.params import Params
p = Params()
if p.get('IsOnroad') is not False:
  raise SystemExit('STOP: offroad state is not confirmed.')
for key, value in [('OpenpilotEnabledToggle', False), ('NAPPedalEnabled', False), ('DisableUpdates', True)]:
  if p.get('IsOnroad') is not False:
    raise SystemExit('STOP: vehicle state changed.')
  p.put(key, value)
  if p.get(key) is not value:
    raise SystemExit('STOP: could not verify ' + key)
print('Assistance and pedal control disabled. Saved pedal calibration is unchanged.')
PY

target="/data/roadline-cruise-build-$revision"
[[ ! -L "$target" ]] || fail "Candidate path must not be a symlink."
[[ "$(df --output=avail -B1 /data | tail -1)" -gt 8589934592 ]] || fail "At least 8 GiB free is required."
if [[ ! -e "$target" ]]; then
  git clone --no-checkout https://github.com/visegrips70/Roadline.git "$target"
  git -C "$target" fetch origin "$revision"
  git -C "$target" checkout --detach "$revision"
fi
cd "$target"
[[ "$(git rev-parse HEAD)" == "$revision" ]] || fail "Existing candidate is a different revision."
[[ -z "$(git status --porcelain --untracked-files=no)" ]] || fail "Candidate source has local changes."
git submodule update --init --recursive
git lfs pull
git submodule foreach --recursive 'git lfs pull'
bash tools/roadline/build_installer_on_device.sh "$revision"
echo "Fixed candidate built and packaged, including new Panda firmware."
echo "Active installation was not switched. No hardware was flashed."
echo "Package: /data/roadline-package-$revision"
