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
    client_context: Dict[str, object] | None = None,
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

    # Client domain safety checks
    if client_context:
        school_specificity = int(client_context.get("school_specificity_score", 0) or 0)
        if school_specificity < 55:
            issues.append("school_specificity_low")
        anchors = client_context.get("anchors", [])
        tachy_links = int(client_context.get("tachy_link_count", 0) or 0)
        if tachy_links > 2:
            issues.append("client_tachy_link_overcount")
            issues.append("backlink_intent_too_obvious")
        seen = set()
        for a in anchors:
            clean = str(a).strip().lower()
            if clean in seen:
                issues.append("exact_match_anchor_overuse")
            seen.add(clean)
            ok, reason = validate_client_anchor(clean)
            if not ok:
                issues.append("backlink_intent_too_obvious")
                issues.append(reason)
        if "powered by tachy school erp" in working_html.lower() and "rel=" not in working_html.lower():
            issues.append("powered_by_rel_missing")
        cross_domain_similarity = float(client_context.get("cross_domain_similarity", 0) or 0)
        if cross_domain_similarity > 0.75:
            issues.append("cross_domain_similarity_high")
        canonical_mode = str(client_context.get("canonical_mode", ""))
        if canonical_mode == "canonical_to_tachy" and "tachy.in" not in working_html.lower():
            issues.append("canonical_decision_inconsistent")

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


def calculate_school_specificity_score(page_html: str, school_profile: Dict[str, object]) -> int:
    score = 100
    text = extract_visible_text(page_html)
    school_name = str(school_profile.get("school_name", "")).strip().lower()
    city = str(school_profile.get("city", "")).strip().lower()
    modules = [str(m).lower() for m in school_profile.get("modules_used", [])]
    go_live = str(school_profile.get("go_live_date", "")).strip()
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page_html, flags=re.I | re.S)
    h1_text = h1.group(1).lower() if h1 else ""
    if school_name and school_name not in h1_text:
        score -= 20
    if city and text.count(city) < 1:
        score -= 10
    if modules and not any(m.replace("_", " ") in text for m in modules):
        score -= 10
    if go_live and go_live not in text:
        score -= 10
    generic_markers = ["best school erp software india", "school erp software in india", "tachy school erp is india"]
    if any(m in text for m in generic_markers):
        score -= 30
    return max(0, min(100, score))


ALLOWED_CLIENT_ANCHORS = {
    "tachy school erp",
    "powered by tachy school erp",
    "school erp platform by tachy",
    "learn more about tachy school erp",
    "our school erp platform",
    "school management platform",
}
BLOCKED_CLIENT_ANCHORS = {
    "best school erp software",
    "school erp india",
    "school management software",
    "top school erp",
}


def validate_client_anchor(anchor_text: str) -> Tuple[bool, str]:
    a = (anchor_text or "").strip().lower()
    if a in BLOCKED_CLIENT_ANCHORS:
        return False, "blocked_exact_match_commercial_anchor"
    if a not in ALLOWED_CLIENT_ANCHORS:
        return False, "anchor_not_in_allowlist"
    return True, "ok"


def compare_with_tachy_pages(client_html: str, tachy_pages_dir: str) -> float:
    client_text = extract_visible_text(client_html)
    max_sim = 0.0
    if not tachy_pages_dir or not os.path.isdir(tachy_pages_dir):
        return 0.0
    for fn in os.listdir(tachy_pages_dir):
        if not fn.endswith(".html"):
            continue
        try:
            with open(os.path.join(tachy_pages_dir, fn), "r", encoding="utf-8") as fh:
                max_sim = max(max_sim, similarity_score(client_text, extract_visible_text(fh.read())))
        except Exception:
            continue
    return round(max_sim, 4)


def compare_with_other_client_pages(client_html: str, db_path: str) -> float:
    client_text = extract_visible_text(client_html)
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT visible_text FROM client_pages WHERE visible_text IS NOT NULL ORDER BY id DESC LIMIT 500").fetchall()
    conn.close()
    mx = 0.0
    for (txt,) in rows:
        mx = max(mx, similarity_score(client_text, txt or ""))
    return round(mx, 4)


def auto_select_output_mode(page_type: str, similarity_score_value: float, school_specificity_score: int, proof_status: str) -> str:
    if page_type.startswith("tachy_"):
        return page_type
    if school_specificity_score < 50:
        return "client_noindex_support"
    if similarity_score_value > 0.75:
        return "client_canonicalized"
    if page_type == "case_study" and proof_status != "verified":
        return "client_noindex_support"
    if page_type == "case_study":
        return "client_case_study"
    if page_type == "erp_announcement":
        return "client_announcement"
    return "client_indexed"


def _client_base_html(title: str, body: str, canonical: str, robots: str, schema_json: str, hreflang: str = "") -> str:
    return f"""<!doctype html>
<html lang=\"en-IN\"><head>
<meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>
<title>{title}</title>
<meta name=\"description\" content=\"{title}\"/>
<meta name=\"robots\" content=\"{robots}\"/>
<link rel=\"canonical\" href=\"{canonical}\"/>{hreflang}
<script type=\"application/ld+json\">{schema_json}</script>
</head><body>{body}</body></html>"""


def generate_client_page(page_type: str, school_profile: Dict[str, object], config: Dict[str, str], proof_status: str = "neutral") -> Dict[str, object]:
    school = school_profile["school_name"]
    city = school_profile["city"]
    state = school_profile["state"]
    domain = school_profile["school_domain"].rstrip("/")
    slug = sanitize_slug(f"{school}-{page_type}")
    canonical = f"https://{domain}/{slug}.html"
    modules = ", ".join(school_profile.get("modules_used", [])) or "fees, attendance, report cards"
    go_live = school_profile.get("go_live_date", "")
    link_anchor = "TACHY School ERP"
    _ok, _reason = validate_client_anchor(link_anchor)
    tlink = f'<a href="https://tachy.in" rel="nofollow">{link_anchor}</a>'
    title_map = {
        "our_erp_page": f"{school} Uses TACHY School ERP",
        "parent_help_center": f"Parent Help Center — {school}",
        "fee_payment_guide": f"How to Pay School Fees Online — {school}",
        "attendance_guide": f"How to Check Student Attendance — {school}",
        "report_card_guide": f"How to Access Report Cards Online — {school}",
        "erp_announcement": f"{school} Goes Digital with TACHY School ERP",
        "digital_transformation_story": f"How {school} Digitized School Management",
        "case_study": f"{school} ERP Case Study",
        "school_faq": f"Frequently Asked Questions — {school} Digital Platform",
        "app_download_guide": f"Download the {school} School App",
    }
    title = title_map.get(page_type, f"{school} Digital Platform")
    body = f"<h1>{title}</h1><p>{school} in {city}, {state} uses a digital workflow for {modules}. Powered support: {tlink}</p>"
    if go_live:
        body += f"<p>Go-live date: {go_live}.</p>"
    if page_type == "parent_help_center":
        body += "<h2>Login Guide</h2><p>Use school-issued credentials to login.</p><h2>Fee Payments</h2><p>Pay online securely.</p>"
    if page_type == "case_study" and proof_status != "verified":
        body += "<p>Results vary by school size and deployment scope.</p>"
    schema = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": canonical})
    html = _client_base_html(title, body, canonical, "index,follow", schema)
    specificity = calculate_school_specificity_score(html, school_profile)
    decision_mode = auto_select_output_mode(page_type, 0.0, specificity, proof_status)
    if decision_mode == "client_noindex_support":
        html = html.replace("index,follow", "noindex,nofollow")
    return {"slug": slug, "html": html, "school_specificity_score": specificity, "output_mode": decision_mode, "canonical": canonical}


def generate_board_city_page(board: str, city: str, state: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"{board}-school-erp-{city}")
    title = f"{board} School ERP in {city}"
    body = f"<h1>{title}</h1><h2>{board} grading workflows</h2><p>Board-specific report cards for {city}, {state} schools.</p>"
    schema = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[]})
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema)
    return {"slug": slug, "html": html}


def generate_locality_page(locality: str, city: str, state: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"school-erp-{locality}-{city}")
    title = f"School ERP {locality} {city}"
    body = f"<h1>{title}</h1><p>Locality-focused service context for {locality}, {city}, {state}.</p>"
    schema = json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title})
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema)
    return {"slug": slug, "html": html}


def generate_module_city_page(module: str, city: str, state: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"school-{module}-software-{city}")
    title = f"School {module.title()} Software in {city}"
    body = f"<h1>{title}</h1><p>{module.title()} workflows for schools in {city}, {state}.</p>"
    schema = json.dumps({"@context":"https://schema.org","@type":"WebPage","name":title})
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema)
    return {"slug": slug, "html": html}


def generate_voice_faq_page(city: str, state: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"faq-school-erp-{city}")
    title = f"FAQ School ERP {city}"
    body = f"<h1>{title}</h1><h2>What is school ERP software in {city}?</h2><p>It helps manage fees, attendance, and communication.</p>"
    schema = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":f"What is school ERP software in {city}?","acceptedAnswer":{"@type":"Answer","text":"A digital school operations platform."}}]})
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema)
    return {"slug": slug, "html": html}


def generate_comparison_page(competitor: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"tachy-vs-{competitor}")
    title = f"TACHY vs {competitor.title()}"
    body = f"<h1>{title}</h1><table><tr><th>Criteria</th><th>TACHY</th><th>{competitor.title()}</th></tr><tr><td>Implementation</td><td>Guided rollout</td><td>Varies by plan</td></tr></table>"
    schema = json.dumps({"@context":"https://schema.org","@type":"Article","headline":title})
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema)
    return {"slug": slug, "html": html}


def generate_hindi_city_page(city: str, state: str, website: str) -> Dict[str, str]:
    slug = sanitize_slug(f"{city}-school-erp-hindi")
    title = f"TACHY स्कूल ERP सॉफ्टवेयर — {city}, {state}"
    body = f"<h1>{title}</h1><p>{city} के स्कूलों के लिए फीस, उपस्थिति और रिपोर्ट कार्ड प्रबंधन का डिजिटल समाधान।</p>"
    base = website.rstrip("/")
    hreflang = f'<link rel="alternate" hreflang="en-IN" href="{base}/{sanitize_slug(city)}-school-erp.html"/><link rel="alternate" hreflang="hi" href="{base}/{slug}.html"/>'
    schema = json.dumps({"@context":"https://schema.org","@type":"WebPage","inLanguage":"hi-IN","name":title}, ensure_ascii=False)
    html = _client_base_html(title, body, f"{website.rstrip('/')}/{slug}.html", "index,follow", schema, hreflang=hreflang)
    return {"slug": slug, "html": html}


def generate_gbp_posts(city: str, state: str, website: str, count: int = 10) -> List[Dict[str, str]]:
    base = f"{website.rstrip('/')}/school-erp-{sanitize_slug(city)}.html?utm_source=gbp&utm_medium=post&utm_campaign={sanitize_slug(city)}"
    templates = [
        "Schools in {city} are simplifying operations with digital ERP workflows. Explore demo options: {url}",
        "Feature spotlight for {city} schools: fee reminders, attendance visibility, and parent communication. {url}",
        "FAQ for {city} parents: how digital fee receipts and attendance updates work. {url}",
        "Book a guided ERP demo for {city}, {state} schools. {url}",
        "State-ready workflows for {state} boards and school admins in {city}. {url}",
    ]
    posts = []
    for i in range(count):
        txt = templates[i % len(templates)].format(city=city, state=state, url=base)
        posts.append({"post_type": f"type_{i%5+1}", "post_content": txt[:1500], "utm_url": base})
    return posts


def generate_wa_broadcasts(city: str, state: str, board: str, school_name: str = "{school_name}") -> List[Dict[str, str]]:
    variants = [
        f"Namaste Principal, {city} schools are adopting digital ERP for fees/attendance. Want a short demo for {school_name}?",
        f"Following up for {school_name}: we can share a {board}-ready ERP walkthrough tailored for {city}.",
        f"Demo confirmed: we’ll cover admissions, fees, attendance, and report cards for {school_name} in {state}.",
        f"For accountants at {school_name}: fee ledgers, reminders, and receipts can be automated safely.",
        f"For school management: ERP helps visibility across academics and operations, tailored for {city} schools.",
    ]
    roles = ["Principal", "Principal", "Management", "Accountant", "Trust"]
    return [{"target_role": roles[i], "message_text": v[:300], "char_count": len(v[:300])} for i, v in enumerate(variants)]
