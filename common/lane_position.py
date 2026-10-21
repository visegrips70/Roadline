"""Lane preference in centimetres; independent of camera calibration."""

MIN_OFFSET_CM = -30
MAX_OFFSET_CM = 30
LEGACY_OFFSETS_CM = {-3: -30, -2: -23, -1: -15, 0: 0, 1: 15, 2: 23, 3: 30}


def parse_offset_cm(value):
  """Reject malformed/out-of-range settings instead of silently rounding them."""
  if isinstance(value, bool):
    raise ValueError("Use a whole number of centimetres")
  if isinstance(value, bytes):
    value = value.decode("ascii")
  if isinstance(value, str):
    value = value.strip()
    if not value or not value.lstrip("+-").isascii() or not value.lstrip("+-").isdigit():
      raise ValueError("Use a whole number of centimetres")
    value = int(value)
  if not isinstance(value, int) or not MIN_OFFSET_CM <= value <= MAX_OFFSET_CM:
    raise ValueError("Lane position must be between -30 and +30 cm")
  return value


def resolve_offset_cm(value, legacy_value=0):
  """An absent new key preserves old presets; a corrupt new key falls to centre."""
  if value is None:
    # Params normally returns an int. Also accept its historical text encoding.
    try:
      legacy = parse_offset_cm(legacy_value)
    except (ValueError, UnicodeError):
      return 0
    return LEGACY_OFFSETS_CM.get(legacy, 0)
  try:
    return parse_offset_cm(value)
  except (ValueError, UnicodeError):
    return 0


def offset_label(value):
  cm = resolve_offset_cm(value)
  return "Center" if cm == 0 else f"{'Right' if cm > 0 else 'Left'} {abs(cm)} cm"
