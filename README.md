# SignBridge — Real-Time Sign Language Recognition

A working final-year project that recognizes American Sign Language (ASL)
alphabet signs from a webcam in real time, builds them into sentences, and
speaks them aloud — fully offline.

This repository has two parts:

1. **`signbridge-ml/`** — the actual working AI system (Python). This is the
   engine that does real recognition. **This is what you run and demo.**
2. **`signbridge/`** — a polished website / landing page that presents the
   project (good for your portfolio, GitHub, and report screenshots).

---

## How the recognition works (methodology)

```
Webcam ─▶ MediaPipe Hands ─▶ Normalize 21 landmarks ─▶ Random Forest ─▶ Letter
                                                                          │
                                              Stability buffer + cooldown ▼
                                                          Sentence ─▶ Text-to-Speech
```

1. **Hand tracking** — Google's MediaPipe detects the hand and returns
   **21 landmark points** (x, y per point).
2. **Normalization** — landmarks are shifted relative to the wrist and scaled
   by hand size, so the model works regardless of where the hand is in frame
   or how far it is from the camera. (See `utils.py`.) This is the key step
   that makes the model generalize.
3. **Classification** — a **Random Forest** trained on *your own* collected
   samples predicts the letter from the 42 normalized features.
4. **Stability buffer** — a letter is only added to the sentence after it has
   been predicted consistently for several frames, with a short cooldown.
   This is what stops the same letter repeating endlessly.
5. **Speech** — `pyttsx3` reads the finished sentence aloud, offline.

> **Note on J and Z:** these two ASL letters involve motion, so they can't be
> recognized from a single still frame. They are excluded from the static
> classifier (`LABELS` in `utils.py`). Mention this in your viva — it shows you
> understand the problem domain. Supporting them would need sequence models
> (e.g. an LSTM over multiple frames) — a good "future work" point.

---

## Setup

### 1. Check your Python version
MediaPipe supports **Python 3.8–3.11** (not 3.12+). Check:
```bash
python --version
```
If you're on 3.12+, install Python 3.11 and use it for this project.

### 2. Create a virtual environment (recommended)
```bash
cd signbridge-ml
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running it — three steps

### Step 1 — Collect your training data
```bash
python collect_data.py
```
- A webcam window opens and tracks your hand.
- Make a letter sign, then **press that letter key** (A–Z) to save a sample.
- The screen shows your sample counts and which letters need more.
- Collect **~100–150 samples per letter**, varying angle and position slightly.
- Press **ESC** to save and quit. Creates `data.csv`.

> The more varied your data, the better it works. Collect in good lighting
> against a plain background, and capture each letter from a few angles.

### Step 2 — Train the model
```bash
python train_model.py
```
- Trains the Random Forest on `data.csv`.
- Prints test accuracy and a per-letter report.
- Saves `model.pkl`. Aim for **>90% test accuracy**; if low, collect more data.

### Step 3 — Run live recognition
```bash
python app.py
```
Controls (with the camera window focused):

| Key   | Action                 |
|-------|------------------------|
| A–Z   | (just sign them)       |
| SPACE | add a space            |
| B     | backspace              |
| C     | clear sentence         |
| S     | speak the sentence     |
| ESC   | quit                   |

---

## Tuning (in `app.py`)

If recognition feels too jumpy or too slow, adjust these at the top of `app.py`:

- `STABILITY_FRAMES` — higher = steadier but slower to register a letter.
- `MIN_CONFIDENCE` — raise to reject uncertain predictions.
- `COOLDOWN_SEC` — minimum time between two committed letters.

---

## Files

| File                | Purpose                                          |
|---------------------|--------------------------------------------------|
| `utils.py`          | Landmark extraction + normalization (shared)     |
| `collect_data.py`   | Capture labeled training samples → `data.csv`    |
| `train_model.py`    | Train Random Forest → `model.pkl`                |
| `app.py`            | Live recognition + sentence building + speech    |
| `requirements.txt`  | Dependencies                                     |

---

## Tech stack

- **MediaPipe** — hand landmark detection
- **scikit-learn** — Random Forest classifier
- **OpenCV** — webcam capture and on-screen UI
- **pyttsx3** — offline text-to-speech
- **NumPy / pandas / joblib** — data handling and model persistence

---

## Suggested "future work" (for your report)

- Sequence model (LSTM / GRU) to support motion letters J and Z, and words.
- Larger, multi-person dataset for speaker-independent accuracy.
- On-device deployment to mobile (MediaPipe + TFLite).
- Word-level prediction and autocomplete.
```
