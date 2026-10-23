#!/usr/bin/env python3
"""Read-only Pre-AP input capture. Subscribes to messages; never sends CAN or writes Params."""
import json
import math
from pathlib import Path
import time

DISABLED = ('OpenpilotEnabledToggle', 'NAPPedalEnabled', 'NAPRadarEnabled',
            'NAPiBoosterEnabled', 'NAPNavigationManeuvers', 'NAPMapDrivingAssist')
SPECS = {
  (0, 'BrakeMessage'): ('driverBrakeStatus',),
  (0, 'DI_torque1'): ('DI_pedalPos',),
  (0, 'EPAS_sysStatus'): ('EPAS_torsionBarTorque', 'EPAS_internalSAS', 'EPAS_handsOnLevel',
                         'EPAS_eacStatus', 'EPAS_eacErrorCode'),
  (2, 'GAS_SENSOR'): ('INTERCEPTOR_GAS', 'INTERCEPTOR_GAS2', 'STATE', 'IDX'),
}


def require_parked(sm, params, now):
  for key in DISABLED:
    path = params / key
    if not path.is_file() or path.read_bytes().strip() != b'0':
      raise ValueError(f'{key} must remain 0.')
  for name in ('pandaStates', 'carState'):
    age = now - sm.logMonoTime[name] / 1e9
    if not sm.seen[name] or not sm.valid[name] or not 0 <= age <= 1:
      raise ValueError(f'Fresh valid {name} required.')
  cs = sm['carState']
  if (str(cs.gearShifter) != 'park' or not cs.canValid or cs.canTimeout
      or any(not math.isfinite(v) or abs(v) > .05 for v in (cs.vEgo, cs.vEgoRaw))):
    raise ValueError('Park, zero speed and valid vehicle CAN are required.')
  pandas = sm['pandaStates']
  if not pandas or any(str(p.safetyModel) != 'noOutput' or p.controlsAllowed
                       or str(p.faultStatus) != 'none' or len(p.faults) or p.heartbeatLost
                       for p in pandas):
    raise ValueError('Live noOutput with controls disallowed and no reported Panda faults required.')


class Capture:
  def __init__(self):
    from opendbc.can import CANParser
    self.parsers = {bus: CANParser('tesla_preap', [(name, 0) for b, name in SPECS if b == bus], bus)
                    for bus in (0, 2)}
    self.records = {}
    for (bus, name), signals in SPECS.items():
      msg = self.parsers[bus].dbc.name_to_msg[name]
      self.records[(bus, msg.address)] = dict(name=name, size=msg.size, received=0,
          bad_length=0, bad_checksum=0, last_time=None, values={s: [] for s in signals})

  def feed(self, timestamp, frames):
    accepted = []
    for address, data, bus in frames:
      record = self.records.get((bus, address))
      if record is None:
        continue
      record['received'] += 1
      if len(data) != record['size']:
        record['bad_length'] += 1
        continue
      # These three Tesla messages carry an additive checksum in the last byte.
      # BrakeMessage has no checksum signal in tesla_preap.dbc.
      if record['name'] != 'BrakeMessage' and data[-1] != ((address & 255) + (address >> 8) + sum(data[:-1])) & 255:
        record['bad_checksum'] += 1
        continue
      accepted.append((address, data, bus))
    for bus, parser in self.parsers.items():
      for address in parser.update([(timestamp, accepted)]):
        record = self.records[(bus, address)]
        record['last_time'] = timestamp / 1e9
        for signal, values in record['values'].items():
          values.extend(parser.vl_all[address][signal])

  def summary(self, now):
    result = {}
    for (bus, address), record in self.records.items():
      signals = {}
      for signal, values in record['values'].items():
        signals[signal] = None if not values else dict(samples=len(values),
            first=round(values[0], 4), last=round(values[-1], 4),
            min=round(min(values), 4), max=round(max(values), 4))
        if values and signal in ('driverBrakeStatus', 'STATE', 'IDX', 'EPAS_handsOnLevel', 'EPAS_eacStatus', 'EPAS_eacErrorCode'):
          signals[signal]['observed'] = sorted(set(values))
        if values and signal == 'IDX':
          signals[signal]['consecutive_steps'] = sum(int(b) == (int(a) + 1) % 16 for a, b in zip(values, values[1:], strict=False))
          signals[signal]['other_steps'] = len(values) - 1 - signals[signal]['consecutive_steps']
      result[f"{record['name']} bus {bus} ({address:#x})"] = dict(
          received=record['received'], bad_length=record['bad_length'], bad_checksum=record['bad_checksum'],
          age_seconds=None if record['last_time'] is None else round(now - record['last_time'], 3), signals=signals)
    return result


def main():
  from cereal import messaging
  params = Path('/data/params/d')
  if (params / 'NAPPedalCanBus').read_bytes().strip() != b'2':
    raise ValueError('This observation is for the configured bus-2 pedal.')
  sm = messaging.SubMaster(['pandaStates', 'carState'])
  deadline = time.monotonic() + 5
  while time.monotonic() < deadline and not all(sm.seen.values()):
    sm.update(100)
  require_parked(sm, params, time.monotonic())
  capture = Capture()
  sock = messaging.sub_sock('can')
  start = time.monotonic()
  prompts = [(0, 'CAPTURE STARTED: stay in Park. Leave pedals and steering alone for five seconds.'),
             (5, 'BRAKE: press and release the brake twice; stay in Park.'),
             (15, 'ACCELERATOR: with the brake released, lightly press and release the accelerator twice; stay in Park.'),
             (25, 'STEERING: gently turn the wheel a little each way, then return it to center. Do not force it.'),
             (38, 'REST: release the pedals and leave the wheel still.')]
  index = 0
  while time.monotonic() - start < 45:
    sm.update(100)
    now = time.monotonic()
    require_parked(sm, params, now)
    if index < len(prompts) and now - start >= prompts[index][0]:
      print(prompts[index][1], flush=True)
      index += 1
    for event in messaging.drain_sock(sock):
      capture.feed(event.logMonoTime, [(f.address, bytes(f.dat), f.src) for f in event.can])
  require_parked(sm, params, time.monotonic())
  print(json.dumps(capture.summary(time.monotonic()), indent=2), flush=True)
  print('READ-ONLY CAPTURE COMPLETE. Input observations do not establish actuator or disengagement performance.')


if __name__ == '__main__':
  try:
    main()
  except (ValueError, OSError) as error:
    raise SystemExit(f'STOP: {error}') from error
