"""
Trains the text scam-classification pipeline:
  1. Binary classifier: scam vs safe  (TF-IDF + Logistic Regression)
  2. Multiclass classifier: scam type (TF-IDF + Random Forest), trained
     only on rows labeled as scam.

v2 changes (fixing accuracy/reliability issues from v1):
  - Proper 3-way split: train / validation / test (stratified), instead
    of a single train/test split. The validation set is used to sanity
    check the model during development; the held-out test set is only
    ever scored once at the end and is what the printed metrics reflect.
  - De-duplicates rows before splitting so no identical message can
    appear in both train and test (train/test leakage check).
  - Vectorizer is fit ONLY on the training split, never on val/test,
    so evaluation numbers reflect genuine generalization.
  - Prints accuracy, precision, recall, F1, and a confusion matrix for
    both the binary and scam-type models, instead of just accuracy.
  - Retrains against whatever scikit-learn version is currently
    installed, which also fixes the
    "'LogisticRegression' object has no attribute 'multi_class'" error
    that happens when a .joblib saved under one sklearn version is
    loaded under a different one. If you ever see that error again,
    it means your installed scikit-learn version changed since the
    models were last trained -- just re-run this script to fix it.

Run:  python -m app.ml.train_text_model
"""
import os
import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_recall_fscore_support,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "app", "data", "labeled_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def _print_metrics(name, y_true, y_pred, labels=None):
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    print(f"\n=== {name} — held-out TEST set ===")
    print(f"Accuracy:  {acc:.3f}")
    print(f"Precision: {precision:.3f}  (weighted avg)")
    print(f"Recall:    {recall:.3f}  (weighted avg)")
    print(f"F1-score:  {f1:.3f}  (weighted avg)")
    print("\nFull classification report:")
    print(classification_report(y_true, y_pred, zero_division=0))
    print("Confusion matrix:")
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    if labels is not None:
        print("Labels order:", list(labels))
    print(cm)


def train():
    print(f"scikit-learn version in use for training: {sklearn.__version__}")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "label"])

    before = len(df)
    df = df.drop_duplicates(subset=["text"])
    after = len(df)
    if before != after:
        print(f"Removed {before - after} duplicate text rows before splitting "
              f"(prevents train/test leakage).")

    # --- 3-way stratified split: 70% train / 15% val / 15% test ---
    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=42, stratify=df["label"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=42, stratify=temp_df["label"]
    )
    print(f"\nSplit sizes -> train: {len(train_df)}  val: {len(val_df)}  test: {len(test_df)}")

    # --- Binary scam/safe classifier ---
    vectorizer = TfidfVectorizer(
        max_features=6000, ngram_range=(1, 2), stop_words="english",
        min_df=1, sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(train_df["text"])
    X_val_vec = vectorizer.transform(val_df["text"])
    X_test_vec = vectorizer.transform(test_df["text"])

    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)
    clf.fit(X_train_vec, train_df["label"])

    val_preds = clf.predict(X_val_vec)
    print(f"\n[validation check] binary classifier accuracy: {accuracy_score(val_df['label'], val_preds):.3f}")

    test_preds = clf.predict(X_test_vec)
    _print_metrics("Binary scam/safe classifier", test_df["label"], test_preds, labels=[0, 1])

    joblib.dump(vectorizer, os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
    joblib.dump(clf, os.path.join(MODELS_DIR, "binary_classifier.joblib"))

    # --- Scam type multiclass classifier (trained on scam rows only) ---
    scam_train = train_df[train_df["label"] == 1]
    scam_val = val_df[val_df["label"] == 1]
    scam_test = test_df[test_df["label"] == 1]

    type_vectorizer = TfidfVectorizer(
        max_features=6000, ngram_range=(1, 2), stop_words="english",
        min_df=1, sublinear_tf=True,
    )
    Xt_train = type_vectorizer.fit_transform(scam_train["text"])
    Xt_val = type_vectorizer.transform(scam_val["text"])
    Xt_test = type_vectorizer.transform(scam_test["text"])

    type_clf = RandomForestClassifier(
        n_estimators=300, random_state=42, class_weight="balanced_subsample",
        min_samples_leaf=1,
    )
    type_clf.fit(Xt_train, scam_train["scam_type"])

    val_type_preds = type_clf.predict(Xt_val)
    print(f"\n[validation check] scam-type classifier accuracy: {accuracy_score(scam_val['scam_type'], val_type_preds):.3f}")

    test_type_preds = type_clf.predict(Xt_test)
    _print_metrics(
        "Scam type classifier", scam_test["scam_type"], test_type_preds,
        labels=sorted(scam_test["scam_type"].unique()),
    )

    joblib.dump(type_vectorizer, os.path.join(MODELS_DIR, "type_tfidf_vectorizer.joblib"))
    joblib.dump(type_clf, os.path.join(MODELS_DIR, "scam_type_classifier.joblib"))

    print(f"\nModels saved to {MODELS_DIR}")
    print("NOTE: these test-set scores reflect performance on this project's own "
          "synthetic/template dataset. They are a pipeline-correctness check, not "
          "a real-world accuracy benchmark -- swap in a larger real-world labeled "
          "dataset (same text,label,scam_type CSV format) before relying on this "
          "for production-grade accuracy claims.")


if __name__ == "__main__":
    train()
