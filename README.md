# Roadline

A NAP-based development fork for pre-Autopilot Tesla Model S and comma 3X.

**Development source only. Not ready for installation or road use.**
The desktop/Panda firmware build, control tests and static safety analysis pass.
The latest clean CI run and actual Comma 3X validation remain gates. No validated Roadline
installer is available. See [current readiness](docs/roadline/READINESS_2026-10-21.md)
and [Comma 3X preparation](docs/roadline/COMMA_3X.md).

Publication note: `system/hardware/tici/id_rsa` remains excluded. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) records the initial publication and omission; the [current readiness report](docs/roadline/READINESS_2026-10-21.md) identifies subsequent source changes and their validation.


Roadline starts from Philip's `openpilot-preap` main branch, retaining NAP's
pre-AP Tesla interface, Comma Pedal configuration, radar options, and existing
navigation/cornering features. It does not convert this hardware into Tesla FSD.

## Added in this development version

- **Lane position:** a parked-only setting in centimetres, -30 left to +30 right.
  It adjusts the existing bounded lane-centering assist. Existing NAP presets
  carry over until a new preference is saved. It does not alter camera calibration.
- **Attention diagnostics:** a local-log summary of the classifier's reasons for
  an attention alert. It can help investigate false alerts without suppressing them.
- **Restored protection:** baseline NAP attention timeouts and the pre-AP firmware
  checks for driver steering override and relevant EPAS faults.
- **Reproducible checks:** UI callbacks, 27 idealized straight-road simulation cases,
  NAP/Pedal/radar configuration combinations, monitoring and safety tests, plus a
  workflow that reports failures instead of promoting a release automatically.

The lane adjustment requires NAP Lane Centering to be enabled and confident lane
lines at ordinary road speeds. It yields to override and maneuver gates. A 1 cm
setting step is a preference, not a promise of 1 cm tracking accuracy. Mount and
calibration problems must be evaluated separately; rotating the device is not
part of this setting.

## Compatibility and installation status

The base is specifically NAP's `TESLA_MODEL_S_PREAP` platform and `teslaPreap`
safety mode. NAP Pedal calibration and CAN-bus parameter names are retained.
The software honors radar-enabled/disabled settings; this is not a radar repair.
This version adds no iBooster control and cannot add friction-brake authority to
an accelerator/regen-only installation.

Compatibility with an individual installation still requires its current NAP
branch/commit, Software screen, Tesla settings and hardware configuration. Before
any future upgrade, preserve the existing settings/calibration and a verified
rollback path. No device upgrade, firmware flashing or calibration changes have
been performed as part of this work.

## Development

See [VALIDATION.md](docs/roadline/VALIDATION.md) for build/test commands and release
gates, and [PROVENANCE.md](docs/roadline/PROVENANCE.md) for exact upstream revisions.
All source changes belong to Roadline; no upstream repositories are modified.

After building the native dependencies, a read-only local log report can be run:

```bash
.venv/bin/python -m tools.roadline.review_log /path/to/qlog.zst
```

Inputs must already be local files. The report uploads nothing and includes no
camera images, GPS, route identifiers or absolute timestamps. Classification
percentages alone cannot prove whether an alert was justified.

## Attribution

Based on Philip's work, NotAutopilot, comma.ai openpilot, and their contributors.
Original licensing and attribution are preserved. Historical upstream material
is retained in [UPSTREAM_README.md](docs/roadline/UPSTREAM_README.md); its installer
links are for upstream NAP, not for Roadline.
