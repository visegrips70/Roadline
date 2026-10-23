# Panda, pedal, steering and radar installation

Reviewed October 22, 2026 against Roadline candidate
`369fc9d10f82789728f2a94ad6e1e2dd077dd8af`, NAP release
`e99f4dc7508874e639bfa81ad1f1cb1dfaedea09`, and the NAP installation wiki.
These are four different components. A successful software build is not evidence
that any of them has passed a live vehicle check.

| Component | Included in Roadline | Separate vehicle work |
| --- | --- | --- |
| Internal Panda | H7 firmware and recovery bootstub, built from the pinned Panda source plus Roadline's opendbc safety headers; startup signature check and automatic update | Verify the running firmware and CAN health after first boot |
| Comma Pedal | Driver, Bus 0/2 setting, calibration settings and guided calibration tool | Pedal microcontroller firmware is separate; identify the existing board/firmware before deciding it needs an update |
| EPAS steering | NAP backup, patch and restore tools, with the EPAS bootloader asset | A steering ECU flash is a separate, deliberate operation; a Comma reinstall alone does not establish that it is needed |
| Bosch radar | CAN parser/DBC, tracking, settings, and Panda gateway emulation | Verify communication, fault status and physical alignment; investigate radar pairing only if evidence calls for it |

## Build and first boot

Panda is pinned to `NotAutopilot/panda@282fae705ecd16dc94e0978a23b1f0c015303d1d`.
Both the inspected NAP release and Roadline use that Panda revision, but their
opendbc trees differ. `panda/SConscript` includes opendbc safety headers, including
`opendbc_repo/opendbc/safety/modes/tesla_preap.h`. Therefore copying an old NAP
Panda binary is not a substitute for building Roadline's matching firmware.

The normal SCons build includes:

- `panda/board/obj/panda_h7.bin.signed`
- `panda/board/obj/bootstub.panda_h7.bin`
- `opendbc_repo/opendbc/dbc/tesla_radar_bosch_generated.dbc`

The updated `tools/roadline/build_on_device.sh` checks those files and the pedal,
steering and radar support files before writing its success marker. It records
their SHA-256 hashes in `build/roadline-device/hardware-bundle.json`. This is a
file inventory and signed-image-layout check, not RSA authentication, proof of
build provenance, or a live hardware test. The preceding pinned-checkout and
clean-source checks remain required.

`selfdrive/pandad/pandad.py` compares the connected Panda signature with the
built image. It flashes when needed, then verifies the resulting signature.
Starting Roadline can therefore change Panda firmware even while offroad. This
does not flash the pedal board, EPAS controller or radar.

The file-only report can optionally compare the cached startup record:

```bash
python3 tools/roadline/hardware_bundle.py --params /data/params/d
```

Run it from the intended checkout. Its exit status checks bundle files only;
`last_reported_panda.matches_bundle` is a separate result. `PandaSignatures` can
be stale, so even a match does not prove the current Panda is healthy or running
that image. Do not open a second direct Panda connection just to obtain this
inventory while pandad owns the device.

## Preserve settings and identify what survived

The pre-reset backup records pedal enabled on **Bus 2**, with completed
calibration. It also records radar enabled, behind-nosecone enabled and radar
lateral offset **+0.16 m**. These are this vehicle's recorded settings, not
defaults for other installations. Compare the restored settings with the backup
and actual hardware before enabling assistance. The older `nap_params.json`
contains conflicting defaults and must not overwrite the verified calibration.

A reset can remove Comma-side parameters, software and locally saved ECU backups.
The EPAS, pedal and radar have separate controllers; erasing `/data` is not itself
an instruction to reflash those controllers. Their current state is unverified.
The EPAS image shipped in source is not proof that a vehicle-specific backup was
successfully extracted. Preserve an actual confirmed extraction off the device
before any deliberate steering firmware operation.

## Power states are procedure-specific

Ordinary software changes must be offroad with stable power. The inherited NAP
EPAS procedure instead requires the car awake, stationary in Park, with reliable
12 V power. Its warnings require a backup before modifying steering firmware.
Pedal calibration has different preconditions in the actual code: car on,
Neutral, brake held, accelerator untouched. Calibration sends pedal commands;
it must not run automatically during software installation or on a disconnected
bench device. Follow the reviewed on-device procedure only when calibration is
actually needed.

## Radar is part of both the application and Panda

The Bosch radar parser reads CAN bus 1; the pedal Bus 2 setting is unrelated.
`NAPRadarEnabled` selects radar availability and the Panda radar-emulation flag.
`NAPRadarBehindNosecone` adds the mounting-position flag, and `NAPRadarOffset`
adjusts the reported lateral position in the radar interface.

Panda's `tesla_preap_gtw_emulation` translates chassis CAN traffic from bus 0 to
the messages expected by the radar on bus 1. The installer must retain this
matching firmware as well as the radar DBC, interface and `radard` application.
There is no separate radar firmware image/flasher in the inspected release.
The existing radar may already be configured; a Comma reset does not demonstrate
that VIN learning or radar reflashing is required.

After reconnecting the vehicle, verify sustained radar messages, reported faults
and plausible detections with assistance disabled. A disconnected shop bench
cannot establish radar health. Radar detections also do not add friction-brake
control to this pedal/regen installation.

The inherited `Test Radar` and `Calibrate Radar` scripts are not passive software
checks: they open Panda and select ALLOUTPUT while the UI stops pandad. They do
not reproduce the normal `teslaPreap` gateway-emulation path. The inherited
`diagnose_radar.py` also contains older safety flags and source-address mappings.
Do not use those scripts as the sole acceptance test or launch them automatically
from an installer. Live acceptance needs observations of the normal running stack.

## Differences between the wiki and this release

The NAP wiki describes Flash Panda, Flash Pedal and Radar VIN Learn buttons.
Those buttons are absent from the inspected release's settings code and the
Roadline settings code. The pedal wiki also describes a manual accelerator sweep,
whereas `nap_content.py` and `calibrate_pedal.py` require leaving it untouched.
Do not combine these conflicting instructions or promise absent UI actions.

Sources:

- [NAP install guide](https://notautopilot.com/wiki/getting-started/install)
- [Pedal guide](https://notautopilot.com/wiki/hardware/pedal-interceptor)
- [EPAS guide](https://notautopilot.com/wiki/hardware/epas-firmware)
- [Radar guide](https://notautopilot.com/wiki/hardware/bosch-radar)
- [Pinned NAP settings instructions](https://github.com/NotAutopilot/openpilot/blob/e99f4dc7508874e639bfa81ad1f1cb1dfaedea09/selfdrive/ui/layouts/settings/nap_content.py)
- [Pinned NAP startup firmware handling](https://github.com/NotAutopilot/openpilot/blob/e99f4dc7508874e639bfa81ad1f1cb1dfaedea09/selfdrive/pandad/pandad.py)
- Roadline `panda/SConscript`, `selfdrive/pandad/pandad.py`,
  `opendbc_repo/opendbc/car/tesla/preap/interface.py`,
  `opendbc_repo/opendbc/car/tesla/radar_interface.py`, and
  `opendbc_repo/opendbc/safety/modes/tesla_preap.h`.
