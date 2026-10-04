# Requirements and Evidence Map

This map connects the case-study topics to the implementation and the evidence generated from the three supplied scan folders. “Available evidence” describes what these inputs demonstrate; it does not convert internal proxy comparisons into physical accuracy scores.

| Case-study topic | Implementation or artifact | Available evidence |
|---|---|---|
| LiDAR room outline and plan export | `roomscan/pipeline.py`; JSON/SVG examples in `outputs/submission_preview/` | Runs on all three bundles and exports geometric footprint estimates. |
| Photo route using 2-8 views | `roomscan/vision.py`; CLI `--tier photo` | Samples up to eight frames from each bundled RGB video. The supplied proxies yield zero accepted 3D points. |
| Video reconstruction | `roomscan/vision.py`; CLI `--tier video` | Two bundles yield sparse hulls; the third yields three points and no area. Outputs use paired pose and intrinsic metadata. |
| RGB/depth separation | `roomscan/vision.py` | RGB routes read video, odometry, and camera intrinsics; they do not read depth or confidence images. |
| RGB decoding and synchronization | OpenCV backend and `requirements-vision.txt` | Video frame counts align with odometry rows in the supplied bundles; frame IDs are checked. |
| Pose drift correction | `roomscan/geometry.py`; before/after artifacts under `outputs/single_room/`, `outputs/floor_only/`, and `outputs/with_ceiling/` | Conservative translational correction is implemented. The supplied data has no physical trajectory reference for scoring its dimensional effect. |
| Benchmark measurements | `roomscan/benchmark.py`; `outputs/benchmark/benchmark_measurements.csv`, `.json`, and `.md` | Reports geometric area proxies, cross-modal differences, and within-capture split sensitivity. |
| Empirical dimensional accuracy and interval calibration | `TECHNICAL_REPORT.md` and benchmark report | The folders contain no independent tape/laser dimensions. Current intervals are heuristic and explicitly uncalibrated. |
| Repeatability | Benchmark report | A second capture of the same room is not present; split-frame comparisons are within-capture sampling checks. |
| Connected multi-room layout | LiDAR output contract includes `stitched_property_plan` | The supplied bundles are independent single scans, without a connected-room traversal or adjacency sequence. |
| Opening detection and width measurement | Output contract and quality flags | No opening inventory or labeled reference measurements are present for evaluation. |
| Damage classes, concealed damage, and scope line items | Output contract fields | The supplied folders include no staged damage labels, validated concealment rules, or pricing schedule. |
| Consumer-app comparison | Benchmark scope | No same-room app exports or app/version details are included in the supplied data. |
| Capture-device/app characterization | Supplied bundle metadata | The folders do not identify the phone capture app/version or provide an installable capture client. |
| Output schema | `schemas/case-study-output.schema.json` | A local draft schema is included. The published schema referenced in the brief was not included in the workspace. |
| Reproduction and review | `README.md`, `outputs/submission_preview/README.md` | The benchmark can be rerun after copying the supplied folders beside the repository; compact JSON/SVG examples are included for direct review. |

For numeric benchmark results and interpretation, see the [benchmark report](outputs/benchmark/benchmark_summary.md). For the full processing method and measurement scope, see the [technical report](TECHNICAL_REPORT.md).
