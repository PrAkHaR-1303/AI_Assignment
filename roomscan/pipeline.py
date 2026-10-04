"""Reconstruct an exploratory LiDAR-tier floor outline and export case-study JSON/SVG."""

from __future__ import annotations

import csv
import html
import json
import math
import statistics
import time
from array import array
from pathlib import Path

from .geometry import close_trajectory, convex_hull, polygon_area, quantile, rotate_by_quaternion, simplify_closed_polygon
from .png import read_gray_png


SCHEMA_VERSION = "applied-ai-case-study/0.1"


def _portable_path(path: Path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{(key or "").strip(): (value or "").strip() for key, value in row.items()} for row in reader]


def _read_intrinsics(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append([float(value.strip()) for value in line.split(",")])
    if len(rows) != 3 or any(len(row) != 3 for row in rows):
        raise ValueError(f"Expected a 3x3 camera matrix: {path}")
    return rows


def _pose(row):
    return {
        "timestamp": float(row["timestamp"]),
        "frame": row["frame"].strip(),
        "x": float(row["x"]),
        "y": float(row["y"]),
        "z": float(row["z"]),
        "qx": float(row["qx"]),
        "qy": float(row["qy"]),
        "qz": float(row["qz"]),
        "qw": float(row["qw"]),
        "fx": float(row["fx"]),
        "fy": float(row["fy"]),
        "cx": float(row["cx"]),
        "cy": float(row["cy"]),
    }


def _project_frame(depth, confidence, pose, matrix, corrected_pose, pixel_stride, depth_scale):
    width, height = depth.width, depth.height
    rgb_width = max(1.0, matrix[0][2] * 2.0)
    rgb_height = max(1.0, matrix[1][2] * 2.0)
    sx, sy = width / rgb_width, height / rgb_height
    fx, fy = pose["fx"] * sx, pose["fy"] * sy
    cx, cy = pose["cx"] * sx, pose["cy"] * sy
    if fx <= 0 or fy <= 0:
        raise ValueError(f"Invalid focal length at frame {pose['frame']}")

    raw_points = []
    fixed_points = []
    q = (pose["qx"], pose["qy"], pose["qz"], pose["qw"])
    for v in range(0, height, pixel_stride):
        for u in range(0, width, pixel_stride):
            confidence_value = confidence.at(u, v) if confidence is not None else 255
            if confidence_value == 0:
                continue
            distance = depth.at(u, v) * depth_scale
            if distance < 0.15 or distance > 10.0:
                continue
            camera_point = ((u - cx) * distance / fx, -(v - cy) * distance / fy, -distance)
            rotated = rotate_by_quaternion(camera_point, q)
            raw_points.append((rotated[0] + pose["x"], rotated[1] + pose["y"], rotated[2] + pose["z"]))
            fixed_points.append(
                (
                    rotated[0] + corrected_pose["x"],
                    rotated[1] + corrected_pose["y"],
                    rotated[2] + corrected_pose["z"],
                )
            )
    return raw_points, fixed_points


def _estimate_plan(points, ceiling_observed=False):
    xs, ys, zs = array("f"), array("f"), array("f")
    for x, y, z in points:
        xs.append(x)
        ys.append(y)
        zs.append(z)
    if len(xs) < 40:
        return {"status": "insufficient_points", "point_count": len(xs), "polygon": [], "walls": [], "area_m2": None, "ceiling_height_m": None}

    floor_y = quantile(ys, 0.02)
    upper_y = quantile(ys, 0.98)
    ceiling_height = max(0.0, upper_y - floor_y) if ceiling_observed else None

    # Use points away from the floor/uppermost surface so the hull follows wall faces.
    low_band = floor_y + 0.20
    high_band = min(floor_y + 2.30, upper_y - 0.12)
    wall_samples = [(float(xs[i]), float(zs[i])) for i, y in enumerate(ys) if low_band <= y <= high_band]
    if len(wall_samples) < 20:
        wall_samples = [(float(x), float(z)) for x, z in zip(xs, zs)]
    polygon = simplify_closed_polygon(convex_hull(wall_samples))
    area = polygon_area(polygon)
    walls = []
    for i, start in enumerate(polygon):
        end = polygon[(i + 1) % len(polygon)]
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length >= 0.15:
            walls.append({"wall_id": f"wall_{len(walls)+1:02d}", "classification_status": "candidate_hull_edge_unverified_as_wall", "start_xz_m": [round(start[0], 3), round(start[1], 3)], "end_xz_m": [round(end[0], 3), round(end[1], 3)], "length_m": round(length, 3)})
    status = "outline_estimated" if len(polygon) >= 3 and area > 0 else "outline_unavailable"
    return {
        "status": status,
        "point_count": len(xs),
        "floor_reference_y_m": round(floor_y, 3),
        "observed_vertical_extent_m": round(max(0.0, upper_y - floor_y), 3),
        "polygon": [[round(x, 3), round(z, 3)] for x, z in polygon],
        "walls": walls,
        "area_m2": round(area, 3) if area > 0 else None,
        "ceiling_height_m": round(ceiling_height, 3) if ceiling_height is not None else None,
        "ceiling_evidence": "operator_confirmed_capture" if ceiling_observed else "not_confirmed",
    }


def _interval(value, absolute_floor, relative):
    if value is None:
        return None
    half_width = max(absolute_floor, abs(value) * relative)
    return {"lower": round(value - half_width, 3), "upper": round(value + half_width, 3), "confidence_level": 0.95, "calibration_status": "uncalibrated_assumption"}


def _measurement(value, unit, absolute_floor, relative, status="estimated"):
    return {"value": value, "unit": unit, "interval_95": _interval(value, absolute_floor, relative), "status": status}


def _render_svg(plan, output_path: Path, title: str, source_label="exploratory LiDAR estimate", footer_note="Plan outline is a convex hull of sampled depth points; openings and damage are not assessed."):
    polygon = plan.get("polygon") or []
    if len(polygon) < 3:
        content = "<text x='40' y='80' font-size='16'>No stable room outline could be estimated.</text>"
        output_path.write_text(_svg_shell(title, 900, 620, content), encoding="utf-8")
        return
    min_x = min(point[0] for point in polygon); max_x = max(point[0] for point in polygon)
    min_z = min(point[1] for point in polygon); max_z = max(point[1] for point in polygon)
    span_x = max(0.5, max_x - min_x); span_z = max(0.5, max_z - min_z)
    scale = min(740 / span_x, 450 / span_z)
    margin_x, margin_y = 80.0, 110.0
    px = lambda x: margin_x + (x - min_x) * scale
    py = lambda z: margin_y + (max_z - z) * scale
    coords = " ".join(f"{px(x):.1f},{py(z):.1f}" for x, z in polygon)
    items = [f"<polygon points='{coords}' fill='#edf3f8' stroke='#17324d' stroke-width='4' stroke-linejoin='round'/> "]
    for index, wall in enumerate(plan.get("walls", [])):
        sx, sz = wall["start_xz_m"]; ex, ez = wall["end_xz_m"]
        mx, mz = (px(sx) + px(ex)) / 2, (py(sz) + py(ez)) / 2
        label = html.escape(f"{wall['length_m']:.2f} m")
        items.append(f"<text x='{mx:.1f}' y='{mz-8:.1f}' text-anchor='middle' font-size='14' fill='#17324d'>{label}</text>")
    area = plan.get("area_m2")
    subtitle = f"Estimated convex-hull area: {area:.2f} m²" if area is not None else "Estimated area unavailable"
    items.append(f"<text x='40' y='48' font-size='21' font-weight='700' fill='#17324d'>{html.escape(title)}</text>")
    items.append(f"<text x='40' y='76' font-size='14' fill='#526477'>{html.escape(subtitle)} · {html.escape(source_label)}</text>")
    items.append(f"<text x='40' y='590' font-size='12' fill='#526477'>{html.escape(footer_note)}</text>")
    output_path.write_text(_svg_shell(title, 900, 620, "\n".join(items)), encoding="utf-8")


def _svg_shell(title, width, height, content):
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<rect width='100%' height='100%' fill='#ffffff'/><title>{html.escape(title)}</title>{content}</svg>
"""


def _serialize_capture(capture_dir: Path, poses, point_list, stats, matrix, drift, tier, relative_error, ceiling_observed):
    plan = _estimate_plan(point_list, ceiling_observed)
    walls = []
    for wall in plan.get("walls", []):
        wall = dict(wall)
        wall["length"] = _measurement(wall.pop("length_m"), "m", 0.10, relative_error)
        walls.append(wall)
    area = plan.get("area_m2")
    ceiling = plan.get("ceiling_height_m")
    center_x = statistics.fmean(p["x"] for p in poses) if poses else 0.0
    center_z = statistics.fmean(p["z"] for p in poses) if poses else 0.0
    plan_polygon = plan.get("polygon", [])
    output = {
        "schema_version": SCHEMA_VERSION,
        "capture_id": capture_dir.name,
        "capture_path": _portable_path(capture_dir),
        "input_tier": tier,
        "processing_status": plan["status"],
        "units": "m",
        "assumptions": [
            "16-bit grayscale depth is interpreted as millimeters, based on value range and capture layout.",
            "Camera coordinates use x-right, y-up, z-forward-negated and pose quaternions are xyzw camera-to-world rotations.",
            "Depth intrinsics are scaled from camera_matrix.csv using the inferred RGB principal-point dimensions.",
            "The outline is a convex hull of sampled wall-band points; it is not a watertight or orthogonal room model.",
        ],
        "measurements": {
            "floor_area": _measurement(area, "m2", 0.20, relative_error, "convex_hull_proxy_uncalibrated"),
            "ceiling_height": _measurement(ceiling, "m", 0.05, relative_error, "vertical_extent_proxy_uncalibrated" if ceiling is not None else "not_observed"),
            "footprint_axis_aligned_width_x": _measurement(round(max((p[0] for p in plan_polygon), default=0) - min((p[0] for p in plan_polygon), default=0), 3), "m", 0.10, relative_error) if plan_polygon else None,
            "footprint_axis_aligned_length_z": _measurement(round(max((p[1] for p in plan_polygon), default=0) - min((p[1] for p in plan_polygon), default=0), 3), "m", 0.10, relative_error) if plan_polygon else None,
        },
        "rooms": [{
            "room_id": capture_dir.name,
            "geometry_status": plan["status"],
            "polygon_xz_m": plan_polygon,
            "floor_area": _measurement(area, "m2", 0.20, relative_error, "convex_hull_proxy_uncalibrated"),
            "ceiling_height": _measurement(ceiling, "m", 0.05, relative_error, "vertical_extent_proxy_uncalibrated" if ceiling is not None else "not_observed"),
            "walls": walls,
            "openings": [],
            "opening_detection_status": "not_implemented",
            "ceiling_evidence": plan.get("ceiling_evidence", "not_observed"),
        }],
        "stitched_property_plan": {
            "status": "single_capture_only",
            "rooms": [capture_dir.name],
            "adjacencies": [],
            "note": "The supplied data contains independent single-scan folders and no connector room, shared landmarks, or room-level ground truth for multi-room registration.",
        },
        "damage_regions": {"status": "not_assessed", "items": [], "classes": [], "note": "No trained damage model or staged damage labels are provided."},
        "concealed_damage": {"status": "not_assessed", "flags": [], "rules_fired": [], "note": "No moisture, thermal, or material-specific evidence is available in the supplied sensor bundle."},
        "scope_line_items": {"status": "not_assessed", "items": [], "note": "Line items require validated damage regions and surface assignments."},
        "quality_flags": [
            "Room boundary is a convex hull of sampled 3D returns and may include furniture or unobserved space.",
            "Hull edges are candidates, not verified wall surfaces.",
            "Measurement intervals are not calibrated against independent ground truth.",
        ],
        "confidence_intervals": {"calibration_status": "uncalibrated_no_ground_truth", "method": f"Conservative heuristic ±{relative_error:.0%} relative or stated absolute floor; not empirically calibrated."},
        "drift_correction": drift,
        "capture_statistics": stats,
        "camera_matrix_rgb": matrix,
        "trajectory_center_xz_m": [round(center_x, 3), round(center_z, 3)],
        "rendered_plan": "plan.svg",
    }
    return output, plan


def reconstruct(capture_dir: Path, output_dir: Path, frame_stride: int = 30, pixel_stride: int = 6, depth_scale: float = 0.001, tier: str = "lidar", ceiling_observed: bool = False, frame_offset: int = 0):
    started = time.perf_counter()
    if frame_stride < 1 or pixel_stride < 1:
        raise ValueError("frame_stride and pixel_stride must be positive integers")
    if frame_offset < 0 or frame_offset >= frame_stride:
        raise ValueError("frame_offset must be in the range [0, frame_stride)")
    if depth_scale <= 0:
        raise ValueError("depth_scale must be greater than zero")
    capture_dir = capture_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for required in ("odometry.csv", "camera_matrix.csv", "depth"):
        if not (capture_dir / required).exists():
            raise FileNotFoundError(f"Expected {required} under {capture_dir}")

    pose_rows = _read_csv(capture_dir / "odometry.csv")
    poses = [_pose(row) for row in pose_rows]
    corrected_poses, loop = close_trajectory(poses)
    intrinsics = _read_intrinsics(capture_dir / "camera_matrix.csv")
    depth_dir = capture_dir / "depth"
    confidence_dir = capture_dir / "confidence"
    frame_names = sorted(path.stem for path in depth_dir.glob("*.png"))
    if not frame_names:
        raise FileNotFoundError(f"No depth PNGs under {depth_dir}")
    pose_by_frame = {pose["frame"]: index for index, pose in enumerate(poses)}
    points_before, points_after = [], []
    used_frames = []
    missing_pose, missing_confidence = 0, 0
    for sequence_index, frame_name in enumerate(frame_names):
        if sequence_index % frame_stride != frame_offset:
            continue
        pose_index = pose_by_frame.get(frame_name)
        if pose_index is None:
            missing_pose += 1
            continue
        depth_path = depth_dir / f"{frame_name}.png"
        conf_path = confidence_dir / f"{frame_name}.png"
        depth = read_gray_png(depth_path)
        confidence = read_gray_png(conf_path) if conf_path.exists() else None
        if confidence is None:
            missing_confidence += 1
        raw, fixed = _project_frame(depth, confidence, poses[pose_index], intrinsics, corrected_poses[pose_index], pixel_stride, depth_scale)
        points_before.extend(raw)
        points_after.extend(fixed)
        used_frames.append(frame_name)

    duration = poses[-1]["timestamp"] - poses[0]["timestamp"] if len(poses) > 1 else 0.0
    stats = {
        "depth_frames_available": len(frame_names),
        "odometry_rows": len(poses),
        "imu_rows": len(_read_csv(capture_dir / "imu.csv")) if (capture_dir / "imu.csv").exists() else None,
        "processed_depth_frames": len(used_frames),
        "frame_stride": frame_stride,
        "frame_offset": frame_offset,
        "pixel_stride": pixel_stride,
        "missing_pose_for_selected_frame_count": missing_pose,
        "selected_frames_without_confidence_count": missing_confidence,
        "duration_seconds": round(duration, 3),
        "processing_seconds": round(time.perf_counter() - started, 3),
        "rgb_video_available": (capture_dir / "rgb.mp4").exists(),
        "rgb_video_decoded": False,
        "ceiling_capture_operator_confirmed": ceiling_observed,
    }
    drift = {
        "method": "position revisit loop closure with linear translation residual distribution; vertical frame retained from odometry",
        "applied": loop is not None,
        "closure": loop,
        "fallback": "no geometric loop closure found; pose positions remain unchanged",
        "limitations": "Single translational closure only; no rotation graph, wall-plane optimization, or multi-room constraints.",
    }
    relative_error = {"photo": 0.20, "video": 0.10, "lidar": 0.05}.get(tier, 0.20)
    before, before_plan = _serialize_capture(capture_dir, poses, points_before, stats, intrinsics, {**drift, "applied": False, "method": "raw odometry poses; no loop closure"}, tier, relative_error, ceiling_observed)
    after, after_plan = _serialize_capture(capture_dir, corrected_poses, points_after, stats, intrinsics, drift, tier, relative_error, ceiling_observed)

    before_json = output_dir / "before_fix.json"
    after_json = output_dir / "plan.json"
    before_json.write_text(json.dumps(before, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    after_json.write_text(json.dumps(after, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    _render_svg(before_plan, output_dir / "before_fix.svg", capture_dir.name + " (before drift correction)")
    _render_svg(after_plan, output_dir / "plan.svg", capture_dir.name)

    ablation = {
        "capture_id": capture_dir.name,
        "regeneration_command": f"python -m roomscan \"{_portable_path(capture_dir)}\" --output \"{_portable_path(output_dir)}\" --frame-stride {frame_stride} --frame-offset {frame_offset}",
        "before": {"method": "raw odometry poses", "footprint_area_m2": before_plan.get("area_m2"), "polygon_xz_m": before_plan.get("polygon", [])},
        "after": {"method": drift["method"], "footprint_area_m2": after_plan.get("area_m2"), "polygon_xz_m": after_plan.get("polygon", [])},
        "loop_closure": loop,
        "interpretation": "Geometric drift ablation only; no ground truth was supplied, so area accuracy or gate movement cannot be claimed.",
    }
    (output_dir / "drift_ablation.json").write_text(json.dumps(ablation, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return after
