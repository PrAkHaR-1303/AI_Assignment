# Supplied Scan Results

These are pipeline outputs from the supplied LiDAR bundles, not benchmark accuracy scores. No laser/tape reference values were provided, so area and height errors, interval calibration, and case-study gates are not computable.

| Capture | Depth frames used | Processing time (s) | Footprint hull area (m²) | Ceiling vertical span (m) | Pre-correction loop residual (m) | Hull area before → after (m²) |
|---|---:|---:|---:|---:|---:|---:|
| `single_room` | 58 / 1,715 | 5.47 | 33.725 | Not confirmed | 0.00624 | 33.741 → 33.725 |
| `single_scan_floor_only` | 176 / 5,251 | 13.17 | 92.541 | Not confirmed | 0.00068 | 92.537 → 92.541 |
| `single_scan_with_ceiling` | 325 / 9,745 | 22.84 | 176.161 | 4.035* | 0.00015 | 176.161 → 176.161 |

`*` The ceiling sample was run with `--ceiling-observed`; 4.035 m is the point-cloud vertical span, not ground-truth ceiling height. All hull areas are uncalibrated proxies and can include furniture or unobserved space. The loop residuals are self-consistency measurements from odometry, not absolute drift errors. Timings were freshly recorded in the current Windows workspace and will vary with hardware.

Each row can be regenerated using the commands in [README.md](../README.md). Full JSON and SVG results are stored beside this summary.

## Case-study gate evaluation

The three local LiDAR commands were rerun successfully during review and regenerated all five expected artifacts per sample. This verifies that the supplied-export LiDAR path executes; it does not establish measurement accuracy.

| Gate | Required evidence | Result |
|---|---|---|
| Per-room wall lengths and floor area | Laser/tape references for each room | Not evaluated; no ground truth |
| Opening detection and width | Annotated opening inventory and measured widths | Not evaluated; opening detector is not implemented |
| Ceiling height | Independent per-room height measurements | Not evaluated; the reported 4.035 m is only a point-cloud vertical span |
| Repeatability | Two same-tier scans of the same room | Not evaluated; no repeat scan supplied |
| Photo-tier whole-property plan | Per-room photos, connector, correct adjacency, calibrated footprint | Not implemented; no photo-only input path or connector capture |
| Video-tier measurement | Video-only run and ground truth | Not implemented; RGB video is present but not decoded |
| Drift accountability | On/off ablation scored against footprint ground truth | Partial; geometric ablation exists, but no truth-based score |
| Consumer-app comparison | Same two rooms, app/version, exports, and dimension errors | Missing |

The repository's [submission status](../SUBMISSION_STATUS.md) explains the remaining evidence and implementation gaps. These entries are intentionally marked unevaluated instead of inferred from plausible-looking plans.
