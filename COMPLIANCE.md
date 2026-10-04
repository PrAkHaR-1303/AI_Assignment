# Case Study Compliance and Evidence Map

Statuses below distinguish implemented code paths from demonstrated acceptance. The benchmark uses only the three supplied folders. No accuracy gate is marked passed without an independent reference.

| Requirement | Implementation/artifact | Status |
|---|---|---|
| Dimensioned LiDAR outline and plan export | `roomscan/pipeline.py`, `outputs/benchmark/runs/*/full/plan.json`, `plan.svg` | Implemented exploratory convex-hull proxy; dimensions uncalibrated. |
| Photo tier from 2-8 stills | `roomscan/vision.py`, CLI `--tier photo` | Experimental adapter samples up to 8 still frames from `rgb.mp4`; pose-assisted with `odometry.csv`; zero accepted points on the supplied photo proxies. Not a strict standalone-photo tier. |
| Video tier | `roomscan/vision.py`, CLI `--tier video` | Experimental RGB/ORB triangulation uses paired odometry poses; two bundles yield sparse hulls, one does not. Not strict video-only metric reconstruction. |
| No depth leakage into RGB routes | `roomscan/vision.py` | Implemented: RGB routes read video, odometry, and intrinsics; they do not read depth/confidence directories. |
| RGB input decoding and synchronization | OpenCV backend, `requirements-vision.txt` | Verified on the three bundles; frame counts match odometry rows and frame IDs are checked. |
| LiDAR drift correction and before/after artifacts | `roomscan/geometry.py`, `outputs/benchmark/runs/*/full/drift_ablation.json` | Implemented single translational loop closure; not scored against physical truth. |
| Data-only benchmark measurements | `roomscan/benchmark.py`, `outputs/benchmark/benchmark_measurements.csv`, `.json`, `.md` | Implemented: hull proxies, RGB/LiDAR differences, and within-capture split stability. These are not physical accuracy or repeatability scores. |
| Photo/video wall-length and footprint accuracy gates | Benchmark summary | Not evaluated; no independent measured dimensions; photo proxies have no accepted points. |
| Opening detection and width <= 2 cm gate | `roomscan/vision.py`, `roomscan/pipeline.py` | Detector absent; not evaluated. |
| Ceiling-height error and repeat spread | LiDAR output and benchmark | Not evaluated; observed point-cloud extent is not physical ceiling ground truth and there is no repeat scan. |
| Three connected rooms and correct whole-property adjacency | `stitched_property_plan` output | Not met; the folders are independent single-scan captures without a connector sequence. |
| Two staged damage classes, concealed-damage rules, and scope | Output placeholders marked `not_assessed` | Not implemented/evaluated; no labels, validated rules, or pricing schedule. |
| Consumer-app head-to-head on two rooms | No same-room app exports | Not evaluated; app name/version and exports are absent. |
| Named installable capture app and device matrix | `CAPTURE_PROTOCOL.md` | Not verified; local exports do not identify their phone app/version or device. |
| Published schema validation | `schemas/case-study-output.schema.json` | Unverified; the published schema referenced in the brief was not included. |
| Fresh clone reproduces the exact benchmark | `README.md`, `DATA_BUNDLE.md` | Code and report are reproducible after copying the supplied folders and installing the optional RGB dependency. Raw bundles are ignored by Git. |
| Technical report and fix-loop record | `TECHNICAL_REPORT.md`, `FIX_LOOP.md` | Present; physical accuracy improvement is not claimed. |

## Measurement boundary

The RGB/LiDAR comparison uses estimates from the same capture as an internal consistency check. The LiDAR estimate is not independent truth. Interleaved LiDAR frame splits are from one trajectory and do not meet a repeated-capture requirement. See `outputs/benchmark/benchmark_summary.md` for exact values and caveats.
