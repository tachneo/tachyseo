import hashlib
import html
import json
import os
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

BLOCKED_LOCATION_TERMS = {
    "name", "top", "best", "near", "near me", "cheap", "good", "software", "erp",
    "school", "school erp", "school software", "management software", "school management",
}
SUSPICIOUS_TOKENS = {"http", "www", ".com", "buy", "sale", "discount", "download", "free", "login"}
GENERIC_MODIFIERS = {"best", "top", "cheap", "affordable", "good", "near", "near me"}

PAGE_BLUEPRINTS: Dict[str, Dict[str, object]] = {
    "india_commercial": {"min_words": 900, "min_internal_links": 5, "min_local_blocks": 1},
    "state_hub": {"min_words": 650, "min_internal_links": 8, "min_local_blocks": 2},
    "city_commercial": {"min_words": 1200, "min_internal_links": 8, "min_local_blocks": 4},
    "locality": {"min_words": 900, "min_internal_links": 6, "min_local_blocks": 4},
    "module": {"min_words": 800, "min_internal_links": 6, "min_local_blocks": 1},
    "module_city": {"min_words": 1100, "min_internal_links": 7, "min_local_blocks": 3},
    "board_city": {"min_words": 1100, "min_internal_links": 7, "min_local_blocks": 3},
    "comparison": {"min_words": 1200, "min_internal_links": 6, "min_local_blocks": 1},
    "pricing": {"min_words": 900, "min_internal_links": 6, "min_local_blocks": 1},
    "demo": {"min_words": 700, "min_internal_links": 5, "min_local_blocks": 1},
    "hindi": {"min_words": 700, "min_internal_links": 5, "min_local_blocks": 2},
    "blog": {"min_words": 900, "min_internal_links": 5, "min_local_blocks": 1},
    "faq_voice": {"min_words": 700, "min_internal_links": 4, "min_local_blocks": 2},
}

KEYWORD_BUCKETS = {
    "primary_commercial": ["school erp software india", "school management software india", "best school erp india"],
    "local_commercial": ["school erp bihar", "school erp patna", "school management software patna"],
    "pricing_intent": ["school erp pricing india", "school management software cost india"],
    "board_intent": ["cbse school erp patna"],
    "module_intent": ["school fee management software patna", "school attendance software patna", "school report card software patna"],
    "comparison_intent": ["tachy vs entab", "tachy vs fedena", "tachy vs vidyalaya"],
    "hindi_regional_intent": ["पटना स्कूल ईआरपी सॉफ्टवेयर", "बिहार स्कूल मैनेजमेंट सॉफ्टवेयर"],
    "voice_search_intent": ["what is the best school erp software in patna", "is there school erp software near me"],
    "demo_cta_intent": ["free school erp demo india"],
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value).strip()
    return value


def slugify_safe(value: str) -> str:
    normalized = normalize_text(value).lower()
    normalized = re.sub(r"[^a-z0-9\s-]", " ", normalized)
    normalized = re.sub(r"\s+", "-", normalized).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    return normalized


def sanitize_slug(value: str, blocked_words=None) -> str:
    blocked_words = blocked_words or BLOCKED_LOCATION_TERMS
    slug = slugify_safe(value)
    parts = [p for p in slug.split("-") if p and p not in blocked_words]
    return "-".join(parts)


def validate_location_name(name: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    raw = normalize_text(name)
    lower = raw.lower()
    if len(raw) < 3:
        reasons.append("too_short")
    if re.fullmatch(r"\d+", lower):
        reasons.append("numeric_only")
    if lower in BLOCKED_LOCATION_TERMS:
        reasons.append("blocked_term")
    if any(tok in lower for tok in SUSPICIOUS_TOKENS):
        reasons.append("suspicious_token")
    if lower in GENERIC_MODIFIERS:
        reasons.append("generic_modifier")
    if sum(ch.isalpha() for ch in raw) < 2:
        reasons.append("malformed_place")
    if len(lower.split()) > 5:
        reasons.append("too_many_terms")
    return (len(reasons) == 0), reasons


def validate_location_row(city: str, state: str, country: str, existing_slugs=None) -> Dict[str, object]:
    existing_slugs = existing_slugs or set()
    city_ok, city_reasons = validate_location_name(city)
    state_ok, state_reasons = validate_location_name(state)
    clean_city = normalize_text(city).title()
    clean_state = normalize_text(state).title()
    clean_country = normalize_text(country or "India").title() or "India"
    base_slug = sanitize_slug(clean_city)
    is_intl = clean_country.lower() not in {"india", "bharat", "भारत"}
    if not base_slug:
        city_ok = False
        city_reasons.append("empty_slug")
    suffix = "-indian-school-erp" if is_intl else "-school-erp"
    slug = f"{base_slug}{suffix}"
    if slug in existing_slugs:
        city_ok = False
        city_reasons.append("duplicate_slug")
    review_state = "publish_ready"
    if not city_ok or not state_ok:
        review_state = "blocked_invalid"
    elif clean_city.lower() in {"new area", "phase 1", "zone"}:
        review_state = "manual_review"
        city_reasons.append("low_confidence_location")
    return {
        "city": clean_city,
        "state": clean_state,
        "country": clean_country,
        "slug": slug,
        "is_international": 1 if is_intl else 0,
        "review_state": review_state,
        "reasons": sorted(set(city_reasons + state_reasons)),
    }


def extract_visible_text(html_doc: str) -> str:
    txt = re.sub(r"<script[\s\S]*?</script>", " ", html_doc, flags=re.I)
    txt = re.sub(r"<style[\s\S]*?</style>", " ", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip().lower()
    return txt


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shingles(text: str, size: int = 4) -> set:
    words = text.split()
    if len(words) < size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i:i+size]) for i in range(len(words)-size+1)}


def similarity_score(a: str, b: str) -> float:
    a_set = shingles(a)
    b_set = shingles(b)
    if not a_set or not b_set:
        return 0.0
    return len(a_set & b_set) / max(1, len(a_set | b_set))


def detect_thin_content(word_count: int, min_words: int) -> bool:
    return word_count < min_words


def parse_schema_blocks(html_doc: str) -> Tuple[bool, List[str]]:
    errors = []
    blocks = re.findall(r'<script[^>]+application/ld\+json[^>]*>([\s\S]*?)</script>', html_doc, flags=re.I)
    if not blocks:
        return False, ["schema_missing"]
    for idx, block in enumerate(blocks, start=1):
        try:
            json.loads(block.strip())
        except Exception as exc:  # defensive
            errors.append(f"schema_block_{idx}_invalid:{exc}")
    return len(errors) == 0, errors


@dataclass
class QualityGateResult:
    quality_score: int
    publish_status: str
    reason_codes: List[str]
    similarity_score: float
    content_hash: str
    thin_content: int
    schema_status: str
    image_status: str


def run_quality_gate(db_path: str, html_doc: str, slug: str, page_type: str, location_valid: bool, review_state: str) -> QualityGateResult:
    blueprint = PAGE_BLUEPRINTS.get(page_type, PAGE_BLUEPRINTS["city_commercial"])
    text = extract_visible_text(html_doc)
    words = len(text.split())
    content_hash = text_fingerprint(text)
    schema_ok, schema_errors = parse_schema_blocks(html_doc)
    similarity = 0.0

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT visible_text FROM page_qc WHERE slug != ? ORDER BY id DESC LIMIT 250", (slug,)).fetchall()
    conn.close()
    for (prev_text,) in rows:
        if prev_text:
            similarity = max(similarity, similarity_score(text, prev_text))

    reason_codes = []
    score = 100
    thin = int(detect_thin_content(words, int(blueprint["min_words"])))
    if not location_valid or review_state == "blocked_invalid":
        score -= 25
        reason_codes.append("invalid_location")
    if thin:
        score -= 20
        reason_codes.append("thin_content")
    if similarity > 0.78:
        score -= 20
        reason_codes.append("high_similarity")
    if not schema_ok:
        score -= 10
        reason_codes.extend(schema_errors)
    if "<h1" not in html_doc.lower() or "<h2" not in html_doc.lower() or "<title>" not in html_doc.lower():
        score -= 8
        reason_codes.append("heading_structure_incomplete")
    link_count = len(re.findall(r"<a\s+", html_doc.lower()))
    if link_count < int(blueprint["min_internal_links"]):
        score -= 7
        reason_codes.append("internal_links_low")
    local_hits = len(re.findall(r"\b(city|state|bihar|patna|district|service area|local)\b", text))
    if local_hits < int(blueprint["min_local_blocks"]):
        score -= 5
        reason_codes.append("local_context_low")

    image_status = "passed"
    for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_doc, flags=re.I):
        if src.startswith("http"):
            continue
        test_path = src.lstrip("/")
        if test_path and not os.path.exists(test_path) and "assets/" not in test_path:
            image_status = "fallback_used"
            reason_codes.append(f"missing_image:{src}")
            score -= 3

    publish_status = "publish_ready"
    if review_state == "manual_review":
        publish_status = "manual_review"
    if reason_codes or score < 75:
        publish_status = "manual_review" if publish_status != "blocked_invalid" else publish_status
    if review_state == "blocked_invalid":
        publish_status = "blocked_invalid"

    if score < 55:
        publish_status = "blocked_invalid"

    return QualityGateResult(
        quality_score=max(0, min(100, score)),
        publish_status=publish_status,
        reason_codes=sorted(set(reason_codes)),
        similarity_score=round(similarity, 4),
        content_hash=content_hash,
        thin_content=thin,
        schema_status="valid" if schema_ok else "invalid",
        image_status=image_status,
    )


def apply_noindex_if_needed(html_doc: str, publish_status: str) -> str:
    if publish_status == "publish_ready":
        return html_doc
    if 'name="robots"' in html_doc.lower():
        return re.sub(r'<meta\s+name=["\']robots["\'][^>]*>', '<meta name="robots" content="noindex,nofollow"/>', html_doc, flags=re.I)
    return html_doc.replace("</head>", "  <meta name=\"robots\" content=\"noindex,nofollow\"/>\n</head>")


def proof_mode_context(db_path: str, city: str, state: str, freshness_days: int = 180) -> Dict[str, object]:
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        """
        SELECT platform_name, rating, review_count, source_url, verification_date
        FROM proof_sources
        WHERE is_verified = 1 AND (city = ? OR city IS NULL) AND (state = ? OR state IS NULL)
        ORDER BY verification_date DESC LIMIT 1
        """,
        (city, state),
    ).fetchone()
    testimonials = conn.execute(
        """
        SELECT person_name, role, school_name, quote, source_url, verification_date
        FROM testimonials
        WHERE is_verified = 1 AND (city = ? OR city IS NULL) AND (state = ? OR state IS NULL)
        ORDER BY verification_date DESC LIMIT 3
        """,
        (city, state),
    ).fetchall()
    conn.close()

    if not row:
        return {"mode": "neutral", "aggregate_rating": None, "testimonials": []}

    platform_name, rating, review_count, source_url, verification_date = row
    stale = True
    try:
        stale = datetime.strptime(verification_date, "%Y-%m-%d") < (datetime.utcnow() - timedelta(days=freshness_days))
    except Exception:
        stale = True

    if stale:
        return {"mode": "neutral", "aggregate_rating": None, "testimonials": []}

    return {
        "mode": "verified",
        "aggregate_rating": {
            "platform_name": platform_name,
            "rating": rating,
            "review_count": review_count,
            "source_url": source_url,
            "verification_date": verification_date,
        },
        "testimonials": testimonials,
    }
