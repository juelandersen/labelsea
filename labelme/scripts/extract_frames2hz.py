import cv2
import argparse
from pathlib import Path
import sys
import math

def time_to_seconds(time_str):
    """Convert hh:mm:ss to total seconds"""
    try:
        h, m, s = map(int, time_str.split(":"))
        return h * 3600 + m * 60 + s
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Time must be in format hh:mm:ss"
        )

def main():
    parser = argparse.ArgumentParser(
        description="Extract frames at exact timestamps every 0.5 seconds"
    )

    parser.add_argument(
        "--video",
        required=True,
        help="Path to input mp4 video"
    )

    parser.add_argument(
        "--start",
        type=time_to_seconds,
        default=0,
        help="Start time (hh:mm:ss)"
    )

    parser.add_argument(
        "--end",
        type=time_to_seconds,
        default=None,
        help="End time (hh:mm:ss)"
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Output directory for frames"
    )

    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Video not found: {video_path}")
        sys.exit(1)

    # Default output folder: named after video
    if args.output is None:
        output_dir = video_path.parent / video_path.stem
    else:
        output_dir = Path(args.output)

    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("Could not open video")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    start_sec = args.start
    end_sec = args.end if args.end is not None else duration

    if start_sec >= end_sec:
        print("Start time must be before end time")
        sys.exit(1)

    print(f"Extracting frames from {start_sec:.1f}s to {end_sec:.1f}s")
    print("Sampling exactly every 0.5 seconds")
    print(f"Saving to: {output_dir}")

    step = 0.5  # seconds
    saved_idx = 0

    # Ensure clean floating-point stepping
    n_steps = int(math.floor((end_sec - start_sec) / step)) + 1

    for i in range(n_steps):
        t = start_sec + i * step

        # Seek by exact timestamp (milliseconds)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ret, frame = cap.read()
        if not ret:
            break

        out_name = output_dir / f"frame_{saved_idx:06d}_{t:.1f}s.jpg"
        cv2.imwrite(str(out_name), frame)
        saved_idx += 1

    cap.release()
    print(f"Done. Extracted {saved_idx} frames.")

if __name__ == "__main__":
    main()
