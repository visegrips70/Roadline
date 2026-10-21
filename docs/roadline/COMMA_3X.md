# Comma 3X preparation

Roadline is still an installation candidate in development. A desktop build and
offline tests do not establish device operation. Do not use the historical NAP
installer URL as a Roadline installer. The private Roadline repository also cannot
be assumed to work with an anonymous custom-installer URL.

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
Panda. **No specific revision has been cleared for this step yet.**

## Before activation

Preserve the known-working NAP software and its exact revision, `/data/params`,
`/data/nap_params.json`, and the existing dashboard/configuration locally. Params
may contain credentials, so keep the complete backup on your own device/computer;
share only the allowlisted report. Establish a recovery method that remains usable
if the UI cannot boot. No activation or rollback command is supplied until the
actual installation has been inspected.

Starting manager can automatically flash Panda firmware. After the device build,
the first boot and firmware match, UI/dashboard imports, driver monitoring, CAN
health, calibration, override and disengagement behavior need explicit validation.
Road use remains blocked pending hardware and controlled-course verification.
