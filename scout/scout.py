#!/usr/bin/env python3
"""
Scout — finds and pre-qualifies web-app leads for Kyle's pipeline.

Shape:
  1. SEARCH   DuckDuckGo HTML for "<niche> in <area>" (+ extra queries)
  2. VISIT    every candidate site (real fetch, 10s timeout)
  3. QUALIFY  HTTPS, load time, mobile viewport, old-builder fingerprints,
              booking/contact form, findable email
  4. SCORE    bad-site signals add up; modern-site signals subtract
  5. WRITE    out/leads-YYYY-MM-DD.csv   → import straight into pipeline.html
              out/drafts-YYYY-MM-DD.md   → review queue: drafted first-touch emails

Nothing is ever sent. Human reviews drafts, human sends.

Usage:
  python3 scout.py --niche "holiday cottages" --area "Cornwall" --limit 10
  python3 scout.py                      # uses config.json defaults
"""
import argparse, csv, json, re, ssl, sys, time, urllib.parse, urllib.request
from datetime import date, timedelta
from email.utils import parseaddr
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
CTX = ssl.create_default_context()

# ---------------- source 1: OpenStreetMap (no bot wall, direct website URLs) ----------------
def _overpass(query, tries=3):
    """POST to Overpass with mirror fallback + backoff. Raises on final failure."""
    OSM_UA = {"User-Agent": "kylemonk-lead-scout/1.0 (site audit outreach research)"}
    mirrors = ["https://overpass-api.de/api/interpreter",
               "https://overpass.kumi.systems/api/interpreter",
               "https://overpass.private.coffee/api/interpreter"]
    last = None
    for attempt in range(tries):
        url = mirrors[attempt % len(mirrors)]
        try:
            req = urllib.request.Request(url,
                                         data=f"data={urllib.parse.quote(query)}".encode(),
                                         headers=OSM_UA)
            return json.loads(urllib.request.urlopen(req, timeout=60, context=CTX).read())
        except Exception as e:
            last = e
            time.sleep(15 * (attempt + 1))
    raise last

def osm_prospects(niche, area, limit):
    """Geocode the area, then Overpass-query tourism businesses that have a website."""
    tourism = {
        "holiday cottages": "guest_house|apartment|chalet",
        "self catering accommodation": "apartment|guest_house|chalet",
        "wedding venues": "hotel|guest_house",
        "boutique b&b": "guest_house|hotel|bed_and_breakfast",
    }.get(niche, "guest_house|hotel|apartment|chalet|bed_and_breakfast")
    try:
        q = urllib.parse.urlencode({"q": area, "format": "json", "limit": 1})
        req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + q,
                                     headers={"User-Agent": "kylemonk-lead-scout/1.0", "Accept": "application/json"})
        geo = json.loads(urllib.request.urlopen(req, timeout=15, context=CTX).read())
        if not geo:
            return []
        bb = geo[0]["boundingbox"]  # [south, north, west, east]
        bbox = f'{bb[0]},{bb[2]},{bb[1]},{bb[3]}'
        overpass = ("[out:json][timeout:60];"
                    f'nwr["tourism"~"^({tourism})$"]["website"~"."]({bbox});'
                    "out tags 200;")
        data = _overpass(overpass)
        seen, out = set(), []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            site = tags.get("website") or tags.get("contact:website") or ""
            if not site:
                continue
            site = site.strip()
            if not site.startswith("http"):
                site = "https://" + site
            host = urllib.parse.urlsplit(site).netloc.lower()
            if not host or host in seen or any(d in host for d in (
                    "facebook.com", "instagram.com", "airbnb", "booking.com", "tripadvisor",
                    "laterooms", "expedia", "sykescottages", "cottages.com", "hoseasons",
                    "snaptrip", "canopyandstars", "sawdays", "pitchup", "google.com")):
                continue
            seen.add(host)
            out.append((site, tags.get("name", "")))
            if len(out) >= limit * 3:
                break
        return out
    except Exception:
        return []

# ---------------- source 2: DuckDuckGo HTML (fallback — rate-limits hard) ----------------
def ddg(query, retries=2):
    """Return result URLs from DuckDuckGo HTML endpoint."""
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            html = urllib.request.urlopen(req, timeout=15, context=CTX).read().decode("utf-8", "ignore")
            links = []
            for m in re.finditer(r'uddg=([^&"]+)', html):
                real = urllib.parse.unquote(m.group(1))
                links.append(real)
            seen, out = set(), []
            for l in links:
                host = urllib.parse.urlsplit(l).netloc.lower()
                if host and host not in seen and not any(
                    d in host for d in DD_BLOCK
                ):
                    seen.add(host)
                    out.append(l)
            if out:
                return out
        except Exception:
            pass
        time.sleep(2 + attempt * 2)
    return []

DD_BLOCK = ("duckduckgo", "google.", "facebook.com", "instagram.com", "tripadvisor",
            "booking.com", "airbnb", "expedia", "yelp.", "guardian", "wikipedia",
            "rightmove", "zoopla", "sykescottages", "cottages.", "canopyandstars",
            "uniquehome.stays", "sawdays", "pitchup", "hoseasons")

# ---------------- fetch ----------------
def fetch(url):
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers=UA)
        raw = urllib.request.urlopen(req, timeout=10, context=CTX).read()
        dt = time.time() - t0
        return raw.decode("utf-8", "ignore"), dt, None
    except urllib.error.HTTPError as e:
        return "", None, f"HTTP {e.code}"
    except ssl.SSLError:
        return "", None, "SSL error (invalid/expired cert)"
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        return "", None, f"unreachable: {reason}"
    except Exception as e:
        return "", None, f"error: {type(e).__name__}"

# ---------------- qualification ----------------
OLD_BUILDERS = {
    "wix.com": "Wix (free/old tier)", "godaddy": "GoDaddy Builder",
    "secureserver": "GoDaddy Builder", "websitebuilder": "generic site builder",
    "1and1": "1&1/Ionos template", "ionos": "Ionos template",
    "moonfruit": "Moonfruit (dead platform)", "weebly": "Weebly",
    "yolasite": "Yola", "jimdo": "Jimdo", "vistaprint": "VistaPrint",
    "wordpress.org": None, "jquery-1.": "ancient jQuery (pre-2016 stack)",
}
MODERN_MARKERS = ("__next", "_next/static", "webflow", "svelte", "data-react",
                  "framerusercontent", "vercel", "netlify")

def qualify(url):
    """Visit a site and return a dict of signals + human-readable problems."""
    problems, score, info = [], 0, {}
    https = url.lower().startswith("https")
    if not https:
        problems.append("no HTTPS — browsers show 'Not secure' to every visitor")
        score += 3

    home, load_s, err = fetch(url if https else url.replace("http://", "https://"))
    if err and "SSL" in err:
        # https is broken — try plain http before declaring the site dead
        home, load_s, err = fetch(url if not https else url.replace("https://", "http://"))
        if not err:
            problems.append("HTTPS is broken — visitors get a security warning before the site loads")
            score += 3
    if err:
        if "HTTP 4" in err or "unreachable" in str(err) or "error" in str(err):
            # site fully broken = strongest possible prospect signal, but verify
            problems.append("site currently fails to load for visitors (verify manually)")
            score += 3
            return {"url": url, "score": score, "problems": problems,
                    "email": "", "load_s": None, "tech": "unknown"}
        else:
            return None

    low = home.lower()

    # speed
    if load_s is not None:
        info["load_s"] = round(load_s, 1)
        if load_s > 5:   problems.append(f"server took {load_s:.1f}s just to serve the homepage"); score += 3
        elif load_s > 3: problems.append(f"homepage took {load_s:.1f}s to load — past Google's 3s bounce cliff"); score += 2
    kb = len(home) // 1024
    if kb > 500: problems.append(f"page is {kb}KB of raw HTML — badly bloated"); score += 1

    # mobile
    if 'name="viewport"' not in low and "viewport" not in low:
        problems.append("no mobile viewport — site renders tiny/shrunk on phones"); score += 2

    # old tech fingerprints
    tech = []
    for marker, label in OLD_BUILDERS.items():
        if marker in low:
            if label:
                tech.append(label)
                if marker in ("moonfruit", "jquery-1.", "1and1"):
                    problems.append(f"built on {label}"); score += 3
                else:
                    tech_only = label
                    score += 1
    if tech: info["tech"] = ", ".join(sorted(set(t for t in tech if t))) or "CMS"
    mgen = re.search(r'name="generator"\s+content="([^"]+)"', home, re.I)
    if mgen:
        gen = mgen.group(1)
        ym = re.search(r"(19|20)\d{2}", gen)
        if ym and int(ym.group(0)) < 2019:
            problems.append(f"site generator stamp is from {ym.group(0)} — a rebuild is overdue"); score += 2

    # booking / enquiry capture
    has_form = "<form" in low
    has_booking_word = any(w in low for w in ("book", "enquiry", "inquiry", "check availability", "availability"))
    if not has_form and not has_booking_word:
        problems.append("no booking or enquiry form — every booking relies on a phone call"); score += 2

    # modern-site penalty
    if any(m in low for m in MODERN_MARKERS):
        score -= 6

    # find a contact email (homepage + likely contact pages)
    email = find_email(home)
    if not email:
        for path in ("/contact", "/contact-us", "/about"):
            page, _, e = fetch(url.rstrip("/") + path)
            if not e:
                email = find_email(page)
                if email: break
            if email: break
    info["email_found"] = bool(email)

    if not problems:
        return None  # site looks fine — not a prospect
    return {"url": url, "score": score, "problems": problems,
            "email": email, "load_s": info.get("load_s"), "tech": info.get("tech", "")}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
def find_email(html):
    m = re.search(r"mailto:([^\"'>\s]+)", html, re.I)
    if m:
        e = parseaddr(m.group(1))[1]
        if "@" in e: return e
    for e in EMAIL_RE.findall(html):
        if not any(x in e.lower() for x in (".png", ".jpg", ".webp", "sentry", "example", "yourdomain", "domain.com", "email.com", ".js")):
            return e
    return ""

# ---------------- output ----------------
def today(): return date.today().isoformat()

def write_csv(rows, niche, area):
    path = OUT / f"leads-{today()}.csv"
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["name", "biz", "url", "email", "value", "stage", "due", "notes", "updated"])
        for r in rows:
            dom = urllib.parse.urlsplit(r["url"]).netloc.replace("www.", "")
            biz = r.get("name_hint") or dom.split(".")[0].replace("-", " ").replace("_", " ").title()
            due = (date.today() + timedelta(days=2)).isoformat()
            w.writerow(["", biz, r["url"], r["email"], 1800, "prospect", due,
                        f"score {r['score']}: " + "; ".join(r["problems"][:2]),
                        today()])
    return path

def write_drafts(rows, niche, area):
    path = OUT / f"drafts-{today()}.md"
    with open(path, "w") as f:
        f.write(f"# Outreach drafts — {today()}\n")
        f.write(f"*{niche} · {area} · generated by scout. REVIEW & EDIT before sending. "
                f"Nothing has been sent. Delete any you don't like; fix any [brackets].*\n\n---\n\n")
        for i, r in enumerate(sorted(rows, key=lambda x: -x["score"]), 1):
            dom = urllib.parse.urlsplit(r["url"]).netloc.replace("www.", "")
            biz = r.get("name_hint") or dom.split(".")[0].replace("-", " ").title()
            f.write(f"## {i}. {biz} — score {r['score']}/20\n")
            f.write(f"**{r['url']}** · contact: {r['email'] or '*no email found — check site/Instagram*'}"
                    f" · load: {r['load_s'] if r['load_s'] else '?'}s{(' · ' + r['tech']) if r['tech'] else ''}\n\n")
            f.write("**Problems found:**\n")
            for p in r["problems"]:
                f.write(f"- {p}\n")
            f.write("\n**Draft:**\n\n```\n")
            f.write(f"Subject: {biz}'s website — one quick thing\n\n")
            f.write(f"Hi [Name — find on site/LinkedIn],\n\n")
            f.write(f"I build websites for {niche} businesses and was looking at {dom} today.\n\n")
            top = r["problems"][0][0].lower() + r["problems"][0][1:] if r["problems"] else ""
            f.write(f"One thing: {top}.\n\n")
            second = f" Also, {r['problems'][1][0].lower() + r['problems'][1][1:]}." if len(r["problems"]) > 1 else ""
            f.write(f"{second.strip()}\n\n" if second.strip() else "\n")
            f.write("I run a free 10-point teardown for businesses like yours — what's slow, "
                    "what's costing you bookings, what to fix first. Want me to run one on your site? "
                    "No charge, useful even if you never hire me.\n\n— Kyle\nhttps://goodanalysis.github.io/kylemonk-site/\n```\n\n---\n\n")
    return path

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche"); ap.add_argument("--area")
    ap.add_argument("--limit", type=int, default=10, help="min qualified leads wanted")
    ap.add_argument("--min-score", type=int, default=5)
    a = ap.parse_args()

    cfg = {}
    cfg_path = HERE / "config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
    niche = a.niche or cfg.get("niche", "holiday cottages")
    area = a.area or cfg.get("area", "Cornwall")
    min_score = a.min_score or cfg.get("min_score", 5)

    OUT.mkdir(exist_ok=True)

    # Source 1: OpenStreetMap — direct business websites, no bot wall
    named = osm_prospects(niche, area, a.limit)
    candidates = [u for u, _ in named]
    biz_names = {u: n for u, n in named}
    print(f"  OSM: {len(candidates)} businesses with own websites")
    if len(candidates) < a.limit:
        # Source 2: DDG fallback (only when OSM runs dry)
        queries = [
            f'{niche} in {area} own website',
            f'"{niche}" "{area}" book direct',
            f'{niche} {area} independent owner',
            f'{niche} {area} self catering contact',
        ]
        qi = 0
        while len(candidates) < a.limit * 3 and qi < len(queries):
            found = ddg(queries[qi]); qi += 1
            known = set(candidates)
            candidates += [u for u in found if u not in known]
            print(f"  DDG {qi}/{len(queries)}: +{len(found)} candidates ({len(candidates)} total)")
            if not found: time.sleep(3)
    candidates = candidates[:30]

    qualified = []
    for i, url in enumerate(candidates, 1):
        if len(qualified) >= a.limit: break
        print(f"  [{i}/{len(candidates)}] checking {urllib.parse.urlsplit(url).netloc}…", end=" ", flush=True)
        r = qualify(url)
        if r and r["score"] >= min_score:
            r["name_hint"] = biz_names.get(url, "")
            qualified.append(r)
            print(f"QUALIFIED (score {r['score']})")
        else:
            print("skip" + (f" (score {r['score']})" if r else ""))
        time.sleep(0.8)  # polite

    if not qualified:
        print("\nNo qualified leads this pass — try a different area or lower --min-score.")
        sys.exit(0)

    csv_p = write_csv(qualified, niche, area)
    md_p = write_drafts(qualified, niche, area)
    print(f"\n✔ {len(qualified)} qualified leads")
    print(f"  CSV (→ pipeline.html Import): {csv_p}")
    print(f"  Drafts (→ review & send):     {md_p}")
    print(f"  Avg score: {sum(r['score'] for r in qualified)/len(qualified):.1f}")

if __name__ == "__main__":
    main()
