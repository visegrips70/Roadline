# Timed bench boot of the native 2fbfa0c package

This is a one-device recovery helper for the reviewed comma 3X package, not an
installer or permission to drive. It is pinned to AGNOS 17.2, the exact runtime
payload hash, and the existing paths shown below. It does not publish a release.

Disconnect the vehicle harness and use stable wall/bench power. Do not use an
underpowered laptop USB port. `IsOnroad=0` alone cannot prove the harness is
disconnected. Normal startup includes pandad and can update the internal Panda
firmware; keep the vehicle disconnected throughout this test and recovery.

The helper expects:

- `/data/openpilot` to be a symlink to `/data/roadline-candidate-5de8b00`.
- The NAP backup at `/data/nap-before-roadline-e99f4dc`.
- A regular executable `/data/continue.sh` whose launch body is
  `cd /data/openpilot` followed by `exec ./launch_openpilot.sh`.
- The untouched package at `/data/roadline-repackage.qhnsNW/output/runtime`.
- Payload SHA-256 `a93bec8362161c117c36139842c253cbb32bfb7135ac0bc3c7bb7137babdecea`.

After obtaining `tools/roadline/bench_boot.py` from a reviewed, pinned commit as
`/data/roadline-bench-2fbfa0c.py`, run on the comma:

```sh
sudo -n /usr/bin/python3 /data/roadline-bench-2fbfa0c.py start --vehicle-disconnected
```

It verifies the payload before creating local Git metadata needed by startup,
installs a recovery timer and startup wrapper, stops the current service, saves a
private local copy of Params, and disables assistance and updates. It then changes
only the active symlink and starts the candidate. The source build and NAP backup
are preserved. The local Git commit identifies a bench checkout; the runtime's
`git_src_commit` and release manifest retain the native source revision.

The timer requests return after 180 seconds. Service shutdown/startup can take
additional time. If power is interrupted, the reboot guard restores the previous
path before the original launch body runs. The wrapper uses AGNOS's existing
`/data/continue.sh` entry point. It saves and restores that file's exact bytes,
owner and executable mode, and refuses an unfamiliar launcher. No `/etc` writes,
systemd enablement, root remount, or OS service override is performed. The timed
return uses `systemd-run`, which creates a transient timer.
Automatic return still needs actual device
verification; unit tests exercise the recovery logic with service calls mocked.

Observe whether the Roadline animation and home screen appear, any error text,
and whether the previous installation returns. After about three minutes:

```sh
sudo -n /usr/bin/python3 /data/roadline-bench-2fbfa0c/control.py status
```

Expected results are `TEST STATE: returned`, the previous active path, service
`active`, assistance `0`, updates disabled `1`, and both backup checks true. A
running service alone does not prove the UI, cameras, firmware or vehicle controls
are healthy. Inspect the screen and the saved `service-log.txt` if startup fails.

For an immediate manual return:

```sh
sudo -n /usr/bin/python3 /data/roadline-bench-2fbfa0c/control.py rollback
```

Recovery restores saved NAP/Roadline settings and calibration and leaves
assistance off and updates disabled. It does not restore transient process IDs
or automatically enable driving. Full Params and logs remain root-readable in
`/data/roadline-bench-2fbfa0c`; do not publish that directory, because Params can
contain credentials. The original `/data/continue.sh` is restored during recovery.
Do not delete the helper or record while the test is pending. A repeated test is
deliberately refused pending review, except for the narrowly checked retry below.

## Retrying the read-only filesystem failure

The original helper attempted to create a service under `/etc/systemd/system`.
On AGNOS 17.2 this failed with `EROFS` before the timer, settings snapshot or
candidate switch. A record showing `returned`, no `start_time`, and no settings
snapshot therefore does not mean the candidate was tested.

After obtaining the corrected helper, this one-time retry is supported:

```sh
sudo -n /usr/bin/python3 /data/roadline-bench-2fbfa0c.py start --vehicle-disconnected --retry-unstarted
```

The retry rechecks the exact package hash, launcher and previous active path. It
also checks that the local Git metadata is from the failed bench attempt. It
preserves the old record under `/data/roadline-bench-2fbfa0c-before-rofs-fix` before
starting a fresh test. It refuses a record with a prior candidate start, a settings
snapshot, another startup wrapper, or an existing archive. No package download,
rebuild, reset or manual deletion is required.

The `CANDIDATE START REQUESTED` status field distinguishes a pre-switch failure
from an attempted candidate launch. It is not proof of successful UI startup.

Upstream startup entry point:
[AGNOS comma.sh](https://github.com/commaai/agnos-builder/blob/master/userspace/root/usr/comma/comma.sh).

Successful bench observations are only startup/recovery evidence. They do not
validate steering takeover, braking, pedal behavior, radar or road use. No
permanent switch, reset, OTA enablement or install URL is performed here.
