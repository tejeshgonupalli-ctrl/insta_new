import subprocess
from pathlib import Path


def trim_video(input_path, max_seconds=30):
    """
    Trim video to first `max_seconds`
    Returns trimmed video path
    """
    input_path = Path(input_path)
    output_path = input_path.with_name(
        input_path.stem + f"_trim{input_path.suffix}"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-t", str(max_seconds),
        "-c", "copy",
        str(output_path)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return str(output_path)
