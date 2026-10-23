#!/usr/bin/env bash
# Run only in a separate checkout. Does not install software or flash hardware.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$ROOT"
bash tools/roadline/build_on_device.sh "$@"
export PATH="/usr/local/venv/bin:$PATH"
export PYTHONPATH="$ROOT:$ROOT/server"
python -m SCons -j2 selfdrive/ui/installer/installers/installer_roadline_staging
python - <<'PY'
from pathlib import Path
import hashlib
from tools.roadline.download_release import elf_is_aarch64
p = Path('selfdrive/ui/installer/installers/installer_roadline_staging')
b = p.read_bytes()
assert elf_is_aarch64(b[:64]), 'Installer must be an ARM64 ELF executable'
assert 0 < len(b) < 2500000, 'Installer exceeds setup download limit'
assert b'https://github.com/visegrips70/Roadline.git' in b, 'Wrong installer repository'
assert b'roadline-release-staging' in b, 'Wrong installer branch'
out = Path('build/roadline-device/installer.sha256')
out.write_text(hashlib.sha256(b).hexdigest() + '  ' + p.name + '\n')
print(out.read_text())
print('Installer compiled. The release branch is not published; do not reset the device.')
PY

python tools/roadline/package_native_release.py "$ROOT" "/data/roadline-package-$1" "$1"
