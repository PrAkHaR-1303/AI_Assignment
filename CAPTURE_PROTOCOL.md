# Capture Route Status

The case-study workspace contains three exported LiDAR capture bundles, but it does not identify the phone app or its version and does not include an iPhone, Xcode project, signing profile, or TestFlight build. I have therefore not labeled an unverified app workflow as a ready capture route.

For a usable follow-up capture route, the app must export this folder layout without cloud processing:

1. `rgb.mp4` with the full walkthrough video.
2. `depth/NNNNNN.png` as 16-bit grayscale metric depth frames.
3. `confidence/NNNNNN.png` as 8-bit grayscale confidence frames.
4. `odometry.csv` with synchronized frame timestamps, camera translation, quaternion, and intrinsics.
5. `imu.csv` and `camera_matrix.csv`.

The operator should walk each room perimeter at a steady pace, pause at each doorway, include the floor and ceiling in at least one slow sweep, avoid rapid turns, and revisit the start of the room before stopping. Each room should be captured separately and named consistently; a multi-room run must include the connector and doorway sequence. The protocol is not ready for defense until an installable capture app/version is named and an iPhone 15-or-newer run proves this export contract.
