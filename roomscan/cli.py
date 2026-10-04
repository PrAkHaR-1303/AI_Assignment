from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import reconstruct


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reconstruct an exploratory LiDAR floor outline from a supplied capture bundle.")
    parser.add_argument("capture", type=Path, help="Capture directory containing depth/, confidence/, odometry.csv, and camera_matrix.csv")
    parser.add_argument("--output", type=Path, default=Path("outputs"), help="Directory for plan.json, plan.svg, and drift ablation")
    parser.add_argument("--frame-stride", type=int, default=30, help="Use every Nth depth frame (default: 30)")
    parser.add_argument("--pixel-stride", type=int, default=6, help="Use every Nth pixel in each direction (default: 6)")
    parser.add_argument("--depth-scale", type=float, default=0.001, help="Convert stored depth units to meters (default: millimeters)")
    parser.add_argument("--tier", choices=("lidar", "video", "photo"), default="lidar", help="Input tier; photo/video use the same output contract but are currently marked unsupported")
    parser.add_argument("--ceiling-observed", action="store_true", help="Mark that an operator verified the scan includes a visible ceiling surface")
    args = parser.parse_args(argv)
    try:
        if args.tier != "lidar":
            raise ValueError(f"The {args.tier} reconstruction adapter is not implemented. The supplied bundles contain LiDAR depth and poses.")
        result = reconstruct(args.capture, args.output, args.frame_stride, args.pixel_stride, args.depth_scale, args.tier, args.ceiling_observed)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps({"capture_id": result["capture_id"], "status": result["processing_status"], "output_dir": args.output.resolve().as_posix(), "processed_frames": result["capture_statistics"]["processed_depth_frames"]}, indent=2))
    return 0
