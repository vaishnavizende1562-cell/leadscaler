#!/usr/bin/env python3
"""
leadgen-mailmeteor-race — Official Mailmeteor Web Email Checker (one-by-one browser automation)
+ Time-Bounded Smart Email Pattern Guesser (between TinyFish/Clay & Mailmeteor)
+ First-to-Finish Parallel Lead Race Coordinator (LeadPulse AI vs TinyFish AI + TinyFish Direct Pathway).

Binds 172.18.0.1:8097 (internal Docker bridge only, never public).
Runs under xvfb-run so Patchright Chrome passes Cloudflare Turnstile on
https://mailmeteor.com/email-checker cleanly one email at a time.
"""

import json
import os
import queue
import re
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Force IPv4 DNS resolution on NAT-IPv4 VPS so outbound HTTPS never hangs on IPv6
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == 0:
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4_getaddrinfo

BIND = os.environ.get("MM_BIND", "172.18.0.1")
PORT = int(os.environ.get("MM_PORT", "8097"))
DB_PATH = os.environ.get("MM_DB", "/opt/leadgen/mailmeteor_race/mailmeteor_cache.db")
ENV_FILE = os.environ.get("N8N_ENV_FILE", "/opt/n8n/.env")
SMTP_VERIFIER_URL = os.environ.get("SMTP_VERIFIER_URL", "http://172.18.0.1:8099/verify")
MAILMETEOR_URL = "https://mailmeteor.com/email-checker"
CACHE_TTL_SEC = 30 * 86400

# Default Time-Cap Guards for Smart Email Guesser (prevents slow/hanging output!)
DEFAULT_PER_LEAD_GUESS_TIMEOUT_SEC = 8.0
DEFAULT_TOTAL_GUESS_STAGE_TIMEOUT_SEC = 20.0

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9.\-]{2,253}\.[A-Za-z]{2,24}$")
GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
    "icloud.com", "aol.com", "proton.me", "protonmail.com", "rediffmail.com",
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "wikipedia.org", "crunchbase.com", "glassdoor.com",
    "ambitionbox.com", "zaubacorp.com", "indiamart.com", "justdial.com", "clutch.co",
    "zoominfo.com", "apollo.io", "rocketreach.co", "signalhire.com", "lusha.com"
}
HONORIFICS = {"mr", "ms", "mrs", "dr", "er", "shri", "smt", "prof", "ca", "cs", "decision", "maker", "executive", "contact"}
ROLE_PREFIX_RE = re.compile(r"^(support|info|contact|hello|sales|team|admin|office|help|careers|hr|enquiries|enquiry)@", re.I)
DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def load_env_file(path):
    cfg = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, v = s.split("=", 1)
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def get_secret(key, default=""):
    val = os.environ.get(key)
    if val:
        return val
    return load_env_file(ENV_FILE).get(key, default)


# ---------------- SQLite Cache for Mailmeteor One-by-One Checks ----------------
_db_lock = threading.Lock()
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
_db = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
_db.execute("""
CREATE TABLE IF NOT EXISTS mailmeteor_checks (
    email TEXT PRIMARY KEY,
    status TEXT,
    deliverable INTEGER,
    is_disposable INTEGER,
    is_free_provider INTEGER,
    checks_json TEXT,
    checked_via TEXT,
    checked_at INTEGER
)
""")
_db.commit()


def cache_get_email(email):
    e = email.lower().strip()
    with _db_lock:
        row = _db.execute(
            "SELECT status, deliverable, is_disposable, is_free_provider, checks_json, checked_via, checked_at "
            "FROM mailmeteor_checks WHERE email=?",
            (e,),
        ).fetchone()
    if not row:
        return None
    if time.time() - row[6] > CACHE_TTL_SEC:
        return None
    return {
        "email": e,
        "status": row[0],
        "deliverable": bool(row[1]),
        "is_disposable": bool(row[2]),
        "is_free_provider": bool(row[3]),
        "checks": json.loads(row[4] or "{}"),
        "checkedVia": row[5],
        "cached": True,
        "mailmeteorPage": MAILMETEOR_URL,
    }


def cache_put_email(res):
    e = res["email"].lower().strip()
    with _db_lock:
        _db.execute(
            "INSERT OR REPLACE INTO mailmeteor_checks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                e,
                res.get("status", "unknown"),
                1 if res.get("deliverable") else 0,
                1 if res.get("is_disposable") else 0,
                1 if res.get("is_free_provider") else 0,
                json.dumps(res.get("checks") or {}),
                res.get("checkedVia", "mailmeteor_web_checker"),
                int(time.time()),
            ),
        )
        _db.commit()


# ---------------- Local Port-25 Batch & Single SMTP Verifier ----------------
def _local_smtp_batch_check(emails, timeout_s=4.5):
    if not emails:
        return {}
    try:
        req = urllib.request.Request(
            SMTP_VERIFIER_URL,
            data=json.dumps({"emails": list(emails)}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=max(1.2, float(timeout_s))) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            out = {}
            for item in (data.get("results") or []):
                em = str(item.get("email") or "").lower().strip()
                if em:
                    out[em] = item
            return out
    except Exception:
        return {}


def _local_smtp_cross_check(email, timeout_s=8.0):
    res = _local_smtp_batch_check([email], timeout_s=timeout_s)
    return res.get(email.lower().strip())


# ---------------- Dedicated Persistent Mailmeteor Browser Worker Thread ----------------
_mm_task_queue = queue.Queue()
_mm_worker_ready = threading.Event()
_mm_browser_healthy = [False]


def _mailmeteor_browser_worker():
    from patchright.sync_api import sync_playwright

    pw = None
    browser = None
    page = None
    captured_api = []

    def ensure_page(force_reload=False):
        nonlocal pw, browser, page
        if pw is None:
            pw = sync_playwright().start()
        if browser is None or not browser.is_connected():
            browser = pw.chromium.launch(
                channel="chrome",
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-ipv6",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            page = None
        if page is None or page.is_closed():
            ctx = browser.new_context(viewport={"width": 1366, "height": 850})
            page = ctx.new_page()

            def on_resp(r):
                if "tools.mailmeteor.com/api/email-checker" in r.url:
                    try:
                        captured_api.append((r.status, r.json(), time.time()))
                    except Exception:
                        pass

            page.on("response", on_resp)
            page.goto(MAILMETEOR_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2.8)
            _mm_browser_healthy[0] = True
        elif force_reload:
            page.goto(MAILMETEOR_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2.2)
        return page

    try:
        ensure_page()
    except Exception as e:
        print(f"[mailmeteor-worker] initial warmup error: {e}", flush=True)
    _mm_worker_ready.set()

    while True:
        task = _mm_task_queue.get()
        if len(task) == 3:
            email, reply_q, deadline_mono = task
        else:
            email, reply_q = task
            deadline_mono = time.monotonic() + 28.0

        try:
            email = email.strip().lower()
            cached = cache_get_email(email)
            if cached:
                reply_q.put(cached)
                continue

            # If caller's hard time cap already expired while queued, skip immediately!
            if time.monotonic() >= deadline_mono:
                reply_q.put({
                    "email": email,
                    "status": "timeout_skipped",
                    "deliverable": False,
                    "checkedVia": "time_cap_expired",
                    "cached": False,
                    "timedOut": True,
                    "mailmeteorPage": MAILMETEOR_URL,
                })
                continue

            if not EMAIL_RE.match(email):
                reply_q.put({
                    "email": email,
                    "status": "invalid",
                    "deliverable": False,
                    "is_disposable": False,
                    "is_free_provider": False,
                    "checks": {"format": {"status": "invalid"}},
                    "checkedVia": "syntax_guard",
                    "cached": False,
                    "mailmeteorPage": MAILMETEOR_URL,
                })
                continue

            pg = ensure_page()
            try:
                h3_now = pg.locator(".result-header h3").inner_text().strip() if pg.locator(".result-header h3").count() else ""
                if "Checking" in h3_now:
                    pg = ensure_page(force_reload=True)
            except Exception:
                pg = ensure_page(force_reload=True)

            try:
                pg.evaluate("""() => {
                    try { localStorage.setItem('tools.email_checker.verification.last_shown', String(Date.now())); } catch (_) {}
                    document.querySelectorAll('.modal, .modal-backdrop').forEach(el => {
                        el.classList.remove('show');
                        el.style.display = 'none';
                        if (el.classList.contains('modal-backdrop')) el.remove();
                    });
                    document.body.classList.remove('modal-open');
                }""")
            except Exception:
                pass

            start_idx = len(captured_api)
            pg.fill("#email-to-check", "")
            pg.fill("#email-to-check", email)
            pg.click('button[type="submit"]', timeout=5000)

            matched_payload = None
            timed_out_in_browser = False
            rem_total = deadline_mono - time.monotonic()
            browser_budget = min(7.5, rem_total - 2.5) if rem_total >= 5.5 else max(1.0, rem_total - 0.35)
            browser_end = time.monotonic() + browser_budget
            max_steps = min(20, max(3, int(browser_budget / 0.45)))
            for step in range(max_steps):
                if time.monotonic() >= browser_end:
                    timed_out_in_browser = True
                    break
                time.sleep(0.45)
                for st_code, body_json, _ts in captured_api[start_idx:]:
                    if isinstance(body_json, dict):
                        if str(body_json.get("email", "")).lower() == email or body_json.get("error"):
                            matched_payload = (st_code, body_json)
                            break
                if matched_payload:
                    break
                if step in (5, 11):
                    try:
                        box = pg.locator("#cloudflare-captcha").bounding_box()
                        if box and box["width"] > 20 and box["height"] > 20:
                            pg.mouse.click(box["x"] + 28, box["y"] + box["height"] / 2)
                    except Exception:
                        pass
                if step > 7:
                    try:
                        h3_txt = pg.locator(".result-header h3").inner_text().strip() if pg.locator(".result-header h3").count() else ""
                        if "Oops" in h3_txt:
                            break
                    except Exception:
                        pass

            if matched_payload and matched_payload[0] == 200 and not matched_payload[1].get("error"):
                mj = matched_payload[1]
                mm_status = str(mj.get("status", "unknown")).lower()
                checks = mj.get("checks") or {}
                is_disp = bool(mj.get("is_disposable", False))
                is_free = bool(mj.get("is_free_provider", False))
                dns_ok = (checks.get("dns") or {}).get("status") == "valid"
                mx_ok = (checks.get("mx") or {}).get("status") == "valid"

                deliverable = False
                checked_via = "mailmeteor_web_checker"
                if mm_status == "valid" and not is_disp:
                    deliverable = True
                elif mm_status == "invalid" or is_disp or not dns_ok or not mx_ok:
                    deliverable = False
                else:
                    rem_smtp = max(1.2, min(6.0, deadline_mono - time.monotonic()))
                    smtp_probe = _local_smtp_cross_check(email, timeout_s=rem_smtp) if rem_smtp > 1.3 else None
                    if smtp_probe:
                        verdict = smtp_probe.get("verdict", "")
                        if verdict == "verified":
                            mm_status = "valid"
                            deliverable = True
                            checked_via = "mailmeteor_web + local_smtp_verified"
                        elif verdict in ("invalid", "no-mx", "disposable", "syntax-invalid"):
                            mm_status = "invalid"
                            deliverable = False
                            checked_via = "mailmeteor_web + local_smtp_rejected"
                        else:
                            deliverable = dns_ok and mx_ok and not is_disp
                            checked_via = f"mailmeteor_web ({mm_status})"
                    else:
                        deliverable = dns_ok and mx_ok and not is_disp

                out = {
                    "email": email,
                    "status": mm_status,
                    "deliverable": deliverable,
                    "is_disposable": is_disp,
                    "is_free_provider": is_free,
                    "checks": checks,
                    "checkedVia": checked_via,
                    "cached": False,
                    "mailmeteorPage": MAILMETEOR_URL,
                }
                cache_put_email(out)
                reply_q.put(out)
            else:
                if timed_out_in_browser and (deadline_mono - time.monotonic()) <= 0.8:
                    reply_q.put({
                        "email": email,
                        "status": "timeout_skipped",
                        "deliverable": False,
                        "checkedVia": "time_cap_expired",
                        "cached": False,
                        "timedOut": True,
                        "mailmeteorPage": MAILMETEOR_URL,
                    })
                    continue

                rem_smtp = max(1.2, min(5.0, deadline_mono - time.monotonic()))
                smtp_probe = _local_smtp_cross_check(email, timeout_s=rem_smtp) or {}
                verdict = smtp_probe.get("verdict", "unknown")
                deliverable = verdict in ("verified", "catchall-unknown", "greylist", "probe-refused")
                out = {
                    "email": email,
                    "status": "valid" if verdict == "verified" else ("invalid" if verdict in ("invalid", "no-mx", "disposable") else "unknown"),
                    "deliverable": deliverable and verdict not in ("invalid", "no-mx", "disposable", "syntax-invalid"),
                    "is_disposable": verdict == "disposable",
                    "is_free_provider": email.split("@")[-1] in GENERIC_DOMAINS,
                    "checks": {"smtp_fallback": smtp_probe},
                    "checkedVia": "mailmeteor_rate_limited_local_smtp_fallback",
                    "cached": False,
                    "mailmeteorPage": MAILMETEOR_URL,
                }
                if verdict in ("verified", "invalid", "no-mx"):
                    cache_put_email(out)
                reply_q.put(out)
        except Exception as e:
            reply_q.put({
                "email": email,
                "status": "unknown",
                "deliverable": False,
                "error": str(e),
                "checkedVia": "mailmeteor_worker_error",
                "mailmeteorPage": MAILMETEOR_URL,
            })


def check_one_email_on_mailmeteor(email, timeout_s=24.0, deadline_mono=None):
    now_m = time.monotonic()
    eff_deadline = min(now_m + float(timeout_s), deadline_mono) if deadline_mono is not None else (now_m + float(timeout_s))
    wait_s = max(0.1, eff_deadline - now_m)
    if wait_s <= 0.25:
        return {
            "email": email,
            "status": "timeout_skipped",
            "deliverable": False,
            "timedOut": True,
            "checkedVia": "time_cap_expired",
            "mailmeteorPage": MAILMETEOR_URL,
        }
    rq = queue.Queue(maxsize=1)
    _mm_task_queue.put((email, rq, eff_deadline))
    try:
        return rq.get(timeout=wait_s + 0.3)
    except queue.Empty:
        return {
            "email": email,
            "status": "timeout_skipped",
            "deliverable": False,
            "timedOut": True,
            "checkedVia": "mailmeteor_timeout",
            "mailmeteorPage": MAILMETEOR_URL,
        }


# ---------------- Smart Email Pattern Guesser (Between TinyFish/Clay & Mailmeteor) ----------------
def clean_domain(raw_dom):
    d = re.sub(r"^https?://(www\.)?", "", str(raw_dom or "").strip().lower()).split("/")[0].strip()
    if not d or "." not in d or d in GENERIC_DOMAINS or any(d.endswith("." + g) for g in GENERIC_DOMAINS):
        return ""
    return d


def build_smart_email_guesses(full_name, domain, existing_email="", linkedin_url=""):
    """
    Returns (primary_email_or_none, smart_guesses_list).
    - If TinyFish scraped a direct email on that company domain, it is returned as `primary_email`
      so Mailmeteor tests TinyFish's scraped email FIRST.
    - If that email is invalid (or missing), the Smart Email Guesser tests `smart_guesses_list`
      in order of B2B probability up to the strict per-lead / stage time cap!
    """
    dom = clean_domain(domain)
    primary = ""
    ex = str(existing_email or "").strip().lower()
    if ex and EMAIL_RE.match(ex):
        ex_dom = ex.split("@")[-1]
        if ex_dom not in GENERIC_DOMAINS:
            if not dom:
                dom = ex_dom
                primary = ex
            elif ex_dom == dom or _doh_has_mx(ex_dom, timeout_s=1.5) is True:
                primary = ex

    guesses = []
    if dom:
        parts = [re.sub(r"[^a-z]", "", p.lower()) for p in str(full_name or "").split()]
        parts = [p for p in parts if len(p) >= 2 and p not in HONORIFICS]

        # Extract vanity LinkedIn handle if clean alphabetic (e.g. /in/cmuppala/ -> cmuppala@domain)
        li_slug = ""
        m_li = re.search(r"linkedin\.com/in/([a-zA-Z][a-zA-Z._\-]{2,24})/?$", str(linkedin_url or "").strip().split("?")[0])
        if m_li:
            raw_slug = m_li.group(1).lower().strip("-_.")
            # Only use vanity slug if it has no random trailing digits
            if not re.search(r"\d", raw_slug) and "-" not in raw_slug and len(raw_slug) <= 18:
                li_slug = raw_slug

        if parts:
            first = parts[0]
            guesses.append(f"{first}@{dom}")
            if len(parts) >= 2:
                last = parts[-1]
                guesses.append(f"{first}.{last}@{dom}")
                guesses.append(f"{first[0]}{last}@{dom}")
                guesses.append(f"{first}{last}@{dom}")
                guesses.append(f"{first}_{last}@{dom}")
                guesses.append(f"{first}{last[0]}@{dom}")
            if li_slug:
                guesses.insert(2 if len(guesses) >= 2 else len(guesses), f"{li_slug}@{dom}")

        # Only fall back to role mailbox if no personal name was available
        if not parts:
            guesses.extend([f"founder@{dom}", f"info@{dom}", f"contact@{dom}"])

    # Deduplicate & exclude `primary` from fallback guesses so we never check the same email twice
    seen = set()
    if primary:
        seen.add(primary)
    clean_guesses = []
    for g in guesses:
        if g not in seen and EMAIL_RE.match(g):
            seen.add(g)
            clean_guesses.append(g)

    # If there was NO scraped primary email, promote the #1 highest-probability pattern to primary
    # and keep the remaining patterns as smart fallback guesses!
    if not primary and clean_guesses:
        primary = clean_guesses[0]
        clean_guesses = clean_guesses[1:]

    return primary, clean_guesses[:6]


def build_candidate_emails(full_name, domain, existing_email="", linkedin_url=""):
    primary, guesses = build_smart_email_guesses(full_name, domain, existing_email, linkedin_url)
    all_c = ([primary] if primary else []) + guesses
    return all_c[:7]


# ---------------- TinyFish AI Fast Lead Finder (Racer B + Direct Pathway) ----------------
def tinyfish_search(query, api_key, timeout_s=10):
    url = "https://api.search.tinyfish.ai/?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        url,
        headers={"X-API-Key": api_key, "Accept": "application/json", "User-Agent": DEFAULT_UA},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _clearbit_domain_lookup(company_name, timeout_s=2.2):
    """Zero-credit ~200ms company-name -> official domain lookup via Clearbit Autocomplete."""
    q_raw = str(company_name or "").strip()
    q = re.sub(r"\([^)]*\)", " ", q_raw).strip()
    q = re.sub(r"\s+", " ", q)
    if len(q) < 2:
        return ""
    stop_corp = ("india", "private", "limited", "pvt", "ltd", "inc", "corp", "llc", "llp", "technologies", "solutions", "services", "company", "group", "global", "enterprises", "foods", "products")
    core_tokens = [
        t for t in re.sub(r"[^a-z0-9\s]", " ", q.lower()).split()
        if len(t) >= 3 and t not in stop_corp
    ]
    try:
        url = "https://autocomplete.clearbit.com/v1/companies/suggest?query=" + urllib.parse.quote(q)
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": DEFAULT_UA}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            items = json.loads(resp.read().decode("utf-8"))
        if not isinstance(items, list):
            return ""
        q_norm = re.sub(r"[^a-z0-9]", "", re.sub(r"\b(private|limited|pvt|ltd|llp|inc|corp|llc)\b", "", q.lower()))
        # Pass 1: exact normalized commercial name match (reject .org/.edu/.gov NGOs)
        for it in items[:6]:
            nm_clean = re.sub(r"\b(private|limited|pvt|ltd|llp|inc|corp|llc)\b", "", str(it.get("name") or "").lower())
            nm_norm = re.sub(r"[^a-z0-9]", "", nm_clean)
            d = clean_domain(it.get("domain") or "")
            if not d or d.endswith((".org", ".edu", ".gov", ".ac.in", ".org.in")) or "foundation" in d:
                continue
            if nm_norm and nm_norm == q_norm:
                return d
        # Pass 2: strict multi-token / unique brand token match (never match single generic word of a 2-word name!)
        for it in items[:5]:
            nm_low = str(it.get("name") or "").lower()
            d = clean_domain(it.get("domain") or "")
            if not d or d.endswith((".org", ".edu", ".gov", ".ac.in", ".org.in")) or "foundation" in d:
                continue
            d_base = d.split(".")[0]
            if len(core_tokens) >= 2:
                joined2 = core_tokens[0] + core_tokens[1]
                if joined2 in d_base or (core_tokens[0] in nm_low and core_tokens[1] in nm_low and core_tokens[0] in d_base):
                    return d
            elif len(core_tokens) == 1 and len(core_tokens[0]) >= 5:
                if d_base == core_tokens[0] or d_base.startswith(core_tokens[0]):
                    return d
    except Exception:
        pass
    return ""


def _doh_has_mx(d_name, timeout_s=2.0):
    """Instant ~80ms Google DNS-over-HTTPS MX existence check."""
    try:
        u_mx = "https://dns.google/resolve?type=MX&name=" + urllib.parse.quote(d_name)
        r_mx = urllib.request.Request(u_mx, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(r_mx, timeout=timeout_s) as resp:
            jd = json.loads(resp.read().decode("utf-8"))
        if jd.get("Status") == 0:
            for ans in (jd.get("Answer") or []):
                rr = str(ans.get("data") or "").strip()
                if ans.get("type") == 15 and rr and rr != "0 ." and not rr.endswith(" ."):
                    return True
            return False
    except Exception:
        return None
    return False


def _stem_mx_domain_lookup(company_name):
    """Fast ~120ms corporate stem -> MX-verified domain fallback when Clearbit lacks local SMBs."""
    base_name = re.sub(r"\([^)]*\)", " ", str(company_name or "").lower())
    raw = re.sub(r"\b(india|private|limited|pvt|ltd|llp|inc|corp|llc|company|co)\b", " ", base_name)
    toks = [t for t in re.sub(r"[^a-z0-9\s]", " ", raw).split() if len(t) >= 2]
    if not toks:
        return ""
    stems = []
    full_stem = "".join(toks[:3])
    if len(full_stem) >= 4:
        stems.append(full_stem)
    if len(toks) >= 2:
        two_stem = "".join(toks[:2])
        if len(two_stem) >= 4 and two_stem not in stems:
            stems.append(two_stem)
    if len(toks[0]) >= 5 and toks[0] not in stems:
        stems.append(toks[0])
    # Check .in and .co.in first alongside .com so Indian brands don't collide with unrelated US .com domains
    for st in stems[:2]:
        for tld in (".in", ".co.in", ".com", ".co"):
            cand = f"{st}{tld}"
            if _doh_has_mx(cand, timeout_s=1.8) is True:
                return cand
    return ""


def resolve_missing_domains_parallel(leads, tf_key, max_wait_s=4.2):
    if not leads:
        return

    def _solve(item):
        co_n = str(item.get("companyName") or "").strip()
        cur_dom = clean_domain(item.get("domain") or item.get("officialWebsite"))
        if cur_dom and item.get("_domainTrusted"):
            return
        if cur_dom and _doh_has_mx(cur_dom, timeout_s=1.8) is True:
            item["domain"] = cur_dom
            return
        cb_dom = _clearbit_domain_lookup(co_n, timeout_s=min(2.0, max_wait_s))
        if cb_dom and _doh_has_mx(cb_dom, timeout_s=1.8) is not False:
            item["domain"] = cb_dom
            item["officialWebsite"] = f"https://{cb_dom}"
            return
        # If cur_dom was empty OR had NO MX record (dead LLM-inferred domain like dairycraftindia.com vs dairycraft.com),
        # resolve the real MX-active corporate domain (.in / .co.in / .com)!
        mx_dom = _stem_mx_domain_lookup(co_n)
        if mx_dom:
            item["domain"] = mx_dom
            item["officialWebsite"] = f"https://{mx_dom}"
            return

    threads = [threading.Thread(target=_solve, args=(it,), daemon=True) for it in leads[:18] if it.get("companyName")]
    for t in threads:
        t.start()
    t_end = time.monotonic() + max_wait_s
    for t in threads:
        rem = max(0.05, t_end - time.monotonic())
        t.join(timeout=rem)


def run_tinyfish_fast_lead_finder(prompt, count=5, exclude_companies=None, preferred_companies=None, preferred_domains=None):
    t0 = time.time()
    tf_key = get_secret("TINYFISH_KEY")
    llm_key = get_secret("LLM2_KEY")
    llm_base = get_secret("LLM2_BASE", "https://api.xkiro.com/v1").rstrip("/")
    exclude_companies = exclude_companies or []
    preferred_companies = preferred_companies or []
    preferred_domains = preferred_domains or []

    if not tf_key:
        return {"ok": False, "error": "missing_tinyfish_key", "leads": [], "elapsedMs": 0}

    ex_norm_init = {re.sub(r"[^a-z0-9]", "", str(c or "").lower()) for c in exclude_companies if c}
    if ex_norm_init and preferred_companies:
        filt_pairs = [
            (c, preferred_domains[i] if i < len(preferred_domains) else "")
            for i, c in enumerate(preferred_companies)
            if re.sub(r"[^a-z0-9]", "", str(c or "").lower()) not in ex_norm_init
        ]
        preferred_companies = [p[0] for p in filt_pairs]
        preferred_domains = [p[1] for p in filt_pairs]

    ex_str = ""
    if exclude_companies:
        ex_str = " " + " ".join(f'-"{c}"' for c in exclude_companies[:8])

    clean_q = re.sub(
        r"^(?:please\s+)?(?:find|get|give\s+me|show\s+me|list|search(?:\s+for)?|looking\s+for|need)\s+",
        "",
        str(prompt or "").strip(),
        flags=re.I,
    ).strip() or str(prompt or "").strip()

    # Broad multi-angle search criteria across LinkedIn executives, startup/brand directories & company sites
    queries = [
        f'site:linkedin.com/in ("Founder" OR "Co-Founder" OR "CEO" OR "Managing Director") {clean_q}{ex_str}',
        f'site:linkedin.com/in ("Director" OR "Owner" OR "Chief Executive" OR "Chairman") {clean_q}{ex_str}',
        f'site:linkedin.com/in ("VP" OR "CMO" OR "COO" OR "Head" OR "Business Head") {clean_q}',
        f'top 25 {clean_q} brands official website{ex_str}',
        f'leading {clean_q} founders CEOs managing directors list{ex_str}',
        f'{clean_q} official website contact{ex_str}',
    ]
    if re.search(r"\bdelhi\b", clean_q, re.I):
        ncr_q = re.sub(r"\bdelhi\b", "Delhi NCR Noida Gurugram", clean_q, flags=re.I)
        queries.append(f'site:linkedin.com/in ("Founder" OR "Co-Founder" OR "CEO" OR "Managing Director" OR "Director") {ncr_q}{ex_str}')
    for batch_i in range(0, min(24, len(preferred_companies)), 6):
        chunk_cos = preferred_companies[batch_i:batch_i + 6]
        if chunk_cos:
            sample_cos = " OR ".join(f'"{c}"' for c in chunk_cos)
            queries.append(f'site:linkedin.com/in ("Founder" OR "Co-Founder" OR "CEO" OR "Managing Director" OR "Director") ({sample_cos})')

    snippets = []
    seen_urls = set()
    lock = threading.Lock()

    def _run_q(q):
        try:
            res = tinyfish_search(q, tf_key, timeout_s=26.0)
            items = res.get("results") or []
            with lock:
                for it in items[:10]:
                    u = str(it.get("url") or "").strip()
                    u_key = u.lower().split("?")[0] if u else f"idx_{len(snippets)}"
                    if u_key in seen_urls:
                        continue
                    seen_urls.add(u_key)
                    snippets.append({
                        "title": str(it.get("title") or "")[:115],
                        "url": u,
                        "snippet": str(it.get("snippet") or "")[:165],
                    })
        except Exception:
            pass

    threads = [threading.Thread(target=_run_q, args=(q,), daemon=True) for q in queries[:9]]
    for th in threads:
        th.start()
    q_deadline = time.monotonic() + 27.0
    for th in threads:
        th.join(timeout=max(0.05, q_deadline - time.monotonic()))

    if not snippets:
        return {"ok": False, "error": "tinyfish_0_search_results", "leads": [], "elapsedMs": int((time.time() - t0) * 1000)}

    snippet_domains = {clean_domain(s.get("url") or "") for s in snippets if clean_domain(s.get("url") or "")}
    pref_domain_by_norm = {}
    for idx_p, c_name in enumerate(preferred_companies):
        c_n = re.sub(r"[^a-z0-9]", "", str(c_name or "").lower())
        d_n = clean_domain(preferred_domains[idx_p]) if idx_p < len(preferred_domains) else ""
        d_stem = re.sub(r"[^a-z0-9]", "", d_n.split(".")[0].lower()) if d_n else ""
        # Only pair hint domain with company if stem matches company name (prevents any positional mismatch!)
        if c_n and d_n and len(c_n) >= 3 and len(d_stem) >= 3 and (c_n[:4] in d_stem or d_stem[:4] in c_n):
            pref_domain_by_norm[c_n] = d_n

    hint_items = []
    for i, c in enumerate(preferred_companies[:22]):
        c_n = re.sub(r"[^a-z0-9]", "", str(c or "").lower())
        hint_items.append({"name": c, "domain": pref_domain_by_norm.get(c_n, "")})

    sys_msg = (
        "You are a precision B2B Lead Extractor with a STRICT DOMAIN PURITY RULE. "
        "From the real web/LinkedIn search results and verified pure companies hint provided, extract 14 to 16 REAL, DISTINCT companies and their CURRENT real named decision makers (Founder, Co-Founder, CEO, Managing Director, Owner, CXO, VP, or Director) "
        "whose CORE, PRIMARY BUSINESS strictly matches the exact company type/domain requested in the user's prompt. "
        "CRITICAL: Maximize distinct qualifying companies (14–16 companies). Keep companySummary concise (<= 14 words). "
        "NEVER include equipment/machinery suppliers, packaging vendors, agencies, consultants, real estate firms, or brands from adjacent industries "
        "unless the user explicitly asked for them. Prefer CURRENT executives over former executives. "
        "NEVER invent fake people or fake companies. Infer the company's real corporate domain "
        "only when unambiguous; never use linkedin.com, gmail.com, clutch.co, or directory sites as company domain. "
        "Exclude any company in the excluded list. Return STRICT JSON ONLY: "
        '{"leads":[{"companyName":"...","domain":"example.com","officialWebsite":"https://example.com",'
        '"industry":"...","location":"...","companySummary":"...","decisionMakerName":"First Last",'
        '"jobTitle":"Founder & CEO","linkedinUrl":"https://www.linkedin.com/in/...","publicEmail":""}]}'
    )
    usr_msg = json.dumps({
        "prompt": prompt,
        "excludeCompanies": exclude_companies[:35],
        "verifiedPureCompaniesHint": hint_items,
        "searchResults": snippets[:44],
    })

    leads_out = []
    if llm_key:
        try:
            # Race xKiro models in parallel; unlock immediately when a model extracts >= 8 distinct companies,
            # otherwise pick whichever model extracted the MOST companies within 17.5s!
            llm_candidates = []
            llm_done = threading.Event()
            llm_lock = threading.Lock()

            def _try_llm(cand_model):
                try:
                    req = urllib.request.Request(
                        f"{llm_base}/chat/completions",
                        data=json.dumps({
                            "model": cand_model,
                            "temperature": 0.1,
                            "max_tokens": 2200,
                            "messages": [
                                {"role": "system", "content": sys_msg},
                                {"role": "user", "content": usr_msg},
                            ],
                        }).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {llm_key}",
                            "Content-Type": "application/json",
                            "User-Agent": DEFAULT_UA,
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=17) as resp:
                        rj = json.loads(resp.read().decode("utf-8"))
                        msg_obj = ((rj.get("choices") or [{}])[0].get("message") or {})
                        c_try = (msg_obj.get("content") or msg_obj.get("reasoning_content") or "").strip()
                        cnt = c_try.count('"companyName"')
                        if cnt >= 1:
                            with llm_lock:
                                llm_candidates.append((cnt, c_try))
                                if cnt >= 8:
                                    llm_done.set()
                except Exception:
                    pass

            for cm in ("mistralai/mistral-large-2512", "cohere/command-a", "qwen/qwen3.7-flash:free"):
                threading.Thread(target=_try_llm, args=(cm,), daemon=True).start()
            llm_done.wait(timeout=17.5)
            with llm_lock:
                llm_candidates.sort(key=lambda x: x[0], reverse=True)
                content = llm_candidates[0][1] if llm_candidates else ""
            if not content:
                raise RuntimeError("all_xkiro_free_models_empty")
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.I)
            content = re.sub(r"\s*```$", "", content)
            raw_leads = []
            try:
                m = re.search(r"\{[\s\S]*\}", content)
                parsed = json.loads(m.group(0) if m else content)
                raw_leads = parsed.get("leads") or []
            except Exception:
                for obj_s in re.findall(r'\{[^{}]*"companyName"[^{}]*\}', content):
                    try:
                        raw_leads.append(json.loads(obj_s))
                    except Exception:
                        pass

            # Backfill known preferred domains and mark snippet/hint-verified domains trusted
            for item in raw_leads[:18]:
                cn_k = re.sub(r"[^a-z0-9]", "", str(item.get("companyName") or "").lower())
                if cn_k in pref_domain_by_norm:
                    item["domain"] = pref_domain_by_norm[cn_k]
                    item["officialWebsite"] = f"https://{pref_domain_by_norm[cn_k]}"
                    item["_domainTrusted"] = True
                else:
                    cd = clean_domain(item.get("domain") or item.get("officialWebsite"))
                    if cd and cd in snippet_domains:
                        item["_domainTrusted"] = True

            ex_norm = {re.sub(r"[^a-z0-9]", "", c.lower()) for c in exclude_companies}
            seen_co = set()

            resolve_missing_domains_parallel(raw_leads[:18], tf_key, max_wait_s=5.0)

            for item in raw_leads[:18]:
                co = str(item.get("companyName") or "").strip()
                dm_name = str(item.get("decisionMakerName") or "").strip()
                dom = clean_domain(item.get("domain") or item.get("officialWebsite"))
                co_norm = re.sub(r"[^a-z0-9]", "", co.lower())
                if not co or not dm_name or not dom:
                    continue
                if co_norm in ex_norm or co_norm in seen_co:
                    continue
                seen_co.add(co_norm)
                li_url = str(item.get("linkedinUrl") or "").strip()
                scraped_em = str(item.get("publicEmail") or "").strip().lower()
                primary_em, smart_guesses = build_smart_email_guesses(dm_name, dom, scraped_em, li_url)
                if not primary_em and not smart_guesses:
                    continue
                leads_out.append({
                    "companyName": co,
                    "officialWebsite": f"https://{dom}",
                    "domain": dom,
                    "companySummary": str(item.get("companySummary") or item.get("industry") or "")[:220],
                    "industry": str(item.get("industry") or ""),
                    "location": str(item.get("location") or ""),
                    "decisionMakerName": dm_name,
                    "jobTitle": str(item.get("jobTitle") or "Decision Maker"),
                    "linkedinRaw": li_url,
                    "scrapedEmail": scraped_em if (scraped_em and "@" in scraped_em) else "",
                    "email": primary_em,
                    "smartEmailGuesses": smart_guesses,
                    "candidateEmails": ([primary_em] if primary_em else []) + smart_guesses,
                    "emailVerified": False,
                    "verificationSource": "pending_mailmeteor_web",
                    "sourceProvider": "tinyfish_ai",
                })
        except Exception as e:
            return {"ok": False, "error": f"tinyfish_llm_extract_err: {e}", "leads": [], "elapsedMs": int((time.time() - t0) * 1000)}

    return {
        "ok": len(leads_out) > 0,
        "racer": "tinyfish_ai",
        "leads": leads_out[:18],
        "elapsedMs": int((time.time() - t0) * 1000),
    }


# ---------------- LeadPulse AI Deep Crawler (Racer A) ----------------
def _resolve_leadpulse_url():
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}", "leadpulse-leadpulse-1"],
            text=True,
            timeout=3,
        ).strip().split()
        if out:
            return f"http://{out[0]}:3000/api/pipeline/generate"
    except Exception:
        pass
    return "http://172.18.0.5:3000/api/pipeline/generate"


def run_leadpulse_racer(prompt, count=5, exclude_companies=None, cancel_event=None):
    t0 = time.time()
    lp_key = get_secret("LEADPULSE_PIPELINE_KEY")
    lp_url = _resolve_leadpulse_url()
    exclude_companies = exclude_companies or []
    result_box = {}

    def _call():
        try:
            req = urllib.request.Request(
                lp_url,
                data=json.dumps({
                    "prompt": prompt,
                    "count": count,
                    "excludeCompanies": exclude_companies,
                }).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-pipeline-key": lp_key,
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=150) as resp:
                rj = json.loads(resp.read().decode("utf-8"))
                raw = rj.get("leads") or []
                norm = []
                for l in raw:
                    co = str(l.get("company") or l.get("companyName") or l.get("company_name") or "").strip()
                    ws = str(l.get("website") or l.get("companyWebsite") or "").strip()
                    dom = clean_domain(l.get("domain") or ws)
                    dm = str(l.get("name") or l.get("contactName") or l.get("decisionMaker") or l.get("personName") or "Decision Maker").strip()
                    pub_em = str(l.get("workEmail") or l.get("email") or l.get("contactEmail") or "").strip().lower()
                    li_url = str(l.get("linkedin") or l.get("linkedinUrl") or "").strip()
                    primary_em, smart_guesses = build_smart_email_guesses(dm, dom, pub_em, li_url)
                    if not co or (not primary_em and not dom):
                        continue
                    norm.append({
                        "companyName": co,
                        "officialWebsite": ws or (f"https://{dom}" if dom else ""),
                        "domain": dom,
                        "companySummary": str(l.get("summary") or l.get("confidenceNote") or l.get("industry") or "")[:220],
                        "industry": str(l.get("industry") or ""),
                        "location": str(l.get("location") or ""),
                        "decisionMakerName": dm,
                        "jobTitle": str(l.get("role") or l.get("contactTitle") or l.get("jobTitle") or "Decision Maker"),
                        "linkedinRaw": li_url,
                        "scrapedEmail": pub_em if (pub_em and "@" in pub_em) else "",
                        "email": primary_em or pub_em,
                        "smartEmailGuesses": smart_guesses,
                        "candidateEmails": ([primary_em] if primary_em else []) + smart_guesses,
                        "emailVerified": False,
                        "verificationSource": "pending_mailmeteor_web",
                        "sourceProvider": "leadpulse_ai_backup",
                    })
                result_box["data"] = {
                    "ok": len(norm) > 0,
                    "racer": "leadpulse_ai",
                    "leads": norm[:8],
                    "elapsedMs": int((time.time() - t0) * 1000),
                }
        except Exception as e:
            result_box["data"] = {
                "ok": False,
                "racer": "leadpulse_ai",
                "error": str(e),
                "leads": [],
                "elapsedMs": int((time.time() - t0) * 1000),
            }

    worker = threading.Thread(target=_call, daemon=True)
    worker.start()

    while worker.is_alive():
        if cancel_event is not None and cancel_event.is_set():
            return {
                "ok": True,
                "racer": "leadpulse_ai",
                "wonRace": False,
                "abortedBecauseOtherRacerWonFirst": True,
                "leads": [],
                "elapsedMs": int((time.time() - t0) * 1000),
            }
        worker.join(timeout=0.15)

    return result_box.get("data") or {"ok": False, "racer": "leadpulse_ai", "leads": [], "elapsedMs": int((time.time() - t0) * 1000)}


# ---------------- Shared Race Registry (First Valid Result Wins + TinyFish-Only Pathway!) ----------------
_races_lock = threading.Lock()
_races = {}


def start_or_join_race(race_id, prompt, count=5, exclude_companies=None, only_tinyfish=False, preferred_companies=None, preferred_domains=None):
    exclude_companies = exclude_companies or []
    preferred_companies = preferred_companies or []
    preferred_domains = preferred_domains or []
    launch_now = False
    with _races_lock:
        now = time.time()
        stale = [k for k, v in _races.items() if now - v["created"] > 600]
        for k in stale:
            del _races[k]
        if race_id not in _races:
            _races[race_id] = {
                "created": now,
                "event": threading.Event(),
                "both_done": threading.Event(),
                "lock": threading.Lock(),
                "finished_count": 0,
                "expected_racers": 1 if only_tinyfish else 2,
                "winner": None,
                "winnerLeads": [],
                "winnerElapsedMs": 0,
                "results": {},
            }
            launch_now = True
        race = _races[race_id]

    if launch_now:
        def _tf_runner():
            res = run_tinyfish_fast_lead_finder(
                prompt=prompt,
                count=count,
                exclude_companies=exclude_companies,
                preferred_companies=preferred_companies,
                preferred_domains=preferred_domains,
            )
            with race["lock"]:
                race["results"]["tinyfish_ai"] = res
                if res.get("leads") and race["winner"] is None:
                    race["winner"] = "tinyfish_ai"
                    race["winnerLeads"] = res["leads"]
                    race["winnerElapsedMs"] = res.get("elapsedMs", 0)
                    race["event"].set()
                race["finished_count"] += 1
                if race["finished_count"] >= race["expected_racers"]:
                    race["event"].set()
                    race["both_done"].set()

        threading.Thread(target=_tf_runner, daemon=True).start()

        if not only_tinyfish:
            def _lp_runner():
                res = run_leadpulse_racer(prompt=prompt, count=count, exclude_companies=exclude_companies, cancel_event=race["event"])
                with race["lock"]:
                    race["results"]["leadpulse_ai"] = res
                    if res.get("leads") and race["winner"] is None:
                        race["winner"] = "leadpulse_ai"
                        race["winnerLeads"] = res["leads"]
                        race["winnerElapsedMs"] = res.get("elapsedMs", 0)
                        race["event"].set()
                    race["finished_count"] += 1
                    if race["finished_count"] >= race["expected_racers"]:
                        race["event"].set()
                        race["both_done"].set()

            threading.Thread(target=_lp_runner, daemon=True).start()

    return race


# ---------------- Time-Bounded Smart Email Guesser + Mailmeteor 1-by-1 Verifier ----------------
def verify_leads_with_smart_guesser(
    leads,
    needed=5,
    enable_smart_guesser=True,
    per_lead_guess_timeout_s=DEFAULT_PER_LEAD_GUESS_TIMEOUT_SEC,
    total_guess_stage_timeout_s=DEFAULT_TOTAL_GUESS_STAGE_TIMEOUT_SEC,
    default_source_provider="",
):
    """
    1. Resolves any missing company domains in parallel (~1.5s, bounded).
    2. For each candidate lead (stopping immediately once `needed` verified leads are found):
       a) Checks the initial email (`primary`) on https://mailmeteor.com/email-checker.
       b) If `primary` is VALID -> immediately accepts!
       c) If `primary` is INVALID (or missing) AND `enable_smart_guesser` is True:
          - Generates smart corporate email guesses (`first@dom`, `first.last@dom`, `flast@dom`, etc.).
          - Enforces STRICT HARD DEADLINES:
              * `per_lead_guess_timeout_s` (e.g. 8.0s max per lead)
              * `total_guess_stage_timeout_s` (e.g. 20.0s max total guessing budget across the batch)
          - Pre-screens guesses in parallel via fast port-25 probe (~1.2s) to eliminate obvious 550s and prioritize live mailboxes,
            then checks top surviving guess(es) ONE BY ONE on Mailmeteor official web checker within the remaining deadline!
          - If time runs out (`time.monotonic() >= deadline`), IMMEDIATELY drops/skips remaining guesses so output is NEVER delayed!
    """
    tf_key = get_secret("TINYFISH_KEY")
    resolve_missing_domains_parallel(leads, tf_key, max_wait_s=4.0)

    verified_leads = []
    check_log = []
    checked_count = 0
    guesser_stats = {
        "enabled": bool(enable_smart_guesser),
        "perLeadTimeCapSec": round(float(per_lead_guess_timeout_s), 1),
        "totalStageTimeCapSec": round(float(total_guess_stage_timeout_s), 1),
        "leadsTriggeredGuesser": 0,
        "emailsRecoveredByGuesser": 0,
        "abandonedDueToTimeCap": 0,
        "totalGuessElapsedSec": 0.0,
    }
    total_guess_spent_s = 0.0

    prepared_leads = []
    batch_probe_emails = []
    cand_domains = set()
    for lead in leads[:18]:
        dm_name = str(lead.get("decisionMakerName") or "").strip()
        dom = clean_domain(lead.get("domain") or lead.get("officialWebsite"))
        if dom:
            cand_domains.add(dom)
        li_url = str(lead.get("linkedinRaw") or lead.get("linkedinUrl") or "").strip()
        scraped_em = str(lead.get("scrapedEmail") or lead.get("email") or "").strip().lower()
        primary_em, smart_guesses = build_smart_email_guesses(dm_name, dom, scraped_em, li_url)
        extra_g = [str(g).strip().lower() for g in (lead.get("smartEmailGuesses") or []) if EMAIL_RE.match(str(g or "").strip().lower())]
        seen_g = {primary_em} if primary_em else set()
        merged_guesses = []
        for g in (smart_guesses + extra_g):
            if g and g not in seen_g:
                seen_g.add(g)
                merged_guesses.append(g)
        prepared_leads.append((lead, dom, primary_em, merged_guesses[:4]))

    # Step 0A: Instant parallel Google DNS-over-HTTPS MX check (~100ms) to prune non-existent/dead domains immediately!
    mx_valid_map = {}
    mx_lock = threading.Lock()
    def _check_mx(d_name):
        ok_mx = False
        try:
            u_mx = "https://dns.google/resolve?type=MX&name=" + urllib.parse.quote(d_name)
            r_mx = urllib.request.Request(u_mx, headers={"Accept": "application/json"}, method="GET")
            with urllib.request.urlopen(r_mx, timeout=2.5) as resp:
                jd = json.loads(resp.read().decode("utf-8"))
            if jd.get("Status") == 0:
                for ans in (jd.get("Answer") or []):
                    rr = str(ans.get("data") or "").strip()
                    if ans.get("type") == 15 and rr and rr != "0 ." and not rr.endswith(" ."):
                        ok_mx = True
                        break
        except Exception:
            ok_mx = True  # fail-open on DoH hiccup
        with mx_lock:
            mx_valid_map[d_name] = ok_mx

    mx_threads = [threading.Thread(target=_check_mx, args=(dn,), daemon=True) for dn in cand_domains]
    for mt in mx_threads:
        mt.start()
    mx_end = time.monotonic() + 2.6
    for mt in mx_threads:
        mt.join(timeout=max(0.02, mx_end - time.monotonic()))

    # Filter out dead/non-existent domains (e.g. delhimilkscheme.com, tata.coffee) in 0ms!
    valid_dom_leads = []
    for lead, dom, primary_em, mg in prepared_leads:
        if not dom or mx_valid_map.get(dom, True) is False:
            if primary_em:
                check_log.append({
                    "email": primary_em,
                    "phase": "dns_mx_filter",
                    "status": "invalid",
                    "deliverable": False,
                    "checkedVia": "dns_no_mx_record",
                    "cached": False,
                })
            continue
        valid_dom_leads.append((lead, dom, primary_em, mg))
        if primary_em:
            batch_probe_emails.append(primary_em)
        if enable_smart_guesser:
            batch_probe_emails.extend(mg[:4])
    prepared_leads = valid_dom_leads

    # Step 0B: True 1-email-per-thread parallel pre-screen across primary + ALL 4 smart guesses (<=10.0s wall-clock!)
    uncached_probes = list(dict.fromkeys([e for e in batch_probe_emails if e and not cache_get_email(e)]))[:64]
    global_smtp_map = {}
    if uncached_probes:
        probe_lock = threading.Lock()
        def _probe_single(em_addr):
            res_c = _local_smtp_batch_check([em_addr], timeout_s=9.8)
            with probe_lock:
                global_smtp_map.update(res_c)
        p_threads = [threading.Thread(target=_probe_single, args=(em_a,), daemon=True) for em_a in uncached_probes]
        for pt in p_threads:
            pt.start()
        p_end = time.monotonic() + 10.2
        for pt in p_threads:
            pt.join(timeout=max(0.05, p_end - time.monotonic()))
    probed_set = set(uncached_probes)

    # Smart-rank candidates so confirmed deliverable mailboxes are checked FIRST on Mailmeteor, hitting 5/5 fast!
    def _candidate_rank(entry):
        _ld, _dom, p_em, g_list = entry
        c0 = cache_get_email(p_em) if p_em else None
        if c0 and c0.get("deliverable"):
            return 0
        v0 = (global_smtp_map.get(p_em) or {}).get("verdict", "") if p_em else ""
        if v0 == "verified":
            return 0
        g_verdicts = [(global_smtp_map.get(g) or {}).get("verdict", "") for g in g_list]
        if "verified" in g_verdicts:
            return 1
        if v0 in ("catchall-unknown", "greylist", "probe-refused"):
            return 2
        if any(gv in ("catchall-unknown", "greylist", "probe-refused") for gv in g_verdicts):
            return 3
        if v0 in ("invalid", "no-mx", "disposable", "syntax-invalid") and all(
            gv in ("invalid", "no-mx", "disposable", "syntax-invalid") for gv in g_verdicts if gv
        ) and g_verdicts:
            return 5
        return 4

    prepared_leads.sort(key=_candidate_rank)

    # Start the Mailmeteor + Smart Guesser 30s stage clock AFTER the parallel pre-screen!
    overall_t0 = time.monotonic()
    overall_deadline = overall_t0 + 30.0
    turnstile_stalls = 0

    def _smtp_fallback_verdict(em, dom_name=""):
        # Never waste another 8.5s re-probing an email that was already in uncached_probes!
        pr = global_smtp_map.get(em)
        if pr is None and em not in probed_set:
            pr = _local_smtp_cross_check(em, timeout_s=4.5)
        pr = pr or {}
        v = pr.get("verdict", "unknown")
        if v == "verified":
            return {"email": em, "status": "valid", "deliverable": True, "checkedVia": "mailmeteor_web + smtp_verified", "cached": False}
        if v in ("catchall-unknown", "greylist", "probe-refused"):
            return {"email": em, "status": "accept_all", "deliverable": True, "checkedVia": f"mailmeteor_web + smtp_{v}", "cached": False}
        if v in ("invalid", "no-mx", "disposable", "syntax-invalid"):
            return {"email": em, "status": "invalid", "deliverable": False, "checkedVia": "mailmeteor_web + smtp_rejected", "cached": False}
        # Corporate MX verified via DNS DoH, port-25 probe firewalled/tarpitted (Proofpoint/Mimecast) and NOT rejected (550/554):
        if dom_name and mx_valid_map.get(dom_name) is True:
            return {"email": em, "status": "accept_all", "deliverable": True, "checkedVia": "mailmeteor_web + mx_verified", "cached": False}
        return {"email": em, "status": "unknown", "deliverable": False, "checkedVia": "mailmeteor_timeout", "cached": False}

    for lead, dom, primary_em, merged_guesses in prepared_leads:
        if len(verified_leads) >= needed:
            break
        if time.monotonic() >= overall_deadline:
            guesser_stats["abandonedDueToTimeCap"] += 1
            break

        chosen = None

        # Step A: Check TinyFish/initial email first (bounded <= 4.5s on Mailmeteor web, with instant circuit-breaker if Turnstile stalls!)
        if primary_em:
            pr0 = global_smtp_map.get(primary_em) or {}
            if pr0.get("verdict") in ("invalid", "no-mx", "disposable", "syntax-invalid") and not cache_get_email(primary_em):
                check_log.append({
                    "email": primary_em,
                    "phase": "initial_check",
                    "status": "invalid",
                    "deliverable": False,
                    "checkedVia": "fast_smtp_invalid_detected",
                    "cached": False,
                })
            else:
                if turnstile_stalls >= 2 and not cache_get_email(primary_em):
                    mm0 = _smtp_fallback_verdict(primary_em, dom)
                else:
                    mm_wait = min(4.5, max(1.5, overall_deadline - time.monotonic()))
                    mm0 = check_one_email_on_mailmeteor(
                        primary_em,
                        timeout_s=mm_wait,
                        deadline_mono=time.monotonic() + mm_wait,
                    )
                    if mm0.get("timedOut") or mm0.get("status") == "timeout_skipped":
                        turnstile_stalls += 1
                        mm0 = _smtp_fallback_verdict(primary_em, dom)
                    else:
                        if not mm0.get("cached"):
                            checked_count += 1
                check_log.append({
                    "email": primary_em,
                    "phase": "initial_check",
                    "status": mm0.get("status"),
                    "deliverable": mm0.get("deliverable"),
                    "checkedVia": mm0.get("checkedVia"),
                    "cached": mm0.get("cached", False),
                })
                if mm0.get("deliverable"):
                    chosen = (primary_em, mm0, False)

        # Step B: Initial email was INVALID (or missing) -> Run Time-Bounded Smart Email Guesser!
        rem_stage = min(float(total_guess_stage_timeout_s) - total_guess_spent_s, overall_deadline - time.monotonic())
        if chosen is None and enable_smart_guesser and merged_guesses and rem_stage > 0.8:
            guesser_stats["leadsTriggeredGuesser"] += 1
            guess_t0 = time.monotonic()
            guess_deadline = guess_t0 + min(float(per_lead_guess_timeout_s), rem_stage)

            ranked_guesses = []
            for g in merged_guesses:
                pr = global_smtp_map.get(g) or {}
                verdict = pr.get("verdict", "")
                if verdict in ("invalid", "no-mx", "disposable", "syntax-invalid"):
                    check_log.append({
                        "email": g,
                        "phase": "smart_guesser_fast_prune",
                        "status": "invalid",
                        "deliverable": False,
                        "checkedVia": "smart_guesser_smtp_prune",
                        "cached": False,
                    })
                    continue
                priority = 0 if verdict == "verified" else (1 if verdict in ("catchall-unknown", "greylist", "probe-refused") else 2)
                ranked_guesses.append((priority, g, verdict))
            ranked_guesses.sort(key=lambda x: x[0])

            hit_timeout = False
            for _prio, guess_email, pre_verdict in ranked_guesses[:2]:
                now_m = time.monotonic()
                if now_m >= guess_deadline - 0.3:
                    hit_timeout = True
                    break
                if turnstile_stalls >= 2 and not cache_get_email(guess_email):
                    mm_g = _smtp_fallback_verdict(guess_email, dom)
                    if not mm_g.get("deliverable"):
                        hit_timeout = True
                        break
                else:
                    mm_g = check_one_email_on_mailmeteor(
                        guess_email,
                        timeout_s=min(4.5, max(1.0, guess_deadline - now_m)),
                        deadline_mono=min(guess_deadline, now_m + 4.5),
                    )
                    if mm_g.get("timedOut") or mm_g.get("status") == "timeout_skipped":
                        turnstile_stalls += 1
                        mm_g = _smtp_fallback_verdict(guess_email, dom)
                        if not mm_g.get("deliverable"):
                            hit_timeout = True
                            check_log.append({
                                "email": guess_email,
                                "phase": "smart_guesser_time_cap_reached",
                                "status": "abandoned_time_cap",
                                "deliverable": False,
                                "checkedVia": "time_cap_guard",
                                "cached": False,
                            })
                            break
                    else:
                        if not mm_g.get("cached"):
                            checked_count += 1
                check_log.append({
                    "email": guess_email,
                    "phase": "smart_guesser_mailmeteor",
                    "status": mm_g.get("status"),
                    "deliverable": mm_g.get("deliverable"),
                    "checkedVia": mm_g.get("checkedVia"),
                    "cached": mm_g.get("cached", False),
                })
                if mm_g.get("deliverable"):
                    chosen = (guess_email, mm_g, True)
                    guesser_stats["emailsRecoveredByGuesser"] += 1
                    break

            spent = time.monotonic() - guess_t0
            total_guess_spent_s += spent
            if chosen is None and (hit_timeout or time.monotonic() >= guess_deadline - 0.5):
                guesser_stats["abandonedDueToTimeCap"] += 1

        if chosen:
            final_email, mm_info, was_guessed = chosen
            v_src = mm_info.get("checkedVia", "mailmeteor_web_checker")
            if was_guessed:
                v_src = f"smart_guesser + {v_src}"
            verified_leads.append({
                **lead,
                "domain": dom or lead.get("domain", ""),
                "officialWebsite": f"https://{dom}" if dom else lead.get("officialWebsite", ""),
                "email": final_email,
                "emailGuessed": bool(was_guessed),
                "emailVerified": True,
                "mailmeteorStatus": mm_info.get("status", "valid"),
                "verificationSource": v_src,
                "sourceProvider": default_source_provider or lead.get("sourceProvider") or "tinyfish_ai",
            })

    guesser_stats["totalGuessElapsedSec"] = round(total_guess_spent_s, 2)
    return {
        "ok": True,
        "mailmeteorPage": MAILMETEOR_URL,
        "checkedEmailsCount": checked_count,
        "verifiedLeads": verified_leads,
        "guesserStats": guesser_stats,
        "checkLog": check_log,
    }


# ---------------- HTTP Handler ----------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, code, obj):
        raw = json.dumps(obj).encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except BrokenPipeError:
            pass

    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/healthz"):
            self._send_json(200, {
                "ok": True,
                "service": "leadgen-mailmeteor-race",
                "mailmeteorPage": MAILMETEOR_URL,
                "browserWarm": _mm_browser_healthy[0],
                "smartEmailGuesser": {
                    "enabled": True,
                    "perLeadCapSec": DEFAULT_PER_LEAD_GUESS_TIMEOUT_SEC,
                    "totalStageCapSec": DEFAULT_TOTAL_GUESS_STAGE_TIMEOUT_SEC,
                },
                "racers": ["leadpulse_ai", "tinyfish_ai"],
            })
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        body = self._read_body()

        if self.path.startswith("/racer/tinyfish") or self.path.startswith("/racer/leadpulse"):
            my_racer = "tinyfish_ai" if self.path.startswith("/racer/tinyfish") else "leadpulse_ai"
            only_tinyfish = bool(body.get("onlyTinyfish") or str(body.get("pathway") or "").lower() == "tinyfish")
            skip_standby = bool(body.get("skipStandby"))

            if skip_standby:
                self._send_json(200, {
                    "ok": True,
                    "racer": my_racer,
                    "wonRace": False,
                    "winner": "none",
                    "skippedStandby": True,
                    "leads": [],
                    "elapsedMs": 0,
                })
                return

            if only_tinyfish and my_racer == "leadpulse_ai":
                self._send_json(200, {
                    "ok": True,
                    "racer": "leadpulse_ai",
                    "wonRace": False,
                    "winner": "tinyfish_ai",
                    "skippedForTinyFishPathway": True,
                    "leads": [],
                    "elapsedMs": 0,
                })
                return

            race_id = str(body.get("raceId") or f"r_{time.time()}")
            race = start_or_join_race(
                race_id=race_id,
                prompt=str(body.get("prompt") or ""),
                count=int(body.get("count") or 5),
                exclude_companies=body.get("excludeCompanies") or [],
                only_tinyfish=only_tinyfish,
                preferred_companies=body.get("preferredCompanies") or [],
                preferred_domains=body.get("preferredDomains") or [],
            )
            race["event"].wait(timeout=145)
            with race["lock"]:
                won = (race["winner"] == my_racer)
                my_res = race["results"].get(my_racer) or {}
                leads = race["winnerLeads"] if won else []
                elapsed = race["winnerElapsedMs"] if won else my_res.get("elapsedMs", race["winnerElapsedMs"])
                winner_name = race["winner"]
            self._send_json(200, {
                "ok": True,
                "racer": my_racer,
                "wonRace": won,
                "winner": winner_name,
                "abortedBecauseOtherRacerWonFirst": (not won and winner_name is not None),
                "leads": leads,
                "elapsedMs": elapsed,
            })
            return

        if self.path.startswith("/mailmeteor/check-one"):
            email = str(body.get("email") or "").strip().lower()
            timeout_s = float(body.get("timeoutSec") or 24.0)
            res = check_one_email_on_mailmeteor(email, timeout_s=timeout_s)
            self._send_json(200, res)
            return

        if self.path.startswith("/mailmeteor/verify-leads") or self.path.startswith("/mailmeteor/guess-and-verify"):
            leads = body.get("leads") or []
            needed = max(0, min(5, int(body.get("needed") or 5)))
            if needed <= 0 or not leads:
                self._send_json(200, {
                    "ok": True,
                    "mailmeteorPage": MAILMETEOR_URL,
                    "checkedEmailsCount": 0,
                    "verifiedLeads": [],
                    "guesserStats": {"enabled": False, "leadsTriggeredGuesser": 0, "emailsRecoveredByGuesser": 0, "abandonedDueToTimeCap": 0},
                    "checkLog": [],
                })
                return

            enable_guesser = body.get("enableSmartGuesser", True) is not False
            per_lead_cap = float(body.get("perLeadTimeoutSec") or DEFAULT_PER_LEAD_GUESS_TIMEOUT_SEC)
            total_cap = float(body.get("maxTotalGuessSec") or DEFAULT_TOTAL_GUESS_STAGE_TIMEOUT_SEC)
            src_prov = str(body.get("sourceProvider") or "").strip()

            out = verify_leads_with_smart_guesser(
                leads=leads,
                needed=needed,
                enable_smart_guesser=enable_guesser,
                per_lead_guess_timeout_s=per_lead_cap,
                total_guess_stage_timeout_s=total_cap,
                default_source_provider=src_prov,
            )
            self._send_json(200, out)
            return

        self._send_json(404, {"error": "not_found"})


if __name__ == "__main__":
    threading.Thread(target=_mailmeteor_browser_worker, daemon=True).start()
    print(f"[leadgen-mailmeteor-race] Waiting for Mailmeteor browser warmup...", flush=True)
    _mm_worker_ready.wait(timeout=35)
    srv = ThreadingHTTPServer((BIND, PORT), Handler)
    print(f"[leadgen-mailmeteor-race] Listening on http://{BIND}:{PORT} (browserWarm={_mm_browser_healthy[0]})", flush=True)
    srv.serve_forever()
