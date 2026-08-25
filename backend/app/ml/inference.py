"""
Loads the trained text models once at process startup and exposes a
simple predict() function used by the API layer. Also computes basic
explainability signals (top contributing terms) using the logistic
regression coefficients / TF-IDF weights of the submitted text, which
approximates SHAP-style local explanations without the runtime cost of
full SHAP for a linear model.
"""
import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

_vectorizer = None
_binary_clf = None
_type_vectorizer = None
_type_clf = None


class ModelLoadError(Exception):
    pass


def _lazy_load():
    global _vectorizer, _binary_clf, _type_vectorizer, _type_clf
    if _vectorizer is None:
        try:
            _vectorizer = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
            _binary_clf = joblib.load(os.path.join(MODELS_DIR, "binary_classifier.joblib"))
            _type_vectorizer = joblib.load(os.path.join(MODELS_DIR, "type_tfidf_vectorizer.joblib"))
            _type_clf = joblib.load(os.path.join(MODELS_DIR, "scam_type_classifier.joblib"))
        except AttributeError as e:
            # Happens when the saved .joblib files were pickled with a
            # different scikit-learn version than what's currently
            # installed (e.g. the old "'LogisticRegression' object has
            # no attribute 'multi_class'" error). Fix: retrain locally
            # against the currently installed scikit-learn so the
            # pickled objects match — never downgrade/pin sklearn to
            # chase an old model file.
            raise ModelLoadError(
                "Saved ML models appear to be incompatible with the currently "
                "installed scikit-learn version. Retrain them by running "
                "'python -m app.ml.train_text_model' from the backend directory "
                f"(original error: {e})"
            )


def models_available() -> bool:
    required = ["tfidf_vectorizer.joblib", "binary_classifier.joblib",
                "type_tfidf_vectorizer.joblib", "scam_type_classifier.joblib"]
    return all(os.path.exists(os.path.join(MODELS_DIR, f)) for f in required)


def _top_contributing_terms(text: str, top_n: int = 8) -> list:
    """Local explainability: which words in THIS text pushed the score
    toward 'scam', based on TF-IDF weight * logistic-regression coefficient."""
    vec = _vectorizer.transform([text])
    coefs = _binary_clf.coef_[0]
    feature_names = np.array(_vectorizer.get_feature_names_out())

    nonzero_idx = vec.nonzero()[1]
    if len(nonzero_idx) == 0:
        return []

    contributions = vec[0, nonzero_idx].toarray().flatten() * coefs[nonzero_idx]
    terms = feature_names[nonzero_idx]

    order = np.argsort(contributions)[::-1]
    top = [
        {"term": terms[i], "contribution": round(float(contributions[i]), 4)}
        for i in order[:top_n] if contributions[i] > 0
    ]
    return top


def predict_text(text: str) -> dict:
    _lazy_load()
    if not text or not text.strip():
        return {
            "scam_probability": 0.0,
            "predicted_label": "safe",
            "scam_type": None,
            "scam_type_confidence": None,
            "top_terms": [],
        }

    vec = _vectorizer.transform([text])
    proba = _binary_clf.predict_proba(vec)[0]
    scam_prob = float(proba[1]) * 100

    result = {
        "scam_probability": round(scam_prob, 2),
        "predicted_label": "scam" if scam_prob >= 50 else "safe",
        "scam_type": None,
        "scam_type_confidence": None,
        "top_terms": _top_contributing_terms(text),
    }

    if scam_prob >= 40:  # still classify type even near the boundary, for evidence
        type_vec = _type_vectorizer.transform([text])
        type_proba = _type_clf.predict_proba(type_vec)[0]
        best_idx = int(np.argmax(type_proba))
        result["scam_type"] = _type_clf.classes_[best_idx]
        result["scam_type_confidence"] = round(float(type_proba[best_idx]) * 100, 2)

    return result
