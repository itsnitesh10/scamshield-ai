"""
AI Investigator: takes the STRUCTURED output of the ML risk engine
(never the other way around) and produces a plain-language explanation,
attacker-intent summary and recommended action.

Important: this layer never re-decides the scam probability. It only
explains/contextualizes numbers that already came from the ML detectors
and the risk engine. If no LLM is configured, a deterministic
rule-based explanation generator produces an equivalent structured
result so the feature still works end-to-end without an API key.
"""
import json
from app.ai_investigator.providers import get_provider, NoOpProvider

SYSTEM_PROMPT = """You are a cybersecurity analyst assistant embedded in a scam-detection \
product called ScamShield AI. You are given structured, already-computed machine-learning \
detection results (risk score, scam category, evidence signals) for a piece of user-submitted \
content. Your job is ONLY to explain and contextualize these results for a non-technical user — \
you do NOT re-classify or override the risk score.

Respond ONLY with valid JSON, no markdown fences, no preamble, in this exact shape:
{
  "simple_explanation": "one or two plain-language sentences",
  "why_suspicious": ["short bullet", "short bullet", ...],
  "attacker_goal": "one sentence describing what the attacker is trying to get the victim to do",
  "recommended_action": ["short imperative bullet", "short imperative bullet", ...]
}
"""


def _build_user_prompt(risk_result: dict, submitted_text: str, url_result: dict = None) -> str:
    payload = {
        "overall_risk_score": risk_result.get("overall_risk_score"),
        "risk_level": risk_result.get("risk_level"),
        "scam_category": risk_result.get("scam_category"),
        "confidence": risk_result.get("confidence"),
        "evidence": risk_result.get("evidence"),
        "submitted_content_excerpt": (submitted_text or "")[:600],
    }
    if url_result:
        payload["url_analysis"] = {
            "url": url_result.get("url"),
            "malicious_probability": url_result.get("malicious_probability"),
            "evidence": url_result.get("evidence"),
        }
    return json.dumps(payload, indent=2)


def _rule_based_fallback(risk_result: dict) -> dict:
    level = risk_result.get("risk_level", "Low")
    category = risk_result.get("scam_category") or "suspicious content"
    evidence = risk_result.get("evidence", [])

    action_map = {
        "Critical": [
            "Do not click any links or share any codes/passwords.",
            "Do not make any payment or share OTP.",
            "Report and block the sender.",
            "Contact the organization directly using their official app or website.",
        ],
        "High": [
            "Avoid clicking links or replying with personal/financial details.",
            "Verify independently through the organization's official channel.",
            "Do not share OTP, passwords, or card details.",
        ],
        "Medium": [
            "Be cautious before acting on this message.",
            "Verify the sender's identity through an independent channel.",
        ],
        "Low": [
            "No strong signs of a scam were found, but stay cautious with unexpected requests.",
        ],
    }

    return {
        "simple_explanation": f"This content was rated {level} risk ({risk_result.get('overall_risk_score')}/100), "
                               f"most consistent with a {category.replace('_', ' ')} pattern.",
        "why_suspicious": evidence,
        "attacker_goal": "Likely trying to get you to click a link, share credentials/OTP, or send money."
                          if level in ("Critical", "High") else "No clear malicious intent detected.",
        "recommended_action": action_map.get(level, action_map["Low"]),
        "generated_by": "rule_based_fallback",
    }


def investigate(risk_result: dict, submitted_text: str = "", url_result: dict = None) -> dict:
    provider = get_provider()

    if isinstance(provider, NoOpProvider):
        return _rule_based_fallback(risk_result)

    user_prompt = _build_user_prompt(risk_result, submitted_text, url_result)
    try:
        raw = provider.generate(SYSTEM_PROMPT, user_prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json\n", "", 1) if cleaned.startswith("json\n") else cleaned
        parsed = json.loads(cleaned)
        parsed["generated_by"] = "llm"
        return parsed
    except Exception:
        # Never let an LLM/network failure break the core detection response —
        # degrade gracefully to the rule-based explanation.
        fallback = _rule_based_fallback(risk_result)
        fallback["generated_by"] = "rule_based_fallback_after_llm_error"
        return fallback
