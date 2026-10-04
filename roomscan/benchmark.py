"""Reproducible, data-only measurements for the three supplied scan bundles.

The interleaved frame subsets measure within-capture sampling stability. They
are not repeat captures and must not be presented as repeatability or accuracy
against physical ground truth.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import tempfile
from pathlib import Path

from .pipeline import reconstruct
from .vision import reconstruct_rgb, _vision_modules


DEFAULT_BUNDLES = (
    ("single_room", "single_room", False),
    ("single_scan_floor_only", "single_scan_floor_only", False),
    ("single_scan_with_ceiling", "single_scan_with_ceiling", True),
)


def _capture_dir(root: Path, folder: str) -> Path:
    candidates = sorted((root / folder).glob("*/odometry.csv"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one capture with odometry.csv under {root / folder}; found {len(candidates)}"
        )
    return candidates[0].parent


def _metric(plan: dict, key: str):
    value = (plan.get("measurements") or {}).get(key)
    return value.get("value") if isinstance(value, dict) else None


def _spread_percent(first, second):
    if first is None or second is None:
        return None
    mean = (abs(first) + abs(second)) / 2.0
    return (abs(first - second) / mean * 100.0) if mean else 0.0


def _load_plan(output_dir: Path):
    return json.loads((output_dir / "plan.json").read_text(encoding="utf-8"))


def _measure_bundle(root: Path, output_root: Path, label: str, folder: str, ceiling_observed: bool, frame_stride: int, pixel_stride: int, max_video_frames: int):
    capture_dir = _capture_dir(root, folder)
    full_dir = output_root / "runs" / label / "full"
    full = reconstruct(
        capture_dir,
        full_dir,
        frame_stride=frame_stride,
        pixel_stride=pixel_stride,
        tier="lidar",
        ceiling_observed=ceiling_observed,
    )
    full_plan = _load_plan(full_dir)

    # The union of these two disjoint sets is the normal frame-stride sample.
    # Using the same pixels and fewer frames in each half isolates frame-sampling
    # sensitivity within the one supplied trajectory.
    split_plans = []
    with tempfile.TemporaryDirectory(prefix=f"{label}-split-", dir=output_root) as temporary:
        temp_root = Path(temporary)
        for split_name, offset in (("A", 0), ("B", frame_stride)):
            split_dir = temp_root / split_name
            reconstruct(
                capture_dir,
                split_dir,
                frame_stride=frame_stride * 2,
                pixel_stride=pixel_stride,
                tier="lidar",
                ceiling_observed=ceiling_observed,
                frame_offset=offset,
            )
            split_plans.append(_load_plan(split_dir))

    first, second = split_plans
    area_a, area_b = _metric(first, "floor_area"), _metric(second, "floor_area")
    width_a = _metric(first, "footprint_axis_aligned_width_x")
    width_b = _metric(second, "footprint_axis_aligned_width_x")
    length_a = _metric(first, "footprint_axis_aligned_length_z")
    length_b = _metric(second, "footprint_axis_aligned_length_z")
    height_a = (first.get("rooms") or [{}])[0].get("ceiling_height", {}).get("value")
    height_b = (second.get("rooms") or [{}])[0].get("ceiling_height", {}).get("value")
    video_path = capture_dir / "rgb.mp4"
    ablation_path = full_dir / "drift_ablation.json"
    ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
    photo_dir = output_root / "runs" / label / "photo"
    video_dir = output_root / "runs" / label / "video"
    photo_result = reconstruct_rgb(capture_dir, photo_dir, "photo", photo_count=8)
    video_result = reconstruct_rgb(capture_dir, video_dir, "video", max_video_frames=max_video_frames)
    lidar_area = _metric(full_plan, "floor_area")
    photo_area = _metric(photo_result, "floor_area")
    video_area = _metric(video_result, "floor_area")

    def lidar_difference_percent(value):
        if value is None or lidar_area in (None, 0):
            return None
        return abs(value - lidar_area) / abs(lidar_area) * 100.0

    row = {
        "bundle": label,
        "capture_id": capture_dir.name,
        "processing_status": full_plan.get("processing_status"),
        "floor_area_proxy_m2": _metric(full_plan, "floor_area"),
        "footprint_width_proxy_m": _metric(full_plan, "footprint_axis_aligned_width_x"),
        "footprint_length_proxy_m": _metric(full_plan, "footprint_axis_aligned_length_z"),
        "observed_vertical_extent_proxy_m": (full_plan.get("rooms") or [{}])[0].get("ceiling_height", {}).get("value"),
        "depth_frames_available": full_plan.get("capture_statistics", {}).get("depth_frames_available"),
        "depth_frames_processed": full_plan.get("capture_statistics", {}).get("processed_depth_frames"),
        "capture_duration_s": full_plan.get("capture_statistics", {}).get("duration_seconds"),
        "rgb_video_present": video_path.is_file(),
        "rgb_video_bytes": video_path.stat().st_size if video_path.is_file() else None,
        "photo_visual_hull_area_proxy_m2": photo_area,
        "photo_rgb_frames_used": photo_result.get("capture_statistics", {}).get("rgb_decoded_frame_count"),
        "photo_visual_points": photo_result.get("capture_statistics", {}).get("triangulated_unique_point_count"),
        "photo_video_odometry_frame_count_match": photo_result.get("capture_statistics", {}).get("odometry_video_frame_count_match"),
        "photo_median_reprojection_error_px": photo_result.get("capture_statistics", {}).get("median_reprojection_error_px"),
        "photo_area_difference_from_lidar_percent": lidar_difference_percent(photo_area),
        "video_visual_hull_area_proxy_m2": video_area,
        "video_rgb_frames_used": video_result.get("capture_statistics", {}).get("rgb_decoded_frame_count"),
        "video_visual_points": video_result.get("capture_statistics", {}).get("triangulated_unique_point_count"),
        "video_video_odometry_frame_count_match": video_result.get("capture_statistics", {}).get("odometry_video_frame_count_match"),
        "video_median_reprojection_error_px": video_result.get("capture_statistics", {}).get("median_reprojection_error_px"),
        "opencv_version": video_result.get("capture_statistics", {}).get("opencv_version"),
        "video_area_difference_from_lidar_percent": lidar_difference_percent(video_area),
        "rgb_comparison_interpretation": "cross_modal_difference_from_LiDAR_not_physical_accuracy",
        "split_a_frames": first.get("capture_statistics", {}).get("processed_depth_frames"),
        "split_b_frames": second.get("capture_statistics", {}).get("processed_depth_frames"),
        "split_area_a_proxy_m2": area_a,
        "split_area_b_proxy_m2": area_b,
        "split_area_absolute_difference_m2": abs(area_a - area_b) if area_a is not None and area_b is not None else None,
        "split_area_difference_percent": _spread_percent(area_a, area_b),
        "split_width_absolute_difference_m": abs(width_a - width_b) if width_a is not None and width_b is not None else None,
        "split_length_absolute_difference_m": abs(length_a - length_b) if length_a is not None and length_b is not None else None,
        "split_height_absolute_difference_m": abs(height_a - height_b) if height_a is not None and height_b is not None else None,
        "loop_closure_residual_m": (ablation.get("loop_closure") or {}).get("pre_correction_residual_m"),
        "physical_accuracy_status": "not_evaluated_no_independent_ground_truth",
        "repeatability_status": "not_evaluated_single_capture_only",
        "split_metric_interpretation": "within_capture_sampling_stability_not_repeatability",
    }
    row["photo_status"] = photo_result.get("processing_status")
    row["video_status"] = video_result.get("processing_status")
    return row


def run_benchmark(root: Path, output_dir: Path, frame_stride: int = 30, pixel_stride: int = 6, max_video_frames: int = 100):
    if frame_stride < 1 or pixel_stride < 1:
        raise ValueError("frame_stride and pixel_stride must be positive integers")
    root = root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2, _ = _vision_modules()

    rows = []
    for label, folder, ceiling_observed in DEFAULT_BUNDLES:
        row = _measure_bundle(
            root, output_dir, label, folder, ceiling_observed, frame_stride, pixel_stride, max_video_frames
        )
        rows.append(row)

    report = {
        "benchmark_version": "supplied-scan-internal/1.0",
        "inputs": [folder for _, folder, _ in DEFAULT_BUNDLES],
        "method": {
            "primary_measurements": "Existing LiDAR depth and camera-pose projection pipeline; all dimensions are uncalibrated geometric proxies.",
            "sampling_stability": "Two disjoint interleaved frame subsets at twice the normal stride. Their union is the normal sampled sequence.",
            "ground_truth": "No independent laser/tape dimensions are present in the three supplied folders; accuracy gates are not evaluated.",
            "repeatability": "No second capture of the same room is present; within-capture split differences are not repeatability.",
            "photo_video": "Sparse RGB feature clouds are triangulated with the synchronized metric poses and intrinsics present in the same capture folder; depth/ and confidence/ are not read by these tiers. The photo tier uses eight still frames sampled from rgb.mp4 because the folders contain no separate photo files.",
            "cross_modal_comparison": "Photo/video hull areas are compared with the LiDAR hull area from the same bundle. This is modality consistency only; the LiDAR estimate is not independent physical ground truth.",
        },
        "configuration": {"frame_stride": frame_stride, "pixel_stride": pixel_stride, "photo_still_count": 8, "max_video_frames": max_video_frames, "opencv_version": cv2.__version__, "python_version": platform.python_version(), "units": "m"},
        "measurements": rows,
    }
    (output_dir / "benchmark_measurements.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )

    csv_path = output_dir / "benchmark_measurements.csv"
    fields = list(rows[0]) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Supplied-Scan Benchmark Measurements",
        "",
        "This benchmark uses only the three supplied folders. Values are measured from the current LiDAR reconstruction and are not ground-truth accuracy scores.",
        f"Runtime: Python {platform.python_version()}, OpenCV {cv2.__version__}; frame stride {frame_stride}, pixel stride {pixel_stride}, video cap {max_video_frames} frames.",
        "",
        "| Scan | LiDAR area (m²) | Photo points | Photo area (m²) | Video points | Video area (m²) | Video vs LiDAR (%) | Split LiDAR area difference (%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        def fmt(key, digits=3):
            value = row.get(key)
            return "—" if value is None else f"{value:.{digits}f}"
        lines.append(
            f"| `{row['bundle']}` | {fmt('floor_area_proxy_m2')} | {row['photo_visual_points']} | "
            f"{fmt('photo_visual_hull_area_proxy_m2')} | {row['video_visual_points']} | {fmt('video_visual_hull_area_proxy_m2')} | "
            f"{fmt('video_area_difference_from_lidar_percent', 2)} | {fmt('split_area_difference_percent', 2)} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- LiDAR area, width, length, and vertical extent are geometric proxies from the supplied scans; they are not tape-measured room dimensions.",
        "- Photo uses up to eight still frames sampled from the bundled RGB video; video uses a deterministic subsample of the full RGB stream. Both triangulate RGB feature matches with camera poses and intrinsics from the same bundle. Neither reads depth/ or confidence/.",
        "- Photo/video versus LiDAR differences are internal cross-modal comparisons, not errors against an independent truth source. These pose-assisted paths are not strict image-only tiers.",
        "- Split differences compare interleaved frames from one scan and describe sensitivity to frame sampling only. They are not repeat-scan repeatability.",
        "- Photo/video metric accuracy, opening width, ceiling accuracy, staged-damage detection, multi-room stitching, and consumer-app comparison are not measured by this dataset.",
        "- No acceptance gate is marked passed without the corresponding independent reference data.",
        "",
        "## Reproduce",
        "",
        f"`python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride {frame_stride} --pixel-stride {pixel_stride} --max-video-frames {max_video_frames}`",
        "",
    ])
    (output_dir / "benchmark_summary.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Measure data-derived LiDAR proxies and within-capture sampling stability for the supplied bundles.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root containing the three supplied scan folders")
    parser.add_argument("--output", type=Path, default=Path("outputs/benchmark"), help="Directory for benchmark JSON, CSV, and Markdown outputs")
    parser.add_argument("--frame-stride", type=int, default=30)
    parser.add_argument("--pixel-stride", type=int, default=6)
    parser.add_argument("--max-video-frames", type=int, default=100, help="Maximum video-tier RGB frames per bundle")
    args = parser.parse_args(argv)
    try:
        result = run_benchmark(args.root, args.output, args.frame_stride, args.pixel_stride, args.max_video_frames)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({"output_dir": args.output.resolve().as_posix(), "bundle_count": len(result["measurements"]), "status": "complete_data_only_measurements"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
