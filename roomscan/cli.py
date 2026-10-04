from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import reconstruct
from .vision import reconstruct_rgb


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reconstruct a sparse RGB or LiDAR room outline from a supplied capture bundle.")
    parser.add_argument("capture", type=Path, help="Capture directory containing rgb.mp4, odometry.csv, and camera_matrix.csv; LiDAR also needs depth/")
    parser.add_argument("--output", type=Path, default=Path("outputs"), help="Directory for plan.json and plan.svg; LiDAR also writes its drift ablation")
    parser.add_argument("--frame-stride", type=int, default=30, help="Use every Nth depth frame (default: 30)")
    parser.add_argument("--frame-offset", type=int, default=0, help="Frame residue within the stride; used by the data-only stability benchmark")
    parser.add_argument("--pixel-stride", type=int, default=6, help="Use every Nth pixel in each direction (default: 6)")
    parser.add_argument("--depth-scale", type=float, default=0.001, help="Convert stored depth units to meters (default: millimeters)")
    parser.add_argument("--tier", choices=("lidar", "video", "photo"), default="lidar", help="Input tier to reconstruct")
    parser.add_argument("--photo-count", type=int, default=8, help="Photo tier stills sampled from the bundled RGB video (2-8; default 8)")
    parser.add_argument("--max-video-frames", type=int, default=350, help="Maximum RGB frames used by the video tier")
    parser.add_argument("--ceiling-observed", action="store_true", help="Mark that an operator verified the scan includes a visible ceiling surface")
    args = parser.parse_args(argv)
    try:
        if args.tier == "lidar":
            result = reconstruct(args.capture, args.output, args.frame_stride, args.pixel_stride, args.depth_scale, args.tier, args.ceiling_observed, args.frame_offset)
        else:
            result = reconstruct_rgb(args.capture, args.output, args.tier, args.photo_count, args.max_video_frames)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.error(str(error))
    stats = result["capture_statistics"]
    processed = stats.get("processed_depth_frames", stats.get("rgb_decoded_frame_count"))
    print(json.dumps({"capture_id": result["capture_id"], "tier": result["input_tier"], "status": result["processing_status"], "output_dir": args.output.resolve().as_posix(), "processed_frames": processed}, indent=2))
    return 0
