# Roadline source provenance

Roadline is an independent development fork. No changes have been pushed to its source projects.
Original licenses and attribution remain in place.

| Component | Source | Pinned revision |
| --- | --- | --- |
| openpilot base | philipr144-create/openpilot-preap, main | `6f7fecb69a301fe553bd603994683dabc0f5415a` |
| opendbc base | philipr144-create/opendbc-preap | `31da4137f2ce06702bc595a05689d537f046bb70` |
| Dashboard | philipr144-create/NAP-Dash | `269c421628c7e874e1daa84e17a38b83f3ccb7b2` |
| Panda | NotAutopilot/panda | `282fae705ecd16dc94e0978a23b1f0c015303d1d` |
| Messaging | commaai/msgq | `ed2777747d60de5a399b74ef1d4be4c1fb406ae1` |
| Rednose | commaai/rednose | `6ccb8d055652cd9769b5e418edf116272fde4e09` |
| WebRTC | commaai/teleoprtc | `389815b8ca5302ce7c1504b7841d4eb61a8cd51b` |
| Tinygrad | tinygrad/tinygrad | `2f55005ad93c777cca69b20dddc28c7f02f0eb01` |

The opendbc gitlink is replaced by its tracked source files so Roadline's safety restoration
lives entirely in this repository. It is not a patch pushed to a separate opendbc repository.
Generated build files are excluded. The upstream opendbc license is preserved.

The original absolute `server -> /data/server` symlink is replaced with a pinned public
dashboard submodule. This makes imports reproducible on a development machine; it does not
establish that every dashboard service works on a comma. Its independent runtime dependencies
and device startup still need validation.

Inherited GitHub workflows are archived in `.github/upstream-workflows/`. Only Roadline's
validation workflow is active in this new project. There is no automatic deployment or
release promotion. Historical upstream README content is kept in `docs/roadline/UPSTREAM_README.md`.

Roadline is packaged as a new repository root commit with no upstream history. The
exact source revisions above preserve provenance. Imported source bytes, aside from
the two documented pre-AP safety files, match the pinned opendbc tree exactly.
