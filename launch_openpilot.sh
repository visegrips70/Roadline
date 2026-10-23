#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd "$DIR" || exit 1
export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
# Pairing is a local credential, independent of driving/calibration settings.
# Failure leaves normal startup available and reports navigation unavailable.
if [ -d /data/params/d ]; then
  python3 "$DIR/tools/roadline/navigation_setup.py" ||
    echo "Roadline: navigation pairing needs attention."
fi
python3 "$DIR/mpp_writer.py" &
exec "$DIR/launch_chffrplus.sh"
