#!/usr/bin/env python3
"""Create an unpublished runtime from an inactive native build; never activate it."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from download_release import PRIVATE_NAMES, inspect_tree

OMIT_DIRS = {'.git', '.github', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.cache', 'build'}
OMIT_FILES = {'.git', '.gitmodules', '.gitattributes', '.lfsconfig', '.sconsign.dblite'}


def copy_runtime(source, destination):
  """Copy build products and flattened dependencies without Git metadata or logs."""
  for parent, dirs, files in os.walk(source, followlinks=False):
    rel = Path(parent).relative_to(source)
    target = destination / rel
    target.mkdir(parents=True, exist_ok=True)
    dirs[:] = sorted(d for d in dirs if d not in OMIT_DIRS)
    entries = files + [d for d in dirs if (Path(parent) / d).is_symlink()]
    for name in sorted(entries):
      src = Path(parent) / name
      dst = target / name
      if name in OMIT_FILES or name.endswith(('.o', '.os', '.a', '.pyc', '.log', '.bak')):
        continue
      if name in PRIVATE_NAMES or name == '.env' or (name.startswith('.env.') and not name.endswith(('example', 'sample'))):
        raise ValueError(f'Private configuration in build tree: {rel / name}')
      if src.is_symlink():
        if os.path.isabs(os.readlink(src)) or not src.resolve().is_relative_to(source) or not src.exists():
          raise ValueError(f'Nonportable symlink: {rel / name}')
        dst.symlink_to(os.readlink(src))
      elif src.is_file():
        with src.open('rb') as f:
          head = f.read(256)
        if b'PRIVATE KEY-----' in head:
          raise ValueError(f'Private key in build tree: {rel / name}')
        shutil.copy2(src, dst)
      else:
        raise ValueError(f'Unsupported entry: {rel / name}')


def package(source, output, revision):
  source = source.resolve()
  output = output.absolute()
  if output.exists() or output.is_symlink():
    raise ValueError('Output must be a new directory; nothing will be overwritten.')
  if output.resolve().is_relative_to(source) or source.is_relative_to(output.resolve()):
    raise ValueError('Output and source must not overlap.')
  active = Path('/data/openpilot').resolve()
  if source == active or output.resolve() == active:
    raise ValueError('Use an inactive checkout and a separate output directory.')
  actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
  if actual != revision or (source / 'build/roadline-device/built_commit.txt').read_text().strip() != revision:
    raise ValueError('Source and successful native-build record must match the requested revision.')
  if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
    raise ValueError('Tracked source changed after checkout.')
  output.mkdir(parents=False)
  payload = output / 'runtime'
  payload.mkdir()
  copy_runtime(source, payload)
  (payload / 'prebuilt').touch()
  (payload / 'git_src_commit').write_text(revision + '\n')
  (payload / 'roadline_release.json').write_text(json.dumps({
    'schema_version': 1, 'source_revision': revision,
    'target': {'model': 'comma tizi', 'architecture': 'aarch64', 'agnos': '17.2'},
    'channel': 'staging', 'road_ready': False,
  }, indent=2) + '\n')
  report = inspect_tree(payload)
  (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
  blockers = [b for b in report['blockers'] if b != 'No exact-payload validation evidence supplied; publication is blocked.']
  if blockers:
    raise ValueError('Runtime incomplete. See report.json; do not publish this directory.')
  print(f'Runtime prepared at {payload}; bench validation and publication remain outstanding.')


if __name__ == '__main__':
  p = argparse.ArgumentParser(description=__doc__)
  p.add_argument('source', type=Path)
  p.add_argument('output', type=Path)
  p.add_argument('revision')
  a = p.parse_args()
  try:
    package(a.source, a.output, a.revision)
  except (ValueError, OSError, subprocess.CalledProcessError) as e:
    raise SystemExit(f'STOP: {e}')
