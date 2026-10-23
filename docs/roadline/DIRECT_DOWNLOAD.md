# Roadline direct-download status

The native 2fbfa0c installer and runtime are built. The operator observed the
Roadline interface, and the post-reboot inspector confirmed the previous
installation, exact launcher, all 30 compared settings, and all 3,892 original
package files. Assistance and automatic updates remain disabled.

The **installation-test staging link is live**:

https://raw.githubusercontent.com/visegrips70/Roadline/roadline-installers/installer

Use this URL at the comma's **Custom Software** setup screen. NAP does not have to
be installed first: this downloads the complete Roadline runtime. The target is
comma 3X on AGNOS 17.2. Keep the vehicle harness disconnected and use stable bench
power during the first installation test. Do not engage assistance based on this
publication result.

[Publication workflow](https://github.com/visegrips70/Roadline/actions/runs/40017050346)
passed package reconstruction, all 63 tooling tests, anonymous branch access, and
the ARM64 installer download/checksum check. The runtime commit is
`f72bd877ee3e6b43c644587f95f9df0a9bdc91c8`. The receipt is
`release/roadline/candidates/2fbfa0c-publication.json`.

A clean setup installation on the physical device has not yet been tested.
Uninstall in this software requests an AGNOS system reset; preserve needed
settings and recovery copies outside the device before using it. Publishing this
link has not changed or reset the current device installation.

The workflow reconstructs the untouched package from pinned public source and
checksummed native build chunks. It verifies the complete payload hash before
publishing both new branches atomically. It refuses to overwrite an existing
channel. It never executes the installer or vehicle software.

Known cosmetic issue: a registered prebuilt boot can skip the startup animation.
The evidence gate permits a documented `splash_playback: deferred` only with
`channel: staging` and `purpose: installation-test`; all build, boot, settings and
recovery checks still require passing evidence. Stable publication still requires
splash playback. This is a disclosed deferral, not a claimed playback success.

A live download is distinct from a successful clean installation. Clean setup,
first boot through the installer, and driving validation remain outstanding. The
first installer deliberately disables assistance and automatic updates. Do not
reset a device to try an unpublished or unverified URL.

## Installer and runtime

Comma setup requires an ARM64 ELF installer, not a source ZIP, shell script, or
GitHub repository page. The reviewed installer is 2,040,440 bytes and targets
`https://github.com/visegrips70/Roadline.git`, branch `roadline-release-staging`.
It requires the prepared runtime markers and executables before replacing the
installation. It sets assistance off and updates disabled before first boot.

The runtime includes the pinned source, flattened submodules, native build
products, model chunks, firmware support files, licenses and NAP/comma attribution.
The tested runtime contains no private settings or local navigation pairing key.
The separate original NAP backup and recovery record are not release assets.

## Publication and verification

`tools/roadline/publish_staging.py` reconstructs only the reviewed 2fbfa0c payload.
Its parts and source files are verified individually, then the complete tree is
checked with `download_release.py`. The workflow creates new runtime and installer
branches in one atomic push; it cannot replace existing branches. Its GitHub token
is scoped to repository contents and is not written into the release.

The exact target is comma 3X (`comma tizi`), ARM64, AGNOS 17.2. A successful
publication report identifies both Git commits and the installer SHA-256. It is
transport/assembly evidence, not proof of clean installation or vehicle safety.

After publication, the installer URL can be checked without executing it:

```sh
python3 tools/roadline/verify_install_url.py \
  'https://raw.githubusercontent.com/visegrips70/Roadline/roadline-installers/installer' \
  --sha256 e2cdbe18ee902534c0b97ad898f604d884f76c77d86a578bd5333694cb623f61
```

The URL verifier rejects wrong architecture, HTML/script responses, changed
content, truncated downloads and non-HTTPS redirects. A stable download address
alone does not enable OTA updates. Future updates need their own reviewed runtime
publication; the staging installer deliberately keeps automatic updates disabled.

The animated splash still needs a source change and device playback verification.
Steering takeover, pedal/brake behavior, CAN health, driver monitoring and the
reported wrong-turn incident remain separate from download/installation checks.
