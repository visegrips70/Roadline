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

## Passive startup follow-up

The operator subsequently reported the c79c68f runtime still selected after the
requested reboot, with assistance/pedal control disabled, the previous install
preserved and saved calibration matching. A disconnected 10-second observation
received current, valid Panda/device/manager messages, no reported Panda faults,
and `noOutput` with controls disallowed. The SPI counter increased by five;
a later 30-second log sample contained two NACK messages and no captured final
transfer-failure or timeout message. This does not prove the absence of other
communication errors or establish actuator health.

The first parked vehicle observation received current, valid `carState` and
Panda messages, zero speed, Park gear, CAN ignition, no reported Panda/steering
faults and no expected process reported stopped. However, Panda remained in
`elm327` diagnostic mode with controls disallowed. Source inspection found that
`ControlsReady` was only written by `controls_update`, which passive mode never
calls. This leaves the passive `noOutput` configuration waiting in pandad.

The follow-up source change signals readiness immediately after the passive
`CarParams` configuration has been persisted. It does not call `CI.init` or
`CI.apply`; active-mode initialization and firmware are unchanged. Seven isolated
tests execute the real constructor/loop methods with real CarParams serialization
and mocked transport/persistence. Four passive regressions failed before the
change; all seven pass afterward. The tests also cover failed parameter writes
and failed active interface initialization. The focused CI suite already includes
their directory. Device installation/verification of this follow-up is pending.

The inherited Pre-AP `standstill` value is derived from stock cruise state and
can be false while zero speed and Park are reported. Also, `brakePressed` is
deliberately suppressed in the published car state to retain steering when the
driver brakes. Neither published field alone validates the physical brake or
standstill signals. Raw brake, pedal and steering input checks remain required
before any engagement test. No assistance settings or public installer release
have been promoted by this follow-up.

The operator's subsequent readback confirmed `FirmwareQueryDone=1`, absent
`ControlsReady`, passive `TESLA_MODEL_S_PREAP`, and requested `noOutput`, while
the vehicle was awake. This matches the source defect above. The correction is
published in `99f383b43ecd7c97a976ef9ec4dae40231d645f0` (including preserved
car-daemon executable mode).

`tools/roadline/apply_passive_startup.py apply` installs only that exact car-daemon
file into the existing c79c68f candidate. Run it as root only while `IsOnroad=0`
and the existing assistance/pedal/radar/navigation settings remain disabled.
It validates hardware/OS, base release, current firmware-file hash, candidate
path and recovery state. Both old and new source-file hashes are pinned. It
backs up the original file to the first-start recovery directory, stops the
service, rechecks the guards, atomically replaces the file preserving ownership and permissions,
and requests a service restart. It writes no parameters and never sets
`ControlsReady` itself. The corrected car process performs the normal handshake.

The base release identifier remains c79c68f. `roadline_local_changes.json` records
the applied file's source revision and hash, explicitly with `road_ready=false`.
This locally modified runtime is not a pristine publishable release artifact.
The original package, previous installation and firmware files stay untouched.
The same helper's `rollback` action restores just this file while offroad; the
existing `control.py rollback --vehicle-disconnected` still returns the entire
candidate to the previous installation. Normal full rollback precautions apply.

Thirty-five transaction tests use temporary files and simulated service calls,
covering apply/rollback, repeat apply, wrong/missing settings, unknown content,
failed restart, interrupted file replacement, missing backup, vehicle wake during
stop, external edits and wrong active paths. They pass together with the seven
startup regressions. Checksums also reproduce the exact published file from the
actual c79c68f baseline. No test here sends CAN or establishes hardware health.
After applying, an awake, parked, assistance-disabled observation must confirm
fresh Panda `noOutput` with controls disallowed and `ControlsReady=1`.

The first device update attempts stopped in initial validation before backup or
service stop. Navigation maneuvers first needed to be disabled; after that, the
operator verified that both installed and pristine-package `card.py` had the
expected original SHA256 but permissions `0775`. The updater had incorrectly
required exactly `0755`. It now accepts either executable mode and preserves the
installed mode on apply, rollback and failed-restart recovery. Other permissions,
including world-write and special bits, remain rejected; exact source hashes and
all offroad/disabled-state checks remain required. Contents and permission
failures now have separate messages. Regression tests reproduce the original
`0775` failure and cover both modes, rejected modes and a permission change during
service stop. The car-daemon correction itself is unchanged. Successful device
application and the subsequent live passive-mode check remain pending.

The operator subsequently applied the correction successfully with the expected
new source hash and preserved `0775` permissions. A 15-second awake, parked
observation confirmed `FirmwareQueryDone=1`, `ControlsReady=1`, assistance and
pedal control disabled, and fresh valid Panda and car messages. Panda reported
`noOutput`, controls disallowed, CAN ignition, no faults and no lost heartbeat;
car state reported valid CAN, no timeout, zero speed and Park. This confirms the
passive-startup handshake on this device. The single SPI counter reading does
not establish an error rate or resolve the earlier communication observations.

`tools/roadline/observe_parked_inputs.py` provides the next read-only, 45-second
input capture. It subscribes to existing CAN/car/Panda streams, writes no Params,
opens no Panda hardware handle and publishes no CAN. It requires current valid
Park/zero-speed data, live noOutput/controls disallowed and all six assistance
flags disabled throughout. Prompts cover rest, manual brake press/release,
light accelerator press/release in Park, and gentle steering input. The report
uses raw bus-0 brake/steering/factory-pedal messages and bus-2 pedal feedback,
rejects malformed/checksum-invalid frames where checksums are defined, reports
missing signals explicitly, and retains pedal status and counter observations.
It does not interpret a pedal fault status as healthy or establish brake,
steering-disengagement, longitudinal-control or actuation performance. Review
the resulting input report before planning an active-control test.

The operator's first 45-second input capture observed raw brake status 1/2 and
returned to 1, changing steering angle/torque, and 4,395 fresh bus-2 pedal
messages. Both pedal sensor channels responded, all 4,394 counter transitions
were consecutive, and the pedal status remained 5 (`FAULT_TIMEOUT`). This is
consistent with the current noOutput/no-command condition; pedal fault clearing
and actuation remain untested. EPAS reported status 0 (`EAC_INHIBITED`) and error
4 (`EAC_ERROR_TMP_FAULT`), so responding steering sensors do not establish
steering-control availability or a successful takeover/disengagement test.

The capture helper incorrectly rejected every factory-pedal `DI_torque1` frame
by assuming the same address-sum checksum as EPAS/pedal feedback. Reinspection of
the earlier private recording found a stable additive residual of 0x07 in all
58,848 factory-pedal frames, versus 0x09 assumed from address 0x108. This observation
is not a verified general checksum specification. The helper now decodes those
raw diagnostic values with `checksum_validation=not_verified` and
`bad_checksum=null`, and reports the observed residual distribution. It no longer
labels them as corrupted CAN. BrakeMessage similarly reports checksum checking
as not defined by the DBC. EPAS and interceptor checksum rejection remains in
place. No runtime decoder, Panda safety hook or actuator logic was changed.

The corrected helper also reports EPAS steering-fault/reduced-assist bits and
offers `--accelerator-only` for a 20-second parked repeat with the same passive
guards. Three new regressions cover captured factory-pedal bytes, an unknown
residual without claiming integrity, and rejection of a bad steering checksum.
All 76 focused tests pass locally. Offline replay recovered all 58,848
factory-pedal observations (0 to 40 percent in the earlier recording), while
14,712 EPAS and 57,472 interceptor messages passed their existing checksum checks.
The earlier recording does not replace the current parked accelerator repeat.
