import os
import joblib
import pandas as pd

from app.url_analysis.features import extract_features, rule_based_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

_clf = None
_columns = None


def _lazy_load():
    global _clf, _columns
    if _clf is None:
        clf_path = os.path.join(MODELS_DIR, "url_classifier.joblib")
        cols_path = os.path.join(MODELS_DIR, "url_feature_columns.joblib")
        if os.path.exists(clf_path) and os.path.exists(cols_path):
            _clf = joblib.load(clf_path)
            _columns = joblib.load(cols_path)


def analyze_url(url: str) -> dict:
    features = extract_features(url)
    _lazy_load()

    ml_prob = None
    if _clf is not None:
        row = {k: v for k, v in features.items() if k in _columns}
        for c in _columns:
            if c not in row:
                row[c] = 0
        df = pd.DataFrame([row])[_columns]
        df = df.astype({c: int for c in df.columns if df[c].dtype == bool})
        ml_prob = float(_clf.predict_proba(df)[0][1]) * 100

    heuristic_score = rule_based_score(features)

    # Blend ML probability (when available) with the deterministic
    # heuristic score rather than trusting either blindly.
    if ml_prob is not None:
        final_score = round(0.7 * ml_prob + 0.3 * heuristic_score, 2)
    else:
        final_score = round(heuristic_score, 2)

    evidence = []
    if features["has_ip_address"]:
        evidence.append("URL uses a raw IP address instead of a domain name")
    if not features["is_https"]:
        evidence.append("Connection is not secured with HTTPS")
    if features["has_url_shortener"]:
        evidence.append("URL uses a link shortener, hiding the real destination")
    if features["suspicious_tld"]:
        evidence.append("Domain uses a top-level domain commonly abused for scams")
    if features["possible_brand_impersonation"]:
        evidence.append(f"Mentions a known brand ({', '.join(features['brand_mentioned'])}) outside the actual domain — possible impersonation")
    if features["excessive_subdomains"]:
        evidence.append("Unusually high number of subdomains, often used to disguise the real domain")
    if features["suspicious_keyword_count"] > 0:
        evidence.append(f"Contains suspicious keywords: {', '.join(features['suspicious_keywords_found'][:5])}")
    if features["has_at_symbol"]:
        evidence.append("Contains an '@' symbol, which can be used to obscure the true destination")

    return {
        "url": url,
        "malicious_probability": final_score,
        "ml_probability": round(ml_prob, 2) if ml_prob is not None else None,
        "heuristic_probability": round(heuristic_score, 2),
        "features": {k: v for k, v in features.items()},
        "evidence": evidence,
    }
