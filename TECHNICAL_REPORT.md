# Indoor Room Reconstruction from Supplied Scan Bundles

## Executive summary

This implementation processes the three supplied scan bundles with a depth-based LiDAR route and two pose-assisted RGB routes. It exports JSON room plans and SVG visualizations and includes a repeatable benchmark over the available data. The benchmark quantifies the behavior of the current reconstructions; it does not establish physical measurement accuracy.

## Inputs and processing routes

| Route | Input and method | Result on supplied bundles |
|---|---|---|
| LiDAR | Project sampled depth returns with camera intrinsics and poses; estimate a convex-hull footprint; apply a conservative translational correction when a trajectory revisit is detected. | Produces an area proxy and plan output for each bundle. Hulls may include furniture or omit unseen boundaries. |
| Photo proxy | Select up to eight frames from `rgb.mp4`; match ORB features with essential-matrix RANSAC; triangulate using the paired metric camera poses and intrinsics. | Zero accepted 3D points on each supplied bundle. No footprint area is reported. |
| Video proxy | Sample RGB frames; match and filter ORB features; triangulate with the paired camera poses and intrinsics. | Two bundles produce sparse point hulls. The ceiling bundle produces three points and no area. |

The RGB routes use synchronized metadata from the same export and do not read the `depth/` or `confidence/` directories. The photo input is a frame-sampled proxy because the supplied folders do not contain independent still photographs. The local output contract is [schemas/case-study-output.schema.json](schemas/case-study-output.schema.json); the published schema referenced by the case-study brief was not included in the workspace.

## Benchmark results

The benchmark used frame stride 30, pixel stride 6, and a cap of 100 video frames. Areas below are in square metres and are geometric proxies.

| Capture | LiDAR area | Photo points | Video points | Video area | Video/LiDAR area difference | LiDAR split area difference |
|---|---:|---:|---:|---:|---:|---:|
| `single_room` | 33.725 | 0 | 362 | 3.146 | 90.67% | 26.44% |
| `single_scan_floor_only` | 92.541 | 0 | 163 | 39.941 | 56.84% | 19.97% |
| `single_scan_with_ceiling` | 176.161 | 0 | 3 | Not available | Not available | 5.64% |

The cross-modal differences compare outputs from the same capture and are diagnostic consistency measures, not errors against independent truth. The LiDAR split values compare interleaved frame subsets from one scan and describe sampling sensitivity, not repeated-capture repeatability. The [benchmark report](outputs/benchmark/benchmark_summary.md) contains the full interpretation and machine-readable data.

## Evaluation scope and calibration

Current 95% intervals use tier-dependent heuristic allowances and are tagged `uncalibrated_assumption`. They are not empirical confidence intervals. No tape or laser reference dimensions are present in the supplied folders, so physical wall-length, footprint-area, and ceiling-height accuracy cannot be scored from this dataset.

The three folders are independent single-scan exports. They do not include a repeated capture of the same room, a connected multi-room walkthrough, an opening inventory, staged-damage labels, a pricing schedule, consumer-app exports, or capture-device/app identification. As a result, repeatability, connected-room adjacency, opening-width performance, damage classification, concealed-damage decisions, scope pricing, and consumer-app comparisons are outside the evidence available here. These fields are represented as unassessed in outputs where applicable.

Principal geometric risks include pose error, incomplete wall coverage, limited RGB feature overlap, depth-to-camera assumptions, and furniture entering convex hulls. The RGB metric scale depends on the supplied camera poses. These risks are reflected in the quality flags and output notes.

## Reproduction

From the repository root, place the same three supplied folders beside `README.md`, then run:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100
```

The benchmark writes JSON, CSV, Markdown, and per-tier plans under `outputs/benchmark/`. The [submission preview gallery](outputs/submission_preview/README.md) contains compact copies of the nine JSON/SVG plans for direct review.
