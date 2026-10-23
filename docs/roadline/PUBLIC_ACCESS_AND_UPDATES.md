# Public source and updates from the comma

Status (2026-10-23): GitHub confirms the repository is public. Device updates remain unconfigured and the repair candidate remains a draft.

The owner requested public source access and future updates without connecting a
Mac. Roadline is built on NAP / NotAutopilot and comma.ai openpilot; retain the
prominent [upstream credits](../../CREDITS.md) in the public project and releases.

## Three separate steps

1. **Public source:** repository visibility makes source and reachable history
   readable without a GitHub login. Review all branches, history and attachments
   for private material first. The GitHub connection used for this work cannot
   change visibility; that action uses GitHub's Settings page.
2. **One-time device configuration:** verify the active checkout, its `origin`,
   `UpdaterTargetBranch`, `DisableUpdates`, startup path and recovery arrangement.
   Public HTTPS origin would be `https://github.com/visegrips70/Roadline.git`.
   The last reported device was installed from a pinned candidate; it must not
   be assumed to track a branch. Its first-start installer deliberately sets
   `DisableUpdates=1`; verify the live value before any change. Check the symlink-based installation against the
   updater's staging/swap behavior before enabling it. Do not embed credentials.
3. **Reviewed update channel:** publish validated revisions to a dedicated
   release branch. Keep development and repair branches separate. No validated
   Roadline release branch or installer is available yet. Do not point the car
   at a moving development branch as a substitute.

## Intended routine after configuration and validation

Keep the comma powered, connected to Wi-Fi or a hotspot, and offroad. In
**Settings > Software**, use **CHECK**, **DOWNLOAD** when offered, then
**Install Update**. The inherited updater can also stage downloads in the
background while offroad. Installation uses the existing reboot/startup path.
It fetches the configured Git origin and target branch; making GitHub public
does not change either setting on the device.

The NAP/openpilot updater already provides this mechanism. Roadline should
preserve and validate it rather than claim it as a new Roadline feature. A Mac
should not be required for normal updates once the one-time setup works;
recovery access may still be needed for a failed installation.

## Current limits

This document does not enable updates, switch branches, merge the repair draft,
or change the owner's device. The first-drive incident investigation and device
acceptance remain open. Public development source is not driving approval.
Direct installation from a custom URL is a separate deliverable described in
[DIRECT_DOWNLOAD.md](DIRECT_DOWNLOAD.md).
