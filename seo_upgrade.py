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

SUPPORTED_SCHEMA_TYPES = {
    "Organization", "LocalBusiness", "SoftwareApplication", "FAQPage", "BreadcrumbList", "WebPage",
    "Product", "VideoObject", "HowTo", "Article", "CollectionPage", "Service",
}
OUTDATED_META_PATTERNS = [
    re.compile(r'<meta[^>]+name=["\']keywords["\'][^>]*>', re.I),
    re.compile(r'<meta[^>]+name=["\']revisit-after["\'][^>]*>', re.I),
    re.compile(r'<meta[^>]+name=["\']rating["\'][^>]*>', re.I),
]
CLAIM_RULES = {
    "risky_superlative_claim": [
        (re.compile(r"\b#\s*1\b", re.I), "leading"),
        (re.compile(r"\bbest\b", re.I), "trusted"),
        (re.compile(r"\bmost trusted\b", re.I), "widely used"),
    ],
    "unsupported_stat": [
        (re.compile(r"\b500\+\s*schools\b", re.I), "schools across India"),
        (re.compile(r"\b20\+\s*states\b", re.I), "multiple regions"),
        (re.compile(r"\b95%\+\b", re.I), "high engagement"),
        (re.compile(r"\bgo live in 3[–-]7 days\b", re.I), "go live based on setup"),
        (re.compile(r"\btrained in under 4 hours\b", re.I), "training is guided step-by-step"),
        (re.compile(r"\bsave 3[–-]5 hours daily\b", re.I), "save administration effort"),
    ],
}


@dataclass
class YouTubeData:
    video_id: str
    watch_url: str
    embed_url: str
    thumbnail_url: str


@dataclass
class PublishSafetyResult:
    publish_safety_status: str
    issue_codes: List[str]
    claim_status: str
    video_status: str
    business_entity_status: str
    testimonial_status: str
    outdated_meta_status: str
    schema_status: str
    rewritten_html: str


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


def _iter_schema_nodes(block_json):
    if isinstance(block_json, dict):
        if "@graph" in block_json and isinstance(block_json["@graph"], list):
            for node in block_json["@graph"]:
                if isinstance(node, dict):
                    yield node
        else:
            yield block_json
    elif isinstance(block_json, list):
        for item in block_json:
            if isinstance(item, dict):
                yield item


def validate_schema_semantics(html_doc: str, proof_mode: str = "neutral") -> Tuple[bool, List[str]]:
    errors: List[str] = []
    seen_ids = set()
    blocks = re.findall(r'<script[^>]+application/ld\+json[^>]*>([\s\S]*?)</script>', html_doc, flags=re.I)
    if not blocks:
        return False, ["schema_missing"]
    for idx, block in enumerate(blocks, start=1):
        try:
            parsed = json.loads(block.strip())
        except Exception as exc:
            errors.append(f"schema_json_invalid_{idx}:{exc}")
            continue
        for node in _iter_schema_nodes(parsed):
            node_type = node.get("@type")
            node_id = node.get("@id")
            if node_id:
                if node_id in seen_ids:
                    errors.append("duplicate_schema_id")
                seen_ids.add(node_id)
            if node_type and node_type not in SUPPORTED_SCHEMA_TYPES:
                errors.append(f"unsupported_schema_type:{node_type}")
            for key in ("url", "contentUrl", "embedUrl"):
                if key in node and not str(node.get(key, "")).startswith(("http://", "https://")):
                    errors.append(f"invalid_url:{key}")
            for date_key in ("datePublished", "dateModified", "uploadDate"):
                if date_key in node and not re.match(r"^\d{4}-\d{2}-\d{2}", str(node.get(date_key, ""))):
                    errors.append(f"invalid_date:{date_key}")
            if node_type == "AggregateRating" and proof_mode != "verified":
                errors.append("aggregate_rating_without_verified_proof")
            if node_type == "VideoObject":
                if not node.get("embedUrl") or "youtube.com/embed/" not in str(node.get("embedUrl")):
                    errors.append("invalid_video_embed")
    return (len(errors) == 0), sorted(set(errors))


def parse_youtube_input(value: str) -> YouTubeData | None:
    raw = (value or "").strip()
    if not raw:
        return None
    patterns = [
        re.compile(r"^[A-Za-z0-9_-]{11}$"),
        re.compile(r"(?:v=|\/shorts\/|\/embed\/|youtu\.be\/)([A-Za-z0-9_-]{11})"),
    ]
    video_id = ""
    if patterns[0].match(raw):
        video_id = raw
    else:
        for pat in patterns[1:]:
            m = pat.search(raw)
            if m:
                video_id = m.group(1)
                break
    if not video_id:
        return None
    return YouTubeData(
        video_id=video_id,
        watch_url=f"https://www.youtube.com/watch?v={video_id}",
        embed_url=f"https://www.youtube.com/embed/{video_id}",
        thumbnail_url=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    )


def detect_outdated_meta(html_doc: str) -> List[str]:
    hits = []
    for pat in OUTDATED_META_PATTERNS:
        if pat.search(html_doc):
            hits.append("outdated_meta_tags")
    return sorted(set(hits))


def remove_outdated_meta(html_doc: str) -> str:
    updated = html_doc
    for pat in OUTDATED_META_PATTERNS:
        updated = pat.sub("", updated)
    return updated


def validate_testimonials(testimonials: list, freshness_days: int = 180) -> Tuple[bool, List[str]]:
    issues = []
    if not testimonials:
        return False, ["missing_verified_testimonial"]
    cutoff = datetime.utcnow() - timedelta(days=freshness_days)
    valid_count = 0
    for row in testimonials:
        quote = str(row[3]).strip() if len(row) > 3 else ""
        verification_date = str(row[5]).strip() if len(row) > 5 else ""
        if len(quote.split()) < 8:
            issues.append("testimonial_quote_too_short")
            continue
        try:
            if datetime.strptime(verification_date, "%Y-%m-%d") < cutoff:
                issues.append("stale_proof_data")
                continue
        except Exception:
            issues.append("testimonial_missing_verification_date")
            continue
        valid_count += 1
    if valid_count == 0:
        issues.append("unverified_testimonial")
    return valid_count > 0, sorted(set(issues))


def claim_policy_rewrite(html_doc: str, proof_mode: str = "neutral") -> Tuple[str, List[str], str]:
    issues: List[str] = []
    updated = html_doc
    if proof_mode == "verified":
        return updated, issues, "verified_numeric_claim"
    for group, patterns in CLAIM_RULES.items():
        for pat, replacement in patterns:
            if pat.search(updated):
                issues.append(group)
                updated = pat.sub(replacement, updated)
    if re.search(r"\b\d+(\.\d+)?\s*★", updated):
        updated = re.sub(r"\b\d+(\.\d+)?\s*★", "highly rated", updated)
        issues.append("unsupported_rating_claim")
    return updated, sorted(set(issues)), ("soft_marketing_claim" if not issues else "unsupported_stat")


def evaluate_business_entity_mode(html_doc: str, city: str, config: Dict[str, str]) -> Tuple[str, List[str]]:
    has_local = "localbusiness" in html_doc.lower()
    has_office_flag = str(config.get("has_physical_office_in_city", "0")) == "1"
    service_area_mode = str(config.get("use_service_area_business_mode", "1")) == "1"
    primary_city = str(config.get("primary_business_city", "")).strip().lower()
    issues = []
    if has_local and not has_office_flag and city.strip().lower() != primary_city and not service_area_mode:
        issues.append("misleading_localbusiness")
        return "manual_review", issues
    return "safe", issues


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


def run_publish_safety_validator(
    html_doc: str,
    city: str,
    config: Dict[str, str],
    proof_mode: str,
    testimonials: list,
) -> PublishSafetyResult:
    working_html = html_doc
    issues: List[str] = []

    # Claim governance + rewrite
    rewritten_html, claim_issues, claim_status = claim_policy_rewrite(working_html, proof_mode=proof_mode)
    working_html = rewritten_html
    issues.extend(claim_issues)

    # Video safety
    video_status = "not_present"
    if "videoobject" in working_html.lower():
        parsed_video = parse_youtube_input(config.get("demo_video_id", ""))
        if not parsed_video:
            video_status = "invalid"
            issues.append("invalid_video_url")
            working_html = re.sub(r'<script[^>]+application/ld\+json[^>]*>[\s\S]*?VideoObject[\s\S]*?</script>', "", working_html, flags=re.I)
        else:
            video_status = "valid"
            working_html = re.sub(r"https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]{11}", parsed_video.watch_url, working_html)
            working_html = re.sub(r"https?://(?:www\.)?youtube\.com/embed/[A-Za-z0-9_-]{11}", parsed_video.embed_url, working_html)
            working_html = re.sub(r"https?://i\.ytimg\.com/vi/[A-Za-z0-9_-]{11}/hqdefault\.jpg", parsed_video.thumbnail_url, working_html)

    # Testimonials
    testimonial_ok, testimonial_issues = validate_testimonials(testimonials, freshness_days=int(config.get("proof_freshness_days", "180") or "180"))
    testimonial_status = "verified" if testimonial_ok else "fallback"
    issues.extend(testimonial_issues)
    if not testimonial_ok:
        issues.append("unverified_testimonial")
        # Remove fabricated review schema blocks
        working_html = re.sub(r'<script[^>]+application/ld\+json[^>]*>[\s\S]*?AggregateRating[\s\S]*?</script>', "", working_html, flags=re.I)

    # Outdated meta
    outdated_meta_issues = detect_outdated_meta(working_html)
    outdated_meta_status = "clean"
    if outdated_meta_issues and str(config.get("enable_legacy_meta_tags", "0")) != "1":
        working_html = remove_outdated_meta(working_html)
        outdated_meta_status = "removed"
        issues.extend(outdated_meta_issues)

    # Business entity safety
    business_status, business_issues = evaluate_business_entity_mode(working_html, city, config)
    issues.extend(business_issues)

    # Schema semantics
    schema_ok, schema_errors = validate_schema_semantics(working_html, proof_mode=proof_mode)
    schema_status = "valid" if schema_ok else "invalid"
    issues.extend(schema_errors)

    publish_safety_status = "safe"
    if issues or schema_status == "invalid" or business_status != "safe":
        publish_safety_status = "manual_review"
        working_html = apply_noindex_if_needed(working_html, "manual_review")

    return PublishSafetyResult(
        publish_safety_status=publish_safety_status,
        issue_codes=sorted(set(issues)),
        claim_status=claim_status,
        video_status=video_status,
        business_entity_status=business_status,
        testimonial_status=testimonial_status,
        outdated_meta_status=outdated_meta_status,
        schema_status=schema_status,
        rewritten_html=working_html,
    )


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
