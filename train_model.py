"""
train_model.py — train the Random Forest on collected landmark data.

Reads data.csv, trains a classifier, reports accuracy on a held-out
test set, and saves the trained model to model.pkl.

Run this AFTER collecting data with collect_data.py.
"""

import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATA_FILE = "data.csv"
MODEL_FILE = "model.pkl"


def main():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found. Run collect_data.py first.")
        return

    df = pd.read_csv(DATA_FILE)
    if len(df) < 50:
        print(f"WARNING: only {len(df)} samples. Collect more for a reliable model.")

    X = df.drop(columns=["label"]).values
    y = df["label"].values

    print(f"Loaded {len(df)} samples across {len(set(y))} letters.")
    print("Per-letter counts:")
    print(df["label"].value_counts().sort_index().to_string())

    # stratified split so every letter appears in train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        n_jobs=-1,
        random_state=42,
    )
    print("\nTraining Random Forest...")
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nTest accuracy: {acc * 100:.2f}%\n")
    print("Classification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(clf, MODEL_FILE)
    print(f"Saved trained model to {MODEL_FILE}")


if __name__ == "__main__":
    main()
