def seconds_to_mmss(seconds: float) -> str:
    """Convert seconds to MM:SS.mmm format."""
    if seconds is None or seconds < 0:
        return "00:00.000"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def seconds_to_hms(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    if seconds is None or seconds < 0:
        return "00:00:00"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"
