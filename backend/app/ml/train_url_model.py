"""
Trains a Random Forest classifier on URL structural features.

Training data: synthetically generated malicious-pattern URLs (typosquats,
IP-based links, shortened links, keyword-stuffed phishing links, excessive
subdomains) vs. legitimate-pattern URLs (real-looking clean domains).

This keeps the "URL feature extraction" (app/url_analysis/features.py)
completely decoupled from training, so the feature set can be reused for
inference regardless of how the model was trained.
"""
import os
import random
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.url_analysis.features import extract_features

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MALICIOUS_PATTERNS = [
    "http://192.168.4.55/secure-login",
    "http://verify-{b}-account.{tld}",
    "http://{b}-kyc-update.{tld}",
    "https://bit.ly/{b}verify",
    "http://{b}.security-alert-login.{tld}",
    "http://secure.{b}.confirm-payment.{tld}",
    "http://{b}support-refund-claim.{tld}",
    "http://account-{b}.suspend-notice.{tld}",
    "http://win-free-{b}-gift.{tld}",
    "http://{b}-invoice-billing-update.{tld}",
    "http://{b}@malicious-redirect.{tld}/login",
    "http://{b}.{b}.{b}.verify-secure.{tld}",
]
LEGIT_PATTERNS = [
    "https://www.{b}.com",
    "https://{b}.com/account/settings",
    "https://www.{b}.com/help/support",
    "https://mail.{b}.com",
    "https://developer.{b}.com/docs",
    "https://{b}.com/en-us/products",
    "https://checkout.{b}.com/order/12345",
    "https://news.{b}.com/latest",
    "https://{b}.com/careers",
    "https://api.{b}.com/v1/status",
]

BRANDS = ["paypal", "amazon", "google", "microsoft", "netflix", "chase",
          "hdfcbank", "icicibank", "flipkart", "linkedin", "apple", "github"]
BAD_TLDS = ["xyz", "top", "live", "info", "click", "gq", "tk", "win", "biz"]


def gen(pattern):
    return (pattern.replace("{b}", random.choice(BRANDS))
                   .replace("{tld}", random.choice(BAD_TLDS)))


def build_urls():
    rows = []
    for p in MALICIOUS_PATTERNS:
        for _ in range(15):
            rows.append((gen(p), 1))
    for p in LEGIT_PATTERNS:
        for _ in range(15):
            rows.append((gen(p), 0))
    random.shuffle(rows)
    return rows


def train():
    rows = build_urls()
    feats = []
    labels = []
    for url, label in rows:
        f = extract_features(url)
        f.pop("suspicious_keywords_found", None)
        f.pop("brand_mentioned", None)
        f.pop("full_domain", None)
        feats.append(f)
        labels.append(label)

    df = pd.DataFrame(feats)
    df = df.astype({c: int for c in df.columns if df[c].dtype == bool})

    X_train, X_test, y_train, y_test = train_test_split(
        df, labels, test_size=0.2, random_state=42, stratify=labels
    )
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print("=== URL malicious classifier ===")
    print(classification_report(y_test, preds))

    joblib.dump(clf, os.path.join(MODELS_DIR, "url_classifier.joblib"))
    joblib.dump(list(df.columns), os.path.join(MODELS_DIR, "url_feature_columns.joblib"))
    print(f"Saved to {MODELS_DIR}")


if __name__ == "__main__":
    train()
