"""Sparse RGB reconstruction from the videos bundled with each scan.

The supplied capture exports synchronize RGB frame IDs with metric camera poses
in odometry.csv. This module uses RGB features for scene points and uses those
bundled poses/intrinsics for metric triangulation. It deliberately does not
read depth/ or confidence/. Because the pose/scale comes from the sensor export,
these are pose-assisted RGB tiers, not strict image-only reconstruction.
"""

from __future__ import annotations

import json
import math
import statistics
import time
from pathlib import Path

from .geometry import rotate_by_quaternion
from .pipeline import (
    SCHEMA_VERSION,
    _measurement,
    _portable_path,
    _read_csv,
    _read_intrinsics,
    _render_svg,
    _estimate_plan,
    _pose,
)


def _vision_modules():
    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise RuntimeError(
            "RGB photo/video tiers require OpenCV and NumPy. Install them with: "
            "python -m pip install -r requirements-vision.txt"
        ) from error
    return cv2, np


def _normalize(vector, np):
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-9:
        return None
    return vector / norm


def _camera_ray(pixel, pose, scale_x: float, scale_y: float, np):
    u, v = pixel
    fx, fy = pose["fx"] * scale_x, pose["fy"] * scale_y
    cx, cy = pose["cx"] * scale_x, pose["cy"] * scale_y
    camera_direction = ((u - cx) / fx, -(v - cy) / fy, -1.0)
    world_direction = rotate_by_quaternion(camera_direction, (pose["qx"], pose["qy"], pose["qz"], pose["qw"]))
    return _normalize(np.asarray(world_direction, dtype=np.float64), np)


def _project_world(point, pose, scale_x: float, scale_y: float, np):
    delta = (float(point[0]) - pose["x"], float(point[1]) - pose["y"], float(point[2]) - pose["z"])
    local = rotate_by_quaternion(delta, (-pose["qx"], -pose["qy"], -pose["qz"], pose["qw"]))
    depth = -local[2]
    if depth <= 0.05:
        return None
    return (pose["fx"] * scale_x * local[0] / depth + pose["cx"] * scale_x,
            pose["fy"] * scale_y * -local[1] / depth + pose["cy"] * scale_y)


def _triangulate_pair(pixel_a, pixel_b, pose_a, pose_b, scale_x: float, scale_y: float, np):
    origin_a = np.asarray((pose_a["x"], pose_a["y"], pose_a["z"]), dtype=np.float64)
    origin_b = np.asarray((pose_b["x"], pose_b["y"], pose_b["z"]), dtype=np.float64)
    direction_a = _camera_ray(pixel_a, pose_a, scale_x, scale_y, np)
    direction_b = _camera_ray(pixel_b, pose_b, scale_x, scale_y, np)
    if direction_a is None or direction_b is None:
        return None

    # Closest points between the two camera rays; reject nearly parallel views.
    delta = origin_a - origin_b
    dot = float(np.dot(direction_a, direction_b))
    denominator = 1.0 - dot * dot
    if denominator < 0.0004:
        return None
    d = float(np.dot(direction_a, delta))
    e = float(np.dot(direction_b, delta))
    distance_a = (dot * e - d) / denominator
    distance_b = (e - dot * d) / denominator
    if distance_a <= 0.05 or distance_b <= 0.05 or max(distance_a, distance_b) > 20.0:
        return None
    point_a = origin_a + distance_a * direction_a
    point_b = origin_b + distance_b * direction_b
    ray_gap = float(np.linalg.norm(point_a - point_b))
    point = (point_a + point_b) / 2.0
    if ray_gap > max(0.08, 0.04 * ((distance_a + distance_b) / 2.0)):
        return None

    projected_a = _project_world(point, pose_a, scale_x, scale_y, np)
    projected_b = _project_world(point, pose_b, scale_x, scale_y, np)
    if projected_a is None or projected_b is None:
        return None
    reprojection_a = math.dist(projected_a, pixel_a)
    reprojection_b = math.dist(projected_b, pixel_b)
    if max(reprojection_a, reprojection_b) > 8.0:
        return None
    return point, (reprojection_a + reprojection_b) / 2.0


def _select_frame_indices(frame_count: int, tier: str, fps: float, photo_count: int, max_video_frames: int):
    if frame_count < 2:
        raise ValueError("The bundled RGB video must contain at least two frames")
    last_usable = max(0, frame_count - 3)
    if tier == "photo":
        count = min(8, max(2, photo_count), max(2, last_usable + 1))
        if count == 1:
            return [0]
        return sorted({round(index * last_usable / (count - 1)) for index in range(count)})
    target_step = max(1, round(max(1.0, fps) * 0.45))
    cap_step = max(1, math.ceil((frame_count - 1) / max(1, max_video_frames - 1)))
    step = max(target_step, cap_step)
    values = list(range(0, max(1, last_usable + 1), step))
    if values[-1] != last_usable:
        values.append(last_usable)
    return values


def _read_selected_frames(video_path: Path, frame_indices: list[int], cv2, np, max_width: int):
    capture = cv2.VideoCapture(str(video_path), cv2.CAP_FFMPEG)
    if not capture.isOpened():
        raise ValueError(f"OpenCV/FFmpeg could not open the bundled video: {video_path}")
    reported_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    try:
        decode_backend = capture.getBackendName()
    except cv2.error:
        decode_backend = "unknown"
    orb = cv2.ORB_create(nfeatures=3200, scaleFactor=1.2, nlevels=8, edgeThreshold=19, fastThreshold=12)
    selected = {}
    scale_x = scale_y = 1.0
    def read_exact_frame(target):
        # Seeking exactly to a final HEVC frame can fail on some decoders. Retry
        # from a few earlier points, checking the reported decoded frame ID so
        # a picture is never paired with the wrong odometry row.
        anchors = (target, max(0, target - 1), max(0, target - 5), max(0, target - 15))
        for anchor in dict.fromkeys(anchors):
            capture.set(cv2.CAP_PROP_POS_FRAMES, anchor)
            for _ in range(min(20, target - anchor + 2)):
                ok, candidate = capture.read()
                actual = round(capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                if ok and candidate is not None and actual == target:
                    return candidate
                if actual >= target:
                    break
        return None

    for frame_index in frame_indices:
        frame = read_exact_frame(frame_index)
        if frame is None:
            continue
        height, width = frame.shape[:2]
        factor = min(1.0, max_width / max(1, width))
        if factor < 1.0:
            frame = cv2.resize(frame, (round(width * factor), round(height * factor)), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        selected[frame_index] = {
            "keypoints": keypoints or [],
            "descriptors": descriptors,
            "width": gray.shape[1],
            "height": gray.shape[0],
            "gray": gray,
        }
    capture.release()
    scale_x = (selected[next(iter(selected))]["width"] / source_width) if selected else 1.0
    scale_y = (selected[next(iter(selected))]["height"] / source_height) if selected else 1.0
    return selected, {"video_frame_count_reported": reported_count, "video_fps_reported": fps,
                      "video_width_px": source_width, "video_height_px": source_height,
                      "decoded_selected_frame_count": len(selected), "decode_backend": decode_backend,
                      "opencv_version": cv2.__version__, "orb_scale_x": scale_x, "orb_scale_y": scale_y}


def _build_visual_cloud(selected, frame_indices, pose_by_frame, scale_x, scale_y, cv2, np, tier="video"):
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    points = []
    reprojection_errors = []
    pair_stats = []
    if tier == "photo":
        pair_indices = [(a, b) for a in range(len(frame_indices)) for b in range(a + 1, len(frame_indices))]
    else:
        pair_indices = [(index, index + 1) for index in range(len(frame_indices) - 1)]
    for index_a, index_b in pair_indices:
        frame_a, frame_b = frame_indices[index_a], frame_indices[index_b]
        image_a, image_b = selected.get(frame_a), selected.get(frame_b)
        pose_a, pose_b = pose_by_frame.get(f"{frame_a:06d}"), pose_by_frame.get(f"{frame_b:06d}")
        if not image_a or not image_b or pose_a is None or pose_b is None:
            continue
        descriptors_a, descriptors_b = image_a["descriptors"], image_b["descriptors"]
        if descriptors_a is None or descriptors_b is None or len(descriptors_a) < 8 or len(descriptors_b) < 8:
            pair_stats.append({"frame_a": frame_a, "frame_b": frame_b, "matches": 0, "visual_inliers": 0, "triangulated_points": 0})
            continue
        matches = matcher.knnMatch(descriptors_a, descriptors_b, k=2)
        good = [first for pair in matches if len(pair) == 2 for first, second in [pair] if first.distance < 0.72 * second.distance]
        if len(good) < 8:
            pair_stats.append({"frame_a": frame_a, "frame_b": frame_b, "matches": len(good), "visual_inliers": 0, "triangulated_points": 0})
            continue
        pixels_a = np.float32([image_a["keypoints"][match.queryIdx].pt for match in good])
        pixels_b = np.float32([image_b["keypoints"][match.trainIdx].pt for match in good])
        fx = (pose_a["fx"] + pose_b["fx"]) * scale_x / 2.0
        fy = (pose_a["fy"] + pose_b["fy"]) * scale_y / 2.0
        cx = (pose_a["cx"] + pose_b["cx"]) * scale_x / 2.0
        cy = (pose_a["cy"] + pose_b["cy"]) * scale_y / 2.0
        camera_matrix = np.asarray(((fx, 0.0, cx), (0.0, fy, cy), (0.0, 0.0, 1.0)), dtype=np.float64)
        try:
            essential, mask = cv2.findEssentialMat(pixels_a, pixels_b, camera_matrix, method=cv2.RANSAC, prob=0.999, threshold=1.5)
        except cv2.error:
            essential, mask = None, None
        if essential is None or mask is None:
            pair_stats.append({"frame_a": frame_a, "frame_b": frame_b, "matches": len(good), "visual_inliers": 0, "triangulated_points": 0})
            continue
        mask = mask.reshape(-1).astype(bool)
        inlier_a, inlier_b = pixels_a[mask], pixels_b[mask]
        pair_points = 0
        for pixel_a, pixel_b in zip(inlier_a, inlier_b):
            result = _triangulate_pair(pixel_a, pixel_b, pose_a, pose_b, scale_x, scale_y, np)
            if result is None:
                continue
            point, error = result
            points.append((float(point[0]), float(point[1]), float(point[2])))
            reprojection_errors.append(error)
            pair_points += 1
        pair_stats.append({"frame_a": frame_a, "frame_b": frame_b, "matches": len(good), "visual_inliers": int(mask.sum()), "triangulated_points": pair_points})

    # Deduplicate repeated observations of the same scene feature before hull building.
    unique = {}
    for point in points:
        key = tuple(round(component / 0.04) for component in point)
        unique.setdefault(key, point)
    return list(unique.values()), reprojection_errors, pair_stats


def _visual_output(capture_dir, output_dir, tier, poses, matrix, selected, frame_indices, video_metadata, points, reprojection_errors, pair_stats, started, photo_count):
    from .pipeline import _interval

    plan = _estimate_plan(points, ceiling_observed=False)
    walls = []
    tier_error = {"photo": 0.20, "video": 0.10}[tier]
    for wall in plan.get("walls", []):
        item = dict(wall)
        item["length"] = _measurement(item.pop("length_m"), "m", 0.10, tier_error, "visual_sparse_proxy_uncalibrated")
        walls.append(item)
    polygon = plan.get("polygon", [])
    area = plan.get("area_m2")
    width = round(max((point[0] for point in polygon), default=0) - min((point[0] for point in polygon), default=0), 3) if polygon else None
    length = round(max((point[1] for point in polygon), default=0) - min((point[1] for point in polygon), default=0), 3) if polygon else None
    # A point-cloud vertical span is not evidence of a detected ceiling surface.
    height = None
    center_x = statistics.fmean(pose["x"] for pose in poses) if poses else 0.0
    center_z = statistics.fmean(pose["z"] for pose in poses) if poses else 0.0
    pair_inliers = sum(row["visual_inliers"] for row in pair_stats)
    match_count = sum(row["matches"] for row in pair_stats)
    triangulated_count = len(points)
    plan_file = output_dir / "plan.svg"
    _render_svg(
        plan,
        plan_file,
        f"{capture_dir.name} ({tier} RGB pose-assisted)",
        source_label="sparse RGB triangulation with bundled metric poses",
        footer_note="Sparse visual-feature hull; pose-assisted, uncalibrated, openings and damage not assessed.",
    )
    duration = round(time.perf_counter() - started, 3)
    status = plan.get("status", "visual_reconstruction_unavailable")
    assumptions = [
        "RGB observations come from the bundled rgb.mp4; no depth or confidence PNG is read by this tier.",
        "Camera poses, metric scale, and per-frame camera intrinsics are read from the synchronized odometry.csv bundled with the RGB capture.",
        "The photo tier selects up to eight still frames from the bundled video because no standalone photo capture is included in the supplied folders.",
        "Sparse ORB matches are triangulated using known bundled poses; the outline is a convex hull of observed 3D feature points, not a validated wall reconstruction.",
    ]
    if triangulated_count < 40:
        assumptions.append("Fewer than 40 unique triangulated features were available; room measurements are unavailable or unreliable.")
    output = {
        "schema_version": SCHEMA_VERSION,
        "capture_id": capture_dir.name,
        "capture_path": _portable_path(capture_dir),
        "input_tier": tier,
        "processing_status": f"{status}_pose_assisted_rgb",
        "units": "m",
        "assumptions": assumptions,
        "measurements": {
            "floor_area": _measurement(area, "m2", 0.20, tier_error, "visual_sparse_proxy_uncalibrated" if area is not None else "not_estimated"),
            "ceiling_height": _measurement(height, "m", 0.05, tier_error, "visual_vertical_extent_proxy_uncalibrated" if height is not None else "not_observed"),
            "footprint_axis_aligned_width_x": _measurement(width, "m", 0.10, tier_error, "visual_sparse_proxy_uncalibrated") if width is not None else None,
            "footprint_axis_aligned_length_z": _measurement(length, "m", 0.10, tier_error, "visual_sparse_proxy_uncalibrated") if length is not None else None,
        },
        "rooms": [{
            "room_id": capture_dir.name,
            "geometry_status": f"{status}_pose_assisted_rgb",
            "polygon_xz_m": polygon,
            "floor_area": _measurement(area, "m2", 0.20, tier_error, "visual_sparse_proxy_uncalibrated" if area is not None else "not_estimated"),
            "ceiling_height": _measurement(height, "m", 0.05, tier_error, "visual_vertical_extent_proxy_uncalibrated" if height is not None else "not_observed"),
            "walls": walls,
            "openings": [],
            "opening_detection_status": "not_implemented",
            "ceiling_evidence": "visual_point_cloud_vertical_extent_not_validated" if height is not None else "not_observed",
        }],
        "stitched_property_plan": {"status": "single_capture_only", "rooms": [capture_dir.name], "adjacencies": [], "note": "The supplied folders contain independent single-scan captures, not a connected multi-room route."},
        "damage_regions": {"status": "not_assessed", "items": [], "classes": [], "note": "RGB feature tracking is not a damage classifier; the supplied folders have no damage labels."},
        "concealed_damage": {"status": "not_assessed", "flags": [], "rules_fired": [], "note": "No concealed-damage labels or validated sensor rules are present in the supplied folders."},
        "scope_line_items": {"status": "not_assessed", "items": [], "note": "No validated damage regions or price schedule are present."},
        "confidence_intervals": {"calibration_status": "uncalibrated_no_independent_ground_truth", "method": f"Heuristic ±{tier_error:.0%} relative allowance or stated absolute floor; not empirically calibrated."},
        "drift_correction": {"method": "Use paired odometry.csv metric camera poses directly; no visual loop-closure optimization", "applied": False, "limitations": "This RGB result is pose-assisted, not an image-only tier, and uses no independent ground truth."},
        "capture_statistics": {
            **video_metadata,
            "rgb_decoded_frame_count": len(selected),
            "rgb_candidate_frames": len(frame_indices),
            "rgb_selected_frame_ids": frame_indices,
            "photo_still_count": len(selected) if tier == "photo" else None,
            "photo_still_limit": photo_count if tier == "photo" else None,
            "orb_keypoint_counts": {str(index): len(frame.get("keypoints", [])) for index, frame in selected.items()},
            "visual_pair_count": len(pair_stats),
            "visual_match_count": match_count,
            "essential_matrix_inlier_count": pair_inliers,
            "triangulated_unique_point_count": triangulated_count,
            "median_reprojection_error_px": round(statistics.median(reprojection_errors), 3) if reprojection_errors else None,
            "processing_seconds": duration,
            "odometry_pose_count": len(poses),
            "odometry_video_frame_count_match": video_metadata.get("video_frame_count_reported") == len(poses),
        },
        "camera_matrix_rgb": matrix,
        "trajectory_center_xz_m": [round(center_x, 3), round(center_z, 3)],
        "rendered_plan": "plan.svg",
        "quality_flags": [
            "Metric scale and camera poses come from the paired odometry export, so this is not a strict photo-only/video-only reconstruction.",
            "Wall edges are sparse-feature convex-hull candidates and may include furniture or omit unobserved areas.",
            "All measurement intervals are uncalibrated; no independent laser/tape references are present.",
        ],
        "visual_pairs": pair_stats,
    }
    if triangulated_count < 40:
        output["quality_flags"].append("Fewer than 40 unique triangulated RGB features were reconstructed; geometric output is insufficient for dimensional use.")
    (output_dir / "plan.json").write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return output


def reconstruct_rgb(capture_dir: Path, output_dir: Path, tier: str, photo_count: int = 8, max_video_frames: int = 350, max_width: int = 960):
    if tier not in {"photo", "video"}:
        raise ValueError("RGB tier must be 'photo' or 'video'")
    if photo_count < 2 or photo_count > 8:
        raise ValueError("photo_count must be between 2 and 8")
    if max_video_frames < 2:
        raise ValueError("max_video_frames must be at least 2")
    started = time.perf_counter()
    cv2, np = _vision_modules()
    capture_dir = capture_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = capture_dir / "rgb.mp4"
    if not video_path.is_file():
        raise FileNotFoundError(f"Expected bundled RGB video: {video_path}")
    pose_rows = _read_csv(capture_dir / "odometry.csv")
    poses = [_pose(row) for row in pose_rows]
    pose_by_frame = {pose["frame"]: pose for pose in poses}
    matrix = _read_intrinsics(capture_dir / "camera_matrix.csv")

    probe = cv2.VideoCapture(str(video_path), cv2.CAP_FFMPEG)
    if not probe.isOpened():
        raise ValueError(f"OpenCV/FFmpeg could not open the bundled video: {video_path}")
    frame_count = int(probe.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(probe.get(cv2.CAP_PROP_FPS))
    probe.release()
    if frame_count != len(poses):
        raise ValueError(f"RGB video has {frame_count} frames but odometry.csv has {len(poses)} rows; frame sync cannot be assumed")

    frame_indices = _select_frame_indices(frame_count, tier, fps, photo_count, max_video_frames)
    selected, video_metadata = _read_selected_frames(video_path, frame_indices, cv2, np, max_width)
    if len(selected) < 2:
        raise ValueError("Fewer than two RGB frames could be decoded")
    scale_x, scale_y = video_metadata["orb_scale_x"], video_metadata["orb_scale_y"]
    points, reprojection_errors, pair_stats = _build_visual_cloud(selected, frame_indices, pose_by_frame, scale_x, scale_y, cv2, np, tier)
    return _visual_output(capture_dir, output_dir, tier, poses, matrix, selected, frame_indices, video_metadata, points, reprojection_errors, pair_stats, started, photo_count)
