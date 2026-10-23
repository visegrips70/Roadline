# Approved media recovered

The repair candidate contains all three unchanged approved binary assets in
`selfdrive/assets/roadline/`. They were recovered from the existing media package
and checked against the original manifest before upload. These are actual PNG/MP4
bytes stored in Git, not LFS pointers or regenerated artwork.

| File | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| logo.png | 748335 | 3fee5eb04a58371404db18a6a33ff936d2846d04a8d125b1b7189aac92749dd7 |
| startup.mp4 | 620473 | eee01080bd398f53688b08bed490b55addfdfb22f2a9d03a39b742a83b976265 |
| startup_still.png | 470156 | 23f593fe4fa7a9d81effbdcf3449af9454c91ad20fd69359317c8ed4bb894425 |

The approved source from `roadline-branding-upload` is integrated with the
first-drive repairs, including the newer live lane-position description. Display
labels use Roadline; internal NAP compatibility names and licenses remain intact.
The startup animation runs only in the existing spinner and never delays the
parent's startup completion. Missing media/decoder failures use the still or wordmark.

Run `python3 -m unittest discover -s tools/roadline -p test_branding.py -v`
for the media, fallback, syntax and label checks. The full validation runner also
includes these checks and release preparation tests. Native comma display/GPU
behavior, boot and rollback remain unverified. This branch is not a tested install
release and has not changed the device. See the [drive review](DRIVE_REVIEW_2026-10-22.md)
for the control incident release blockers. No public installer is enabled.
