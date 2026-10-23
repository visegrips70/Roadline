# Cruise re-engagement and pedal feedback correction

The installed staging source `2fbfa0c654230ead83596e2f6a474f8a8692f464`
recorded six Controls Mismatch disengagements, each approximately two seconds
after an engagement request. The pedal option was disabled, selecting stock
cruise mode and explaining the separate “Arm Stock Cruise” message.

## Changes

- Panda's Pre-AP hook now requires a recent neutral-to-pull stalk transition.
  That explicit gesture resets the stale cruise latch left when the heartbeat
  withdraws controls permission after application disengagement. A held pull,
  a pull at startup, or stale neutral input cannot re-arm. Door, gear, steering
  override, EPAS rejection and invalid-RX interlocks remain effective. A pull
  consumed during an interlock needs a new release and pull after it clears.
- `GAS_SENSOR` decodes the high nibble as status and the low nibble as counter.
  The old Tesla DBC reversed them. Five recorded wire frames and independent
  synthetic bytes exercise the decoder without relying on CANPacker to create
  the expected encoding. Command-message fields and calibration are unchanged.
- Unavailable pedal feedback clears the longitudinal request, target and brake
  resume state. Feedback recovery alone cannot restore that request. The final
  pedal command path independently rejects enabled output on faulted or stale
  feedback, while allowing disabled passthrough commands.
- Brake still pauses longitudinal control while preserving lateral control;
  steering takeover still cancels both. Pedal control is not automatically enabled.

## Validation

An offline CAN replay loaded freshly compiled baseline and patched safety
libraries separately. It fed the recorded selected CAN RX messages and injected
the three permission withdrawals observed in the recording. At 150 ms after
each of nine application engagement requests, the baseline accepted three and
rejected the same six that produced Controls Mismatch. The patched hook accepted
all nine. This is a re-arm regression replay, not a closed-loop driving test or
proof of live firmware behavior.

Local checks:

- Fresh opendbc DBC generation and safety-library compilation passed.
- Pre-AP safety and feature suite: **203 passed, 8 skipped**.
- Wider safety suite: **2,901 passed, 1,539 skipped**; two MISRA mutation checks
  initially failed because Cppcheck was absent. After installing the required
  Cppcheck 2.17.1, both mutation checks passed independently.
- MISRA baseline passed with Cppcheck 2.17.1.
- Ruff passed for the modified/new focused test files; `git diff --check` passed.
- Build-helper Bash syntax passed. Its non-device guard rejected this desktop
  environment before device writes or checkout creation.

The two uploaded sessions contain approximately 11 minutes of usable data. The
last full and summary logs have incomplete tails; all six mismatch incidents
occur earlier in complete segments. Raw logs, vehicle identifiers, routes,
coordinates and calibration values are not published with this change.

## Device build and remaining checks

`tools/roadline/prepare_cruise_build.sh` takes the full reviewed source commit.
Save it as `/data/roadline-prepare-cruise-build.sh` and invoke it over an SSH TTY.
It checks Comma 3X / AGNOS 17.2 and offroad state, disables assistance and pedal
control using the installed Params API, preserves calibration, and builds a
pinned checkout in an independent tmux session. It packages the runtime and
new Panda firmware without switching `/data/openpilot` or flashing hardware.

This commit is source, not an installed update. The published installer still
points to the earlier staging runtime. A native build, package verification,
bench startup and live stationary checks are still required before updating
that channel or enabling control. The old hardcoded `bench_boot.py` is for the
previous package and must not be used to activate this candidate.

The disconnected radar remains outside this change. A transmitting pedal and
restored calibration do not establish healthy pedal actuation. The recorded
status nibble was 5 with pedal output disabled; it must not be treated as status
0 or bypassed. Preserve NAP/Philip and comma attribution already in the project.

## Native package and guarded first start (October 23 follow-up)

The operator reported a successful native Comma 3X build of source
`c79c68fe5dac6d9668aadb6a64ee7b0557e89599` with build exit code 0.
The package contains 3,915 regular files and has payload checksum
`44a6e1ea33f500395653002ad0b1062186f8501532f2ed05eae70c5e0e4c9986`.
Its Panda H7 firmware checksum is
`8ece3dee9a1fb90f8d048272ea26a7bf26f6646e18e0100802b77bbec8eb0fc0`.
These are operator-supplied file observations, not live hardware validation.

The original CI run found 12 inherited tests using incomplete pedal doubles or
uninitialized feedback. Test-only commit `53dd4d62d7444f4cebf00a55f0fa2fb58f198e09`
provides explicit healthy feedback without weakening any existing assertion and
adds fault/timeout packed-command checks. Its full development validation passed:
https://github.com/visegrips70/Roadline/actions/runs/40032967778
The driving code and firmware source are identical to the native c79c68f build.

`tools/roadline/start_cruise_candidate.py` is for this exact package and a clean
2fbfa0c installation stored as the real `/data/openpilot` directory. It rehashes
the complete package, checks both firmware baselines, and copies the runtime to
`/data/roadline-runtime-c79c68f`, leaving the original package unused. It stops
the comma service, snapshots selected driving settings and calibration locally,
preserves the old installation at `/data/roadline-before-cruise-c79c68f`, and
switches the active link. Recovery files stay in the root-only directory
`/data/roadline-cruise-recovery-c79c68f`. Nothing from the device is uploaded.

Run start and rollback only with vehicle wiring disconnected and stable separate
power. Normal pandad startup can flash the internal Panda; the helper does not
flash the pedal, radar or EPAS. It never enables assistance, pedal control,
navigation maneuvers, radar or updates. Every subsequent candidate boot also
keeps those controls disabled until a separately reviewed promotion. The candidate
stays selected after normal reboot; there is no timer returning to the old build.
An interrupted directory swap is recovered through `/data/continue.sh` without
writing to the read-only OS partition.

After first start, read status on the Comma with:

```sh
sudo -n /usr/bin/python3 /data/roadline-cruise-recovery-c79c68f/control.py status
```

Manual return, with vehicle wiring disconnected and separate power:

```sh
sudo -n /usr/bin/python3 /data/roadline-cruise-recovery-c79c68f/control.py rollback --vehicle-disconnected
```

Rollback restores the previous directory and selected settings, leaving assistance
and pedal control disabled. Its normal Panda startup must finish; restoring the
software path alone does not prove firmware recovery. The helper refuses to
overwrite an unknown active path, changed launcher or corrupted snapshot. A
failed pre-switch preparation can leave an inactive runtime copy; inspect status
rather than deleting it or blindly retrying.

Nineteen host tests cover normal start and reboot, real local Git metadata,
interrupted switch and rollback gaps, failed service startup, parameter snapshot
failure, checksum/mode/link tampering, onroad refusal, repeated starts, preserved
calibration and refusal to overwrite externally changed paths. Services and
vehicle hardware are simulated. Bench startup and live stationary checks remain
outstanding; public installer publication and road readiness are unchanged.
