# Navigation and lane position — development draft

These changes are on `roadline-first-drive-fixes`, not the installed vehicle.
Do not install this branch or perform another assisted drive until the first-drive
turn incident, replay, clean build, and hardware acceptance are resolved.

## Navigation

The dashboard uses the comma's GPS. It does not import a route from Tesla MCU2
native navigation. On a phone or computer connected to the same network, open
`http://<comma-IP>:7070/phone-nav`. The owner's last reported IP is
`192.168.68.70`; check the device's network page if it changes.

On a fresh install, Roadline now creates the navigation pairing key during normal
startup. It persists in `/data/roadline/navigation-pairing-key` and is copied into
each checkout's expected dashboard location. Existing valid keys are preserved.
Conflicting or corrupt existing keys produce an error instead of being silently
overwritten. Keys are private local files and must not be committed or uploaded.
A factory reset that erases /data also erases this key; browsers then need pairing
again.

1. While parked, open the navigation page and pair. The pinned NAP dashboard's
   default setup PIN is `087911`, unless `NAP_PHONE_PAIR_CODE` overrides it.
   This PIN is static; the page's old one-time/expiration wording is inaccurate.
2. Search the full address including city, select the correct result, then choose
   **Start route on comma**. Save a destination to use the comma's Routes screen.
3. New search/route calculation requires internet and a fresh GPS fix. Phone
   hotspot networking may give the comma a different IP.
4. Keep **Navigation influence OFF** while the turn fault is under review.
   Directions and saved destinations are separate from maneuver control.

Pairing setup alone can be checked without changing driving settings:
`python3 tools/roadline/navigation_setup.py`.
It prints no credential. The dashboard reads the key when its process starts.
This helper has not been run on the owner's current device.

## Live lane preference

With Lane Centering Assist enabled on Pre-AP, the driving display adds:
**Left**, a visible centimetre preference, **Center**, and **Right**.
Each left/right release changes the preference by one centimetre; holding does
not repeat. Center requests zero. Input is bounded to -30/+30 cm with a 250-ms
debounce. The value shown is a preference, not measured displacement.

The controller reads the preference at 10 Hz while engaged. Existing confidence,
road geometry, speed, turn-signal, driver-takeover and lane-change restrictions
remain. Added lateral acceleration and its slew limit remain unchanged.
A preference is not applied where those checks reject lane-centering assistance.
The displayed green model path is not shifted. The existing keyboard setting
and strength/toggle edits remain restricted to parked use.

The third HUD row is hidden if the screen is too short to fit without covering
the driving-intent card. Device rendering and touch placement still need review.
