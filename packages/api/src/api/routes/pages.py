"""Tiny landing + callback pages so the deployed API can be logged into without a frontend.

Place at: packages/api/src/api/routes/pages.py

The Spotify callback in auth.py redirects to {FRONTEND_URL}/auth/callback?token=...&user_id=...
With FRONTEND_URL set to the API's own public URL, that lands on callback_page() below,
which shows the JWT so you can use it in curl / the smoke test / Swagger.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)

_STYLE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 34rem; margin: 3rem auto;
         padding: 0 1rem; line-height: 1.5; }
  a.btn, button { display: inline-block; padding: .7rem 1.2rem; border-radius: .5rem;
         border: 0; background: #1db954; color: #000; font-weight: 600; font-size: 1rem;
         text-decoration: none; cursor: pointer; }
  textarea { width: 100%; height: 8rem; font-family: ui-monospace, monospace;
         font-size: .8rem; word-break: break-all; }
  code { background: rgba(127,127,127,.2); padding: .1rem .3rem; border-radius: .25rem; }
  .muted { opacity: .7; font-size: .9rem; }
</style>
"""

HOME_HTML = f"""<!doctype html>
<html lang="en"><head><title>Wavelength staging</title>{_STYLE}</head>
<body>
  <h1>Wavelength</h1>
  <p>Staging API. Log in with Spotify to get a session token.</p>
  <p><a class="btn" href="/auth/spotify/authorize">Connect Spotify</a></p>
  <p class="muted">API docs: <a href="/docs">/docs</a></p>
</body></html>"""

CALLBACK_HTML = f"""<!doctype html>
<html lang="en"><head><title>Wavelength login</title>{_STYLE}</head>
<body>
  <h1 id="title">Logging in...</h1>
  <div id="ok" hidden>
    <p>Spotify login worked. Your session token (JWT):</p>
    <textarea id="token" readonly></textarea>
    <p><button id="copy" type="button">Copy token</button></p>
    <p>User id: <code id="uid"></code></p>
    <p class="muted">Use it as <code>Authorization: Bearer &lt;token&gt;</code>, for example
    <code>TOKEN=&lt;token&gt; python scripts/smoke_test.py &lt;api url&gt;</code>.</p>
  </div>
  <p id="err" hidden>No token found in the URL. <a href="/">Start again</a>.</p>
<script>
  const params = new URLSearchParams(location.search);
  const token = params.get("token");
  if (token) {{
    document.getElementById("title").textContent = "Connected";
    document.getElementById("token").value = token;
    document.getElementById("uid").textContent = params.get("user_id") || "";
    document.getElementById("ok").hidden = false;
    document.getElementById("copy").addEventListener("click", async () => {{
      try {{ await navigator.clipboard.writeText(token); }}
      catch (e) {{ document.getElementById("token").select(); }}
    }});
    // remove the token from the address bar / history
    history.replaceState(null, "", location.pathname);
  }} else {{
    document.getElementById("title").textContent = "Login failed";
    document.getElementById("err").hidden = false;
  }}
</script>
</body></html>"""


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return HOME_HTML


@router.get("/auth/callback", response_class=HTMLResponse)
def callback_page() -> str:
    return CALLBACK_HTML
