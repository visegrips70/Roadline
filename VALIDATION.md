> Historical initial-snapshot report. See [current readiness](docs/roadline/READINESS_2026-10-21.md) for the continuation checks and blockers.

# Roadline 0.1 development validation

Status: **not ready for installation or road use**. Checked on 2026-10-21 on Linux x86-64,
Python 3.12.13. Read the machine-readable report and logs alongside this document.

## What changed

- Parked-only lane-position setting in whole centimetres, from -30 (left) to +30 (right).
  Old NAP presets are retained until a new setting is saved; zero explicitly means center.
- The desired centerline is clamped at least 1.25 m from each detected lane line. This is
  a geometric target bound, not a guarantee about the vehicle's actual position or obstacles.
- Existing 20–70 mph, confidence, curvature, override, acceleration and jerk gates remain.
  This adjustment is for ordinary lane following; it does not reshape intersection turns.
- Driver monitoring restored to the NAP baseline: 11-second active timeout and 30-second
  passive timeout. These are internal awareness budgets, not promised alert delays.
  Warning timing, recovery, and other monitoring logic remain upstream behavior.
- Firmware safety again blocks steering for EPAS hands-on level 3 or relevant EPAS
  rejection faults. An explicit-rearm regression test exercises the actual safety library.
- A local-log report distinguishes head pose, eyes, phone classification, missing face,
  uncertainty and monitoring mode. It does not diagnose false positives by itself.

## Results and limits

The full native `scons -j 2` build passes. This includes native Python bindings, the control
solvers and the Panda firmware targets selected by the source tree. It is not a comma 3X
ARM userspace build or a flashed-device test. A CasADi compatibility warning appeared during
solver generation; it was not a build failure.

The final focused run has **127 passes and 9 skips**, including pre-AP safety, lane,
UI-callback, local-diagnostic, monitoring and eight NAP configuration combinations.
The skipped cases are not counted as validation. The logs retain the exact tested revision.
Focused lane, UI-callback, local-diagnostic and monitoring checks pass. The lane simulation
contains 27 idealized straight-road cases (12/20/28 m/s, 0.1/0.3/0.5 second command delay,
and -10/0/+10 cm preference), starting 25 cm left. It uses a bicycle model with actuator lag;
it does not run the neural driving model or reproduce real camera/calibration behavior.
The target has an existing 3 cm deadband: a 1 cm preference step does not guarantee 1 cm of
physical movement. Screen rendering was not tested; actual settings callbacks and Params were.

The broader inherited feature suite currently has **131 passes and 6 failures**. All six
also reproduce with the original controlsd file; the other tested modules involved are
unchanged from their pinned sources. The failures are retained, not skipped or rewritten:

| Test | Mismatch requiring review |
| --- | --- |
| `test_legacy_level_three_and_low_speed_torque_allowance` | Expected takeover-torque threshold differs from current source |
| `test_no_blinker_cannot_apply_an_explicit_model_turn_even_with_floor` | Explicit model turn without indicator does not disable lateral control as expected |
| `test_curved_or_misaligned_path_cannot_reacquire` | Expected takeover latch behavior differs |
| `test_renewed_driver_input_restarts_quiet_interval` | Reacquisition timing differs |
| `test_signal_cannot_keep_centered_takeover_latched` | Reacquisition occurs sooner than expected |
| `test_brake_held_straight_prediction_receives_intent_through_speed_noise` | Moving brake input does not cancel turn desire as expected |

The complete safety run has **2,890 passes, 1,539 skips and 3 failures**. Two MISRA mutation
checks fail because the environment cannot run their sudo-based dependency setup. The MG
`test_against_torque_driver` assertion also fails; Roadline has not changed MG code and has not
established its root cause. The pre-AP Tesla safety tests pass. Skipped tests are not passes.

Docker is unavailable here, so the upstream Docker safety gate has not been completed.
System-package setup is blocked by the environment's user/group restrictions; those
restrictions were not bypassed. The GitHub workflow is prepared to run a clean Docker build,
but no GitHub CI result is claimed until it actually runs.

## Remaining release gates

1. Resolve the six inherited feature mismatches against explicit, reviewed intended behavior.
2. Complete the clean Docker/native safety checks and investigate the MG failure.
3. Build and boot the exact revision on a comma 3X; verify dashboard imports, UI, monitoring,
   CAN health, steering faults, driver override, disengagement and deliberate re-engagement.
4. Review actual logs for the left bias and false attention alerts. Verify mounting and
   calibration before selecting an offset. No private driving logs have been obtained here.
5. Perform controlled closed-course validation of both directions, narrow lanes, lane loss,
   curves, transitions, handoff and navigation failure cases with qualified oversight.

No Roadline installer, road-ready release, driver-monitor bypass, or unattended-driving
claim is provided. Philip's navigation and cornering features are inherited experimental
code; this work does not establish FSD capability, improved cornering, or reliable route execution.

## Reproduce on a development machine

Clone the published Roadline source with submodules and Git LFS, then run:

```bash
git submodule update --init --recursive
git lfs pull
uv sync --frozen --extra testing
.venv/bin/python tools/roadline/validate.py
```

The runner builds and executes all four groups, records every exit status in
`build/roadline-validation/summary.json`, and exits nonzero if any group fails.
It neither flashes firmware nor sends CAN traffic. Do not run development validation
on a device controlling a moving vehicle.

## Packaging note

The distributed snapshot is an independently rooted repository. Its runtime files
match the tested working copy. Packaging also preserves the original CRLF bytes
of `ESR.dbc` and `mazda_rx8.dbc`; the tested Git revision had normalized those
index entries to LF even though the actual tested working files retained CRLF.
Other post-validation additions are documentation and saved reports.
