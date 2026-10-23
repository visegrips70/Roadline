#!/usr/bin/env python3
"""Read-only comparison of the returned 2fbfa0c bench test; never print credentials."""
import hashlib
import json
import os
from pathlib import Path

RUNTIME = Path('/data/roadline-repackage.qhnsNW/output/runtime')
STATE = Path('/data/roadline-bench-2fbfa0c')
REPORT_SHA256 = '0ab9571cac52a280307ee130a730e5ccfee976cf6cefa8e161e4678cd4a9c548'
MODES_SHA256 = '3c46229e9b00f149fc4bcf2b4dd09b5c611ca91c68da602174def9c647d16229'
# These targets and execute-bit digest were verified directly in the original archive.
LINKS = {
  'cereal/car.capnp': '../opendbc_repo/opendbc/car/car.capnp',
  'rednose': 'rednose_repo/rednose', 'teleoprtc': 'teleoprtc_repo/teleoprtc',
  'msgq': 'msgq_repo/msgq', 'docs/concepts/safety.md': '../SAFETY.md',
  'docs/index.md': 'getting-started/what-is-openpilot.md',
  'third_party/acados/larch64/lib/libqpOASES_e.so': 'libqpOASES_e.so.3.1',
  'third_party/acados/aarch64': 'larch64/',
  'third_party/acados/Darwin/lib/libqpOASES_e.dylib': 'libqpOASES_e.3.1.dylib',
  'third_party/acados/x86_64/lib/libqpOASES_e.so': 'libqpOASES_e.so.3.1',
  'opendbc': 'opendbc_repo/opendbc',
  'selfdrive/modeld/models/big_driving_vision.onnx': 'driving_vision.onnx',
  'selfdrive/modeld/models/big_driving_policy.onnx': 'driving_policy.onnx',
  'tinygrad': 'tinygrad_repo/tinygrad', 'openpilot/common': '../common',
  'openpilot/third_party': '../third_party', 'openpilot/selfdrive': '../selfdrive/',
  'openpilot/system': '../system/', 'openpilot/tools': '../tools',
}


def file_hash(path):
  h = hashlib.sha256()
  with path.open('rb') as f:
    for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
  return h.hexdigest()


def compare_payload(root, report_path, report_hash=REPORT_SHA256, modes_hash=MODES_SHA256, links=None):
  root = root.resolve()
  data = report_path.read_bytes()
  if hashlib.sha256(data).hexdigest() != report_hash:
    raise ValueError('The original package report differs from the reviewed report.')
  expected = {item['path']: item for item in json.loads(data)['files']}
  links = LINKS if links is None else links
  changed, missing, type_changed = [], [], []
  modes = hashlib.sha256()
  for rel, item in sorted(expected.items()):
    path = root / rel
    if path.is_symlink() or not path.resolve().is_relative_to(root):
      type_changed.append(rel)
      continue
    if not path.exists():
      missing.append(rel)
      continue
    if not path.is_file():
      type_changed.append(rel)
      continue
    modes.update((json.dumps([rel, bool(path.stat().st_mode & 0o100)], separators=(',', ':')) + '\n').encode())
    if path.stat().st_size != item['bytes'] or file_hash(path) != item['sha256']:
      changed.append(rel)
  link_changes = [rel for rel, target in links.items()
                  if not (root / rel).is_symlink() or os.readlink(root / rel) != target]
  present = set()
  for parent, dirs, files in os.walk(root, followlinks=False):
    dirs[:] = sorted(d for d in dirs if d != '.git')
    for name in files + [d for d in dirs if (Path(parent) / d).is_symlink()]:
      present.add((Path(parent) / name).relative_to(root).as_posix())
  extra = present - expected.keys() - links.keys()
  caches = {p for p in extra if '__pycache__' in Path(p).parts and p.endswith('.pyc')}
  pairing = {'server/phone_navigation/.pairing-key'} & extra
  other = sorted(extra - caches - pairing)
  modes_match = modes.hexdigest() == modes_hash
  return {
    'original_report_verified': True,
    'original_file_count': len(expected),
    'original_files_and_execute_bits_and_links_match': not (changed or missing or type_changed or link_changes) and modes_match,
    'changed_original_files': changed, 'missing_original_files': missing,
    'changed_original_types': type_changed, 'execute_bits_match': modes_match,
    'changed_symlinks': sorted(link_changes),
    'added_python_cache_count': len(caches), 'local_navigation_key_present': bool(pairing),
    'other_added_count': len(other), 'other_added_paths_first_40': other[:40],
    'added_file_contents_read': False,
    'used_runtime_is_a_release_artifact': False,
  }


def compare_settings(state_dir, params):
  saved = state_dir / 'params-before'
  if not saved.is_dir(): return {'snapshot_present': False, 'matches': False}
  fixed = {'CalibrationParams', 'LiveParameters', 'LiveTorqueParameters',
           'LaneOffsetCm', 'PreAPLaneCentering'}
  names = {p.name for p in saved.iterdir()} | {p.name for p in params.iterdir()}
  names = sorted(n for n in names if n.startswith(('NAP', 'Roadline')) or n in fixed)
  changed = []
  for name in names:
    old, current = saved / name, params / name
    if old.is_symlink() or current.is_symlink():
      changed.append(name)
    elif old.is_file() != current.is_file() or (old.is_file() and old.read_bytes() != current.read_bytes()):
      changed.append(name)
  return {'snapshot_present': True, 'keys_compared': len(names),
          'matches': not changed, 'differing_key_names': changed}


def recovery_details(state_dir, active, launcher, params):
  state = json.loads((state_dir / 'state.json').read_text())
  if state.get('phase') != 'returned':
    raise ValueError('Wait until the bench test has returned before inspecting its files.')
  info = state.get('launcher', {})
  launcher_matches = (not launcher.is_symlink() and launcher.is_file() and
                      file_hash(launcher) == info.get('sha256') and
                      launcher.stat().st_mode & 0o777 == info.get('mode') and
                      launcher.stat().st_uid == info.get('uid') and launcher.stat().st_gid == info.get('gid'))
  saved_launcher = state_dir / 'continue-before.sh'
  return {
    'phase': state['phase'], 'candidate_start_requested': 'start_time' in state,
    'returned_on_boot': state.get('returned_on_boot'), 'active_path': str(active.resolve()),
    'active_path_matches_previous': str(active.resolve()) == state.get('previous'),
    'startup_launcher_restored': launcher_matches,
    'startup_launcher_backup_matches': saved_launcher.is_file() and file_hash(saved_launcher) == info.get('sha256'),
    'assistance_disabled': (params / 'OpenpilotEnabledToggle').read_bytes() == b'0',
    'updates_disabled': (params / 'DisableUpdates').read_bytes() == b'1',
    'settings': compare_settings(state_dir, params),
  }


def main():
  recovery = recovery_details(STATE, Path('/data/openpilot'), Path('/data/continue.sh'), Path('/data/params/d'))
  if not recovery['active_path_matches_previous']:
    raise ValueError('The candidate is not confirmed inactive; inspect its active path first.')
  result = {'recovery': recovery, 'payload': compare_payload(RUNTIME, RUNTIME.parent / 'report.json')}
  print(json.dumps(result, indent=2))


if __name__ == '__main__':
  try: main()
  except (OSError, ValueError, KeyError) as e: raise SystemExit('STOP: ' + str(e))
