-- TACHY SEO PRO v4.0 migration (backward compatible)
CREATE TABLE IF NOT EXISTS client_schools (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  school_name TEXT NOT NULL,
  school_domain TEXT NOT NULL,
  city TEXT,
  state TEXT,
  board TEXT,
  school_type TEXT,
  num_branches INTEGER DEFAULT 1,
  modules_used TEXT DEFAULT '[]',
  go_live_date TEXT,
  parent_app_available INTEGER DEFAULT 0,
  fee_payment_available INTEGER DEFAULT 0,
  report_card_available INTEGER DEFAULT 0,
  attendance_available INTEGER DEFAULT 0,
  support_email TEXT,
  support_phone TEXT,
  school_logo_path TEXT,
  implementation_notes TEXT,
  approved_testimonial TEXT,
  approved_testimonial_person TEXT,
  indexing_allowed INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS client_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_school_id INTEGER,
  page_type TEXT,
  slug TEXT,
  file_path TEXT,
  visible_text TEXT,
  word_count INTEGER DEFAULT 0,
  school_specificity_score INTEGER DEFAULT 0,
  cross_domain_similarity_score REAL DEFAULT 0,
  tachy_similarity_score REAL DEFAULT 0,
  indexing_mode TEXT DEFAULT 'noindex',
  canonical_target TEXT DEFAULT '',
  backlink_mode TEXT DEFAULT 'nofollow',
  link_count_to_tachy INTEGER DEFAULT 0,
  anchor_text_profile TEXT DEFAULT '{}',
  proof_status TEXT DEFAULT 'neutral',
  publish_status TEXT DEFAULT 'manual_review',
  publish_safety_status TEXT DEFAULT 'manual_review',
  reason_codes TEXT DEFAULT '[]',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS client_similarity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_slug TEXT,
  compared_to_slug TEXT,
  compared_to_domain TEXT,
  similarity_score REAL,
  action_taken TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS canonical_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT,
  client_domain TEXT,
  decision_type TEXT,
  reason TEXT,
  similarity_score REAL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS client_safety_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_slug TEXT,
  issue_codes TEXT DEFAULT '[]',
  school_specificity_score INTEGER DEFAULT 0,
  publish_status TEXT DEFAULT 'manual_review',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS board_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  board TEXT, city TEXT, state TEXT,
  slug TEXT UNIQUE, file_path TEXT,
  word_count INTEGER DEFAULT 0,
  seo_score INTEGER DEFAULT 0,
  generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS locality_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  locality TEXT, city TEXT, state TEXT,
  slug TEXT UNIQUE, file_path TEXT,
  word_count INTEGER DEFAULT 0,
  seo_score INTEGER DEFAULT 0,
  generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS module_city_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT, city TEXT, state TEXT,
  slug TEXT UNIQUE, file_path TEXT,
  word_count INTEGER DEFAULT 0,
  seo_score INTEGER DEFAULT 0,
  generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS gbp_posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city TEXT, state TEXT, post_type TEXT,
  post_content TEXT, utm_url TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wa_broadcasts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city TEXT, state TEXT, target_role TEXT,
  message_text TEXT, char_count INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
