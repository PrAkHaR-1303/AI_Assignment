# Applied AI Case Study: Indoor Room Reconstruction

This repository contains a local reconstruction pipeline, a deterministic benchmark, and reviewer-ready JSON/SVG outputs for the three scan bundles supplied with the case study.

## Included

- **LiDAR route:** projects depth returns using the supplied camera calibration and poses, then estimates a room footprint and applies a conservative translational loop correction when a revisit is detected.
- **RGB photo and video routes:** extract ORB features from the bundled RGB video and triangulate with synchronized camera poses and intrinsics. These are pose-assisted RGB routes; they do not read depth or confidence maps. The photo route samples up to eight frames because separate photo files were not supplied.
- **Benchmark:** reports per-scan area proxies, RGB/LiDAR comparisons, and sensitivity to interleaved frame sampling within each capture.
- **Outputs:** machine-readable JSON, plan SVGs, and a local output schema.

## Run

Use Python 3.10 or newer. From the repository root, install the optional RGB dependency and run the benchmark:

```powershell
python -m pip install -r requirements-vision.txt
python -m roomscan.benchmark --root . --output outputs/benchmark --frame-stride 30 --pixel-stride 6 --max-video-frames 100
```

To run an individual route:

```powershell
python -m roomscan "single_room/c00a170fe1" --tier lidar --output "outputs/single_room_lidar"
python -m roomscan "single_room/c00a170fe1" --tier photo --photo-count 8 --output "outputs/single_room_photo"
python -m roomscan "single_room/c00a170fe1" --tier video --max-video-frames 100 --output "outputs/single_room_video"
```

## Results and review

- [Benchmark measurements](outputs/benchmark/benchmark_summary.md) with CSV and JSON data
- [Plan gallery](outputs/submission_preview/README.md) with all nine tier output pairs
- [Technical report](TECHNICAL_REPORT.md)
- [Requirements and evidence map](REQUIREMENTS_EVIDENCE.md)
- [Engineering iteration record](FIX_LOOP.md)
- [Local output schema](schemas/case-study-output.schema.json)

## Evaluation scope

The implementation uses only the three supplied folders. The RGB routes use `rgb.mp4` and synchronized `odometry.csv`/`camera_matrix.csv` metadata; the LiDAR route uses depth and confidence data. Benchmark areas are geometric proxies, and RGB/LiDAR comparisons use estimates from the same capture. The supplied bundles are independent single scans and contain no physical reference measurements, repeat scans, connected multi-room walkthrough, opening inventory, damage labels, or consumer-app exports. Requirements needing those references are documented as outside the measured scope in the evidence map.

The raw folders are intentionally excluded from Git because they total about 874 MB. Copy the supplied folders beside this README before reproducing the benchmark. The repository contains compact derived output artifacts for review.
