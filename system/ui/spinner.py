#!/usr/bin/env python3
import select
import sys

import pyray as rl

from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.roadline_spinner import RoadlineFallback, RoadlineSpinner


def _read_stdin():
  """Non-blocking read of available lines from stdin."""
  lines = []
  while True:
    rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
    if not rlist:
      break
    line = sys.stdin.readline().strip()
    if line == "":
      break
    lines.append(line)
  return lines


def main():
  gui_app.init_window("Roadline startup")
  try:
    spinner = RoadlineSpinner()
  except Exception as exc:
    print(f"Roadline startup unavailable; using wordmark: {exc}", file=sys.stderr)
    spinner = RoadlineFallback()
  last_text = ""
  try:
    for _ in gui_app.render():
      text_list = _read_stdin()
      if text_list:
        last_text = text_list[-1]
        spinner.set_text(last_text)
      try:
        spinner.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
      except Exception as exc:
        if type(spinner) is RoadlineFallback:
          raise
        print(f"Roadline video drawing failed; using wordmark: {exc}", file=sys.stderr)
        try:
          spinner.close()
        except Exception:
          pass
        spinner = RoadlineFallback()
        spinner.set_text(last_text)
        spinner.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
  finally:
    spinner.close()


if __name__ == "__main__":
  main()
