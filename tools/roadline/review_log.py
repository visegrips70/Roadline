#!/usr/bin/env python3
"""Summarize attention classifier signals from LOCAL logs without uploading them."""

import argparse
from collections import Counter
import json
from pathlib import Path


class AttentionReview:
  def __init__(self):
    self.counts = Counter()
    self.alert_starts = Counter()
    self.previous_alerts = set()

  def add(self, state, valid=True):
    if not valid:
      self.counts['invalid_packets'] += 1
      self.previous_alerts = set()
      return
    self.counts['samples'] += 1
    self.counts['face_not_detected'] += not state.faceDetected
    self.counts['uncertain_pose'] += not state.isLowStd
    self.counts['passive_monitoring'] += not state.isActiveMode
    self.counts['distracted'] += state.isDistracted
    for bit, name in ((1, 'head_pose'), (2, 'eyes'), (4, 'phone')):
      self.counts[name] += bool(state.distractedType & bit)
    alerts = {str(e.name) for e in state.events if 'distract' in str(e.name).lower() or 'unresponsive' in str(e.name).lower()}
    self.alert_starts.update(alerts - self.previous_alerts)
    self.previous_alerts = alerts

  def report(self):
    total = self.counts['samples']
    return {
      'valid_samples': total,
      'invalid_packets': self.counts['invalid_packets'],
      'sample_percentages': {
        key: round(100 * self.counts[key] / total, 2) if total else None
        for key in ('face_not_detected', 'uncertain_pose', 'passive_monitoring', 'distracted', 'head_pose', 'eyes', 'phone')
      },
      'observed_alert_starts': dict(sorted(self.alert_starts.items())),
      'interpretation': (
        'Classifier outputs, not proof of actual distraction or false positives. '
        + 'Percentages count samples, not time. Gaps can split alert episodes. '
        + 'No camera images, GPS, route identifiers, or absolute timestamps are exported.'
      ),
    }


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('logs', type=Path, nargs='+', help='Local rlog/qlog files, in chronological order')
  args = parser.parse_args()
  if any(not path.is_file() for path in args.logs):
    parser.error('Every input must be an existing local file; URLs and route IDs are not accepted.')
  # Delay native/log imports so the summary logic also runs in lightweight tests.
  from openpilot.tools.lib.logreader import LogReader

  review = AttentionReview()
  for path in args.logs:
    for event in LogReader(str(path.resolve())):
      if event.which() == 'driverMonitoringState':
        review.add(event.driverMonitoringState, valid=event.valid)
  print(json.dumps(review.report(), indent=2))


if __name__ == '__main__':
  main()
