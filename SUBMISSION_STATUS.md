# Submission Status

**Status: reproducible three-route prototype; case-study acceptance gates are not all met.** The implementation uses only the three supplied folders. The RGB routes use `rgb.mp4` plus synchronized pose/intrinsics metadata from those folders; they do not use the depth or confidence maps. The benchmark records measured outputs and explicit failures without treating LiDAR as physical ground truth.

## Verified with the supplied folders

The benchmark command completed for all three bundles using Python and the optional OpenCV dependency. It generated LiDAR, photo-proxy, and video-proxy results under `outputs/benchmark/runs/` and summary tables under `outputs/benchmark/`.

Compact JSON/SVG copies of all nine tier outputs are included in the [submission preview gallery](outputs/submission_preview/README.md) for direct review from the repository.

| Bundle | LiDAR hull area proxy (m²) | Photo frames / accepted points | Video hull area proxy (m²) | Video vs LiDAR area difference | LiDAR split area difference |
|---|---:|---:|---:|---:|---:|
| `single_room` | 33.725 | 8 / 0 | 3.146 | 90.67% | 26.44% |
| `single_scan_floor_only` | 92.541 | 8 / 0 | 39.941 | 56.84% | 19.97% |
| `single_scan_with_ceiling` | 176.161 | 7 / 0 | Not available (3 points) | Not available | 5.64% |

All areas are reconstruction proxies. Photo/video differences are comparisons to LiDAR output from the same capture, not errors against independent physical measurements. The interleaved split values measure sensitivity to frame sampling within a scan, not repeated-scan repeatability.

## Requirement status

| Requirement | Status | Evidence or limitation |
|---|---|---|
| LiDAR input route | Implemented | Depth/confidence projection, camera poses, JSON/SVG output, and drift ablation run on all three folders. |
| Video input route | Implemented as an experimental pose-assisted RGB path | ORB feature matching and triangulation from RGB frames; metric camera poses/intrinsics are read from the paired export. Two bundles produce sparse hulls; the ceiling bundle yields only 3 points. |
| Photo input route, 2-8 stills | Implemented as an eight-frame proxy | Eight stills are sampled from each `rgb.mp4`; all three supplied photo proxies yield zero accepted 3D points. No standalone still-photo files exist. |
| Strict photo-only/video-only metric reconstruction | Not met | RGB routes use synchronized pose/intrinsics metadata for metric triangulation and scale. They do not use depth maps, but they are not image-only. |
| Laser/tape accuracy and calibrated confidence intervals | Not evaluated | No independent physical reference measurements are in the supplied folders. Current intervals are explicitly uncalibrated. |
| Repeatability | Not evaluated | No second capture of the same room exists. Frame splits are not repeats. |
| Three connected rooms and whole-property stitching | Not met | The supplied bundles are three independent single-scan exports, not three connected rooms in one property. |
| Opening detection and width gate | Not implemented/evaluated | No opening inventory or detector is available. |
| Two staged damage classes and concealed-damage rules | Not implemented/evaluated | The folders contain no damage labels or validation data. |
| Scope line items | Not implemented/evaluated | No validated damage regions or pricing rules are supplied. |
| Consumer-app comparison on two rooms | Not evaluated | No named app/version or app exports are in the folders. |
| Installable iPhone capture route and device matrix | Not verified | Existing export layout is processed locally, but the capture app/version and device are not identified in the data. |
| Published output schema | Unverified | The brief's published schema was not present; this repo uses a local draft schema. |
| Reproducible benchmark measurements | Implemented for available evidence | See [benchmark summary](outputs/benchmark/benchmark_summary.md), CSV, and JSON. |

## Reproduce

Install the optional RGB dependency and run the benchmark from the repository root:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100
```

The raw folders remain intentionally ignored by Git and are not uploaded by the benchmark. A fresh clone needs the same three supplied folders copied beside the repository files.

## Submission guidance

Submit this as an exploratory implementation with the measured limitations above. Do not state that the dimensional, opening, repeatability, stitching, damage, or consumer-app acceptance gates pass. See [COMPLIANCE.md](COMPLIANCE.md) and [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) for the implementation and evidence details.
