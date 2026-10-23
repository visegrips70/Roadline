#!/usr/bin/env python3
"""Standalone branding tests; no car hardware, native build, network or UI needed.

Run: python3 -m unittest discover -s tools/roadline -p test_branding.py -v
Native rendering is stubbed: these tests are not a comma display/road validation.
"""
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
  spec = importlib.util.spec_from_file_location(name, path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


video = load('roadline_video_test', ROOT / 'system/ui/lib/roadline_video.py')


class VideoTests(unittest.TestCase):
  def test_queue_is_bounded(self):
    self.assertEqual(video.RoadlineVideo(Path('missing')).frames.maxsize, 2)

  def test_empty_sample_is_immediate(self):
    player = video.RoadlineVideo(Path('missing'))
    self.assertIsNone(player.sample(0))

  def test_future_frame_is_held(self):
    player = video.RoadlineVideo(Path('missing'))
    player.frames.put_nowait((0.5, 'later'))
    self.assertIsNone(player.sample(0.4))
    self.assertEqual(player.sample(0.5), 'later')

  def test_latest_due_frame_wins(self):
    player = video.RoadlineVideo(Path('missing'))
    player.frames.put_nowait((0.0, 'first'))
    player.frames.put_nowait((0.1, 'second'))
    self.assertEqual(player.sample(0.2), 'second')

  def test_movie_ends_at_4p5_seconds(self):
    player = video.RoadlineVideo(Path('missing'))
    player.frames.put_nowait((4.4, 'last'))
    self.assertIsNone(player.sample(4.5))
    self.assertTrue(player.stopped.is_set())
    self.assertTrue(player.frames.empty())

  def test_close_is_idempotent(self):
    player = video.RoadlineVideo(Path('missing'))
    player.close()
    player.close()
    player.start()
    self.assertIsNone(player._thread)

  def test_missing_file_fails_without_ui_exception(self):
    with tempfile.TemporaryDirectory() as tmp:
      player = video.RoadlineVideo(Path(tmp) / 'missing.mp4')
      player.start()
      self.assertTrue(player.finished.wait(2))
      self.assertIn('missing', player.error)
      player.close()

  def test_oversize_file_is_rejected(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'oversize.mp4'
      with path.open('wb') as f:
        f.truncate(4 * 1024 * 1024 + 1)
      player = video.RoadlineVideo(path)
      player._decode()
      self.assertIn('size limit', player.error)

  def test_decoder_error_is_captured(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'bad.mp4'
      path.write_bytes(b'bad')
      player = video.RoadlineVideo(path)
      fake_av = types.SimpleNamespace(open=lambda *a, **kw: (_ for _ in ()).throw(ValueError('bad codec')))
      with patch.dict(sys.modules, {'av': fake_av}):
        player._decode()
      self.assertEqual(player.error, 'bad codec')
      self.assertTrue(player.finished.is_set())

  def test_decoder_rejects_unexpected_dimensions(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'bad.mp4'
      path.write_bytes(b'bad')
      class Movie:
        streams = types.SimpleNamespace(video=[types.SimpleNamespace(width=10, height=10, average_rate=30)])
        def __enter__(self):
          return self
        def __exit__(self, *args):
          pass
      player = video.RoadlineVideo(path)
      with patch.dict(sys.modules, {'av': types.SimpleNamespace(open=lambda *a, **kw: Movie())}):
        player._decode()
      self.assertIn('Unexpected', player.error)

  def test_stop_releases_full_queue_worker(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / 'movie.mp4'
      path.write_bytes(b'movie')
      class Frame:
        def reformat(self, **kwargs):
          return self
        def to_ndarray(self):
          return b'pixels'
      class Movie:
        streams = types.SimpleNamespace(video=[types.SimpleNamespace(width=2160, height=1080, average_rate=30,
                                                                     codec_context=types.SimpleNamespace(thread_count=0))])
        def __enter__(self):
          return self
        def __exit__(self, *args):
          pass
        def decode(self, stream):
          for _ in range(135):
            yield Frame()
      player = video.RoadlineVideo(path)
      with patch.dict(sys.modules, {'av': types.SimpleNamespace(open=lambda *a, **kw: Movie())}):
        player.start()
        deadline = time.monotonic() + 2
        while not player.frames.full() and time.monotonic() < deadline:
          time.sleep(0.005)
        self.assertTrue(player.frames.full())
        player.close()
        self.assertTrue(player.finished.wait(1))
        self.assertIsNone(player.error)


class Rect:
  def __init__(self, x, y, width=0, height=0):
    self.x, self.y, self.width, self.height = x, y, width, height


class StubVideo:
  def __init__(self, path):
    self.error = None
    self.starts = 0
    self.closed = False
  def start(self):
    self.starts += 1
  def sample(self, elapsed):
    return None
  def close(self):
    self.closed = True


class RenderTests(unittest.TestCase):
  def setUp(self):
    self.draws = []
    self.clock = [0.0]
    def record(name):
      return lambda *args, **kwargs: self.draws.append((name, args))
    rl = types.SimpleNamespace(Color=lambda *x: x, BLACK=(0, 0, 0, 255), WHITE=(255, 255, 255, 255),
                               Rectangle=Rect, Vector2=Rect,
                               draw_rectangle_rec=record('rect'), draw_rectangle_rounded=record('rounded'),
                               draw_texture_pro=record('texture'), draw_text_ex=record('text'))
    gui = types.SimpleNamespace(font=lambda: object(), texture=lambda *a: types.SimpleNamespace(width=2160, height=1080))
    mods = {
      'pyray': rl,
      'openpilot.system.ui.lib.application': types.SimpleNamespace(ASSETS_DIR=ROOT / 'selfdrive/assets', gui_app=gui),
      'openpilot.system.ui.lib.roadline_video': types.SimpleNamespace(DECODE_HEIGHT=540, DECODE_WIDTH=1080, DURATION=4.5,
                                                                   RoadlineVideo=StubVideo),
      'openpilot.system.ui.lib.text_measure': types.SimpleNamespace(measure_text_cached=lambda f, text, size: Rect(len(text)*size/2, 0)),
      'openpilot.system.ui.text': types.SimpleNamespace(wrap_text=lambda text, *a: text.splitlines()),
      'openpilot.system.ui.widgets': types.SimpleNamespace(Widget=object),
    }
    with patch.dict(sys.modules, mods):
      self.module = load('roadline_spinner_test', ROOT / 'system/ui/roadline_spinner.py')
    self.timer = patch.object(self.module, 'time', types.SimpleNamespace(monotonic=lambda: self.clock[0]))
    self.timer.start()
    self.addCleanup(self.timer.stop)
    self.rect = Rect(0, 0, 2160, 1080)

  def test_progress_is_actual_and_clamped(self):
    spinner = self.module.RoadlineFallback()
    for value, expected in [('0', 0), ('28', 28), ('100', 100), ('500', 100)]:
      spinner.set_text(value)
      self.assertEqual(spinner._progress, expected)
      spinner._render(self.rect)

  def test_nonnumeric_status_preserved(self):
    spinner = self.module.RoadlineFallback()
    text = 'Building UI\nNative build error: details'
    spinner.set_text(text)
    self.assertIsNone(spinner._progress)
    spinner._render(self.rect)
    rendered = [args[1] for name, args in self.draws if name == 'text']
    self.assertIn('Building UI', rendered)
    self.assertIn('Native build error: details', rendered)

  def test_non_ascii_digits_are_not_parsed(self):
    spinner = self.module.RoadlineFallback()
    spinner.set_text('²')
    self.assertEqual(spinner._status, '²')

  def test_fallback_is_green_white_roadline(self):
    self.module.RoadlineFallback()._render(self.rect)
    texts = [args[1] for name, args in self.draws if name == 'text']
    self.assertEqual(texts, ['ROAD', 'LINE'])

  def test_playback_starts_once(self):
    spinner = self.module.RoadlineSpinner()
    spinner._render(self.rect)
    self.clock[0] = 0.4
    spinner._render(self.rect)
    self.assertEqual(spinner._video.starts, 1)

  def test_error_falls_back_to_still(self):
    spinner = self.module.RoadlineSpinner()
    spinner._video.error = 'missing codec'
    spinner._render(self.rect)
    self.assertTrue(spinner._failed)
    self.assertTrue(spinner._video.closed)
    self.assertTrue(any(name == 'texture' for name, _ in self.draws))

  def test_slow_decoder_timeout_uses_still(self):
    spinner = self.module.RoadlineSpinner()
    spinner._render(self.rect)
    self.clock[0] = 1.1
    spinner._render(self.rect)
    self.assertTrue(spinner._failed)
    self.assertTrue(spinner._video.closed)

  def test_final_still_is_held_without_loop(self):
    spinner = self.module.RoadlineSpinner()
    spinner._render(self.rect)
    self.clock[0] = 4.5
    spinner._render(self.rect)
    self.clock[0] = 45
    spinner._render(self.rect)
    self.assertEqual(spinner._video.starts, 1)
    self.assertTrue(spinner._video.closed)
    self.assertEqual(sum(name == 'texture' for name, _ in self.draws), 2)

  def test_missing_still_falls_back_to_wordmark(self):
    spinner = self.module.RoadlineSpinner()
    spinner._still_attempted = True
    spinner._video.error = 'missing media'
    spinner._render(self.rect)
    texts = [args[1] for name, args in self.draws if name == 'text']
    self.assertEqual(texts, ['ROAD', 'LINE'])

  def test_zero_sized_rect_does_not_start_decoder(self):
    spinner = self.module.RoadlineSpinner()
    spinner._render(Rect(0, 0, 0, 0))
    self.assertEqual(spinner._video.starts, 0)


class PackageTests(unittest.TestCase):
  def test_approved_media_hashes(self):
    assets = ROOT / 'selfdrive/assets/roadline'
    manifest = json.loads((assets / 'manifest.json').read_text())
    for name, entry in manifest['files'].items():
      data = (assets / name).read_bytes()
      self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'], name)
      self.assertEqual(len(data), entry['bytes'], name)

  def test_no_active_philly_branding(self):
    for relative in ['selfdrive/ui', 'system/ui']:
      for file in (ROOT / relative).rglob('*.py'):
        self.assertNotIn('philly', file.read_text().lower(), str(file))
    self.assertFalse((ROOT / 'system/ui/phillyfork_spinner.py').exists())
    self.assertFalse((ROOT / 'selfdrive/assets/images/spinner_comma.png').exists())

  def test_python_syntax(self):
    files = ['system/ui/spinner.py', 'system/ui/roadline_spinner.py', 'system/ui/lib/roadline_video.py',
             'selfdrive/ui/ui.py', 'selfdrive/ui/layouts/home.py', 'selfdrive/ui/layouts/onboarding.py',
             'selfdrive/ui/layouts/settings/nap.py', 'selfdrive/ui/layouts/settings/settings.py']
    for name in files:
      ast.parse((ROOT / name).read_text(), filename=name)

  def test_home_and_settings_names(self):
    home = (ROOT / 'selfdrive/ui/layouts/home.py').read_text()
    self.assertIn("gui_label(title, 'ROADLINE'", home)
    self.assertIn('brand = "Roadline"', home)
    self.assertIn('PanelInfo(tr_noop("Roadline"), NAPLayout())', (ROOT / 'selfdrive/ui/layouts/settings/settings.py').read_text())

  def test_nap_compatibility_paths_preserved(self):
    home = (ROOT / 'selfdrive/ui/layouts/home.py').read_text()
    for token in ['/data/nap_destination_presets.json', 'X-NAP-Phone-Key', 'http://127.0.0.1:7070/phone-nav/api/start']:
      self.assertIn(token, home)

  def test_video_is_only_startup_presentation(self):
    module = (ROOT / 'system/ui/roadline_spinner.py').read_text()
    for forbidden in ['Params(', 'ui_state', 'messaging', 'socket', 'subprocess', 'time.sleep', '.join(']:
      self.assertNotIn(forbidden, module)
    self.assertIn('self.spinner_proc.kill()', (ROOT / 'common/spinner.py').read_text())

  def test_no_legacy_logo_reference(self):
    for relative in ['selfdrive/ui', 'system/ui']:
      for file in (ROOT / relative).rglob('*.py'):
        self.assertNotIn('spinner_comma.png', file.read_text())


if __name__ == '__main__':
  unittest.main(verbosity=2)
