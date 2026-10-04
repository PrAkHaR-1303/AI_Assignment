# Technical Report: LiDAR Baseline (Partial Submission)

## System and tier design

The implementation is a local Python package with a one-command LiDAR path. It decodes the supplied 16-bit grayscale depth and 8-bit confidence PNGs, joins frames by their six-digit frame IDs to odometry rows, scales camera intrinsics to the depth image size, projects valid samples into the world frame, and estimates a 2D convex-hull footprint. The output contains wall segments, floor-area and ceiling-height fields, confidence intervals, sensor statistics, and an SVG plan. It is deterministic and has no network or pretrained model dependency.

| Input tier | Brief's target hardware | Implementation status | Accuracy evidence |
|---|---|---|---|
| Photos, 2-8 stills per room | iPhone 15 or newer | Not implemented; photo-only input is rejected | None; no photo benchmark |
| Handheld video | iPhone 15 or newer | Not implemented; bundled RGB video is not decoded | None; no video benchmark |
| LiDAR depth, poses, and intrinsics | Pro-class iPhone | Reader runs on supplied export layout; capture-device model is unknown | Uncalibrated; no accuracy gate claimed |

This is a status matrix, not a validated compatibility matrix. The brief requires iPhone 15+ photo/video runs and Pro-class LiDAR; this workspace contains only three LiDAR exports without hardware identifiers.

## Geometry and drift

Depth points are projected using the camera-to-world quaternion and translation for the corresponding frame. The plan outline is the convex hull of points in a wall-height band. This is intentionally simple: it can include furniture, omit unseen wall sections, and does not force right angles. A revisit detector searches for trajectory positions within 0.45 m separated by at least 240 frames. If it finds a match, the translation residual is distributed linearly over the path and carried into the trajectory tail. `before_fix.json` and `before_fix.svg` preserve raw-odometry results; `plan.json` and `plan.svg` use the corrected poses. `drift_ablation.json` reports both footprints.

This is the shipped drift fix hypothesis: an uncorrected translation residual can warp a room outline when a scan revisits the same place. The fix constrains one geometric revisit. It does not optimize rotation, wall planes, or multiple rooms. The ablation cannot establish improved accuracy because no laser/tape footprint is present.

## Error budget and calibration

The pipeline reports a 95% interval using a tier-relative allowance with an absolute floor. Every interval is tagged `uncalibrated_assumption`; it must not be interpreted as an empirical confidence interval. The most serious current measurement risks are pose-frame convention, drift between revisits, camera-intrinsics scaling, incomplete wall coverage, and furniture points entering the convex hull. Ceiling height is unreported unless an operator explicitly confirms that the ceiling was visible; the numeric result is then the observed vertical point-cloud span, not a validated laser measurement.

The supplied scans have 1,715, 5,251, and 9,745 matching depth/odometry frames, with 16-bit 256 x 192 depth maps. Their IMU streams and RGB videos are present. There is no annotated room outline, opening inventory, ceiling measurement, damage label, repeated same-tier capture, multi-room connector, consumer-app export, or measured benchmark.

## Damage, scope, and stitching

Damage classes, concealed-damage rules, surface assignments, and scope line items are present as explicit output fields with `not_assessed` states. No model or evidence exists in the workspace to support those claims. The three folders are separate scans; there is no shared landmark or connector capture for room alignment, so the stitched-property output records a single room and no adjacency.

## Fix loop and gates

The before/after files regenerate from the CLI. The current fix is the revisit translation correction described above. The data can show its geometric footprint effect, but cannot score an opening miss rate, ceiling-height error, repeatability spread, photo/video calibration, multi-room drift, or consumer-app comparison. Those gates remain unevaluated rather than inferred from appearance.

## Failure modes and next evidence

The baseline may produce a plausible outline with incorrect metric dimensions if the quaternion convention, depth unit, or intrinsics scale differs from the assumed export convention. Convex hulls overestimate non-convex rooms and can be pulled outward by furniture. Missing walls are not inferred. Reflections, glass, wet-look surfaces, and low light have not been measured. The next required bundle is a multi-room walk with at least three rooms and a connector, a furnished room with two staged damage classes, a repeated scan, laser/tape dimensions and openings, and a same-room consumer-app export. Photo and video captures plus the named iOS capture route are also required before the walk-in test can be claimed.
