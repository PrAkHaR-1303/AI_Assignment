# Applied AI Case Study: Supplied-Scan Reconstruction

This repository implements three local reconstruction routes over the three supplied scan folders. It adds RGB-based sparse reconstruction for the photo and video routes and a reproducible benchmark using only the supplied folders.

## Run the tiers

Use Python 3.10 or newer from the repository root.

The LiDAR path uses only the standard library:

```powershell
python -m roomscan "single_room/c00a170fe1" --tier lidar --output "outputs/single_room_lidar"
python -m roomscan "single_scan_floor_only/1a8384c3f6" --tier lidar --output "outputs/floor_only_lidar"
python -m roomscan "single_scan_with_ceiling/c7d28f72c6" --tier lidar --output "outputs/with_ceiling_lidar" --ceiling-observed
```

The RGB routes use the video and synchronized `odometry.csv`/`camera_matrix.csv` from the same supplied folder. They do not read `depth/` or `confidence/`. Install the optional vision dependency first:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan "single_room/c00a170fe1" --tier photo --photo-count 8 --output "outputs/single_room_photo"
python -m roomscan "single_room/c00a170fe1" --tier video --max-video-frames 100 --output "outputs/single_room_video"
```

The photo route selects 2-8 still frames from the folder's `rgb.mp4`, since the supplied folders contain no separate photo files. The video route samples the RGB stream. Both triangulate ORB feature matches using the metric camera poses and intrinsics bundled with each video. These are **pose-assisted RGB tiers**, not strict photo-only or video-only systems. Their room hulls and intervals are uncalibrated proxies; inspect the quality flags in `plan.json` before interpreting them.

Each tier writes a `plan.json` and `plan.svg`. The local draft output schema is [schemas/case-study-output.schema.json](schemas/case-study-output.schema.json); the published schema referenced by the PDF was not included in the supplied workspace.

## Reproduce the benchmark

The benchmark re-runs LiDAR for each folder, computes interleaved-frame sampling stability, runs the photo/video routes, and compares their hull-area proxies to the LiDAR result from the same folder:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100
```

It writes `benchmark_measurements.json`, `benchmark_measurements.csv`, `benchmark_summary.md`, and the per-tier JSON/SVG runs under `outputs/benchmark/runs/`.

The interleaved splits show sensitivity to frame sampling within one capture. Photo/video versus LiDAR differences show internal modality consistency. Neither is an independent accuracy or repeatability benchmark: no tape/laser measurements or repeated scans are present in the folders. The report leaves the assignment's accuracy gates unevaluated.

## Inputs

Each supplied folder contains `rgb.mp4`, `depth/`, `confidence/`, `odometry.csv`, `imu.csv`, and `camera_matrix.csv`. The RGB videos are HEVC/H.265; the optional OpenCV wheel supplies FFmpeg decoding. Video frame counts match the odometry row counts in the supplied bundles.

```text
single_room/c00a170fe1/
single_scan_floor_only/1a8384c3f6/
single_scan_with_ceiling/c7d28f72c6/
```

The bundles remain ignored by Git because they contain about 874 MB of interior video and sensor data. A clone needs the supplied folders copied beside this README to regenerate results.

## Scope and limits

The LiDAR route estimates a convex-hull outline from sampled depth returns and applies a conservative single-loop translation correction when detected. The RGB routes build sparse feature-point hulls using synchronized camera poses. These are exploratory methods, not validated room plans.

Opening detection, connected multi-room stitching, damage classification, concealed-damage decisions, scope pricing, empirical interval calibration, repeat-scan repeatability, and consumer-app comparison are not established by the supplied data. The benchmark does not label these requirements as passed. See [SUBMISSION_STATUS.md](SUBMISSION_STATUS.md), [COMPLIANCE.md](COMPLIANCE.md), [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md), and [DATA_BUNDLE.md](DATA_BUNDLE.md).
