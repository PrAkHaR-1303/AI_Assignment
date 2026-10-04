# Engineering Iteration Record: RGB Route Coverage

## Objective

Add photo and video processing paths to the existing LiDAR reconstruction package, using only the three supplied scan folders. The RGB paths must avoid depth and confidence images and record enough diagnostics to evaluate their behavior.

## Implementation

`roomscan/vision.py` adds separate photo and video routes. Both detect and match ORB image features, filter matches with essential-matrix RANSAC, and triangulate from synchronized metric camera poses and intrinsics. The photo route selects up to eight frames from the bundled video because no standalone photographs are supplied. Frame-ID checks, match counts, triangulated-point counts, reprojection statistics, JSON output, and SVG output are recorded.

## Measured results

| Measure | Before iteration | After iteration |
|---|---:|---:|
| RGB route implementations | 0 | 2 experimental routes |
| Photo proxy accepted points | No route | 0 across the three bundles |
| Video proxy | No route | 362 points / 3.146 m²; 163 points / 39.941 m²; 3 points / no area |
| Independent accuracy comparison | No reference data | No reference data |

Video area differences from the same-capture LiDAR proxy are 90.67% and 56.84% for the two bundles with a reported area. The third has too few points for an area. These measurements show code-path coverage and current reconstruction behavior; they do not establish room-dimension accuracy.

The LiDAR interleaved-frame split area differences are 26.44%, 19.97%, and 5.64%. They describe sensitivity to frame sampling within one scan and are not repeated-scan results.

## Evaluation boundary

The supplied videos do not provide independent still-photo captures or physical room dimensions. Further changes to matching parameters can be measured against the same internal proxy comparisons, but an accuracy improvement cannot be demonstrated without independent references. The current outputs preserve the observed point counts and area differences rather than substituting a different tier's estimate.

See [the benchmark report](outputs/benchmark/benchmark_summary.md) and [the plan gallery](outputs/submission_preview/README.md) for the per-capture results.
