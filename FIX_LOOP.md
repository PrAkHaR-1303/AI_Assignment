# Fix Loop: Sparse RGB Tier Coverage

**Status: experimental adapter shipped; dimensional fix not demonstrated.** This record uses only the three supplied folders and does not claim an accuracy gate passed.

## Failure selected

Before the RGB work, photo/video input was rejected: adapter coverage was 0/2. The remaining assignment risk was the absence of non-LiDAR routes. The largest measurable weakness in the supplied-data benchmark is that every eight-frame photo proxy produced zero accepted triangulated points. Video hull-area disagreement from LiDAR is 56.84% and 90.67% for the two bundles with estimates; the third video proxy has only three points.

The LiDAR within-scan split area differences are 26.44%, 19.97%, and 5.64%. They indicate sensitivity to sample phase, not repeat-scan repeatability.

## Root-cause evidence

The RGB implementation uses ORB matches, an essential-matrix RANSAC filter, and triangulation against the camera poses/intrinsics bundled with each RGB video. A photo proxy samples up to eight stills from the video; the data contains no standalone still photos. The selected wide-spaced frames do not supply enough accepted overlapping feature tracks for triangulation. Video gives more matches, but point hulls still differ substantially from the LiDAR hulls and lack independent physical scoring.

## Shipped change and observed result

Shipped `roomscan/vision.py` with separate photo and video input paths. Both use RGB for feature observations and the paired pose/intrinsics files for metric triangulation; neither reads depth or confidence maps. Added frame-ID synchronization checks, per-pair match counts, triangulated point counts, reprojection statistics, SVG/JSON outputs, and a reproducible benchmark.

| Evidence | Before | After |
|---|---:|---:|
| RGB tier adapters available | 0/2 | 2/2 experimental paths |
| Photo proxy accepted points | No path | 0 for all 3 supplied captures |
| Video proxy | No path | 2 sparse hulls; one insufficient-point result |
| Accuracy gate movement | Not measurable | Not measurable; no independent ground truth |

## Next iteration boundary

The current photo selection and sparse geometry do not support a room-dimension claim. Do not describe adapter coverage as accuracy success. The benchmark outputs preserve this result rather than substituting a LiDAR-derived value for a photo estimate. A meaningful accuracy fix cannot be scored from these folders because they contain no independent room dimensions, repeat capture, or separate photo-only capture.
