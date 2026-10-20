"""Read Kohl's search results through a real Chrome window on the user's Mac.

kohls.com answers every script, and headless Chrome, with 403 "Access Denied".
A normal windowed Chrome gets the page, so this drives one over the DevTools
protocol: Chrome runs on the Mac with --remote-debugging-port, an ssh tunnel
brings that port here, and Playwright (from Herald's venv) connects to it.
Run with the venv's python: `python lib/kohls_browser.py '["mens bomber jacket"]' 3 <ssh-host>`.
Only the main grid is read (not carousels or ads), 120 items a page, in Kohl's relevance order.
Prints a JSON list of {id, title, price, was, url, image, query}.
"""
import json, re, socket, subprocess, sys, time, urllib.request

PORT = 9222
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# Expanded by the Mac's shell, so the profile lives in whoever's home it is.
PROFILE = '"$HOME/.herald-shop-chrome"'
HOST = "localhost"

CARDS = """() => {
 const ids = e => new Set([...e.querySelectorAll("a[href*='/product/prd-']")].map(x => (x.href.match(/prd-(\\d+)/)||[0,x.href])[1]));
 const seen = new Set(), out = [];
 for (const a of document.querySelectorAll(".product-grid a[href*='/product/prd-']")) {
  const id = (a.href.match(/prd-(\\d+)/)||[0,a.href])[1]; if (seen.has(id)) continue; seen.add(id);
  let c = a; while (c.parentElement && ids(c.parentElement).size === 1) c = c.parentElement;
  out.push({id, url: a.href, text: c.innerText.slice(0, 400), image: (c.querySelector('img') || {}).src || null});
 } return out; }"""


def port_open():
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("localhost", PORT)) == 0


def browser_up():
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/json/version", timeout=2)
        return True
    except Exception:
        return False


def close_browser():
    """Quit the Chrome this started, and only that one (matched on its profile).

    Left running, it is the user's Chrome: opening Chrome from Spotlight or the
    Dock brings this instance forward instead of starting theirs, so they land
    in an empty profile. And because it was started over ssh it cannot reach
    the login keychain, so Chrome shows "Relaunch the browser to load your
    profile data and keep it encrypted". Both were seen on 18 Oct 2026.
    The [e] keeps pkill from matching the shell that runs it.
    """
    subprocess.run(["ssh", "-o", "ConnectTimeout=8", HOST,
                    "pkill -f 'user-data-dir=[^ ]*herald-shop-chrom[e]'"],
                   capture_output=True, timeout=30)


def ensure_browser():
    """Start Chrome on the Mac and the tunnel to it, if they are not already up.

    The tunnel outlives Chrome (quitting Chrome, or the Mac sleeping, leaves the
    local port open and answering nothing), so an open port is not proof of a
    browser: ask Chrome itself, and restart only the half that is missing.
    """
    if browser_up():
        return
    subprocess.run(["ssh", "-o", "ConnectTimeout=8", HOST,
                    f'nohup "{CHROME}" --remote-debugging-port={PORT} --user-data-dir={PROFILE} '
                    f'--no-first-run --no-default-browser-check about:blank >/dev/null 2>&1 &'],
                   check=True, timeout=30)
    time.sleep(4)
    if not port_open():
        subprocess.run(["ssh", "-f", "-N", "-o", "ExitOnForwardFailure=yes",
                        "-L", f"{PORT}:localhost:{PORT}", HOST], check=True, timeout=30)
    for _ in range(10):
        if browser_up():
            return
        time.sleep(1)
    raise RuntimeError(f"Chrome on {HOST} did not come up (is it awake and unlocked?)")


def parse(card, query):
    lines = [l.strip() for l in card["text"].split("\n") if l.strip()]
    prices = re.findall(r"\$\d[\d,]*\.\d\d", card["text"])
    return {"id": card["id"], "title": next((l for l in lines if len(l) > 8 and not l.startswith(("$", "+")) and "out of 5" not in l), ""), "price": prices[0] if prices else None,
            "was": prices[-1] if len(prices) > 1 else None, "url": card["url"].split("&topSkuId")[0].split("?topSkuId")[0],
            "image": card["image"], "query": query}


def search(queries, pages=3):
    from playwright.sync_api import sync_playwright
    ensure_browser()
    try:
        return _search(sync_playwright, queries, pages)
    finally:
        close_browser()


def _search(sync_playwright, queries, pages):
    out, seen = [], set()
    with sync_playwright() as p:
        ctx = p.chromium.connect_over_cdp(f"http://localhost:{PORT}").contexts[0]
        pg = ctx.new_page()
        for q in queries:
            for n in range(pages):
                url = "https://www.kohls.com/search.jsp?search=" + q.replace(" ", "+") + (f"&WS={120 * n}" if n else "")
                for attempt in range(3):
                    try:
                        pg.goto(url, wait_until="domcontentloaded", timeout=45000)
                        pg.wait_for_timeout(6000 + 3000 * attempt)
                        cards = pg.evaluate(CARDS)
                        break
                    except Exception as e:
                        print(f"kohls '{q}' p{n} try {attempt + 1}: {str(e).splitlines()[0][:100]}", file=sys.stderr)
                        cards = []
                for c in cards:
                    if c["id"] not in seen:
                        seen.add(c["id"])
                        out.append(parse(c, q))
        pg.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) > 3:
        HOST = sys.argv[3]
    json.dump(search(json.loads(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 3), sys.stdout)
