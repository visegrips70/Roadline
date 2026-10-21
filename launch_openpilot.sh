#!/usr/bin/env bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null && pwd)"
cd "$DIR" || exit 1
export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
python3 "$DIR/mpp_writer.py" &
exec "$DIR/launch_chffrplus.sh"
