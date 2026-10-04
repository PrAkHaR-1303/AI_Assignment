# Applied AI Case Study: Room Scan Baseline

This repository contains a deterministic, offline LiDAR-tier baseline for the three capture bundles supplied with the case study. It reads the raw depth maps, confidence maps, camera intrinsics, and per-frame poses, applies a conservative trajectory revisit correction when one is visible, and writes a JSON result plus a dimensioned SVG plan and a before/after drift ablation.

## Run one capture

From the repository root, use Python 3.10 or newer. The implementation uses only the Python standard library:

```powershell
python -m roomscan "single_room/c00a170fe1" --output "outputs/single_room"
```

The same command works for the other supplied LiDAR captures:

```powershell
python -m roomscan "single_scan_floor_only/1a8384c3f6" --output "outputs/floor_only"
python -m roomscan "single_scan_with_ceiling/c7d28f72c6" --output "outputs/with_ceiling" --ceiling-observed
```

Each run creates `plan.json`, `plan.svg`, `before_fix.json`, `before_fix.svg`, and `drift_ablation.json`. The local draft output contract is in `schemas/case-study-output.schema.json`; the case-study PDF refers to a published schema that was not included. `--frame-stride` and `--pixel-stride` control the deterministic sampling rate. For a denser run, try `--frame-stride 15 --pixel-stride 8`; using every frame at full pixel resolution can require substantial memory.

## What the baseline measures

The LiDAR path projects sampled 16-bit depth pixels into the odometry frame, estimates a 2D convex-hull footprint and candidate boundary segments, reports a ceiling-height proxy only when an operator confirms the ceiling was captured, and emits per-measurement uncertainty intervals. The intervals are explicitly marked uncalibrated because the workspace contains no laser/tape ground truth.

Photo-only and video-only reconstruction, opening detection, damage classification, concealed-damage rules, scope pricing, and multi-room registration are not implemented. Those need image reconstruction/model inputs, labeled damage examples, a connector-room benchmark, and independent measurements. The code emits these fields with a `not_assessed` status instead of inventing results. See [COMPLIANCE.md](COMPLIANCE.md) for the complete requirement map and [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) for the current error budget and fix-loop account.

## Input bundle layout

```text
capture/
  camera_matrix.csv
  odometry.csv
  imu.csv
  rgb.mp4
  depth/000000.png ...
  confidence/000000.png ...
```

The video is recorded in the bundle but is not decoded in this baseline. Depth values are interpreted as millimeters and converted to meters. Camera intrinsics are scaled from the RGB principal-point dimensions to the 256 x 192 depth maps. Ceiling height remains unreported by default; pass `--ceiling-observed` only when an operator verified that a ceiling surface was captured, as shown in the ceiling sample command above.

## Reproduction notes

The pipeline is local and makes no network calls. Its output depends only on the capture files and CLI parameters. JSON includes the chosen sampling rates, data counts, assumptions, and the exact input capture path. The depth projection and plane/hull estimates are engineering baselines, not a validated product or a claim that the case-study accuracy gates pass.
