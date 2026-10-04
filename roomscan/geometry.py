"""Geometry helpers for point projection, drift correction, and plan outlines."""

from __future__ import annotations

import math
from array import array
from collections import defaultdict
from typing import Iterable, Sequence


def rotate_by_quaternion(point: tuple[float, float, float], q: tuple[float, float, float, float]):
    x, y, z, w = q
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm == 0:
        return point
    x, y, z, w = x / norm, y / norm, z / norm, w / norm
    vx, vy, vz = point
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


def close_trajectory(poses: Sequence[dict], radius: float = 0.45, min_gap: int = 240):
    """Apply one conservative translational loop closure when the path revisits itself.

    A revisit is a pair of tracked positions within ``radius`` meters and at least
    ``min_gap`` frames apart. The accumulated translation residual is distributed
    linearly over that path segment and carried into the trajectory tail.
    """
    if len(poses) < min_gap + 2:
        return [dict(p) for p in poses], None
    cell_size = radius
    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    best = None
    for j, pose in enumerate(poses):
        x, z = pose["x"], pose["z"]
        cx, cz = math.floor(x / cell_size), math.floor(z / cell_size)
        for bx in range(cx - 1, cx + 2):
            for bz in range(cz - 1, cz + 2):
                for i in buckets.get((bx, bz), ()):
                    if j - i < min_gap:
                        continue
                    dx, dz = x - poses[i]["x"], z - poses[i]["z"]
                    distance = math.hypot(dx, dz)
                    if distance <= radius and (best is None or distance < best[0]):
                        best = (distance, i, j, dx, dz)
        buckets[(cx, cz)].append(j)

    corrected = [dict(p) for p in poses]
    if best is None:
        return corrected, None

    distance, start, end, residual_x, residual_z = best
    span = max(1, end - start)
    for index in range(start + 1, len(corrected)):
        fraction = min(1.0, (index - start) / span)
        corrected[index]["x"] -= fraction * residual_x
        corrected[index]["z"] -= fraction * residual_z
    return corrected, {
        "start_frame_index": start,
        "end_frame_index": end,
        "pre_correction_residual_m": distance,
        "translation_residual_x_m": residual_x,
        "translation_residual_z_m": residual_z,
    }


def convex_hull(points: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 2:
        return unique

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def simplify_closed_polygon(polygon: Sequence[tuple[float, float]], tolerance: float = 0.12):
    if len(polygon) <= 4:
        return list(polygon)
    # Keep hull vertices with a meaningful direction change; drop near-collinear samples.
    result = []
    for i, current in enumerate(polygon):
        previous = polygon[i - 1]
        following = polygon[(i + 1) % len(polygon)]
        ax, ay = current[0] - previous[0], current[1] - previous[1]
        bx, by = following[0] - current[0], following[1] - current[1]
        cross = abs(ax * by - ay * bx)
        scale = max(math.hypot(ax, ay) + math.hypot(bx, by), 1e-6)
        if cross / scale >= tolerance:
            result.append(current)
    return result if len(result) >= 3 else list(polygon)


def polygon_area(polygon: Sequence[tuple[float, float]]) -> float:
    if len(polygon) < 3:
        return 0.0
    return abs(
        sum(
            polygon[i][0] * polygon[(i + 1) % len(polygon)][1]
            - polygon[(i + 1) % len(polygon)][0] * polygon[i][1]
            for i in range(len(polygon))
        )
    ) / 2.0


def quantile(values: array, fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return float(ordered[index])
