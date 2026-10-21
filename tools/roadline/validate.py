#!/usr/bin/env python3
"""Run development checks and retain failures. Does not install or drive a car."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
FOCUSED = [
  'selfdrive/ui/tests/test_roadline_settings.py',
  'selfdrive/controls/tests/test_roadline_lane_position.py',
  'selfdrive/controls/tests/test_roadline_lane_simulation.py',
  'selfdrive/controls/tests/test_lane_centering.py',
  'tools/roadline/tests',
  'selfdrive/monitoring/test_monitoring.py',
  'opendbc_repo/opendbc/safety/tests/test_tesla_preap.py',
]
FEATURES = ['selfdrive/controls/tests', 'selfdrive/controls/lib/tests']


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--output', type=Path, default=ROOT / 'build/roadline-validation')
  parser.add_argument('--jobs', type=int, default=2)
  args = parser.parse_args()
  if args.jobs < 1:
    parser.error('--jobs must be positive')
  output = args.output.resolve()
  output.mkdir(parents=True, exist_ok=True)
  revision = os.environ.get('ROADLINE_REVISION')
  dirty = None  # Docker source copies intentionally contain no .git metadata.
  if revision is None:
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True))
  env = dict(os.environ, SCALE='1', PYTHONPATH=f'{ROOT}:{ROOT / "server"}')
  env['PATH'] = f'{Path(sys.executable).parent}:{env.get("PATH", "")}'
  pytest = [sys.executable, '-m', 'pytest', '-n', '0']
  checks = [
    ('native-build', [sys.executable, '-m', 'SCons', '-j', str(args.jobs)]),
    ('focused', pytest + FOCUSED),
    ('inherited-features', pytest + FEATURES),
    ('dashboard', [sys.executable, '-m', 'unittest', 'discover', '-s', 'server/tests', '-q']),
    ('all-safety', pytest + ['opendbc_repo/opendbc/safety/tests']),
    ('misra-baseline', ['bash', 'opendbc_repo/opendbc/safety/tests/misra/test_misra.sh']),
  ]
  results = []
  native_build_passed = False
  for name, command in checks:
    if name not in ('native-build', 'misra-baseline') and not native_build_passed:
      # Compiled Python extensions and libsafety may still be present from an
      # older revision. Never report tests against them as this revision's pass.
      (output / f'{name}.log').write_text('BLOCKED: native build failed; compiled dependencies may be stale.\n')
      results.append(dict(name=name, command=command, exit_code=None, elapsed_seconds=0,
                          blocked_by='native-build'))
      print(f'{name}: BLOCKED by native-build', flush=True)
      continue
    print(f'Running {name}; log: {output / (name + ".log")}', flush=True)
    start = time.monotonic()
    with (output / f'{name}.log').open('w') as log:
      result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if name == 'native-build':
      native_build_passed = result.returncode == 0
    results.append(dict(name=name, command=command, exit_code=result.returncode,
                        elapsed_seconds=round(time.monotonic() - start, 2)))
    print(f'{name}: {"PASS" if result.returncode == 0 else "FAIL"}', flush=True)
    if result.returncode:
      print('\n'.join((output / f'{name}.log').read_text(errors='replace').splitlines()[-30:]), flush=True)
  report = dict(revision=revision, working_tree_modified=dirty, checks=results,
                status='PASS' if all(row['exit_code'] == 0 for row in results) else 'FAIL',
                scope='Desktop development checks; no device, road, or end-to-end model validation.')
  (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
  return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
  raise SystemExit(main())
