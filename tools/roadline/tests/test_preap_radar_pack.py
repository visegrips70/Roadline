from pathlib import Path
import subprocess


def test_radar_packet_encoding_with_undefined_behavior_sanitizer(tmp_path):
  root = Path(__file__).resolve().parents[3]
  source = Path(__file__).with_name("preap_radar_pack.c")
  executable = tmp_path / "radar_pack"
  compilation = subprocess.run([
    "gcc", "-std=gnu11", "-O1", "-g", "-fsanitize=undefined",
    "-fno-sanitize-recover=undefined", "-I", str(root / "opendbc_repo"),
    str(source), "-lm", "-o", str(executable),
  ], capture_output=True, text=True)
  assert compilation.returncode == 0, compilation.stderr
  result = subprocess.run([str(executable)], check=True, capture_output=True, text=True)
  assert "65536 radar speed/counter combinations passed" in result.stdout
