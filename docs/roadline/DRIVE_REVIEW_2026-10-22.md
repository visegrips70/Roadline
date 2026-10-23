# First vehicle drive review — October 22, 2026

**Release blocked. Do not install these draft corrections for another assisted road test.**
The owner reported an unexpected right turn with a left signal, steering takeover
that did not cancel engagement, repeated 60-mph cruise selection, and failed
re-engagement. The supplied compact logs corroborate the key symptoms. No device
changes, firmware flashing or additional driving were performed for this review.

## Evidence and limitations

The supplied archive contains 29 qlogs: six segments from route 7, two from route
8 and 21 from route 9. Route 9 has driving enabled and radar unavailable; the
preceding two routes were passive. All identify commit
`5de8b005d6f34d730815966fdb2875374408bf61`. The init record also marks the checkout
dirty, so the commit identifier alone is not proof that every running file was
identical to that commit. The relevant local engagement/car-state source blobs
were compared with the exact GitHub revision and match.

One trailing event in route 9 segment 20 is incomplete, consistent with a file
copied while logging was still in progress. Complete preceding messages were
recovered. The incidents below are in earlier complete segments. Raw logs,
credentials, coordinates, video and device identifiers are not included here.

Times below use the device's recorded clock converted to America/Chicago (CDT).
Qlogs are sampled and topics are asynchronous: snapshots must not be treated as
frame-exact CAN proof. Full rlogs are still required for the direction incident
and exact hardware/software disengagement ordering.

| Observation | Recorded evidence | Interpretation |
| --- | --- | --- |
| Unexpected 60-mph target | About 6:30:09 p.m. at 31.7 mph; about 6:32:59 p.m. at 13.9 mph; about 6:36:15 p.m. at 30.8 mph | The selected target jumps to about 60 mph. This is a setpoint, not evidence the car reached 60 mph. |
| Driver takeover mismatch | Controls Mismatch at about 6:31:49, 6:33:59 and 6:37:51 p.m. | Panda permission is withdrawn while the application remains enabled; raw CAN is needed to distinguish hands-on level from rack-rejection triggers. |
| Missing full disengage flag | 348 sampled `steeringPressed=true` car-state records; `steeringDisengage=false` in all 12,450 car-state samples | Matches the source forcing the raw disengage flag false. Sample count is not a count of separate interventions. |
| Wrong-direction steering | Around 6:33:53–6:33:55 p.m., left indicator true/right false while positive (rightward) curvature is requested; measured steering moves right | Supports the reported wrong-direction maneuver. Full model desires, navigation decision state and CAN timing are not in the compact record. |
| Failed re-engagement | After the second mismatch, software cruise remains true and `cruiseMismatch` recurs despite stalk events; cancel events around 6:36:13 precede a new enable around 6:36:15 | A stale cruise latch prevents a fresh rising enable edge. This was not an unsolicited restart: the owner confirms pulling the stalk again. |
| Radar disabled | Route 9 `radarUnavailable=true`, Panda `teslaPreap` parameter 5 | Pedal plus nosecone flag, with radar-emulation bit absent. This drive does not establish radar health. |

## Narrow draft corrections

1. Restore the application steering-disengage flag to match Panda's raw hands-on
   level 3 / EPAS rejection conditions. Report actual EPAS rejection as a temporary
   steering fault rather than overwriting it with false.
2. Cancel the software cruise FSM on detected driver steering as well as raw
   disengagement; ignore engagement gestures while the override is held. The FSM
   and controller share the existing takeover effort thresholds, including the
   direct signaled-turn path before the filtered pressed flag becomes true.
3. Capture current measured speed, rounded to the display unit, on engagement.
   Remove the unvalidated `/dev/shm/mpp_speed_limit` target substitution and its
   automatic updates. Manual stalk speed changes remain available.
4. Remove the legacy dashboard offset/trim addition to the reported cruise target.
   Those legacy dashboard fields no longer affect this Pre-AP target; their UI
   cleanup belongs with the broader branding/settings work.
5. Require the application's enabled flag before allowing pedal actuation or an
   enabled zero-torque hold. A stale software cruise latch must not issue enabled
   pedal hold commands after the application disables.
6. Remove the controller's timed steering reacquisition after quiet driver effort.
   Latch detected takeover at the actuator controller and disable both steering
   requests and pedal output. Require observed full application/cruise
   disengagement before accepting a fresh engagement. Apply the same blocked
   lateral state to synthetic turn-signal controllers. Normal EPAS power remains
   enabled so manual power steering is retained.
7. Preserve the requested brake behavior in pedal mode: brake input pauses speed
   control while lateral assistance remains engaged. Steering takeover while
   braking still cancels both axes and clears the brake/throttle resume state.

The effort thresholds and highway steering-pressed filter are inherited, not
newly validated takeover latency limits. Actual driver effort and cancellation
timing still require bench and controlled vehicle validation.

These changes leave Panda limits and mismatch alerts intact. They do not fix or
validate the wrong-direction path, guarantee all re-engagement scenarios, enable
live lane trim, establish Tesla MCU2 route access, or configure automatic updates.

## Validation

- New regression checks first reproduced 13 failures against the prior source.
- Focused real car-state / engagement / controller tests: 69 passed, with four
  unittest subtests also passing. Counts overlap with the broader suite.
- Initial broader controls, Pre-AP and Tesla Pre-AP Panda tests: 754 passed, nine skipped,
  with 200 unittest subtests also passing. The initial run found two old controller
  test doubles missing `enabled`; both now explicitly describe enabled operation,
  and the complete suite was rerun successfully without changing their assertions.
- The follow-up controller change replaces obsolete tests that expected automatic
  steering handback with full cancellation/fresh engagement expectations. Added
  checks decode actual packed steering and pedal messages, including stale enable
  flags, low/high-speed takeover, EPAS rejection, brake-only input, and steering
  takeover while braking.
- Follow-up full suite: 764 passed, nine skipped, 200 subtests passed, and one
  new test-fixture failure. Empty input CAN made the simulated pedal time out,
  so the test incorrectly expected a disabled heartbeat on every 20-ms slot
  instead of the inherited 1-Hz timeout cadence. The command-routing fixture now
  explicitly supplies fresh pedal feedback. No production code changed for this
  correction. Rerunning all 30 first-drive takeover/brake tests passed, including
  that failure; the broader suite was not repeated after this fixture-only fix.
- `git diff --check` passed. These are local software tests, not evidence that the
  vehicle takeover behavior or wrong-direction maneuver is corrected.
- Clean CI, new device build, actual takeover timing and closed-course acceptance:
  not established for this draft.

Reproduction from the repository root (with the project dependencies installed):

```sh
python -m pytest -n 0 selfdrive/controls/tests selfdrive/controls/lib/tests \
  opendbc_repo/opendbc/car/tesla/preap/tests \
  opendbc_repo/opendbc/safety/tests/test_tesla_preap.py -q
```

## Required next evidence

Full `rlog.zst` files from route 9 segments 3, 5, 6, 8 and 9 cover the first
mismatch, wrong-direction maneuver, blocked stalk attempts, successful recovery,
and the last mismatch. Preserve the complete recordings and current source.
The wrong-direction defect remains a release blocker even if all unit tests pass.

## Other requested work

Live lane-position trim is requested: 1-cm left/right increments, explicit center,
bounded gradual application and visible preference. It is not implemented here.
Do not enable it before resolving takeover and direction faults. MCU2 navigation
needs a verified route-data interface. Branding and direct-download/update work
must preserve upstream licenses and remain separate from a tested release channel.

## Subsequent repair work — October 23, 2026 UTC

GitHub Actions run [39879373978](https://github.com/visegrips70/Roadline/actions/runs/39879373978)
completed clean development validation successfully for commit
`12498d1f5b016c0cb071b181f03f5ee17d7a0865`, including the native build and
validation runner. This does not establish vehicle behavior.

A further draft adds an independent sharp-turn direction veto that does not
depend on model desire classification or navigation-decision freshness. At up to
25 mph, an opposite-indicator curvature request of magnitude 0.02 or greater
raises a dedicated immediate-disable/no-entry event. The actuator controller also
checks the final request and blocks both steering and pedal commands. The fault
remains latched after indicator release or a subsequent good prediction; clear
cruise fully before a fresh engagement. It never substitutes an invented path.
Small corrections, unsignaled bends, and high-speed road following retain their
existing behavior; these boundaries still need replay and vehicle validation.

New regressions cover the recorded rightward-request values with absent or
ambiguous model desires, mirrored right-indicator cases, malformed numeric input,
supervisor cancellation, stale cruise flags, and decoded steering/pedal CAN.
These new checks have not yet run. The local execution environment is unavailable;
the draft PR is being validated by GitHub Actions. No vehicle files were changed.
The full rlogs are still required to establish the incident's complete cause.

The next draft also supplies persistent dashboard pairing initialization during
startup and live 1-cm lane-preference buttons. The controller now accepts that
preference while active, through the unchanged lane-centering health/geometry,
acceleration and jerk limits. Tests cover persistence/migration failures, actual
HUD callbacks, bounds/debounce, and preference reversals under the existing output
limits. Two older actuator test doubles now explicitly include zero curvature;
production direction validation was not relaxed for incomplete mocks.
See [navigation and lane-position notes](NAVIGATION_AND_LANE_POSITION.md).
No new tests are claimed passed until their GitHub run finishes.
