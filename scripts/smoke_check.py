"""Smoke test for a deployed Wavelength API.

Usage:
    python scripts/smoke_check.py https://your-api.up.railway.app
    TOKEN=<jwt> python scripts/smoke_check.py https://your-api.up.railway.app

Without TOKEN it checks health, docs, auth-protection and the Spotify redirect.
With TOKEN (the JWT from a real login) it also hits the authenticated endpoints.
Route paths are discovered from /openapi.json, so prefixes don't need to be hardcoded.
"""

import os
import sys
from urllib.parse import parse_qs, urlparse

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("TOKEN")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def find_path(paths: list[str], suffix: str) -> str | None:
    return next((p for p in paths if p.endswith(suffix)), None)


client = httpx.Client(base_url=BASE, timeout=20, follow_redirects=False)

# 1. health
r = client.get("/health")
check("health", r.status_code == 200 and r.json().get("status") == "ok", f"({r.status_code})")

# 2. openapi (also tells us the real route paths)
r = client.get("/openapi.json")
paths = list(r.json().get("paths", {})) if r.status_code == 200 else []
check("openapi reachable", r.status_code == 200, f"({len(paths)} routes)")

# 2b. landing + callback pages (the no-frontend login path)
for page in ("/", "/auth/callback"):
    r = client.get(page)
    check(f"page {page}", r.status_code == 200 and "text/html" in r.headers.get("content-type", ""),
          f"({r.status_code})")

# 3. protected route rejects anonymous calls
me = find_path(paths, "/me")
if me:
    r = client.get(me)
    check("anonymous /me rejected", r.status_code in (401, 403), f"({me} -> {r.status_code})")

# 4. Spotify authorize redirect uses the right redirect_uri
auth = find_path(paths, "/authorize")
if auth:
    r = client.get(auth)
    loc = r.headers.get("location", "")
    q = parse_qs(urlparse(loc).query)
    check(
        "authorize redirects to Spotify",
        r.status_code in (302, 303, 307) and "accounts.spotify.com" in loc,
        f"({r.status_code})",
    )
    redirect_uri = q.get("redirect_uri", [""])[0]
    check(
        "redirect_uri is https and not localhost",
        redirect_uri.startswith("https://") and "localhost" not in redirect_uri
        and "127.0.0.1" not in redirect_uri,
        f"({redirect_uri})",
    )
    print(f"       -> make sure this EXACT value is registered in Spotify: {redirect_uri}")

# 5. authenticated checks (optional)
if TOKEN:
    h = {"Authorization": f"Bearer {TOKEN}"}
    for suffix in ("/me", "/profile", "/filters", "/feed", "/threads"):
        p = find_path(paths, suffix)
        if p and "{" not in p:
            r = client.get(p, headers=h)
            check(f"GET {p}", r.status_code == 200, f"({r.status_code})")
else:
    print("TOKEN not set, skipping authenticated checks")

failed = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
