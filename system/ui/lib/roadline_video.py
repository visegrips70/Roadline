"""Bounded, asynchronous decoding of Roadline's bundled startup movie.

No display, CAN, parameters, network, or manager dependencies. Importing PyAV
and decoding are deliberately confined to a daemon worker, never the UI loop.
"""
import queue
import threading
import time
from pathlib import Path

DURATION = 4.5
FPS = 30
FRAME_COUNT = 135
DECODE_WIDTH = 1080
DECODE_HEIGHT = 540


class RoadlineVideo:
  def __init__(self, path: Path):
    self.path = path
    self.frames = queue.Queue(maxsize=2)
    self.stopped = threading.Event()
    self.finished = threading.Event()
    self.error: str | None = None
    self._pending = None
    self._thread = None

  def start(self):
    if self._thread is None and not self.stopped.is_set():
      self._thread = threading.Thread(target=self._decode, name="roadline-splash", daemon=True)
      self._thread.start()

  def _decode(self):
    try:
      if not self.path.is_file() or not 0 < self.path.stat().st_size <= 4 * 1024 * 1024:
        raise ValueError("Bundled startup movie is missing or exceeds the size limit")
      import av
      began = time.monotonic()
      with av.open(str(self.path), mode="r") as movie:
        stream = movie.streams.video[0]
        if stream.width != 2160 or stream.height != 1080 or stream.average_rate != FPS:
          raise ValueError("Unexpected startup movie format")
        stream.codec_context.thread_count = 1
        for index, frame in enumerate(movie.decode(stream)):
          if index >= FRAME_COUNT or self.stopped.is_set() or time.monotonic() - began > DURATION + 2:
            break
          # One quarter of the full-resolution pixel count keeps GPU uploads small.
          pixels = frame.reformat(width=DECODE_WIDTH, height=DECODE_HEIGHT, format="rgba").to_ndarray()
          while not self.stopped.is_set():
            try:
              self.frames.put((index / FPS, pixels), timeout=0.03)
              break
            except queue.Full:
              if time.monotonic() - began > DURATION + 2:
                return
    except Exception as exc:
      self.error = str(exc)
    finally:
      self.finished.set()

  def sample(self, elapsed: float):
    """Latest due frame, or None. Never wait for the decoder or drain unboundedly."""
    if self.stopped.is_set() or elapsed >= DURATION:
      self.close()
      return None
    latest = None
    for _ in range(3):  # two queued frames plus one previously held future frame
      if self._pending is None:
        try:
          self._pending = self.frames.get_nowait()
        except queue.Empty:
          break
      if self._pending[0] > elapsed:
        break
      latest = self._pending[1]
      self._pending = None
    return latest

  def close(self):
    # No join: missing/corrupt media must never hold up startup or teardown.
    self.stopped.set()
    self._pending = None
    for _ in range(2):
      try:
        self.frames.get_nowait()
      except queue.Empty:
        break
