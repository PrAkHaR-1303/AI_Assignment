# Applied AI Case Study: Three-Tier Reconstruction Prototype

## System and input discipline

The package processes only the three supplied folders. The LiDAR route reads depth, confidence, intrinsics, and camera poses. The RGB routes read `rgb.mp4` plus synchronized `odometry.csv` and camera intrinsics; they do not read depth or confidence images. The photo route samples up to eight still frames from each bundled video because no standalone photo inputs were supplied. The RGB routes use metric camera-pose metadata, so they are pose-assisted RGB prototypes rather than strict image-only systems.

The local output contract is `schemas/case-study-output.schema.json`. The published schema named by the case-study brief was not included in the workspace. Every output includes assumptions and quality flags; measurements and intervals are explicitly marked uncalibrated.

## Tier implementations

| Tier | Processing | Result status |
|---|---|---|
| LiDAR | Project sampled depth points through the paired camera poses; estimate a convex-hull footprint and candidate edges. Apply one conservative translation correction when a trajectory revisit is detected. | Runs on all three supplied bundles. Hulls can include furniture or miss unseen boundaries. |
| Photo proxy | Select 2-8 RGB frames from the supplied video, detect ORB features, match pairs, reject outliers with an essential-matrix RANSAC step, and triangulate using synchronized metric poses. | The supplied proxies produce zero accepted 3D points; no photo area is reported. |
| Video proxy | Sample RGB frames, detect/match ORB features, reject outliers, and triangulate against synchronized metric poses. | Two bundles produce sparse hulls; the ceiling bundle produces only three points and no area. Results disagree strongly with the LiDAR hulls. |

The OpenCV dependency is isolated in `requirements-vision.txt`; the original LiDAR route remains standard-library-only. The video clips are HEVC and OpenCV's FFmpeg backend decodes them locally. RGB frame counts match the associated odometry rows, and the implementation checks frame IDs before using a pose.

## Data-derived benchmark

The benchmark reruns LiDAR with a fixed frame and pixel stride, runs both RGB proxies, and computes a pair of disjoint interleaved LiDAR frame subsets per capture. The RGB/LiDAR comparison is an internal modality comparison. The split comparison measures sampling sensitivity within one capture.

| Capture | LiDAR area proxy (m²) | Photo points | Video area proxy (m²) | Video/LiDAR area difference | LiDAR split area difference |
|---|---:|---:|---:|---:|---:|
| `single_room` | 33.725 | 0 | 3.146 | 90.67% | 26.44% |
| `single_scan_floor_only` | 92.541 | 0 | 39.941 | 56.84% | 19.97% |
| `single_scan_with_ceiling` | 176.161 | 0 | Not available (3 points) | Not available | 5.64% |

These are geometric proxies, not measured room dimensions. The area disagreements show that the current sparse RGB reconstruction is not reliable enough to stand in for the LiDAR result. The split differences are not repeat-scan results. Full per-tier outputs and machine-readable measurements are under `outputs/benchmark/`.

## Error budget and calibration

The dominant risks are camera-pose error, image/pose synchronization, limited RGB overlap, sparse feature triangulation, depth-to-camera assumptions in the LiDAR route, incomplete wall coverage, and furniture entering convex hulls. The RGB output's metric scale depends on bundled camera poses. The photo proxy is also derived from video frames rather than a separate still capture.

Current 95% intervals use tier-dependent heuristic allowances and are tagged `uncalibrated_assumption`. They are not empirical confidence intervals. No laser/tape ground truth is present, so wall-length error, floor-area error, ceiling error, and the brief's numeric accuracy gates cannot be evaluated.

## Open case-study requirements

The folders contain independent single-scan bundles. They do not include a connected three-room walk, separate still-photo capture, repeat scan of the same room, staged-damage labels, opening inventory, measured physical dimensions, named consumer-app exports, or capture-device/app metadata. Consequently this implementation does not establish opening width, ceiling accuracy, repeatability, whole-property adjacency, damage/concealed-damage detection, scope pricing, or consumer-app comparison. These outputs remain explicitly `not_assessed`.

The existing drift ablation compares raw and corrected pose geometry, but it has no physical reference. The benchmark exposes an additional sampling-stability problem: area changes across the two disjoint subsets by 5.64%-26.44%. No accuracy improvement is claimed from that internal measure.

## Reproduction

From the workspace root, install OpenCV for the RGB routes and run:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100
```

The supplied raw folders are intentionally ignored by Git. Reproduction from a clone requires those same folders to be copied beside the repository; no other dataset is used.
