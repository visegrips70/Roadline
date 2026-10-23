#!/usr/bin/env python3
"""Read-only Pre-AP input capture. Subscribes to messages; never sends CAN or writes Params."""
import argparse
from collections import Counter
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
                         'EPAS_eacStatus', 'EPAS_eacErrorCode', 'EPAS_steeringFault', 'EPAS_steeringReduced'),
  (2, 'GAS_SENSOR'): ('INTERCEPTOR_GAS', 'INTERCEPTOR_GAS2', 'STATE', 'IDX'),
}
# The generic address-sum rule was verified for these messages, not DI_torque1.
# Earlier 2013 vehicle captures of DI_torque1 have a stable residual of 0x07,
# instead of 0x09 from address 0x108. Report that evidence without declaring a
# checksum algorithm verified or altering any runtime parser/safety checks.
CHECKSUM_MESSAGES = {'EPAS_sysStatus', 'GAS_SENSOR'}


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
          bad_length=0, bad_checksum=0 if name in CHECKSUM_MESSAGES else None,
          checksum_residuals=Counter(), last_time=None, values={s: [] for s in signals})

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
      if record['name'] == 'DI_torque1':
        record['checksum_residuals'][(data[-1] - sum(data[:-1])) & 255] += 1
      if record['name'] in CHECKSUM_MESSAGES and data[-1] != ((address & 255) + (address >> 8) + sum(data[:-1])) & 255:
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
        if values and signal in ('driverBrakeStatus', 'STATE', 'IDX', 'EPAS_handsOnLevel', 'EPAS_eacStatus', 'EPAS_eacErrorCode',
                                 'EPAS_steeringFault', 'EPAS_steeringReduced'):
          signals[signal]['observed'] = sorted(set(values))
        if values and signal == 'IDX':
          signals[signal]['consecutive_steps'] = sum(int(b) == (int(a) + 1) % 16 for a, b in zip(values, values[1:], strict=False))
          signals[signal]['other_steps'] = len(values) - 1 - signals[signal]['consecutive_steps']
      result[f"{record['name']} bus {bus} ({address:#x})"] = dict(
          received=record['received'], bad_length=record['bad_length'], bad_checksum=record['bad_checksum'],
          checksum_validation=('address_sum' if record['name'] in CHECKSUM_MESSAGES else
                               'not_verified' if record['name'] == 'DI_torque1' else 'not_defined_in_dbc'),
          checksum_additive_residuals={f'{seed:#04x}': count for seed, count in sorted(record['checksum_residuals'].items())},
          age_seconds=None if record['last_time'] is None else round(now - record['last_time'], 3), signals=signals)
    return result


def main():
  from cereal import messaging
  args = argparse.ArgumentParser(description=__doc__)
  args.add_argument('--accelerator-only', action='store_true', help='20-second repeat for factory pedal input; all guards remain.')
  options = args.parse_args()
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
  duration = 45
  if options.accelerator_only:
    duration = 20
    prompts = [(0, 'CAPTURE STARTED: stay in Park. Leave the pedals released for five seconds.'),
               (5, 'ACCELERATOR: lightly press and release twice while remaining in Park.'),
               (15, 'REST: release the accelerator fully; stay in Park.')]
  print('Factory-pedal checksum validation is unverified; raw values are diagnostic observations only.', flush=True)
  index = 0
  while time.monotonic() - start < duration:
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
