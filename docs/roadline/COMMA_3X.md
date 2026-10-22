# Comma 3X preparation

Roadline is still an installation candidate in development. A desktop build and
offline tests do not establish device operation. Do not use the historical NAP
installer URL as a Roadline installer. The private Roadline repository also cannot
be assumed to work with an anonymous custom-installer URL.

The source candidate is `369fc9d10f82789728f2a94ad6e1e2dd077dd8af` in
`visegrips70/Roadline`. Its [clean validation run](https://github.com/visegrips70/Roadline/actions/runs/39617654298)
passed the build, focused checks, controls, dashboard, complete safety suite and
static analysis. This pins the software candidate for compatibility review;
the owner subsequently reported a successful build on the Comma 3X (exit 0).
Roadline boot and operation have not been verified. A later reset/reinstall means
the old candidate and recovery directories must be inventoried again.

See [Panda, pedal, steering and radar installation](HARDWARE_INSTALL.md) for the
component inventory, firmware handling, saved configuration and discrepancies
between NAP's wiki and the inspected release.

## Read the existing installation

Use `tools/roadline/device_report.py` with the existing Comma's Python interpreter.
It uses the standard library only. It reads the hardware model, AGNOS version,
installed branch and revision, and a fixed list of NAP settings. It does not import
vehicle-control modules, touch CAN, flash firmware, change settings, or collect
VINs, account tokens, driving logs, or key files.

```bash
python3 /path/to/device_report.py > /tmp/roadline-device-report.json
```

Exit 2 means the report lists an unresolved compatibility condition; the JSON is
still produced. Exit 0 only means those inventory checks found no blockers. It
never means that driving is approved. Share that report for compatibility review,
or provide the Software screen and Tesla/Pedal/Radar settings screens.

The candidate source targets AGNOS 17.2 and Python 3.12.3–3.12.x. The exact current
NAP revision, Pedal calibration/bus, radar configuration and car wiring must be
reviewed before switching. Settings must be preserved rather than guessed from
the software defaults. No new friction-brake or iBooster capability is provided.

## Compile without switching the active software

After the reviewed source revision passes CI, prepare a separate authenticated
checkout under `/data`, with its pinned submodules and Git LFS assets. Keep the
existing `/data/openpilot` intact. Power the Comma on a bench, disconnected from
the vehicle, for the first device build. A missing off-road-state file is a stop
condition; do not create or falsify it to get past the check.

Run `tools/roadline/build_on_device.sh` with the reviewed full commit SHA from that
candidate checkout. The script rejects other hardware, an unexpected OS, a dirty
or mismatched checkout, missing assets and the active installation directory.
It runs the hardware's own minimal build and saves a log. It does not activate
Roadline, start manager/pandad, install dependencies, update AGNOS, or flash the
Panda. The updated build tool also records the required Panda firmware and
pedal/steering/radar files before marking a build complete. The earlier device
build of `369fc9d` predates that additional inventory check.

## Before activation

Preserve the known-working NAP software and its exact revision, `/data/params`,
`/data/nap_params.json`, and the existing dashboard/configuration locally. Params
may contain credentials, so keep the complete backup on your own device/computer;
share only the allowlisted report. Establish a recovery method that remains usable
if the UI cannot boot. A previous session supplied a guarded switch/rollback
script, but its device-side copy and backup are unverified after the reset. Do
not reuse its paths without checking the new installation first.

Starting manager can automatically flash Panda firmware. After the device build,
the first boot and firmware match, UI/dashboard imports, driver monitoring, CAN
health, calibration, override and disengagement behavior need explicit validation.
Road use remains blocked pending hardware and controlled-course verification.
