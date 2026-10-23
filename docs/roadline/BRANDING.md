**Draft repair candidate: approved binary media are included.** See [upload status](BRANDING_UPLOAD_STATUS.md).

# Roadline green-and-white branding update

## Included

- The owner's approved 4.5-second, silent, green/white-on-black startup video,
  unchanged from the approved file, plus the approved still and logo.
- Playback in the existing startup spinner only. It plays once and then holds
  the still; the parent can terminate the spinner as soon as startup completes.
  A quick boot can therefore shorten the animation. There is no minimum delay.
- Real startup progress and error/status messages remain visible. The decoder
  has a two-frame queue, one decoder thread, and a startup timeout. Missing or
  invalid video falls back to the still; missing images fall back to a native
  green/white Roadline wordmark. No extra package is added to the dependency lock.
- Roadline home-page title, settings-tab label, welcome text, window title, and
  version label. The home background uses the approved artwork without cropping.
- Removed the old Philly Fork startup module, its two wallpapers, and the old
  red/blue NAP startup logo from this updated source package.

## Deliberately unchanged

Driving control, driver monitoring, safety/firmware, radar/pedal calibration,
parameter identifiers, navigation API contracts, Python package names, upstream
copyright/license notices, and historical provenance documents. Internal NAP
names are compatibility identifiers, not the product's display branding.
The existing onroad layout is unchanged. This is not a new onroad animation.

## Validation and limitations

The source bundle contains the exact approved media; see
`selfdrive/assets/roadline/manifest.json` for SHA-256 hashes.
`python3 -m unittest discover -s tools/roadline -p test_branding.py -v`
runs the standalone tests. These use stubbed native graphics and decoder interfaces;
they check queueing, timeout, single-play/fallback behavior, labels, media hashes,
syntax and protected interface names. FFmpeg separately decoded the original
135-frame MP4 without reporting errors. See the package's `VALIDATION.json`.

This update has NOT been tested on the comma 3X display or in the car. Actual device smoothness and GPU/codec behavior remain unverified.
The download is development source, not a standalone install image. Upstream
Git LFS objects, submodules, model weights, and font files must be obtained from
the original pinned project dependencies; they are not supplied by this bundle.
Do not replace a running installation by unzipping this source into /data/openpilot.

## Repository state

The approved branding source and exact media are integrated into the draft
`roadline-first-drive-fixes` branch. Main, the installed 5de8b00 revision and the
install-readiness branch have not been promoted. Current validation and remaining
release blockers are recorded in [the drive review](DRIVE_REVIEW_2026-10-22.md).
