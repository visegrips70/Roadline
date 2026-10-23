**Draft repair update:** Branding source and all three exact approved binary assets are included. See [upload status](BRANDING_UPLOAD_STATUS.md). The installer is still disabled.

# Roadline direct-download preparation

Status: preparation tooling, not a live installer or device-ready release.

## Intended experience

On a comma 3X setup screen, select Custom Software, enter one Roadline HTTPS URL,
and receive the tested Roadline release with the approved green/white branding.
A stable URL and a separate staging URL should select reviewed release payloads,
not a moving development branch. Neither URL has been created or enabled.

The inspected setup implementation in `system/ui/tici_setup.py` requires an ELF
installer, not a ZIP, GitHub web page, or shell script. The installer in
`selfdrive/ui/installer/installer.cc` then clones a Git repository and starts its
launcher. Those are two separate artifacts: the installer executable and the
complete prepared runtime. A source ZIP is neither a prebuilt runtime nor an
installer. See also the official openpilot installation overview:
https://github.com/commaai/openpilot#using-openpilot-in-a-car

## Repository and privacy

The development repository is `visegrips70/Roadline`, currently private. Keep its
visibility unchanged. The simple `installer.comma.ai/<owner>/<branch>` convention
must not be treated as a working Roadline link: the existing repository is not
named openpilot and is not anonymously cloneable. Do not embed a personal access
token, SSH private key, navigation pairing key, or device settings in an installer.
The reviewed installer generator documents its repository-name assumptions:
https://github.com/sshane/openpilot-installer-generator#aliases

Preferred publication design: a separately audited release-only distribution
repository, containing the flattened, tested runtime and required licenses, plus
an explicit-repository AGNOS installer served over HTTPS. Public distribution
requires a deliberate publication decision; this work does not publish code or
change repository visibility. A genuinely private installer would instead need
a designed enrollment/authentication flow, not a token pasted into a public URL.

## Checks implemented here

`tools/roadline/download_release.py` reads a prepared release tree and emits a JSON
report. It does not build, install, update parameters, contact CAN, flash firmware,
execute model pickles, or publish anything. Its checks include required files,
ARM64 binary headers/execute bits, compiled model chunks and camera warps, obvious
private material, unresolved LFS pointers, unsafe symlinks, source provenance,
approved media hashes, and superseded display assets.

```bash
python3 tools/roadline/download_release.py /path/to/prepared-release > /tmp/roadline-release-report.json
```

Exit 2 and `BLOCKED` are expected for the current source snapshots. To request
publication review, supply `--evidence /path/outside/release/evidence.json` with
`source_revision`, `payload_sha256`, the exact target object, and a `checks` object.
Required check names are `desktop_ci`, `comma3x_build`, `bench_boot`,
`splash_playback`, `settings_backup_restore`, and `rollback`. Each needs a literal
`status: pass` and a nonempty evidence `reference`. These are maintainer assertions,
not cryptographically authenticated attestations. Passing returns REVIEW_REQUIRED,
never driving approval. Keep evidence and reports outside the hashed payload.

`tools/roadline/verify_install_url.py` fetches a proposed permanent HTTPS URL with
an AGNOSSetup user agent, checks its size, ARM64 ELF header and reviewed SHA-256,
and rejects HTML/ZIP/script responses, credential-bearing URLs and HTTP downgrades.
It does not execute or save the downloaded installer.

```bash
python3 tools/roadline/verify_install_url.py '<reviewed HTTPS installer URL>' --sha256 '<reviewed 64-character checksum>'
```

A passing header/checksum check is not proof the installer executes or that the
runtime repository is anonymously accessible. A clean setup install, first boot,
settings restoration and recovery still require device testing. The URL verifier
intentionally rejects expiring query-token URLs; choose a stable hosting endpoint.

## Next release milestones

1. Pin the integrated repair candidate after its remaining incident investigation
   and validation. The exact approved branding media are now included on the
   repair branch; the device and install-readiness branch have not been updated.
2. Build that pinned source and every pinned dependency on the reviewed comma 3X
   target. Use the existing inactive-checkout bench build process. Do not use
   upstream `release/build_release.sh` unchanged: it deletes `/data/openpilot` and
   pushes to comma.ai's repository. Do not use the destructive cleanup in
   `release/build_stripped.sh` against a working installation either.
3. Prepare a separate immutable runtime payload, flatten submodules, materialize
   required LFS assets, preserve licenses, and remove private data. A native
   builder/packager and explicit-repository installer are still to be implemented
   and validated. Required fonts/assets come from the pinned upstream dependencies.
4. Validate exact-payload bench boot, startup graphics, settings restoration and
   rollback; record evidence. Hardware checks are not replaced by unit tests.
5. After a privacy/licensing review and publication approval, serve the installer
   and runtime anonymously. Verify the installer checksum and repository access,
   test a fresh setup installation, then promote staging to stable manually.

`release/roadline/channels.json` leaves both URLs and release hashes unset and
publication disabled. The new GitHub workflow tests and packages only these
preparation tools. It does not produce a native comma build or enable updates.

## Unchanged

No driving/control/driver-monitoring algorithms, firmware rules, pedal/radar
configuration, source package name, dependency locks, installed software, or
repository visibility are changed by this preparation work. Do not reset or
uninstall the working comma software to try an unpublished URL.
