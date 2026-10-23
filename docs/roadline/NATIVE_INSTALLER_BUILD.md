# Native Roadline installer build

This is an unpublished staging installer for comma 3X on AGNOS 17.2. It is not a
working setup URL or a validated driving release. NAP and comma.ai attribution is
preserved. No change is made to any upstream repository.

Run in a new, pinned, recursively initialized checkout under `/data`, with the
car off and stable power. The build refuses the active checkout. Do not uninstall
or reset first.

```
bash tools/roadline/build_installer_on_device.sh <full-commit-sha>
```

The script builds the runtime, then the ARM64 installer, checks its format/size
and embedded repository/branch, and prepares a separate runtime directory:

- `selfdrive/ui/installer/installers/installer_roadline_staging`
- `build/roadline-device/installer.sha256`
- `/data/roadline-package-<full-commit-sha>/runtime`
- `/data/roadline-package-<full-commit-sha>/report.json`

Packaging does not overwrite an existing output. It rejects known private-file
names and external symlinks, flattens submodules, excludes Git metadata and build
logs, and runs the existing release gate. This is not an exhaustive secret audit.
A failed package is retained for inspection; do not publish it. Missing validation
evidence is expected and keeps publication blocked, even after a successful build.

The staging installer explicitly clones `visegrips70/Roadline`, branch
`roadline-release-staging`. That branch does not exist yet. It must contain a
reviewed compiled runtime, not development source. The installer does not reuse an
upstream cache. Before replacing the installation it requires the prebuilt marker,
Roadline release manifest, camera executable and launcher. It sets assistance off
and disables automatic updates for initial bench validation. These checks do not
constitute cryptographic payload verification or driving validation.

## Remaining device and publication work

1. Build on the actual comma and review the package report.
2. Preserve settings and the original NAP recovery option before first boot.
3. Verify the exact runtime's parked boot, graphics, settings and recovery.
4. Audit and publish only the flattened runtime to the release branch, including
   licenses and source provenance. Publish the matching installer executable as a
   GitHub release asset and verify its anonymous HTTPS download and SHA-256.
5. Test the custom-software setup flow and first boot before sharing an install
   URL as working. OTA configuration follows bench validation.

The installer target must never be built with INTERNAL enabled. It installs no
SSH keys or pairing secrets. The build scripts never invoke the installer,
manager, pandad, firmware flashers, system reset, or a Git push.
