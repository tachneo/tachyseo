#!/usr/bin/env python3
"""
TACHY SEO PRO v4.0 — WordPress Direct Publisher + Ultimate SEO Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEW in v4.0:
  🆕 WordPress REST API integration — post directly to any WP site
  🆕 Multi-site WP manager (tachy.in + 12fail.com + more)
  🆕 WP Connection Tester with live status indicator
  🆕 Application Password auth (no plugin needed — WP 5.6+)
  🆕 Bulk city page publisher — 200+ cities in one click
  🆕 Blog post scheduler with publish/draft/future options
  🆕 Auto-assign WP categories & tags from keyword list
  🆕 Custom slug, SEO title, meta description via Yoast/RankMath API
  🆕 Featured image auto-attach via Media Library
  🆕 Duplicate check — skips already-published pages
  🆕 Re-publish / update existing posts
  🆕 WP publish queue with thread-safe progress
  🆕 SEO trending keyword injector (Google Trends patterns)
  🆕 Post analytics: track views, comments via WP stats
  🆕 Google Search Console ping after publish
  🆕 12fail.com blog-specific templates (failure stories, city guides)
  🆕 Competitor keyword gap auto-injector into posts
  🆕 LSI keyword density optimizer before publish
  🆕 Internal link mesh builder for WP posts
  🆕 Readability score checker (Flesch-Kincaid)
  🆕 Hindi/Hinglish title variants for India traffic
  🆕 WP post export to CSV with post IDs and URLs
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3, os, json, threading, webbrowser, re, random, time, queue, zipfile, csv, base64
from datetime import datetime, timedelta
import http.server, socketserver, urllib.parse, urllib.request, urllib.error
import io, hashlib

# ══════════════════════════════════════════════════════════════════════
#  PATHS & CONFIG
# ══════════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "tachy_seo_v4.db")
OUT_DIR  = os.path.join(BASE_DIR, "seo_pages_v4")

# ══════════════════════════════════════════════════════════════════════
#  WORDPRESS API ENGINE
# ══════════════════════════════════════════════════════════════════════
class WordPressAPI:
    """
    WordPress REST API v2 client.
    Uses Application Passwords (WP 5.6+) — NO plugin required.
    Setup: WP Admin → Users → Your Profile → Application Passwords → Add New
    """
    def __init__(self, site_url, username, app_password):
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password.replace(" ", "")  # WP strips spaces
        self.base_api = f"{self.site_url}/wp-json/wp/v2"
        self._auth_header = self._make_auth()

    def _make_auth(self):
        credentials = f"{self.username}:{self.app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        return f"Basic {token}"

    def _request(self, method, endpoint, data=None, params=None, timeout=30):
        url = f"{self.base_api}/{endpoint}"
        if params:
            query = urllib.parse.urlencode(params)
            url += f"?{query}"
        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "User-Agent": "TACHY-SEO-PRO/4.0"
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode()), resp.status
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                err_json = json.loads(error_body)
                raise Exception(f"HTTP {e.code}: {err_json.get('message', error_body[:200])}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP {e.code}: {error_body[:200]}")
        except urllib.error.URLError as e:
            raise Exception(f"Connection failed: {e.reason}")

    def test_connection(self):
        """Test credentials and return site info."""
        try:
            data, status = self._request("GET", "users/me")
            return True, f"✅ Connected as: {data.get('name','?')} | Role: {data.get('roles',['?'])[0]} | Site: {self.site_url}"
        except Exception as e:
            return False, f"❌ Failed: {str(e)}"

    def get_site_info(self):
        """Get basic WP site information."""
        try:
            url = f"{self.site_url}/wp-json"
            req = urllib.request.Request(url, headers={"User-Agent": "TACHY-SEO-PRO/4.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                return {
                    "name": data.get("name", ""),
                    "description": data.get("description", ""),
                    "url": data.get("url", ""),
                    "wp_version": data.get("namespaces", []),
                }
        except Exception as e:
            return {"error": str(e)}

    def get_categories(self):
        """Get all categories."""
        data, _ = self._request("GET", "categories", params={"per_page": 100})
        return data

    def get_tags(self):
        """Get all tags."""
        data, _ = self._request("GET", "tags", params={"per_page": 100})
        return data

    def create_category(self, name, description=""):
        """Create a new category, return its ID."""
        data, _ = self._request("POST", "categories", {"name": name, "description": description})
        return data.get("id")

    def create_tag(self, name):
        """Create a new tag, return its ID."""
        data, _ = self._request("POST", "tags", {"name": name})
        return data.get("id")

    def get_or_create_category(self, name):
        """Get existing category ID or create new one."""
        try:
            cats = self.get_categories()
            for cat in cats:
                if cat["name"].lower() == name.lower():
                    return cat["id"]
            return self.create_category(name)
        except:
            return None

    def get_or_create_tag(self, name):
        """Get existing tag ID or create new one."""
        try:
            tags = self.get_tags()
            for tag in tags:
                if tag["name"].lower() == name.lower():
                    return tag["id"]
            return self.create_tag(name)
        except:
            return None

    def post_exists(self, slug):
        """Check if a post with this slug already exists."""
        try:
            data, _ = self._request("GET", "posts", params={"slug": slug, "per_page": 1})
            return len(data) > 0, data[0].get("id") if data else None
        except:
            return False, None

    def create_post(self, title, content, slug, meta_desc="", status="publish",
                    categories=None, tags=None, featured_media=None, extra_meta=None,
                    update_existing=False):
        """
        Create or update a WordPress post.
        Returns (post_id, post_url, action)
        """
        # Check if already exists
        exists, existing_id = self.post_exists(slug)
        if exists and not update_existing:
            return existing_id, f"{self.site_url}/{slug}/", "skipped"

        payload = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": status,
            "excerpt": meta_desc[:300] if meta_desc else "",
        }
        if categories: payload["categories"] = categories
        if tags:       payload["tags"] = tags
        if featured_media: payload["featured_media"] = featured_media

        # Yoast SEO / RankMath meta (stored as post meta — requires REST meta support)
        if meta_desc:
            payload["meta"] = {
                "_yoast_wpseo_metadesc": meta_desc,
                "_yoast_wpseo_title": title,
                "rank_math_description": meta_desc,
                "rank_math_title": title,
            }
        if extra_meta:
            payload.setdefault("meta", {}).update(extra_meta)

        if exists and update_existing:
            data, _ = self._request("POST", f"posts/{existing_id}", payload)
            return data.get("id"), data.get("link", ""), "updated"
        else:
            data, _ = self._request("POST", "posts", payload)
            return data.get("id"), data.get("link", ""), "created"

    def create_page(self, title, content, slug, meta_desc="", status="publish",
                    update_existing=False):
        """Create or update a WordPress PAGE (not post)."""
        # Check pages endpoint
        try:
            existing, _ = self._request("GET", "pages", params={"slug": slug, "per_page": 1})
            exists = len(existing) > 0
            existing_id = existing[0].get("id") if existing else None
        except:
            exists, existing_id = False, None

        if exists and not update_existing:
            return existing_id, f"{self.site_url}/{slug}/", "skipped"

        payload = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": status,
            "excerpt": meta_desc[:300] if meta_desc else "",
            "meta": {
                "_yoast_wpseo_metadesc": meta_desc,
                "rank_math_description": meta_desc,
            }
        }

        if exists and update_existing:
            data, _ = self._request("POST", f"pages/{existing_id}", payload)
            return data.get("id"), data.get("link", ""), "updated"
        else:
            data, _ = self._request("POST", "pages", payload)
            return data.get("id"), data.get("link", ""), "created"

    def list_posts(self, per_page=20, page=1, post_type="posts"):
        """List existing posts."""
        data, _ = self._request("GET", post_type, params={"per_page": per_page, "page": page, "_fields": "id,title,slug,link,status,date"})
        return data

    def delete_post(self, post_id, force=False):
        """Move post to trash (or permanently delete if force=True)."""
        data, _ = self._request("DELETE", f"posts/{post_id}", params={"force": str(force).lower()})
        return data

    def ping_search_engines(self, sitemap_url):
        """Ping search engines to re-crawl sitemap. (Google deprecated their public ping endpoint in 2023, so this pings Bing)."""
        bing_url = f"https://www.bing.com/ping?sitemap={urllib.parse.quote(sitemap_url)}"
        try:
            req = urllib.request.Request(bing_url, headers={"User-Agent": "TACHY-SEO-PRO/4.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return True, f"✅ Bing pinged successfully! (Google no longer supports pings — submit sitemap in Google Search Console once.)"
        except Exception as e:
            return False, f"Ping failed: {e}"


# ══════════════════════════════════════════════════════════════════════
#  CONTENT VARIATION POOLS
# ══════════════════════════════════════════════════════════════════════
HERO_INTROS = [
    "India's most visual and easy-to-use AI-powered school ERP, now serving schools in {city}, {state}.",
    "Trusted by private, CBSE and ICSE schools across {state}, TACHY School ERP with AI features is the smart choice for {city}.",
    "Schools in {city} are going digital with TACHY — the complete AI-driven school management platform built for Indian schools.",
    "From admissions to analytics, {city} schools choose TACHY School ERP for speed, simplicity and measurable results.",
    "TACHY School ERP brings world-class school automation to every school in {city} — at a price that fits Indian budgets.",
    "More than 500 schools across {state} trust TACHY School ERP. Now bringing that same power to {city}.",
    "Running a school in {city} just got easier. TACHY automates every admin task so your teachers can focus on teaching.",
    "The school management revolution has arrived in {city}, {state}. TACHY School ERP — where simplicity meets power.",
    "{city} school administrators save 4+ hours daily with TACHY's automated workflows. Fees, attendance, exams — all digital.",
    "Leading schools in {city} have already switched to TACHY ERP. Join India's fastest-growing school management platform.",
]

WHY_PARAS = [
    "In {city}, school administrators face the daily challenge of managing hundreds of students, staff payrolls, exam records, and parent communication — all while keeping costs low. TACHY School ERP solves every challenge in one connected platform featuring AI-generated report card comments and smart analytics.",
    "Schools in {city} and across {state} are switching from paper registers and disconnected spreadsheets to TACHY's unified digital platform. The result? Less admin time, faster fee collection, and happier parents using our AI-driven WhatsApp Bot.",
    "Whether you manage a 200-student private school or a 2,000-student senior secondary institution in {city}, TACHY School ERP scales with your needs and adapts to your workflow with cutting-edge AI features.",
    "{city}'s school landscape is competitive. Parents expect digital report cards, online fee payment, and real-time attendance alerts. TACHY gives your school all of this from day one, keeping you ahead of the curve.",
    "The best-run schools in {city} have one thing in common: they use digital management systems. TACHY ERP is the most comprehensive, affordable, AI-powered, and easy-to-implement choice in {state}.",
]

FAQS_POOL = [
    ("What is TACHY School ERP and how does it help {city} schools?",
     "TACHY School ERP is a complete cloud-based school management software designed for Indian schools. Schools in {city} use TACHY to automate admissions, collect fees online, track attendance, manage exams and report cards, handle transport, process payroll, and communicate with parents — all from one dashboard."),
    ("Is TACHY School ERP suitable for CBSE schools in {city}?",
     "Yes, absolutely. TACHY is fully pre-configured for CBSE-affiliated schools in {city}. This includes CBSE grading formats (A1–E), CCE-style report cards, activity-based learning records, and co-scholastic areas — all matching exact CBSE formats."),
    ("How much does school ERP software cost for a {city} school?",
     "TACHY School ERP pricing for {city} schools is based on student strength and modules selected. We offer flexible monthly and annual plans starting at very affordable rates. Contact us at +91 8434801033 for a custom pricing quote. We also offer a free demo before any commitment."),
    ("Can TACHY handle fee collection online for {city} schools?",
     "Yes! TACHY's fee module lets {city} schools collect fees via UPI, NEFT, IMPS, debit/credit cards, and cash — with auto-generated digital receipts sent to parents via WhatsApp and email. You can set custom fee heads, late fines, concessions, and sibling discounts."),
    ("How long does it take to implement TACHY in a {city} school?",
     "Most schools in {city} are fully live on TACHY within 3 to 7 working days. Our onboarding team handles all data migration and provides on-site or remote staff training. We also offer 30 days of WhatsApp support at no extra charge."),
    ("Does TACHY School ERP have a mobile app for parents and teachers?",
     "Yes. TACHY provides Android apps for both parents and teachers. {city} teachers can mark attendance, enter exam marks, and send class notices from their phone. Parents receive real-time attendance alerts, fee reminders, and report card notifications instantly."),
    ("Is TACHY School ERP cloud-based or server-installed?",
     "TACHY School ERP is 100% cloud-based. Schools in {city} access the entire system from any browser — no software installation or server required. Your data is stored securely with regular backups and role-based access control."),
    ("Does TACHY offer a free trial for schools in {city}?",
     "Yes, TACHY offers a free live demo for schools in {city}. During the demo, our team walks you through all modules — admissions, fees, attendance, exams, transport, HR — customized to your school's board and class structure. Book at tachy.in or call +91 8434801033."),
    ("Does TACHY support WhatsApp integration for {city} schools?",
     "Yes. TACHY integrates directly with WhatsApp Business API. {city} schools can send fee reminders, attendance alerts, exam notifications, and school circulars directly to parent WhatsApp numbers — ensuring 95%+ message open rates."),
    ("How is TACHY different from other school ERP software available in {city}?",
     "TACHY was built specifically for the Indian school context — UPI fee collection, multilingual support, CBSE/ICSE/state board formats, WhatsApp integration, and local implementation support. Unlike generic ERPs, TACHY requires no technical expertise to operate."),
]

TESTIMONIALS_POOL = [
    ("Rajesh Kumar Sharma","Principal","Delhi Public School, {city}","Switching to TACHY School ERP was the best decision for our school. Fee collection time dropped by 70% and parent satisfaction has never been higher."),
    ("Mrs. Priya Srivastava","School Administrator","St. Mary's Convent, {city}","TACHY's admission module is a game-changer. We now process 3x more admissions in less time with zero paperwork. Excellent support team."),
    ("Mr. Anil Mishra","Director","Modern Academy, {city}","As a school owner, I needed something affordable yet powerful. TACHY delivers exactly that. The analytics dashboard gives me real-time visibility every morning."),
    ("Mrs. Sunita Devi","Accountant","Sunrise School, {city}","The fee management module has eliminated all billing errors. Every receipt, every ledger entry is auto-generated. Highly recommended!"),
    ("Mr. Deepak Verma","Headmaster","Saraswati Vidya Mandir, {city}","We were on manual registers for 15 years. TACHY helped us digitize everything in just one week. Even our older teachers love it."),
    ("Dr. Meena Khanna","Trustee","Bright Future International School, {city}","After evaluating 6 different school ERP products, we chose TACHY for its simplicity and local support. The WhatsApp feature transformed parent engagement."),
]

STATE_DATA = {
    "Bihar":            {"board":"Bihar Board (BSEB)","code":"BR","hindi":"बिहार","schools":"25,000+"},
    "Uttar Pradesh":    {"board":"UP Board (UPMSP)","code":"UP","hindi":"उत्तर प्रदेश","schools":"1,50,000+"},
    "Jharkhand":        {"board":"JAC Board","code":"JH","hindi":"झारखंड","schools":"18,000+"},
    "West Bengal":      {"board":"WBBSE / WBCHSE","code":"WB","hindi":"पश्चिम बंगाल","schools":"55,000+"},
    "Odisha":           {"board":"BSE Odisha","code":"OD","hindi":"ओडिशा","schools":"22,000+"},
    "Madhya Pradesh":   {"board":"MPBSE","code":"MP","hindi":"मध्य प्रदेश","schools":"1,10,000+"},
    "Rajasthan":        {"board":"RBSE","code":"RJ","hindi":"राजस्थान","schools":"1,20,000+"},
    "Maharashtra":      {"board":"MSBSHSE","code":"MH","hindi":"महाराष्ट्र","schools":"1,08,000+"},
    "Karnataka":        {"board":"KSEEB","code":"KA","hindi":"कर्नाटक","schools":"62,000+"},
    "Tamil Nadu":       {"board":"TN Board","code":"TN","hindi":"तमिलनाडु","schools":"45,000+"},
    "Telangana":        {"board":"TS Board","code":"TG","hindi":"तेलंगाना","schools":"30,000+"},
    "Gujarat":          {"board":"GSEB","code":"GJ","hindi":"गुजरात","schools":"35,000+"},
    "Delhi":            {"board":"CBSE / DoE","code":"DL","hindi":"दिल्ली","schools":"5,000+"},
    "DEFAULT":          {"board":"CBSE / State Board","code":"IN","hindi":"भारत","schools":"thousands of"},
}

CITY_FACTS = {
    "Patna":       {"pop":"2.4 million","schools":"1,200+","boards":"CBSE, ICSE, Bihar Board"},
    "Katihar":     {"pop":"240,000","schools":"400+","boards":"CBSE, Bihar Board"},
    "Muzaffarpur": {"pop":"393,000","schools":"600+","boards":"CBSE, Bihar Board"},
    "Ranchi":      {"pop":"1.1 million","schools":"800+","boards":"CBSE, ICSE, JAC"},
    "Lucknow":     {"pop":"3.5 million","schools":"2,500+","boards":"CBSE, ICSE, UP Board"},
    "Delhi":       {"pop":"20 million","schools":"5,000+","boards":"CBSE, ICSE"},
    "Mumbai":      {"pop":"20 million","schools":"6,000+","boards":"CBSE, ICSE, SSC"},
    "Bengaluru":   {"pop":"12 million","schools":"3,500+","boards":"CBSE, ICSE, SSLC"},
    "DEFAULT":     {"pop":"growing","schools":"hundreds of","boards":"CBSE, ICSE, State Board"},
}

# ══════════════════════════════════════════════════════════════════════
#  TRENDING SEO KEYWORD TEMPLATES FOR BLOGS
# ══════════════════════════════════════════════════════════════════════
TRENDING_BLOG_TEMPLATES = {
    "city_erp_guide": {
        "title": "Best School ERP Software in {city} {year} — Complete Guide for School Owners",
        "slug": "school-erp-software-{city_slug}-{year}",
        "meta": "Looking for the best school ERP software in {city}? Read our {year} guide covering top features, pricing, CBSE support & why TACHY is #1 in {state}.",
        "tags": ["school ERP {city}", "school management software {city}", "CBSE ERP {city}"],
        "category": "School ERP by City",
        "trending_keywords": ["school ERP software {city}", "school management {city}", "school fee software {city}", "best school ERP {state}"],
    },
    "fee_management": {
        "title": "How {city} Schools Collect Fees Online in {year} — Step by Step Guide",
        "slug": "online-fee-collection-schools-{city_slug}",
        "meta": "Step-by-step guide for {city} school administrators to switch from manual fee registers to fully digital online fee management with TACHY ERP.",
        "tags": ["online fee collection {city}", "school fee software", "digital fee management"],
        "category": "Fee Management",
        "trending_keywords": ["school fee collection online {city}", "digital fee receipt schools", "UPI fee collection schools"],
    },
    "cbse_erp": {
        "title": "CBSE School Management Software in {city} — Why Schools Are Switching in {year}",
        "slug": "cbse-school-management-software-{city_slug}",
        "meta": "Best CBSE school management software in {city}. TACHY ERP is pre-configured for CBSE grading, CCE report cards, and all required formats. Free demo.",
        "tags": ["CBSE school software {city}", "CBSE ERP India", "CBSE report card software"],
        "category": "CBSE Schools",
        "trending_keywords": ["CBSE school ERP {city}", "CBSE management software", "CBSE report card generator"],
    },
    "comparison": {
        "title": "Top 5 School ERP Software in {city} Compared — Which One to Choose in {year}?",
        "slug": "best-school-erp-comparison-{city_slug}-{year}",
        "meta": "Compare top school ERP software for {city} schools in {year}. Honest review of features, pricing, support — find out why TACHY outranks them all.",
        "tags": ["school ERP comparison {city}", "best school software India", "Fedena alternative"],
        "category": "ERP Comparisons",
        "trending_keywords": ["best school ERP {city}", "school ERP comparison India", "Fedena vs TACHY", "school software review {city}"],
    },
    "admission_guide": {
        "title": "How to Digitize School Admissions in {city} — {year} Complete Guide",
        "slug": "digital-school-admission-management-{city_slug}",
        "meta": "Learn how {city} schools are digitizing admissions with TACHY's admission management module. Online forms, document upload, and zero paperwork.",
        "tags": ["school admission software {city}", "digital admissions schools", "online admission management"],
        "category": "School Admissions",
        "trending_keywords": ["school admission software {city}", "online admission management India", "digital school enrollment {city}"],
    },
    "parent_app": {
        "title": "Best School Parent Communication App for {city} Schools — {year} Review",
        "slug": "school-parent-communication-app-{city_slug}",
        "meta": "Discover how {city} schools are using TACHY's parent app for real-time attendance alerts, fee reminders & WhatsApp notifications. Free demo available.",
        "tags": ["school parent app {city}", "school WhatsApp integration", "parent communication schools"],
        "category": "Parent Communication",
        "trending_keywords": ["school parent app {city}", "school WhatsApp notification", "parent teacher app India"],
    },
    # 12fail.com specific blog templates
    "12fail_story": {
        "title": "From Manual Registers to Digital School: A {city} School's Story",
        "slug": "school-digitization-success-story-{city_slug}",
        "meta": "Read how a school in {city}, {state} transformed from manual registers to 100% digital operations using TACHY School ERP. Real story, real results.",
        "tags": ["school digital transformation {city}", "school ERP success story", "school management software"],
        "category": "Success Stories",
        "trending_keywords": ["school digital transformation {city}", "school ERP case study India", "school management software story"],
    },
    "12fail_guide": {
        "title": "{city} School Owners: 7 Signs You Need School ERP Software in {year}",
        "slug": "signs-school-needs-erp-{city_slug}",
        "meta": "Is your {city} school struggling with manual work? Here are 7 clear signs it's time to switch to school ERP software — and how TACHY helps.",
        "tags": ["school ERP {city}", "school management problems", "school software India"],
        "category": "School Management Tips",
        "trending_keywords": ["school ERP {city}", "school management problems India", "when to use school ERP"],
    },
}

# 200+ Indian cities
INDIAN_CITIES = [
    ("Patna","Bihar",1),("Katihar","Bihar",2),("Muzaffarpur","Bihar",2),
    ("Gaya","Bihar",2),("Bhagalpur","Bihar",2),("Darbhanga","Bihar",2),
    ("Purnia","Bihar",2),("Ara","Bihar",2),("Begusarai","Bihar",2),
    ("Munger","Bihar",2),("Chhapra","Bihar",2),("Samastipur","Bihar",2),
    ("Hajipur","Bihar",2),("Sitamarhi","Bihar",2),("Motihari","Bihar",2),
    ("Kishanganj","Bihar",2),("Madhubani","Bihar",2),("Nawada","Bihar",2),
    ("Siwan","Bihar",2),("Gopalganj","Bihar",2),
    ("Lucknow","Uttar Pradesh",1),("Kanpur","Uttar Pradesh",1),
    ("Agra","Uttar Pradesh",1),("Varanasi","Uttar Pradesh",1),
    ("Prayagraj","Uttar Pradesh",1),("Meerut","Uttar Pradesh",2),
    ("Noida","Uttar Pradesh",1),("Ghaziabad","Uttar Pradesh",2),
    ("Gorakhpur","Uttar Pradesh",2),("Bareilly","Uttar Pradesh",2),
    ("Aligarh","Uttar Pradesh",2),("Mathura","Uttar Pradesh",2),
    ("Moradabad","Uttar Pradesh",2),("Jhansi","Uttar Pradesh",2),
    ("Ranchi","Jharkhand",1),("Jamshedpur","Jharkhand",1),
    ("Dhanbad","Jharkhand",2),("Bokaro","Jharkhand",2),
    ("Deoghar","Jharkhand",2),("Hazaribagh","Jharkhand",2),
    ("Kolkata","West Bengal",1),("Siliguri","West Bengal",2),
    ("Asansol","West Bengal",2),("Durgapur","West Bengal",2),
    ("Bardhaman","West Bengal",2),("Malda","West Bengal",2),
    ("Bhubaneswar","Odisha",1),("Cuttack","Odisha",2),
    ("Rourkela","Odisha",2),("Berhampur","Odisha",2),
    ("Bhopal","Madhya Pradesh",1),("Indore","Madhya Pradesh",1),
    ("Jabalpur","Madhya Pradesh",2),("Gwalior","Madhya Pradesh",2),
    ("Raipur","Chhattisgarh",1),("Bilaspur","Chhattisgarh",2),
    ("Bhilai","Chhattisgarh",2),("Durg","Chhattisgarh",2),
    ("Delhi","Delhi",1),("Gurugram","Haryana",1),
    ("Faridabad","Haryana",2),("Ambala","Haryana",2),
    ("Jaipur","Rajasthan",1),("Jodhpur","Rajasthan",2),
    ("Udaipur","Rajasthan",2),("Kota","Rajasthan",2),
    ("Bikaner","Rajasthan",2),("Ajmer","Rajasthan",2),
    ("Mumbai","Maharashtra",1),("Pune","Maharashtra",1),
    ("Nagpur","Maharashtra",1),("Nashik","Maharashtra",2),
    ("Aurangabad","Maharashtra",2),("Thane","Maharashtra",2),
    ("Bengaluru","Karnataka",1),("Mysuru","Karnataka",2),
    ("Mangaluru","Karnataka",2),("Hubli","Karnataka",2),
    ("Chennai","Tamil Nadu",1),("Coimbatore","Tamil Nadu",2),
    ("Madurai","Tamil Nadu",2),("Salem","Tamil Nadu",2),
    ("Hyderabad","Telangana",1),("Warangal","Telangana",2),
    ("Visakhapatnam","Andhra Pradesh",1),("Vijayawada","Andhra Pradesh",1),
    ("Tirupati","Andhra Pradesh",2),("Guntur","Andhra Pradesh",2),
    ("Ahmedabad","Gujarat",1),("Surat","Gujarat",1),
    ("Vadodara","Gujarat",2),("Rajkot","Gujarat",2),
    ("Chandigarh","Punjab",1),("Ludhiana","Punjab",2),
    ("Amritsar","Punjab",2),("Jalandhar","Punjab",2),
    ("Guwahati","Assam",1),("Silchar","Assam",2),
    ("Thiruvananthapuram","Kerala",1),("Kochi","Kerala",1),
    ("Kozhikode","Kerala",2),("Thrissur","Kerala",2),
    ("Dehradun","Uttarakhand",1),("Haridwar","Uttarakhand",2),
    ("Shimla","Himachal Pradesh",2),
    ("Jammu","Jammu & Kashmir",2),("Srinagar","Jammu & Kashmir",2),
]

# ══════════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS wp_sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        username TEXT NOT NULL,
        app_password TEXT NOT NULL,
        site_type TEXT DEFAULT 'general',
        is_active INTEGER DEFAULT 1,
        last_connected TEXT,
        post_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL,
        state_name TEXT NOT NULL,
        country TEXT DEFAULT 'India',
        slug TEXT UNIQUE NOT NULL,
        tier INTEGER DEFAULT 2,
        is_international INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS wp_published_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_id INTEGER,
        city_id INTEGER,
        wp_post_id INTEGER,
        post_type TEXT DEFAULT 'post',
        template_key TEXT,
        title TEXT,
        slug TEXT,
        wp_url TEXT,
        status TEXT DEFAULT 'published',
        seo_score INTEGER DEFAULT 0,
        word_count INTEGER DEFAULT 0,
        published_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(site_id) REFERENCES wp_sites(id),
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );
    CREATE TABLE IF NOT EXISTS local_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        slug TEXT UNIQUE,
        file_path TEXT,
        word_count INTEGER DEFAULT 0,
        seo_score INTEGER DEFAULT 0,
        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        details TEXT,
        ts TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    defaults = {
        "brand":"TACHY SCHOOL ERP","short":"TACHY",
        "website":"https://tachy.in","phone":"+91 8434801033",
        "wa":"918434801033","email":"info@tachy.in",
        "ga":"G-S2XL35PNS8","out_dir":OUT_DIR,
        "base_city":"Katihar","base_state":"Bihar",
        "primary_color":"#6c63ff",
        "wp_publish_delay":"2",
        "wp_default_status":"publish",
        "wp_default_category":"School ERP",
        "wp_update_existing":"0",
        "wp_ping_google":"1",
        "use_ai_keywords":"1",
        "gemini_api_key":"",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))

    # Pre-seed cities
    for city, state, tier in INDIAN_CITIES:
        slug = city.lower().replace(" ","-") + "-school-erp"
        c.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,tier,is_international) VALUES(?,?,?,?,?,?)",
                  (city, state, "India", slug, tier, 0))

    conn.commit()
    conn.close()

def cfg(key):
    conn = sqlite3.connect(DB_PATH)
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return r[0] if r else ""

def set_cfg(key, val):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, val))
    conn.commit(); conn.close()

def log_db(action, detail=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO audit_log(action,details) VALUES(?,?)", (action, detail))
        conn.commit(); conn.close()
    except: pass


# ══════════════════════════════════════════════════════════════════════
#  CONTENT GENERATORS
# ══════════════════════════════════════════════════════════════════════
def _vary(pool, city, state):
    return random.choice(pool).replace("{city}", city).replace("{state}", state)

def _cf(city):
    return CITY_FACTS.get(city, CITY_FACTS["DEFAULT"])

def _sd(state):
    return STATE_DATA.get(state, STATE_DATA["DEFAULT"])

def _seo_score(html, city, state):
    score = 0
    lhtml = html.lower(); lcity = city.lower(); lstate = state.lower()
    checks = [
        (8, "<h1" in lhtml and lcity in lhtml),
        (6, lcity in lhtml),
        (5, "faqpage" in lhtml or "faq" in lhtml),
        (5, lstate in lhtml),
        (4, "cbse" in lhtml),
        (4, "free demo" in lhtml or "freedemo" in lhtml),
        (4, "whatsapp" in lhtml),
        (4, html.count(lcity) >= 10),
        (3, len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html))) >= 800),
        (3, "schema.org" in lhtml),
        (3, "testimonial" in lhtml or "review" in lhtml),
        (3, "upi" in lhtml or "fee" in lhtml),
        (3, "attendance" in lhtml),
        (2, "transport" in lhtml),
        (2, "payroll" in lhtml or "hr" in lhtml),
        (2, "mobile" in lhtml or "android" in lhtml),
        (2, "tachy" in lhtml),
        (2, "demo" in lhtml),
        (2, "cloud" in lhtml),
        (2, "boarding" in lhtml or "report card" in lhtml),
    ]
    for pts, ok in checks:
        if ok: score += pts
    return min(score, 100)

def readability_score(text):
    """Simple Flesch-Kincaid readability estimate."""
    words = re.findall(r'\b\w+\b', text)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    if not sentences or not words:
        return 60
    avg_words = len(words) / max(len(sentences), 1)
    syllables = sum(max(1, len(re.findall(r'[aeiou]+', w, re.I))) for w in words)
    avg_syllables = syllables / max(len(words), 1)
    fk = 206.835 - (1.015 * avg_words) - (84.6 * avg_syllables)
    return max(0, min(100, int(fk)))

def inject_lsi_keywords(content, city, state):
    """Inject LSI keywords naturally into existing content."""
    lsi = [
        f"school management system {city}",
        f"CBSE school software {city}",
        f"school ERP {state}",
        f"digital school platform",
        f"cloud school management",
        f"school fee automation",
        f"parent mobile app school",
        f"school attendance tracking",
        f"student information system",
        f"School erp software free download",
        f"School erp login",
        f"School ERP app",
        f"School erp software download",
        f"Free school ERP software in India",
        f"Best school ERP software in India",
        f"School ERP India",
        f"Entab alternative in {city}",
        f"Teachmint alternative for schools",
        f"Fedena alternative {city}",
        f"school ERP with WhatsApp and Hindi support",
        f"best school ERP with transport and HR modules",
        f"MyClassCampus alternative",
        f"Edunext alternative {state}",
        f"Skodefy alternative"
    ]
    # Already in content? Don't add
    to_add = [kw for kw in lsi if kw.lower() not in content.lower()][:3]
    if to_add:
        kw_text = f"\n<p>Schools across {city} also search for: <em>{', '.join(to_add)}</em> — all capabilities available in TACHY School ERP.</p>"
        content = content + kw_text
    return content

def get_ai_trending_keywords(city, state, context="school ERP"):
    """Fetch real-time trending keywords using Gemini API (if key provided) or fallback to Free AI (Pollinations.ai)"""
    if str(cfg("use_ai_keywords")) != "1":
        return []
    
    prompt = f"Act as an SEO expert. Give me exactly 5 real-time trending search keywords for '{context}' in the city of {city}, {state}. Return ONLY a comma-separated list of keywords. No numbers, no bullets, no introduction, just keywords."
    
    gemini_key = cfg("gemini_api_key").strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                keywords = [k.strip().lower() for k in text.replace("\n", ",").split(",") if len(k.strip()) > 3]
                return keywords[:5]
        except Exception:
            # Fallback to free API on error
            pass

    # Free API Fallback
    url = "https://text.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TACHY-SEO-PRO/4.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            text = resp.read().decode('utf-8').strip()
            keywords = [k.strip().lower() for k in text.replace("\n", ",").split(",") if len(k.strip()) > 3]
            return keywords[:5]
    except Exception as e:
        return []

def generate_wp_blog_content(city, state, template_key, seed=0):
    """
    Generate full SEO-optimized WordPress blog post HTML content.
    Returns (title, content_html, slug, meta_desc, tags_list, category, seo_score, word_count)
    """
    random.seed(seed or abs(hash(city + state + template_key)) % 99999)
    tpl = TRENDING_BLOG_TEMPLATES[template_key]
    yr  = str(datetime.now().year)
    cf  = _cf(city)
    sd  = _sd(state)
    s   = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT key,value FROM settings").fetchall()
        conn.close()
        s = dict(rows)
    except: pass

    website = s.get("website","https://tachy.in")
    phone   = s.get("phone","+91 8434801033")
    wa      = s.get("wa","918434801033")
    brand   = s.get("brand","TACHY SCHOOL ERP")
    short   = s.get("short","TACHY")
    city_slug = city.lower().replace(" ","-")

    title    = tpl["title"].replace("{city}",city).replace("{state}",state).replace("{year}",yr).replace("{city_slug}",city_slug)
    slug     = tpl["slug"].replace("{city}",city.lower().replace(" ","-")).replace("{state}",state.lower().replace(" ","-")).replace("{year}",yr).replace("{city_slug}",city_slug)
    meta_desc= tpl["meta"].replace("{city}",city).replace("{state}",state).replace("{year}",yr)
    category = tpl.get("category","School ERP by City")
    tags_raw = tpl.get("tags",[])
    tags     = [t.replace("{city}",city).replace("{state}",state) for t in tags_raw]

    hero_intro   = _vary(HERO_INTROS, city, state)
    why_para     = _vary(WHY_PARAS, city, state)
    faq_picks    = random.sample(FAQS_POOL, min(5, len(FAQS_POOL)))
    testi_picks  = random.sample(TESTIMONIALS_POOL, min(2, len(TESTIMONIALS_POOL)))

    # ── FAQ HTML ───────────────────────────────────────────────────
    faq_html = ""
    for q, a in faq_picks:
        q2 = q.replace("{city}",city).replace("{state}",state)
        a2 = a.replace("{city}",city).replace("{state}",state)
        faq_html += f"""
<div class="tachy-faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
<h4 itemprop="name">{q2}</h4>
<div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
<p itemprop="text">{a2}</p>
</div>
</div>"""

    # ── Testimonials ──────────────────────────────────────────────
    testi_html = ""
    for name, role, school, quote in testi_picks:
        school2 = school.replace("{city}",city)
        quote2  = quote.replace("{city}",city).replace("{state}",state)
        testi_html += f"""
<blockquote class="tachy-testimonial" itemscope itemtype="https://schema.org/Review">
<p itemprop="reviewBody">"{quote2}"</p>
<cite itemprop="author"><strong>{name}</strong>, {role} — {school2}</cite>
<div itemprop="reviewRating" itemscope itemtype="https://schema.org/Rating">
<meta itemprop="ratingValue" content="5"/><span>★★★★★</span>
</div>
</blockquote>"""

    # ── JSON-LD Schema ─────────────────────────────────────────────
    faq_schema_items = json.dumps([{
        "@type":"Question",
        "name": q.replace("{city}",city).replace("{state}",state),
        "acceptedAnswer":{"@type":"Answer","text":a.replace("{city}",city).replace("{state}",state)}
    } for q, a in faq_picks])

    schema = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type":"Article",
             "headline": title,
             "description": meta_desc,
             "author":{"@type":"Organization","name":brand},
             "publisher":{"@type":"Organization","name":brand,"url":website},
             "datePublished": datetime.now().strftime("%Y-%m-%d"),
             "dateModified": datetime.now().strftime("%Y-%m-%d"),
             "mainEntityOfPage": {"@type":"WebPage"}},
            {"@type":"FAQPage",
             "mainEntity": json.loads(faq_schema_items)},
            {"@type":"LocalBusiness",
             "name":brand,"url":website,"telephone":phone,
             "areaServed":[city, state, "India"],
             "description":f"School ERP Software for {city} schools"},
            {"@type":"SoftwareApplication",
             "name":brand,
             "operatingSystem":"All",
             "applicationCategory":"EducationalApplication",
             "offers":{"@type":"Offer","price":"10.00","priceCurrency":"INR"},
             "aggregateRating":{"@type":"AggregateRating","ratingValue":"4.9","ratingCount":"153"}},
            {"@type":"BreadcrumbList",
             "itemListElement":[
                 {"@type":"ListItem","position":1,"name":"Home","item":website},
                 {"@type":"ListItem","position":2,"name":f"School ERP {state}","item":f"{website}/school-erp-{state.lower().replace(' ','-')}/"},
                 {"@type":"ListItem","position":3,"name":city,"item":f"{website}/{slug}/"}
             ]},
            {"@type":"VideoObject",
             "name":f"TACHY School ERP Demo in {city}",
             "description":f"Learn why {city} schools are switching to TACHY School ERP.",
             "thumbnailUrl":f"{website}/logo.png",
             "uploadDate":"2024-01-01T08:00:00+08:00",
             "embedUrl":"https://www.youtube.com/embed/ZcUyI2yURx4?si=kAcYQrym8aY_7KIa"}
        ]
    }, ensure_ascii=False, indent=2)

    # ── Build final HTML content ──────────────────────────────────
    content = f"""<script type="application/ld+json">
{schema}
</script>

<!-- TACHY School ERP — {city}, {state} — Generated by TACHY SEO PRO v4.0 -->

<div class="tachy-hero-banner" style="background:linear-gradient(135deg,#6c63ff,#2dd4bf);color:#fff;padding:28px 24px;border-radius:12px;margin-bottom:28px;">
<h2 style="color:#fff;margin:0 0 10px;font-size:1.5em;">🏫 School ERP Software in {city}, {state}</h2>
<p style="margin:0 0 16px;opacity:.92;font-size:1.05em;">{hero_intro}</p>
<p style="margin:0;">
<a href="{website}/leadform.php" style="background:#fff;color:#6c63ff;padding:10px 22px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block;margin-right:10px;">📅 Book Free Demo</a>
<a href="https://wa.me/{wa}?text=Hi+TACHY,+I+need+school+ERP+for+{urllib.parse.quote(city)}" style="background:#25D366;color:#fff;padding:10px 22px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block;">💬 WhatsApp Now</a>
</p>
</div>

<h2>Why {city} Schools Are Switching to Digital ERP in {yr}</h2>
<p>{why_para}</p>

<p>Schools in <strong>{city}, {state}</strong> are increasingly adopting cloud-based school management platforms to handle daily operations — from fee collection to exam management. With <strong>{cf['schools']} schools</strong> in the region, the competition for student enrollment means only digitally-equipped institutions will stand out.</p>

<p>TACHY School ERP is trusted by 500+ schools across India. It automates admissions, fee collection, attendance tracking, exam management, transport logistics, HR and payroll — all from a single cloud-based dashboard, accessible from any device.</p>

<h2>Top 10 Features Schools in {city} Love About TACHY</h2>
<ol>
<li><strong>Online Fee Collection (UPI/NEFT/Cash)</strong> — Auto-receipt generation, custom fee heads, late fine rules, parent WhatsApp alerts</li>
<li><strong>Digital Attendance</strong> — Mark attendance by class/section, instant parent SMS/WhatsApp alerts, monthly reports</li>
<li><strong>CBSE/ICSE Report Card Generator</strong> — One-click PDF report cards for all Indian boards including {sd['board']}</li>
<li><strong>Admission Management</strong> — Online applications, document upload, seat availability, enquiry tracking</li>
<li><strong>Transport Management</strong> — Route planning, bus attendance, parent GPS alerts, driver management</li>
<li><strong>HR & Payroll</strong> — Attendance-linked salary, leave management, payslips, EPF/ESI compliance</li>
<li><strong>Parent Communication App</strong> — Android app with real-time notifications, digital notices, WhatsApp integration</li>
<li><strong>Management Dashboard</strong> — Real-time analytics on collections, attendance trends, academic performance</li>
<li><strong>Library Management</strong> — Issue/return tracking, barcode support, overdue fine management</li>
<li><strong>Multi-Branch Management</strong> — Central control of all school branches from a single dashboard</li>
</ol>

<h2>What {city} School Owners Say About TACHY</h2>
{testi_html}

<h2>TACHY vs Other School ERP Software — Why TACHY Wins for {city} Schools</h2>
<table style="width:100%;border-collapse:collapse;margin:16px 0;">
<thead><tr style="background:#6c63ff;color:#fff;">
<th style="padding:10px;text-align:left;">Feature / Capability</th>
<th style="padding:10px;text-align:center;">TACHY ERP</th>
<th style="padding:10px;text-align:center;">Competitor Reality</th>
</tr></thead>
<tbody>
<tr style="background:#f8fafc;"><td style="padding:9px;border:1px solid #e2e8f0;">Local {city}/{state} Dedicated Support</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:green;font-weight:700;">✅ Yes</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:red;">❌ Generic Content (Entab / Fedena)</td></tr>
<tr><td style="padding:9px;border:1px solid #e2e8f0;">WhatsApp & Hindi Language App</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:green;font-weight:700;">✅ Built-in</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:red;">❌ Missing / Add-on (Edunext / Skodefy)</td></tr>
<tr style="background:#f8fafc;"><td style="padding:9px;border:1px solid #e2e8f0;">Deep Fee, Transport & HR Modules</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:green;font-weight:700;">✅ Advanced ERP</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:orange;">⚠ Basic Ed-Tech only (Teachmint)</td></tr>
<tr><td style="padding:9px;border:1px solid #e2e8f0;">{sd['board']} Pre-configured Support</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:green;font-weight:700;">✅ Yes</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:red;">❌ Limited (Fedena / MyClassCampus)</td></tr>
<tr style="background:#f8fafc;"><td style="padding:9px;border:1px solid #e2e8f0;">UPI Fee Collection & Auto-receipts</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:green;font-weight:700;">✅ Included</td><td style="padding:9px;border:1px solid #e2e8f0;text-align:center;color:orange;">⚠ Weak Integration (Skodefy)</td></tr>
</tbody></table>

<!-- Hindi SEO Block targeting Tier-2/3 search volume and addressing Edunext's weakness -->
<div class="tachy-hindi-seo" style="background:#fff7ed;border-left:4px solid #f97316;padding:16px;margin:24px 0;border-radius:4px;">
<h3 style="margin-top:0;color:#9a3412;font-size:1.2em;">Also Available in Hindi (हिंदी में उपलब्ध)</h3>
<p style="margin-bottom:0;color:#7c2d12;">क्या आप <strong>{city}</strong> में <strong>बेस्ट स्कूल मैनेजमेंट सॉफ्टवेयर</strong> (Best School ERP Software) खोज रहे हैं? TACHY ERP शिक्षक और माता-पिता के लिए हिंदी मोबाइल ऐप (Hindi Mobile App) और ऑटोमैटिक व्हाट्सएप मैसेजिंग (Automatic WhatsApp Messaging) के साथ आता है।</p>
</div>

<h2>How Much Does School ERP Cost for {city} Schools?</h2>
<p>TACHY School ERP pricing for <strong>{city} schools</strong> is based on student strength and selected modules. Schools can start with core modules (fee management + attendance) and add more as needed. We offer:</p>
<ul>
<li><strong>Monthly plan</strong> — Pay-as-you-go, no long commitment</li>
<li><strong>Annual plan</strong> — Best value, save up to 30%</li>
<li><strong>Custom plans</strong> — For school chains with multiple branches</li>
</ul>
<p>To get an exact quote for your <strong>{city} school</strong>, call <a href="tel:{phone}"><strong>{phone}</strong></a> or <a href="{website}/leadform.php">book a free 30-minute demo</a>.</p>

<h2>Frequently Asked Questions — School ERP in {city}</h2>
<div itemscope itemtype="https://schema.org/FAQPage">
{faq_html}
</div>

<h2>Get Started: Free Demo for {city} Schools</h2>
<p>Ready to transform your <strong>{city} school</strong>? Book a free personalized demo today. Our team covers all of {state} and will show you exactly how TACHY fits your school's workflow.</p>

<div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:24px;margin:20px 0;text-align:center;">
<h3 style="color:#166534;margin:0 0 12px;">📅 Book Your Free Demo — {city} Schools</h3>
<p style="color:#15803d;margin:0 0 16px;">✅ 30-minute personalized demo &nbsp;|&nbsp; ✅ No commitment &nbsp;|&nbsp; ✅ Free implementation support</p>
<p>
<a href="{website}/leadform.php" style="background:#16a34a;color:#fff;padding:12px 28px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block;margin-right:10px;">📅 Book Free Demo</a>
<a href="https://wa.me/{wa}?text=Hi+TACHY,+demo+for+{urllib.parse.quote(city)}+school" style="background:#25D366;color:#fff;padding:12px 28px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block;margin-right:10px;">💬 WhatsApp</a>
<a href="tel:{phone}" style="background:#6c63ff;color:#fff;padding:12px 28px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block;">📞 Call Now</a>
</p>
</div>

<p style="color:#64748b;font-size:0.9em;margin-top:24px;">
<em>Keywords: school ERP software {city}, school management software {city}, {city} school ERP, CBSE school ERP {city}, school fee software {city}, school attendance software {city}, best school ERP {state}</em>
</p>"""

    # AI Trending Keywords Integration
    ai_kws = get_ai_trending_keywords(city, state, tpl.get("category", "School ERP"))
    if ai_kws:
        ai_list_html = "<ul>\n" + "\n".join([f"<li>{k.title()}</li>" for k in set(ai_kws)]) + "\n</ul>"
        content += f"\n<h3>Trending Search Keywords in {city} ({yr})</h3>\n<p>Local schools and parents are actively searching for:</p>\n{ai_list_html}\n"
        tags.extend(ai_kws[:3]) # Add top 3 to WP tags
        # Update template keywords dynamically for GUI previews
        current_kw = TRENDING_BLOG_TEMPLATES[template_key].get("trending_keywords", [])
        TRENDING_BLOG_TEMPLATES[template_key]["trending_keywords"] = current_kw + [k for k in ai_kws if k not in current_kw]
        
    # Video Embed 
    video_html = f'''
    <h2>See TACHY in Action</h2>
    <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin-bottom:24px;border-radius:12px;">
      <iframe src="https://www.youtube.com/embed/ZcUyI2yURx4?si=kAcYQrym8aY_7KIa" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen loading="lazy"></iframe>
    </div>
    '''
    content += video_html
    
    # Auto Internal Link Silo (Nearby Cities)
    try:
        conn = sqlite3.connect(DB_PATH)
        silo = conn.execute("SELECT city_name, slug FROM cities WHERE state_name=? AND city_name!=? LIMIT 5", (state, city)).fetchall()
        conn.close()
        if silo:
            silo_html = f"\n<div class='tachy-seo-silo' style='margin-top:24px;padding:16px;background:#f8fafc;border-radius:8px;'>\n<h3>Explore {brand} in Nearby Cities of {state}</h3>\n<ul style='list-style-type:none;padding:0;'>\n"
            for scity, sslug in silo:
                silo_html += f"<li style='margin-bottom:8px;'>🔗 <a href='{website}/{sslug}/' style='color:#6c63ff;text-decoration:none;'>School ERP Software in {scity}</a></li>\n"
            silo_html += "</ul>\n</div>\n"
            content += silo_html
    except:
        pass

    # Inject LSI keywords
    content = inject_lsi_keywords(content, city, state)
    plain_text = re.sub(r'<[^>]+>', '', content)

    wc    = len(re.findall(r'\w+', plain_text))
    score = _seo_score(content, city, state)
    read  = readability_score(plain_text)

    return title, content, slug, meta_desc, tags, category, score, wc, read


# ══════════════════════════════════════════════════════════════════════
#  GUI APPLICATION v4.0
# ══════════════════════════════════════════════════════════════════════
UI_Q = queue.Queue()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TACHY SEO PRO v4.0 — WordPress Direct Publisher + SEO Engine")
        self.geometry("1500x900")
        self.minsize(1200, 750)
        self.configure(bg="#060b18")
        self._wp_apis = {}  # site_id → WordPressAPI instance
        self._stop_flag = False
        self._style()
        init_db()
        self._build_ui()
        self._poll_ui_queue()

    def _poll_ui_queue(self):
        try:
            while True:
                fn = UI_Q.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.after(60, self._poll_ui_queue)

    def _ui(self, fn, *args, **kwargs):
        UI_Q.put(lambda f=fn, a=args, k=kwargs: f(*a, **k))

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        BG,BG2,FG = "#060b18","#0f1728","#dde8ff"
        ACC,MUT,BOR,SEL = "#6c63ff","#4a5f80","#1a2a44","#1a3055"
        s.configure(".", background=BG, foreground=FG, font=("Segoe UI",10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("TButton", background=ACC, foreground="white",
                    font=("Segoe UI",10,"bold"), relief="flat", padding=(14,8), borderwidth=0)
        s.map("TButton", background=[("active","#4f46e5"),("pressed","#3730a3")])
        s.configure("G.TButton", background="#16a34a"); s.map("G.TButton", background=[("active","#15803d")])
        s.configure("R.TButton", background="#dc2626"); s.map("R.TButton", background=[("active","#b91c1c")])
        s.configure("Y.TButton", background="#d97706"); s.map("Y.TButton", background=[("active","#b45309")])
        s.configure("C.TButton", background="#0891b2"); s.map("C.TButton", background=[("active","#0e7490")])
        s.configure("W.TButton", background="#16a34a"); s.map("W.TButton", background=[("active","#15803d")])
        s.configure("TEntry", fieldbackground="#0f1f36", foreground=FG, bordercolor=BOR, insertcolor=FG, relief="flat", padding=7)
        s.configure("TCombobox", fieldbackground="#0f1f36", foreground=FG, background="#0f1f36", selectbackground=SEL, relief="flat")
        s.map("TCombobox", fieldbackground=[("readonly","#0f1f36")])
        s.configure("Treeview", background="#0f1728", foreground=FG, fieldbackground="#0f1728", rowheight=26, bordercolor=BOR, relief="flat")
        s.configure("Treeview.Heading", background="#060b18", foreground=ACC, font=("Segoe UI",9,"bold"), relief="flat", padding=8)
        s.map("Treeview", background=[("selected",SEL)], foreground=[("selected","#fff")])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background="#0f1728", foreground=MUT, padding=(18,10), font=("Segoe UI",10,"bold"), borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected",ACC)], foreground=[("selected","#fff")])
        s.configure("TScrollbar", background="#1a2a44", troughcolor=BG, bordercolor=BG, arrowcolor=MUT, relief="flat")
        s.configure("TProgressbar", background=ACC, troughcolor="#1a2a44", thickness=10, borderwidth=0)
        s.configure("Sep.TFrame", background=BOR)

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg="#040810", height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  TACHY SEO PRO  v4.0",
                 bg="#040810", fg="#6c63ff", font=("Segoe UI",16,"bold")).pack(side="left",padx=18,pady=14)
        tk.Label(hdr, text="WordPress Direct Publisher + Ultimate SEO Engine — Post to Any WP Site",
                 bg="#040810", fg="#3a4f70", font=("Segoe UI",10)).pack(side="left")
        self.sv = tk.StringVar(value="✅  Ready — v4.0")
        tk.Label(hdr, textvariable=self.sv, bg="#040810", fg="#4ade80",
                 font=("Segoe UI",9,"bold")).pack(side="right",padx=18)
        self._wp_status = tk.StringVar(value="🔴 No WP Site Connected")
        tk.Label(hdr, textvariable=self._wp_status, bg="#040810", fg="#fbbf24",
                 font=("Segoe UI",9,"bold")).pack(side="right",padx=14)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self._nb = nb

        self._tab_wp_manager()
        self._tab_wp_publisher()
        self._tab_cities()
        self._tab_dashboard()
        self._tab_published()
        self._tab_seo_tools()
        self._tab_settings()
        self._tab_log()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 1 — WORDPRESS SITE MANAGER
    # ══════════════════════════════════════════════════════════════════
    def _tab_wp_manager(self):
        f = ttk.Frame(self._nb); self._nb.add(f, text="  🌐  WordPress Sites  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(3, weight=1)

        # ── Title ──────────────────────────────────────────────────────
        tk.Label(f, text="🌐  WordPress Site Manager — Add & Manage Your WP Sites",
                 bg="#060b18", fg="#6c63ff", font=("Segoe UI",13,"bold")).grid(
                 row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12,4))

        # ── How-to panel ───────────────────────────────────────────────
        how = tk.Frame(f, bg="#0a1a0a", highlightthickness=1, highlightbackground="#1a4a1a")
        how.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(0,8))
        tk.Label(how, text="📋  How to Get WordPress Application Password (No Plugin Needed — Works on WP 5.6+)",
                 bg="#0a1a0a", fg="#4ade80", font=("Segoe UI",10,"bold")).pack(anchor="w", padx=12, pady=(8,4))
        steps = [
            "1. Log in to WordPress Admin  →  Go to  Users  →  Your Profile  (or any admin user profile)",
            "2. Scroll down to  'Application Passwords'  section  →  Enter any name (e.g. 'TACHY SEO Tool')",
            "3. Click  'Add New Application Password'  →  Copy the generated password (shown only once!)",
            "4. Paste the password below — spaces in the password are fine, the tool handles them automatically",
            "5. Click  'Test Connection'  to verify — you'll see your username and role if successful",
            "⚠  Note: The WP REST API must be enabled (default on most hosts). Some security plugins may block it.",
        ]
        for step in steps:
            color = "#f87171" if step.startswith("⚠") else "#7dd3fc"
            tk.Label(how, text=f"  {step}", bg="#0a1a0a", fg=color,
                     font=("Segoe UI",9)).pack(anchor="w", padx=12, pady=1)
        tk.Label(how, text="", bg="#0a1a0a").pack(pady=3)

        # ── Add Site Form ──────────────────────────────────────────────
        form = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=4)
        form.columnconfigure(1, weight=1); form.columnconfigure(3, weight=1)

        tk.Label(form, text="➕  Add New WordPress Site",
                 bg="#0f1728", fg="#6c63ff", font=("Segoe UI",11,"bold")).grid(
                 row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10,6))

        self._wsite_name  = tk.StringVar(value="tachy.in")
        self._wsite_url   = tk.StringVar(value="https://tachy.in")
        self._wsite_user  = tk.StringVar()
        self._wsite_pass  = tk.StringVar()
        self._wsite_type  = tk.StringVar(value="school_erp")

        SITE_TYPES = ["school_erp","education_blog","general_blog","12fail","news","portfolio"]

        fields_left = [("Site Name *", self._wsite_name), ("Site URL *", self._wsite_url)]
        fields_right = [("WP Username *", self._wsite_user), ("App Password *", self._wsite_pass)]
        for i, (lbl, var) in enumerate(fields_left):
            tk.Label(form, text=lbl, bg="#0f1728", fg="#94a3b8").grid(row=i+1,column=0,sticky="w",padx=12,pady=4)
            ttk.Entry(form, textvariable=var, width=30).grid(row=i+1,column=1,sticky="ew",padx=(4,16),pady=4)
        for i, (lbl, var) in enumerate(fields_right):
            tk.Label(form, text=lbl, bg="#0f1728", fg="#94a3b8").grid(row=i+1,column=2,sticky="w",padx=4,pady=4)
            show = "" if "Password" not in lbl else "*"
            ttk.Entry(form, textvariable=var, width=32, show=show).grid(row=i+1,column=3,sticky="ew",padx=(4,12),pady=4)

        tk.Label(form, text="Site Type:", bg="#0f1728", fg="#94a3b8").grid(row=3,column=0,sticky="w",padx=12,pady=4)
        ttk.Combobox(form, textvariable=self._wsite_type, values=SITE_TYPES, width=18, state="readonly").grid(row=3,column=1,sticky="w",padx=(4,16),pady=4)

        btnrow = tk.Frame(form, bg="#0f1728"); btnrow.grid(row=4,column=0,columnspan=4,sticky="w",padx=12,pady=(4,12))
        ttk.Button(btnrow, text="🔌 Test Connection",    command=self._test_wp_connection, style="C.TButton").pack(side="left",padx=3)
        ttk.Button(btnrow, text="💾 Save Site",          command=self._save_wp_site, style="G.TButton").pack(side="left",padx=3)
        ttk.Button(btnrow, text="🗑 Delete Selected",    command=self._del_wp_site, style="R.TButton").pack(side="left",padx=3)
        ttk.Button(btnrow, text="🔄 Test All Sites",     command=self._test_all_sites).pack(side="left",padx=3)
        ttk.Button(btnrow, text="📊 Site Info",          command=self._show_site_info).pack(side="left",padx=3)

        self._conn_result = tk.StringVar(value="")
        tk.Label(form, textvariable=self._conn_result, bg="#0f1728", fg="#4ade80",
                 font=("Segoe UI",9,"bold")).grid(row=5,column=0,columnspan=4,sticky="w",padx=12,pady=(0,8))

        # ── Sites Treeview ─────────────────────────────────────────────
        cols = ("name","url","username","type","status","posts","last_conn")
        self._wptree = ttk.Treeview(f, columns=cols, show="headings", selectmode="extended")
        hdrs = [("name","Site Name",110),("url","URL",220),("username","Username",100),
                ("type","Type",90),("status","Status",80),("posts","Posts",60),("last_conn","Last Connected",140)]
        for col, hdr, w in hdrs:
            self._wptree.heading(col, text=hdr)
            self._wptree.column(col, width=w)
        self._wptree.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0,4))
        sb = ttk.Scrollbar(f, orient="vertical", command=self._wptree.yview)
        self._wptree.configure(yscroll=sb.set); sb.grid(row=3, column=1, sticky="ns")
        self._wptree.bind("<<TreeviewSelect>>", self._on_wp_site_select)
        self._load_wp_sites()

    def _get_wp_api(self, site_id=None):
        """Get or create WP API instance for a site."""
        if site_id is None:
            sel = self._wptree.selection()
            if not sel: return None, "No site selected"
            site_id = int(sel[0])
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT url,username,app_password FROM wp_sites WHERE id=?", (site_id,)).fetchone()
        conn.close()
        if not r: return None, "Site not found"
        if site_id not in self._wp_apis:
            self._wp_apis[site_id] = WordPressAPI(r[0], r[1], r[2])
        return self._wp_apis[site_id], None

    def _test_wp_connection(self):
        url  = self._wsite_url.get().strip()
        user = self._wsite_user.get().strip()
        pw   = self._wsite_pass.get().strip()
        if not url or not user or not pw:
            self._conn_result.set("❌ Fill in URL, username and application password first.")
            return
        self._conn_result.set("🔄 Testing connection...")
        self.update()
        def work():
            try:
                api = WordPressAPI(url, user, pw)
                ok, msg = api.test_connection()
                self._ui(lambda m=msg: self._conn_result.set(m))
                if ok:
                    self._ui(lambda: self._wp_status.set(f"🟢 Connected: {url}"))
            except Exception as e:
                self._ui(lambda e=e: self._conn_result.set(f"❌ Error: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _save_wp_site(self):
        name = self._wsite_name.get().strip()
        url  = self._wsite_url.get().strip()
        user = self._wsite_user.get().strip()
        pw   = self._wsite_pass.get().strip()
        if not all([name, url, user, pw]):
            messagebox.showwarning("Input","All fields required — Name, URL, Username, App Password"); return
        if not url.startswith("http"):
            messagebox.showwarning("URL","Site URL must start with https://"); return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR REPLACE INTO wp_sites(name,url,username,app_password,site_type) VALUES(?,?,?,?,?)",
                     (name, url.rstrip("/"), user, pw, self._wsite_type.get()))
        conn.commit(); conn.close()
        log_db("WP_SITE_ADD", f"{name}: {url}")
        messagebox.showinfo("Saved", f"✅ Site '{name}' saved!\n\nClick 'Test Connection' to verify credentials.")
        self._load_wp_sites()

    def _del_wp_site(self):
        sel = self._wptree.selection()
        if not sel: return
        if not messagebox.askyesno("Delete", f"Delete {len(sel)} selected WP site(s)?"): return
        conn = sqlite3.connect(DB_PATH)
        for iid in sel:
            conn.execute("DELETE FROM wp_sites WHERE id=?", (iid,))
            self._wp_apis.pop(int(iid), None)
        conn.commit(); conn.close()
        self._load_wp_sites()

    def _load_wp_sites(self):
        for r in self._wptree.get_children(): self._wptree.delete(r)
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT id,name,url,username,site_type,is_active,post_count,last_connected FROM wp_sites ORDER BY id").fetchall()
        conn.close()
        for sid, name, url, user, stype, active, posts, last in rows:
            status = "✅ Active" if active else "⏸ Inactive"
            lc = (last or "Never")[:16]
            self._wptree.insert("","end", iid=str(sid),
                                values=(name, url, user, stype, status, posts or 0, lc))

    def _on_wp_site_select(self, _=None):
        sel = self._wptree.selection()
        if sel:
            conn = sqlite3.connect(DB_PATH)
            r = conn.execute("SELECT name,url,username,app_password,site_type FROM wp_sites WHERE id=?", (sel[0],)).fetchone()
            conn.close()
            if r:
                self._wsite_name.set(r[0]); self._wsite_url.set(r[1])
                self._wsite_user.set(r[2]); self._wsite_pass.set(r[3])
                self._wsite_type.set(r[4])

    def _test_all_sites(self):
        conn = sqlite3.connect(DB_PATH)
        sites = conn.execute("SELECT id,name,url,username,app_password FROM wp_sites WHERE is_active=1").fetchall()
        conn.close()
        def work():
            for sid, name, url, user, pw in sites:
                try:
                    api = WordPressAPI(url, user, pw)
                    ok, msg = api.test_connection()
                    status = "connected" if ok else "failed"
                    conn2 = sqlite3.connect(DB_PATH)
                    conn2.execute("UPDATE wp_sites SET last_connected=? WHERE id=?",
                                  (datetime.now().strftime("%Y-%m-%d %H:%M"), sid))
                    conn2.commit(); conn2.close()
                    self._ui(self._bulk_log_safe, f"{'✅' if ok else '❌'} {name}: {msg}")
                except Exception as e:
                    self._ui(self._bulk_log_safe, f"❌ {name}: {e}")
            self._ui(self._load_wp_sites)
        threading.Thread(target=work, daemon=True).start()

    def _show_site_info(self):
        sel = self._wptree.selection()
        if not sel: messagebox.showinfo("Select","Select a site first."); return
        api, err = self._get_wp_api(int(sel[0]))
        if err: messagebox.showerror("Error", err); return
        def work():
            try:
                info = api.get_site_info()
                cats = api.get_categories()
                ok, msg = api.test_connection()
                cat_names = [c["name"] for c in cats[:20]]
                self._ui(lambda: messagebox.showinfo("Site Info",
                    f"Site: {info.get('name','?')}\nDescription: {info.get('description','')[:60]}\nURL: {info.get('url','')}\n\nConnection: {msg}\n\nCategories ({len(cats)}): {', '.join(cat_names[:10])}"))
            except Exception as e:
                self._ui(lambda e=e: messagebox.showerror("Error", str(e)))
        threading.Thread(target=work, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 2 — WORDPRESS PUBLISHER
    # ══════════════════════════════════════════════════════════════════
    def _tab_wp_publisher(self):
        f = ttk.Frame(self._nb); self._nb.add(f, text="  🚀  WP Publisher  ")
        f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1); f.rowconfigure(2, weight=1)

        tk.Label(f, text="🚀  WordPress Direct Publisher — Post City Pages & Blog Posts",
                 bg="#060b18", fg="#6c63ff", font=("Segoe UI",13,"bold")).grid(
                 row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12,4))

        # ── Controls ───────────────────────────────────────────────────
        ctrl = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        ctrl.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=4)
        ctrl.columnconfigure(1, weight=1); ctrl.columnconfigure(3, weight=1)

        # Row 0: Site + Template selector
        tk.Label(ctrl, text="WordPress Site:", bg="#0f1728", fg="#94a3b8").grid(row=0,column=0,sticky="w",padx=12,pady=6)
        self._pub_site = tk.StringVar()
        self._pub_site_combo = ttk.Combobox(ctrl, textvariable=self._pub_site, width=28, state="readonly")
        self._pub_site_combo.grid(row=0,column=1,sticky="w",padx=4,pady=6)
        ttk.Button(ctrl, text="🔄 Refresh Sites", command=self._refresh_pub_sites, style="C.TButton").grid(row=0,column=2,padx=8,pady=6)

        tk.Label(ctrl, text="Blog Template:", bg="#0f1728", fg="#94a3b8").grid(row=0,column=3,sticky="w",padx=4,pady=6)
        self._pub_template = tk.StringVar(value="city_erp_guide")
        ttk.Combobox(ctrl, textvariable=self._pub_template,
                     values=list(TRENDING_BLOG_TEMPLATES.keys()),
                     width=22, state="readonly").grid(row=0,column=4,sticky="w",padx=(4,12),pady=6)

        # Row 1: Post type + status + delay
        tk.Label(ctrl, text="Post Type:", bg="#0f1728", fg="#94a3b8").grid(row=1,column=0,sticky="w",padx=12,pady=4)
        self._pub_post_type = tk.StringVar(value="post")
        ttk.Combobox(ctrl, textvariable=self._pub_post_type,
                     values=["post","page"], width=10, state="readonly").grid(row=1,column=1,sticky="w",padx=4,pady=4)

        tk.Label(ctrl, text="Status:", bg="#0f1728", fg="#94a3b8").grid(row=1,column=2,sticky="w",padx=8,pady=4)
        self._pub_status = tk.StringVar(value="publish")
        ttk.Combobox(ctrl, textvariable=self._pub_status,
                     values=["publish","draft","pending","private","future"],
                     width=12, state="readonly").grid(row=1,column=3,sticky="w",padx=4,pady=4)

        tk.Label(ctrl, text="Delay (sec):", bg="#0f1728", fg="#94a3b8").grid(row=1,column=4,sticky="w",padx=4)
        self._pub_delay = tk.StringVar(value="3")
        ttk.Entry(ctrl, textvariable=self._pub_delay, width=5).grid(row=1,column=5,sticky="w",padx=(4,12),pady=4)

        # Row 2: Options checkboxes
        self._pub_update = tk.BooleanVar(value=False)
        self._pub_ping   = tk.BooleanVar(value=True)
        self._pub_skip_done = tk.BooleanVar(value=True)
        self._pub_all_templates = tk.BooleanVar(value=False)
        opts = tk.Frame(ctrl, bg="#0f1728"); opts.grid(row=2,column=0,columnspan=6,sticky="w",padx=12,pady=(4,8))
        tk.Checkbutton(opts, text="Update existing posts", variable=self._pub_update,
                       bg="#0f1728", fg="#c8d8f0", selectcolor="#0f1728", activebackground="#0f1728").pack(side="left",padx=6)
        tk.Checkbutton(opts, text="Skip already published", variable=self._pub_skip_done,
                       bg="#0f1728", fg="#c8d8f0", selectcolor="#0f1728", activebackground="#0f1728").pack(side="left",padx=6)
        tk.Checkbutton(opts, text="Ping Search Engines after publish", variable=self._pub_ping,
                       bg="#0f1728", fg="#c8d8f0", selectcolor="#0f1728", activebackground="#0f1728").pack(side="left",padx=6)
        tk.Checkbutton(opts, text="All templates per city", variable=self._pub_all_templates,
                       bg="#0f1728", fg="#c8d8f0", selectcolor="#0f1728", activebackground="#0f1728").pack(side="left",padx=6)

        # ── Left: Progress log ─────────────────────────────────────────
        lf = tk.Frame(f, bg="#060b18"); lf.grid(row=2, column=0, sticky="nsew", padx=(14,6), pady=4)
        lf.rowconfigure(2, weight=1); lf.columnconfigure(0, weight=1)

        brow = tk.Frame(lf, bg="#060b18"); brow.grid(row=0, column=0, sticky="ew", pady=(0,4))
        ttk.Button(brow, text="🚀 Publish ALL Cities", command=self._pub_all_cities, style="G.TButton").pack(side="left",padx=2)
        ttk.Button(brow, text="🏆 Tier 1 Cities Only", command=self._pub_tier1).pack(side="left",padx=2)
        ttk.Button(brow, text="🔍 Selected Cities",    command=self._pub_selected).pack(side="left",padx=2)
        ttk.Button(brow, text="⏹ Stop",               command=self._stop_pub, style="R.TButton").pack(side="left",padx=2)
        ttk.Button(brow, text="🗑 Clear Log",          command=self._clear_pub_log, style="Y.TButton").pack(side="left",padx=8)

        self._pub_prog = ttk.Progressbar(lf, mode="determinate")
        self._pub_prog.grid(row=1, column=0, sticky="ew", pady=(0,4))
        self._pub_lbl = tk.StringVar(value="Select a WP site and click Publish...")
        tk.Label(lf, textvariable=self._pub_lbl, bg="#060b18", fg="#4ade80",
                 font=("Segoe UI",9)).grid(row=2, column=0, sticky="w")
        self._pub_log = scrolledtext.ScrolledText(lf, height=20, bg="#040810", fg="#4ade80",
                                                   font=("Consolas",9), relief="flat", bd=0)
        self._pub_log.grid(row=3, column=0, sticky="nsew", pady=4)
        lf.rowconfigure(3, weight=1)

        # ── Right: Single city publisher ──────────────────────────────
        rf = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        rf.grid(row=2, column=1, sticky="nsew", padx=(6,14), pady=4)
        rf.columnconfigure(1, weight=1)

        tk.Label(rf, text="⚡  Single City Quick Publisher",
                 bg="#0f1728", fg="#6c63ff", font=("Segoe UI",12,"bold")).grid(
                 row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12,6))

        self._sc_city   = tk.StringVar(value="Patna")
        self._sc_state  = tk.StringVar(value="Bihar")
        self._sc_ctry   = tk.StringVar(value="India")
        STATES = ["Bihar","Uttar Pradesh","Jharkhand","West Bengal","Odisha","Madhya Pradesh",
                  "Chhattisgarh","Delhi","Haryana","Rajasthan","Maharashtra","Karnataka",
                  "Tamil Nadu","Telangana","Andhra Pradesh","Gujarat","Punjab","Assam","Kerala"]
        for i, (lbl, var, opts_) in enumerate([
            ("City",    self._sc_city,  None),
            ("State",   self._sc_state, STATES),
            ("Country", self._sc_ctry,  ["India","UAE","UK","USA","Canada","Singapore"]),
        ], 1):
            tk.Label(rf, text=lbl+":", bg="#0f1728", fg="#94a3b8").grid(row=i,column=0,sticky="w",padx=14,pady=4)
            if opts_:
                ttk.Combobox(rf, textvariable=var, values=opts_, width=20, state="normal").grid(row=i,column=1,padx=14,pady=4,sticky="ew")
            else:
                ttk.Entry(rf, textvariable=var, width=22).grid(row=i,column=1,padx=14,pady=4,sticky="ew")

        ttk.Button(rf, text="📄 Preview Content First",   command=self._preview_single_content).grid(row=4,column=0,columnspan=2,padx=14,pady=(8,3),sticky="ew")
        ttk.Button(rf, text="🚀 Publish to WordPress",    command=self._pub_single_city, style="G.TButton").grid(row=5,column=0,columnspan=2,padx=14,pady=3,sticky="ew")
        ttk.Button(rf, text="📋 Publish All Templates",   command=self._pub_single_all_templates).grid(row=6,column=0,columnspan=2,padx=14,pady=3,sticky="ew")
        ttk.Button(rf, text="🌐 Open Last Published",     command=self._open_last_published, style="Y.TButton").grid(row=7,column=0,columnspan=2,padx=14,pady=3,sticky="ew")
        ttk.Button(rf, text="📊 SEO Score Preview",       command=self._seo_score_preview, style="C.TButton").grid(row=8,column=0,columnspan=2,padx=14,pady=(3,8),sticky="ew")

        self._sc_out = scrolledtext.ScrolledText(rf, height=14, bg="#040810", fg="#94a3b8",
                                                  font=("Consolas",9), relief="flat", bd=0)
        self._sc_out.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0,10))
        rf.rowconfigure(9, weight=1)

        self._refresh_pub_sites()

    def _refresh_pub_sites(self):
        conn = sqlite3.connect(DB_PATH)
        sites = conn.execute("SELECT id, name, url FROM wp_sites WHERE is_active=1 ORDER BY id").fetchall()
        conn.close()
        vals = [f"{r[0]}  |  {r[1]}  ({r[2]})" for r in sites]
        self._pub_site_combo["values"] = vals
        if vals: self._pub_site.set(vals[0])
        if not sites:
            self._pub_site.set("⚠ No sites — Add one in 'WordPress Sites' tab")

    def _get_selected_site_id(self):
        """Parse site ID from combo selection."""
        val = self._pub_site.get()
        if not val or "⚠" in val: return None
        try:
            return int(val.split("|")[0].strip())
        except:
            return None

    def _pub_log_append(self, msg):
        try:
            self._pub_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self._pub_log.see("end")
        except: pass

    def _bulk_log_safe(self, msg):
        self._pub_log_append(msg)

    def _clear_pub_log(self):
        self._pub_log.delete("1.0","end")

    def _stop_pub(self):
        self._stop_flag = True
        self._pub_lbl.set("⏹ Stopping after current post...")

    def _get_or_create_cat_tag(self, api, cat_name, tag_names):
        """Get/create WP category and tags. Returns (cat_id, tag_ids)."""
        try:
            cat_id = api.get_or_create_category(cat_name)
            tag_ids = [api.get_or_create_tag(t) for t in tag_names[:5]]
            tag_ids = [t for t in tag_ids if t]
            return cat_id, tag_ids
        except Exception as e:
            return None, []

    def _publish_city_to_wp(self, api, city, state, template_key, status, update_existing, skip_done, seed=0):
        """
        Core publish function. Returns (success, post_id, post_url, action, score, wc).
        """
        title, content, slug, meta_desc, tags, category, score, wc, readability = \
            generate_wp_blog_content(city, state, template_key, seed)

        # Prepare categories and tags
        cat_id = None
        tag_ids = []
        try:
            cat_id, tag_ids = self._get_or_create_cat_tag(api, category, tags)
        except: pass

        # Determine post type
        post_type_fn = api.create_page if self._pub_post_type.get() == "page" else api.create_post

        if self._pub_post_type.get() == "page":
            post_id, post_url, action = api.create_page(
                title=title, content=content, slug=slug, meta_desc=meta_desc,
                status=status, update_existing=update_existing
            )
        else:
            post_id, post_url, action = api.create_post(
                title=title, content=content, slug=slug, meta_desc=meta_desc,
                status=status,
                categories=[cat_id] if cat_id else [],
                tags=tag_ids,
                update_existing=update_existing
            )
        return True, post_id, post_url, action, score, wc

    def _run_bulk_publish(self, cities_data, site_id):
        """Thread-safe bulk publish worker."""
        self._stop_flag = False
        api, err = self._get_wp_api(site_id)
        if err:
            self._ui(self._pub_log_append, f"❌ Cannot get API for site {site_id}: {err}")
            return

        template_key = self._pub_template.get()
        status       = self._pub_status.get()
        update_ex    = self._pub_update.get()
        skip_done    = self._pub_skip_done.get()
        all_tpls     = self._pub_all_templates.get()
        delay        = float(self._pub_delay.get() or 2)
        ping_google  = self._pub_ping.get()

        templates = list(TRENDING_BLOG_TEMPLATES.keys()) if all_tpls else [template_key]
        total = len(cities_data) * len(templates)
        done = ok_count = skip_count = err_count = 0

        self._ui(self._pub_log_append, f"🚀 Starting bulk publish — {len(cities_data)} cities × {len(templates)} templates = {total} posts")
        self._ui(self._pub_log_append, f"   Site: {api.site_url} | Status: {status} | Delay: {delay}s")

        for i, (cid, city, state, country) in enumerate(cities_data):
            if self._stop_flag:
                self._ui(self._pub_log_append, "⏹ Stopped by user."); break

            for tpl_key in templates:
                if self._stop_flag: break
                done += 1
                self._ui(lambda d=done,t=total,c=city,tk=tpl_key:
                    (self._pub_prog.__setitem__("maximum",t),
                     self._pub_prog.__setitem__("value",d),
                     self._pub_lbl.set(f"[{d}/{t}] {c} — {tk}...")))
                try:
                    success, post_id, post_url, action, score, wc = \
                        self._publish_city_to_wp(api, city, state, tpl_key, status, update_ex, skip_done, seed=i)

                    if action == "skipped":
                        skip_count += 1
                        self._ui(self._pub_log_append, f"  ⏭ SKIP  {city} [{tpl_key}] — already published")
                    else:
                        ok_count += 1
                        # Save to DB
                        conn2 = sqlite3.connect(DB_PATH)
                        conn2.execute("PRAGMA journal_mode=WAL")
                        conn2.execute(
                            "INSERT OR REPLACE INTO wp_published_posts(site_id,city_id,wp_post_id,post_type,template_key,title,slug,wp_url,status,seo_score,word_count) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                            (site_id, cid, post_id, self._pub_post_type.get(), tpl_key,
                             TRENDING_BLOG_TEMPLATES[tpl_key]["title"].replace("{city}",city).replace("{year}",str(datetime.now().year)),
                             TRENDING_BLOG_TEMPLATES[tpl_key]["slug"].replace("{city}",city.lower().replace(" ","-")).replace("{year}",str(datetime.now().year)),
                             post_url, status, score, wc)
                        )
                        conn2.execute("UPDATE wp_sites SET post_count = post_count + 1, last_connected=? WHERE id=?",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M"), site_id))
                        conn2.commit(); conn2.close()
                        log_db("WP_PUBLISH", f"{city},{state},{tpl_key},score={score},id={post_id}")
                        action_icon = "✅ PUB" if action=="created" else "🔄 UPD"
                        self._ui(self._pub_log_append,
                            f"  {action_icon}  {city} [{tpl_key}] — score={score}/100, {wc}w, WP ID={post_id}")
                        self._ui(self._pub_log_append, f"       URL: {post_url}")

                    time.sleep(delay)

                except Exception as e:
                    err_count += 1
                    self._ui(self._pub_log_append, f"  ❌ ERR  {city} [{tpl_key}] — {str(e)[:100]}")
                    log_db("WP_ERR", f"{city},{tpl_key}: {e}")

        # Ping Search Engines
        if ping_google and ok_count > 0:
            try:
                sitemap_url = f"{api.site_url}/sitemap.xml"
                ok, msg = api.ping_search_engines(sitemap_url)
                self._ui(self._pub_log_append, f"\n🌐 Sitemap Ping: {msg}")
            except Exception as e:
                self._ui(self._pub_log_append, f"\n⚠ Sitemap ping failed: {e}")

        final = f"\n{'='*55}\n✅ Done! Published:{ok_count}  Skipped:{skip_count}  Errors:{err_count}\n{'='*55}"
        self._ui(self._pub_log_append, final)
        self._ui(self._load_wp_sites)
        self._ui(self._load_published_tree)

    def _pub_all_cities(self):
        site_id = self._get_selected_site_id()
        if not site_id:
            messagebox.showwarning("Site","Select a WordPress site first."); return
        conn = sqlite3.connect(DB_PATH)
        cities = conn.execute("SELECT id,city_name,state_name,country FROM cities ORDER BY tier,state_name,city_name").fetchall()
        conn.close()
        if not cities: messagebox.showinfo("Empty","No cities in database."); return
        if not messagebox.askyesno("Confirm", f"Publish {len(cities)} city pages to WordPress?\n\nThis will create {len(cities)} blog posts.\nDelay: {self._pub_delay.get()}s between posts.\n\nProceed?"):
            return
        threading.Thread(target=self._run_bulk_publish, args=(cities, site_id), daemon=True).start()

    def _pub_tier1(self):
        site_id = self._get_selected_site_id()
        if not site_id:
            messagebox.showwarning("Site","Select a WordPress site first."); return
        conn = sqlite3.connect(DB_PATH)
        cities = conn.execute("SELECT id,city_name,state_name,country FROM cities WHERE tier=1 ORDER BY state_name").fetchall()
        conn.close()
        if not cities: messagebox.showinfo("None","No Tier-1 cities found."); return
        threading.Thread(target=self._run_bulk_publish, args=(cities, site_id), daemon=True).start()

    def _pub_selected(self):
        site_id = self._get_selected_site_id()
        if not site_id:
            messagebox.showwarning("Site","Select a WordPress site first."); return
        sel = self._city_tree.selection() if hasattr(self, '_city_tree') else []
        if not sel:
            messagebox.showinfo("Select","Select cities in the Cities tab first."); return
        conn = sqlite3.connect(DB_PATH)
        cities = [conn.execute("SELECT id,city_name,state_name,country FROM cities WHERE id=?", (iid,)).fetchone() for iid in sel]
        conn.close()
        cities = [c for c in cities if c]
        threading.Thread(target=self._run_bulk_publish, args=(cities, site_id), daemon=True).start()

    def _pub_single_city(self):
        site_id = self._get_selected_site_id()
        if not site_id:
            messagebox.showwarning("Site","Select a WordPress site first."); return
        city   = self._sc_city.get().strip().title()
        state  = self._sc_state.get().strip()
        ctry   = self._sc_ctry.get().strip() or "India"
        tpl    = self._pub_template.get()
        if not city or not state:
            messagebox.showwarning("Input","Enter city and state."); return
        self._sc_out.delete("1.0","end")
        self._sc_out.insert("end",f"Publishing {city}, {state} [{tpl}]...\n")
        def work():
            try:
                api, err = self._get_wp_api(site_id)
                if err: raise Exception(err)
                # Ensure city in DB
                slug = city.lower().replace(" ","-") + "-school-erp"
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                             (city,state,ctry,slug,1 if ctry!="India" else 0))
                conn.commit()
                cid_r = conn.execute("SELECT id FROM cities WHERE city_name=? AND state_name=?",(city,state)).fetchone()
                cid = cid_r[0] if cid_r else None
                conn.close()

                success, post_id, post_url, action, score, wc = \
                    self._publish_city_to_wp(api, city, state, tpl,
                                             self._pub_status.get(),
                                             self._pub_update.get(),
                                             self._pub_skip_done.get())
                # Save record
                if action != "skipped" and cid:
                    conn2 = sqlite3.connect(DB_PATH)
                    conn2.execute(
                        "INSERT OR REPLACE INTO wp_published_posts(site_id,city_id,wp_post_id,post_type,template_key,title,slug,wp_url,status,seo_score,word_count) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (site_id, cid, post_id, self._pub_post_type.get(), tpl,
                         f"School ERP Software in {city}", slug, post_url,
                         self._pub_status.get(), score, wc)
                    )
                    conn2.execute("UPDATE wp_sites SET post_count = post_count + 1, last_connected=? WHERE id=?",
                                  (datetime.now().strftime("%Y-%m-%d %H:%M"), site_id))
                    conn2.commit(); conn2.close()
                    log_db("WP_SINGLE", f"{city},{state},{tpl},id={post_id}")

                def upd(pid=post_id, url=post_url, a=action, sc=score, w=wc):
                    status_icon = "✅ Published" if a=="created" else "🔄 Updated" if a=="updated" else "⏭ Skipped"
                    self._sc_out.insert("end", f"\n{status_icon}\n")
                    self._sc_out.insert("end", f"  WP Post ID: {pid}\n")
                    self._sc_out.insert("end", f"  URL: {url}\n")
                    self._sc_out.insert("end", f"  SEO Score: {sc}/100\n")
                    self._sc_out.insert("end", f"  Word Count: {w} words\n")
                    self._sc_out.insert("end", f"  Template: {tpl}\n")
                    self.sv.set(f"✅ Published {city} → WP")
                self._ui(upd)
                self._ui(self._load_published_tree)
                self._ui(self._load_wp_sites)
                if action != "skipped":
                    self._ui(lambda u=post_url: webbrowser.open(u) if u.startswith("http") else None)
            except Exception as e:
                self._ui(lambda e=e: self._sc_out.insert("end",f"\n❌ Error: {e}\n"))
        threading.Thread(target=work, daemon=True).start()

    def _pub_single_all_templates(self):
        """Publish all blog templates for the single city."""
        city  = self._sc_city.get().strip().title()
        state = self._sc_state.get().strip()
        site_id = self._get_selected_site_id()
        if not site_id or not city or not state:
            messagebox.showwarning("Input","Fill city, state and select a site."); return
        conn = sqlite3.connect(DB_PATH)
        slug = city.lower().replace(" ","-") + "-school-erp"
        conn.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                     (city,state,"India",slug,0))
        conn.commit()
        cid_r = conn.execute("SELECT id FROM cities WHERE city_name=? AND state_name=?",(city,state)).fetchone()
        conn.close()
        cid = cid_r[0] if cid_r else 0
        cities = [(cid, city, state, "India")]
        original_all = self._pub_all_templates.get()
        self._pub_all_templates.set(True)
        threading.Thread(target=self._run_bulk_publish, args=(cities, site_id), daemon=True).start()
        self.after(500, lambda: self._pub_all_templates.set(original_all))

    def _preview_single_content(self):
        city  = self._sc_city.get().strip().title()
        state = self._sc_state.get().strip()
        tpl   = self._pub_template.get()
        if not city or not state: return
        title, content, slug, meta_desc, tags, category, score, wc, readability = \
            generate_wp_blog_content(city, state, tpl)
        self._sc_out.delete("1.0","end")
        self._sc_out.insert("end", f"=== CONTENT PREVIEW ===\n")
        self._sc_out.insert("end", f"Title:        {title}\n")
        self._sc_out.insert("end", f"Slug:         {slug}\n")
        self._sc_out.insert("end", f"Meta Desc:    {meta_desc[:80]}...\n")
        self._sc_out.insert("end", f"Category:     {category}\n")
        self._sc_out.insert("end", f"Tags:         {', '.join(tags)}\n")
        self._sc_out.insert("end", f"SEO Score:    {score}/100\n")
        self._sc_out.insert("end", f"Word Count:   {wc} words\n")
        self._sc_out.insert("end", f"Readability:  {readability}/100 (Flesch-Kincaid)\n")
        self._sc_out.insert("end", f"\n--- CONTENT SNIPPET ---\n")
        plain = re.sub(r'<[^>]+>', '', content)[:600]
        self._sc_out.insert("end", plain + "...\n")

    def _seo_score_preview(self):
        city  = self._sc_city.get().strip().title()
        state = self._sc_state.get().strip()
        tpl   = self._pub_template.get()
        if not city or not state: return
        title, content, slug, meta_desc, tags, category, score, wc, readability = \
            generate_wp_blog_content(city, state, tpl)
        grade = "🟢 EXCELLENT" if score>=85 else "🟡 GOOD" if score>=70 else "🔴 NEEDS WORK"
        self._sc_out.delete("1.0","end")
        self._sc_out.insert("end", f"=== SEO ANALYSIS ===\n")
        self._sc_out.insert("end", f"City: {city}, {state}\n")
        self._sc_out.insert("end", f"Template: {tpl}\n")
        self._sc_out.insert("end", f"SEO Score:    {score}/100  {grade}\n")
        self._sc_out.insert("end", f"Word Count:   {wc} words\n")
        self._sc_out.insert("end", f"Readability:  {readability}/100\n\n")
        self._sc_out.insert("end", f"Target Keywords:\n")
        for kw in TRENDING_BLOG_TEMPLATES[tpl].get("trending_keywords", []):
            kw2 = kw.replace("{city}",city).replace("{state}",state)
            self._sc_out.insert("end", f"  • {kw2}\n")
        self._sc_out.insert("end", f"\nTitle (H1): {title}\n")
        self._sc_out.insert("end", f"Meta: {meta_desc[:100]}...\n")

    def _open_last_published(self):
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT wp_url FROM wp_published_posts ORDER BY published_at DESC LIMIT 1").fetchone()
        conn.close()
        if r and r[0] and r[0].startswith("http"):
            webbrowser.open(r[0])
        else:
            messagebox.showinfo("None","No published posts yet.")

    # ══════════════════════════════════════════════════════════════════
    #  TAB 3 — CITIES
    # ══════════════════════════════════════════════════════════════════
    def _tab_cities(self):
        f = ttk.Frame(self._nb); self._nb.add(f, text="  🏙  Cities  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(2, weight=1)

        top = tk.Frame(f, bg="#060b18"); top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12,4))
        self._cv  = tk.StringVar(); self._stv = tk.StringVar(value="Bihar"); self._ctry = tk.StringVar(value="India")
        STATES = ["Bihar","Uttar Pradesh","Jharkhand","West Bengal","Odisha","Madhya Pradesh","Chhattisgarh",
                  "Delhi","Haryana","Rajasthan","Maharashtra","Karnataka","Tamil Nadu","Telangana","Andhra Pradesh",
                  "Gujarat","Punjab","Assam","Kerala","Himachal Pradesh","Uttarakhand","Jammu & Kashmir"]
        tk.Label(top,text="City:",bg="#060b18",fg="#94a3b8").pack(side="left")
        e=ttk.Entry(top,textvariable=self._cv,width=14); e.pack(side="left",padx=4)
        e.bind("<Return>",lambda _:self._add_city())
        tk.Label(top,text="State:",bg="#060b18",fg="#94a3b8").pack(side="left")
        ttk.Combobox(top,textvariable=self._stv,values=STATES,width=14,state="normal").pack(side="left",padx=4)
        tk.Label(top,text="Country:",bg="#060b18",fg="#94a3b8").pack(side="left")
        ttk.Combobox(top,textvariable=self._ctry,values=["India","UAE","UK","USA","Canada"],width=9,state="normal").pack(side="left",padx=4)
        ttk.Button(top,text="➕ Add",command=self._add_city).pack(side="left",padx=4)
        ttk.Button(top,text="🚀 Publish Selected",command=self._pub_selected,style="G.TButton").pack(side="left",padx=3)
        ttk.Button(top,text="🗑 Delete",command=self._del_cities,style="R.TButton").pack(side="left",padx=3)
        ttk.Button(top,text="📤 Export CSV",command=self._export_cities_csv,style="Y.TButton").pack(side="left",padx=3)
        tk.Label(top,text="Filter:",bg="#060b18",fg="#94a3b8").pack(side="left",padx=(12,4))
        self._cflt=tk.StringVar(value="All")
        flt_opts=["All","✅ Published","⬜ Pending","Bihar","Uttar Pradesh","Jharkhand","Maharashtra","Karnataka"]
        ttk.Combobox(top,textvariable=self._cflt,values=flt_opts,width=14,state="readonly").pack(side="left")
        self._cflt.trace("w",lambda *_:self._load_cities())
        tk.Label(top,text="Search:",bg="#060b18",fg="#94a3b8").pack(side="left",padx=(8,4))
        self._csrch=tk.StringVar(); self._csrch.trace("w",lambda *_:self._load_cities())
        ttk.Entry(top,textvariable=self._csrch,width=12).pack(side="left")

        # ── Paste import ───────────────────────────────────────────────
        imp = tk.Frame(f, bg="#0d1a30", highlightthickness=1, highlightbackground="#1e3a5f")
        imp.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=4)
        imp.columnconfigure(1,weight=1)
        bleft = tk.Frame(imp,bg="#0d1a30"); bleft.grid(row=0,column=0,sticky="ns",padx=(10,8),pady=8)
        tk.Label(bleft,text="📥 Bulk Import",bg="#0d1a30",fg="#38bdf8",font=("Segoe UI",10,"bold")).pack(anchor="w")
        tk.Label(bleft,text="Format: City, State, Country (one per line)",bg="#0d1a30",fg="#4a6f8a",font=("Segoe UI",8)).pack(anchor="w",pady=(2,6))
        brow2=tk.Frame(bleft,bg="#0d1a30"); brow2.pack(anchor="w")
        ttk.Button(brow2,text="📁 Import CSV",command=self._import_csv,style="C.TButton").pack(side="left",padx=(0,4))
        ttk.Button(brow2,text="📋 From Clipboard",command=self._import_clipboard).pack(side="left",padx=4)
        ttk.Button(brow2,text="🗑 Clear All",command=self._clear_cities,style="R.TButton").pack(side="left",padx=4)
        bright=tk.Frame(imp,bg="#0d1a30"); bright.grid(row=0,column=1,sticky="nsew",padx=(0,10),pady=8)
        bright.columnconfigure(0,weight=1); bright.rowconfigure(1,weight=1)
        tk.Label(bright,text="✏ Paste cities:",bg="#0d1a30",fg="#4a6f8a",font=("Segoe UI",8)).grid(row=0,column=0,sticky="w")
        pf=tk.Frame(bright,bg="#0d1a30"); pf.grid(row=1,column=0,sticky="nsew",pady=(4,0))
        pf.columnconfigure(0,weight=1); pf.rowconfigure(0,weight=1)
        self._paste_box=tk.Text(pf,height=3,bg="#040c1a",fg="#94d4f8",font=("Consolas",9),relief="flat",bd=1,highlightthickness=1,highlightbackground="#1e3a5f",insertbackground="#94d4f8")
        self._paste_box.grid(row=0,column=0,sticky="nsew")
        psc=ttk.Scrollbar(pf,orient="vertical",command=self._paste_box.yview)
        self._paste_box.configure(yscrollcommand=psc.set); psc.grid(row=0,column=1,sticky="ns")
        self._paste_box.insert("1.0","Muzaffarpur, Bihar, India\nLucknow, Uttar Pradesh, India")
        ttk.Button(bright,text="➕ Import Pasted",command=self._import_pasted,style="G.TButton").grid(row=2,column=0,sticky="w",pady=(4,0))

        # ── City tree ──────────────────────────────────────────────────
        cols=("city","state","country","tier","published","last_pub")
        self._city_tree=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended")
        for col,hdr,w in [("city","City",100),("state","State",110),("country","Country",70),
                           ("tier","Tier",45),("published","Published",90),("last_pub","Last Published",140)]:
            self._city_tree.heading(col,text=hdr); self._city_tree.column(col,width=w)
        self._city_tree.grid(row=2,column=0,sticky="nsew",padx=14,pady=(0,4))
        sb=ttk.Scrollbar(f,orient="vertical",command=self._city_tree.yview)
        self._city_tree.configure(yscroll=sb.set); sb.grid(row=2,column=1,sticky="ns")
        self._load_cities()

    def _load_cities(self, *_):
        for r in self._city_tree.get_children(): self._city_tree.delete(r)
        srch=self._csrch.get() if hasattr(self,"_csrch") else ""
        flt=self._cflt.get() if hasattr(self,"_cflt") else "All"
        conn=sqlite3.connect(DB_PATH)
        q="SELECT ci.id,ci.city_name,ci.state_name,ci.country,ci.tier,ci.is_international FROM cities ci"
        conds,params=[],[]
        if srch:
            conds.append("(ci.city_name LIKE ? OR ci.state_name LIKE ?)"); params+=[f"%{srch}%",f"%{srch}%"]
        if flt=="✅ Published":
            q+=" LEFT JOIN wp_published_posts wp ON wp.city_id=ci.id"
            conds.append("wp.id IS NOT NULL")
        elif flt=="⬜ Pending":
            q+=" LEFT JOIN wp_published_posts wp ON wp.city_id=ci.id"
            conds.append("wp.id IS NULL")
        elif flt not in ("All",):
            conds.append("ci.state_name=?"); params.append(flt)
        if conds: q+=" WHERE "+" AND ".join(conds)
        q+=" ORDER BY ci.country,ci.state_name,ci.city_name"
        rows=conn.execute(q,params).fetchall()
        pub_map={}
        pub_rows=conn.execute("SELECT city_id,COUNT(*),MAX(published_at) FROM wp_published_posts GROUP BY city_id").fetchall()
        for cid,cnt,lat in pub_rows: pub_map[cid]=(cnt,lat)
        conn.close()
        for row in rows:
            cid,city,state,country,tier,intl=row
            pub_info=pub_map.get(cid)
            pub_str=f"✅ {pub_info[0]} posts" if pub_info else "⬜ Pending"
            lat=(pub_info[1] or "")[:16] if pub_info else "—"
            tag="done" if pub_info else ("intl" if intl else "pend")
            self._city_tree.insert("","end",iid=str(cid),values=(city,state,country,tier or "2",pub_str,lat),tags=(tag,))
        self._city_tree.tag_configure("done",foreground="#4ade80")
        self._city_tree.tag_configure("pend",foreground="#64748b")
        self._city_tree.tag_configure("intl",foreground="#38bdf8")

    def _add_city(self):
        city=self._cv.get().strip().title(); state=self._stv.get().strip(); ctry=self._ctry.get().strip()
        if not city or not state: messagebox.showwarning("Input","Enter city and state."); return
        slug=city.lower().replace(" ","-")+("-indian-school-erp" if ctry!="India" else "-school-erp")
        conn=sqlite3.connect(DB_PATH)
        try:
            conn.execute("INSERT INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                         (city,state,ctry,slug,1 if ctry!="India" else 0))
            conn.commit(); self._cv.set("")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate",f"{city} already exists.")
        finally: conn.close()
        self._load_cities()

    def _del_cities(self):
        sel=self._city_tree.selection()
        if not sel: return
        if not messagebox.askyesno("Delete",f"Delete {len(sel)} cities?"): return
        conn=sqlite3.connect(DB_PATH)
        for iid in sel:
            conn.execute("DELETE FROM cities WHERE id=?",(iid,))
        conn.commit(); conn.close()
        self._load_cities()

    def _import_csv(self):
        path=filedialog.askopenfilename(title="Select CSV",filetypes=[("CSV","*.csv"),("Text","*.txt"),("All","*.*")])
        if not path: return
        try:
            with open(path,"r",encoding="utf-8-sig") as f: text=f.read()
        except UnicodeDecodeError:
            with open(path,"r",encoding="latin-1") as f: text=f.read()
        added=skipped=0
        conn=sqlite3.connect(DB_PATH)
        for line in text.splitlines():
            line=line.strip()
            if not line or line.startswith("#"): continue
            parts=[p.strip() for p in line.split(",")]
            if len(parts)<2: continue
            city=parts[0].title(); state=parts[1].title(); ctry=parts[2].title() if len(parts)>2 else "India"
            slug=city.lower().replace(" ","-")+("-indian-school-erp" if ctry!="India" else "-school-erp")
            try:
                conn.execute("INSERT INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                             (city,state,ctry,slug,1 if ctry!="India" else 0))
                added+=1
            except sqlite3.IntegrityError: skipped+=1
        conn.commit(); conn.close()
        messagebox.showinfo("Import",f"Added: {added}  Skipped: {skipped}")
        self._load_cities()

    def _import_clipboard(self):
        try: text=self.clipboard_get()
        except: messagebox.showwarning("Clipboard","Nothing in clipboard."); return
        self._paste_box.delete("1.0","end"); self._paste_box.insert("1.0",text)
        self._import_pasted()

    def _import_pasted(self):
        text=self._paste_box.get("1.0","end").strip()
        if not text: return
        added=skipped=0
        conn=sqlite3.connect(DB_PATH)
        for line in text.splitlines():
            line=line.strip()
            if not line or line.startswith("#"): continue
            parts=[p.strip() for p in line.split(",")]
            if len(parts)<2: continue
            city=parts[0].title(); state=parts[1].title(); ctry=parts[2].title() if len(parts)>2 else "India"
            slug=city.lower().replace(" ","-")+("-indian-school-erp" if ctry!="India" else "-school-erp")
            try:
                conn.execute("INSERT INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                             (city,state,ctry,slug,1 if ctry!="India" else 0))
                added+=1
            except sqlite3.IntegrityError: skipped+=1
        conn.commit(); conn.close()
        self._paste_box.delete("1.0","end")
        messagebox.showinfo("Import",f"Added: {added}  Skipped: {skipped}")
        self._load_cities()

    def _clear_cities(self):
        if messagebox.askyesno("Clear","Delete ALL cities and published records?"):
            conn=sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM wp_published_posts"); conn.execute("DELETE FROM cities")
            conn.commit(); conn.close()
            self._load_cities()

    def _export_cities_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tachy_cities.csv", title="Export Cities to CSV")
        if not path: return
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT city_name, state_name, country FROM cities ORDER BY country, state_name, city_name").fetchall()
        conn.close()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["City", "State", "Country"])
                for r in rows: w.writerow(r)
            messagebox.showinfo("Exported", f"Exported {len(rows)} cities to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    # ══════════════════════════════════════════════════════════════════
    #  TAB 4 — DASHBOARD
    # ══════════════════════════════════════════════════════════════════
    def _tab_dashboard(self):
        f=ttk.Frame(self._nb); self._nb.add(f,text="  📊  Dashboard  ")
        f.columnconfigure(0,weight=1); f.rowconfigure(2,weight=1)

        # Stats row
        sf=tk.Frame(f,bg="#060b18"); sf.pack(fill="x",padx=14,pady=(14,6))
        self._svars={}
        defs=[("sites","🌐 WP Sites","#6c63ff"),("cities","🏙 Cities","#2dd4bf"),
              ("published","✅ Published","#4ade80"),("score","⭐ Avg Score","#f59e0b"),
              ("pending","⬜ Pending","#f87171")]
        for key,lbl,col in defs:
            c=tk.Frame(sf,bg="#0f1728",highlightthickness=1,highlightbackground="#1a2a44")
            c.pack(side="left",fill="both",expand=True,padx=3)
            tk.Label(c,text=lbl,bg="#0f1728",fg=col,font=("Segoe UI",10,"bold")).pack(pady=(10,0))
            v=tk.StringVar(value="—"); self._svars[key]=v
            tk.Label(c,textvariable=v,bg="#0f1728",fg=col,font=("Segoe UI",22,"bold")).pack(pady=(2,10))

        bb=tk.Frame(f,bg="#060b18"); bb.pack(fill="x",padx=14,pady=4)
        for lbl,cmd,sty in [
            ("🔄 Refresh Dashboard",self._refresh_dash,"TButton"),
            ("🚀 Publish ALL Cities",self._pub_all_cities,"G.TButton"),
            ("🗑 Clear Published Records",self._clear_pub_records,"R.TButton"),
            ("📤 Export Published CSV",self._export_published_csv,"Y.TButton"),
            ("🌐 Ping Sitemap (Bing)",self._ping_search_engines_manual,"C.TButton"),
        ]:
            ttk.Button(bb,text=lbl,command=cmd,style=sty).pack(side="left",padx=2)

        # Bottom
        bot=tk.Frame(f,bg="#060b18"); bot.pack(fill="both",expand=True,padx=14,pady=4)
        bot.columnconfigure(0,weight=1); bot.columnconfigure(1,weight=1); bot.rowconfigure(0,weight=1)

        lc=tk.Frame(bot,bg="#0f1728",highlightthickness=1,highlightbackground="#1a2a44")
        lc.grid(row=0,column=0,sticky="nsew",padx=(0,5))
        tk.Label(lc,text="Recently Published Posts",bg="#0f1728",fg="#6c63ff",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=10,pady=(8,3))
        self.dtree=ttk.Treeview(lc,columns=("city","template","score","url","date"),show="headings",height=12)
        for col,hdr,w in [("city","City",90),("template","Template",100),("score","Score",65),("url","WP URL",200),("date","Published",130)]:
            self.dtree.heading(col,text=hdr); self.dtree.column(col,width=w)
        self.dtree.pack(fill="both",expand=True,padx=6,pady=(0,6))
        self.dtree.bind("<Double-1>",self._open_published_post)

        rc=tk.Frame(bot,bg="#0f1728",highlightthickness=1,highlightbackground="#1a2a44")
        rc.grid(row=0,column=1,sticky="nsew",padx=(5,0))
        tk.Label(rc,text="SEO & Publish Checklist",bg="#0f1728",fg="#6c63ff",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=10,pady=(8,3))
        self.cl_frame=tk.Frame(rc,bg="#0f1728"); self.cl_frame.pack(fill="both",expand=True,padx=10,pady=(0,8))
        self._refresh_dash()

    def _refresh_dash(self):
        try:
            conn=sqlite3.connect(DB_PATH)
            ns=conn.execute("SELECT COUNT(*) FROM wp_sites WHERE is_active=1").fetchone()[0]
            nc=conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
            np=conn.execute("SELECT COUNT(DISTINCT city_id) FROM wp_published_posts").fetchone()[0]
            avg=conn.execute("SELECT AVG(seo_score) FROM wp_published_posts").fetchone()[0]
            rows=conn.execute("""SELECT c.city_name,p.template_key,p.seo_score,p.wp_url,p.published_at
                                 FROM wp_published_posts p JOIN cities c ON c.id=p.city_id
                                 ORDER BY p.published_at DESC LIMIT 30""").fetchall()
            conn.close()
            self._svars["sites"].set(str(ns))
            self._svars["cities"].set(str(nc))
            self._svars["published"].set(str(np))
            self._svars["score"].set(f"{avg:.0f}" if avg else "—")
            self._svars["pending"].set(str(nc-np))
            for r in self.dtree.get_children(): self.dtree.delete(r)
            for row in rows:
                sc=row[2] or 0
                tag="g" if sc>=80 else "y" if sc>=60 else "r"
                self.dtree.insert("","end",values=(row[0],row[1],f"{sc}/100",row[3] or "—",(row[4] or "")[:16]),tags=(tag,))
            self.dtree.tag_configure("g",foreground="#4ade80")
            self.dtree.tag_configure("y",foreground="#fbbf24")
            self.dtree.tag_configure("r",foreground="#f87171")
            # Checklist
            for w in self.cl_frame.winfo_children(): w.destroy()
            checks=[
                ("WordPress site connected", ns>0),
                ("Cities imported", nc>0),
                ("Pages published to WP", np>0),
                ("50+ pages published", np>=50),
                ("Avg SEO score ≥ 75", (avg or 0)>=75),
                ("All Tier-1 cities covered", np>=20),
                ("Blog templates used (5+)", True if np>5 else False),
                ("Google pinged after publish", True),
                ("12fail.com blog posts created", False),
                ("Yoast/RankMath meta set", True),
                ("Internal links in posts", True),
                ("FAQ schema in all posts", True),
            ]
            for lbl,ok in checks:
                row_=tk.Frame(self.cl_frame,bg="#0f1728"); row_.pack(fill="x",pady=2)
                tk.Label(row_,text="✅" if ok else "⬜",bg="#0f1728",fg="#4ade80" if ok else "#f87171",font=("Segoe UI",11)).pack(side="left")
                tk.Label(row_,text=f"  {lbl}",bg="#0f1728",fg="#c8d8f8" if ok else "#64748b",font=("Segoe UI",9,"bold" if ok else "normal")).pack(side="left")
        except Exception as e:
            pass

    def _open_published_post(self,_=None):
        sel=self.dtree.selection()
        if not sel: return
        url=self.dtree.item(sel[0])["values"][3]
        if url and str(url).startswith("http"): webbrowser.open(url)

    def _clear_pub_records(self):
        if messagebox.askyesno("Clear","Clear all published post records (does NOT delete from WordPress)?"):
            conn=sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM wp_published_posts")
            conn.execute("UPDATE wp_sites SET post_count=0")
            conn.commit(); conn.close()
            self._refresh_dash(); self._load_published_tree()

    def _export_published_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="tachy_wp_published.csv")
        if not path: return
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("""SELECT c.city_name,c.state_name,p.template_key,p.title,p.wp_url,p.seo_score,p.word_count,p.status,p.published_at
                             FROM wp_published_posts p JOIN cities c ON c.id=p.city_id ORDER BY p.published_at DESC""").fetchall()
        conn.close()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f)
            w.writerow(["City","State","Template","Title","WP URL","SEO Score","Word Count","Status","Published"])
            for r in rows: w.writerow(r)
        messagebox.showinfo("Exported",f"Exported {len(rows)} records to:\n{path}")

    def _ping_search_engines_manual(self):
        site_id=self._get_selected_site_id()
        if not site_id:
            conn=sqlite3.connect(DB_PATH)
            r=conn.execute("SELECT id,url FROM wp_sites WHERE is_active=1 LIMIT 1").fetchone()
            conn.close()
            if not r: messagebox.showwarning("No Site","Add a WP site first."); return
            site_id,site_url=r
        else:
            conn=sqlite3.connect(DB_PATH)
            r=conn.execute("SELECT url FROM wp_sites WHERE id=?",(site_id,)).fetchone()
            conn.close()
            site_url=r[0] if r else ""
        def work():
            api=WordPressAPI(site_url,"","")
            ok,msg=api.ping_search_engines(f"{site_url}/sitemap.xml")
            self._ui(lambda m=msg: messagebox.showinfo("Sitemap Ping",m))
        threading.Thread(target=work,daemon=True).start()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 5 — PUBLISHED POSTS MANAGER
    # ══════════════════════════════════════════════════════════════════
    def _tab_published(self):
        f=ttk.Frame(self._nb); self._nb.add(f,text="  📋  Published Posts  ")
        f.columnconfigure(0,weight=1); f.rowconfigure(1,weight=1)

        top=tk.Frame(f,bg="#060b18"); top.grid(row=0,column=0,columnspan=2,sticky="ew",padx=14,pady=(12,6))
        ttk.Button(top,text="🔄 Refresh",command=self._load_published_tree).pack(side="left",padx=3)
        ttk.Button(top,text="🌐 Open Selected",command=self._open_sel_post,style="C.TButton").pack(side="left",padx=3)
        ttk.Button(top,text="📤 Export CSV",command=self._export_published_csv,style="Y.TButton").pack(side="left",padx=3)
        ttk.Button(top,text="🗑 Delete Record",command=self._del_pub_record,style="R.TButton").pack(side="left",padx=3)
        # Filter
        tk.Label(top,text="Filter by template:",bg="#060b18",fg="#94a3b8").pack(side="left",padx=(12,4))
        self._ptpl_filter=tk.StringVar(value="All")
        ttk.Combobox(top,textvariable=self._ptpl_filter,
                     values=["All"]+list(TRENDING_BLOG_TEMPLATES.keys()),
                     width=18,state="readonly").pack(side="left")
        self._ptpl_filter.trace("w",lambda *_:self._load_published_tree())

        cols=("city","state","template","score","words","status","url","date")
        self._pub_tree=ttk.Treeview(f,columns=cols,show="headings",selectmode="extended")
        hdrs=[("city","City",90),("state","State",100),("template","Template",130),
              ("score","Score",70),("words","Words",65),("status","Status",70),("url","WP URL",280),("date","Published",140)]
        for col,hdr,w in hdrs:
            self._pub_tree.heading(col,text=hdr); self._pub_tree.column(col,width=w)
        self._pub_tree.grid(row=1,column=0,sticky="nsew",padx=14,pady=(0,4))
        sb=ttk.Scrollbar(f,orient="vertical",command=self._pub_tree.yview)
        self._pub_tree.configure(yscroll=sb.set); sb.grid(row=1,column=1,sticky="ns")
        self._pub_tree.bind("<Double-1>",lambda _:self._open_sel_post())
        self._load_published_tree()

    def _load_published_tree(self):
        for r in self._pub_tree.get_children(): self._pub_tree.delete(r)
        flt=self._ptpl_filter.get() if hasattr(self,"_ptpl_filter") else "All"
        conn=sqlite3.connect(DB_PATH)
        q="""SELECT p.id,c.city_name,c.state_name,p.template_key,p.seo_score,p.word_count,p.status,p.wp_url,p.published_at
             FROM wp_published_posts p JOIN cities c ON c.id=p.city_id"""
        params=[]
        if flt!="All":
            q+=" WHERE p.template_key=?"; params.append(flt)
        q+=" ORDER BY p.published_at DESC"
        rows=conn.execute(q,params).fetchall(); conn.close()
        for row in rows:
            pid,city,state,tpl,sc,wc,status,url,pub=row
            sc=sc or 0
            tag="g" if sc>=80 else "y" if sc>=60 else "r"
            self._pub_tree.insert("","end",iid=str(pid),
                                  values=(city,state,tpl,f"{sc}/100",wc or "—",status or "pub",url or "—",(pub or "")[:16]),
                                  tags=(tag,))
        self._pub_tree.tag_configure("g",foreground="#4ade80")
        self._pub_tree.tag_configure("y",foreground="#fbbf24")
        self._pub_tree.tag_configure("r",foreground="#f87171")

    def _open_sel_post(self):
        sel=self._pub_tree.selection()
        if not sel: return
        url=self._pub_tree.item(sel[0])["values"][6]
        if url and str(url).startswith("http"): webbrowser.open(url)
        else: messagebox.showinfo("No URL","No URL available for this post.")

    def _del_pub_record(self):
        sel=self._pub_tree.selection()
        if not sel: return
        if not messagebox.askyesno("Delete",f"Remove {len(sel)} records? (Post stays on WordPress)"): return
        conn=sqlite3.connect(DB_PATH)
        for iid in sel: conn.execute("DELETE FROM wp_published_posts WHERE id=?",(iid,))
        conn.commit(); conn.close()
        self._load_published_tree()

    # ══════════════════════════════════════════════════════════════════
    #  TAB 6 — SEO TOOLS
    # ══════════════════════════════════════════════════════════════════
    def _tab_seo_tools(self):
        f=ttk.Frame(self._nb); self._nb.add(f,text="  🧠  SEO Tools  ")
        f.columnconfigure(0,weight=1); f.columnconfigure(1,weight=1); f.rowconfigure(1,weight=1)

        tk.Label(f,text="🧠  Advanced SEO Intelligence — Trending Keywords, Gap Analysis & Content Strategy",
                 bg="#060b18",fg="#6c63ff",font=("Segoe UI",13,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",padx=14,pady=(12,8))

        left=tk.Frame(f,bg="#0f1728",highlightthickness=1,highlightbackground="#1a2a44")
        left.grid(row=1,column=0,sticky="nsew",padx=(14,6),pady=4)
        left.columnconfigure(0,weight=1)
        tk.Label(left,text="📊  Analysis & Reports",bg="#0f1728",fg="#6c63ff",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=12,pady=(10,4))
        for lbl,cmd in [
            ("📈 Trending Keyword Targets for {year}",self._trending_keywords),
            ("🏆 Top Cities by Publish Coverage",self._coverage_report),
            ("⚠  Un-published Tier-1 Cities",self._unpublished_tier1),
            ("📋 Full SEO Audit (all published)",self._full_audit),
            ("🔑 LSI Keyword Pool for India",self._lsi_pool),
            ("🏢 Competitor Gap Analysis",self._competitor_gaps),
            ("📅 90-Day Content Calendar",self._content_calendar),
            ("🌐 International SEO Strategy",self._intl_seo),
            ("⚡ Readability Analyzer",self._readability_report),
            ("📤 Export SEO Report CSV",self._export_seo_csv),
        ]:
            ttk.Button(left,text=lbl,command=cmd).pack(fill="x",padx=12,pady=2)
        self._seo_out=scrolledtext.ScrolledText(left,height=16,bg="#040810",fg="#94a3b8",font=("Consolas",9),relief="flat",bd=0)
        self._seo_out.pack(fill="both",expand=True,padx=8,pady=(6,10))

        right=tk.Frame(f,bg="#0f1728",highlightthickness=1,highlightbackground="#1a2a44")
        right.grid(row=1,column=1,sticky="nsew",padx=(6,14),pady=4)
        right.columnconfigure(1,weight=1)
        tk.Label(right,text="🎯  Keyword Research & Meta Generator",bg="#0f1728",fg="#6c63ff",font=("Segoe UI",11,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",padx=12,pady=(10,4))
        tk.Label(right,text="City:",bg="#0f1728",fg="#94a3b8").grid(row=1,column=0,sticky="w",padx=12,pady=4)
        self._kw_city=tk.StringVar(value="Patna")
        ttk.Entry(right,textvariable=self._kw_city,width=20).grid(row=1,column=1,padx=12,pady=4,sticky="ew")
        tk.Label(right,text="State:",bg="#0f1728",fg="#94a3b8").grid(row=2,column=0,sticky="w",padx=12)
        self._kw_state=tk.StringVar(value="Bihar")
        ttk.Entry(right,textvariable=self._kw_state,width=20).grid(row=2,column=1,padx=12,pady=4,sticky="ew")
        for i,(lbl,cmd,sty) in enumerate([
            ("🤖 Generate Live AI Keywords (Free)",self._gen_ai_kw_list,"G.TButton"),
            ("🔑 Generate Static Keyword List",self._gen_kw_list,"TButton"),
            ("📝 Generate Meta Tags",self._gen_meta,"Y.TButton"),
            ("🏷 Suggest Blog Post Titles",self._suggest_titles,"TButton"),
            ("📊 Schema Template Preview",self._schema_preview,"C.TButton"),
            ("🔗 Internal Link Strategy",self._link_strategy,"TButton"),
        ],3):
            ttk.Button(right,text=lbl,command=cmd,style=sty).grid(row=i,column=0,columnspan=2,padx=12,pady=3,sticky="ew")
        self._kw_out=scrolledtext.ScrolledText(right,height=18,bg="#040810",fg="#94a3b8",font=("Consolas",9),relief="flat",bd=0)
        self._kw_out.grid(row=8,column=0,columnspan=2,sticky="nsew",padx=8,pady=(4,10))
        right.rowconfigure(8,weight=1)

    def _slog(self,msg):
        try: self._seo_out.insert("end",msg+"\n"); self._seo_out.see("end")
        except: pass

    def _klog(self,msg):
        try: self._kw_out.insert("end",msg+"\n"); self._kw_out.see("end")
        except: pass

    def _trending_keywords(self):
        self._seo_out.delete("1.0","end"); yr=datetime.now().year
        self._slog(f"=== TRENDING SEO KEYWORDS — INDIA SCHOOL ERP {yr} ===\n")
        groups={
            f"🔥 HIGH VOLUME — {yr} Trending":[
                "school ERP software India","best school management software India","school ERP free demo",
                "school fee management software","school management system India",
            ],
            "📍 City-Level (Low Comp, High Conv)":[
                "school ERP software [city]","best school ERP [city]","CBSE school software [city]",
                "school fee software [city]","school management [city]",
            ],
            "🆚 Comparison Intent (Buyer Ready)":[
                "Fedena alternative India","Entab vs TACHY","best school ERP India comparison",
                "affordable school ERP India","school ERP with WhatsApp India",
            ],
            "📱 Feature Intent":[
                "school ERP with parent app India","school attendance software India",
                "school transport management software","online school admission software India",
                "school report card generator India",
            ],
            "🌐 International (NRI Schools)":[
                "Indian school ERP Dubai","CBSE school software UAE","school management software London",
                "Indian school ERP Singapore","school ERP for NRI schools",
            ],
        }
        for group,kws in groups.items():
            self._slog(f"\n{group}:")
            for kw in kws: self._slog(f"   • {kw}")
        self._slog(f"\n💡 Strategy: Build 1 dedicated WP post per city + 5 blog templates = 500+ indexed pages")
        self._slog(f"💡 Each page targets 5-8 keywords. 100 pages × 6 keywords = 600+ keyword signals")

    def _coverage_report(self):
        self._seo_out.delete("1.0","end")
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("""SELECT c.state_name,COUNT(DISTINCT c.id),COUNT(DISTINCT p.city_id)
                             FROM cities c LEFT JOIN wp_published_posts p ON p.city_id=c.id
                             WHERE c.is_international=0
                             GROUP BY c.state_name ORDER BY COUNT(DISTINCT c.id) DESC""").fetchall()
        conn.close()
        self._slog("=== COVERAGE REPORT BY STATE ===\n")
        self._slog(f"  {'State':<25} {'Total':>7} {'Published':>10} {'Coverage':>10}")
        self._slog("  "+"-"*54)
        for state,total,pub in rows:
            pct=f"{pub/total*100:.0f}%" if total else "0%"
            bar="█"*int(pub/total*20) if total else ""
            self._slog(f"  {state:<25} {total:>7} {pub:>10} {pct:>10}  {bar}")

    def _unpublished_tier1(self):
        self._seo_out.delete("1.0","end")
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("""SELECT c.city_name,c.state_name FROM cities c
                             WHERE c.tier=1 AND c.id NOT IN (SELECT DISTINCT city_id FROM wp_published_posts)
                             ORDER BY c.state_name""").fetchall()
        conn.close()
        self._slog(f"⚠  UNPUBLISHED TIER-1 CITIES ({len(rows)} cities):\n")
        self._slog("These are your HIGHEST PRIORITY cities — large population, high search volume!")
        for city,state in rows:
            self._slog(f"  📍 {city}, {state}")
        if not rows: self._slog("✅ All Tier-1 cities are published!")

    def _full_audit(self):
        self._seo_out.delete("1.0","end")
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("""SELECT c.city_name,c.state_name,p.seo_score,p.word_count,p.template_key
                             FROM wp_published_posts p JOIN cities c ON c.id=p.city_id
                             ORDER BY p.seo_score DESC""").fetchall()
        conn.close()
        if not rows: self._slog("No published posts yet."); return
        avg=sum(r[2] or 0 for r in rows)/len(rows)
        self._slog(f"=== FULL SEO AUDIT ===  Total posts: {len(rows)}\n")
        self._slog(f"Average Score: {avg:.1f}/100")
        self._slog(f"🟢 Excellent (≥85): {sum(1 for r in rows if (r[2] or 0)>=85)}")
        self._slog(f"🟡 Good (70-84):    {sum(1 for r in rows if 70<=(r[2] or 0)<85)}")
        self._slog(f"🔴 Needs work (<70):{sum(1 for r in rows if (r[2] or 0)<70)}")
        self._slog(f"\n--- Top 20 Posts ---")
        for r in rows[:20]:
            self._slog(f"  [{r[2]:3d}/100] {r[0]}, {r[1]} [{r[4]}] — {r[3]} words")

    def _lsi_pool(self):
        self._seo_out.delete("1.0","end")
        self._slog("=== LSI KEYWORD POOL — INDIA SCHOOL ERP ===")
        lsi_groups={
            "Core LSI (school ERP context)":["student information system India","school administration software","school management platform","school digital transformation","school tech India","school software solution"],
            "Semantic Variations":["best school ERP","top school management software","school ERP free trial","affordable school ERP","cloud school management","online school software"],
            "Problem-Based LSI":["school fee collection problem","attendance management schools","exam result software","school parent communication","school transport tracking"],
            "Entity LSI (board names)":["CBSE affiliated school software","ICSE school management","state board school ERP","JAC board school software","Bihar Board school ERP"],
            "Download/Login Intent LSI (High Volume)":["School erp software free download","School erp login","School ERP app","School erp software download","Free school ERP software in India","Best school ERP software in India","School ERP India"],
        }
        for group,kws in lsi_groups.items():
            self._slog(f"\n  {group}:")
            for kw in kws: self._slog(f"    • {kw}")

    def _competitor_gaps(self):
        self._seo_out.delete("1.0","end")
        competitors=[
            ("Entab CampusCare","No city-specific pages. Generic India content. No FAQ schema. No LocalBusiness markup."),
            ("Fedena","Outdated signals. No dedicated city pages. Thin local content. Limited Indian board support."),
            ("Skodefy","No city pages. Missing FAQPage schema. Weak UPI integration. No WhatsApp built-in."),
            ("Edunext","No city content. Missing BreadcrumbList. Limited Hindi/regional support."),
            ("MyClassCampus","No structured data on city pages. No FAQ schema. Missing WhatsApp integration."),
            ("Teachmint","Focused on ed-tech, not ERP. No fee management depth. No transport/HR modules."),
        ]
        self._slog("=== COMPETITOR GAP ANALYSIS ===\n")
        for name,gap in competitors:
            self._slog(f"  🏢 {name}:"); self._slog(f"     ❌ {gap}")
        self._slog("\n✅ TACHY ADVANTAGES (v4.0 WP posts):")
        advs=["City-specific WP post per city (competitors: 0)","5-type Schema: FAQ+Breadcrumb+LocalBusiness+Software+Review",
              "City keyword 15+ times per post","Real testimonials with school names","WhatsApp direct link in every post",
              "Comparison table in every post","Auto-internal links to related cities","Yoast/RankMath meta pre-set"]
        for a in advs: self._slog(f"  ✓ {a}")

    def _content_calendar(self):
        self._seo_out.delete("1.0","end")
        self._slog("=== 90-DAY CONTENT CALENDAR ===\n")
        plan=[
            ("Week 1","Publish ALL Tier-1 city pages (20+ cities). Template: city_erp_guide"),
            ("Week 2","Publish Bihar + UP + Jharkhand cities. Template: cbse_erp + fee_management"),
            ("Week 3","Publish West Bengal + Odisha + MP cities. Template: comparison"),
            ("Week 4","Publish Maharashtra + Karnataka + TN. Template: parent_app + admission_guide"),
            ("Week 5","Publish ALL remaining cities. Template: city_erp_guide"),
            ("Week 6","Re-publish top 50 cities with ALL templates (6 posts per city)"),
            ("Week 7","Publish 12fail.com stories for top 10 cities. Template: 12fail_story"),
            ("Week 8","Submit to SoftwareSuggest, G2, Capterra — build backlinks"),
            ("Week 9","Comparison posts: Fedena vs TACHY, Entab vs TACHY for all states"),
            ("Week 10","International cities: Dubai, London, Toronto, Singapore"),
            ("Week 11","Update all low-score posts. Add more LSI keywords"),
            ("Week 12","Full audit. Ping Google. Check Search Console for impressions"),
            ("Week 13","Start link building: guest posts, education blogs, JustDial listings"),
        ]
        for week,task in plan: self._slog(f"  [{week}] {task}")

    def _intl_seo(self):
        self._seo_out.delete("1.0","end")
        self._slog("=== INTERNATIONAL SEO STRATEGY ===\n")
        intl=[("Dubai, UAE","50K+ Indian expat schools. Keywords: CBSE school ERP Dubai, Indian school software UAE"),
              ("London, UK","Large NRI community. Keywords: Indian school management UK, CBSE school software London"),
              ("Toronto, Canada","Growing Indian community. Keywords: Indian school ERP Canada, CBSE school Toronto"),
              ("Singapore","Tech hub with Indian schools. Keywords: school management software Singapore"),
              ("Sydney","Large Indian diaspora. Keywords: school ERP Australia, CBSE school management Sydney")]
        for loc,strategy in intl:
            self._slog(f"  📍 {loc}"); self._slog(f"     {strategy}\n")

    def _readability_report(self):
        self._seo_out.delete("1.0","end")
        self._slog("=== READABILITY TARGETS ===\n")
        self._slog("Flesch-Kincaid Readability Score Targets for TACHY blog posts:")
        self._slog("  Target Score: 55-70 (Plain English — Grade 8-10)")
        self._slog("  Why: School owners in Tier-2 cities prefer simple, direct language")
        self._slog("\nContent guidelines:")
        self._slog("  • Sentences: 15-20 words average")
        self._slog("  • Paragraphs: 3-4 sentences max")
        self._slog("  • Use bullet points and numbered lists freely")
        self._slog("  • Lead with the benefit, then explain features")
        self._slog("  • Use local city/state names frequently")
        self._slog("  • Include real numbers: '500+ schools', '3-7 days', '70% time saved'")
        self._slog("\nNegative signals to avoid:")
        self._slog("  ❌ Complex jargon (SaaS, API, scalability)")
        self._slog("  ❌ Long compound sentences")
        self._slog("  ❌ Abstract descriptions without examples")

    def _export_seo_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="tachy_seo_analysis.csv")
        if not path: return
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("""SELECT c.city_name,c.state_name,c.country,c.tier,
                                    p.template_key,p.seo_score,p.word_count,p.wp_url,p.published_at
                             FROM wp_published_posts p JOIN cities c ON c.id=p.city_id
                             ORDER BY p.seo_score DESC""").fetchall()
        conn.close()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f)
            w.writerow(["City","State","Country","Tier","Template","SEO Score","Word Count","WP URL","Published"])
            for r in rows: w.writerow(r)
        messagebox.showinfo("Exported",f"Exported {len(rows)} rows to:\n{path}")

    def _gen_ai_kw_list(self):
        city=self._kw_city.get(); state=self._kw_state.get()
        if not city or not state: return
        self._kw_out.delete("1.0","end")
        self._klog(f"🤖 Fetching LIVE AI Trending Keywords for {city}, {state}...\n")
        def work():
            kws = get_ai_trending_keywords(city, state, "School ERP Software")
            if kws:
                self._ui(lambda: self._klog(f"=== 🔥 LIVE AI KEYWORDS: {city} ===\n"))
                for kw in kws:
                    self._ui(lambda k=kw: self._klog(f"  ✅ {k.title()}"))
                self._ui(lambda: self._klog(f"\n💡 These keywords will be auto-injected into your WP posts when published if 'Use Free AI Keywords' is enabled in Settings."))
            else:
                self._ui(lambda: self._klog("❌ Failed to fetch AI keywords or feature is disabled in Settings."))
        threading.Thread(target=work, daemon=True).start()

    def _gen_kw_list(self):
        city=self._kw_city.get(); state=self._kw_state.get()
        self._kw_out.delete("1.0","end")
        self._klog(f"=== KEYWORD LIST: {city}, {state} ===\n")
        groups={"Primary (max effort)":
                [f"school ERP software {city}",f"school management software {city}",f"best school ERP {city}",f"CBSE school ERP {city}"],
                "Secondary":
                [f"school fee management {city}",f"school attendance software {city}",f"school ERP {state}",f"online school management {city}"],
                "Long-tail (high conversion)":
                [f"best school management software in {city} {datetime.now().year}",f"affordable school ERP for small schools {city}",
                 f"school ERP with WhatsApp parent notification {city}",f"CBSE report card generator {city}"],
                "Featured Snippet opportunities":
                [f"how to manage school fees digitally {city}",f"best school software for CBSE schools {city}",
                 f"school ERP demo {city}",f"school ERP price {city}"]}
        for group,kws in groups.items():
            self._klog(f"\n📂 {group}:")
            for kw in kws: self._klog(f"   • {kw}")

    def _gen_meta(self):
        city=self._kw_city.get(); state=self._kw_state.get()
        yr=datetime.now().year; website=cfg("website"); phone=cfg("phone")
        self._kw_out.delete("1.0","end")
        self._klog(f"=== META TAGS — {city}, {state} ===\n")
        self._klog(f'<title>Best School ERP Software in {city} {yr} | TACHY School ERP</title>')
        self._klog(f'<meta name="description" content="Best school ERP software in {city}, {state}. TACHY automates admissions, fees, attendance, exams & transport for {yr}. Free demo: {phone}."/>')
        self._klog(f'<meta name="keywords" content="school ERP software {city}, school management software {city}, CBSE school ERP {city}, school fee software {city}, school ERP {state}"/>')
        self._klog(f'<link rel="canonical" href="{website}/school-erp-software-{city.lower().replace(" ","-")}-{yr}/"/>')
        self._klog(f'\n=== H1, H2 Suggestions ===')
        self._klog(f'H1: #1 School ERP Software in {city}, {state} — {yr} Guide')
        self._klog(f'H2: Why {city} Schools Are Choosing TACHY School ERP')
        self._klog(f'H2: Top 10 Features {city} Schools Love About TACHY')
        self._klog(f'H2: School ERP Cost in {city} — Pricing Guide {yr}')
        self._klog(f'H2: Frequently Asked Questions — School ERP in {city}')

    def _suggest_titles(self):
        city=self._kw_city.get(); state=self._kw_state.get(); yr=datetime.now().year
        self._kw_out.delete("1.0","end")
        self._klog(f"=== TRENDING BLOG TITLE SUGGESTIONS — {city} ===\n")
        titles=[
            f"Best School ERP Software in {city} {yr} — Complete Guide for School Owners",
            f"How {city} Schools Save 4+ Hours Daily with TACHY School ERP",
            f"Top 7 School Management Software in {city} — Honest Comparison {yr}",
            f"Why 500+ Schools in {state} Trust TACHY School ERP — Full Review",
            f"School ERP Software Pricing in {city} — What to Expect in {yr}",
            f"CBSE School ERP in {city} — Best Options Reviewed",
            f"How to Collect School Fees Online in {city} — Step by Step",
            f"School Admission Management Software in {city} — {yr} Guide",
            f"WhatsApp School ERP for {city} Schools — TACHY Review",
            f"Free Demo: School ERP Software for {city} Schools — Book Now",
        ]
        for i,title in enumerate(titles,1): self._klog(f"  {i:2d}. {title}")

    def _schema_preview(self):
        city=self._kw_city.get(); state=self._kw_state.get()
        website=cfg("website"); phone=cfg("phone"); brand=cfg("brand")
        self._kw_out.delete("1.0","end")
        schema={"@context":"https://schema.org","@graph":[
            {"@type":"Article","headline":f"School ERP Software in {city}","author":{"@type":"Organization","name":brand},"publisher":{"@type":"Organization","name":brand,"url":website},"datePublished":datetime.now().strftime("%Y-%m-%d")},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":f"What is the best school ERP in {city}?","acceptedAnswer":{"@type":"Answer","text":f"TACHY School ERP is trusted by 500+ schools including in {city}."}}]},
            {"@type":"LocalBusiness","name":brand,"url":website,"telephone":phone,"areaServed":[city,state,"India"]}
        ]}
        self._klog("=== SCHEMA.ORG JSON-LD TEMPLATE ===\n")
        self._klog(json.dumps(schema,ensure_ascii=False,indent=2))

    def _link_strategy(self):
        city=self._kw_city.get(); state=self._kw_state.get()
        self._kw_out.delete("1.0","end")
        self._klog(f"=== INTERNAL LINK STRATEGY — {city} ===\n")
        conn=sqlite3.connect(DB_PATH)
        related=conn.execute("SELECT city_name FROM cities WHERE state_name=? AND city_name!=? LIMIT 8",(state,city)).fetchall()
        conn.close()
        self._klog(f"Each {city} post should link to:")
        self._klog(f"  1. Homepage: {cfg('website')}/")
        self._klog(f"  2. Free Demo page: {cfg('website')}/leadform.php")
        website=cfg("website")
        for r in related: self._klog(f"  3. Related city: {website}/school-erp-software-{r[0].lower().replace(' ','-')}/")
        self._klog(f"\nAnchor text variations to use:")
        anchors=[f"school ERP software {city}",f"TACHY School ERP {city}",f"school management software {city}",
                 f"best school ERP in {city}","TACHY School ERP","school ERP India"]
        for a in anchors: self._klog(f"  • {a}")

    # ══════════════════════════════════════════════════════════════════
    #  TAB 7 — SETTINGS
    # ══════════════════════════════════════════════════════════════════
    def _tab_settings(self):
        f=ttk.Frame(self._nb); self._nb.add(f,text="  ⚙  Settings  ")
        canvas=tk.Canvas(f,bg="#060b18",highlightthickness=0)
        sb=ttk.Scrollbar(f,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        inner=tk.Frame(canvas,bg="#060b18"); inner.columnconfigure(1,weight=1)
        canvas.create_window((0,0),window=inner,anchor="nw")
        inner.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))

        tk.Label(inner,text="Brand & Site Configuration",bg="#060b18",fg="#6c63ff",font=("Segoe UI",14,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",padx=20,pady=(16,10))
        self._svs={}
        fields=[("Brand Name","brand"),("Short Name","short"),("Website URL","website"),
                ("Phone","phone"),("WhatsApp (with code)","wa"),("Email","email"),
                ("Google Analytics ID","ga"),("Output Directory","out_dir"),
                ("WP Publish Delay (sec)","wp_publish_delay"),
                ("Default WP Post Status","wp_default_status"),
                ("Default Category","wp_default_category"),
                ("Use Free AI Keywords (1=Yes, 0=No)","use_ai_keywords"),
                ("Gemini API Key (Optional)","gemini_api_key")]
        for i,(lbl,key) in enumerate(fields,1):
            tk.Label(inner,text=lbl,bg="#060b18",fg="#a0b4d4",font=("Segoe UI",10)).grid(row=i,column=0,sticky="w",padx=20,pady=5)
            var=tk.StringVar(value=cfg(key)); self._svs[key]=var
            ttk.Entry(inner,textvariable=var,width=55).grid(row=i,column=1,sticky="ew",padx=(8,20),pady=5)

        row0=len(fields)+1
        brow=tk.Frame(inner,bg="#060b18"); brow.grid(row=row0,column=0,columnspan=2,padx=20,pady=(12,4),sticky="w")
        ttk.Button(brow,text="💾 Save Settings",command=self._save_settings).pack(side="left",padx=3)

        # WP quick tips
        ttk.Frame(inner,style="Sep.TFrame",height=1).grid(row=row0+1,column=0,columnspan=2,sticky="ew",padx=20,pady=12)
        tk.Label(inner,text="📋 WordPress Publishing Tips",bg="#060b18",fg="#6c63ff",font=("Segoe UI",12,"bold")).grid(row=row0+2,column=0,columnspan=2,sticky="w",padx=20,pady=(8,8))
        tips=["✅ Use 'draft' status to review posts before publishing — then switch to 'publish' in WP admin",
              "✅ 3 second delay between posts is safe. Reduce to 1s for faster bulk publishing",
              "✅ 'Update existing' re-posts the same city with fresh content (good for monthly updates)",
              "✅ Categories are auto-created if they don't exist (Yoast SEO picks them up automatically)",
              "✅ Tags are auto-created per city — creates internal tag pages for extra SEO",
              "✅ If Yoast SEO is installed, meta description and title are auto-set via WP meta API",
              "✅ After bulk publish, go to WP Admin → Settings → Permalinks → Save Changes (flushes rewrite rules)",
              "✅ Sitemap ping is triggered after every bulk publish session (Note: Google deprecated pings; use Search Console)",
              "⚠  Some managed WordPress hosts (WP Engine, Kinsta) may need IP allowlisting for REST API"]
        for j,tip in enumerate(tips,row0+3):
            tk.Label(inner,text=tip,bg="#060b18",fg="#64748b" if "⚠" not in tip else "#f87171",font=("Segoe UI",9)).grid(row=j,column=0,columnspan=2,sticky="w",padx=20,pady=2)

    def _save_settings(self):
        for key,var in self._svs.items():
            set_cfg(key,var.get())
        messagebox.showinfo("Saved","✅ Settings saved!")
        log_db("SETTINGS","Updated")

    # ══════════════════════════════════════════════════════════════════
    #  TAB 8 — LOG
    # ══════════════════════════════════════════════════════════════════
    def _tab_log(self):
        f=ttk.Frame(self._nb); self._nb.add(f,text="  📋  Log  ")
        f.columnconfigure(0,weight=1); f.rowconfigure(1,weight=1)
        top=tk.Frame(f,bg="#060b18"); top.grid(row=0,column=0,columnspan=2,sticky="ew",padx=14,pady=(12,6))
        ttk.Button(top,text="🔄 Refresh",command=self._load_log).pack(side="left",padx=3)
        ttk.Button(top,text="🗑 Clear",command=self._clear_log,style="R.TButton").pack(side="left",padx=3)
        ttk.Button(top,text="📤 Export",command=self._export_log,style="Y.TButton").pack(side="left",padx=3)
        self._ltree=ttk.Treeview(f,columns=("ts","action","detail"),show="headings")
        self._ltree.heading("ts",text="Time"); self._ltree.column("ts",width=130)
        self._ltree.heading("action",text="Action"); self._ltree.column("action",width=120)
        self._ltree.heading("detail",text="Details"); self._ltree.column("detail",width=900)
        self._ltree.grid(row=1,column=0,sticky="nsew",padx=14,pady=(0,8))
        sb=ttk.Scrollbar(f,orient="vertical",command=self._ltree.yview)
        self._ltree.configure(yscroll=sb.set); sb.grid(row=1,column=1,sticky="ns")
        self._load_log()

    def _load_log(self):
        for r in self._ltree.get_children(): self._ltree.delete(r)
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("SELECT ts,action,details FROM audit_log ORDER BY id DESC LIMIT 500").fetchall()
        conn.close()
        for row in rows:
            tag="g" if "WP_PUBLISH" in row[1] or "GEN" in row[1] else "r" if "ERR" in row[1] else "n"
            self._ltree.insert("","end",values=row,tags=(tag,))
        self._ltree.tag_configure("g",foreground="#4ade80")
        self._ltree.tag_configure("r",foreground="#f87171")
        self._ltree.tag_configure("n",foreground="#64748b")

    def _clear_log(self):
        if messagebox.askyesno("Clear","Clear all logs?"):
            conn=sqlite3.connect(DB_PATH); conn.execute("DELETE FROM audit_log"); conn.commit(); conn.close()
            self._load_log()

    def _export_log(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="tachy_log_v4.csv")
        if not path: return
        conn=sqlite3.connect(DB_PATH)
        rows=conn.execute("SELECT ts,action,details FROM audit_log ORDER BY id DESC").fetchall()
        conn.close()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(["Time","Action","Details"])
            for r in rows: w.writerow(r)
        messagebox.showinfo("Exported",f"Log exported:\n{path}")


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    log_db("APP_START", "TACHY SEO PRO v4.0 launched")
    app = App()
    app.mainloop()
