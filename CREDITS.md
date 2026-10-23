# Credits and upstream foundation

**Roadline is built on NAP (NotAutopilot), Philip's pre-AP work, and comma.ai openpilot.**
The driving stack and most of the source in this repository are inherited from
those projects and their contributors. Roadline would not exist without them.

| Project / contributors | Inherited foundation |
| --- | --- |
| [NotAutopilot (NAP)](https://github.com/NotAutopilot/openpilot) and its contributors | Pre-Autopilot Tesla support, pedal and steering integration, radar support, configuration and recovery work. [NAP website and documentation](https://notautopilot.com). |
| [Philip / philipr144-create](https://github.com/philipr144-create/openpilot-preap) and contributors | The immediate openpilot-preap base, [opendbc-preap](https://github.com/philipr144-create/opendbc-preap), and [NAP-Dash](https://github.com/philipr144-create/NAP-Dash), including the inherited dashboard, navigation and tuning features. |
| [comma.ai openpilot](https://github.com/commaai/openpilot) and contributors | Core driving, perception, planning, driver monitoring, device software and the underlying open-source platform. |
| [Tinkla](https://tinkla.us/t/index) and [xnor-tech](https://github.com/xnor-tech/openpilot) | Earlier Tesla integration work credited by the inherited NAP README. |
| Panda, opendbc, msgq, rednose, teleoprtc, tinygrad and their contributors | Firmware, vehicle definitions and supporting libraries. Exact source repositories and revisions are recorded in [provenance](docs/roadline/PROVENANCE.md). |

## What Roadline contributes

Roadline-specific work includes lane-position controls, changes to takeover and
cruise behavior, incident diagnostics and regression tests, packaging and recovery
preparation, navigation pairing setup, and Roadline's own branding. Several of
these extend or restore inherited behavior. The vision models, NAP vehicle
integration, dashboard and navigation foundation are not original Roadline work.

The earlier "about 95% unchanged" comparison counted source files at a particular
revision. It was not a measurement of original authorship, lines of code, or
driving behavior, and will change as development continues.

## Attribution and independence

Keep upstream copyright headers, license files and contributor acknowledgments
with inherited source and distributions. The [root license](LICENSE), component
licenses and [original NAP README](docs/roadline/UPSTREAM_README.md) remain in place.
This credits page supplements them; it does not replace or change their terms.

Use the description "Roadline — built on NAP / NotAutopilot and comma.ai openpilot"
in releases and project introductions. Roadline's name and graphics identify this
fork and its changes; they do not transfer credit for the inherited foundation.

Roadline is independently maintained. No endorsement or review by NAP, Philip,
comma.ai, Tesla or the other upstream contributors is implied. Roadline changes
and their validation are the responsibility of Roadline's maintainers. Send
Roadline-specific bug reports to this repository, not to upstream maintainers.
