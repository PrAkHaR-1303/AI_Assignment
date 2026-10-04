# Fix Loop Declaration

## Worst current gate

Photo-tier whole-property stitch is the clearest failing gate in this submission. The measured coverage is **0 of 1 mandatory input tiers implemented** for photos; the CLI rejects photo-only input, and the workspace contains no photo capture folders. This is a product-coverage failure, not an accuracy score.

## Root-cause hypothesis and evidence

The implementation has no monocular reconstruction backend, no scale calibration source for still-image folders, and no multi-room overlap/adjacency graph. The supplied LiDAR exports cannot stand in for a photo-only capture because they already contain depth and poses. The evidence is the input inventory and the explicit unsupported-tier error in `roomscan/cli.py`.

## Fix intended and prediction

The required fix is a scale-aware multi-view photo reconstruction adapter, followed by room registration and a connector/doorway adjacency graph. The predicted result is that the same JSON/SVG contract can be emitted from per-room photo folders; the photo wall-length and stitched-footprint gates still require laser/tape ground truth before a numeric accuracy prediction is defensible.

## Shipped work and limits

This submission ships the LiDAR reader, deterministic projection, local output schema, and drift ablation. It does **not** ship the photo adapter, so the photo-tier failure remains open. The LiDAR runs do include reproducible raw-pose and corrected-pose outputs in each `outputs/<sample>/` folder. Their footprint differences are geometry-only; there is no ground truth with which to establish a gate movement. This is recorded as incomplete rather than described as a passing fix loop.
