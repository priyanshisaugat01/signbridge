"""
collect_data.py — capture your own hand-sign training data.

How it works:
  - Opens your webcam and tracks one hand with MediaPipe.
  - Show a letter sign, then press that letter key (A-Z) to save
    a sample of the current hand pose, labeled with that letter.
  - Live on-screen counts show how many samples you have per letter.
  - Aim for ~100-150 samples per letter, from slightly different
    angles/positions, for a robust model.
  - Press ESC to save everything and quit.

Output: data.csv  (42 landmark features + a 'label' column)

Tip: collect in good, even lighting against a plain background.
"""

import csv
import os
import cv2
import mediapipe as mp

from utils import landmarks_to_features, FEATURE_COLUMNS, LABELS

DATA_FILE = "data.csv"

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def load_counts():
    counts = {l: 0 for l in LABELS}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            for row in reader:
                if row:
                    lbl = row[-1]
                    counts[lbl] = counts.get(lbl, 0) + 1
    return counts


def ensure_header():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as f:
            csv.writer(f).writerow(FEATURE_COLUMNS + ["label"])


def main():
    ensure_header()
    counts = load_counts()
    print("Loaded existing sample counts:", counts)
    print("\nShow a sign, then press its letter key to capture. ESC to quit.\n")

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    csv_file = open(DATA_FILE, "a", newline="")
    writer = csv.writer(csv_file)

    last_features = None

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        last_features = None
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame, hand, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
            last_features = landmarks_to_features(hand)
            cv2.putText(frame, "Hand detected - press a letter to save",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 230, 140), 2)
        else:
            cv2.putText(frame, "No hand detected",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # show total + a few lowest-count letters to guide collection
        total = sum(counts.values())
        cv2.putText(frame, f"Total samples: {total}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        lowest = sorted(counts.items(), key=lambda x: x[1])[:6]
        hint = "Need more: " + ", ".join(f"{k}({v})" for k, v in lowest)
        cv2.putText(frame, hint,
                    (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("SignBridge - Data Collection", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            break
        # letter keys
        if key != 255:
            ch = chr(key).upper()
            if ch in LABELS and last_features is not None:
                writer.writerow(last_features + [ch])
                counts[ch] += 1
                print(f"Saved sample for '{ch}'  (now {counts[ch]})")

    csv_file.close()
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    print("\nDone. Final counts:", counts)
    print(f"Saved to {DATA_FILE}")


if __name__ == "__main__":
    main()
