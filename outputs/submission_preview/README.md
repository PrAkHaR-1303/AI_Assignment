# Submission Preview Gallery

Compact plan outputs generated from the three supplied scan folders. These are included so a reviewer can inspect the artifacts without downloading the raw sensor bundles. They are geometric reconstruction proxies, not physically validated room plans. The photo route produces zero accepted 3D points in all three scans; the sparse video route is incomplete and differs substantially from LiDAR. See the [benchmark measurements](../benchmark/benchmark_summary.md) and [submission status](../../SUBMISSION_STATUS.md) for the full caveats.

| Supplied bundle | LiDAR | Photo proxy | Video proxy |
|---|---|---|---|
| `single_room` | [SVG](single_room/lidar/plan.svg) · [JSON](single_room/lidar/plan.json) | [SVG](single_room/photo/plan.svg) · [JSON](single_room/photo/plan.json) | [SVG](single_room/video/plan.svg) · [JSON](single_room/video/plan.json) |
| `single_scan_floor_only` | [SVG](single_scan_floor_only/lidar/plan.svg) · [JSON](single_scan_floor_only/lidar/plan.json) | [SVG](single_scan_floor_only/photo/plan.svg) · [JSON](single_scan_floor_only/photo/plan.json) | [SVG](single_scan_floor_only/video/plan.svg) · [JSON](single_scan_floor_only/video/plan.json) |
| `single_scan_with_ceiling` | [SVG](single_scan_with_ceiling/lidar/plan.svg) · [JSON](single_scan_with_ceiling/lidar/plan.json) | [SVG](single_scan_with_ceiling/photo/plan.svg) · [JSON](single_scan_with_ceiling/photo/plan.json) | [SVG](single_scan_with_ceiling/video/plan.svg) · [JSON](single_scan_with_ceiling/video/plan.json) |

The `full` benchmark route is named `lidar` here for clarity. All three outputs come from the same benchmark settings documented in the measurement report. These checked-in previews are evidence artifacts; regenerate them by running the benchmark command in the repository README and copying the resulting `plan.json` and `plan.svg` files into the matching folders above.
