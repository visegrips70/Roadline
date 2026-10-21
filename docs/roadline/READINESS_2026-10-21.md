# Roadline continuation: October 21, 2026

**Status: not cleared for installation or road use.** The source work is prepared
locally. Uploading the continuation to the private `visegrips70/Roadline`
repository, branch `roadline-install-readiness`, was rejected by automatic
approval review. The reviewer requires explicit approval of that destination
and the updated source/test/report payload in the current conversation.

## Changes prepared

- Recovered the unuploaded planner/turn-gate fixes and test-fixture updates from
  the previous conversation. The source remains based on the pinned NAP pre-AP
  Tesla platform and Pedal/radar configuration.
- Fixed test fixtures that left mocked planner functions installed globally.
  This caused all 18 following-distance simulations to fail when the suite ran
  together, despite passing in isolation. Cleanup now runs even on test failure.
- Made the launcher resolve its own directory and set its Python path before
  the existing MPP reader starts. Removed the unreachable hard-coded ngrok line.
  This does not establish MCU2 route-navigation integration.
- Fixed undefined signed shifts in radar byte assembly and wheel-speed packing.
  The conversion now uses unsigned 32-bit values before shifting.
- Added an in-memory test of the actual firmware radar forwarding code under
  GCC's undefined-behavior sanitizer. It covers all 4,096 input speed codes and
  16 counters, checking four wheel fields, counter and checksum (65,536 cases).
  The old header fails this same test with a signed-left-shift runtime error;
  the corrected header passes. No physical CAN device is opened by this test.
- Separated static-analysis dependency setup from test execution. Tests now use
  a pinned Cppcheck 2.17.1 and compare generated tables without requiring a Git
  repository. All findings remain failures; no safety rules were suppressed.
- Added dashboard tests to the validation runner. The runner records failures
  and never automatically publishes an installation/release branch.
- Added a read-only device report and a guarded, build-only Comma 3X script.
  See [device preparation](COMMA_3X.md). Neither provides an activation shortcut.

## Evidence

The tested source commit and exact commands are in
[`readiness-results/summary.json`](readiness-results/summary.json). Results are
Linux x86-64 development checks, not ARM/QCOM device operation. The new files in
this report directory are documentation and retained test outputs; the source
revision inside the summary identifies the runtime code that was tested.

| Check | Result |
| --- | --- |
| Full native desktop build | Passed |
| Focused Roadline / pre-AP / monitoring / device-tool checks | 133 passed, 9 skipped |
| Complete controls and planner suite | 553 passed, 1 skipped |
| Firmware behavioral safety suite, excluding MISRA tests | 2,891 passed, 1,539 skipped |
| Complete safety suite including MISRA mutation checks | 2,892 passed, 1,539 skipped, 1 failed (unchanged baseline static findings) |
| Radar packet sanitizer test | 65,536 speed/counter cases passed |
| Dashboard | 74 passed; 3 errors because AF_UNIX datagram sockets are denied by the local environment |
| Static safety analysis | Failed: 77 remaining MISRA/style findings; the reported signed-overflow error is fixed |
| Clean CI for this continuation | Blocked by upload approval; no passing CI result claimed |
| Comma 3X build, boot, CAN/firmware and controlled-course checks | Not performed |

Counts overlap between suites and must not be added as a count of unique tests.
Skipped tests are not passes. The complete all-safety run, including randomized
MISRA mutation checks, is retained separately in `readiness-results/all-safety.log`.
Its result and exit code are authoritative; passing a mutation check does not
clear the failed baseline static analysis.

## Remaining gates

1. Review and resolve the 77 static findings in the inherited Tesla pre-AP,
   Tesla legacy and MG safety headers. The unsigned packing fix removes the
   demonstrated overflow but does not constitute full MISRA compliance.
2. Publish the exact prepared source/tests/build scripts/reports to the private
   Roadline readiness branch and run clean CI, including the real dashboard
   socket tests and static safety analysis. No upstream repository is a target.
3. Read the installed Comma's current NAP revision, AGNOS version, Tesla/Pedal/
   radar settings and calibration. The 2013 pre-AP Model S target is known;
   the exact installed software and current hardware configuration are not.
4. Preserve the working installation/settings and verify recovery, then compile
   the pinned candidate on the actual disconnected Comma 3X. Starting manager
   can automatically flash Panda firmware and requires a separate reviewed step.
5. Validate boot, model execution, UI, monitoring, CAN health, driver override,
   disengagement and explicit re-engagement before controlled-course checks.

The private key `system/hardware/tici/id_rsa` remains excluded. No credentials,
vehicle logs, or calibration backups are included in the intended upload.
