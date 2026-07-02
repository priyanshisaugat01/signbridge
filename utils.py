"""
utils.py — shared helpers for SignBridge ML
Landmark extraction + normalization used by data collection,
training, and the live app so features are always identical.
"""

import numpy as np

# ASL static alphabet. J and Z require motion, so they are excluded
# from the static-image classifier (documented in the README).
LABELS = [c for c in "ABCDEFGHIKLMNOPQRSTUVWXY"]  # 24 static letters


def landmarks_to_features(hand_landmarks):
    """
    Convert MediaPipe hand_landmarks (21 points) into a flat,
    translation- and scale-invariant feature vector of length 42.

    Steps:
      1. Take (x, y) of all 21 landmarks.
      2. Shift so the wrist (landmark 0) is the origin.
      3. Scale by the largest absolute coordinate so hand size
         and distance from camera don't matter.
    """
    pts = []
    for lm in hand_landmarks.landmark:
        pts.append([lm.x, lm.y])
    pts = np.array(pts, dtype=np.float32)  # shape (21, 2)

    # 1 + 2: translate relative to wrist
    base = pts[0].copy()
    pts = pts - base

    # 3: scale normalize
    max_val = np.max(np.abs(pts))
    if max_val > 0:
        pts = pts / max_val

    return pts.flatten().tolist()  # length 42


FEATURE_COLUMNS = [f"{axis}{i}" for i in range(21) for axis in ("x", "y")]
