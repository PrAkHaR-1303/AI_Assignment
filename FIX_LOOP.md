# Fix Loop Declaration

**Rubric status: incomplete.** The drift-correction ablation is shipped, but the worst declared failure is photo-tier whole-property stitching and the photo fix itself is not implemented. This package does not satisfy the brief's requirement for a shipped fix to the worst-performing gate.

## Worst current gate

Photo-tier whole-property stitch is the clearest failing gate in this submission. Photo-adapter coverage is **0/1 required photo input modes**: the CLI rejects photo-only input, and the workspace contains no photo capture folders. This is a product-coverage failure, not an accuracy score.

## Root-cause hypothesis and evidence

The implementation has no monocular reconstruction backend, no scale calibration source for still-image folders, and no multi-room overlap/adjacency graph. The supplied LiDAR exports cannot stand in for a photo-only capture because they already contain depth and poses. The evidence is the input inventory and the explicit unsupported-tier error in `roomscan/cli.py`.

## Fix intended and prediction

The required fix is a scale-aware multi-view photo reconstruction adapter, followed by room registration and a connector/doorway adjacency graph. The implementation target is to move photo-adapter coverage from **0/1 to 1/1**. No wall-length or stitched-footprint accuracy value is predicted without photo captures and laser/tape truth.

## Shipped work and limits

This submission ships the LiDAR reader, deterministic projection, local output schema, and drift ablation. It does **not** ship the photo adapter, so coverage remains **0/1** and this fix loop remains incomplete. The LiDAR runs include raw-pose and corrected-pose outputs in each `outputs/<sample>/` folder. Their footprint differences are geometry-only; there is no ground truth with which to establish a gate movement. The drift correction is separate work and does not repair the worst photo-tier failure.
