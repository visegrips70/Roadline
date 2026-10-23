# Draft source upload: media pending

The branding Python source and text changes are uploaded on this development branch.
The exact approved binary assets have NOT been transferred to GitHub. Do not merge
this draft into an install branch or use it as a device-ready build.

Required directory: `selfdrive/assets/roadline/`

| Missing file | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| logo.png | 748335 | 3fee5eb04a58371404db18a6a33ff936d2846d04a8d125b1b7189aac92749dd7 |
| startup.mp4 | 620473 | eee01080bd398f53688b08bed490b55addfdfb22f2a9d03a39b742a83b976265 |
| startup_still.png | 470156 | 23f593fe4fa7a9d81effbdcf3449af9454c91ad20fd69359317c8ed4bb894425 |

These are the unchanged approved files in the downloadable branding kit and
combined Roadline development stack. Upload the actual bytes, not LFS pointers,
links, regenerated artwork, or base64 text saved with PNG/MP4 extensions.

The full local source package with all three media files passed 28 branding tests,
38 release-gate tests, and 14 URL-verifier tests before this source upload. Those
are synthetic local tests, not comma hardware tests. The media/hash tests cannot
pass in this GitHub draft until the missing files are uploaded. The import checks
only source syntax and the 52 preparation-tool tests on GitHub.

After all three files are present, run `python3 tools/roadline/test_branding.py`,
then the complete development build and the remaining native/bench release gates.
No installer URL, publication, firmware flash, device update, or driving approval
is enabled by this draft. Main, the install branch, and first-drive fixes are
not modified. Internal NAP compatibility names and licensing are preserved.
