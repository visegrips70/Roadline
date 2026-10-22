# Roadline continuation: October 21, 2026

**Status: source uploaded; not cleared for installation or road use.** The
continuation is published to the private `visegrips70/Roadline` repository on
`roadline-install-readiness`. The source commit is
`369fc9d10f82789728f2a94ad6e1e2dd077dd8af`.
Its complete tree matches the locally tested commit; the mapping is in
[`readiness-results/publication.json`](readiness-results/publication.json).
The [clean CI run](https://github.com/visegrips70/Roadline/actions/runs/39617654298)
passed every validation stage. The owner subsequently provided the device
inventory and a successful Comma 3X build result. Boot and hardware validation
remain. This is a development candidate, not a verified device release.

**October 22 recovery update:** after requesting the first Roadline start, the
owner reset the device and later reported NAP reinstalled. Roadline's successful
boot was never established. External settings backup integrity was checked, but
the surviving device directories and current settings are unknown. See the
[hardware installation review](HARDWARE_INSTALL.md) for Panda, pedal, EPAS and
radar requirements. Its new file-inventory tool has separate validation from the
historical source-candidate CI results below.

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
- Resolved all 77 previously reported static findings in the inherited safety
  headers. Byte assembly, CRC and speed conversions now have explicit types;
  hooks use single returns; local state has local scope; MG has its missing
  declaration. Existing steering/Pedal limits, diagnostic allowlists and
  forwarding decisions remain covered by the behavioral tests. No analysis
  rules were suppressed. The checker report's stale command/path heading was
  corrected; its list of checkers was unchanged.
- Added sanitizer checks for CRC/SNA replacement, 98,304 legacy forwarding cases,
  and 172,032 single-byte diagnostic mutations across speed/freshness states.
  Each diagnostic case also checks rejection on the wrong bus and wrong length.
  The tests cover the 40 mph threshold, 250 ms freshness boundary and timer wrap.
- Made the validation runner block dependent tests if the native build fails,
  preventing a stale compiled safety library from producing misleading passes.
  Documentation-only pushes no longer restart the source commit's CI run.

## Evidence

The tested source commit and exact commands are in
[`readiness-results/summary.json`](readiness-results/summary.json). Results are
Linux x86-64 development checks, not ARM/QCOM device operation. The new files in
this report directory are documentation and retained test outputs; the source
revision inside the summary identifies the runtime code that was tested.

| Check | Result |
| --- | --- |
| Full native desktop build, including Panda ARM firmware targets | Passed |
| Focused Roadline / pre-AP / monitoring / device-tool checks | 135 passed, 9 skipped |
| Complete controls and planner suite | 553 passed, 1 skipped |
| Complete safety suite including MISRA mutation checks | 2,893 passed, 1,539 skipped |
| Firmware packet/diagnostic sanitizer tests | Passed; includes 65,536 radar speed/counter cases |
| Dashboard, local environment | 74 passed; 3 errors because AF_UNIX datagram sockets are denied locally |
| Dashboard, first clean GitHub run | All 77 passed on published commit `21519fb`; dashboard source is unchanged |
| Static safety analysis | Passed with pinned Cppcheck 2.17.1 and existing suppression policy |
| Clean CI for source commit `369fc9d` | Passed all six stages, including all 77 dashboard tests and static analysis |
| Comma 3X build of `369fc9d` | Owner-reported SCons completion and exit 0; build marker matched |
| Roadline boot, live CAN/firmware and controlled-course checks | Unverified; device subsequently reset and NAP reinstalled |

Counts overlap between suites and must not be added as a count of unique tests.
Skipped tests are not passes. The complete all-safety run, including randomized
MISRA mutation checks, is retained separately in `readiness-results/all-safety.log`.
Its result and exit code are authoritative. Mutation checks sample two cases;
the unchanged baseline is always checked separately by the validation runner.
The local overall summary remains FAIL because of the three socket-permission
errors; those errors were not skipped or converted into passes. The first CI
summary and dashboard log are retained as `ci-first-summary.json` and
`ci-first-dashboard.log`. That first CI run failed its old static baseline;
its passing dashboard result was not used to declare the newer source passed.

The final [clean CI summary](readiness-results/ci-verified/summary.json) records the
exact published source commit and an overall **PASS**. The full logs remain in the
[GitHub Actions artifact](https://github.com/visegrips70/Roadline/actions/runs/39617654298/artifacts/12354102888).
The downloaded artifact's SHA-256 matches GitHub's artifact digest, recorded in `publication.json`.
Its counts match the local focused, controls and safety counts; all 77 dashboard
tests pass in CI. Subsequent report-only commits do not change the tested code.

## Remaining gates

Passing automated static checks does not establish complete MISRA compliance or
vehicle safety certification. The remaining work is:

1. Re-read the Comma's current NAP revision, AGNOS version, Tesla/Pedal/radar
   settings, calibration and surviving directories following the reset.
2. Preserve the working installation/settings and verify recovery. Inventory any
   surviving pinned build, or rebuild an inactive candidate as necessary. Starting
   manager can automatically flash Panda firmware and requires a reviewed step.
3. Validate boot, model execution, UI, monitoring, CAN health, driver override,
   disengagement and explicit re-engagement before controlled-course checks.

The private key `system/hardware/tici/id_rsa` remains excluded. No credentials,
vehicle logs, or calibration backups are included in the upload. No upstream
repository or active vehicle installation has been modified.
