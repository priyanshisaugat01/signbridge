"""
app.py — live sign-language recognition with the trained model.

Features:
  - Real-time hand tracking (MediaPipe) + letter prediction (your model).
  - STABILITY BUFFER: a letter is only added to the sentence once it has
    been predicted consistently for several frames. This prevents the same
    letter repeating endlessly (the "OOOOOO" problem) and makes output clean.
  - Build words and sentences on screen.
  - Offline text-to-speech with pyttsx3.

Controls (press while the window is focused):
  SPACE  - add a space
  B      - backspace (delete last character)
  C      - clear the whole sentence
  S      - speak the sentence aloud
  ESC    - quit

Run this AFTER train_model.py has produced model.pkl.
"""

import os
import time
from collections import deque, Counter

import cv2
import numpy as np
import joblib
import mediapipe as mp
import pyttsx3

from utils import landmarks_to_features

MODEL_FILE = "model.pkl"

# --- tuning knobs -----------------------------------------------------------
STABILITY_FRAMES = 12     # how many recent frames must agree on a letter
MIN_CONFIDENCE = 0.60     # ignore low-confidence predictions
COOLDOWN_SEC = 1.0        # min time between committing two letters
# ---------------------------------------------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


def main():
    if not os.path.exists(MODEL_FILE):
        print(f"ERROR: {MODEL_FILE} not found. Run train_model.py first.")
        return

    model = joblib.load(MODEL_FILE)
    tts = pyttsx3.init()
    tts.setProperty("rate", 150)

    cap = cv2.VideoCapture(0)
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    recent = deque(maxlen=STABILITY_FRAMES)   # recent stable predictions
    sentence = ""
    last_commit_time = 0.0
    current_letter = "-"
    current_conf = 0.0

    print("Running. Focus the camera window and use SPACE / B / C / S / ESC.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        predicted = None
        current_conf = 0.0

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(
                frame, hand, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
            features = np.array(landmarks_to_features(hand)).reshape(1, -1)

            probs = model.predict_proba(features)[0]
            idx = int(np.argmax(probs))
            current_conf = float(probs[idx])
            predicted = model.classes_[idx]

            if current_conf >= MIN_CONFIDENCE:
                recent.append(predicted)
                current_letter = predicted
            else:
                current_letter = "?"
        else:
            recent.clear()
            current_letter = "-"

        # commit a letter only when recent frames agree + cooldown passed
        now = time.time()
        if len(recent) == recent.maxlen:
            most_common, count = Counter(recent).most_common(1)[0]
            if count >= int(STABILITY_FRAMES * 0.8) and (now - last_commit_time) > COOLDOWN_SEC:
                sentence += most_common
                last_commit_time = now
                recent.clear()
                print(f"Added '{most_common}' -> {sentence}")

        draw_ui(frame, current_letter, current_conf, sentence)

        cv2.imshow("SignBridge - Live Recognition", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 27:        # ESC
            break
        elif key == 32:      # SPACE
            sentence += " "
        elif key in (ord("b"), ord("B")):
            sentence = sentence[:-1]
        elif key in (ord("c"), ord("C")):
            sentence = ""
        elif key in (ord("s"), ord("S")):
            if sentence.strip():
                tts.say(sentence)
                tts.runAndWait()

    cap.release()
    hands.close()
    cv2.destroyAllWindows()


def draw_ui(frame, letter, conf, sentence):
    h, w = frame.shape[:2]
    green = (140, 230, 0)

    # current prediction box
    cv2.rectangle(frame, (10, 10), (260, 120), (20, 20, 20), -1)
    cv2.putText(frame, "Prediction", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    cv2.putText(frame, str(letter), (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, green, 3)
    cv2.putText(frame, f"{conf*100:4.0f}%", (140, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, green, 2)

    # sentence bar at the bottom
    cv2.rectangle(frame, (0, h - 70), (w, h), (20, 20, 20), -1)
    cv2.putText(frame, "Sentence:", (15, h - 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
    cv2.putText(frame, sentence[-40:] + "|", (15, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # controls hint
    cv2.putText(frame, "SPACE=space  B=back  C=clear  S=speak  ESC=quit",
                (w - 470, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)


if __name__ == "__main__":
    main()
