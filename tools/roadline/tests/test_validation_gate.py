import json
import subprocess
import sys

from tools.roadline import validate


def test_failed_build_blocks_tests_that_could_load_stale_extensions(monkeypatch, tmp_path):
  monkeypatch.setenv('ROADLINE_REVISION', 'a' * 40)
  monkeypatch.setattr(sys, 'argv', ['validate.py', '--output', str(tmp_path)])
  commands = []

  def run(command, **kwargs):
    commands.append(command)
    return subprocess.CompletedProcess(command, 1 if 'SCons' in command else 0)

  monkeypatch.setattr(validate.subprocess, 'run', run)
  assert validate.main() == 1
  report = json.loads((tmp_path / 'summary.json').read_text())
  assert report['status'] == 'FAIL'
  assert len(commands) == 2  # Build and independent static analysis only.
  assert commands[-1][-1].endswith('test_misra.sh')
  blocked = {row['name'] for row in report['checks'] if row.get('blocked_by') == 'native-build'}
  assert blocked == {'focused', 'inherited-features', 'dashboard', 'all-safety'}
