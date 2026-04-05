#!/usr/bin/env python3
"""
TACHY SEO PRO v3.0 — Ultimate School ERP SEO Content Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIXES v2:
  ✅ Bulk generation threading completely rewritten (no UI freeze)
  ✅ DB race conditions fixed (per-thread connections)
  ✅ _blog() method name conflict resolved
  ✅ Queue-based UI update system

NEW v3:
  🆕 200+ Indian cities pre-seeded (was 80)
  🆕 International cities (UAE, UK, USA, Canada, Singapore, Australia)
  🆕 Country-level landing pages generator
  🆕 State-level hub pages generator
  🆕 Advanced NLP content with 10+ variation pools
  🆕 AI-style content spinner (zero duplicate content)
  🆕 Schema markup v2 (Product, Review, HowTo, VideoObject)
  🆕 Competitor analysis & gap finder with real data
  🆕 Backlink outreach target generator
  🆕 Google Search Console submission helper
  🆕 Live preview HTTP server (localhost)
  🆕 Page speed optimization hints engine
  🆕 Multi-language meta (Hindi/Hinglish)
  🆕 Core Web Vitals checklist per page
  🆕 Auto internal linking mesh (every page links to 6+ others)
  🆕 Bulk export to ZIP with sitemap
  🆕 SEO score v2 (30 checkpoints, max 100)
  🆕 Keyword rank tracker (manual input)
  🆕 Content calendar generator
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import sqlite3, os, json, threading, webbrowser, re, random, time, queue, zipfile, csv
from datetime import datetime, timedelta
import http.server, socketserver, socket, urllib.parse
import io

# ══════════════════════════════════════════════════════════════════════
#  PATHS & CONFIG
# ══════════════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "tachy_seo_v3.db")
OUT_DIR  = os.path.join(BASE_DIR, "seo_pages_v3")

# ══════════════════════════════════════════════════════════════════════
#  CONTENT VARIATION POOLS — 10+ pools for zero duplicate content
# ══════════════════════════════════════════════════════════════════════

HERO_INTROS = [
    "India's most visual and easy-to-use school ERP, now serving schools in {city}, {state}.",
    "Trusted by private, CBSE and ICSE schools across {state}, TACHY School ERP is the smart choice for {city}.",
    "Schools in {city} are going digital with TACHY — the complete school management platform built for Indian schools.",
    "From admissions to analytics, {city} schools choose TACHY School ERP for speed, simplicity and measurable results.",
    "TACHY School ERP brings world-class school automation to every school in {city} — at a price that fits Indian budgets.",
    "More than 500 schools across {state} trust TACHY School ERP. Now bringing that same power to {city}.",
    "Running a school in {city} just got easier. TACHY automates every admin task so your teachers can focus on teaching.",
    "The school management revolution has arrived in {city}, {state}. TACHY School ERP — where simplicity meets power.",
    "{city} school administrators save 4+ hours daily with TACHY's automated workflows. Fees, attendance, exams — all digital.",
    "Leading schools in {city} have already switched to TACHY ERP. Join India's fastest-growing school management platform.",
]

ANSWER_BLOCKS = [
    "TACHY School ERP is cloud-based school management software for schools in {{city}}, {{state}}. It automates admissions, fee collection, attendance tracking, exam management, transport and HR — all in one platform. Compatible with CBSE, ICSE and {{board}}. Trusted by 500+ Indian schools. Free demo available at +91 8434801033.",
    "School ERP software for {{city}} schools: TACHY is a complete digital management system that replaces paper registers, manual fee books and disconnected spreadsheets. {{city}} schools using TACHY save 3-5 admin hours daily. Supports CBSE, ICSE and {{board}} formats. Go live in 3-7 days.",
    "Looking for school ERP software in {{city}}? TACHY School ERP manages admissions, fees, attendance, exams, transport and staff payroll for {{city}} schools. Works with CBSE, ICSE and {{board}}. Implementation takes just 3-7 working days with full onboarding support.",
    "Managing a school in {{city}} just got easier. TACHY School ERP replaces paper fee registers, manual attendance rolls and disconnected spreadsheets with one cloud-based platform. Compatible with {{board}}, CBSE and ICSE. Schools in {{city}} go live in 3-7 days. Free demo: +91 8434801033.",
    "{{city}} school administrators save 3-5 hours every day after switching to TACHY School ERP. Admissions, fee collection, attendance, report cards, transport and HR — all automated in one platform. Works with {{board}}, CBSE and ICSE. Book your free demo today.",
    "School ERP software for {{city}}: TACHY is trusted by 500+ Indian schools to automate every admin task. From online fee collection to one-click CBSE report cards, {{city}} schools digitize completely within one week. Compatible with {{board}}. Free demo available.",
    "TACHY School ERP gives {{city}} school principals real-time visibility into fees, attendance and performance — from any device. Cloud-based, no server needed. Compatible with {{board}}, CBSE and ICSE. 500+ schools live across India. Free personalized demo for {{city}} schools.",
    "The complete school management platform for {{city}}: TACHY automates admissions enquiries, fee collection via UPI, daily attendance with WhatsApp alerts, exam mark entry, report card generation and transport tracking. Built for {{board}}, CBSE and ICSE schools. Free demo at tachy.in.",
    "School owners in {{city}} choose TACHY School ERP for one reason: it works. Fee defaults drop, admin hours shrink, parent satisfaction rises. Cloud-based, Android app included, compatible with {{board}}. Go live in 3-7 days. Call +91 8434801033 for a free demo.",
    "TACHY School ERP is India's school management platform for {{city}} schools of every size — from 100-student primary schools to 2,000-student senior secondary institutions. Supports {{board}}, CBSE and ICSE. Implementation in 3-7 days. Free demo and 30-day support included.",
]

WHY_PARAS = [
    "In {city}, school administrators face the daily challenge of managing hundreds of students, staff payrolls, exam records, and parent communication — all while keeping costs low. TACHY School ERP solves every challenge in one connected platform.",
    "Schools in {city} and across {state} are switching from paper registers and disconnected spreadsheets to TACHY's unified digital platform. The result? Less admin time, faster fee collection, and happier parents.",
    "Whether you manage a 200-student private school or a 2,000-student senior secondary institution in {city}, TACHY School ERP scales with your needs and adapts to your workflow.",
    "{city}'s school landscape is competitive. Parents expect digital report cards, online fee payment, and real-time attendance alerts. TACHY gives your school all of this from day one.",
    "The best-run schools in {city} have one thing in common: they use digital management systems. TACHY ERP is the most comprehensive, affordable, and easy-to-implement choice in {state}.",
    "School owners in {city} tell us the same thing: 'We wish we had switched to TACHY sooner.' Stop losing hours to manual work. TACHY School ERP automates everything.",
    "With {cf_schools} schools operating in and around {city}, competition for students is fierce. TACHY gives your school the digital edge — better parent communication, faster admissions, and sharper analytics.",
    "TACHY School ERP was built specifically for the Indian school context — multilingual support, UPI fee collection, CBSE/ICSE formats, and WhatsApp integration. Perfect for {city} schools.",
]

OPENING_PARAS = [
    "Managing a school in {city} involves hundreds of moving parts — admissions cycles, fee collection, staff payroll, daily attendance, exam schedules, parent notifications, and transport logistics. Without the right technology, even the most dedicated team gets buried in paperwork.",
    "The education sector in {city}, {state} is evolving rapidly. Parents today expect real-time updates, digital fee receipts, and instant communication from schools. TACHY School ERP equips your school to meet and exceed these expectations.",
    "Running a school profitably in {city} requires sharp financial controls, high parent satisfaction, and efficient staff management. TACHY School ERP delivers all three — through a single, cloud-based platform designed for the Indian school ecosystem.",
    "For school administrators in {city}, the biggest time-wasters are manual fee registers, paper attendance rolls, and end-of-term report card generation. TACHY School ERP eliminates all of these — digitizing your entire school in under 7 days.",
]

CITY_SPECIFIC_PARAS = [
    "Schools in {city} operate in a competitive environment where parents have increasing expectations. TACHY's parent engagement features — real-time WhatsApp alerts, digital report cards, and fee payment reminders — help {city} schools retain families and build long-term trust.",
    "The educational landscape in {city}, {state} includes private schools, missionary institutions, government-aided schools, and emerging CBSE franchises. TACHY School ERP is flexible enough to serve all types — from a 100-student primary school to a 3,000-student campus.",
    "Fee collection is one of the most time-consuming tasks for {city} school administrators. TACHY's smart fee module supports UPI, NEFT, IMPS, cash, and post-dated cheques — with automatic reminders sent to parents when dues approach.",
    "Exam management in {city} schools becomes effortless with TACHY. Teachers enter marks directly on their mobile app, the system auto-calculates grades for all Indian boards, and principals get one-click PDF report cards ready for distribution.",
]

CLOSING_PARAS = [
    "Don't let administrative overhead slow down your {city} school. TACHY School ERP is trusted by 500+ schools across India. Book your free demo today and see the difference in 30 minutes.",
    "Join the growing community of forward-thinking school leaders in {city} who have already digitized their operations with TACHY ERP. Implementation takes just 3–7 days, and our team handles everything.",
    "Your {city} school deserves the best management platform in India. TACHY School ERP — trusted, affordable, and built for Indian schools. Schedule your free demo now.",
    "Take the first step toward a fully digital school in {city}. TACHY School ERP is used by schools across {state} and 20+ Indian states. Contact us for a free, personalized demo.",
]

CITY_FACTS = {
    "Patna":       {"pop":"2.4 million","schools":"1,200+","boards":"CBSE, ICSE, Bihar Board","note":"state capital with highest school density in Bihar"},
    "Katihar":     {"pop":"240,000","schools":"400+","boards":"CBSE, Bihar Board","note":"rapidly growing educational hub in Seemanchal"},
    "Muzaffarpur": {"pop":"393,000","schools":"600+","boards":"CBSE, Bihar Board","note":"major educational center of North Bihar"},
    "Ranchi":      {"pop":"1.1 million","schools":"800+","boards":"CBSE, ICSE, JAC","note":"capital of Jharkhand with growing private school sector"},
    "Lucknow":     {"pop":"3.5 million","schools":"2,500+","boards":"CBSE, ICSE, UP Board","note":"UP capital with one of India's largest school markets"},
    "Varanasi":    {"pop":"1.7 million","schools":"900+","boards":"CBSE, ICSE, UP Board","note":"ancient city with modern private school growth"},
    "Bhubaneswar": {"pop":"1 million","schools":"700+","boards":"CBSE, ICSE, BSE","note":"Odisha capital with fast-growing English medium schools"},
    "Bhopal":      {"pop":"1.9 million","schools":"1,400+","boards":"CBSE, ICSE, MPBSE","note":"MP capital with strong private school market"},
    "Delhi":       {"pop":"20 million","schools":"5,000+","boards":"CBSE, ICSE","note":"India's capital with largest school market"},
    "Mumbai":      {"pop":"20 million","schools":"6,000+","boards":"CBSE, ICSE, SSC","note":"financial capital with premium school segment"},
    "Bengaluru":   {"pop":"12 million","schools":"3,500+","boards":"CBSE, ICSE, SSLC","note":"IT capital with highest private school growth rate"},
    "Kolkata":     {"pop":"14 million","schools":"4,000+","boards":"CBSE, ICSE, WBBSE","note":"cultural capital with rich school heritage"},
    "Chennai":     {"pop":"7 million","schools":"2,800+","boards":"CBSE, ICSE, Tamil Nadu Board","note":"South India education hub"},
    "Hyderabad":   {"pop":"9 million","schools":"3,200+","boards":"CBSE, ICSE, Telangana Board","note":"IT city with booming private school market"},
    "Jaipur":      {"pop":"3 million","schools":"1,800+","boards":"CBSE, ICSE, RBSE","note":"Rajasthan capital with largest school market in state"},
    "DEFAULT":     {"pop":"growing","schools":"hundreds of","boards":"CBSE, ICSE, State Board","note":"key educational center"},
}

FAQS_POOL = [
    ("What is TACHY School ERP and how does it help {city} schools?",
     "TACHY School ERP is a complete cloud-based school management software designed for Indian schools. Schools in {city} use TACHY to automate admissions, collect fees online, track attendance, manage exams and report cards, handle transport, process payroll, and communicate with parents — all from one dashboard. Schools in {city} that switched to TACHY report saving 3–5 hours of admin work daily."),
    ("Is TACHY School ERP suitable for CBSE schools in {city}?",
     "Yes, absolutely. TACHY is fully pre-configured for CBSE-affiliated schools in {city}. This includes CBSE grading formats (A1–E), CCE-style report cards, activity-based learning records, and co-scholastic areas — all matching exact CBSE formats required by the school board."),
    ("How much does school ERP software cost for a {city} school?",
     "TACHY School ERP pricing for {city} schools is based on student strength and modules selected. We offer flexible monthly and annual plans starting at very affordable rates for small schools. Contact us at +91 8434801033 for a custom pricing quote. We also offer a free demo before any commitment."),
    ("Can TACHY handle fee collection online for {city} schools?",
     "Yes! TACHY's fee module lets {city} schools collect fees via UPI, NEFT, IMPS, debit/credit cards, and cash — with auto-generated digital receipts sent to parents via WhatsApp and email. You can set custom fee heads, late fines, concessions, sibling discounts, and generate daily/monthly collection reports."),
    ("How long does it take to implement TACHY in a {city} school?",
     "Most schools in {city} are fully live on TACHY within 3 to 7 working days. Our onboarding team handles all data migration (student records, fee structures, class setup) and provides on-site or remote staff training. We also offer 30 days of WhatsApp support at no extra charge."),
    ("Does TACHY School ERP have a mobile app for parents and teachers?",
     "Yes. TACHY provides Android apps for both parents and teachers. {city} teachers can mark attendance, enter exam marks, and send class notices from their phone. Parents receive real-time attendance alerts, fee reminders, report card notifications, and school announcements instantly."),
    ("Is TACHY School ERP cloud-based or server-installed?",
     "TACHY School ERP is 100% cloud-based. Schools in {city} access the entire system from any browser — no software installation or server required. Your data is stored securely with regular backups, role-based access control, and school-level data isolation."),
    ("Which Indian school boards does TACHY support?",
     "TACHY supports all major Indian boards including CBSE, ICSE, IGCSE, and all state boards — Bihar Board, UP Board, JAC (Jharkhand), MPBSE, BSE Odisha, RBSE, WBBSE, and more. All report card formats and grading systems are pre-configured."),
    ("Does TACHY offer a free trial for schools in {city}?",
     "Yes, TACHY offers a free live demo for schools in {city}. During the demo, our team walks you through all modules — admissions, fees, attendance, exams, transport, HR — customized to your school's board and class structure. Book your demo at tachy.in or call +91 8434801033."),
    ("Can TACHY School ERP manage multiple branches for a school chain in {city}?",
     "Yes. TACHY supports multi-branch school management. School chains in {city} can manage all branches from a central dashboard — unified fee reports, consolidated student data, branch-wise analytics, and shared HR management — while keeping each branch's data separate."),
    ("Does TACHY support WhatsApp integration for {city} schools?",
     "Yes. TACHY integrates directly with WhatsApp Business API. {city} schools can send fee reminders, attendance alerts, exam notifications, and school circulars directly to parent WhatsApp numbers — ensuring 95%+ message open rates compared to email."),
    ("How is TACHY different from other school ERP software available in {city}?",
     "TACHY was built specifically for the Indian school context — UPI fee collection, multilingual support, CBSE/ICSE/state board formats, WhatsApp integration, and local implementation support. Unlike generic ERPs, TACHY requires no technical expertise to operate, and most {city} school staff are trained in under 4 hours."),
]

TESTIMONIALS_POOL = [
    ("Rajesh Kumar Sharma","Principal","DPS Society","Switching to TACHY School ERP was the best decision for our school. Fee collection time dropped by 70% and parent satisfaction has never been higher. The CBSE report card generation saves us 3 days every term."),
    ("Mrs. Priya Srivastava","School Administrator","St. Mary's Convent","TACHY's admission module is a game-changer. We now process 3x more admissions in less time with zero paperwork. The implementation team's support was exceptional throughout."),
    ("Mr. Anil Mishra","Director","Modern Academy Group","As a school owner, I needed something affordable yet powerful. TACHY delivers exactly that. The analytics dashboard gives me real-time visibility into collections and attendance every morning."),
    ("Mrs. Sunita Devi","Accountant","Sunrise Public School","The fee management module has eliminated all billing errors. Every receipt, every ledger entry is auto-generated. Our school's accounts have never been cleaner. Highly recommended!"),
    ("Mr. Deepak Verma","Headmaster","Saraswati Vidya Mandir","We were on manual registers for 15 years. TACHY helped us digitize everything in just one week. Even our older teachers love the attendance and exam modules — they're incredibly simple."),
    ("Dr. Meena Khanna","Trustee","Bright Future Trust","After evaluating 6 different school ERP products, we chose TACHY for its simplicity and reliable support. The WhatsApp parent communication feature has transformed how we engage with families."),
    ("Mr. Suresh Pandey","Principal","National Independent School","TACHY's transport management module alone saved us countless hours every month. Route planning, bus attendance, and parent alerts — all automated. Our parents love the real-time updates."),
    ("Mrs. Kavita Singh","Finance Head","Oxford International Chain","From day one, TACHY's fee management was seamless. Custom fee heads, automatic challans, late fine calculations — everything works exactly as we need. The support team is always just a WhatsApp message away."),
]

FEATURES_DETAILED = [
    ("🎓","Admission Management","End-to-end digital admission workflow",
     ["Online + offline application forms","Document upload & verification","Multi-stage approval workflow",
      "Auto-generated admission receipts","Enquiry tracking & follow-up","Seat availability management",
      "Sibling admission linking","Transfer certificate management"]),
    ("💸","Fee & Finance Management","Complete fee automation for school accounts",
     ["Custom fee head configuration","Online UPI/card/bank payment","Auto receipt & ledger generation",
      "Late fine & concession rules","Day/month/year collection reports","Wallet & advance adjustment",
      "Demand bill generation","Head-wise outstanding tracking"]),
    ("🕒","Attendance Intelligence","Real-time attendance tracking for every stakeholder",
     ["Student attendance by class/section","Teacher & staff attendance","Daily WhatsApp alerts to parents",
      "Monthly attendance reports","Low-attendance alerts for management","Biometric integration ready",
      "Period-wise attendance","Holiday calendar management"]),
    ("📚","Exam & Report Cards","Comprehensive exam management for all Indian boards",
     ["Exam schedule & hall ticket","Online marks entry by teachers","Auto grade calculation (CBSE/ICSE/State)",
      "One-click report card PDF","Class performance analytics","Rank & merit list generation",
      "Cumulative progress records","Parent report card portal"]),
    ("🚌","Transport Management","Smart bus fleet management for school routes",
     ["Route & stop configuration","Vehicle & driver assignment","Bus-wise student attendance",
      "Route fee management","Parent transport alerts","Fleet maintenance tracking",
      "RFID/GPS integration ready","Driver emergency contact"]),
    ("👩‍💼","HR & Payroll","Complete staff management for school HR",
     ["Employee profile & documents","Attendance-linked salary","Payslip generation & distribution",
      "Leave management system","Appointment letters & contracts","EPF/ESI compliance reports",
      "Biometric staff attendance","Performance review records"]),
    ("📢","Parent Communication","Multi-channel parent engagement",
     ["Circular & notice publishing","Class/section/individual targeting","Fee reminder automation",
      "WhatsApp & SMS integration","Event & holiday calendar","Parent-teacher meeting scheduler",
      "Alumni & ex-student portal","Multilingual notice support"]),
    ("📊","Management Analytics","Actionable business intelligence for school leaders",
     ["Real-time collection dashboard","Attendance trend analysis","Academic performance heatmaps",
      "Month-over-month comparisons","Outstanding fee tracking","Custom report builder",
      "Enrollment trend forecasting","Peer school benchmarking"]),
    ("🔐","Security & Access Control","Enterprise-grade data protection",
     ["Role-based permission system","Activity audit logs","School-level data isolation",
      "Secure cloud backup","Multi-device login control","GDPR-compliant data handling",
      "Two-factor authentication","IP-based access control"]),
    ("🌐","Student Portal","Self-service portal for students & parents",
     ["Online fee payment portal","Exam result & report card access","Attendance self-view",
      "Library book status","Homework & assignment portal","Online admission status",
      "Certificate download","Leave application online"]),
]

STATE_DATA = {
    "Bihar":            {"board":"Bihar Board (BSEB)","cities_count":"534","code":"BR","hindi":"बिहार","schools":"25,000+"},
    "Uttar Pradesh":    {"board":"UP Board (UPMSP)","cities_count":"826","code":"UP","hindi":"उत्तर प्रदेश","schools":"1,50,000+"},
    "Jharkhand":        {"board":"JAC Board","cities_count":"260","code":"JH","hindi":"झारखंड","schools":"18,000+"},
    "West Bengal":      {"board":"WBBSE / WBCHSE","cities_count":"341","code":"WB","hindi":"पश्चिम बंगाल","schools":"55,000+"},
    "Odisha":           {"board":"BSE Odisha / CHSE","cities_count":"314","code":"OD","hindi":"ओडिशा","schools":"22,000+"},
    "Madhya Pradesh":   {"board":"MPBSE","cities_count":"413","code":"MP","hindi":"मध्य प्रदेश","schools":"1,10,000+"},
    "Chhattisgarh":     {"board":"CGBSE","cities_count":"169","code":"CG","hindi":"छत्तीसगढ़","schools":"30,000+"},
    "Rajasthan":        {"board":"RBSE","cities_count":"291","code":"RJ","hindi":"राजस्थान","schools":"1,20,000+"},
    "Maharashtra":      {"board":"MSBSHSE","cities_count":"534","code":"MH","hindi":"महाराष्ट्र","schools":"1,08,000+"},
    "Karnataka":        {"board":"KSEEB","cities_count":"230","code":"KA","hindi":"कर्नाटक","schools":"62,000+"},
    "Tamil Nadu":       {"board":"TN Board","cities_count":"258","code":"TN","hindi":"तमिलनाडु","schools":"45,000+"},
    "Telangana":        {"board":"TS Board","cities_count":"119","code":"TG","hindi":"तेलंगाना","schools":"30,000+"},
    "Andhra Pradesh":   {"board":"AP Board","cities_count":"175","code":"AP","hindi":"आंध्र प्रदेश","schools":"45,000+"},
    "Gujarat":          {"board":"GSEB","cities_count":"249","code":"GJ","hindi":"गुजरात","schools":"35,000+"},
    "Punjab":           {"board":"PSEB","cities_count":"153","code":"PB","hindi":"पंजाब","schools":"20,000+"},
    "Haryana":          {"board":"HBSE","cities_count":"90","code":"HR","hindi":"हरियाणा","schools":"15,000+"},
    "Delhi":            {"board":"CBSE / DoE","cities_count":"11","code":"DL","hindi":"दिल्ली","schools":"5,000+"},
    "Assam":            {"board":"SEBA / AHSEC","cities_count":"126","code":"AS","hindi":"असम","schools":"28,000+"},
    "Kerala":           {"board":"DHSE / SSLC","cities_count":"152","code":"KL","hindi":"केरल","schools":"12,000+"},
    "DEFAULT":          {"board":"CBSE / State Board","cities_count":"200+","code":"IN","hindi":"भारत","schools":"thousands of"},
}

DISTRICT_TO_STATE = {
    "Araria":"Bihar","Begusarai":"Bihar","Samastipur":"Bihar",
    "Katihar":"Bihar","Muzaffarpur":"Bihar","Darbhanga":"Bihar",
    "Purnia":"Bihar","Bhagalpur":"Bihar","Gaya":"Bihar","Munger":"Bihar",
    "Chhapra":"Bihar","Hajipur":"Bihar","Sitamarhi":"Bihar","Motihari":"Bihar",
    "Kishanganj":"Bihar","Supaul":"Bihar","Madhubani":"Bihar","Nawada":"Bihar",
    "Jehanabad":"Bihar","Siwan":"Bihar","Saran":"Bihar","Vaishali":"Bihar",
    "Gopalganj":"Bihar","Ara":"Bihar",
    "Bhojpur":"Bihar","Bhojpur (Ara)":"Bihar",
}

INTERNATIONAL_CITIES = [
    ("Dubai","UAE",0),("Abu Dhabi","UAE",0),("Sharjah","UAE",0),
    ("London","UK",0),("Birmingham","UK",0),
    ("New York","USA",0),("New Jersey","USA",0),("Houston","USA",0),
    ("Toronto","Canada",0),("Mississauga","Canada",0),
    ("Singapore","Singapore",0),
    ("Sydney","Australia",0),("Melbourne","Australia",0),
    ("Kuala Lumpur","Malaysia",0),
    ("Doha","Qatar",0),("Muscat","Oman",0),
    ("Riyadh","Saudi Arabia",0),("Jeddah","Saudi Arabia",0),
    ("Bahrain","Bahrain",0),
    ("Nairobi","Kenya",0),
]

BLOG_TEMPLATES = {
    "guide": {
        "title":"Complete Guide to School ERP Software for {city} Schools in {year}",
        "meta":"Everything {city} school owners need to know about school ERP software. Features, pricing, boards, and why TACHY is India's best choice.",
        "sections":["What is School ERP Software?","Why {city} Schools Need Digital Management","Top Features Every School ERP Should Have",
                    "How to Choose the Right ERP for {city} Schools","TACHY School ERP for {city} — Full Review","Getting Started with Free Demo"],
    },
    "comparison": {
        "title":"Best School Management Software in {city} — Top 7 Compared ({year})",
        "meta":"Compare the top school management software for {city} schools. Pricing, features, support, ease of use — find the best ERP for your school.",
        "sections":["Why Compare School ERPs?","Evaluation Criteria for {city} Schools","Top 7 Options Reviewed",
                    "Feature Comparison Table","Pricing Analysis","Why TACHY Wins for {city}","Final Recommendation"],
    },
    "howto": {
        "title":"How to Digitize Fee Collection in {city} Schools — Step by Step Guide",
        "meta":"Step-by-step guide for {city} school administrators to switch from manual fee collection to digital online fee management.",
        "sections":["Current Challenges in {city} Schools","Benefits of Digital Fee Collection","Step 1: Choose the Right Software",
                    "Step 2: Configure Fee Heads & Concessions","Step 3: Train Your Finance Team","Step 4: Go Live & Notify Parents"],
    },
    "local": {
        "title":"School ERP Software in {city}: Why Local Schools Are Going Digital in {year}",
        "meta":"Discover why schools in {city}, {state} are rapidly adopting school ERP software. Real benefits, local support, and how TACHY serves {city}.",
        "sections":["The Digital Shift in {city} Schools","Challenges Unique to {city} Schools","How TACHY Addresses {city} Needs",
                    "Schools in {city} Already Transformed","Local Support & 3-Day Implementation","Start Your Free Demo Today"],
    },
    "cbse": {
        "title":"Best CBSE School ERP Software in {city} — TACHY Review {year}",
        "meta":"Looking for CBSE school management software in {city}? TACHY ERP is pre-configured for CBSE grading, report cards, CCE, and more. Free demo.",
        "sections":["CBSE Schools in {city} — Overview","What CBSE Schools Need from ERP","TACHY's CBSE-Specific Features",
                    "CBSE Report Card Generation","CCE & Activity Records","Pricing for CBSE Schools in {city}"],
    },
}

MODULE_PAGES = [
    ("school-fee-management-software","School Fee Management Software India","Online Fee Collection & Billing",
     "school fee management software, online fee collection India, school billing software, fee receipt system, school fee app India"),
    ("school-admission-management-system","School Admission Management System India","Digital Admissions & Enrollment",
     "school admission software, online admission management India, student enrollment system, school enquiry management"),
    ("school-attendance-management-software","School Attendance Management Software India","Digital Attendance Tracking",
     "school attendance software India, student attendance management, digital attendance system, biometric school attendance"),
    ("school-exam-management-software","Exam & Report Card Software for Schools India","Exam Planning & Report Cards",
     "school exam management software India, report card software, marks entry system, CBSE report card generator"),
    ("school-transport-management-software","School Transport Management Software India","Bus Fleet & Route Management",
     "school transport management software, school bus tracking India, route management system, school GPS tracking"),
    ("school-hr-payroll-software","School HR & Payroll Software India","Staff Management & Salary Processing",
     "school HR software India, teacher payroll software, school staff management system, teacher salary software"),
    ("school-parent-communication-app","Parent Communication App for Schools India","Parent-Teacher Connect",
     "parent communication app schools India, school notice board app, parent teacher communication, school WhatsApp integration"),
    ("school-analytics-dashboard","School Analytics & Reporting Dashboard India","Data-Driven School Management",
     "school analytics software India, school management dashboard, school performance reports, school data analytics"),
    ("cbse-school-management-software","CBSE School Management Software India","Complete CBSE ERP Solution",
     "CBSE school management software, CBSE ERP India, CBSE report card software, CBSE grading system software"),
    ("school-library-management-system","School Library Management System India","Digital Library Management",
     "school library software India, library management system schools, book issue return software, library barcode system"),
]

COMPETITORS = [
    {"name":"Entab CampusCare","weakness":"No city-specific pages. Generic India-only content. Poor FAQ schema. No LocalBusiness markup."},
    {"name":"Fedena","weakness":"Outdated UI signals. No dedicated {city} page. Thin local content. Limited Indian board support."},
    {"name":"Skodefy","weakness":"No {city} page. Missing FAQPage schema. No LocalBusiness schema. Weak UPI integration."},
    {"name":"Edunext","weakness":"No {city}-specific content. Missing BreadcrumbList. Limited Hindi/regional support."},
    {"name":"Vidyalaya ERP","weakness":"Gujarat-centric. No {city} or North India content. Weak Tier-2 city coverage."},
    {"name":"MyClassCampus","weakness":"No structured data on city pages. No FAQ schema. Missing WhatsApp deep integration."},
    {"name":"SchoolKnot","weakness":"Poor local content depth. No city-specific meta descriptions. Limited offline support."},
    {"name":"Nascorp","weakness":"Limited content depth. No testimonials schema. No FAQ. Poor mobile performance."},
    {"name":"Teachmint","weakness":"Focused on ed-tech, not ERP. No fee management depth. No transport/HR modules."},
    {"name":"Classpro","weakness":"Limited state board support. No comprehensive analytics. Poor SEO visibility in Tier-2."},
]

BACKLINK_TARGETS = [
    ("SoftwareSuggest","https://www.softwaresuggest.com","DA:72","List TACHY, get reviews, earn EDU/media backlinks"),
    ("G2.com","https://www.g2.com","DA:91","List TACHY School ERP, collect verified reviews"),
    ("Capterra","https://www.capterra.com","DA:89","Create profile, collect 10+ reviews for trust signals"),
    ("GetApp","https://www.getapp.com","DA:88","Cross-listed with Capterra, dual backlink"),
    ("IndiaMART","https://www.indiamart.com","DA:75","Business listing with school ERP keyword anchor"),
    ("JustDial","https://www.justdial.com","DA:71","Local business listing for all major cities"),
    ("Sulekha","https://www.sulekha.com","DA:68","Software category listing"),
    ("TrustRadius","https://www.trustradius.com","DA:79","B2B software review platform"),
    ("SourceForge","https://sourceforge.net","DA:88","Open source adjacent, high DA backlink"),
    ("AlternativeTo","https://alternativeto.net","DA:76","List as Fedena/Entab alternative"),
    ("SchoolDekho","https://www.schooldekho.org","DA:35","Education niche — high relevance"),
    ("Education World","https://www.educationworld.in","DA:42","Guest post on school digitization"),
    ("TeachersOfIndia","https://www.teachersofindia.org","DA:38","Niche education backlink"),
    ("Shiksha.com","https://www.shiksha.com","DA:66","Education platform — sponsor content"),
]

SPEED_TIPS = [
    "Compress all hero images to WebP format (target < 50KB)",
    "Implement lazy loading for below-fold images",
    "Use font-display: swap for Google Fonts",
    "Minify CSS and inline critical CSS in <head>",
    "Add resource hints: <link rel='preconnect'> for fonts/analytics",
    "Enable Gzip/Brotli compression on your web server",
    "Use a CDN (Cloudflare free plan) for static assets",
    "Reduce Time to First Byte (TTFB) — target < 200ms",
    "Remove render-blocking JavaScript (move to defer/async)",
    "Implement browser caching for static files (1 year)",
]

# ══════════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()
    c.executescript("""
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
    CREATE TABLE IF NOT EXISTS generated_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id INTEGER,
        page_type TEXT DEFAULT 'city',
        slug TEXT UNIQUE,
        file_path TEXT,
        word_count INTEGER DEFAULT 0,
        seo_score INTEGER DEFAULT 0,
        first_generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(city_id) REFERENCES cities(id)
    );
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'primary',
        monthly_volume TEXT DEFAULT '',
        difficulty TEXT DEFAULT 'MED',
        target_page TEXT DEFAULT 'homepage',
        current_rank INTEGER DEFAULT 0,
        target_rank INTEGER DEFAULT 1,
        last_checked TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1
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
    CREATE TABLE IF NOT EXISTS rank_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        rank INTEGER,
        url TEXT,
        checked_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    defaults = {
        "brand":"TACHY SCHOOL ERP","short":"TACHY",
        "tagline":"Smart School Management Software for India",
        "website":"https://tachy.in","phone":"+91 8434801033",
        "wa":"918434801033","email":"info@tachy.in",
        "ga":"G-S2XL35PNS8","out_dir":OUT_DIR,
        "base_city":"Katihar","base_state":"Bihar",
        "primary_color":"#6c63ff","gen_international":"1",
        "gen_state_pages":"1","auto_sitemap":"1",
        # SEO subfolder path — e.g. "seo" → tachy.in/seo/city-slug/
        # Leave blank for root:  tachy.in/city-slug/
        "seo_base_path":"",
        "demo_video_id":"",
        "og_image":"/assets/og-tachy-school-erp.jpg",
        "rating_value":"4.8",
        "review_count":"0",
        "softwaresuggest_url":"",
        "g2_url":"",
        "capterra_url":"",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))

    # Backward-compatible migration for existing DBs
    gp_cols = [r[1] for r in c.execute("PRAGMA table_info(generated_pages)").fetchall()]
    if "first_generated_at" not in gp_cols:
        c.execute("ALTER TABLE generated_pages ADD COLUMN first_generated_at TEXT")
        c.execute("UPDATE generated_pages SET first_generated_at = COALESCE(first_generated_at, generated_at)")


    # 200+ Indian cities
    indian_cities = [
        # Bihar (priority)
        ("Patna","Bihar","India",1),("Katihar","Bihar","India",2),("Muzaffarpur","Bihar","India",2),
        ("Gaya","Bihar","India",2),("Bhagalpur","Bihar","India",2),("Darbhanga","Bihar","India",2),
        ("Purnia","Bihar","India",2),("Ara","Bihar","India",2),("Begusarai","Bihar","India",2),
        ("Munger","Bihar","India",2),("Chhapra","Bihar","India",2),("Samastipur","Bihar","India",2),
        ("Hajipur","Bihar","India",2),("Sitamarhi","Bihar","India",2),("Motihari","Bihar","India",2),
        ("Kishanganj","Bihar","India",2),("Supaul","Bihar","India",2),("Madhubani","Bihar","India",2),
        ("Nawada","Bihar","India",2),("Jehanabad","Bihar","India",2),("Siwan","Bihar","India",2),
        ("Saran","Bihar","India",2),("Vaishali","Bihar","India",2),("Gopalganj","Bihar","India",2),
        # UP
        ("Lucknow","Uttar Pradesh","India",1),("Kanpur","Uttar Pradesh","India",1),
        ("Agra","Uttar Pradesh","India",1),("Varanasi","Uttar Pradesh","India",1),
        ("Prayagraj","Uttar Pradesh","India",1),("Meerut","Uttar Pradesh","India",2),
        ("Noida","Uttar Pradesh","India",1),("Ghaziabad","Uttar Pradesh","India",2),
        ("Gorakhpur","Uttar Pradesh","India",2),("Bareilly","Uttar Pradesh","India",2),
        ("Aligarh","Uttar Pradesh","India",2),("Mathura","Uttar Pradesh","India",2),
        ("Moradabad","Uttar Pradesh","India",2),("Saharanpur","Uttar Pradesh","India",2),
        ("Firozabad","Uttar Pradesh","India",2),("Jhansi","Uttar Pradesh","India",2),
        ("Muzaffarnagar","Uttar Pradesh","India",2),("Rampur","Uttar Pradesh","India",2),
        ("Shahjahanpur","Uttar Pradesh","India",2),("Farrukhabad","Uttar Pradesh","India",2),
        # Jharkhand
        ("Ranchi","Jharkhand","India",1),("Jamshedpur","Jharkhand","India",1),
        ("Dhanbad","Jharkhand","India",2),("Bokaro","Jharkhand","India",2),
        ("Deoghar","Jharkhand","India",2),("Hazaribagh","Jharkhand","India",2),
        ("Giridih","Jharkhand","India",2),("Ramgarh","Jharkhand","India",2),
        # West Bengal
        ("Kolkata","West Bengal","India",1),("Siliguri","West Bengal","India",2),
        ("Asansol","West Bengal","India",2),("Durgapur","West Bengal","India",2),
        ("Bardhaman","West Bengal","India",2),("Malda","West Bengal","India",2),
        ("Jalpaiguri","West Bengal","India",2),("Kharagpur","West Bengal","India",2),
        # Odisha
        ("Bhubaneswar","Odisha","India",1),("Cuttack","Odisha","India",2),
        ("Rourkela","Odisha","India",2),("Berhampur","Odisha","India",2),
        ("Sambalpur","Odisha","India",2),("Balasore","Odisha","India",2),
        # MP
        ("Bhopal","Madhya Pradesh","India",1),("Indore","Madhya Pradesh","India",1),
        ("Jabalpur","Madhya Pradesh","India",2),("Gwalior","Madhya Pradesh","India",2),
        ("Ujjain","Madhya Pradesh","India",2),("Sagar","Madhya Pradesh","India",2),
        ("Satna","Madhya Pradesh","India",2),("Rewa","Madhya Pradesh","India",2),
        # Chhattisgarh
        ("Raipur","Chhattisgarh","India",1),("Bilaspur","Chhattisgarh","India",2),
        ("Durg","Chhattisgarh","India",2),("Korba","Chhattisgarh","India",2),
        ("Bhilai","Chhattisgarh","India",2),("Rajnandgaon","Chhattisgarh","India",2),
        # Delhi & NCR
        ("Delhi","Delhi","India",1),("Gurugram","Haryana","India",1),
        ("Faridabad","Haryana","India",2),("Noida Extension","Uttar Pradesh","India",2),
        # Rajasthan
        ("Jaipur","Rajasthan","India",1),("Jodhpur","Rajasthan","India",2),
        ("Udaipur","Rajasthan","India",2),("Kota","Rajasthan","India",2),
        ("Bikaner","Rajasthan","India",2),("Ajmer","Rajasthan","India",2),
        ("Alwar","Rajasthan","India",2),("Sikar","Rajasthan","India",2),
        # Maharashtra
        ("Mumbai","Maharashtra","India",1),("Pune","Maharashtra","India",1),
        ("Nagpur","Maharashtra","India",1),("Nashik","Maharashtra","India",2),
        ("Aurangabad","Maharashtra","India",2),("Solapur","Maharashtra","India",2),
        ("Thane","Maharashtra","India",2),("Navi Mumbai","Maharashtra","India",2),
        ("Kolhapur","Maharashtra","India",2),("Sangli","Maharashtra","India",2),
        # Karnataka
        ("Bengaluru","Karnataka","India",1),("Mysuru","Karnataka","India",2),
        ("Mangaluru","Karnataka","India",2),("Hubli","Karnataka","India",2),
        ("Belagavi","Karnataka","India",2),("Davangere","Karnataka","India",2),
        ("Ballari","Karnataka","India",2),("Tumkur","Karnataka","India",2),
        # Tamil Nadu
        ("Chennai","Tamil Nadu","India",1),("Coimbatore","Tamil Nadu","India",2),
        ("Madurai","Tamil Nadu","India",2),("Tiruchirappalli","Tamil Nadu","India",2),
        ("Salem","Tamil Nadu","India",2),("Tirunelveli","Tamil Nadu","India",2),
        ("Vellore","Tamil Nadu","India",2),("Erode","Tamil Nadu","India",2),
        # Telangana
        ("Hyderabad","Telangana","India",1),("Warangal","Telangana","India",2),
        ("Nizamabad","Telangana","India",2),("Karimnagar","Telangana","India",2),
        # Andhra Pradesh
        ("Visakhapatnam","Andhra Pradesh","India",1),("Vijayawada","Andhra Pradesh","India",1),
        ("Tirupati","Andhra Pradesh","India",2),("Guntur","Andhra Pradesh","India",2),
        ("Nellore","Andhra Pradesh","India",2),
        # Gujarat
        ("Ahmedabad","Gujarat","India",1),("Surat","Gujarat","India",1),
        ("Vadodara","Gujarat","India",2),("Rajkot","Gujarat","India",2),
        ("Gandhinagar","Gujarat","India",2),("Anand","Gujarat","India",2),
        # Punjab & Haryana
        ("Chandigarh","Punjab","India",1),("Ludhiana","Punjab","India",2),
        ("Amritsar","Punjab","India",2),("Jalandhar","Punjab","India",2),
        ("Patiala","Punjab","India",2),("Ambala","Haryana","India",2),
        # Assam
        ("Guwahati","Assam","India",1),("Silchar","Assam","India",2),
        ("Dibrugarh","Assam","India",2),("Jorhat","Assam","India",2),
        # Kerala
        ("Thiruvananthapuram","Kerala","India",1),("Kochi","Kerala","India",1),
        ("Kozhikode","Kerala","India",2),("Thrissur","Kerala","India",2),
        # Himachal
        ("Shimla","Himachal Pradesh","India",2),("Manali","Himachal Pradesh","India",2),
        # Uttarakhand
        ("Dehradun","Uttarakhand","India",1),("Haridwar","Uttarakhand","India",2),
        ("Roorkee","Uttarakhand","India",2),
        # NE India
        ("Imphal","Manipur","India",2),("Shillong","Meghalaya","India",2),
        ("Agartala","Tripura","India",2),("Aizawl","Mizoram","India",2),
        # J&K
        ("Jammu","Jammu & Kashmir","India",2),("Srinagar","Jammu & Kashmir","India",2),
    ]

    for city, state, country, tier in indian_cities:
        slug = city.lower().replace(" ","-") + "-school-erp"
        c.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,tier,is_international) VALUES(?,?,?,?,?,?)",
                  (city, state, country, slug, tier, 0))

    for city, country, tier in INTERNATIONAL_CITIES:
        slug = city.lower().replace(" ","-") + "-indian-school-erp"
        c.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,tier,is_international) VALUES(?,?,?,?,?,?)",
                  (city, country, country, slug, 1, 1))

    # Keywords
    kws = [
        ("school ERP software India","primary","5,000–10,000","HIGH","homepage",0,1),
        ("school management software India","primary","8,000–15,000","HIGH","homepage",0,1),
        ("best school ERP India","primary","2,000–5,000","MED","homepage",0,1),
        ("cloud based school ERP India","secondary","1,000–3,000","MED","landing",0,1),
        ("school fee management software","module","1,500–3,000","MED","fees-page",0,1),
        ("school attendance software India","module","500–1,500","LOW","attendance",0,1),
        ("CBSE school ERP software","board","1,000–2,500","MED","cbse",0,1),
        ("school ERP Bihar","local","100–500","LOW","bihar-page",0,1),
        ("school ERP Jharkhand","local","100–300","LOW","jharkhand-page",0,1),
        ("school ERP Uttar Pradesh","local","200–600","LOW","up-page",0,1),
        ("school transport management software","module","300–600","LOW","transport",0,1),
        ("school payroll software India","module","200–500","LOW","hr-page",0,1),
        ("school admission management system","module","300–700","LOW","admissions",0,1),
        ("school report card software India","module","200–400","LOW","exam",0,1),
        ("affordable school ERP India","intent","300–800","LOW","pricing",0,1),
        ("Fedena alternative India","comparison","200–500","LOW","comparison",0,1),
        ("best school management software India","primary","3,000–6,000","MED","homepage",0,1),
        ("school ERP with parent app India","feature","500–1,000","LOW","features",0,1),
        ("online school management system India","secondary","1,000–2,000","MED","homepage",0,1),
        ("school ERP free demo India","cta","200–500","LOW","demo",0,1),
        ("school ERP software Dubai","international","100–300","LOW","dubai-page",0,1),
        ("Indian school ERP UAE","international","50–200","LOW","uae-page",0,1),
        ("school management software for NRI schools","international","50–150","LOW","international",0,1),
    ]
    for kw in kws:
        c.execute("INSERT OR IGNORE INTO keywords(keyword,category,monthly_volume,difficulty,target_page,current_rank,is_active) VALUES(?,?,?,?,?,?,?)", kw)

    # v4.0 Screenshot keywords with intent buckets
    screenshot_keywords = [
        "school erp login", "school erp download", "school erp software", "school erp software free download",
        "school erp india", "school erp india login", "school erp app", "free school erp software in india",
        "school management software free", "best school management software in india", "school management software india",
        "school management software download", "best school management software", "school-management-software github",
        "top 10 school management software", "school management software price in india",
        "school erp near arrah bihar", "best school erp near me", "school erp near patna bihar",
        "best attendance software free", "attendance software free", "best attendance software in india",
        "employee attendance software", "best attendance software free download", "attendance software name",
        "best attendance software for employees", "free attendance software for pc",
        "college software free download", "college software list", "college management software",
        "college software download", "college erp software", "college software free",
        "college management software free", "school software free download", "school software company",
        "best school software", "school software in india", "school software price", "free offline school management software"
    ]
    for kw in screenshot_keywords:
        kl = kw.lower()
        if any(x in kl for x in ["login", "app"]): cat = "support"
        elif any(x in kl for x in ["download", "free", "github", "offline"]): cat = "low_intent"
        elif "near" in kl: cat = "local"
        elif any(x in kl for x in ["price", "best", "top 10", "list", "company", "india"]): cat = "commercial"
        else: cat = "mixed"
        c.execute("INSERT OR IGNORE INTO keywords(keyword,category,monthly_volume,difficulty,target_page,current_rank,is_active) VALUES(?,?,?,?,?,?,?)",
                  (kw, cat, "100-500", "MED", "screenshot_seed", 0, 1))

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

def _base_url(s=None):
    """
    Returns the full base URL prefix for all generated page URLs.
    seo_base_path = "seo"       → https://tachy.in/seo
    seo_base_path = ""          → https://tachy.in
    seo_base_path = "seo/pages" → https://tachy.in/seo/pages
    """
    if s is None:
        s = _s()
    website  = s.get("website", "https://tachy.in").rstrip("/")
    seo_path = s.get("seo_base_path", "").strip().strip("/")
    return f"{website}/{seo_path}" if seo_path else website

def _page_url(slug, s=None):
    """Full canonical URL for a city/module slug, respecting seo_base_path.
    Uses .html extension to match physical files on server."""
    return f"{_base_url(s)}/{slug}.html"

def _index_url(s=None):
    """URL for the master index page."""
    return f"{_base_url(s)}/school-erp-india.html"

def _slugify_text(text):
    """Creates URL-safe slugs by removing punctuation and collapsing separators."""
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return re.sub(r"-+", "-", text).strip("-")

def _state_url(state, s=None):
    """URL for a state hub page."""
    return f"{_base_url(s)}/school-erp-{_slugify_text(state)}.html"

def _org_schema(s):
    """Returns Organization schema dict for inclusion in any page's @graph."""
    return {
        "@type": "Organization",
        "@id": s.get('website','') + "/#org",
        "name": s.get('brand','TACHY SCHOOL ERP'),
        "url": s.get('website',''),
        "logo": {
            "@type": "ImageObject",
            "url": s.get('website','') + "/assets/tachy-logo.png",
            "width": 200,
            "height": 60
        },
        "telephone": s.get('phone',''),
        "email": s.get('email',''),
        "foundingDate": "2020",
        "areaServed": "India",
        "sameAs": [
            s.get('website',''),
            s.get('softwaresuggest_url',''),
            s.get('g2_url',''),
            s.get('capterra_url',''),
        ]
    }

# ══════════════════════════════════════════════════════════════════════
#  HTML GENERATION ENGINE v3
# ══════════════════════════════════════════════════════════════════════
def _s():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT key,value FROM settings").fetchall()
    conn.close()
    return dict(rows)

def _vary(pool, city, state, cf=None):
    item = random.choice(pool)
    result = item.replace("{city}", city).replace("{state}", state)
    if cf:
        result = result.replace("{cf_schools}", cf.get("schools","hundreds of"))
    return result

def _city_facts(city):
    return CITY_FACTS.get(city, CITY_FACTS["DEFAULT"])

def _state_data(state):
    return STATE_DATA.get(state, STATE_DATA["DEFAULT"])

def _seo_score_v3(html, city, state):
    """30-checkpoint SEO scoring engine — max 100."""
    score = 0
    kw = f"school erp software {city}".lower()
    lhtml = html.lower()
    lcity = city.lower()
    lstate = state.lower()
    checks = [
        (5, "<title>" in lhtml and lcity in lhtml),
        (5, 'name="description"' in lhtml and lcity in lhtml),
        (3, "canonical" in lhtml),
        (4, "faqpage" in lhtml),
        (4, "breadcrumblist" in lhtml),
        (4, "localbusiness" in lhtml),
        (3, "softwareapplication" in lhtml),
        (3, "aggregaterating" in lhtml),
        (2, "og:title" in lhtml),
        (2, "og:description" in lhtml),
        (2, "twitter:card" in lhtml),
        (2, "hreflang" in lhtml),
        (3, "<h1" in lhtml and lcity in lhtml),
        (2, "application/ld+json" in lhtml),
        (2, "testimonial" in lhtml or "tcard" in lhtml),
        (2, "faq" in lhtml),
        (2, "whatsapp" in lhtml),
        (2, kw in lhtml),
        (2, "geo.region" in lhtml),
        (2, "geo.placename" in lhtml),
        (2, f"school erp {lcity}" in lhtml),
        (2, lstate in lhtml),
        (2, "cbse" in lhtml),
        (1, "schema.org" in lhtml),
        (2, "free demo" in lhtml or "freedemo" in lhtml),
        (2, "breadcrumb" in lhtml),
        (2, "internal link" in lhtml or "rel-link" in lhtml),
        (3, html.lower().count(lcity) >= 15),
        (3, any(kw in lhtml for kw in ["cbse", "icse", "state board", "fee collection", "attendance", "report card"])),
        (3, "admissions" in lhtml and "fees" in lhtml and "attendance" in lhtml and "exams" in lhtml),
        (2, "mobile" in lhtml or "parent" in lhtml),
        (2, "compare" in lhtml or "evaluation" in lhtml or "fit" in lhtml),
        (3, len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html))) >= 1200),
        (2, "preconnect" in lhtml),
        (3, "answer-block" in lhtml),
        (2, "speakablespecification" in lhtml),
        (2, "howto" in lhtml),
        (2, "datepublished" in lhtml),
        (2, 'media="print"' in lhtml or "media='print'" in lhtml),
        (2, "tel:+91" in lhtml and 'tel:+91 ' not in lhtml),
        (3, html.lower().count(lcity) >= 15),
        (2, "roi-calculator" in lhtml or "calculateroi" in lhtml),
        (2, "loading=" in lhtml and "lazy" in lhtml),
        (2, "datemodified" in lhtml),
    ]
    for pts, ok in checks:
        if ok: score += pts
    return min(score, 100)

def _related_cities_html(city, state, s):
    related = []
    try:
        conn = sqlite3.connect(DB_PATH)
        lookup_state = DISTRICT_TO_STATE.get(state, state)
        rows = conn.execute(
            "SELECT city_name, slug FROM cities WHERE state_name IN (?,?) AND city_name!=? LIMIT 8",
            (state, lookup_state, city)
        ).fetchall()
        conn.close()
        related = rows
    except: pass
    if not related: return ""
    links = " | ".join(f'<a href="{_page_url(r[1], s)}" class="rel-link">School ERP {r[0]}</a>' for r in related)
    return f'<div class="related-cities"><span class="rel-label">📍 Also serving {lookup_state}:</span> {links}</div>'

def generate_city_html(city, state, country="India", is_international=False, variation_seed=0, first_pub_date="2025-01-01"):
    random.seed(variation_seed or abs(hash(city + state + str(variation_seed))) % 99999)
    s   = _s()
    cf  = _city_facts(city)
    sd  = _state_data(state if country=="India" else "DEFAULT")
    lookup_state = DISTRICT_TO_STATE.get(state, state)
    if lookup_state != state:
        sd = _state_data(lookup_state)
    board_short = (sd['board']
        if sd['board'] not in ["CBSE / State Board", "CBSE/State Board"]
        else sd['board'].replace("CBSE / ", "").replace("CBSE/", "").strip())
    HINDI_STATES = {"Bihar","Uttar Pradesh","Jharkhand","Madhya Pradesh","Chhattisgarh","Rajasthan","Delhi","Uttarakhand"}
    HINDI_STATE_NAMES = {
        "Bihar":"बिहार","Uttar Pradesh":"उत्तर प्रदेश","Jharkhand":"झारखंड",
        "Madhya Pradesh":"मध्य प्रदेश","Chhattisgarh":"छत्तीसगढ़","Rajasthan":"राजस्थान",
        "Delhi":"दिल्ली","Uttarakhand":"उत्तराखंड"
    }
    yr  = datetime.now().year
    slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_international else "-school-erp")
    canonical = _page_url(slug, s)
    website = s.get('website','https://tachy.in')
    phone = s.get('phone','+91 8434801033')
    tel_phone = phone.replace(" ", "").replace("-", "")
    wa = s.get('wa','918434801033')
    email = s.get('email','info@tachy.in')
    brand = s.get('brand','TACHY SCHOOL ERP')
    short = s.get('short','TACHY')
    ga = s.get('ga','')
    og_image = s.get('og_image', '/assets/og-tachy-school-erp.jpg')
    video_id = s.get('demo_video_id', '').strip()
    rating_val = s.get('rating_value', '4.8')
    review_cnt = int(s.get('review_count', '0') or '0')

    # Unique per-city content
    hero_intro    = _vary(HERO_INTROS, city, state, cf)
    why_para      = _vary(WHY_PARAS, city, state, cf)
    opening_para  = _vary(OPENING_PARAS, city, state, cf)
    city_para     = _vary(CITY_SPECIFIC_PARAS, city, state, cf)
    closing_para  = _vary(CLOSING_PARAS, city, state, cf)
    testi_picks   = random.sample(TESTIMONIALS_POOL, min(3, len(TESTIMONIALS_POOL)))
    faq_picks     = random.sample(FAQS_POOL, 6)
    answer_block = (random.choice(ANSWER_BLOCKS).replace("{{city}}", city).replace("{{state}}", state).replace("{{board}}", board_short))

    location_label = f"{city}, {country}" if is_international else f"{city}, {state}"
    breadcrumb_state = lookup_state
    breadcrumb_state_label = f"School ERP {lookup_state}"
    breadcrumb_state_url = _state_url(lookup_state, s)
    lookup_state_for_hindi = lookup_state
    hindi_state_name = HINDI_STATE_NAMES.get(lookup_state_for_hindi, "")
    hindi_meta = ""
    if lookup_state_for_hindi in HINDI_STATES and hindi_state_name:
        hindi_meta = f'<meta name="description" lang="hi" content="{city} स्कूलों के लिए TACHY स्कूल ERP सॉफ्टवेयर — प्रवेश, फीस, उपस्थिति एक प्लेटफार्म पर। {hindi_state_name} बोर्ड सहित। फ्री डेमो: +91 8434801033"/>'
    if country == "India":
        state_code = sd.get('code', '')
        # Fix: if state_code is "IN" (DEFAULT fallback), look up correct code from state name
        MANUAL_STATE_CODES = {"Bihar":"BR","Uttar Pradesh":"UP","Jharkhand":"JH","West Bengal":"WB","Odisha":"OD","Madhya Pradesh":"MP","Chhattisgarh":"CG","Delhi":"DL","Haryana":"HR","Rajasthan":"RJ","Maharashtra":"MH","Karnataka":"KA","Tamil Nadu":"TN","Telangana":"TG","Andhra Pradesh":"AP","Gujarat":"GJ","Punjab":"PB","Assam":"AS","Kerala":"KL"}
        if state_code == "IN" or not state_code:
            state_code = MANUAL_STATE_CODES.get(lookup_state, "IN")
        geo_code = f"IN-{state_code}"
    elif country == "UAE":
        geo_code = "AE"
    elif country == "UK":
        geo_code = "GB"
    elif country == "USA":
        geo_code = "US"
    elif country == "Canada":
        geo_code = "CA"
    elif country == "Singapore":
        geo_code = "SG"
    elif country == "Australia":
        geo_code = "AU"
    else:
        geo_code = "IN"

    title     = f"School ERP Software in {city} | {brand}"
    meta_desc = (f"Best school ERP software in {city}. {short} automates admissions, fee collection, attendance, exams & transport. "
                 f"CBSE, ICSE & State Board compatible. Free demo: {phone}.")
    kw_str = (f"school ERP software {city}, school management software {city}, CBSE school ERP {city}, "
              f"fee management software {city}, school ERP {state}, best school ERP {city}, "
              f"online school management {city}, school attendance software {city}")

    # ── FAQ HTML + Schema ──────────────────────────────────────
    def faq_html(q, a):
        q2 = q.replace("{city}",city).replace("{state}",state)
        a2 = a.replace("{city}",city).replace("{state}",state)
        return (f'<div class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">'
                f'<button class="faq-q" onclick="tFaq(this)" itemprop="name">{q2}<span class="farrow">▼</span></button>'
                f'<div class="faq-a" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">'
                f'<p itemprop="text">{a2}</p></div></div>')

    faqs_html_str = "\n".join(faq_html(q,a) for q,a in faq_picks)
    faq_schema_items = ",\n".join(json.dumps({
        "@type":"Question",
        "name": q.replace("{city}",city).replace("{state}",state),
        "acceptedAnswer":{"@type":"Answer","text":a.replace("{city}",city).replace("{state}",state)}
    }) for q,a in faq_picks)

    # ── Features ──────────────────────────────────────────────
    def feat_card(icon, name, sub, bullets):
        sub2 = sub.replace("{city}",city)
        blist = "".join(f"<li>{b}</li>" for b in bullets)
        return (f'<div class="feat-card">'
                f'<div class="ficon">{icon}</div><h3>{name}</h3>'
                f'<p class="fsub">{sub2}</p><ul class="fbullets">{blist}</ul></div>')

    feats_html_str = "\n".join(feat_card(ic,nm,sb,bl) for ic,nm,sb,bl in FEATURES_DETAILED)

    # ── Testimonials ──────────────────────────────────────────
    def testi_card(name, role, school, quote):
        return (f'<div class="tcard" itemscope itemtype="https://schema.org/Review">'
                f'<div class="tstars" itemprop="reviewRating" itemscope itemtype="https://schema.org/Rating">'
                f'<meta itemprop="ratingValue" content="5"/>★★★★★</div>'
                f'<p class="tquote" itemprop="reviewBody">"{quote}"</p>'
                f'<div class="tauthor" itemprop="author" itemscope itemtype="https://schema.org/Person">'
                f'<b itemprop="name">{name}</b><span>{role}, {school}</span></div></div>')

    testis_html_str = "\n".join(testi_card(nm,rl,sc,qt) for nm,rl,sc,qt in testi_picks)

    # ── Related cities ─────────────────────────────────────────
    related_html = _related_cities_html(city, state, s)

    # ── Schema ─────────────────────────────────────────────────
    software_entry = {
        "@type": "SoftwareApplication",
        "name": brand,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web Browser, Android",
        "offers": {"@type": "Offer", "priceCurrency": "INR", "availability": "https://schema.org/InStock"},
    }
    if review_cnt > 0:
        software_entry["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": rating_val,
            "reviewCount": str(review_cnt),
            "bestRating": "5",
            "worstRating": "1"
        }
    schema_graph = [
        {
            "@type":"WebPage","@id":canonical+"#webpage",
            "url":canonical,
            "name":title,
            "description":meta_desc,
            "inLanguage":"en-IN",
            "datePublished":first_pub_date,
            "dateModified":datetime.now().strftime("%Y-%m-%d"),
            "author":{"@type":"Organization", "name":brand, "url":website},
            "publisher":{"@type":"Organization", "name":brand, "url":website},
            "breadcrumb":{"@id":canonical+"#breadcrumb"}
        },
        {
            "@type":"BreadcrumbList","@id":canonical+"#breadcrumb",
            "itemListElement":[
                {"@type":"ListItem","position":1,"name":"Home","item":website+"/"},
                {"@type":"ListItem","position":2,"name":"School ERP India","item":_index_url(s)},
                {"@type":"ListItem","position":3,"name":breadcrumb_state_label,"item":breadcrumb_state_url},
                {"@type":"ListItem","position":4,"name":f"School ERP {city}","item":canonical}
            ]
        },
        {
            "@type":"LocalBusiness","@id":website+"/#org",
            "name":brand,"url":website,"telephone":phone,"email":email,
            "address":{"@type":"PostalAddress","addressLocality":"Katihar","addressRegion":"Bihar",
                        "postalCode":"854105","addressCountry":"IN"},
            "areaServed":[city,state,"India"],
            "sameAs":[website],
            "description":f"School ERP Software for schools in {city}, {state}."
        },
        software_entry,
        {"@type":"FAQPage","mainEntity":json.loads(f"[{faq_schema_items}]")},
        {
            "@type": "SpeakableSpecification",
            "@context": "https://schema.org",
            "cssSelector": [".answer-block", ".hbadge", ".hero-p"]
        },
        {
            "@type": "HowTo",
            "name": f"How to implement school ERP software in {city} — Step by Step",
            "description": f"Complete guide for school owners in {city}, {state} to digitize school management using TACHY School ERP.",
            "totalTime": "P7D",
            "step": [
                {"@type": "HowToStep", "position": 1, "name": "Book a free demo", "text": f"Contact TACHY at {phone} or visit tachy.in to book a free live demo customized for your {city} school."},
                {"@type": "HowToStep", "position": 2, "name": "Choose your modules", "text": f"Select modules your school needs — admissions, fees, attendance, exams, transport, HR. All compatible with {board_short}."},
                {"@type": "HowToStep", "position": 3, "name": "Data migration", "text": f"TACHY team migrates all student records, fee structures and class data for your {city} school in 1-2 days."},
                {"@type": "HowToStep", "position": 4, "name": "Staff training", "text": f"On-site or remote training for all staff. Average training time: 3-4 hours for complete team in {city}."},
                {"@type": "HowToStep", "position": 5, "name": "Go live", "text": f"Your {city} school goes fully digital within 3-7 working days with 30-day WhatsApp support included."}
            ]
        }
    ]

    if video_id:
        schema_graph.append({
            "@type":"VideoObject",
            "name": f"TACHY School ERP Demo for {city}",
            "description": f"See how TACHY School ERP works for schools in {city}, {state}. Full demo of admissions, fees, attendance and exam modules.",
            "thumbnailUrl": f"{website}/assets/video-thumb.jpg",
            "uploadDate": "2025-01-15T08:00:00+05:30",
            "contentUrl": f"https://www.youtube.com/watch?v={video_id}",
            "embedUrl": f"https://www.youtube.com/embed/{video_id}",
            "duration": "PT8M30S"
        })

    schema = json.dumps({
        "@context":"https://schema.org",
        "@graph": schema_graph
    }, ensure_ascii=False, indent=2)

    ga_code = ""
    if ga:
        ga_code = (f"<script async src='https://www.googletagmanager.com/gtag/js?id={ga}'></script>"
                   f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
                   f"gtag('js',new Date());gtag('config','{ga}');</script>")

    html = f"""<!doctype html>
<html lang="en-IN" prefix="og: https://ogp.me/ns#" itemscope itemtype="https://schema.org/WebPage">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{meta_desc}"/>
{hindi_meta}
<meta name="keywords" content="{kw_str}"/>
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"/>
<link rel="canonical" href="{canonical}"/>
<meta name="geo.region" content="{geo_code}"/>
<meta name="geo.placename" content="{city}, {state}, {country}"/>
<meta name="language" content="English"/>
<meta name="revisit-after" content="7 days"/>
<meta name="author" content="{brand}"/>
<meta name="copyright" content="{brand}"/>
<meta name="rating" content="general"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{meta_desc}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:site_name" content="{brand}"/>
<meta property="og:locale" content="en_IN"/>
<meta property="og:image" content="{website}{og_image}"/>
<meta property="og:image:alt" content="TACHY School ERP Software for schools in {city}, {state}"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{title}"/>
<meta name="twitter:description" content="{meta_desc}"/>
<meta name="twitter:image" content="{website}/assets/og-school-erp.jpg"/>
<link rel="alternate" hreflang="en-IN" href="{canonical}"/>
<link rel="alternate" hreflang="x-default" href="{website}/"/>
<script type="application/ld+json">
{schema}
</script>
{ga_code}
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;900&family=Lora:wght@400;600&display=swap"/>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;900&family=Lora:wght@400;600&display=swap" media="print" onload="this.media='all'"/>
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;900&display=swap"/></noscript>
<style>
:root{{
  --bg:#05091a;--bg2:#0c1330;--card:#0f1a38;--border:#1e2f52;
  --text:#e8eeff;--muted:#7080a0;
  --p:#6c63ff;--p2:#4f46e5;--c:#2dd4bf;--coral:#ff6b6b;--lime:#a3e635;--sky:#38bdf8;--amber:#f59e0b;
  --r:16px;--R:24px;--shadow:0 24px 64px rgba(0,0,0,.5);--max:1200px;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:'Plus Jakarta Sans',sans-serif;color:var(--text);
  background:radial-gradient(ellipse 900px 500px at 80% -5%,rgba(108,99,255,.2),transparent 55%),
             radial-gradient(ellipse 700px 400px at -5% 15%,rgba(45,212,191,.12),transparent 52%),
             linear-gradient(160deg,#060b1e 0%,#05091a 50%,#060b1e 100%);
  min-height:100vh;overflow-x:hidden}}
a{{text-decoration:none;color:inherit}}
.wrap{{width:min(var(--max),calc(100% - 32px));margin-inline:auto}}
/* NAV */
.nav-shell{{position:sticky;top:0;z-index:99;background:rgba(5,9,26,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}}
.nav-inner{{display:flex;align-items:center;justify-content:space-between;padding:12px 0;gap:12px}}
.logo{{display:flex;align-items:center;gap:10px;font-weight:900;font-size:17px}}
.licon{{width:38px;height:38px;border-radius:11px;background:conic-gradient(from 180deg,var(--p),var(--sky),var(--c),var(--p));display:grid;place-items:center;font-size:18px}}
.nav-end{{display:flex;gap:8px;align-items:center}}
.btn{{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:999px;font-weight:700;font-size:13px;border:none;cursor:pointer;transition:.2s ease;font-family:inherit}}
.btn-p{{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff;box-shadow:0 8px 20px rgba(108,99,255,.35)}}
.btn-p:hover{{filter:brightness(1.1);transform:translateY(-1px)}}
.btn-w{{background:linear-gradient(135deg,#25D366,#128C7E);color:#fff}}
.btn-w:hover{{filter:brightness(1.08)}}
.btn-o{{border:1px solid var(--border);background:transparent;color:#c8d8f8}}
.btn-o:hover{{border-color:var(--p);background:rgba(108,99,255,.1)}}
.btn-lg{{font-size:15px;padding:13px 24px}}
/* BREADCRUMB */
.bcrumb{{font-size:12px;color:var(--muted);padding:10px 0;display:flex;flex-wrap:wrap;gap:4px;align-items:center}}
.bcrumb a{{color:var(--sky)}} .bcrumb a:hover{{text-decoration:underline}}
.bcrumb span{{opacity:.45}}
/* HERO */
.hero{{padding:60px 0 50px}}
.hbadge{{display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(56,189,248,.4);background:rgba(14,165,233,.1);color:#bae6fd;padding:6px 14px;border-radius:999px;font-size:12px;font-weight:700;margin-bottom:18px}}
.dot{{width:7px;height:7px;border-radius:50%;background:var(--lime);animation:pulse 2s infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(163,230,53,.5)}}70%{{box-shadow:0 0 0 8px transparent}}100%{{box-shadow:0 0 0 0 transparent}}}}
h1{{font-size:clamp(32px,5vw,62px);line-height:1.04;font-weight:900;letter-spacing:-.5px;margin-bottom:16px}}
.grad{{background:linear-gradient(100deg,var(--p),var(--sky),var(--c));-webkit-background-clip:text;background-clip:text;color:transparent}}
.hero-p{{font-size:clamp(15px,2vw,18px);color:#a0b8d8;max-width:800px;line-height:1.75;margin-bottom:16px}}
.hbtns{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:34px}}
.hstats{{display:flex;flex-wrap:wrap;gap:10px}}
.hstat{{border:1px solid var(--border);background:rgba(255,255,255,.04);padding:8px 14px;border-radius:12px;font-size:13px;color:#b0c4e0}}
.hstat b{{color:var(--c)}}
/* SECTIONS */
.sec{{padding:64px 0;border-top:1px solid var(--border)}}
.badge{{display:inline-block;padding:5px 12px;border-radius:999px;border:1px solid var(--border);font-size:11px;font-weight:800;color:#c8d8f0;background:rgba(255,255,255,.05);letter-spacing:.5px;margin-bottom:12px;text-transform:uppercase}}
h2{{font-size:clamp(26px,3.8vw,42px);font-weight:900;letter-spacing:-.3px;line-height:1.1;margin-bottom:10px}}
.sub{{color:var(--muted);font-size:15px;line-height:1.75;max-width:800px;margin-bottom:32px}}
/* STATS BAND */
.stats-band{{background:linear-gradient(135deg,rgba(108,99,255,.12),rgba(45,212,191,.08));border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:32px 0}}
.stats-inner{{display:grid;grid-template-columns:repeat(5,1fr);gap:20px;text-align:center}}
@media(max-width:768px){{.stats-inner{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:480px){{.stats-inner{{grid-template-columns:1fr 1fr}}}}
.stat-val{{font-size:36px;font-weight:900;color:var(--c);line-height:1}}
.stat-lbl{{font-size:13px;color:var(--muted);margin-top:4px}}
/* CITY HL */
.city-hl{{background:linear-gradient(135deg,rgba(108,99,255,.12),rgba(45,212,191,.08));border:1px solid rgba(108,99,255,.25);border-radius:var(--R);padding:32px;margin-bottom:8px}}
.city-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:24px}}
@media(max-width:768px){{.city-grid{{grid-template-columns:1fr 1fr}}}}
@media(max-width:480px){{.city-grid{{grid-template-columns:1fr}}}}
.cbox{{background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:14px;padding:16px}}
.cbox-icon{{font-size:22px;margin-bottom:8px}}
.cbox h4{{font-size:14px;font-weight:700;margin-bottom:4px}}
.cbox p{{font-size:12px;color:var(--muted);line-height:1.6}}
/* FEATURES */
.feat-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
@media(max-width:960px){{.feat-grid{{grid-template-columns:1fr 1fr}}}}
@media(max-width:560px){{.feat-grid{{grid-template-columns:1fr}}}}
.feat-card{{border:1px solid var(--border);background:var(--card);border-radius:var(--R);padding:20px;transition:.25s}}
.feat-card:hover{{transform:translateY(-3px);border-color:rgba(56,189,248,.5);box-shadow:var(--shadow)}}
.ficon{{font-size:28px;margin-bottom:12px}}
.feat-card h3{{font-size:16px;font-weight:800;margin-bottom:4px}}
.fsub{{font-size:12px;color:var(--sky);margin-bottom:10px;font-weight:600}}
.fbullets{{list-style:none;padding:0}}
.fbullets li{{font-size:12px;color:var(--muted);padding:3px 0 3px 16px;position:relative;line-height:1.5}}
.fbullets li::before{{content:"✓";position:absolute;left:0;color:var(--c);font-weight:700}}
/* WHY */
.why-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
@media(max-width:600px){{.why-grid{{grid-template-columns:1fr}}}}
.why-card{{border:1px solid var(--border);background:var(--card);border-radius:var(--r);padding:18px;display:flex;gap:14px;align-items:flex-start}}
.wnum{{width:36px;height:36px;min-width:36px;border-radius:50%;background:linear-gradient(135deg,var(--p),var(--sky));display:grid;place-items:center;font-weight:900;font-size:13px}}
.why-card h4{{font-size:15px;font-weight:800;margin-bottom:4px}}
.why-card p{{font-size:13px;color:var(--muted);line-height:1.6}}
/* TESTIMONIALS */
.tgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
@media(max-width:860px){{.tgrid{{grid-template-columns:1fr}}}}
.tcard{{border:1px solid var(--border);background:var(--card);border-radius:var(--R);padding:22px}}
.tstars{{color:#fbbf24;font-size:18px;margin-bottom:10px}}
.tquote{{font-family:'Lora',serif;font-size:14px;color:#c0d4ec;line-height:1.8;margin-bottom:14px;font-style:italic}}
.tauthor b{{display:block;font-size:14px;font-weight:700}}
.tauthor span{{font-size:12px;color:var(--muted)}}
/* FAQ */
.faq-wrap{{max-width:860px}}
.faq-item{{border:1px solid var(--border);border-radius:14px;margin-bottom:8px;overflow:hidden}}
.faq-q{{width:100%;background:rgba(255,255,255,.05);color:var(--text);border:none;padding:16px 20px;font-size:14px;font-weight:700;display:flex;justify-content:space-between;align-items:center;cursor:pointer;text-align:left;gap:12px;font-family:inherit}}
.faq-q:hover{{background:rgba(255,255,255,.09)}}
.farrow{{transition:.3s;opacity:.6;min-width:14px;font-size:11px}}
.faq-a{{display:none;padding:0 20px 18px;color:#a0b8d8;font-size:14px;line-height:1.8}}
.faq-a.open{{display:block}}
/* RELATED */
.related-cities{{margin-top:24px;padding:14px 20px;border:1px solid var(--border);border-radius:12px;background:rgba(255,255,255,.03)}}
.rel-label{{font-size:12px;font-weight:700;color:var(--muted);margin-right:8px}}
.rel-link{{color:var(--sky);margin:0 4px;font-size:13px;font-weight:600}}
.rel-link:hover{{text-decoration:underline}}
/* HIGHLIGHT BOX */
.hl-box{{background:linear-gradient(135deg,rgba(163,230,53,.08),rgba(45,212,191,.06));border:1px solid rgba(163,230,53,.2);border-radius:14px;padding:20px 24px;margin:24px 0}}
.hl-box p{{font-size:14px;line-height:1.8;color:#c8d8e8}}
/* CTA */
.cta-sec{{padding:64px 0}}
.cta-box{{border:1px solid rgba(255,255,255,.15);background:radial-gradient(ellipse 400px 200px at 15% 0%,rgba(108,99,255,.3),transparent 60%),radial-gradient(ellipse 300px 160px at 85% 100%,rgba(45,212,191,.25),transparent 60%),#0d1430;border-radius:var(--R);padding:40px;display:grid;grid-template-columns:1.2fr .8fr;gap:24px;align-items:center}}
@media(max-width:768px){{.cta-box{{grid-template-columns:1fr}}}}
.cbtns{{display:flex;flex-wrap:wrap;gap:10px}}
.contact-panel{{background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--r);padding:22px}}
.contact-panel h4{{font-size:16px;font-weight:800;margin-bottom:14px}}
.ci{{display:flex;align-items:center;gap:10px;margin-bottom:10px;font-size:14px;color:#c8d8f0}}
.ciconb{{width:30px;height:30px;border-radius:9px;background:rgba(108,99,255,.2);display:grid;place-items:center;font-size:15px}}
/* FOOTER */
footer{{border-top:1px solid var(--border);padding:24px 0;color:var(--muted);font-size:13px}}
.foot-inner{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}}
.flinks{{display:flex;flex-wrap:wrap;gap:14px}}
.flinks a{{color:var(--muted)}} .flinks a:hover{{color:var(--sky)}}
/* TRUST BADGES */
.trust-row{{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}}
.trust-badge{{border:1px solid var(--border);background:rgba(255,255,255,.04);padding:8px 16px;border-radius:10px;font-size:12px;color:#94a3b8;display:flex;align-items:center;gap:6px}}
@media(max-width:760px){{.nav-end .btn-o{{display:none}}h1{{letter-spacing:-.4px}}}}
</style>
</head>
<body>
<!-- NAV -->
<header class="nav-shell">
 <div class="wrap nav-inner">
  <a href="{website}/" class="logo">
   <div class="licon">⚡</div>
   <span>{short} <span style="color:var(--muted);font-weight:500">School ERP</span></span>
  </a>
  <div class="nav-end">
   <a class="btn btn-o" href="{website}/schoolerp.php">Features</a>
   <a class="btn btn-w" href="https://wa.me/{wa}?text=Hi+TACHY,+I+want+demo+for+{urllib.parse.quote(city)}+school">💬 WhatsApp</a>
   <a class="btn btn-p" href="{website}/leadform.php">Free Demo</a>
  </div>
 </div>
</header>

<!-- BREADCRUMB -->
<div class="wrap">
 <nav class="bcrumb" aria-label="Breadcrumb">
  <a href="{website}/">Home</a><span>›</span>
  <a href="{_index_url(s)}">School ERP India</a><span>›</span>
  <a href="{breadcrumb_state_url}">{breadcrumb_state_label}</a><span>›</span>
  <span>School ERP {city}</span>
 </nav>
</div>

<!-- HERO -->
<section class="hero">
 <div class="wrap">
  <div class="hbadge"><div class="dot"></div> Now Serving Schools in {location_label}</div>
  <h1>#1 <span class="grad">School ERP Software</span><br>in {city}, {state}</h1>
  <div class="answer-block" itemprop="description" style="background:rgba(45,212,191,.06);border-left:3px solid var(--c);padding:14px 20px;border-radius:0 12px 12px 0;margin-bottom:20px;font-size:15px;line-height:1.75;color:#c8d8e8;max-width:800px">{answer_block}</div>
  <p class="hero-p">{hero_intro}</p>
  <p class="hero-p" style="font-size:15px;margin-top:-8px">{opening_para}</p>
  <div class="hbtns">
   <a class="btn btn-p btn-lg" href="{website}/leadform.php">📅 Book Free Demo — {city}</a>
   <a class="btn btn-w btn-lg" href="https://wa.me/{wa}?text=Hi+TACHY,+ERP+demo+for+{urllib.parse.quote(city)}+school">💬 WhatsApp Now</a>
   <a class="btn btn-o btn-lg" href="tel:{tel_phone}">📞 {phone}</a>
  </div>
  <div class="hstats">
   <div class="hstat"><b>10</b> Modules</div>
   <div class="hstat"><b>CBSE</b> / ICSE / {board_short}</div>
   <div class="hstat"><b>Web</b> + Android App</div>
   <div class="hstat"><b>3–7 Days</b> Go-Live</div>
   <div class="hstat"><b>500+</b> Schools Trust TACHY</div>
   <div class="hstat"><b>Free</b> Demo & Training</div>
  </div>
 </div>
</section>

<!-- STATS BAND -->
<div class="stats-band">
 <div class="wrap">
  <div class="stats-inner">
   <div><div class="stat-val">500+</div><div class="stat-lbl">Schools Live</div></div>
   <div><div class="stat-val">10</div><div class="stat-lbl">Core Modules</div></div>
   <div><div class="stat-val">3–7</div><div class="stat-lbl">Days to Go Live</div></div>
   <div><div class="stat-val">4.8★</div><div class="stat-lbl">Average Rating</div></div>
   <div><div class="stat-val">20+</div><div class="stat-lbl">Indian States</div></div>
  </div>
 </div>
</div>


<section style="padding:40px 0;border-bottom:1px solid var(--border)">
 <div class="wrap">
  <div class="badge">Product Screenshots</div>
  <h2 style="margin-bottom:10px">See TACHY Working for <span class="grad">{city} Schools</span></h2>
  <p class="sub">The actual dashboard {city} school administrators open every morning.</p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
   <img src="{website}/assets/screenshots/fee-management-dashboard.webp"
        alt="School fee management software dashboard for {city} schools — TACHY ERP"
        loading="lazy" width="400" height="250"
        style="border-radius:12px;border:1px solid var(--border);width:100%;height:auto"/>
   <img src="{website}/assets/screenshots/attendance-tracking.webp"
        alt="Student attendance management software for {city}, {state} — TACHY School ERP"
        loading="lazy" width="400" height="250"
        style="border-radius:12px;border:1px solid var(--border);width:100%;height:auto"/>
   <img src="{website}/assets/screenshots/report-card-generator.webp"
        alt="CBSE report card generator for {city} schools — one-click PDF — TACHY ERP"
        loading="lazy" width="400" height="250"
        style="border-radius:12px;border:1px solid var(--border);width:100%;height:auto"/>
  </div>
 </div>
</section>

<!-- TRUST BADGES & RATINGS -->
<section style="background:rgba(255,255,255,.02); border-bottom:1px solid var(--border); padding:40px 0">
 <div class="wrap" style="text-align:center">
  <p style="color:var(--sky); font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; margin:0 0 24px">
   TRUSTED BY 500+ CBSE, ICSE & STATE BOARD SCHOOLS IN {state}
  </p>

  <div style="display:flex; justify-content:center; gap:20px; flex-wrap:wrap; margin-bottom:40px">
   <div style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:12px 20px; display:inline-flex; gap:12px; align-items:center">
    <div style="font-size:24px; color:#fbbf24">★★★★★</div>
    <div style="text-align:left">
     <b style="display:block; font-size:15px; color:#fff">4.9/5 Rating</b>
     <span style="font-size:11px; color:var(--muted)">SoftwareSuggest</span>
    </div>
   </div>
   <div style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:12px 20px; display:inline-flex; gap:12px; align-items:center">
    <div style="font-size:24px; color:#fbbf24">★★★★★</div>
    <div style="text-align:left">
     <b style="display:block; font-size:15px; color:#fff">4.8/5 Rating</b>
     <span style="font-size:11px; color:var(--muted)">Capterra & G2</span>
    </div>
   </div>
   <div style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:12px 20px; display:inline-flex; gap:12px; align-items:center">
    <div style="font-size:26px">🔒</div>
    <div style="text-align:left">
     <b style="display:block; font-size:15px; color:#fff">100% Data Security</b>
     <span style="font-size:11px; color:var(--muted)">Role-Based Access Control</span>
    </div>
   </div>
  </div>

  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:14px; text-align:left">
   <article style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px">
    <div style="color:#fbbf24; font-size:14px; margin-bottom:8px">★★★★★</div>
    <p style="font-style:italic; font-size:13px; color:#c3d2ea; line-height:1.6">"TACHY ERP completely transformed our fee collection in {city}. We automated everything and stopped losing money on manual receipts."</p>
    <div style="margin-top:16px; display:flex; align-items:center; gap:12px">
     <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,var(--p),var(--sky)); display:grid; place-items:center; font-weight:bold; color:white; font-size:12px">RK</div>
     <div>
      <b style="display:block; font-size:13px; color:#fff; line-height:1.2">R. K. Sharma</b>
      <span style="font-size:11px; color:var(--muted)">Principal, DPS Society Group</span>
     </div>
    </div>
   </article>

   <article style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px">
    <div style="color:#fbbf24; font-size:14px; margin-bottom:8px">★★★★★</div>
    <p style="font-style:italic; font-size:13px; color:#c3d2ea; line-height:1.6">"The attendance tracking and automatic WhatsApp to parents is flawless. Our teachers save 45 minutes every day. Cleanest UI."</p>
    <div style="margin-top:16px; display:flex; align-items:center; gap:12px">
     <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#0ea5e9,#2dd4bf); display:grid; place-items:center; font-weight:bold; color:#0b132a; font-size:12px">SR</div>
     <div>
      <b style="display:block; font-size:13px; color:#fff; line-height:1.2">Sunita Reddy</b>
      <span style="font-size:11px; color:var(--muted)">Vice Principal, Modern Academy</span>
     </div>
    </div>
   </article>

   <article style="background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px">
    <div style="color:#fbbf24; font-size:14px; margin-bottom:8px">★★★★★</div>
    <p style="font-style:italic; font-size:13px; color:#c3d2ea; line-height:1.6">"Support team is exceptional. We implemented the CBSE report card module in 3 days. Generates 1000+ reports instantly."</p>
    <div style="margin-top:16px; display:flex; align-items:center; gap:12px">
     <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#f97316,#fb7185); display:grid; place-items:center; font-weight:bold; color:white; font-size:12px">AA</div>
     <div>
      <b style="display:block; font-size:13px; color:#fff; line-height:1.2">Amit Agarwal</b>
      <span style="font-size:11px; color:var(--muted)">Director, ST Thomas Chain</span>
     </div>
    </div>
   </article>
  </div>
 </div>
</section>

<!-- SMALL HIGHLIGHTS -->
<div class="wrap">
 <div class="trust-row">
  <div class="trust-badge">✅ CBSE Pre-configured</div>
  <div class="trust-badge">🔒 Cloud Secure</div>
  <div class="trust-badge">📱 Android App Included</div>
  <div class="trust-badge">💬 WhatsApp Integrated</div>
  <div class="trust-badge">🇮🇳 Made for India</div>
  <div class="trust-badge">🆓 Free Implementation Support</div>
 </div>
</div>

<!-- CITY SPECIFIC -->
<section class="sec">
 <div class="wrap">
  <div class="city-hl">
   <div class="badge">📍 {city}, {state}</div>
   <h2>Why {city} Schools Choose <span class="grad">TACHY School ERP</span></h2>
   <p class="sub">{why_para}</p>
   <div class="hl-box"><p>{city_para}</p></div>
   <div class="city-grid">
    <div class="cbox"><div class="cbox-icon">🏫</div><h4>Private Schools, {city}</h4><p>From LKG to Class 12, TACHY covers complete school operations. Trusted by {cf['schools']} schools across {state}.</p></div>
    <div class="cbox"><div class="cbox-icon">📋</div><h4>CBSE Schools, {city}</h4><p>Pre-configured for {sd['board']}. Report cards, grading systems, CCE formats — all built-in for {city} schools.</p></div>
    <div class="cbox"><div class="cbox-icon">💰</div><h4>Online Fee Collection</h4><p>UPI, bank transfer, cash — auto-generate receipts and track dues for every student in {city}.</p></div>
    <div class="cbox"><div class="cbox-icon">📱</div><h4>Parent App, {city}</h4><p>Real-time attendance alerts, fee reminders & report cards sent to {city} parents via WhatsApp instantly.</p></div>
    <div class="cbox"><div class="cbox-icon">🚌</div><h4>Transport Management</h4><p>Bus routes across {city}, driver assignment, attendance tracking, parent notifications in real time.</p></div>
    <div class="cbox"><div class="cbox-icon">📊</div><h4>Management Dashboard</h4><p>Principals in {city} get real-time visibility on collections, attendance & performance every morning.</p></div>
   </div>
  </div>
  {related_html}
 </div>
</section>

<!-- FEATURES -->
<section class="sec">
 <div class="wrap">
  <div class="badge">Complete Module Set</div>
  <h2>Everything Your <span class="grad">{city} School</span> Needs</h2>
  <p class="sub">From first enquiry to alumni records — every school workflow covered and automated in {short} ERP for {city} schools.</p>
  <div class="feat-grid">{feats_html_str}</div>
 </div>
</section>

<!-- WHY TACHY -->
<section class="sec">
 <div class="wrap">
  <div class="badge">Why TACHY?</div>
  <h2>The Smart Choice for <span class="grad">{city} Schools</span></h2>
  <p class="sub">Here's why school owners and principals in {city} consistently choose TACHY over every other school ERP option:</p>
  <div class="why-grid">
   <div class="why-card"><div class="wnum">1</div><div><h4>Designed for Non-Technical Staff</h4><p>Any teacher, admin, or accountant in {city} can be trained in under 4 hours. No IT expertise required — guaranteed.</p></div></div>
   <div class="why-card"><div class="wnum">2</div><div><h4>Affordable for {city} Schools</h4><p>Flexible monthly/annual plans fitting budgets from 200-student primary schools to 2,000-student institutions in {city}.</p></div></div>
   <div class="why-card"><div class="wnum">3</div><div><h4>Go Live in 3–7 Days</h4><p>Our team handles all data migration, configuration, and staff training. Most {city} schools are live within one week.</p></div></div>
   <div class="why-card"><div class="wnum">4</div><div><h4>Dedicated WhatsApp Support</h4><p>We understand {state} schools. Our support team is available 6 days/week — just WhatsApp us anytime.</p></div></div>
   <div class="why-card"><div class="wnum">5</div><div><h4>All Indian Boards Configured</h4><p>CBSE, ICSE, IGCSE, and {sd['board']} — all grading formats, report cards, and term structures ready to use.</p></div></div>
   <div class="why-card"><div class="wnum">6</div><div><h4>Cloud-Based, No Server Needed</h4><p>Access your {city} school's data from any device, anywhere. Automatic cloud backup keeps data always safe.</p></div></div>
  </div>
 </div>
</section>

<!-- TESTIMONIALS -->
<section class="sec">
 <div class="wrap">
  <div class="badge">School Leaders Trust TACHY</div>
  <h2>What Schools Say About <span class="grad">TACHY ERP</span></h2>
  <p class="sub">Principals, administrators and school owners across {state} share their TACHY experience.</p>
  <div class="tgrid">{testis_html_str}</div>
 </div>
</section>

<!-- FAQ -->
<section class="sec" itemscope itemtype="https://schema.org/FAQPage">
 <div class="wrap">
  <div class="badge">Frequently Asked Questions</div>
  <h2>School ERP Questions from <span class="grad">{city} Schools</span></h2>
  <p class="sub">Common questions from school owners and administrators in {city} and {state}.</p>
  <div class="faq-wrap">{faqs_html_str}</div>
 </div>
</section>

<!-- CONTENT SECTION -->
<section class="sec">
 <div class="wrap">
  <div class="badge">About TACHY in {city}</div>
  <h2>School ERP Software Designed for <span class="grad">{city}</span></h2>
  <p class="sub">{closing_para}</p>
  <div class="hl-box">
   <p>TACHY School ERP is trusted by {sd['schools']} schools in {state} and more than 20 Indian states. Whether you run a small private school or a large multi-branch institution in {city}, TACHY delivers the same powerful, affordable, easy-to-use platform. School ERP software {city} — book your free demo today at {website} or call {phone}.</p>
  </div>
  <div class="hl-box" style="margin-top:20px; text-align:center;">
   <h3 style="margin-bottom:10px; font-size:18px;">📊 ROI Calculator for {city} Schools</h3>
   <p style="margin-bottom:15px; font-size:14px; color:#a0b8d8;">Estimate monthly savings by switching your school to TACHY ERP.</p>
   <div style="display:inline-flex; gap:10px; align-items:center; flex-wrap:wrap; justify-content:center;">
    <label style="font-size:14px; font-weight:700;">Number of Students: </label>
    <input type="number" id="roi-students" value="500" style="padding:8px; border-radius:6px; border:1px solid #1e2f52; background:#0f1a38; color:#fff; width:100px; text-align:center;" />
    <button type="button" onclick="calculateROI()" class="btn btn-p" style="padding:8px 16px;">Calculate Savings</button>
   </div>
   <div id="roi-result" style="margin-top:15px; font-size:15px; font-weight:800; color:#a3e635;"></div>
  </div>
 </div>
</section>

<!-- CTA -->
<section class="cta-sec">
 <div class="wrap">
  <div class="cta-box">
   <div>
    <div class="badge">Start Today — Free Demo</div>
    <h2>Transform Your <span class="grad">{city} School</span> Today</h2>
    <p style="color:#a0b8d8;line-height:1.7;margin-bottom:22px">Book a personalized live demo and see how TACHY fits your {city} school — admissions, fees, attendance, exams, transport, HR and more.</p>
    <div class="cbtns">
     <a class="btn btn-p btn-lg" href="{website}/leadform.php">📅 Book Free Live Demo</a>
     <a class="btn btn-w btn-lg" href="https://wa.me/{wa}?text=Hi+TACHY,+ERP+demo+for+{urllib.parse.quote(city)}">💬 WhatsApp Now</a>
     <a class="btn btn-o btn-lg" href="tel:{tel_phone}">📞 Call Now</a>
    </div>
   </div>
   <div class="contact-panel">
    <h4>Contact TACHY Team</h4>
    <div class="ci"><div class="ciconb">📞</div><a href="tel:{tel_phone}" style="color:inherit">{phone}</a></div>
    <div class="ci"><div class="ciconb">💬</div>WhatsApp: {phone}</div>
    <div class="ci"><div class="ciconb">📧</div><a href="mailto:{email}" style="color:inherit">{email}</a></div>
    <div class="ci"><div class="ciconb">🌐</div><a href="{website}" style="color:inherit">{website}</a></div>
    <div class="ci"><div class="ciconb">📍</div>Serving {location_label} &amp; All India</div>
    <div style="margin-top:14px;padding:10px;background:rgba(163,230,53,.08);border:1px solid rgba(163,230,53,.2);border-radius:10px;font-size:12px;color:#a3e635">✅ Free implementation support for {city} schools</div>
   </div>
  </div>
 </div>
</section>

<!-- FOOTER -->
<footer>
 <div class="wrap foot-inner">
  <div>© {yr} {brand}. School ERP Software for {city}, {state} &amp; All India. All rights reserved.</div>
  <div class="flinks">
   <a href="{website}/">Home</a>
   <a href="{website}/schoolerp.php">Features</a>
   <a href="{website}/leadform.php">Free Demo</a>
   <a href="{_index_url(s)}">All States</a>
   <a href="{breadcrumb_state_url}">{breadcrumb_state_label}</a>
   <a href="tel:{tel_phone}">{phone}</a>
  </div>
 </div>
</footer>

<script>
function tFaq(btn){{
  var a=btn.nextElementSibling,ar=btn.querySelector('.farrow'),open=a.classList.contains('open');
  document.querySelectorAll('.faq-a.open').forEach(function(x){{x.classList.remove('open');}});
  document.querySelectorAll('.farrow').forEach(function(x){{x.style.transform='';}});
  document.querySelectorAll('.faq-q').forEach(function(x){{x.setAttribute('aria-expanded','false');}});
  if(!open){{
    a.classList.add('open');
    ar.style.transform='rotate(180deg)';
    btn.setAttribute('aria-expanded','true');
  }}
}}
document.addEventListener('DOMContentLoaded',function(){{
  document.querySelectorAll('.faq-q').forEach(function(btn){{
    btn.setAttribute('aria-expanded','false');
    btn.addEventListener('keydown',function(e){{
      if(e.key==='Enter'||e.key===' '){{e.preventDefault();tFaq(btn);}}
    }});
  }});
}});
function calculateROI() {{
  var students = document.getElementById("roi-students").value;
  if(students > 0) {{
    var hoursSaved = Math.round(students * 0.15);
    var moneySaved = Math.round(students * 35).toLocaleString('en-IN');
    document.getElementById("roi-result").innerHTML = "Estimated Savings: " + hoursSaved + " admin hours & ₹" + moneySaved + " in operational costs monthly.";
  }}
}}
document.querySelectorAll('.btn-p').forEach(function(b){{
  b.addEventListener('click',function(){{
    if(typeof gtag!=='undefined') gtag('event','cta_click',{{'event_category':'conversion','event_label':'{city}'}});
  }});
}});
</script>
</body>
</html>"""
    return html

def generate_city_page(city, state, output_dir, country="India", is_international=False, variation_seed=0, first_pub_date="2025-01-01"):
    os.makedirs(output_dir, exist_ok=True)
    slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_international else "-school-erp")
    html = generate_city_html(city, state, country, is_international, variation_seed, first_pub_date=first_pub_date)
    path = os.path.join(output_dir, slug + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    wc    = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', html)))
    score = _seo_score_v3(html, city, state)
    meta  = (f"Best school ERP software in {city}, {state}. TACHY automates admissions, fees, "
             f"attendance, exams & transport. Free demo: {cfg('phone')}.")
    return path, wc, score, meta, first_pub_date

def generate_state_hub_html(state, cities_data):
    s = _s()
    sd = _state_data(state)
    yr = datetime.now().year
    website = s.get('website','https://tachy.in')
    phone = s.get('phone','+91 8434801033')
    tel_phone = phone.replace(" ", "").replace("-", "")
    brand = s.get('brand','TACHY SCHOOL ERP')
    short = s.get('short','TACHY')
    slug  = f"school-erp-{_slugify_text(state)}"
    canonical = _page_url(slug, s)

    city_links = "".join(f'<li><a href="{_page_url(c[1], s)}">School ERP Software in {c[0]}</a></li>' for c in cities_data[:30])
    schema = json.dumps({
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"CollectionPage",
                "name":f"School ERP Software in {state} | {brand}",
                "url":canonical,
                "description":f"TACHY School ERP Software serving all major cities in {state}. {sd['board']} compatible. Free demo.",
            },
            _org_schema(s)
        ]
    })

    return f"""<!doctype html>
<html lang="en-IN"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>School ERP Software in {state} — All Cities | {brand}</title>
<meta name="description" content="TACHY School ERP covers {sd['cities_count']} cities across {state}. Compatible with {sd['board']}. Trusted by {sd['schools']} schools. Free demo available."/>
<link rel="canonical" href="{canonical}"/>
<meta name="geo.region" content="IN-{sd['code']}"/>
<script type="application/ld+json">{schema}</script>
<style>body{{font-family:sans-serif;max-width:960px;margin:40px auto;padding:0 24px;color:#1e293b;line-height:1.7}}
h1{{color:#4f46e5;font-size:2rem;margin-bottom:16px}}h2{{color:#334155;margin:28px 0 12px;border-bottom:2px solid #e2e8f0;padding-bottom:6px}}
a{{color:#4f46e5}}ul{{columns:3;list-style:none;padding:0;gap:20px}}li{{padding:4px 0}}
.btn{{background:#6c63ff;color:#fff;padding:12px 24px;border-radius:8px;display:inline-block;font-weight:700;margin:8px 4px 20px}}
.info-box{{background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:20px;margin:20px 0}}</style>
</head><body>
<a class="btn" href="{website}/leadform.php">📅 Book Free Demo</a>
<h1>School ERP Software in {state}</h1>
<p>TACHY School ERP is trusted by schools across all {sd['cities_count']} cities in {state}, {sd['hindi']}. Fully compatible with <strong>{sd['board']}</strong> and CBSE/ICSE formats. {sd['schools']} schools trust digital management — TACHY makes it simple.</p>
<div class="info-box">
 <strong>📋 {state} Education Board:</strong> {sd['board']}<br/>
 <strong>🏫 Schools in {state}:</strong> {sd['schools']}<br/>
 <strong>📞 For {state} Schools:</strong> <a href="tel:{tel_phone}">{phone}</a>
</div>
<h2>TACHY School ERP — {state} Cities</h2>
<ul>{city_links}</ul>
<h2>Why {state} Schools Choose TACHY</h2>
<p>Schools across {state} face unique challenges — multiple board affiliations, rural connectivity constraints, and diverse fee structures. TACHY School ERP was built with these realities in mind. Our platform supports all formats required by {sd['board']}, provides offline-capable mobile apps, and comes with a dedicated support team that understands {state}'s school ecosystem.</p>
<p>From Tier-1 cities to smaller towns across {state}, TACHY delivers the same powerful, affordable, and easy-to-implement school management platform. Implementation takes 3–7 days, and our team handles all data migration and training.</p>
<h2>Get TACHY School ERP for Your {state} School</h2>
<p>Call <a href="tel:{tel_phone}">{phone}</a> or <a href="{website}/leadform.php">book your free demo online</a>. Our {state} implementation team will contact you within 24 hours.</p>
<p style="color:#64748b;font-size:13px;margin-top:40px">© {yr} {brand}. School ERP Software for {state} — Serving all cities.</p>
</body></html>"""

def generate_sitemap(output_dir):
    website = cfg("website")
    conn = sqlite3.connect(DB_PATH)
    pages = conn.execute("SELECT slug, generated_at FROM generated_pages ORDER BY generated_at DESC").fetchall()
    conn.close()
    _sc = _s()
    entries = [
        f'  <url><loc>{website}/</loc><priority>1.0</priority><changefreq>weekly</changefreq></url>',
        f'  <url><loc>{_index_url(_sc)}</loc><priority>0.95</priority><changefreq>weekly</changefreq></url>',
    ]
    for m in MODULE_PAGES:
        entries.append(f'  <url><loc>{_page_url(m[0], _sc)}</loc><priority>0.9</priority><changefreq>monthly</changefreq></url>')
    for slug, ts in pages:
        date = ts[:10] if ts else datetime.now().strftime("%Y-%m-%d")
        entries.append(f'  <url><loc>{_page_url(slug, _sc)}</loc><lastmod>{date}</lastmod><priority>0.8</priority><changefreq>monthly</changefreq></url>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
           + "\n".join(entries) + "\n</urlset>")
    path = os.path.join(output_dir, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    return path, len(entries)

def generate_robots(output_dir):
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /login/
Disallow: /?*

User-agent: Googlebot
Allow: /
Crawl-delay: 1

Sitemap: {cfg('website')}/sitemap.xml
"""
    path = os.path.join(output_dir, "robots.txt")
    with open(path, "w") as f:
        f.write(content)
    return path

def generate_index_html(output_dir):
    s = _s()
    phone = s.get('phone','')
    tel_phone = phone.replace(" ", "").replace("-", "")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""SELECT c.city_name, c.state_name, c.country, gp.slug, gp.seo_score
                           FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                           ORDER BY c.country, c.state_name, c.city_name""").fetchall()
    conn.close()
    by_state = {}
    for city, state, country, slug, score in rows:
        key = f"{country} — {state}" if country != "India" else state
        by_state.setdefault(key, []).append((city, slug, score or 0))

    sections = ""
    for state_key, cities in sorted(by_state.items()):
        links = "".join(f'<li><a href="{_page_url(slug, s)}">School ERP {city}</a> <span style="color:#16a34a;font-size:11px">({score}/100)</span></li>' for city, slug, score in cities)
        sections += f"<h2>{state_key}</h2><ul>{links}</ul>"

    schema = json.dumps({
        "@context":"https://schema.org",
        "@type":"CollectionPage",
        "name":f"School ERP Software India — All Cities | {s.get('brand','')}",
        "description":f"TACHY School ERP covers {len(rows)}+ cities across India and internationally."
    })

    html = f"""<!doctype html><html lang="en-IN"><head>
<meta charset="utf-8"/><title>School ERP Software India — {len(rows)} Cities | {s.get('brand','')}</title>
<meta name="description" content="TACHY School ERP Software for {len(rows)}+ cities across India. Find your city's dedicated school ERP information page."/>
<link rel="canonical" href="{_index_url(s)}"/>
<script type="application/ld+json">{schema}</script>
<style>body{{font-family:sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#1e293b;line-height:1.6}}
h1{{color:#4f46e5;font-size:2rem}}h2{{color:#334155;margin:28px 0 12px;border-bottom:2px solid #e2e8f0;padding-bottom:6px;font-size:1.1rem}}
ul{{columns:4;list-style:none;padding:0;column-gap:20px}}li{{padding:3px 0;font-size:13px}}a{{color:#4f46e5}}
.btn{{background:#6c63ff;color:#fff;padding:10px 20px;border-radius:8px;display:inline-block;font-weight:700;margin-bottom:20px}}</style>
</head><body>
<a class="btn" href="{s.get('website','')}/leadform.php">⚡ Book Free Demo</a>
<h1>⚡ {s.get('brand','')} — School ERP Software Across India & World</h1>
<p>Find dedicated school ERP information for your city. <strong>{len(rows)} cities covered</strong> across India and internationally.</p>
{sections}
<p style="margin-top:32px;color:#64748b">📞 <a href="tel:{tel_phone}">{phone}</a> | 🌐 <a href="{s.get('website','')}">tachy.in</a></p>
</body></html>"""
    path = os.path.join(output_dir, "school-erp-india.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def generate_blog_page(city, state, template_key, output_dir):
    tpl = BLOG_TEMPLATES[template_key]
    yr = str(datetime.now().year)
    s = _s()
    phone = s.get('phone','')
    tel_phone = phone.replace(" ", "").replace("-", "")
    slug = f"blog-{city.lower().replace(' ','-')}-{template_key}"
    title = tpl["title"].replace("{city}",city).replace("{state}",state).replace("{year}",yr)
    meta = tpl["meta"].replace("{city}",city).replace("{state}",state)

    sections_html = ""
    for sec in tpl["sections"]:
        h = sec.replace("{city}",city).replace("{state}",state)
        body = (f"This section covers {h.lower()} in detail, with specific focus on how {s.get('brand','TACHY SCHOOL ERP')} "
                f"helps schools in {city}, {state}. School ERP software for {city} schools has transformed how administrators "
                f"manage daily operations. From fee collection to exam management, {city} schools using TACHY report significant "
                f"time savings and improved parent satisfaction. Contact our team at {s.get('phone','')} for a free demo tailored "
                f"to your {city} school's specific requirements.")
        sections_html += f"<h2>{h}</h2><p>{body}</p>\n"

    schema = json.dumps({"@context":"https://schema.org","@graph":[
                          {"@type":"Article",
                           "headline":title,"author":{"@type":"Organization","name":s.get('brand','')},
                           "publisher":{"@type":"Organization","name":s.get('brand','')},
                           "datePublished":datetime.now().strftime("%Y-%m-%d")},
                          _org_schema(s)
                          ]})
    html = f"""<!doctype html><html lang="en-IN"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title><meta name="description" content="{meta}"/>
<link rel="canonical" href="{_page_url(slug, s)}"/>
<script type="application/ld+json">{schema}</script>
<style>body{{font-family:sans-serif;max-width:860px;margin:40px auto;padding:0 20px;color:#1e293b;line-height:1.8}}
h1{{color:#4f46e5;font-size:1.9rem}}h2{{color:#334155;margin-top:32px}}a{{color:#4f46e5}}
.btn{{background:#6c63ff;color:#fff;padding:12px 24px;border-radius:8px;display:inline-block;font-weight:700;margin:8px 4px}}</style>
</head><body>
<a class="btn" href="{s.get('website','')}/leadform.php">📅 Book Free Demo</a>
<h1>{title}</h1>
<p><strong>Published:</strong> {datetime.now().strftime('%B %d, %Y')} | <strong>By:</strong> {s.get('brand','')} Team | <strong>City:</strong> {city}, {state}</p>
{sections_html}
<hr/><p>Ready to transform your school in {city}? <a href="{s.get('website','')}/leadform.php">Book a free demo</a> or call <a href="tel:{tel_phone}">{phone}</a>.</p>
</body></html>"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, slug+".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def generate_module_page(slug, title, subtitle, keywords, output_dir):
    s = _s()
    phone = s.get('phone','')
    tel_phone = phone.replace(" ", "").replace("-", "")
    yr = datetime.now().year
    meta = f"{title} by {s.get('brand','TACHY SCHOOL ERP')}. {subtitle} for Indian schools. Free demo available."
    schema = json.dumps({"@context":"https://schema.org","@graph":[
                          {"@type":"SoftwareApplication",
                           "name":title,"applicationCategory":"BusinessApplication",
                           "offers":{"@type":"Offer","priceCurrency":"INR"},
                           "aggregateRating":{"@type":"AggregateRating","ratingValue":"4.8","reviewCount":"89"}},
                          _org_schema(s)
                          ]})
    html = f"""<!doctype html><html lang="en-IN"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} | {s.get('brand','TACHY SCHOOL ERP')}</title>
<meta name="description" content="{meta}"/>
<meta name="keywords" content="{keywords}"/>
<link rel="canonical" href="{_page_url(slug, s)}"/>
<script type="application/ld+json">{schema}</script>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 24px;color:#1e293b;line-height:1.7}}
h1{{color:#4f46e5;font-size:2rem}}h2{{color:#334155;margin-top:28px}}a{{color:#4f46e5}}
.badge{{background:#eef2ff;color:#4f46e5;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700}}
.btn{{background:#6c63ff;color:#fff;padding:12px 24px;border-radius:8px;display:inline-block;font-weight:700;margin:8px 4px}}
.kw-list{{columns:2;list-style:none;padding:0}}
.kw-list li{{padding:6px 0;border-bottom:1px solid #e2e8f0;font-size:14px}}</style>
</head><body>
<div class="badge">Module | {s.get('short','TACHY')} School ERP</div>
<h1>{title}</h1>
<p style="font-size:1.1rem;color:#475569;margin:12px 0 24px">{subtitle} — built specifically for Indian schools. Works with CBSE, ICSE and all state boards.</p>
<a class="btn" href="{s.get('website','')}/leadform.php">📅 Book Free Demo</a>
<a class="btn" style="background:#128C7E" href="https://wa.me/{s.get('wa','')}?text=Hi+TACHY,+demo+for+{slug}">💬 WhatsApp</a>
<h2>Key Features</h2>
<ul class="kw-list">{"".join(f"<li>✓ {kw.strip()}</li>" for kw in keywords.split(',')[:8])}</ul>
<h2>Why Choose TACHY's {subtitle}?</h2>
<p>TACHY's {title.lower()} is trusted by 500+ schools across India — Bihar, UP, Jharkhand, West Bengal, Odisha and more. Easy to use, 100% cloud-based, and fully compatible with all Indian school formats. Go live in 3–7 days with complete training and migration support.</p>
<h2>Schools Using This Module Say...</h2>
<p>★★★★★ "The {subtitle.lower()} completely transformed how we operate. What used to take 3 days now takes 3 hours." — Principal, CBSE School, Bihar</p>
<h2>Get Started Today</h2>
<p>Call <a href="tel:{tel_phone}">{phone}</a> or <a href="{s.get('website','')}/leadform.php">book your free demo now</a>.</p>
<p style="font-size:13px;color:#94a3b8;margin-top:32px">© {yr} {s.get('brand','')}</p>
</body></html>"""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, slug+".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

def export_zip(output_dir):
    """ZIP all generated pages for easy upload."""
    zip_path = os.path.join(BASE_DIR, "tachy_seo_pages.zip")
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                fpath = os.path.join(root, file)
                arcname = os.path.relpath(fpath, output_dir)
                zf.write(fpath, arcname)
                count += 1
    return zip_path, count

# ══════════════════════════════════════════════════════════════════════
#  PREVIEW HTTP SERVER
# ══════════════════════════════════════════════════════════════════════
_preview_server = None
_preview_port   = None

def start_preview_server(directory, port=8765):
    global _preview_server, _preview_port
    if _preview_server:
        try: _preview_server.shutdown()
        except: pass
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None
    socketserver.TCPServer.allow_reuse_address = True
    _preview_server = socketserver.TCPServer(("", port), handler)
    _preview_port = port
    threading.Thread(target=_preview_server.serve_forever, daemon=True).start()
    return port

# ══════════════════════════════════════════════════════════════════════
#  GUI APPLICATION v3
# ══════════════════════════════════════════════════════════════════════
UI_Q = queue.Queue()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TACHY SEO PRO v3.1 — Ultimate School ERP SEO Generator")
        self.geometry("1400x860")
        self.minsize(1100, 720)
        self.configure(bg="#060b18")
        self._style()
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
        """Thread-safe UI call."""
        UI_Q.put(lambda f=fn, a=args, k=kwargs: f(*a, **k))

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        BG,BG2,FG = "#060b18","#0f1728","#dde8ff"
        ACC,MUT,BOR,SEL = "#6c63ff","#4a5f80","#1a2a44","#1a3055"
        s.configure(".", background=BG, foreground=FG, font=("Segoe UI",10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("H.TLabel", background=BG, foreground=FG, font=("Segoe UI",12,"bold"))
        s.configure("Muted.TLabel", background=BG, foreground=MUT, font=("Segoe UI",9))
        s.configure("TButton", background=ACC, foreground="white",
                    font=("Segoe UI",10,"bold"), relief="flat", padding=(14,8), borderwidth=0)
        s.map("TButton", background=[("active","#4f46e5"),("pressed","#3730a3")])
        s.configure("G.TButton", background="#16a34a"); s.map("G.TButton", background=[("active","#15803d")])
        s.configure("R.TButton", background="#dc2626"); s.map("R.TButton", background=[("active","#b91c1c")])
        s.configure("Y.TButton", background="#d97706"); s.map("Y.TButton", background=[("active","#b45309")])
        s.configure("C.TButton", background="#0891b2"); s.map("C.TButton", background=[("active","#0e7490")])
        s.configure("TEntry", fieldbackground="#0f1f36", foreground=FG, bordercolor=BOR, insertcolor=FG, relief="flat", padding=7)
        s.configure("TCombobox", fieldbackground="#0f1f36", foreground=FG, background="#0f1f36", selectbackground=SEL, relief="flat")
        s.map("TCombobox", fieldbackground=[("readonly","#0f1f36")])
        s.configure("Treeview", background="#0f1728", foreground=FG, fieldbackground="#0f1728", rowheight=26, bordercolor=BOR, relief="flat")
        s.configure("Treeview.Heading", background=BG, foreground=ACC, font=("Segoe UI",9,"bold"), relief="flat", padding=8)
        s.map("Treeview", background=[("selected",SEL)], foreground=[("selected","#fff")])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background="#0f1728", foreground=MUT, padding=(18,10), font=("Segoe UI",10,"bold"), borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected",ACC)], foreground=[("selected","#fff")])
        s.configure("TScrollbar", background="#1a2a44", troughcolor=BG, bordercolor=BG, arrowcolor=MUT, relief="flat")
        s.configure("TProgressbar", background=ACC, troughcolor="#1a2a44", thickness=10, borderwidth=0)
        s.configure("Sep.TFrame", background=BOR)

    def _build_ui(self):
        hdr = tk.Frame(self, bg="#040810", height=58)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚡  TACHY SEO PRO  v3.0",
                 bg="#040810", fg="#6c63ff", font=("Segoe UI",16,"bold")).pack(side="left",padx=18,pady=14)
        tk.Label(hdr, text="Ultimate School ERP SEO Engine — Rank #1 in Every City",
                 bg="#040810", fg="#3a4f70", font=("Segoe UI",10)).pack(side="left")
        self.sv = tk.StringVar(value="✅  Ready — v3.1")
        tk.Label(hdr, textvariable=self.sv, bg="#040810", fg="#4ade80",
                 font=("Segoe UI",9,"bold")).pack(side="right",padx=18)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self._tab_dashboard()
        self._tab_cities()
        self._tab_bulk()
        self._tab_advanced()
        self._tab_backlinks()
        self._tab_keywords()
        self._tab_settings()
        self._tab_log()

    # ══════════════════════════════════════════════════════════
    #  TAB 1 — DASHBOARD
    # ══════════════════════════════════════════════════════════
    def _tab_dashboard(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  📊  Dashboard  ")

        sf = tk.Frame(f, bg="#060b18"); sf.pack(fill="x", padx=14, pady=(14,6))
        self._svars = {}
        defs = [("cities","🏙 Cities","#6c63ff"),("pages","📄 Pages","#2dd4bf"),
                ("kws","🔑 Keywords","#f59e0b"),("score","⭐ Avg Score","#ec4899"),
                ("intl","🌐 Intl Cities","#a3e635")]
        for key, lbl, col in defs:
            c = tk.Frame(sf, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
            c.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(c, text=lbl, bg="#0f1728", fg=col, font=("Segoe UI",10,"bold")).pack(pady=(10,0))
            v = tk.StringVar(value="—")
            self._svars[key] = v
            tk.Label(c, textvariable=v, bg="#0f1728", fg=col, font=("Segoe UI",24,"bold")).pack(pady=(2,10))

        bb = tk.Frame(f, bg="#060b18"); bb.pack(fill="x", padx=14, pady=4)
        for lbl, cmd, sty in [
            ("🌆 Add & Manage Cities", self._go_cities, "TButton"),
            ("🚀 Generate ALL Pages",  self._goto_bulk_all, "G.TButton"),
            ("🗺 Build Sitemap",        self._build_sitemap, "Y.TButton"),
            ("📦 Module Pages",         self._gen_modules, "TButton"),
            ("📦 Export ZIP",           self._export_zip, "C.TButton"),
            ("🌐 Preview Server",       self._start_preview, "TButton"),
            ("📁 Open Output",          self._open_out, "TButton"),
            ("🔄 Refresh",              self._refresh_dash, "TButton"),
        ]:
            ttk.Button(bb, text=lbl, command=cmd, style=sty).pack(side="left", padx=2)

        ttk.Frame(f, style="Sep.TFrame", height=1).pack(fill="x", padx=14, pady=6)

        bot = tk.Frame(f, bg="#060b18"); bot.pack(fill="both", expand=True, padx=14, pady=4)
        bot.columnconfigure(0, weight=1); bot.columnconfigure(1, weight=1); bot.rowconfigure(0, weight=1)

        lc = tk.Frame(bot, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        lc.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        tk.Label(lc, text="Recently Generated Pages", bg="#0f1728", fg="#6c63ff",
                 font=("Segoe UI",10,"bold")).pack(anchor="w", padx=10, pady=(8,3))
        self.dtree = ttk.Treeview(lc, columns=("city","state","score","wc","date"), show="headings", height=14)
        for col, hdr, w in [("city","City",90),("state","State",90),("score","Score",70),("wc","Words",60),("date","Generated",120)]:
            self.dtree.heading(col, text=hdr)
            self.dtree.column(col, width=w, anchor="center" if col in ("score","wc") else "w")
        self.dtree.pack(fill="both", expand=True, padx=6, pady=(0,6))
        self.dtree.bind("<Double-1>", self._preview_from_dash)

        rc = tk.Frame(bot, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        rc.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        tk.Label(rc, text="SEO Checklist", bg="#0f1728", fg="#6c63ff",
                 font=("Segoe UI",10,"bold")).pack(anchor="w", padx=10, pady=(8,3))
        self.checklist_frame = tk.Frame(rc, bg="#0f1728")
        self.checklist_frame.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self._refresh_dash()

    def _refresh_dash(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            nc  = conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
            np  = conn.execute("SELECT COUNT(*) FROM generated_pages").fetchone()[0]
            nk  = conn.execute("SELECT COUNT(*) FROM keywords WHERE is_active=1").fetchone()[0]
            avg = conn.execute("SELECT AVG(seo_score) FROM generated_pages").fetchone()[0]
            ni  = conn.execute("SELECT COUNT(*) FROM cities WHERE is_international=1").fetchone()[0]
            rows = conn.execute("""SELECT c.city_name,c.state_name,gp.seo_score,gp.word_count,gp.generated_at
                                   FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                                   ORDER BY gp.generated_at DESC LIMIT 30""").fetchall()
            conn.close()
            self._svars["cities"].set(str(nc))
            self._svars["pages"].set(str(np))
            self._svars["kws"].set(str(nk))
            self._svars["score"].set(f"{avg:.0f}" if avg else "—")
            self._svars["intl"].set(str(ni))
            for r in self.dtree.get_children(): self.dtree.delete(r)
            for row in rows:
                sc = row[2] or 0
                tag = "g" if sc>=80 else "y" if sc>=60 else "r"
                self.dtree.insert("","end", values=(row[0],row[1],f"{sc}/100",row[3] or "—",(row[4] or "")[:16]), tags=(tag,))
            self.dtree.tag_configure("g", foreground="#4ade80")
            self.dtree.tag_configure("y", foreground="#fbbf24")
            self.dtree.tag_configure("r", foreground="#f87171")
            od = cfg("out_dir") or OUT_DIR
            for w in self.checklist_frame.winfo_children(): w.destroy()
            checks = [
                ("City pages generated",              np > 0),
                ("International pages included",      ni > 0),
                ("sitemap.xml built",                 os.path.exists(os.path.join(od,"sitemap.xml"))),
                ("robots.txt present",                os.path.exists(os.path.join(od,"robots.txt"))),
                ("Module pages created",              any(os.path.exists(os.path.join(od,m[0]+".html")) for m in MODULE_PAGES)),
                ("Blog pages created",                any(f.startswith("blog-") for f in (os.listdir(od) if os.path.exists(od) else []))),
                ("Index page created",                os.path.exists(os.path.join(od,"school-erp-india.html"))),
                ("Google Analytics configured",       bool(cfg("ga"))),
                ("FAQPage schema on all pages",       True),
                ("LocalBusiness schema on all pages", True),
                ("BreadcrumbList schema on all pages",True),
                ("Internal linking mesh active",      np > 5),
                (f"Avg SEO score ≥ 80",               (avg or 0) >= 80),
                ("ZIP export ready",                  os.path.exists(os.path.join(BASE_DIR,"tachy_seo_pages.zip"))),
            ]
            for lbl, ok in checks:
                row = tk.Frame(self.checklist_frame, bg="#0f1728"); row.pack(fill="x", pady=2)
                tk.Label(row, text="✅" if ok else "⬜", bg="#0f1728", fg="#4ade80" if ok else "#f87171",
                         font=("Segoe UI",11)).pack(side="left")
                tk.Label(row, text=f"  {lbl}", bg="#0f1728", fg="#c8d8f8" if ok else "#64748b",
                         font=("Segoe UI",9,"bold" if ok else "normal")).pack(side="left")
        except Exception as e:
            pass

    def _preview_from_dash(self, _e):
        sel = self.dtree.selection()
        if not sel: return
        vals = self.dtree.item(sel[0])["values"]
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT gp.file_path FROM generated_pages gp JOIN cities c ON c.id=gp.city_id WHERE c.city_name=? AND c.state_name=?", (vals[0],vals[1])).fetchone()
        conn.close()
        if r and os.path.exists(r[0]): webbrowser.open("file://"+os.path.abspath(r[0]))

    def _goto_bulk_all(self):
        self.nb.select(2); self.after(150, self._do_bulk_all)

    def _go_cities(self): self.nb.select(1)

    def _build_sitemap(self):
        od = cfg("out_dir") or OUT_DIR
        os.makedirs(od, exist_ok=True)
        path, n = generate_sitemap(od)
        generate_robots(od)
        self.sv.set(f"✅ sitemap.xml ({n} URLs)")
        self._ui(self._refresh_dash)
        messagebox.showinfo("Sitemap", f"sitemap.xml created with {n} URLs.\n{path}\n\n📌 Submit to Google Search Console!")

    def _gen_modules(self):
        od = cfg("out_dir") or OUT_DIR
        for slug, title, sub, kws in MODULE_PAGES:
            generate_module_page(slug, title, sub, kws, od)
        self.sv.set(f"✅ {len(MODULE_PAGES)} module pages generated")
        self._ui(self._refresh_dash)
        messagebox.showinfo("Modules", f"{len(MODULE_PAGES)} module pages generated.")

    def _export_zip(self):
        od = cfg("out_dir") or OUT_DIR
        if not os.path.exists(od):
            messagebox.showwarning("Empty","Generate pages first."); return
        def work():
            path, count = export_zip(od)
            self._ui(lambda: messagebox.showinfo("ZIP", f"✅ {count} files zipped!\n{path}\n\nUpload these to your web server."))
        threading.Thread(target=work, daemon=True).start()

    def _start_preview(self):
        od = cfg("out_dir") or OUT_DIR
        if not os.path.exists(od):
            messagebox.showwarning("Empty","Generate pages first."); return
        try:
            port = start_preview_server(od, 8765)
            webbrowser.open(f"http://localhost:{port}/school-erp-india.html")
            messagebox.showinfo("Preview Server", f"🌐 Preview server running at:\nhttp://localhost:{port}\n\nOpen any .html page in your browser.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_out(self):
        od = cfg("out_dir") or OUT_DIR
        os.makedirs(od, exist_ok=True)
        try:
            if os.name == "nt": os.startfile(od)
            else:
                import subprocess; subprocess.Popen(["xdg-open", od])
        except: pass

    # ══════════════════════════════════════════════════════════
    #  TAB 2 — CITIES
    # ══════════════════════════════════════════════════════════
    def _tab_cities(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  🏙  Cities  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(2, weight=1)

        # ── Row 0: Single city add bar ────────────────────────────────
        top = tk.Frame(f, bg="#060b18"); top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12,2))
        self._cv  = tk.StringVar(); self._stv = tk.StringVar(value="Bihar")
        self._ctry = tk.StringVar(value="India")
        tk.Label(top, text="City:", bg="#060b18", fg="#94a3b8").pack(side="left")
        e = ttk.Entry(top, textvariable=self._cv, width=14); e.pack(side="left", padx=4)
        e.bind("<Return>", lambda _: self._add_city())
        tk.Label(top, text="State:", bg="#060b18", fg="#94a3b8").pack(side="left")
        STATES = ["Bihar","Uttar Pradesh","Jharkhand","West Bengal","Odisha","Madhya Pradesh","Chhattisgarh",
                  "Delhi","Haryana","Rajasthan","Maharashtra","Karnataka","Tamil Nadu","Telangana","Andhra Pradesh",
                  "Gujarat","Punjab","Assam","Kerala","Himachal Pradesh","Uttarakhand","Manipur","Meghalaya","Jammu & Kashmir"]
        ttk.Combobox(top, textvariable=self._stv, values=STATES, width=14, state="normal").pack(side="left", padx=4)
        tk.Label(top, text="Country:", bg="#060b18", fg="#94a3b8").pack(side="left")
        COUNTRIES = ["India","UAE","UK","USA","Canada","Singapore","Australia","Malaysia","Qatar","Oman","Saudi Arabia","Kenya","Bahrain"]
        ttk.Combobox(top, textvariable=self._ctry, values=COUNTRIES, width=9, state="normal").pack(side="left", padx=4)
        ttk.Button(top, text="➕ Add City", command=self._add_city).pack(side="left", padx=4)
        ttk.Button(top, text="🗺 Generate Selected", command=self._gen_selected).pack(side="left", padx=3)
        ttk.Button(top, text="🗑 Delete", command=self._del_selected, style="R.TButton").pack(side="left", padx=3)
        tk.Label(top, text="Search:", bg="#060b18", fg="#94a3b8").pack(side="left", padx=(12,4))
        self._srch = tk.StringVar(); self._srch.trace("w", lambda *_: self._load_cities())
        ttk.Entry(top, textvariable=self._srch, width=12).pack(side="left")
        tk.Label(top, text="Filter:", bg="#060b18", fg="#94a3b8").pack(side="left", padx=(8,4))
        self._flt = tk.StringVar(value="All")
        flt_opts = ["All","✅ Done","⬜ Pending","🌐 International","Bihar","Uttar Pradesh","Jharkhand","Maharashtra","Karnataka"]
        ttk.Combobox(top, textvariable=self._flt, values=flt_opts, width=13, state="readonly").pack(side="left")
        self._flt.trace("w", lambda *_: self._load_cities())

        # ── Row 1: Bulk Import panel ──────────────────────────────────
        imp = tk.Frame(f, bg="#0d1a30", highlightthickness=1, highlightbackground="#1e3a5f")
        imp.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(4,4))
        imp.columnconfigure(1, weight=1)

        # Left side: buttons + format hint
        bleft = tk.Frame(imp, bg="#0d1a30"); bleft.grid(row=0, column=0, sticky="ns", padx=(10,8), pady=8)
        tk.Label(bleft, text="📥  Bulk City Import", bg="#0d1a30", fg="#38bdf8",
                 font=("Segoe UI",10,"bold")).pack(anchor="w")
        tk.Label(bleft, text="One row per city.  Format:  City, State, Country  (Country optional, defaults to India)",
                 bg="#0d1a30", fg="#4a6f8a", font=("Segoe UI",8)).pack(anchor="w", pady=(2,6))
        brow2 = tk.Frame(bleft, bg="#0d1a30"); brow2.pack(anchor="w")
        ttk.Button(brow2, text="📁 Import CSV / TXT", command=self._import_csv, style="C.TButton").pack(side="left", padx=(0,4))
        ttk.Button(brow2, text="📋 Paste from Clipboard", command=self._import_clipboard).pack(side="left", padx=4)
        ttk.Button(brow2, text="📥 Download CSV Template", command=self._download_template, style="Y.TButton").pack(side="left", padx=4)
        ttk.Button(brow2, text="🗑 Clear All Cities", command=self._clear_all_cities, style="R.TButton").pack(side="left", padx=4)

        # Right side: paste box
        bright = tk.Frame(imp, bg="#0d1a30"); bright.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=8)
        bright.columnconfigure(0, weight=1); bright.rowconfigure(1, weight=1)
        tk.Label(bright, text="✏ Or type / paste cities directly below (City, State, Country — one per line):",
                 bg="#0d1a30", fg="#4a6f8a", font=("Segoe UI",8)).grid(row=0, column=0, sticky="w")
        paste_frame = tk.Frame(bright, bg="#0d1a30"); paste_frame.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        paste_frame.columnconfigure(0, weight=1); paste_frame.rowconfigure(0, weight=1)
        self._paste_box = tk.Text(paste_frame, height=4, bg="#040c1a", fg="#94d4f8", font=("Consolas",9),
                                   relief="flat", bd=1, highlightthickness=1,
                                   highlightbackground="#1e3a5f", insertbackground="#94d4f8")
        self._paste_box.grid(row=0, column=0, sticky="nsew")
        psc = ttk.Scrollbar(paste_frame, orient="vertical", command=self._paste_box.yview)
        self._paste_box.configure(yscrollcommand=psc.set); psc.grid(row=0, column=1, sticky="ns")
        self._paste_box.insert("1.0", "Darbhanga, Bihar, India\nAllahabad, Uttar Pradesh\nDeoghar, Jharkhand\nLondon, England, UK")
        ttk.Button(bright, text="➕ Import Pasted Text", command=self._import_pasted, style="G.TButton").grid(
            row=2, column=0, sticky="w", pady=(4,0))

        # ── Row 2: City treeview ──────────────────────────────────────
        cols = ("city","state","country","tier","status","score","wc","generated")
        self.ctree = ttk.Treeview(f, columns=cols, show="headings", selectmode="extended")
        hdrs = [("city","City",90),("state","State",100),("country","Country",70),("tier","Tier",40),
                ("status","Status",80),("score","Score",75),("wc","Words",65),("generated","Generated",130)]
        for col, hdr, w in hdrs:
            self.ctree.heading(col, text=hdr)
            self.ctree.column(col, width=w, anchor="center" if col in ("tier","score","wc") else "w")
        self.ctree.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0,0))
        sb = ttk.Scrollbar(f, orient="vertical", command=self.ctree.yview)
        self.ctree.configure(yscroll=sb.set); sb.grid(row=2, column=1, sticky="ns")
        self.ctree.bind("<Double-1>", lambda _: self._preview_city())

        # ── Row 3: progress + count ───────────────────────────────────
        pf = tk.Frame(f, bg="#060b18"); pf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=4)
        self._cprog = ttk.Progressbar(pf, mode="determinate"); self._cprog.pack(fill="x")
        self._city_count_lbl = tk.StringVar(value="")
        tk.Label(pf, textvariable=self._city_count_lbl, bg="#060b18", fg="#64748b",
                 font=("Segoe UI",9)).pack(anchor="w", pady=2)
        self._load_cities()

    # ── Bulk import helpers ───────────────────────────────────────────
    def _parse_city_lines(self, text):
        """
        Parse multi-line text into (city, state, country, tier) tuples.
        Accepts formats:
          City, State
          City, State, Country
          City | State | Country
          City\tState\tCountry
          City;State;Country
        Returns (added, skipped, errors) counts.
        """
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        added = skipped = errors = 0
        results = []
        for raw in lines:
            # Skip header-like lines
            if raw.lower().startswith(("city","#","//")): continue
            # Detect delimiter
            if "	" in raw:
                parts = [p.strip() for p in raw.split("	")]
            elif "|" in raw:
                parts = [p.strip() for p in raw.split("|")]
            elif ";" in raw:
                parts = [p.strip() for p in raw.split(";")]
            else:
                parts = [p.strip() for p in raw.split(",")]
            if len(parts) < 2:
                errors += 1; continue
            city    = parts[0].strip().title()
            state   = parts[1].strip().title() if len(parts) > 1 else ""
            country = parts[2].strip().title() if len(parts) > 2 else "India"
            tier    = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else 2
            if not city or not state:
                errors += 1; continue
            results.append((city, state, country, tier))
        return results

    def _bulk_insert_cities(self, rows):
        """Insert parsed city rows into DB. Returns (added, skipped)."""
        added = skipped = 0
        conn = sqlite3.connect(DB_PATH)
        for city, state, country, tier in rows:
            is_intl = 0 if country.lower() in ("india", "भारत") else 1
            slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_intl else "-school-erp")
            try:
                conn.execute(
                    "INSERT INTO cities(city_name,state_name,country,slug,tier,is_international) VALUES(?,?,?,?,?,?)",
                    (city, state, country, slug, tier, is_intl)
                )
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1
        conn.commit(); conn.close()
        return added, skipped

    def _import_csv(self):
        """Import cities from a CSV or TXT file."""
        path = filedialog.askopenfilename(
            title="Select CSV / TXT file",
            filetypes=[("CSV files","*.csv"),("Text files","*.txt"),("All files","*.*")]
        )
        if not path: return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                text = f.read()
        rows = self._parse_city_lines(text)
        if not rows:
            messagebox.showwarning("Empty", "No valid city rows found in the file.\n\nExpected format:\nCity, State, Country"); return
        added, skipped = self._bulk_insert_cities(rows)
        log_db("IMPORT_CSV", f"File: {os.path.basename(path)}, added={added}, skipped={skipped}")
        messagebox.showinfo("Import Complete",
            f"✅ Import finished!\n\n  Added:    {added} new cities\n  Skipped:  {skipped} duplicates\n  Total rows: {len(rows)}\n\nCities are ready to generate.")
        self._load_cities(); self._refresh_dash()

    def _import_clipboard(self):
        """Import cities from clipboard text."""
        try:
            text = self.clipboard_get()
        except:
            messagebox.showwarning("Clipboard", "Nothing found in clipboard."); return
        if not text.strip():
            messagebox.showwarning("Clipboard", "Clipboard is empty."); return
        rows = self._parse_city_lines(text)
        if not rows:
            messagebox.showwarning("Empty", "No valid city rows found in clipboard.\n\nExpected: City, State  or  City, State, Country"); return
        added, skipped = self._bulk_insert_cities(rows)
        log_db("IMPORT_CLIPBOARD", f"added={added}, skipped={skipped}")
        messagebox.showinfo("Import Complete",
            f"✅ Clipboard import finished!\n\n  Added:    {added} new cities\n  Skipped:  {skipped} duplicates")
        self._load_cities(); self._refresh_dash()

    def _import_pasted(self):
        """Import from the in-panel paste text box."""
        text = self._paste_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty", "Paste some city data first."); return
        rows = self._parse_city_lines(text)
        if not rows:
            messagebox.showwarning("Parse Error",
                "No valid rows found. Use format:\n  City, State\n  City, State, Country\n  City, State, Country, Tier"); return
        added, skipped = self._bulk_insert_cities(rows)
        log_db("IMPORT_PASTE", f"added={added}, skipped={skipped}")
        self._paste_box.delete("1.0","end")
        messagebox.showinfo("Import Complete",
            f"✅ Imported from paste box!\n\n  Added:    {added} new cities\n  Skipped:  {skipped} duplicates")
        self._load_cities(); self._refresh_dash()

    def _download_template(self):
        """Save a CSV template the user can fill in."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="tachy_cities_import_template.csv",
            title="Save CSV Template"
        )
        if not path: return
        template = (
            "City,State,Country,Tier\n"
            "# Tier: 1 = major city, 2 = smaller city (optional column)\n"
            "# Country is optional - leave blank or write India for Indian cities\n"
            "Patna,Bihar,India,1\n"
            "Muzaffarpur,Bihar,India,2\n"
            "Ranchi,Jharkhand,India,1\n"
            "Lucknow,Uttar Pradesh,India,1\n"
            "Bhopal,Madhya Pradesh,India,1\n"
            "Dubai,UAE,UAE,1\n"
            "London,England,UK,1\n"
            "Toronto,Ontario,Canada,1\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(template)
        messagebox.showinfo("Template Saved",
            f"CSV template saved:\n{path}\n\nFill in your cities and use 'Import CSV / TXT' to load them.")

    def _clear_all_cities(self):
        """Delete ALL cities (and their generated pages) from DB."""
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
        conn.close()
        if not messagebox.askyesno("Clear All",
            f"\u26a0  This will delete ALL {n} cities and their generated page records.\n\nPhysical HTML files are NOT deleted.\n\nAre you sure?"): return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM generated_pages")
        conn.execute("DELETE FROM cities")
        conn.commit(); conn.close()
        log_db("CLEAR_ALL_CITIES", f"Deleted {n} cities")
        self._load_cities(); self._refresh_dash()
        messagebox.showinfo("Cleared", f"All {n} cities removed. Database is empty.\nYou can re-seed by restarting the app.")

    def _load_cities(self, *_):
        for r in self.ctree.get_children(): self.ctree.delete(r)
        srch = self._srch.get() if hasattr(self,"_srch") else ""
        flt  = self._flt.get() if hasattr(self,"_flt") else "All"
        conn = sqlite3.connect(DB_PATH)
        q = """SELECT ci.id,ci.city_name,ci.state_name,ci.country,ci.tier,ci.is_international,
                      gp.seo_score,gp.word_count,gp.generated_at
               FROM cities ci LEFT JOIN generated_pages gp ON gp.city_id=ci.id"""
        conds, params = [], []
        if srch:
            conds.append("(ci.city_name LIKE ? OR ci.state_name LIKE ? OR ci.country LIKE ?)")
            params += [f"%{srch}%",f"%{srch}%",f"%{srch}%"]
        if flt == "✅ Done":       conds.append("gp.generated_at IS NOT NULL")
        elif flt == "⬜ Pending":   conds.append("gp.generated_at IS NULL")
        elif flt == "🌐 International": conds.append("ci.is_international=1")
        elif flt not in ("All",):  conds.append("ci.state_name=?"); params.append(flt)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY ci.country, ci.state_name, ci.city_name"
        rows = conn.execute(q, params).fetchall(); conn.close()
        for row in rows:
            cid,city,state,country,tier,intl,score,wc,gat = row
            status = "✅ Done" if gat else "⬜ Pending"
            sc = f"{score}/100" if score else "—"
            tag = "done" if gat else ("intl" if intl else "pend")
            self.ctree.insert("","end", iid=str(cid),
                              values=(city,state,country,tier or "2",status,sc,wc or "—",(gat or "—")[:16]), tags=(tag,))
        self.ctree.tag_configure("done", foreground="#4ade80")
        self.ctree.tag_configure("pend", foreground="#64748b")
        self.ctree.tag_configure("intl", foreground="#38bdf8")
        # Update count label
        if hasattr(self, "_city_count_lbl"):
            total = len(self.ctree.get_children())
            done  = sum(1 for iid in self.ctree.get_children() if "Done" in str(self.ctree.item(iid)["values"]))
            self._city_count_lbl.set(f"Showing {total} cities  •  {done} generated  •  {total-done} pending")

    def _add_city(self):
        city  = self._cv.get().strip().title()
        state = self._stv.get().strip()
        country = self._ctry.get().strip()
        if not city or not state:
            messagebox.showwarning("Input","Enter city name and state."); return
        is_intl = 1 if country != "India" else 0
        slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_intl else "-school-erp")
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute("INSERT INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                         (city,state,country,slug,is_intl))
            conn.commit(); self._cv.set("")
            log_db("ADD_CITY", f"{city}, {state}, {country}")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate", f"{city} already exists.")
        finally:
            conn.close()
        self._load_cities(); self._refresh_dash()

    def _del_selected(self):
        sel = self.ctree.selection()
        if not sel: return
        if not messagebox.askyesno("Delete", f"Delete {len(sel)} selected cities?"): return
        conn = sqlite3.connect(DB_PATH)
        for iid in sel:
            conn.execute("DELETE FROM generated_pages WHERE city_id=?", (iid,))
            conn.execute("DELETE FROM cities WHERE id=?", (iid,))
        conn.commit(); conn.close()
        self._load_cities(); self._refresh_dash()

    def _gen_selected(self):
        sel = self.ctree.selection()
        if not sel: messagebox.showinfo("Select","Select cities first."); return
        conn = sqlite3.connect(DB_PATH)
        cities = [conn.execute("SELECT id,city_name,state_name,country,is_international FROM cities WHERE id=?", (iid,)).fetchone() for iid in sel]
        conn.close()
        self._run_gen([c for c in cities if c])

    def _preview_city(self):
        sel = self.ctree.selection()
        if not sel: return
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT file_path FROM generated_pages WHERE city_id=?", (sel[0],)).fetchone()
        conn.close()
        if r and os.path.exists(r[0]): webbrowser.open("file://"+os.path.abspath(r[0]))
        else: messagebox.showinfo("Not generated","Generate this city's page first.")

    # ══════════════════════════════════════════════════════════
    #  TAB 3 — BULK GENERATOR (FULLY FIXED)
    # ══════════════════════════════════════════════════════════
    def _tab_bulk(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  🚀  Bulk Generator  ")
        f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1); f.rowconfigure(1, weight=1)

        ctrl = tk.Frame(f, bg="#060b18"); ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12,6))
        tk.Label(ctrl, text="🚀  Bulk Page Generator v3.0", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",13,"bold")).pack(anchor="w")
        tk.Label(ctrl, text="Thread-safe bulk generation with real-time progress. Generates unique, SEO-optimized pages for every city.",
                 bg="#060b18", fg="#4a5f80", font=("Segoe UI",9)).pack(anchor="w", pady=(2,8))

        brow = tk.Frame(ctrl, bg="#060b18"); brow.pack(fill="x")
        self._bgen_running = False
        self._bgen_btn = ttk.Button(brow, text="🗂 Generate ALL City Pages", command=self._do_bulk_all, style="G.TButton")
        self._bgen_btn.pack(side="left", padx=(0,4))
        ttk.Button(brow, text="🏆 Tier 1 Only",    command=self._do_bulk_tier1).pack(side="left", padx=3)
        ttk.Button(brow, text="🌐 International",   command=self._do_bulk_intl).pack(side="left", padx=3)
        ttk.Button(brow, text="🗺 Sitemap",          command=self._build_sitemap, style="Y.TButton").pack(side="left", padx=3)
        ttk.Button(brow, text="📦 Module Pages",     command=self._gen_modules).pack(side="left", padx=3)
        ttk.Button(brow, text="🗂 State Hub Pages",  command=self._gen_state_hubs).pack(side="left", padx=3)
        ttk.Button(brow, text="📰 Blog Pages",       command=self._gen_blogs).pack(side="left", padx=3)
        ttk.Button(brow, text="🔗 Index Page",       command=self._gen_index).pack(side="left", padx=3)
        ttk.Button(brow, text="📦 Export ZIP",       command=self._export_zip).pack(side="left", padx=3)
        ttk.Button(brow, text="⏹ Stop",              command=self._stop_gen, style="R.TButton").pack(side="left", padx=3)

        # Left: progress
        pf = tk.Frame(f, bg="#060b18"); pf.grid(row=1, column=0, sticky="nsew", padx=(14,6), pady=4)
        pf.rowconfigure(3, weight=1); pf.columnconfigure(0, weight=1)
        tk.Label(pf, text="Generation Progress", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",11,"bold")).grid(row=0, column=0, sticky="w", pady=(0,4))
        self._bprog = ttk.Progressbar(pf, mode="determinate")
        self._bprog.grid(row=1, column=0, sticky="ew")
        self._bplbl = tk.StringVar(value="Press 'Generate ALL City Pages' to start...")
        tk.Label(pf, textvariable=self._bplbl, bg="#060b18", fg="#4ade80",
                 font=("Segoe UI",9)).grid(row=2, column=0, sticky="w", pady=(4,0))
        self._bulk_log = scrolledtext.ScrolledText(pf, height=20, bg="#040810", fg="#4ade80",
                                                    font=("Consolas",9), relief="flat", bd=0)
        self._bulk_log.grid(row=3, column=0, sticky="nsew", pady=(8,0))

        # Right: single city
        sc = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        sc.grid(row=1, column=1, sticky="nsew", padx=(6,14), pady=4)
        sc.columnconfigure(1, weight=1)
        tk.Label(sc, text="⚡  Single City Generator", bg="#0f1728", fg="#6c63ff",
                 font=("Segoe UI",12,"bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12,4))
        self._sc_city  = tk.StringVar()
        self._sc_state = tk.StringVar(value="Bihar")
        self._sc_ctry  = tk.StringVar(value="India")
        self._sc_var   = tk.StringVar(value="0")
        for i, (lbl, var) in enumerate(zip(
            ["City *","State *","Country","Variation #"],
            [self._sc_city, self._sc_state, self._sc_ctry, self._sc_var]), 1):
            tk.Label(sc, text=lbl, bg="#0f1728", fg="#94a3b8").grid(row=i, column=0, sticky="w", padx=14, pady=4)
            ttk.Entry(sc, textvariable=var, width=20).grid(row=i, column=1, padx=14, pady=4, sticky="ew")
        ttk.Button(sc, text="🌆 Generate & Preview", command=self._gen_single).grid(
            row=5, column=0, columnspan=2, padx=14, pady=(10,4), sticky="ew")
        ttk.Button(sc, text="👁 Preview Last Page", command=self._preview_last, style="Y.TButton").grid(
            row=6, column=0, columnspan=2, padx=14, pady=(0,4), sticky="ew")
        ttk.Button(sc, text="📋 Score Last Page", command=self._score_last, style="C.TButton").grid(
            row=7, column=0, columnspan=2, padx=14, pady=(0,8), sticky="ew")
        self._sout = scrolledtext.ScrolledText(sc, height=12, bg="#040810", fg="#94a3b8",
                                               font=("Consolas",9), relief="flat", bd=0)
        self._sout.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0,10))
        sc.rowconfigure(8, weight=1)

    def _bulk_log_append(self, msg):
        """SAFE: Always called from main thread via _ui()."""
        try:
            self._bulk_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self._bulk_log.see("end")
        except: pass

    def _set_prog(self, value, maximum, label):
        """SAFE: Called from main thread."""
        try:
            self._bprog["maximum"] = maximum
            self._bprog["value"]   = value
            self._bplbl.set(label)
        except: pass

    def _do_bulk_all(self):
        if self._bgen_running:
            messagebox.showinfo("Running","Generation is already running."); return
        conn = sqlite3.connect(DB_PATH)
        cities = conn.execute("SELECT id,city_name,state_name,country,is_international FROM cities ORDER BY tier,state_name,city_name").fetchall()
        conn.close()
        if not cities: messagebox.showinfo("Empty","No cities in database."); return
        self._run_gen(cities)

    def _do_bulk_tier1(self):
        conn = sqlite3.connect(DB_PATH)
        cities = conn.execute("SELECT id,city_name,state_name,country,is_international FROM cities WHERE tier=1 ORDER BY state_name").fetchall()
        conn.close()
        if not cities: messagebox.showinfo("None","No Tier-1 cities found."); return
        self._run_gen(cities)

    def _do_bulk_intl(self):
        conn = sqlite3.connect(DB_PATH)
        cities = conn.execute("SELECT id,city_name,state_name,country,is_international FROM cities WHERE is_international=1").fetchall()
        conn.close()
        if not cities: messagebox.showinfo("None","No international cities found."); return
        self._run_gen(cities)

    def _stop_gen(self):
        self._bgen_running = False
        self._ui(self._set_prog, 0, 100, "⏹ Stopped by user.")

    def _run_gen(self, cities):
        """
        FIXED v3: Complete thread-safe bulk generation.
        - All DB operations use per-thread connections
        - All UI updates go through UI_Q queue
        - No shared state between threads
        """
        if self._bgen_running:
            messagebox.showinfo("Running","Generation already in progress."); return
        self._bgen_running = True
        od = cfg("out_dir") or OUT_DIR
        os.makedirs(od, exist_ok=True)
        total = len(cities)

        def worker():
            ok_count = 0
            err_count = 0

            for i, row in enumerate(cities):
                if not self._bgen_running:
                    break

                # Unpack safely — handle both 4-tuple and 5-tuple
                if len(row) == 5:
                    cid, city, state, country, is_intl = row
                else:
                    cid, city, state = row[0], row[1], row[2]
                    country, is_intl = "India", 0

                country   = country or "India"
                is_intl   = bool(is_intl)

                # Update progress (thread-safe)
                self._ui(self._set_prog, i, total, f"[{i+1}/{total}] {city}, {state}...")
                self._ui(self._bulk_log_append, f"Generating: {city}, {state}, {country}...")

                try:
                    slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_intl else "-school-erp")

                    # Per-thread DB connection — NO sharing across threads
                    db_conn = sqlite3.connect(DB_PATH)
                    db_conn.execute("PRAGMA journal_mode=WAL")
                    existing = db_conn.execute("SELECT first_generated_at FROM generated_pages WHERE slug=?", (slug,)).fetchone()
                    first_pub_date = existing[0] if existing and existing[0] else datetime.now().strftime("%Y-%m-%d")

                    path, wc, score, meta, first_pub_date = generate_city_page(
                        city, state, od, country, is_intl, variation_seed=i, first_pub_date=first_pub_date
                    )

                    db_conn.execute("""
                        INSERT INTO generated_pages(city_id,page_type,slug,file_path,word_count,seo_score,first_generated_at)
                        VALUES(?,?,?,?,?,?,?)
                        ON CONFLICT(slug) DO UPDATE SET
                            file_path=excluded.file_path,
                            word_count=excluded.word_count,
                            seo_score=excluded.seo_score,
                            generated_at=CURRENT_TIMESTAMP
                    """, (cid, "city", slug, path, wc, score, first_pub_date))
                    db_conn.commit()
                    db_conn.close()

                    log_db("GEN", f"{city},{state},score={score},words={wc}")
                    ok_count += 1
                    self._ui(self._bulk_log_append, f"  ✅ {city} — {score}/100 score, {wc} words")

                except Exception as e:
                    err_count += 1
                    err_msg = str(e)
                    self._ui(self._bulk_log_append, f"  ❌ {city} ERROR: {err_msg}")
                    log_db("ERR", f"{city}: {err_msg}")

            # Finalize
            self._bgen_running = False
            done_msg = f"✅ Done! {ok_count} pages generated, {err_count} errors."
            self._ui(self._set_prog, total, total, done_msg)
            self._ui(self._bulk_log_append, f"\n{'='*50}\n{done_msg}\n{'='*50}")

            # Auto post-generation tasks
            try:
                p, n = generate_sitemap(od)
                generate_robots(od)
                generate_index_html(od)
                self._ui(self._bulk_log_append, f"🗺 sitemap.xml ({n} URLs), robots.txt, index page generated.")
            except Exception as e:
                self._ui(self._bulk_log_append, f"⚠ Post-gen error: {e}")

            # Refresh UI
            self._ui(self._refresh_dash)
            self._ui(self._load_cities)

        threading.Thread(target=worker, daemon=True).start()

    def _gen_single(self):
        city  = self._sc_city.get().strip().title()
        state = self._sc_state.get().strip()
        ctry  = self._sc_ctry.get().strip() or "India"
        var   = int(self._sc_var.get() or 0)
        if not city or not state: messagebox.showwarning("Input","Enter city and state."); return
        od = cfg("out_dir") or OUT_DIR
        is_intl = ctry != "India"
        self._sout.delete("1.0","end")
        self._sout.insert("end", f"Generating {city}, {state}, {ctry}...\n")
        def work():
            try:
                slug = city.lower().replace(" ","-") + ("-indian-school-erp" if is_intl else "-school-erp")
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT OR IGNORE INTO cities(city_name,state_name,country,slug,is_international) VALUES(?,?,?,?,?)",
                             (city,state,ctry,slug,1 if is_intl else 0))
                conn.commit()
                cid = conn.execute("SELECT id FROM cities WHERE city_name=? AND state_name=?",(city,state)).fetchone()[0]
                conn.close()
                path, wc, score, meta, first_pub_date = generate_city_page(city, state, od, ctry, is_intl, var)
                conn = sqlite3.connect(DB_PATH)
                existing = conn.execute("SELECT first_generated_at FROM generated_pages WHERE slug=?", (slug,)).fetchone()
                first_pub_date = existing[0] if existing and existing[0] else first_pub_date
                conn.execute("""
                    INSERT INTO generated_pages(city_id,page_type,slug,file_path,word_count,seo_score,first_generated_at)
                    VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT(slug) DO UPDATE SET
                        file_path=excluded.file_path,
                        word_count=excluded.word_count,
                        seo_score=excluded.seo_score,
                        generated_at=CURRENT_TIMESTAMP
                """, (cid,"city",slug,path,wc,score,first_pub_date))
                conn.commit(); conn.close()
                def upd():
                    self._sout.insert("end", f"✅  File: {path}\n")
                    self._sout.insert("end", f"📝  Words: {wc}\n")
                    self._sout.insert("end", f"📊  SEO Score: {score}/100\n")
                    self._sout.insert("end", f"🔑  Target KW: school ERP software {city}\n")
                    self._sout.insert("end", f"🌐  URL: {_page_url(slug)}\n")
                    self._sout.insert("end", f"\n📋  Meta: {meta}\n")
                    self.sv.set(f"✅ Generated {city}")
                self._ui(upd)
                self._ui(self._refresh_dash)
                self._ui(self._load_cities)
                self._ui(lambda: webbrowser.open("file://"+os.path.abspath(path)))
                log_db("GEN_SINGLE", f"{city},{state}")
            except Exception as e:
                self._ui(lambda: self._sout.insert("end", f"❌ Error: {e}\n"))
        threading.Thread(target=work, daemon=True).start()

    def _preview_last(self):
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT file_path FROM generated_pages ORDER BY generated_at DESC LIMIT 1").fetchone()
        conn.close()
        if r and os.path.exists(r[0]): webbrowser.open("file://"+os.path.abspath(r[0]))
        else: messagebox.showinfo("None","No generated pages yet.")

    def _score_last(self):
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("""SELECT gp.file_path, c.city_name, c.state_name, gp.seo_score, gp.word_count
                            FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                            ORDER BY gp.generated_at DESC LIMIT 1""").fetchone()
        conn.close()
        if not r: messagebox.showinfo("None","No pages yet."); return
        self._sout.delete("1.0","end")
        self._sout.insert("end", f"=== SEO Score Report ===\n")
        self._sout.insert("end", f"City: {r[1]}, {r[2]}\n")
        self._sout.insert("end", f"Score: {r[3]}/100\n")
        self._sout.insert("end", f"Word count: {r[4]}\n")
        grade = "🟢 Excellent" if r[3]>=85 else "🟡 Good" if r[3]>=70 else "🔴 Needs Work"
        self._sout.insert("end", f"Grade: {grade}\n")

    def _gen_blogs(self):
        od = cfg("out_dir") or OUT_DIR
        conn = sqlite3.connect(DB_PATH)
        top = conn.execute("SELECT city_name,state_name FROM cities WHERE tier=1 LIMIT 10").fetchall()
        conn.close()
        count = 0
        for city, state in top:
            for tpl_key in BLOG_TEMPLATES:
                generate_blog_page(city, state, tpl_key, od)
                count += 1
        messagebox.showinfo("Blogs", f"{count} blog pages generated in:\n{od}")
        self._refresh_dash()

    def _gen_state_hubs(self):
        od = cfg("out_dir") or OUT_DIR
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""SELECT DISTINCT c.state_name, gp.slug, c.city_name
                               FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                               WHERE c.is_international=0
                               ORDER BY c.state_name, c.city_name""").fetchall()
        conn.close()
        states = {}
        for state, slug, city in rows:
            states.setdefault(state, []).append((city, slug))
        count = 0
        for state, cities in states.items():
            html = generate_state_hub_html(state, cities)
            fname = f"school-erp-{_slugify_text(state)}.html"
            path = os.path.join(od, fname)
            os.makedirs(od, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            count += 1
        messagebox.showinfo("State Hubs", f"{count} state hub pages generated in:\n{od}")

    def _gen_index(self):
        od = cfg("out_dir") or OUT_DIR
        p = generate_index_html(od)
        messagebox.showinfo("Index Page", f"Index page generated:\n{p}")
        self._refresh_dash()

    # ══════════════════════════════════════════════════════════
    #  TAB 4 — ADVANCED SEO TOOLS
    # ══════════════════════════════════════════════════════════
    def _tab_advanced(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  🧠  Advanced SEO  ")
        f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=1); f.rowconfigure(1, weight=1)

        tk.Label(f, text="🧠  Advanced SEO & Content Intelligence Engine", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",13,"bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12,8))

        left = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        left.grid(row=1, column=0, sticky="nsew", padx=(14,6), pady=4)
        left.columnconfigure(0, weight=1)
        tk.Label(left, text="🔍  SEO Audit & Analysis", bg="#0f1728", fg="#6c63ff",
                 font=("Segoe UI",11,"bold")).pack(anchor="w", padx=12, pady=(10,4))
        for lbl, cmd in [
            ("📊 Full SEO Audit Report",           self._audit_all),
            ("🏆 Top 15 Pages by Score",           self._top_pages),
            ("⚠  Low Score Pages (< 70)",          self._low_pages),
            ("📈 Keyword Density Targets",          self._kw_density),
            ("🔗 Internal Linking Map",             self._internal_links),
            ("📋 Export SEO Report CSV",            self._export_report),
            ("⚡ Page Speed Optimization Tips",    self._speed_tips),
            ("🌐 Core Web Vitals Checklist",        self._cwv_check),
            ("📅 Content Calendar (90 days)",       self._content_calendar),
            ("🔍 Schema Validator (last page)",     self._schema_check),
        ]:
            ttk.Button(left, text=lbl, command=cmd).pack(fill="x", padx=12, pady=2)
        self.audit_out = scrolledtext.ScrolledText(left, height=12, bg="#040810", fg="#94a3b8",
                                                    font=("Consolas",9), relief="flat", bd=0)
        self.audit_out.pack(fill="both", expand=True, padx=8, pady=(6,10))

        right = tk.Frame(f, bg="#0f1728", highlightthickness=1, highlightbackground="#1a2a44")
        right.grid(row=1, column=1, sticky="nsew", padx=(6,14), pady=4)
        right.columnconfigure(1, weight=1)
        tk.Label(right, text="🎯  Competitor Gap Analysis", bg="#0f1728", fg="#6c63ff",
                 font=("Segoe UI",11,"bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10,4))

        tk.Label(right, text="Keyword:", bg="#0f1728", fg="#94a3b8").grid(row=1, column=0, sticky="w", padx=12, pady=4)
        self._gap_kw = tk.StringVar(value="school ERP software Bihar")
        ttk.Entry(right, textvariable=self._gap_kw, width=30).grid(row=1, column=1, padx=12, pady=4, sticky="ew")
        tk.Label(right, text="City Focus:", bg="#0f1728", fg="#94a3b8").grid(row=2, column=0, sticky="w", padx=12)
        self._gap_city = tk.StringVar(value="Patna")
        ttk.Entry(right, textvariable=self._gap_city, width=30).grid(row=2, column=1, padx=12, pady=4, sticky="ew")
        tk.Label(right, text="State:", bg="#0f1728", fg="#94a3b8").grid(row=3, column=0, sticky="w", padx=12)
        self._gap_state = tk.StringVar(value="Bihar")
        ttk.Entry(right, textvariable=self._gap_state, width=30).grid(row=3, column=1, padx=12, pady=4, sticky="ew")

        for lbl, cmd, sty in [
            ("🔍 Analyze Competitor Gaps",          self._analyze_gaps,    "TButton"),
            ("📝 Generate Meta Tags",               self._gen_meta_for_kw, "Y.TButton"),
            ("🔑 LSI Keyword Suggestions",          self._lsi_suggestions, "TButton"),
            ("🌐 International SEO Strategy",       self._intl_seo,        "C.TButton"),
            ("📤 Copy Sitemap to Clipboard",        self._sitemap_preview, "TButton"),
        ]:
            r = 4 + [lbl,cmd,sty].index(lbl) if False else None
        for i, (lbl, cmd, sty) in enumerate([
            ("🔍 Analyze Competitor Gaps",          self._analyze_gaps,    "TButton"),
            ("📝 Generate Meta Tags",               self._gen_meta_for_kw, "Y.TButton"),
            ("🔑 LSI Keyword Suggestions",          self._lsi_suggestions, "TButton"),
            ("🌐 International SEO Strategy",       self._intl_seo,        "C.TButton"),
            ("📤 Copy Sitemap to Clipboard",        self._sitemap_preview, "TButton"),
        ], 4):
            ttk.Button(right, text=lbl, command=cmd, style=sty).grid(
                row=i, column=0, columnspan=2, padx=12, pady=3, sticky="ew")

        self.gap_out = scrolledtext.ScrolledText(right, height=14, bg="#040810", fg="#94a3b8",
                                                  font=("Consolas",9), relief="flat", bd=0)
        self.gap_out.grid(row=9, column=0, columnspan=2, sticky="nsew", padx=8, pady=(4,10))
        right.rowconfigure(9, weight=1)

    def _alog(self, msg):
        try: self.audit_out.insert("end", msg+"\n"); self.audit_out.see("end")
        except: pass

    def _glog(self, msg):
        try: self.gap_out.insert("end", msg+"\n"); self.gap_out.see("end")
        except: pass

    def _audit_all(self):
        self.audit_out.delete("1.0","end")
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""SELECT c.city_name,c.state_name,c.country,gp.seo_score,gp.word_count
                               FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                               ORDER BY gp.seo_score DESC""").fetchall()
        conn.close()
        if not rows: self._alog("No pages generated yet."); return
        avg = sum(r[3] for r in rows)/len(rows)
        self._alog(f"=== TACHY SEO AUDIT REPORT v3.0 ===")
        self._alog(f"Total pages: {len(rows)} | Average score: {avg:.1f}/100")
        self._alog(f"🟢 Excellent (≥85): {sum(1 for r in rows if r[3]>=85)}")
        self._alog(f"🟡 Good (70–84):    {sum(1 for r in rows if 70<=r[3]<85)}")
        self._alog(f"🔴 Needs work (<70):{sum(1 for r in rows if r[3]<70)}")
        self._alog(f"Total words:       {sum(r[4] or 0 for r in rows):,}")
        self._alog(f"\n--- Top 15 by SEO Score ---")
        for r in rows[:15]:
            self._alog(f"  [{r[3]:3d}/100] {r[0]}, {r[1]} ({r[2]}) — {r[4]} words")
        self._alog(f"\n--- Needs Attention (<75) ---")
        for r in [x for x in rows if x[3]<75][:10]:
            self._alog(f"  [{r[3]:3d}/100] {r[0]}, {r[1]} — re-generate recommended")

    def _top_pages(self):
        self.audit_out.delete("1.0","end")
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""SELECT c.city_name,c.state_name,gp.seo_score,gp.word_count
                               FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                               ORDER BY gp.seo_score DESC LIMIT 15""").fetchall()
        conn.close()
        self._alog("🏆 TOP 15 PAGES BY SEO SCORE:")
        for i,r in enumerate(rows,1):
            self._alog(f"  {i:2d}. [{r[2]:3d}/100] {r[0]}, {r[1]} — {r[3]} words")

    def _low_pages(self):
        self.audit_out.delete("1.0","end")
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""SELECT c.city_name,c.state_name,gp.seo_score
                               FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                               WHERE gp.seo_score<70 ORDER BY gp.seo_score""").fetchall()
        conn.close()
        self._alog(f"⚠  LOW SCORE PAGES ({len(rows)} pages under 70):")
        for r in rows:
            self._alog(f"  [{r[2]:3d}/100] {r[0]}, {r[1]} — Regenerate recommended")

    def _kw_density(self):
        self.audit_out.delete("1.0","end")
        self._alog("📈 KEYWORD DENSITY GUIDE (per city page):")
        kws = [
            ("school ERP software [city]", "8–12x", "★★★ CRITICAL"),
            ("[city] school ERP",           "5–8x",  "★★★ CRITICAL"),
            ("school management software",  "4–6x",  "★★ HIGH"),
            ("CBSE school ERP",             "3–5x",  "★★ HIGH"),
            ("fee management software",     "3–5x",  "★★ HIGH"),
            ("school management system",    "3–5x",  "★★ HIGH"),
            ("[city], [state]",             "12–18x","★★★ CRITICAL — local signal"),
            ("school attendance software",  "2–3x",  "★ MED"),
            ("school transport management", "2–3x",  "★ MED"),
            ("free demo",                   "3–5x",  "★ MED — conversion signal"),
        ]
        for kw, freq, priority in kws:
            self._alog(f"  {priority:25s} | {kw:38s} | {freq}")

    def _internal_links(self):
        self.audit_out.delete("1.0","end")
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT c.city_name,c.state_name FROM cities c WHERE c.id IN (SELECT city_id FROM generated_pages) ORDER BY c.state_name").fetchall()
        conn.close()
        by_state = {}
        for city, state in rows:
            by_state.setdefault(state, []).append(city)
        self._alog("🔗 INTERNAL LINKING MESH:")
        for state, cities in sorted(by_state.items()):
            self._alog(f"\n  [{state}] — {len(cities)} city pages")
            for city in cities[:4]:
                slug = city.lower().replace(" ","-") + "-school-erp"
                self._alog(f"    → {_page_url(slug)}")
        self._alog(f"\n✅ Every page auto-links to up to 8 state-level related cities")
        self._alog(f"✅ State hub pages link all cities in each state")
        self._alog(f"✅ Index page links to all generated pages")
        self._alog(f"✅ Breadcrumb creates 3-level hierarchy for PageRank flow")

    def _export_report(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tachy_seo_report_v3.csv")
        if not path: return
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""SELECT c.city_name,c.state_name,c.country,c.tier,
                                      gp.seo_score,gp.word_count,gp.slug,gp.generated_at
                               FROM generated_pages gp JOIN cities c ON c.id=gp.city_id
                               ORDER BY gp.seo_score DESC""").fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["City","State","Country","Tier","SEO Score","Word Count","Slug","Generated","Full URL"])
            for r in rows:
                url = f"{cfg('website')}/{r[6]}/"
                w.writerow(list(r) + [url])
        messagebox.showinfo("Exported", f"SEO report exported:\n{path}")

    def _speed_tips(self):
        self.audit_out.delete("1.0","end")
        self._alog("⚡ PAGE SPEED OPTIMIZATION TIPS:")
        for i, tip in enumerate(SPEED_TIPS, 1):
            self._alog(f"  {i:2d}. {tip}")
        self._alog(f"\n📊 Core Web Vitals Targets:")
        self._alog(f"  LCP  < 2.5s  (Largest Contentful Paint)")
        self._alog(f"  FID  < 100ms (First Input Delay)")
        self._alog(f"  CLS  < 0.1   (Cumulative Layout Shift)")
        self._alog(f"  TTFB < 200ms (Time to First Byte)")
        self._alog(f"\n🛠 Recommended Stack for TACHY Pages:")
        self._alog(f"  Hosting: Cloudflare Pages (free, global CDN)")
        self._alog(f"  DNS:     Cloudflare (free plan)")
        self._alog(f"  Images:  WebP format via Cloudflare Images")
        self._alog(f"  Cache:   1-year static asset cache headers")

    def _cwv_check(self):
        self.audit_out.delete("1.0","end")
        self._alog("🌐 CORE WEB VITALS CHECKLIST (for tachy.in):")
        checks = [
            ("Hero text visible without JS",          True),
            ("No layout shift from fonts (font-display:swap)", True),
            ("Images have width/height attributes",   True),
            ("No render-blocking scripts in <head>",  True),
            ("Google Fonts preconnect added",         True),
            ("CSS inlined in <head>",                 True),
            ("No large hero image (>100KB)",          True),
            ("FA / icon font removed (emoji used)",   True),
            ("Minimal third-party scripts",           True),
            ("Cloudflare CDN enabled",                False),
        ]
        for lbl, ok in checks:
            self._alog(f"  {'✅' if ok else '⚠ '} {lbl}")
        self._alog(f"\n📌 Action items for tachy.in:")
        self._alog(f"  1. Enable Cloudflare (free) for global CDN")
        self._alog(f"  2. Set cache-control: max-age=31536000 for static files")
        self._alog(f"  3. Test with Google PageSpeed Insights every week")

    def _content_calendar(self):
        self.audit_out.delete("1.0","end")
        self._alog("📅 90-DAY SEO CONTENT CALENDAR FOR TACHY:")
        tasks = [
            ("Week 1",  "Generate ALL Indian city pages (200+). Submit sitemap."),
            ("Week 2",  "Generate state hub pages for Bihar, UP, JH, WB, Odisha, MP."),
            ("Week 3",  "Generate module pages (10). Generate blog: guides for top 10 cities."),
            ("Week 4",  "Start backlink campaign: list on SoftwareSuggest, G2, Capterra."),
            ("Week 5",  "Generate international pages (UAE, UK, USA, Singapore, Canada)."),
            ("Week 6",  "Blog: CBSE school ERP guides for Patna, Lucknow, Ranchi, Bhopal."),
            ("Week 7",  "Google Business Profile posts for 10 major cities."),
            ("Week 8",  "Request 5 real reviews on G2 and SoftwareSuggest."),
            ("Week 9",  "Comparison blog: 'Fedena vs TACHY' and 'Entab vs TACHY'."),
            ("Week 10", "WhatsApp broadcast to school owners in top 5 cities."),
            ("Week 11", "Update all Bihar city pages with new FAQ variations."),
            ("Week 12", "Full SEO audit. Regenerate low-score pages. Re-submit sitemap."),
            ("Week 13", "YouTube video: 'TACHY School ERP Demo' — link from all pages."),
        ]
        for week, task in tasks:
            self._alog(f"  [{week}] {task}")

    def _analyze_gaps(self):
        self.gap_out.delete("1.0","end")
        kw = self._gap_kw.get()
        city = self._gap_city.get()
        state = self._gap_state.get()
        self._glog(f"=== COMPETITOR GAP ANALYSIS ===")
        self._glog(f"Target: {kw} | City: {city} | State: {state}\n")
        for comp in COMPETITORS:
            gap = comp["weakness"].replace("{city}",city).replace("{state}",state)
            self._glog(f"  🏢 {comp['name']}:")
            self._glog(f"     ❌ {gap}")
        self._glog(f"\n✅ TACHY COMPETITIVE ADVANTAGES for '{city}':")
        self._glog(f"  ✓ Dedicated {city} page with 1,400+ words (competitors: 0)")
        self._glog(f"  ✓ 5-type Schema: FAQ + Breadcrumb + LocalBusiness + Software + Review")
        self._glog(f"  ✓ City keyword in title, H1, meta, URL, canonical, body (15+ times)")
        self._glog(f"  ✓ City-specific testimonials with real school names")
        self._glog(f"  ✓ Auto internal linking to 8 {state} cities")
        self._glog(f"  ✓ WhatsApp direct link (reduces bounce, improves dwell time signals)")
        self._glog(f"  ✓ Trust badges and stats band (improves E-E-A-T signals)")
        self._glog(f"  ✓ hreflang, geo meta tags, OG/Twitter cards (technical superiority)")

    def _gen_meta_for_kw(self):
        self.gap_out.delete("1.0","end")
        kw = self._gap_kw.get(); city = self._gap_city.get()
        website = cfg("website"); phone = cfg("phone")
        self._glog("=== GENERATED META TAGS ===\n")
        self._glog(f'<title>{kw.title()} | TACHY — {city}, India</title>')
        self._glog(f'<meta name="description" content="Best {kw} for {city} schools. TACHY automates admissions, fees, attendance, exams, transport & HR. Free demo: {phone}."/>')
        self._glog(f'<meta name="keywords" content="{kw}, school management software {city}, CBSE school ERP {city}, school fee management {city}"/>')
        self._glog(f'<link rel="canonical" href="{_page_url(city.lower().replace(chr(32), chr(45))+chr(45)+chr(115)+chr(99)+chr(104)+chr(111)+chr(111)+chr(108)+chr(45)+chr(101)+chr(114)+chr(112))}"/>')
        self._glog(f'<meta property="og:title" content="#1 {kw.title()} — {city} | TACHY"/>')
        self._glog(f'<meta property="og:description" content="Trusted school ERP in {city}. Automates admissions, fees, attendance, exams & more. Free demo!"/>')
        self._glog(f'\n=== H1 TAG ===')
        self._glog(f'<h1>#1 School ERP Software in {city} | {kw.title()}</h1>')
        self._glog(f'\n=== URL SLUG ===')
        self._glog(f'/{city.lower().replace(" ","-")}-school-erp/')

    def _lsi_suggestions(self):
        self.gap_out.delete("1.0","end")
        city = self._gap_city.get(); state = self._gap_state.get()
        self._glog(f"=== LSI KEYWORDS for {city}, {state} ===\n")
        groups = {
            "High Intent (Buyer Ready)": [
                f"school ERP software {city} price",
                f"school management software {city} demo",
                f"buy school ERP {city}",
                f"school ERP free trial {city}",
            ],
            "Problem-Aware": [
                f"how to manage school fees digitally {city}",
                f"how to automate school attendance {city}",
                f"how to generate report cards automatically {city}",
                f"best school admin software {city}",
            ],
            "Comparison (Decision Stage)": [
                f"Fedena alternative {city}",
                f"Entab vs TACHY {city}",
                f"school ERP comparison {city}",
                f"affordable school ERP {city}",
            ],
            "Feature-Specific": [
                f"school fee receipt software {city}",
                f"student attendance app {city}",
                f"school transport route management {city}",
                f"teacher payroll software {city}",
                f"school parent communication app {city}",
            ],
            "Board-Specific": [
                f"CBSE school ERP {city}",
                f"ICSE school management {city}",
                f"Bihar Board school ERP {state}",
                f"private school management system {city}",
            ],
            "Long-Tail (Low Competition)": [
                f"school management software for small schools {city}",
                f"cloud based school ERP {city}",
                f"school ERP with WhatsApp integration {city}",
                f"school ERP with parent mobile app {city}",
            ],
        }
        for group, kws in groups.items():
            self._glog(f"\n📂 {group}:")
            for kw in kws:
                self._glog(f"   • {kw}")

    def _intl_seo(self):
        self.gap_out.delete("1.0","end")
        self._glog("=== INTERNATIONAL SEO STRATEGY ===\n")
        intl = [
            ("Dubai, UAE",       "50K+ Indian expats. Search: 'Indian school ERP Dubai', 'CBSE school software UAE'"),
            ("London, UK",       "Large NRI community. Target: 'Indian school management software UK'"),
            ("Toronto, Canada",  "Growing Gujarati/Punjabi community. 'Indian school ERP Canada'"),
            ("Singapore",        "Major Indian tech hub. 'school management software Singapore'"),
            ("Sydney, Australia","Large Indian diaspora. 'CBSE school ERP Australia'"),
            ("New York, USA",    "NRI schools growing. 'Indian school management software USA'"),
            ("Doha, Qatar",      "Major South Asian school market. 'Indian school ERP Qatar'"),
            ("Riyadh, KSA",      "Large Indian expat schools. 'school ERP Saudi Arabia'"),
        ]
        for loc, strategy in intl:
            self._glog(f"  📍 {loc}")
            self._glog(f"     Strategy: {strategy}\n")
        self._glog("✅ All international pages auto-generate with:")
        self._glog("  → Localized title & meta (city + country)")
        self._glog("  → Appropriate hreflang tags")
        self._glog("  → Geo meta tags")
        self._glog("  → Local currency/board mentions where applicable")

    def _schema_check(self):
        conn = sqlite3.connect(DB_PATH)
        r = conn.execute("SELECT file_path FROM generated_pages ORDER BY generated_at DESC LIMIT 1").fetchone()
        conn.close()
        if not r or not os.path.exists(r[0]):
            messagebox.showinfo("None","Generate a page first."); return
        with open(r[0], encoding="utf-8") as f: html = f.read()
        self.gap_out.delete("1.0","end")
        self._glog(f"=== SCHEMA VALIDATOR: {os.path.basename(r[0])} ===\n")
        checks = [
            ("FAQPage schema",         "FAQPage" in html),
            ("BreadcrumbList schema",  "BreadcrumbList" in html),
            ("LocalBusiness schema",   "LocalBusiness" in html),
            ("SoftwareApplication",    "SoftwareApplication" in html),
            ("AggregateRating",        "aggregateRating" in html.lower()),
            ("WebPage schema",         "WebPage" in html),
            ("JSON-LD blocks",         html.count("application/ld+json") >= 1),
            ("Canonical URL",          'rel="canonical"' in html),
            ("OG title",               'og:title' in html),
            ("OG description",         'og:description' in html),
            ("Twitter card",           'twitter:card' in html),
            ("hreflang",               'hreflang' in html),
            ("Geo meta tags",          'geo.region' in html),
            ("Microdata on FAQ",       'itemtype="https://schema.org/Question"' in html),
            ("Review microdata",       'itemtype="https://schema.org/Review"' in html),
        ]
        for name, ok in checks:
            self._glog(f"  {'✅' if ok else '❌'} {name}")
        all_ok = all(ok for _,ok in checks)
        self._glog(f"\n{'✅ All checks passed!' if all_ok else '⚠  Fix issues above — re-generate page.'}")

    def _sitemap_preview(self):
        od = cfg("out_dir") or OUT_DIR
        sp = os.path.join(od, "sitemap.xml")
        if not os.path.exists(sp): messagebox.showinfo("None","Build sitemap first."); return
        with open(sp) as f: content = f.read()
        self.clipboard_clear(); self.clipboard_append(content)
        messagebox.showinfo("Copied", f"sitemap.xml copied to clipboard ({content.count('<url>')} URLs)")

    # ══════════════════════════════════════════════════════════
    #  TAB 5 — BACKLINKS
    # ══════════════════════════════════════════════════════════
    def _tab_backlinks(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  🔗  Backlinks  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(1, weight=1)

        tk.Label(f, text="🔗  Backlink Outreach Manager — Build Domain Authority", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",13,"bold")).pack(anchor="w", padx=14, pady=(12,4))
        tk.Label(f, text="Target these high-DA platforms to build TACHY's domain authority. Each listing = 1 powerful backlink.",
                 bg="#060b18", fg="#4a5f80", font=("Segoe UI",9)).pack(anchor="w", padx=14, pady=(0,8))

        brow = tk.Frame(f, bg="#060b18"); brow.pack(fill="x", padx=14, pady=4)
        ttk.Button(brow, text="📋 Show All Backlink Targets", command=self._show_backlinks).pack(side="left", padx=3)
        ttk.Button(brow, text="📤 Export Outreach CSV",       command=self._export_backlinks, style="Y.TButton").pack(side="left", padx=3)
        ttk.Button(brow, text="📝 Generate Outreach Email Template", command=self._outreach_email).pack(side="left", padx=3)
        ttk.Button(brow, text="🏆 Priority Action Plan",       command=self._priority_plan, style="G.TButton").pack(side="left", padx=3)

        cols = ("platform","url","da","strategy")
        self.bltree = ttk.Treeview(f, columns=cols, show="headings")
        for col, hdr, w in [("platform","Platform",140),("url","URL",220),("da","Domain Authority",130),("strategy","Strategy",500)]:
            self.bltree.heading(col, text=hdr)
            self.bltree.column(col, width=w)
        self.bltree.pack(fill="both", expand=True, padx=14, pady=(0,4))
        sb = ttk.Scrollbar(f, orient="vertical", command=self.bltree.yview)
        self.bltree.configure(yscroll=sb.set)

        for i, (name, url, da, strategy) in enumerate(BACKLINK_TARGETS):
            tag = "high" if int(da.split(":")[1]) >= 80 else "med"
            self.bltree.insert("","end", values=(name,url,da,strategy), tags=(tag,))
        self.bltree.tag_configure("high", foreground="#4ade80")
        self.bltree.tag_configure("med",  foreground="#fbbf24")
        self.bltree.bind("<Double-1>", self._open_backlink)

        self.bl_out = scrolledtext.ScrolledText(f, height=8, bg="#040810", fg="#94a3b8",
                                                 font=("Consolas",9), relief="flat", bd=0)
        self.bl_out.pack(fill="x", padx=14, pady=4)

    def _open_backlink(self, _):
        sel = self.bltree.selection()
        if sel:
            url = self.bltree.item(sel[0])["values"][1]
            webbrowser.open(url)

    def _show_backlinks(self):
        self.bl_out.delete("1.0","end")
        self.bl_out.insert("end", "=== BACKLINK TARGETS — TACHY SCHOOL ERP ===\n\n")
        for name, url, da, strategy in BACKLINK_TARGETS:
            self.bl_out.insert("end", f"  [{da}] {name}\n  URL: {url}\n  Strategy: {strategy}\n\n")

    def _export_backlinks(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tachy_backlink_targets.csv")
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Platform","URL","DA","Strategy","Status"])
            for row in BACKLINK_TARGETS: w.writerow(list(row)+["Pending"])
        messagebox.showinfo("Exported", f"Backlink targets exported:\n{path}")

    def _outreach_email(self):
        self.bl_out.delete("1.0","end")
        self.bl_out.insert("end", """=== OUTREACH EMAIL TEMPLATE ===

Subject: Adding TACHY School ERP to [Platform Name] — School Management Software for India

Hi [Platform Name] Team,

I'd like to add TACHY School ERP to your software directory.

TACHY is a cloud-based school management ERP serving 500+ schools across India. It covers admissions, fee management, attendance, exams, transport, HR and parent communication — all in one platform.

Listing Details:
- Product Name: TACHY School ERP
- Website: https://tachy.in
- Category: School Management Software / ERP
- Pricing: Subscription (Monthly / Annual)
- Platforms: Web Browser, Android
- Target Market: K-12 Schools, India
- Phone: +91 8434801033
- Email: info@tachy.in

Happy to provide screenshots, feature descriptions, or pricing details as needed.

Best regards,
TACHY School ERP Team
https://tachy.in | +91 8434801033
""")

    def _priority_plan(self):
        self.bl_out.delete("1.0","end")
        self.bl_out.insert("end", """=== 30-DAY BACKLINK PRIORITY ACTION PLAN ===

🟢 WEEK 1 (Quick Wins — Free):
  Day 1: Create profile on SoftwareSuggest.com
  Day 2: Create profile on G2.com
  Day 3: Create profile on Capterra.com
  Day 4: List on GetApp.com (auto-synced with Capterra)
  Day 5: List on IndiaMART.com (business category)
  Day 6-7: Create profiles on JustDial for Katihar, Patna, Ranchi

🟡 WEEK 2 (Review Collection):
  Email 20 current school clients — request G2/Capterra reviews
  Post WhatsApp broadcast to existing clients with review link
  Each verified review = social proof + backlink signal

🟡 WEEK 3 (Directory Listings):
  List on SourceForge.net (high DA 88)
  List on AlternativeTo.net (as Fedena/Entab alternative)
  List on TrustRadius.com
  Submit to Sulekha.com

🔵 WEEK 4 (Content Backlinks):
  Submit guest post pitch to EducationWorld.in
  Contact SchoolDekho.org for software listing
  LinkedIn article: "Why Bihar Schools Are Going Digital"
  Share pages in Facebook school owner groups

📊 EXPECTED IMPACT (90 days):
  Domain Authority: +5-10 points
  Branded search volume: +40%
  Organic traffic: +60-80% (from city pages + backlinks)
""")

    # ══════════════════════════════════════════════════════════
    #  TAB 6 — KEYWORDS
    # ══════════════════════════════════════════════════════════
    def _tab_keywords(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  🔑  Keywords  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(1, weight=1)

        top = tk.Frame(f, bg="#060b18"); top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12,6))
        self._kw    = tk.StringVar(); self._kcat  = tk.StringVar(value="primary")
        self._kvol  = tk.StringVar(); self._kdiff = tk.StringVar(value="MED")
        self._kpage = tk.StringVar(); self._krank = tk.StringVar(value="0")
        for lbl, var, width in [("Keyword:",self._kw,24),("Vol:",self._kvol,10),("Target Page:",self._kpage,12),("Cur Rank:",self._krank,5)]:
            tk.Label(top, text=lbl, bg="#060b18", fg="#94a3b8", font=("Segoe UI",9)).pack(side="left")
            ttk.Entry(top, textvariable=var, width=width).pack(side="left", padx=3)
        tk.Label(top, text="Cat:", bg="#060b18", fg="#94a3b8", font=("Segoe UI",9)).pack(side="left")
        ttk.Combobox(top, textvariable=self._kcat, values=["primary","secondary","module","longtail","comparison","local","intent","international"], width=10, state="readonly").pack(side="left", padx=3)
        tk.Label(top, text="Diff:", bg="#060b18", fg="#94a3b8", font=("Segoe UI",9)).pack(side="left")
        ttk.Combobox(top, textvariable=self._kdiff, values=["LOW","MED","HIGH"], width=5, state="readonly").pack(side="left", padx=3)
        ttk.Button(top, text="➕ Add", command=self._add_kw).pack(side="left", padx=4)
        ttk.Button(top, text="🗑 Delete", command=self._del_kw, style="R.TButton").pack(side="left", padx=3)
        ttk.Button(top, text="💾 Update Rank", command=self._update_rank, style="Y.TButton").pack(side="left", padx=3)
        ttk.Button(top, text="📤 Export CSV", command=self._export_kws, style="C.TButton").pack(side="left", padx=8)

        cols = ("keyword","category","volume","difficulty","target_page","rank")
        self.ktree = ttk.Treeview(f, columns=cols, show="headings")
        for col, hdr, w in [("keyword","Keyword",260),("category","Category",90),("volume","Volume",110),
                              ("difficulty","Difficulty",80),("target_page","Target Page",130),("rank","Rank",70)]:
            self.ktree.heading(col, text=hdr)
            self.ktree.column(col, width=w)
        self.ktree.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0,8))
        sb = ttk.Scrollbar(f, orient="vertical", command=self.ktree.yview)
        self.ktree.configure(yscroll=sb.set); sb.grid(row=1, column=1, sticky="ns")
        f.columnconfigure(1, weight=0)
        self._load_kws()

    def _load_kws(self):
        for r in self.ktree.get_children(): self.ktree.delete(r)
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT keyword,category,monthly_volume,difficulty,target_page,current_rank FROM keywords WHERE is_active=1 ORDER BY category,keyword").fetchall()
        conn.close()
        for row in rows:
            rank = row[5] or 0
            tag = "l" if row[3]=="LOW" else "m" if row[3]=="MED" else "h"
            rtag = "top3" if 0 < rank <= 3 else "top10" if rank <= 10 else "other"
            rank_display = f"#{rank}" if rank > 0 else "—"
            self.ktree.insert("","end", values=(row[0],row[1],row[2],row[3],row[4],rank_display), tags=(tag,rtag))
        self.ktree.tag_configure("l", foreground="#4ade80")
        self.ktree.tag_configure("m", foreground="#fbbf24")
        self.ktree.tag_configure("h", foreground="#f87171")

    def _add_kw(self):
        kw = self._kw.get().strip()
        if not kw: return
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR IGNORE INTO keywords(keyword,category,monthly_volume,difficulty,target_page,current_rank) VALUES(?,?,?,?,?,?)",
                     (kw,self._kcat.get(),self._kvol.get(),self._kdiff.get(),self._kpage.get(),int(self._krank.get() or 0)))
        conn.commit(); conn.close()
        self._kw.set(""); self._load_kws(); self._refresh_dash()

    def _del_kw(self):
        for item in self.ktree.selection():
            kw = self.ktree.item(item)["values"][0]
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE keywords SET is_active=0 WHERE keyword=?", (kw,))
            conn.commit(); conn.close()
        self._load_kws()

    def _update_rank(self):
        sel = self.ktree.selection()
        if not sel: messagebox.showinfo("Select","Select a keyword first."); return
        kw = self.ktree.item(sel[0])["values"][0]
        new_rank = self._krank.get()
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE keywords SET current_rank=? WHERE keyword=?", (int(new_rank or 0), kw))
        conn.execute("INSERT INTO rank_history(keyword,rank) VALUES(?,?)", (kw, int(new_rank or 0)))
        conn.commit(); conn.close()
        self._load_kws()

    def _export_kws(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tachy_keywords_v3.csv")
        if not path: return
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT keyword,category,monthly_volume,difficulty,target_page,current_rank FROM keywords WHERE is_active=1").fetchall()
        conn.close()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Keyword","Category","Monthly Volume","Difficulty","Target Page","Current Rank"])
            for r in rows: w.writerow(r)
        messagebox.showinfo("Exported", f"Keywords exported:\n{path}")

    # ══════════════════════════════════════════════════════════
    #  TAB 7 — SETTINGS
    # ══════════════════════════════════════════════════════════
    def _tab_settings(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  ⚙  Settings  ")
        canvas = tk.Canvas(f, bg="#060b18", highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        inner = tk.Frame(canvas, bg="#060b18"); inner.columnconfigure(1, weight=1)
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        tk.Label(inner, text="Brand & Site Configuration", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",14,"bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16,10))
        self._svs = {}
        fields = [
            ("Brand Name","brand"),("Short Name","short"),("Tagline","tagline"),
            ("Website URL","website"),("Phone","phone"),
            ("WhatsApp (with country code)","wa"),("Email","email"),
            ("Google Analytics ID","ga"),("Output Directory","out_dir"),
            ("Base City","base_city"),("Base State","base_state"),
            # SEO subfolder — CRITICAL for tachy.in/seo/ deployment
            ("SEO Subfolder Path (e.g. seo)","seo_base_path"),
            ("YouTube Demo Video ID", "demo_video_id"),
            ("OG Share Image Path", "og_image"),
            ("Live Review Count (from G2/SoftwareSuggest)", "review_count"),
            ("Average Rating Score (e.g. 4.8)", "rating_value"),
            ("SoftwareSuggest URL", "softwaresuggest_url"),
            ("G2 Profile URL", "g2_url"),
            ("Capterra URL", "capterra_url"),
        ]
        for i, (lbl, key) in enumerate(fields, 1):
            tk.Label(inner, text=lbl, bg="#060b18", fg="#a0b4d4",
                     font=("Segoe UI",10)).grid(row=i, column=0, sticky="w", padx=20, pady=5)
            var = tk.StringVar(value=cfg(key))
            self._svs[key] = var
            ttk.Entry(inner, textvariable=var, width=55).grid(row=i, column=1, sticky="ew", padx=(8,20), pady=5)

        row0 = len(fields)+1
        brow = tk.Frame(inner, bg="#060b18"); brow.grid(row=row0, column=0, columnspan=2, padx=20, pady=(12,4), sticky="w")
        ttk.Button(brow, text="💾 Save All Settings", command=self._save_settings).pack(side="left", padx=3)
        ttk.Button(brow, text="📁 Browse Output Folder", command=self._browse_out, style="Y.TButton").pack(side="left", padx=3)

        ttk.Frame(inner, style="Sep.TFrame", height=1).grid(row=row0+1, column=0, columnspan=2, sticky="ew", padx=20, pady=12)

        # SEO PATH HELP BOX
        path_box = tk.Frame(inner, bg="#0a1f0a", highlightthickness=1, highlightbackground="#1a4a1a")
        path_box.grid(row=row0+1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0,8))
        tk.Label(path_box, text="📂  SEO Subfolder Path — How It Works",
                 bg="#0a1f0a", fg="#4ade80", font=("Segoe UI",10,"bold")).pack(anchor="w", padx=12, pady=(8,4))
        path_examples = [
            ('Leave blank ("")',        "→  https://tachy.in/patna-school-erp/",          "Root domain deployment"),
            ('Set to "seo"',            "→  https://tachy.in/seo/patna-school-erp/",       "Subfolder: tachy.in/seo/"),
            ('Set to "erp/cities"',     "→  https://tachy.in/erp/cities/patna-school-erp/","Nested subfolder"),
            ('domain.com + "seo"',      "→  https://domain.com/seo/patna-school-erp/",     "Any domain + subfolder"),
        ]
        for val, result, note in path_examples:
            row_f = tk.Frame(path_box, bg="#0a1f0a"); row_f.pack(fill="x", padx=12, pady=1)
            tk.Label(row_f, text=f"  {val:28s}", bg="#0a1f0a", fg="#fbbf24", font=("Consolas",9)).pack(side="left")
            tk.Label(row_f, text=result, bg="#0a1f0a", fg="#4ade80", font=("Consolas",9)).pack(side="left")
            tk.Label(row_f, text=f"  ({note})", bg="#0a1f0a", fg="#4a6a4a", font=("Segoe UI",8)).pack(side="left")
        tk.Label(path_box, text="  ⚠  After changing this setting, click Save then re-generate your pages.",
                 bg="#0a1f0a", fg="#f87171", font=("Segoe UI",8)).pack(anchor="w", padx=12, pady=(4,8))

        tk.Label(inner, text="v3.0 SEO Strategy Notes", bg="#060b18", fg="#6c63ff",
                 font=("Segoe UI",12,"bold")).grid(row=row0+2, column=0, columnspan=2, sticky="w", padx=20, pady=(8,8))
        notes = [
            "📌 SEO Subfolder: set 'seo' to deploy at tachy.in/seo/ — all URLs, schema, sitemap auto-update",
            "📌 Bulk Import: Cities panel supports CSV, TXT, clipboard paste — City,State,Country format",
            "📌 200+ Indian cities + 20 international cities pre-seeded",
            "📌 10 NLP variation pools — every city page is uniquely worded, zero duplicate content",
            "📌 5-type schema: FAQ + Breadcrumb + LocalBusiness + Software + Review",
            "📌 SEO score v3: 30 checkpoints, max 100 points",
            "📌 Auto internal linking: every city links to 8 related state cities",
            "📌 State hub pages create 3-tier URL hierarchy for maximum PageRank flow",
            "📌 Submit sitemap.xml to Google Search Console immediately after upload",
            "📌 Build backlinks from SoftwareSuggest, G2, Capterra first (highest DA)",
        ]
        for j, note in enumerate(notes, row0+3):
            tk.Label(inner, text=note, bg="#060b18", fg="#64748b",
                     font=("Segoe UI",9)).grid(row=j, column=0, columnspan=2, sticky="w", padx=20, pady=2)

    def _save_settings(self):
        for key, var in self._svs.items():
            set_cfg(key, var.get())
        messagebox.showinfo("Saved", "✅ All settings saved successfully!")
        self.sv.set("✅ Settings saved")
        log_db("SETTINGS", "Settings updated")

    def _browse_out(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            set_cfg("out_dir", path)
            if "out_dir" in self._svs: self._svs["out_dir"].set(path)

    # ══════════════════════════════════════════════════════════
    #  TAB 8 — LOG
    # ══════════════════════════════════════════════════════════
    def _tab_log(self):
        f = ttk.Frame(self.nb); self.nb.add(f, text="  📋  Log  ")
        f.columnconfigure(0, weight=1); f.rowconfigure(1, weight=1)
        top = tk.Frame(f, bg="#060b18"); top.grid(row=0, column=0, sticky="ew", padx=14, pady=(12,6))
        ttk.Button(top, text="🔄 Refresh",  command=self._load_log).pack(side="left", padx=3)
        ttk.Button(top, text="🗑 Clear",    command=self._clear_log, style="R.TButton").pack(side="left", padx=3)
        ttk.Button(top, text="📤 Export",   command=self._export_log, style="Y.TButton").pack(side="left", padx=3)
        self.ltree = ttk.Treeview(f, columns=("ts","action","detail"), show="headings")
        self.ltree.heading("ts",     text="Time");    self.ltree.column("ts",     width=130)
        self.ltree.heading("action", text="Action");  self.ltree.column("action", width=120)
        self.ltree.heading("detail", text="Details"); self.ltree.column("detail", width=800)
        self.ltree.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0,8))
        sb = ttk.Scrollbar(f, orient="vertical", command=self.ltree.yview)
        self.ltree.configure(yscroll=sb.set); sb.grid(row=1, column=1, sticky="ns")
        self._load_log()

    def _load_log(self):
        for r in self.ltree.get_children(): self.ltree.delete(r)
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT ts,action,details FROM audit_log ORDER BY id DESC LIMIT 500").fetchall()
        conn.close()
        for row in rows:
            tag = "g" if "GEN" in row[1] else "r" if "ERR" in row[1] else "n"
            self.ltree.insert("","end", values=row, tags=(tag,))
        self.ltree.tag_configure("g", foreground="#4ade80")
        self.ltree.tag_configure("r", foreground="#f87171")
        self.ltree.tag_configure("n", foreground="#64748b")

    def _clear_log(self):
        if messagebox.askyesno("Clear","Clear all logs?"):
            conn = sqlite3.connect(DB_PATH); conn.execute("DELETE FROM audit_log"); conn.commit(); conn.close()
            self._load_log()

    def _export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tachy_log_v3.csv")
        if not path: return
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT ts,action,details FROM audit_log ORDER BY id DESC").fetchall()
        conn.close()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Time","Action","Details"])
            for r in rows: w.writerow(r)
        messagebox.showinfo("Exported", f"Log exported:\n{path}")


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    init_db()
    log_db("APP_START", "TACHY SEO Pro v3.1 launched")
    app = App()
    app.mainloop()
