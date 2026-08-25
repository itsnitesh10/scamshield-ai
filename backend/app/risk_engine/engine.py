"""
Combines individual detector signals (text ML, URL ML, brand-impersonation
heuristic, OCR confidence) into one overall risk score.

Design notes (why this ISN'T a blind average):
  - Each signal is only included if it's actually applicable to this
    submission (e.g. no URL was submitted -> URL signal excluded, not
    counted as 0).
  - Signals are weighted by how directly they indicate "scam intent"
    vs. supporting context. Text content and URL maliciousness are the
    two strongest independent signals; brand-impersonation is a strong
    but narrower signal; OCR confidence is a quality/uncertainty
    modifier, not a scam signal itself, and instead widens or narrows
    our confidence in the other scores.
  - A "critical override": if ANY single strong signal (text or URL)
    independently clears a very high bar (>=90), the overall risk is
    floored near that value even if other signals are moderate — a
    single very-high-confidence detector shouldn't get diluted by
    averaging with weaker/absent ones.
"""
from dataclasses import dataclass, field
from typing import Optional


RISK_LEVELS = [
    (85, "Critical"),
    (65, "High"),
    (35, "Medium"),
    (0, "Low"),
]


def risk_level_from_score(score: float) -> str:
    for threshold, label in RISK_LEVELS:
        if score >= threshold:
            return label
    return "Low"


@dataclass
class SignalInput:
    text_scam_probability: Optional[float] = None
    text_scam_type: Optional[str] = None
    text_scam_type_confidence: Optional[float] = None
    url_malicious_probability: Optional[float] = None
    url_evidence: list = field(default_factory=list)
    ocr_confidence: Optional[float] = None  # 0-100, quality of OCR extraction
    text_top_terms: list = field(default_factory=list)


WEIGHTS = {
    "text": 0.55,
    "url": 0.45,
}


def compute_overall_risk(signal: SignalInput) -> dict:
    active_signals = {}
    if signal.text_scam_probability is not None:
        active_signals["text"] = signal.text_scam_probability
    if signal.url_malicious_probability is not None:
        active_signals["url"] = signal.url_malicious_probability

    if not active_signals:
        return {
            "overall_risk_score": 0.0,
            "risk_level": "Low",
            "scam_category": None,
            "confidence": 0.0,
            "signals": {},
            "evidence": ["No analyzable content was submitted."],
        }

    # Weighted combination, re-normalized to only active signals
    total_weight = sum(WEIGHTS[k] for k in active_signals)
    weighted_sum = sum(active_signals[k] * WEIGHTS[k] for k in active_signals) / total_weight

    # Critical override: don't dilute a very strong single signal
    max_signal = max(active_signals.values())
    if max_signal >= 90:
        overall = max(weighted_sum, max_signal - 3)
    else:
        overall = weighted_sum

    overall = round(min(overall, 100), 2)

    # Confidence: how much evidence backs this score.
    # More active signals + higher OCR quality (if used) -> higher confidence.
    confidence = 50 + 15 * len(active_signals)
    if signal.ocr_confidence is not None:
        confidence = confidence * (0.5 + 0.5 * (signal.ocr_confidence / 100))
    if signal.text_scam_type_confidence:
        confidence = (confidence + signal.text_scam_type_confidence) / 2
    confidence = round(min(confidence, 99), 2)

    evidence = []
    if signal.text_scam_probability is not None and signal.text_scam_probability >= 40:
        if signal.text_top_terms:
            terms = ", ".join(t["term"] for t in signal.text_top_terms[:5])
            evidence.append(f"Suspicious language patterns detected: {terms}")
        if signal.text_scam_type:
            evidence.append(f"Message content matches known '{signal.text_scam_type.replace('_', ' ')}' patterns")
    evidence.extend(signal.url_evidence)

    scam_category = None
    if signal.text_scam_type and (signal.text_scam_probability or 0) >= 40:
        scam_category = signal.text_scam_type
    elif signal.url_malicious_probability and signal.url_malicious_probability >= 60:
        scam_category = "phishing"

    return {
        "overall_risk_score": overall,
        "risk_level": risk_level_from_score(overall),
        "scam_category": scam_category,
        "confidence": confidence,
        "signals": active_signals,
        "evidence": evidence if evidence else ["No strong suspicious indicators detected."],
    }
