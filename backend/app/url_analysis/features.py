"""
Extracts numeric/boolean features from a URL for malicious-probability
scoring. Does NOT fetch or open the URL — purely lexical/structural
analysis of the string itself, to avoid ever hitting a potentially
malicious endpoint from the server.
"""
import re
import math
from urllib.parse import urlparse
import tldextract

# Use the bundled/offline public-suffix snapshot instead of fetching it from
# publicsuffix.org at runtime (keeps this module usable in network-restricted
# / offline server environments, and avoids a slow first-call fetch).
_no_fetch_extract = tldextract.TLDExtract(suffix_list_urls=())

SUSPICIOUS_KEYWORDS = [
    "verify", "update", "secure", "account", "login", "confirm", "banking",
    "kyc", "suspend", "unlock", "reward", "gift", "free", "bonus", "claim",
    "urgent", "limited", "click", "webscr", "signin", "password", "otp",
    "refund", "invoice", "billing", "delivery", "customs", "prize",
]

SUSPICIOUS_TLDS = {
    "xyz", "top", "live", "info", "click", "gq", "tk", "ml", "cf", "work",
    "loan", "win", "biz", "click", "party", "review",
}

KNOWN_BRANDS = [
    "paypal", "amazon", "google", "apple", "microsoft", "netflix", "facebook",
    "instagram", "whatsapp", "bank", "hdfc", "icici", "sbi", "chase", "irs",
    "gov", "linkedin", "flipkart",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def extract_features(url: str) -> dict:
    if not re.match(r"^https?://", url, re.IGNORECASE):
        normalized = "http://" + url
    else:
        normalized = url

    parsed = urlparse(normalized)
    ext = _no_fetch_extract(normalized)
    domain = ext.domain or ""
    subdomain = ext.subdomain or ""
    suffix = ext.suffix or ""
    full_domain = ".".join(p for p in [subdomain, domain, suffix] if p)
    path = parsed.path or ""
    query = parsed.query or ""

    lower_url = url.lower()

    num_subdomains = len([p for p in subdomain.split(".") if p]) if subdomain else 0

    keyword_hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw in lower_url]

    brand_hits = [b for b in KNOWN_BRANDS if b in lower_url]
    # brand impersonation heuristic: brand mentioned but NOT as the actual
    # registered domain (e.g. "paypal" in a subdomain/path but domain != paypal)
    brand_impersonation = any(b in lower_url and b != domain.lower() for b in brand_hits)

    features = {
        "url_length": len(url),
        "domain_length": len(domain),
        "subdomain_count": num_subdomains,
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_digits": sum(c.isdigit() for c in url),
        "num_special_chars": len(re.findall(r"[^a-zA-Z0-9\.\-/:_?=&]", url)),
        "has_at_symbol": "@" in url,
        "has_ip_address": bool(re.match(r"^(https?://)?\d{1,3}(\.\d{1,3}){3}", url)),
        "is_https": parsed.scheme == "https",
        "suspicious_tld": suffix.lower() in SUSPICIOUS_TLDS,
        "suspicious_keyword_count": len(keyword_hits),
        "suspicious_keywords_found": keyword_hits,
        "brand_mentioned": brand_hits,
        "possible_brand_impersonation": brand_impersonation,
        "domain_entropy": round(_shannon_entropy(domain), 3),
        "has_url_shortener": any(
            s in lower_url for s in ["bit.ly", "tinyurl", "t.co", "goo.gl", "is.gd", "cutt.ly"]
        ),
        "excessive_subdomains": num_subdomains >= 3,
        "full_domain": full_domain,
    }
    return features


def rule_based_score(features: dict) -> float:
    """
    Deterministic heuristic score (0-100) used as a fallback / sanity
    check alongside the trained ML model, and used directly when the
    trained model isn't available.
    """
    score = 0
    if not features["is_https"]:
        score += 15
    if features["has_ip_address"]:
        score += 25
    if features["has_at_symbol"]:
        score += 15
    if features["suspicious_tld"]:
        score += 15
    if features["excessive_subdomains"]:
        score += 10
    if features["has_url_shortener"]:
        score += 10
    if features["possible_brand_impersonation"]:
        score += 20
    score += min(features["suspicious_keyword_count"] * 6, 24)
    if features["url_length"] > 75:
        score += 8
    if features["domain_entropy"] > 4.0:
        score += 8
    if features["num_hyphens"] >= 3:
        score += 6
    return float(min(score, 100))
