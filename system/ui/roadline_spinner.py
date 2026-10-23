"""Roadline green/white startup presentation; no driving/control dependencies."""
import sys
import time

import pyray as rl

from openpilot.system.ui.lib.application import ASSETS_DIR, gui_app
from openpilot.system.ui.lib.roadline_video import DECODE_HEIGHT, DECODE_WIDTH, DURATION, RoadlineVideo
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.text import wrap_text
from openpilot.system.ui.widgets import Widget

GREEN = rl.Color(39, 165, 75, 255)
TRACK = rl.Color(16, 33, 21, 255)


def fit_texture(texture, rect):
  if texture.width <= 0 or texture.height <= 0:
    return
  scale = min(rect.width / texture.width, rect.height / texture.height)
  width, height = texture.width * scale, texture.height * scale
  dest = rl.Rectangle(rect.x + (rect.width - width) / 2, rect.y + (rect.height - height) / 2, width, height)
  rl.draw_texture_pro(texture, rl.Rectangle(0, 0, texture.width, texture.height), dest, rl.Vector2(0, 0), 0.0, rl.WHITE)


class RoadlineFallback(Widget):
  """Asset-independent branding that retains the real progress/message contract."""
  def __init__(self):
    super().__init__()
    self._progress = None
    self._status = ""

  def set_text(self, value: str):
    # Keep upstream numeric progress semantics. Branding never invents a percent.
    if value.isascii() and value.isdigit():
      self._progress = max(0, min(100, int(value)))
      self._status = ""
    else:
      self._progress = None
      self._status = value

  @staticmethod
  def _wordmark(rect):
    font = gui_app.font()
    size = min(112.0, rect.width / 9)
    width = measure_text_cached(font, "ROADLINE", size).x
    x, y = rect.x + (rect.width - width) / 2, rect.y + rect.height * 0.42
    rl.draw_text_ex(font, "ROAD", rl.Vector2(x, y), size, 0.0, rl.WHITE)
    x += measure_text_cached(font, "ROAD", size).x
    rl.draw_text_ex(font, "LINE", rl.Vector2(x, y), size, 0.0, GREEN)

  def _status_panel(self, rect):
    w, h = rect.width, rect.height
    bar = rl.Rectangle(rect.x + w * 0.27, rect.y + h * 0.85, w * 0.46, max(5, h * 0.008))
    rl.draw_rectangle_rounded(bar, 1, 10, TRACK)
    if self._progress is not None:
      if self._progress > 0:
        rl.draw_rectangle_rounded(rl.Rectangle(bar.x, bar.y, bar.width * self._progress / 100, bar.height), 1, 10, GREEN)
    else:
      phase = (time.monotonic() * 0.5) % 1
      rl.draw_rectangle_rounded(rl.Rectangle(bar.x + bar.width * 0.8 * phase, bar.y, bar.width * 0.2, bar.height), 1, 10, GREEN)
    if self._status:
      font_size = max(16, min(30, h * 0.027))
      lines = wrap_text(self._status, font_size, w * 0.88)
      # Grow upwards for long real startup/error messages, rather than hide them.
      line_height = font_size * 1.15
      top = min(rect.y + h * 0.89, rect.y + h * 0.98 - len(lines) * line_height)
      rl.draw_rectangle_rec(rl.Rectangle(rect.x, top - 4, w, len(lines) * line_height + 8), rl.BLACK)
      for i, line in enumerate(lines):
        size = measure_text_cached(gui_app.font(), line, font_size)
        rl.draw_text_ex(gui_app.font(), line, rl.Vector2(rect.x + (w - size.x) / 2, top + i * line_height), font_size, 0, rl.WHITE)

  def _render(self, rect):
    rl.draw_rectangle_rec(rect, rl.BLACK)
    self._wordmark(rect)
    self._status_panel(rect)

  def close(self):
    pass


class RoadlineSpinner(RoadlineFallback):
  """Play the approved video once, then hold the approved still until dismissed.

  Only the existing startup-spinner process owns this widget. The parent remains
  free to terminate that process immediately; playback never delays readiness.
  """
  def __init__(self):
    super().__init__()
    self._video = RoadlineVideo(ASSETS_DIR.joinpath("roadline/startup.mp4"))
    self._started = None
    self._video_texture = None
    self._still = None
    self._still_attempted = False
    self._failed = False

  def _draw_still(self, rect):
    if not self._still_attempted:
      self._still_attempted = True
      try:
        if ASSETS_DIR.joinpath("roadline/startup_still.png").is_file():
          self._still = gui_app.texture("roadline/startup_still.png")
      except Exception as exc:
        print(f"Roadline still unavailable: {exc}", file=sys.stderr)
    if self._still and self._still.width > 0 and self._still.height > 0:
      fit_texture(self._still, rect)
    else:
      self._wordmark(rect)

  def _render(self, rect):
    if rect.width <= 0 or rect.height <= 0:
      return
    now = time.monotonic()
    if self._started is None:
      self._started = now
      self._video.start()
    elapsed = now - self._started
    rl.draw_rectangle_rec(rect, rl.BLACK)
    artwork = rl.Rectangle(rect.x, rect.y, rect.width, rect.height * 0.84)
    if not self._failed and elapsed < DURATION:
      pixels = self._video.sample(elapsed)
      if pixels is not None:
        if self._video_texture is None:
          image = rl.gen_image_color(DECODE_WIDTH, DECODE_HEIGHT, rl.BLACK)
          try:
            self._video_texture = rl.load_texture_from_image(image)
            if self._video_texture.id == 0:
              raise RuntimeError("Video texture allocation failed")
            rl.set_texture_filter(self._video_texture, rl.TextureFilter.TEXTURE_FILTER_BILINEAR)
          finally:
            rl.unload_image(image)
        rl.update_texture(self._video_texture, rl.ffi.cast("void *", pixels.ctypes.data))
      if self._video.error or (self._video_texture is None and elapsed > 1.0):
        self._failed = True
        self._video.close()
        print(f"Roadline video unavailable; using still: {self._video.error or 'decoder startup timeout'}", file=sys.stderr)
    if elapsed >= DURATION or self._failed:
      self._video.close()
      self._draw_still(artwork)
    elif self._video_texture is not None:
      fit_texture(self._video_texture, artwork)
    self._status_panel(rect)

  def close(self):
    self._video.close()
    if self._video_texture is not None:
      rl.unload_texture(self._video_texture)
      self._video_texture = None
