# Supplied-Scan Benchmark Measurements

This benchmark uses only the three supplied folders. Values are measured from the current LiDAR reconstruction and are not ground-truth accuracy scores.
Runtime: Python 3.14.7, OpenCV 5.0.0; frame stride 30, pixel stride 6, video cap 100 frames.

| Scan | LiDAR area (m²) | Photo points | Photo area (m²) | Video points | Video area (m²) | Video vs LiDAR (%) | Split LiDAR area difference (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `single_room` | 33.725 | 0 | — | 362 | 3.146 | 90.67 | 26.44 |
| `single_scan_floor_only` | 92.541 | 0 | — | 163 | 39.941 | 56.84 | 19.97 |
| `single_scan_with_ceiling` | 176.161 | 0 | — | 3 | — | — | 5.64 |

## Interpretation

- LiDAR area, width, length, and vertical extent are geometric proxies from the supplied scans; they are not tape-measured room dimensions.
- Photo uses up to eight still frames sampled from the bundled RGB video; video uses a deterministic subsample of the full RGB stream. Both triangulate RGB feature matches with camera poses and intrinsics from the same bundle. Neither reads depth/ or confidence/.
- Photo/video versus LiDAR differences are internal cross-modal comparisons, not errors against an independent truth source. These pose-assisted paths are not strict image-only tiers.
- Split differences compare interleaved frames from one scan and describe sensitivity to frame sampling only. They are not repeat-scan repeatability.
- Photo/video metric accuracy, opening width, ceiling accuracy, staged-damage detection, multi-room stitching, and consumer-app comparison are not measured by this dataset.
- No acceptance gate is marked passed without the corresponding independent reference data.

## Reproduce

`python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100`
