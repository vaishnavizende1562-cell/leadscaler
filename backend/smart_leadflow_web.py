#!/usr/bin/env python3
"""
leadScaler — Public Web UI, Per-User Workspace & Strict AI Domain Purity Engine
Port: 8095 (172.18.0.1:8095 / 0.0.0.0:8095)
"""
import hashlib
import json
import os
import re
import secrets
import socket
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Force IPv4 on VPS to prevent outbound IPv6 stalls on external HTTPS APIs
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

HOST = os.environ.get("SMART_WEB_HOST", "0.0.0.0")
PORT = int(os.environ.get("SMART_WEB_PORT", "8095"))
N8N_BASE = os.environ.get("N8N_BASE", "http://127.0.0.1:5678")
RACE_HEALTH_URL = os.environ.get("RACE_HEALTH_URL", "http://172.18.0.1:8097/health")
N8N_ENV_FILE = os.environ.get("N8N_ENV_FILE", "/opt/n8n/.env")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SMART_WEB_DB", os.path.join(BASE_DIR, "users_data.sqlite"))
UI_HTML_PATH = os.environ.get("SMART_WEB_HTML", os.path.join(BASE_DIR, "goal_trends_ui.html"))


def load_env_file(path: str) -> dict:
    out = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip().strip('"').strip("'")
    return out


ENV_VARS = load_env_file(N8N_ENV_FILE)
PROSPEO_KEY = os.environ.get("PROSPEO_API_KEY_1") or ENV_VARS.get("PROSPEO_API_KEY_1", "")
TINYFISH_KEY = os.environ.get("TINYFISH_KEY") or ENV_VARS.get("TINYFISH_KEY", "")
XKIRO_KEY = os.environ.get("LLM2_KEY") or ENV_VARS.get("LLM2_KEY", "")
XKIRO_BASE = os.environ.get("LLM2_BASE_URL") or ENV_VARS.get("LLM2_BASE", "") or ENV_VARS.get("LLM2_BASE_URL", "https://api.xkiro.com/v1")

DEFAULT_OFFER = "automate outbound B2B lead gen & sales workflows with AI"
DEFAULT_EMAIL_SUBJECT = "Quick collaboration idea for {{companyName}}"
DEFAULT_EMAIL_BODY = """Hi {{decisionMakerName}},

I came across {{companyName}} and was impressed by your work in {{industry}}.

We help B2B teams automate outbound B2B lead gen & sales workflows with AI, and I thought this could be valuable for your role as {{jobTitle}}.

Would you be open to a brief 10-minute chat this week?

Best regards,
{{senderName}}"""

DB_LOCK = threading.Lock()
JOBS = {}
JOBS_LOCK = threading.Lock()
SUGGEST_CACHE = {}
SUGGEST_LOCK = threading.Lock()

GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "linkedin.com",
    "facebook.com", "instagram.com", "youtube.com", "x.com", "twitter.com",
    "wikipedia.org", "indiamart.com", "justdial.com", "amazon.in", "amazon.com",
    "flipkart.com", "bigbasket.com", "blinkit.com", "swiggy.com", "zomato.com",
    "zaubacorp.com", "tofler.in", "crunchbase.com", "tracxn.com", "glassdoor.com",
}

INDIAN_PLACES = {
    "delhi", "new delhi", "ncr", "delhi ncr", "mumbai", "navi mumbai", "thane",
    "bangalore", "bengaluru", "hyderabad", "secunderabad", "pune", "chennai",
    "kolkata", "ahmedabad", "surat", "vadodara", "rajkot", "jaipur", "udaipur",
    "noida", "greater noida", "gurgaon", "gurugram", "faridabad", "ghaziabad",
    "indore", "bhopal", "chandigarh", "mohali", "ludhiana", "amritsar",
    "lucknow", "kanpur", "varanasi", "nagpur", "nashik", "aurangabad",
    "coimbatore", "madurai", "kochi", "ernakulam", "trivandrum", "visakhapatnam",
    "bhubaneswar", "raipur", "ranchi", "patna", "guwahati", "dehradun", "goa",
    "maharashtra", "karnataka", "gujarat", "tamil nadu", "telangana", "kerala",
    "rajasthan", "uttar pradesh", "haryana", "punjab", "madhya pradesh", "west bengal",
}

INDUSTRY_SYNONYMS = {
    "chemical": ["chemical", "Paint, Coating, and Adhesive Manufacturing"],
    "chemicals": ["chemical", "Paint, Coating, and Adhesive Manufacturing"],
    "petrochemical": ["chemical", "Oil, Gas, and Mining"],
    "agrochemical": ["chemical", "Farming"],
    "pharma": ["pharmaceutical", "biotechnology"],
    "pharmaceutical": ["pharmaceutical", "biotechnology"],
    "biotech": ["biotechnology", "pharmaceutical"],
    "saas": ["Software Development", "Technology, Information and Internet"],
    "software": ["Software Development", "IT Services and IT Consulting"],
    "ai": ["Software Development", "Data Infrastructure and Analytics", "Technology, Information and Internet"],
    "machine learning": ["Software Development", "Data Infrastructure and Analytics"],
    "it": ["IT Services and IT Consulting", "Software Development"],
    "it services": ["IT Services and IT Consulting"],
    "fintech": ["Financial Services", "Banking", "Investment Management"],
    "finance": ["Financial Services", "Banking", "Investment Management"],
    "financial": ["Financial Services", "Banking"],
    "healthcare": ["Hospitals and Health Care", "Medical Practices", "Medical Equipment Manufacturing"],
    "healthtech": ["Hospitals and Health Care", "Medical Equipment Manufacturing"],
    "medical": ["Medical Practices", "Medical Equipment Manufacturing", "Hospitals and Health Care"],
    "ecommerce": ["Online and Mail Order Retail", "General Retail"],
    "e-commerce": ["Online and Mail Order Retail", "General Retail"],
    "retail": ["General Retail", "Online and Mail Order Retail"],
    "edtech": ["E-Learning Providers", "Higher Education", "Education Administration Programs"],
    "education": ["Higher Education", "Education Administration Programs", "E-Learning Providers"],
    "logistics": ["Transportation, Logistics, Supply Chain and Storage", "Freight and Package Transportation", "Warehousing and Storage"],
    "supply chain": ["Transportation, Logistics, Supply Chain and Storage", "Warehousing and Storage"],
    "manufacturing": ["General Manufacturing", "Industrial Machinery Manufacturing", "Machinery Manufacturing"],
    "plastic": ["Plastics Manufacturing", "Plastics and Rubber Product Manufacturing"],
    "plastics": ["Plastics Manufacturing", "Plastics and Rubber Product Manufacturing"],
    "packaging": ["Packaging and Containers", "Plastics and Rubber Product Manufacturing"],
    "textile": ["Textile Manufacturing", "Apparel Manufacturing"],
    "textiles": ["Textile Manufacturing", "Apparel Manufacturing"],
    "apparel": ["Apparel Manufacturing", "Retail Apparel and Fashion"],
    "garment": ["Apparel Manufacturing", "Textile Manufacturing"],
    "food": ["Food and Beverage Manufacturing", "Food and Beverage Services"],
    "beverage": ["Food and Beverage Manufacturing", "Food and Beverage Services"],
    "solar": ["Renewable Energy", "Electric Power Generation"],
    "renewable": ["Renewable Energy", "Electric Power Generation"],
    "energy": ["Renewable Energy", "Oil, Gas, and Mining", "Electric Power Generation"],
    "construction": ["Construction", "Building Materials", "Civil Engineering"],
    "real estate": ["Real Estate"],
    "proptech": ["Real Estate", "Software Development"],
    "automotive": ["Motor Vehicle Manufacturing", "Automotive"],
    "machinery": ["Industrial Machinery Manufacturing", "Machinery Manufacturing"],
    "electronics": ["Appliances, Electrical, and Electronics Manufacturing", "Semiconductor Manufacturing"],
    "electrical": ["Appliances, Electrical, and Electronics Manufacturing"],
    "marketing": ["Marketing Services", "Advertising Services"],
    "advertising": ["Advertising Services", "Marketing Services"],
    "agency": ["Marketing Services", "Advertising Services", "Design Services"],
    "cybersecurity": ["Computer and Network Security", "Data Security Software Products"],
    "cosmetics": ["Cosmetics", "Personal Care Product Manufacturing"],
    "beauty": ["Cosmetics", "Personal Care Product Manufacturing"],
    "skincare": ["Cosmetics", "Personal Care Product Manufacturing"],
    "dairy": ["Dairy Product Manufacturing", "Food and Beverage Manufacturing"],
    "milk": ["Dairy Product Manufacturing", "Food and Beverage Manufacturing"],
    "chocolate": ["Food and Beverage Manufacturing"],
    "coffee": ["Food and Beverage Manufacturing", "Food and Beverage Services"],
    "tea": ["Food and Beverage Manufacturing", "Food and Beverage Services"],
    "bakery": ["Food and Beverage Manufacturing", "Food and Beverage Services"],
    "airline": ["Airlines and Aviation"],
    "airlines": ["Airlines and Aviation"],
    "aviation": ["Airlines and Aviation"],
    "hotel": ["Hospitality"],
    "hotels": ["Hospitality"],
    "hospitality": ["Hospitality"],
    "insurance": ["Insurance"],
    "telecom": ["Telecommunications"],
    "biotech": ["Biotechnology Research"],
}

HEADCOUNT_MAP = {
    "1–10 employees": ["1-10"],
    "1-10 employees": ["1-10"],
    "11–50 employees": ["11-20", "21-50"],
    "11-50 employees": ["11-20", "21-50"],
    "51–200 employees": ["51-100", "101-200"],
    "51-200 employees": ["51-100", "101-200"],
    "201–500 employees": ["201-500"],
    "201-500 employees": ["201-500"],
    "501–1,000 employees": ["501-1000"],
    "501-1000 employees": ["501-1000"],
    "1,000+ employees": ["1001-2000", "2001-5000", "5001-10000", "10000+"],
}

STOP_WORDS = {
    "find", "search", "get", "give", "show", "me", "top", "best", "leading", "list", "of",
    "companies", "company", "business", "businesses", "firms", "firm", "industry", "industries",
    "startups", "startup", "agency", "manufacturers", "manufacturer", "suppliers", "supplier",
    "exporters", "exporter", "dealers", "distributors", "providers", "services", "solutions",
    "brands", "brand", "makers", "maker", "in", "at", "from", "near", "around", "for", "with",
    "and", "or", "the", "a", "an", "to", "by", "all", "any", "employees", "employee", "size",
    "decision", "role", "roles", "ceo", "ceos", "cto", "ctos", "cfo", "coo", "cmo", "founder",
    "founders", "cofounder", "co-founder", "owner", "owners", "director", "directors",
    "managing", "head", "sales", "vp", "president", "partner", "b2b",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def call_xkiro_json(system_prompt: str, user_text: str, max_tokens: int = 800, timeout: float = 10.0) -> dict:
    if not XKIRO_KEY:
        return {}
    base = XKIRO_BASE.rstrip("/")
    for model in ("mistralai/mistral-large-2512", "cohere/command-a", "qwen/qwen3.7-flash:free"):
        try:
            req = urllib.request.Request(
                f"{base}/chat/completions",
                data=json.dumps({
                    "model": model,
                    "temperature": 0,
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_text},
                    ],
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {XKIRO_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": CHROME_UA,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            msg = ((d.get("choices") or [{}])[0].get("message") or {})
            txt = (msg.get("content") or msg.get("reasoning_content") or "").strip()
            m = re.search(r"\{[\s\S]*\}", txt)
            if m:
                return json.loads(m.group(0))
        except Exception:
            continue
    return {}


def tinyfish_web_snippets(queries: list[str], timeout_s: float = 22.0) -> list[dict]:
    if not TINYFISH_KEY or not queries:
        return []
    out = []
    lock = threading.Lock()

    def _fetch(q):
        try:
            qs = urllib.parse.urlencode({"query": q})
            req = urllib.request.Request(
                f"https://api.search.tinyfish.ai?{qs}",
                headers={"X-API-Key": TINYFISH_KEY, "User-Agent": CHROME_UA},
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            with lock:
                for it in (d.get("results") or [])[:10]:
                    out.append({
                        "title": it.get("title", ""),
                        "url": it.get("url", ""),
                        "snippet": it.get("snippet", ""),
                    })
        except Exception:
            pass

    threads = [threading.Thread(target=_fetch, args=(q,), daemon=True) for q in queries[:4]]
    for th in threads:
        th.start()
    t_end = time.monotonic() + timeout_s + 0.5
    for th in threads:
        th.join(timeout=max(0.05, t_end - time.monotonic()))
    return out


def prospeo_suggest(field: str, query: str) -> list:
    q = str(query or "").strip().lower()
    if len(q) < 2 or not PROSPEO_KEY:
        return []
    ck = f"{field}:{q}"
    with SUGGEST_LOCK:
        if ck in SUGGEST_CACHE:
            return SUGGEST_CACHE[ck]
    try:
        req = urllib.request.Request(
            "https://api.prospeo.io/search-suggestions",
            data=json.dumps({field: q}).encode("utf-8"),
            headers={
                "X-KEY": PROSPEO_KEY,
                "Content-Type": "application/json",
                "User-Agent": CHROME_UA,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        key_out = field.replace("_search", "_suggestions")
        val = d.get(key_out) or []
        with SUGGEST_LOCK:
            SUGGEST_CACHE[ck] = val
        return val
    except Exception:
        return []


def resolve_prospeo_location(loc_raw: str) -> list[str]:
    loc_clean = str(loc_raw or "").strip()
    if not loc_clean:
        return []
    low = re.sub(r"\s+", " ", loc_clean.lower()).strip()
    if low in ("ncr", "delhi ncr", "new delhi", "delhi"):
        query = "delhi"
        prefer_country = "india"
    elif low in INDIAN_PLACES:
        query = low
        prefer_country = "india"
    elif low == "india":
        return ["India"]
    elif "india" in low:
        query = re.sub(r"\b(india|in)\b", "", low).strip(" ,-") or "india"
        prefer_country = "india"
    elif low in ("usa", "us", "u.s.", "u.s.a.", "united states"):
        return ["United States"]
    elif low in ("uk", "u.k.", "united kingdom", "britain", "england"):
        return ["United Kingdom"]
    elif low in ("uae", "u.a.e.", "united arab emirates"):
        return ["United Arab Emirates"]
    else:
        query = low
        prefer_country = "india" if any(p in low for p in INDIAN_PLACES) else ""

    suggs = prospeo_suggest("location_search", query)
    if not suggs and "," in query:
        suggs = prospeo_suggest("location_search", query.split(",")[0].strip())

    if suggs:
        names = [s["name"] if isinstance(s, dict) else str(s) for s in suggs]
        if prefer_country:
            matched = [n for n in names if prefer_country in n.lower()]
            if matched:
                return [matched[0]]
        return [names[0]]
    return []


def resolve_prospeo_industries(terms: list[str]) -> list[str]:
    resolved = []

    def add_ind(val: str):
        if val and val not in resolved:
            resolved.append(val)

    for raw_t in terms:
        t = str(raw_t or "").strip()
        if not t:
            continue
        t_low = t.lower()
        matched_syn = False
        for syn_k, syn_vals in INDUSTRY_SYNONYMS.items():
            if re.search(rf"\b{re.escape(syn_k)}s?\b", t_low):
                matched_syn = True
                for sv in syn_vals:
                    if sv[0].isupper():
                        add_ind(sv)
                    else:
                        for s in prospeo_suggest("industry_search", sv)[:4]:
                            add_ind(s if isinstance(s, str) else s.get("name", ""))

        clean_words = [
            w for w in re.sub(r"[^a-z0-9\s]", " ", t_low).split()
            if len(w) >= 3 and w not in STOP_WORDS
        ]
        for q_candidate in ([t_low] if len(t_low) <= 28 else []) + clean_words[:3]:
            for s in prospeo_suggest("industry_search", q_candidate)[:4]:
                add_ind(s if isinstance(s, str) else s.get("name", ""))
            if resolved and matched_syn:
                break

    return resolved[:12]


def parse_roles_list(role_text: str) -> tuple[list[str], str]:
    txt = str(role_text or "").strip()
    if not txt:
        return ["Founder", "Co-Founder", "CEO", "Managing Director", "Director", "Owner"], ""

    role_map = [
        ("co-founder", "Co-Founder"), ("cofounder", "Co-Founder"), ("founder", "Founder"),
        ("ceo", "CEO"), ("chief executive", "CEO"),
        ("cto", "CTO"), ("cfo", "CFO"), ("coo", "COO"), ("cmo", "CMO"),
        ("managing director", "Managing Director"), ("director", "Director"),
        ("owner", "Owner"), ("partner", "Partner"), ("president", "President"),
        ("head of sales", "Head of Sales"), ("sales director", "Sales Director"),
        ("vp", "VP"), ("head of marketing", "Head of Marketing"),
    ]
    found = []
    primary_hint = ""
    for pat, canon in role_map:
        if re.search(rf"\b{re.escape(pat)}s?\b", txt, re.I):
            if not primary_hint:
                primary_hint = canon
            if canon not in found:
                found.append(canon)

    if not found:
        parts = [p.strip() for p in re.split(r"[,/|]+", txt) if len(p.strip()) >= 2]
        found = parts[:5] if parts else ["Founder", "CEO", "Managing Director", "Director"]
        primary_hint = found[0]

    if "Founder" in found and "Co-Founder" not in found:
        found.append("Co-Founder")
    if found == ["CEO"]:
        found.extend(["Managing Director", "Founder", "Director"])
    return found[:8], primary_hint


def build_filter_prompt(filters: dict) -> tuple[str, str]:
    industry = str(filters.get("industry") or "").strip()
    region = str(filters.get("region") or "").strip()
    role = str(filters.get("role") or "").strip()
    company_size = str(filters.get("companySize") or "").strip()
    extra = str(filters.get("extra") or "").strip()

    if industry and extra:
        target_desc = f"{industry} ({extra}) companies"
    elif industry:
        target_desc = f"{industry} companies"
    elif extra:
        target_desc = extra if "compan" in extra.lower() else f"{extra} companies"
    else:
        target_desc = "companies"

    loc_phrase = f" in {region}" if region else ""
    role_phrase = role if role else "Founder, CEO, Managing Director"

    parts = [f"Find {target_desc}{loc_phrase}, decision makers: {role_phrase}"]
    if company_size:
        parts.append(f"company size {company_size}")
    raw_prompt = ", ".join(parts)

    disp = [f"Industry: {industry or 'Any'}"]
    if region:
        disp.append(f"Geo: {region}")
    if role:
        disp.append(f"Role: {role}")
    if company_size:
        disp.append(f"Size: {company_size}")
    if extra:
        disp.append(f"Extra: {extra}")
    return raw_prompt, " · ".join(disp)


def discover_subniche_companies(niche_desc: str, loc_str: str, exclude_companies: list[str]) -> tuple[list[str], list[str]]:
    """Uses TinyFish live web search + xKiro to compile up to 45 genuine pure companies in a target niche."""
    loc_q = f" in {loc_str}" if loc_str else ""
    ex_hint = f" (exclude: {', '.join(exclude_companies[:20])})" if exclude_companies else ""
    queries = [
        f"top 25 {niche_desc} brands companies{loc_q} official website",
        f"list of leading {niche_desc} companies startups{loc_q}",
        f"best {niche_desc} businesses manufacturers providers{loc_q}",
        f"{niche_desc}{loc_q} companies directory websites",
    ]
    snippets = tinyfish_web_snippets(queries, timeout_s=22.0)

    sys_p = (
        "You are an expert B2B market researcher enforcing 100% STRICT DOMAIN PURITY. "
        "Given the user's target niche and location (plus live web snippets), list up to 40 REAL, AUTHENTIC companies "
        "in that location whose CORE, PRIMARY BUSINESS is strictly that exact niche/product/service. "
        "CRITICAL: NEVER include machinery/equipment vendors, packaging suppliers, real estate firms, IT/marketing agencies, "
        "or general multi-category brands where the product is only a minor side item (unless user asked for machinery/packaging/etc.). "
        "Only output root corporate domains you are confident belong to those companies (never marketplaces/directories). "
        'Return STRICT JSON ONLY: {"domains":["example.com",...],"names":["Company Name",...]}'
    )
    usr_p = json.dumps({
        "targetNiche": niche_desc,
        "location": loc_str or "Global / India",
        "excludeCompanies": exclude_companies[:35],
        "webSnippets": snippets[:32],
        "note": ex_hint,
    })
    res = call_xkiro_json(sys_p, usr_p, max_tokens=1400, timeout=11.0)
    ex_norm = {re.sub(r"[^a-z0-9]", "", c.lower()) for c in exclude_companies}

    domains = []
    for d in (res.get("domains") or []):
        dom = re.sub(r"^https?://(www\.)?", "", str(d or "").strip().lower()).split("/")[0]
        if dom and "." in dom and dom not in GENERIC_DOMAINS and dom not in domains:
            domains.append(dom)

    names = []
    for nm in (res.get("names") or []):
        n_clean = str(nm or "").strip()
        n_norm = re.sub(r"[^a-z0-9]", "", n_clean.lower())
        if n_clean and n_norm and n_norm not in ex_norm and n_clean not in names:
            names.append(n_clean)

    return domains[:45], names[:45]


def resolve_targeting_bundle(
    mode: str,
    raw_prompt: str,
    filters: dict | None,
    exclude_companies: list[str] | None = None,
    pathway: str = "free_apis",
) -> tuple[dict, list[str]]:
    exclude_companies = exclude_companies or []

    # Step 1: Ask xKiro for exact domain purity rules (works for BOTH Prompt Mode & Filter Mode!)
    planner_sys = (
        "Analyze this B2B lead search request and return STRICT JSON ONLY:\n"
        "{\n"
        '  "target_niche": "concise exact company type user wants (e.g. chocolate companies, chemical manufacturers, SaaS startups)",\n'
        '  "location": "city/state/country if mentioned else empty string",\n'
        '  "roles": ["explicit job titles mentioned else empty list"],\n'
        '  "is_specific_subniche": true or false (true if narrower than broad LinkedIn industries OR a specific vertical — e.g. airlines, hotels, restaurants, chocolate, tea, coffee, perfume, drone, solar panels, EV, ayurvedic, jewelry, dental, bakery, footwear, spices, toys, pet, interior design, D2C brands; false ONLY for broad standard industries like SaaS/Software, IT Services, Chemical Manufacturing, Pharmaceutical Manufacturing, Financial Services, Hospitals/Healthcare, Real Estate, Logistics),\n'
        '  "broad_industry_terms": ["1-2 closest exact industry roots — NEVER include overly broad umbrella words like transportation when user asked for airlines, or food when user asked for chocolate"],\n'
        '  "core_niche_roots": ["1-4 word stems central to this exact domain, e.g. chocolat, cocoa"],\n'
        '  "must_match_keywords": ["4-10 domain-specific words a genuine matching company would have in its name/description"],\n'
        '  "exclude_prospeo_industries": ["exact Prospeo industries that MUST be excluded so wrong-domain companies never appear — choose from: Machinery Manufacturing, Industrial Machinery Manufacturing, Automation Machinery Manufacturing, Packaging and Containers, Real Estate, IT Services and IT Consulting, Software Development, Marketing Services, Advertising Services, Construction, Business Consulting and Services, Staffing and Recruiting"],\n'
        '  "must_exclude_terms": ["4-10 terms indicating an off-domain company — e.g. for chocolate companies: packaging machinery, equipment distributor, peanut butter, whey protein, protein supplement, real estate, software development, meadery"]\n'
        "}"
    )
    plan = call_xkiro_json(planner_sys, raw_prompt, max_tokens=650, timeout=7.5)

    if mode == "filter" and isinstance(filters, dict):
        f_ind = str(filters.get("industry") or "").strip()
        f_reg = str(filters.get("region") or "").strip()
        f_role = str(filters.get("role") or "").strip()
        f_size = str(filters.get("companySize") or "").strip()
        f_extra = str(filters.get("extra") or "").strip()

        loc_raw = f_reg or str(plan.get("location") or "").strip()
        roles, primary_role = parse_roles_list(f_role)
        hc_ranges = HEADCOUNT_MAP.get(f_size, [])
        ind_terms = [x for x in [f_ind, f_extra] if x] + list(plan.get("broad_industry_terms") or [])
        is_sub = bool(plan.get("is_specific_subniche")) or (bool(f_extra) and not f_ind)
    else:
        loc_raw = str(plan.get("location") or "").strip()
        if not loc_raw:
            m_loc = re.search(r"\b(?:in|from|at|near)\s+([A-Za-z][A-Za-z\s,]{1,32})", raw_prompt, re.I)
            if m_loc:
                loc_raw = re.split(r"\b(?:with|for|having|decision|who|ceo|founder|director)\b", m_loc.group(1), flags=re.I)[0].strip(" ,.")
        has_explicit_role = bool(re.search(r"\b(ceo|cto|cfo|coo|cmo|founder|owner|director|vp|president|partner|sales)\b", raw_prompt, re.I))
        role_txt = ", ".join(plan.get("roles") or []) if has_explicit_role else (raw_prompt if has_explicit_role else "")
        roles, primary_role = parse_roles_list(role_txt)
        hc_ranges = []
        ind_terms = list(plan.get("broad_industry_terms") or [])
        is_sub = bool(plan.get("is_specific_subniche"))

    locations = resolve_prospeo_location(loc_raw) if loc_raw else []
    loc_words = set(re.sub(r"[^a-z0-9\s]", " ", (loc_raw + " " + " ".join(locations)).lower()).split())

    raw_words = [
        w for w in re.sub(r"[^a-z0-9\s-]", " ", raw_prompt.lower()).split()
        if len(w) >= 3 and w not in STOP_WORDS and w not in loc_words and not w.isdigit()
    ]
    # Prioritize user's exact words BEFORE LLM broad industry terms so 'airlines' never expands into 'trucking/transportation'
    ordered_ind_terms = list(raw_words)
    raw_industries = resolve_prospeo_industries(raw_words)
    if not raw_industries:
        for bt in ind_terms:
            if bt not in ordered_ind_terms:
                ordered_ind_terms.append(bt)
        industries = resolve_prospeo_industries(ordered_ind_terms)
    else:
        industries = raw_industries
    must_match = [str(k).lower().strip() for k in (plan.get("must_match_keywords") or []) if len(str(k).strip()) >= 3]
    if not must_match:
        must_match = raw_words[:8]

    ex_inds = [str(x).strip() for x in (plan.get("exclude_prospeo_industries") or []) if x]
    # Never exclude an industry that is in our positive include list
    inc_low = {i.lower() for i in industries}
    ex_inds = [e for e in ex_inds if e.lower() not in inc_low]

    ex_terms = [str(t).lower().strip() for t in (plan.get("must_exclude_terms") or []) if len(str(t).strip()) >= 3]
    core_roots = [str(r).lower().strip() for r in (plan.get("core_niche_roots") or []) if len(str(r).strip()) >= 3]

    target_websites = []
    target_names = []
    niche_label = str(plan.get("target_niche") or raw_prompt).strip()
    if is_sub or (not industries and must_match):
        target_websites, target_names = discover_subniche_companies(niche_label, loc_raw, exclude_companies)

    dedup_kws = list(dict.fromkeys([k for k in (must_match + raw_words) if k not in loc_words and k not in STOP_WORDS]))[:10]
    prospeo_kws = dedup_kws[:8] if (is_sub or not industries) else []

    return (
        {
            "roles": roles,
            "primaryRoleHint": primary_role,
            "locations": locations,
            "industries": industries,
            "excludeIndustries": ex_inds,
            "headcountRanges": hc_ranges,
            "keywords": prospeo_kws,
            "mustMatchKeywords": must_match[:10],
            "mustExcludeTerms": ex_terms[:12],
            "coreNicheRoots": core_roots[:6],
            "websites": target_websites,
            "companyNames": target_names,
        },
        dedup_kws,
    )


def audit_leads_domain_purity(raw_prompt: str, leads: list[dict]) -> list[dict]:
    """Final xKiro strict domain check: removes any company whose primary business does not match the prompt."""
    if not leads or not XKIRO_KEY:
        return leads

    compact = [
        {
            "idx": i,
            "companyName": l.get("companyName", ""),
            "industry": l.get("industry", ""),
            "website": l.get("officialWebsite", ""),
            "summary": str(l.get("companySummary") or "")[:200],
        }
        for i, l in enumerate(leads)
    ]
    sys_p = (
        "You are a strict B2B Lead Quality Auditor. The user searched for a specific type of company. "
        "Review each candidate company and keep ONLY companies whose PRIMARY, CORE business genuinely matches "
        "the exact type of company requested by the user.\n"
        "- Reject machinery/equipment/packaging vendors unless the user explicitly asked for machinery/equipment/packaging.\n"
        "- Reject companies from adjacent/unrelated domains (e.g. if user asked for 'chocolate companies', reject peanut-butter brands, protein supplement brands, general bakeries/coffee brands unless they are primarily a chocolate maker/chocolatier, real estate, IT, etc.).\n"
        'Return STRICT JSON ONLY: {"keep_indices": [0, 1, ...]}'
    )
    usr_p = json.dumps({"userSearch": raw_prompt, "candidates": compact})
    verdict = call_xkiro_json(sys_p, usr_p, max_tokens=220, timeout=7.5)
    keep = verdict.get("keep_indices")
    if isinstance(keep, list):
        keep_set = {int(x) for x in keep if isinstance(x, (int, float)) or str(x).isdigit()}
        filtered = [l for i, l in enumerate(leads) if i in keep_set]
        return filtered
    return leads


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    with DB_LOCK:
        conn = db_connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    handle TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    name_norm TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    sender_name TEXT NOT NULL,
                    offer TEXT NOT NULL,
                    email_subject TEXT NOT NULL,
                    email_body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_users_token ON users(token);

                CREATE TABLE IF NOT EXISTS batches (
                    id TEXT PRIMARY KEY,
                    handle TEXT NOT NULL,
                    prompt_sig TEXT NOT NULL,
                    batch_number INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    prompt_display TEXT NOT NULL,
                    raw_prompt TEXT NOT NULL,
                    filters_json TEXT,
                    routing_json TEXT,
                    leads_json TEXT NOT NULL,
                    csv_text TEXT,
                    elapsed_sec REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(handle) REFERENCES users(handle)
                );
                CREATE INDEX IF NOT EXISTS idx_batches_handle_created ON batches(handle, created_at DESC);

                CREATE TABLE IF NOT EXISTS excluded_companies (
                    handle TEXT NOT NULL,
                    prompt_sig TEXT NOT NULL,
                    company_norm TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (handle, prompt_sig, company_norm)
                );
                """
            )
            conn.commit()
        finally:
            conn.close()


def normalize_handle(raw: str) -> str:
    return str(raw or "").strip().lstrip("@").lower()


def normalize_name(raw: str) -> str:
    return re.sub(r"\s+", " ", str(raw or "").strip()).lower()


def compute_prompt_sig(mode: str, raw_prompt: str, filters: dict | None) -> str:
    if mode == "filter" and isinstance(filters, dict):
        canon = json.dumps(
            {k: str(filters.get(k, "")).strip().lower() for k in sorted(filters.keys())},
            sort_keys=True,
        )
        base = f"filter:{canon}"
    else:
        base = f"prompt:{re.sub(r'\\s+', ' ', raw_prompt.strip().lower())}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def n8n_json(method: str, path: str, payload=None, timeout: int = 240):
    url = f"{N8N_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return resp.status, json.loads(raw) if raw else {}


def sync_template_to_n8n(user_row: dict):
    try:
        n8n_json(
            "POST",
            "/webhook/b2b-smart-leads-template",
            {
                "userId": f"u_{user_row['handle']}",
                "senderName": user_row["sender_name"],
                "subject": user_row["email_subject"],
                "body": user_row["email_body"],
            },
            timeout=12,
        )
    except Exception:
        pass


def get_user_by_token(token: str) -> dict | None:
    if not token:
        return None
    with DB_LOCK:
        conn = db_connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def get_excluded_for_user(handle: str, prompt_sig: str) -> tuple[list[str], int]:
    with DB_LOCK:
        conn = db_connect()
        try:
            rows = conn.execute(
                "SELECT company_name FROM excluded_companies WHERE handle = ? AND prompt_sig = ? ORDER BY created_at ASC",
                (handle, prompt_sig),
            ).fetchall()
            bcount = conn.execute(
                "SELECT COUNT(*) AS c FROM batches WHERE handle = ? AND prompt_sig = ?",
                (handle, prompt_sig),
            ).fetchone()["c"]
            return [r["company_name"] for r in rows], int(bcount)
        finally:
            conn.close()


def save_batch_for_user(
    handle: str,
    prompt_sig: str,
    batch_number: int,
    mode: str,
    prompt_display: str,
    raw_prompt: str,
    filters: dict | None,
    result: dict,
    elapsed_sec: float,
):
    leads = result.get("leads") or []
    routing = result.get("routingSummary") or {}
    csv_text = result.get("csvExport") or ""
    now = utc_now_iso()
    batch_id = f"b_{int(time.time()*1000)}_{secrets.token_hex(3)}"

    with DB_LOCK:
        conn = db_connect()
        try:
            conn.execute(
                """
                INSERT INTO batches (
                    id, handle, prompt_sig, batch_number, mode, prompt_display,
                    raw_prompt, filters_json, routing_json, leads_json, csv_text,
                    elapsed_sec, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    handle,
                    prompt_sig,
                    batch_number,
                    mode,
                    prompt_display,
                    raw_prompt,
                    json.dumps(filters) if filters else None,
                    json.dumps(routing),
                    json.dumps(leads),
                    csv_text,
                    elapsed_sec,
                    now,
                ),
            )
            for l in leads:
                cname = str(l.get("companyName") or "").strip()
                cnorm = re.sub(r"[^a-z0-9]", "", cname.lower())
                if cname and cnorm:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO excluded_companies (
                            handle, prompt_sig, company_norm, company_name, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (handle, prompt_sig, cnorm, cname, now),
                    )
            conn.commit()
        finally:
            conn.close()


def run_job(
    job_id: str,
    user_row: dict,
    mode: str,
    raw_prompt: str,
    prompt_display: str,
    filters: dict | None,
    prompt_sig: str,
    make_another_5: bool,
    force_backup_race: bool,
    pathway: str = "free_apis",
):
    t0 = time.time()
    handle = user_row["handle"]
    pathway_clean = "tinyfish" if str(pathway or "").strip().lower() == "tinyfish" else "free_apis"
    try:
        with JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id]["stage"] = "resolving_pure_domains"
        sync_template_to_n8n(user_row)
        excl_companies, prev_batches = get_excluded_for_user(handle, prompt_sig)
        batch_num = prev_batches + 1

        prospeo_filters, ind_keywords = resolve_targeting_bundle(mode, raw_prompt, filters, excl_companies, pathway=pathway_clean)

        with JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id]["stage"] = "running_tinyfish_guesser_mailmeteor" if pathway_clean == "tinyfish" else "running_free_api_waterfall"

        n8n_payload = {
            "prompt": raw_prompt,
            "userId": f"u_{handle}",
            "pathway": pathway_clean,
            "makeAnother5": bool(make_another_5 or prev_batches > 0),
            "excludeCompanies": excl_companies,
            "prospeoFilters": prospeo_filters,
            "industryKeywords": ind_keywords,
            "strictIndustry": True,
            "senderName": user_row["sender_name"],
            "offer": user_row["offer"],
            "forceBackupRaceTest": bool(force_backup_race),
        }

        status_code, data = n8n_json("POST", "/webhook/b2b-smart-leads", n8n_payload, timeout=240)

        if isinstance(data, dict) and data.get("ok") is not False:
            with JOBS_LOCK:
                if job_id in JOBS:
                    JOBS[job_id]["stage"] = "auditing_domain_purity"
            raw_leads = data.get("leads") or []
            pure_leads = audit_leads_domain_purity(raw_prompt, raw_leads)

            # If post-audit removed off-domain companies leaving fewer than 5 leads, top up via live TinyFish + Smart Guesser + Mailmeteor!
            if len(pure_leads) < 5 and not force_backup_race and (time.time() - t0) < 105:
                seen_names = list(excl_companies) + [str(x.get("companyName") or "") for x in (raw_leads + pure_leads) if x.get("companyName")]
                seen_norm = {re.sub(r"[^a-z0-9]", "", str(x.get("companyName") or "").lower()) for x in pure_leads}
                try:
                    with JOBS_LOCK:
                        if job_id in JOBS:
                            JOBS[job_id]["stage"] = "running_tinyfish_guesser_mailmeteor"
                    topup_payload = dict(n8n_payload)
                    topup_payload["excludeCompanies"] = seen_names
                    topup_payload["pathway"] = "tinyfish"
                    pf_copy = dict(prospeo_filters)
                    pf_copy["companyNames"] = [
                        cn_i for cn_i in (prospeo_filters.get("companyNames") or [])
                        if re.sub(r"[^a-z0-9]", "", str(cn_i or "").lower()) not in {re.sub(r"[^a-z0-9]", "", s.lower()) for s in seen_names}
                    ]
                    topup_payload["prospeoFilters"] = pf_copy
                    sc2, data2 = n8n_json("POST", "/webhook/b2b-smart-leads", topup_payload, timeout=150)
                    if sc2 < 400 and isinstance(data2, dict):
                        extra_pure = audit_leads_domain_purity(raw_prompt, data2.get("leads") or [])
                        for ep in extra_pure:
                            if len(pure_leads) >= 5:
                                break
                            cn = re.sub(r"[^a-z0-9]", "", str(ep.get("companyName") or "").lower())
                            if cn and cn not in seen_norm:
                                seen_norm.add(cn)
                                pure_leads.append(ep)
                except Exception:
                    pass

            final_leads = pure_leads[:5]
            for idx, ld in enumerate(final_leads, 1):
                ld["leadNumber"] = (batch_num - 1) * 5 + idx
            data["leads"] = final_leads
            data["count"] = len(final_leads)
            data["batchNumber"] = batch_num
            start_idx = (batch_num - 1) * 5 + 1
            end_idx = (batch_num - 1) * 5 + len(final_leads)
            data["leadRange"] = f"{start_idx}–{end_idx}" if end_idx >= start_idx else "0"

            # Rebuild CSV export so it matches final audited leads 1:1
            def _csv_esc(v):
                s = str(v or "").replace('"', '""')
                return f'"{s}"' if any(c in s for c in (',', '"', '\n', '\r')) else s
            csv_hdr = ["Lead #", "Company Name", "Official Website", "Industry", "Location", "Company Summary", "Decision Maker", "Job Title", "Email", "Email Status", "LinkedIn", "Source API", "Cold Email Subject", "Cold Email Body"]
            csv_rows = [",".join(csv_hdr)]
            for ld in final_leads:
                ce = ld.get("coldEmail") or {}
                csv_rows.append(",".join(_csv_esc(x) for x in [
                    ld.get("leadNumber", ""), ld.get("companyName", ""), ld.get("officialWebsite", ""),
                    ld.get("industry", ""), ld.get("location", ""), ld.get("companySummary", ""),
                    ld.get("decisionMakerName", ""), ld.get("jobTitle", ""), ld.get("email", ""),
                    ld.get("emailVerificationStatus", ""), ld.get("linkedinUrl", ""), ld.get("sourceApi", ""),
                    ce.get("subject", ""), ce.get("body", ""),
                ]))
            data["csvExport"] = "\n".join(csv_rows)

            elapsed = round(time.time() - t0, 1)
            save_batch_for_user(
                handle=handle,
                prompt_sig=prompt_sig,
                batch_number=batch_num,
                mode=mode,
                prompt_display=prompt_display,
                raw_prompt=raw_prompt,
                filters=filters,
                result=data,
                elapsed_sec=elapsed,
            )
        else:
            elapsed = round(time.time() - t0, 1)

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "completed" if status_code < 400 else "failed"
            JOBS[job_id]["result"] = data
            JOBS[job_id]["elapsedSec"] = elapsed
            JOBS[job_id]["excludedCompaniesCount"] = len(excl_companies)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = f"HTTP {e.code}: {err_body[:300]}"
            JOBS[job_id]["elapsedSec"] = round(time.time() - t0, 1)
    except Exception as e:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(e)
            JOBS[job_id]["elapsedSec"] = round(time.time() - t0, 1)


class SmartWebHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[leadscaler-web] {self.address_string()} - {fmt % args}", flush=True)

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Auth-Token, ngrok-skip-browser-warning")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_json(self, code: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html_bytes: bytes):
        self.send_response(200)
        self._send_cors()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        return json.loads(raw or "{}")

    def _require_user(self) -> dict | None:
        token = self.headers.get("X-Auth-Token", "").strip()
        u = get_user_by_token(token)
        if not u:
            self._send_json(401, {"ok": False, "error": "Please sign in with your name and @handle first."})
            return None
        return u

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            with open(UI_HTML_PATH, "rb") as f:
                self._send_html(f.read())
            return

        if path == "/api/health":
            out = {"ok": True, "webUi": "online"}
            try:
                _, h = n8n_json("GET", "/webhook/b2b-smart-leads-health", None, timeout=8)
                out["n8n"] = h
            except Exception as e:
                out["n8n"] = {"ok": False, "error": str(e)}
            try:
                with urllib.request.urlopen(RACE_HEALTH_URL, timeout=5) as r:
                    out["raceService"] = json.loads(r.read().decode("utf-8"))
            except Exception as e:
                out["raceService"] = {"ok": False, "error": str(e)}
            self._send_json(200, out)
            return

        if path == "/api/auth/check-handle":
            qs = parse_qs(parsed.query)
            handle = normalize_handle((qs.get("handle") or [""])[0])
            if not re.match(r"^[a-z0-9._]{3,30}$", handle):
                self._send_json(200, {"ok": True, "valid": False, "exists": False})
                return
            with DB_LOCK:
                conn = db_connect()
                try:
                    row = conn.execute("SELECT handle FROM users WHERE handle = ?", (handle,)).fetchone()
                finally:
                    conn.close()
            self._send_json(200, {"ok": True, "valid": True, "exists": bool(row), "handle": handle})
            return

        if path == "/api/me":
            u = self._require_user()
            if not u:
                return
            with DB_LOCK:
                conn = db_connect()
                try:
                    b_rows = conn.execute(
                        "SELECT * FROM batches WHERE handle = ? ORDER BY created_at DESC LIMIT 50",
                        (u["handle"],),
                    ).fetchall()
                finally:
                    conn.close()
            batches = []
            for b in b_rows:
                batches.append(
                    {
                        "id": b["id"],
                        "batchNumber": b["batch_number"],
                        "mode": b["mode"],
                        "promptDisplay": b["prompt_display"],
                        "rawPrompt": b["raw_prompt"],
                        "filters": json.loads(b["filters_json"]) if b["filters_json"] else None,
                        "routing": json.loads(b["routing_json"]) if b["routing_json"] else {},
                        "leads": json.loads(b["leads_json"]) if b["leads_json"] else [],
                        "csvText": b["csv_text"] or "",
                        "elapsedSec": b["elapsed_sec"],
                        "createdAt": b["created_at"],
                    }
                )
            self._send_json(
                200,
                {
                    "ok": True,
                    "user": {
                        "handle": u["handle"],
                        "fullName": u["full_name"],
                        "senderName": u["sender_name"],
                        "offer": u["offer"],
                        "emailSubject": u["email_subject"],
                        "emailBody": u["email_body"],
                    },
                    "batches": batches,
                },
            )
            return

        if path.startswith("/api/jobs/"):
            u = self._require_user()
            if not u:
                return
            job_id = path.split("/api/jobs/", 1)[1].strip()
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if not job or job.get("handle") != u["handle"]:
                    self._send_json(404, {"ok": False, "error": "Job not found"})
                    return
                resp = dict(job)
                if resp["status"] == "running":
                    resp["elapsedSec"] = round(time.time() - resp["startedAt"], 1)
            self._send_json(200, resp)
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json()
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {e}"})
            return

        if path == "/api/auth/login":
            full_name = re.sub(r"\s+", " ", str(body.get("fullName") or "").strip())
            handle = normalize_handle(body.get("handle") or "")
            name_norm = normalize_name(full_name)

            if len(full_name) < 2:
                self._send_json(400, {"ok": False, "error": "Please enter your full name (at least 2 characters)."})
                return
            if not re.match(r"^[a-z0-9._]{3,30}$", handle):
                self._send_json(
                    400,
                    {"ok": False, "error": "Unique handle must be 3–30 characters using lowercase letters, numbers, '.' or '_'."},
                )
                return

            now = utc_now_iso()
            with DB_LOCK:
                conn = db_connect()
                try:
                    existing = conn.execute("SELECT * FROM users WHERE handle = ?", (handle,)).fetchone()
                    if existing:
                        if existing["name_norm"] != name_norm:
                            self._send_json(
                                409,
                                {
                                    "ok": False,
                                    "error": f"@{handle} is already taken by another user. Choose your own unique @handle (or enter the exact name registered with @{handle}).",
                                },
                            )
                            return
                        conn.execute("UPDATE users SET last_login_at = ? WHERE handle = ?", (now, handle))
                        conn.commit()
                        token = existing["token"]
                        ret_name = existing["full_name"]
                        returning = True
                    else:
                        token = secrets.token_urlsafe(28)
                        conn.execute(
                            """
                            INSERT INTO users (
                                handle, full_name, name_norm, token, sender_name,
                                offer, email_subject, email_body, created_at, last_login_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                handle,
                                full_name,
                                name_norm,
                                token,
                                full_name,
                                DEFAULT_OFFER,
                                DEFAULT_EMAIL_SUBJECT,
                                DEFAULT_EMAIL_BODY,
                                now,
                                now,
                            ),
                        )
                        conn.commit()
                        ret_name = full_name
                        returning = False
                finally:
                    conn.close()

            self._send_json(
                200,
                {
                    "ok": True,
                    "returning": returning,
                    "token": token,
                    "user": {"handle": handle, "fullName": ret_name},
                },
            )
            return

        if path == "/api/settings":
            u = self._require_user()
            if not u:
                return
            sender_name = str(body.get("senderName") or u["full_name"]).strip()[:80] or u["full_name"]
            offer = str(body.get("offer") or DEFAULT_OFFER).strip()[:240] or DEFAULT_OFFER
            email_subject = str(body.get("emailSubject") or DEFAULT_EMAIL_SUBJECT).strip()[:180] or DEFAULT_EMAIL_SUBJECT
            email_body = str(body.get("emailBody") or DEFAULT_EMAIL_BODY).strip()[:4000] or DEFAULT_EMAIL_BODY

            with DB_LOCK:
                conn = db_connect()
                try:
                    conn.execute(
                        """
                        UPDATE users
                        SET sender_name = ?, offer = ?, email_subject = ?, email_body = ?
                        WHERE handle = ?
                        """,
                        (sender_name, offer, email_subject, email_body, u["handle"]),
                    )
                    conn.commit()
                    updated = dict(conn.execute("SELECT * FROM users WHERE handle = ?", (u["handle"],)).fetchone())
                finally:
                    conn.close()

            sync_template_to_n8n(updated)
            self._send_json(200, {"ok": True})
            return

        if path == "/api/jobs":
            u = self._require_user()
            if not u:
                return

            mode = "filter" if str(body.get("mode") or "").lower() == "filter" else "prompt"
            filters = body.get("filters") if isinstance(body.get("filters"), dict) else None
            make_another_5 = bool(body.get("makeAnother5"))
            force_race = bool(body.get("forceBackupRaceTest"))
            # Default pathway is ALWAYS 'free_apis' (Prospeo -> Clay -> Hunter -> Apollo) if user selects nothing!
            raw_pw = str(body.get("pathway") or "").strip().lower()
            pathway = "tinyfish" if raw_pw == "tinyfish" else "free_apis"
            est_min, est_max = (25, 42) if pathway == "tinyfish" else (20, 35)

            if mode == "filter":
                if not filters or not any(str(v or "").strip() for v in filters.values()):
                    self._send_json(400, {"ok": False, "error": "Please select at least one filter criterion."})
                    return
                raw_prompt, prompt_display = build_filter_prompt(filters)
            else:
                raw_prompt = str(body.get("prompt") or "").strip()
                if len(raw_prompt) < 3:
                    self._send_json(400, {"ok": False, "error": "Please enter a target prompt (at least 3 characters)."})
                    return
                prompt_display = raw_prompt

            prompt_sig = compute_prompt_sig(mode, raw_prompt, filters)
            job_id = f"job_{int(time.time()*1000)}_{secrets.token_hex(4)}"

            with JOBS_LOCK:
                if len(JOBS) > 300:
                    cutoff = time.time() - 3600
                    for k in [k for k, v in JOBS.items() if v.get("startedAt", 0) < cutoff]:
                        JOBS.pop(k, None)
                JOBS[job_id] = {
                    "ok": True,
                    "jobId": job_id,
                    "handle": u["handle"],
                    "mode": mode,
                    "pathway": pathway,
                    "estimatedSecMin": est_min,
                    "estimatedSecMax": est_max,
                    "stage": "resolving_pure_domains",
                    "promptDisplay": prompt_display,
                    "status": "running",
                    "startedAt": time.time(),
                    "elapsedSec": 0.0,
                }

            t = threading.Thread(
                target=run_job,
                args=(job_id, u, mode, raw_prompt, prompt_display, filters, prompt_sig, make_another_5, force_race, pathway),
                daemon=True,
            )
            t.start()
            self._send_json(202, {
                "ok": True,
                "jobId": job_id,
                "status": "running",
                "pathway": pathway,
                "estimatedSecMin": est_min,
                "estimatedSecMax": est_max,
                "promptDisplay": prompt_display,
            })
            return

        self._send_json(404, {"ok": False, "error": "Not found"})


if __name__ == "__main__":
    init_db()
    print(f"[leadscaler-web] Starting on http://{HOST}:{PORT} -> DB={DB_PATH} -> N8N={N8N_BASE}", flush=True)
    srv = ThreadingHTTPServer((HOST, PORT), SmartWebHandler)
    srv.serve_forever()
