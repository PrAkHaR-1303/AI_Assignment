# Supplied Scan Results

These are pipeline outputs from the supplied LiDAR bundles, not benchmark accuracy scores. No laser/tape reference values were provided, so area and height errors, interval calibration, and case-study gates are not computable.

| Capture | Depth frames used | Processing time (s) | Footprint hull area (m²) | Ceiling vertical span (m) | Pre-correction loop residual (m) | Hull area before → after (m²) |
|---|---:|---:|---:|---:|---:|---:|
| `single_room` | 58 / 1,715 | 8.15 | 33.725 | Not confirmed | 0.00624 | 33.741 → 33.725 |
| `single_scan_floor_only` | 176 / 5,251 | 24.60 | 92.541 | Not confirmed | 0.00068 | 92.537 → 92.541 |
| `single_scan_with_ceiling` | 325 / 9,745 | 34.21 | 176.161 | 4.035* | 0.00015 | 176.161 → 176.161 |

`*` The ceiling sample was run with `--ceiling-observed`; 4.035 m is the point-cloud vertical span, not ground-truth ceiling height. All hull areas are uncalibrated proxies and can include furniture or unobserved space. The loop residuals are self-consistency measurements from odometry, not absolute drift errors. Timings are from the current Windows workspace and will vary with hardware.

Each row can be regenerated using the commands in [README.md](../README.md). Full JSON and SVG results are stored beside this summary.
