"""The board's CV viewer in real browsers: verified pdf.js renders the CV, every failure ends in the simple preview.

Runs the board page with a fake in-memory `claude.use("db")` and synthetic data (the example persona), the example
CV built by build.py, and the pinned pdf.js files served locally after checking them against the page's hashes.

    python3 -m unittest tests.board.test_board_visual       (needs: pip install playwright; playwright install)

Skips without Playwright, LaTeX or network unless REQUIRE_BROWSER=1 (CI), where a skip is a failure.
Set BOARD_CSP_FILE=<file> to run every test under the Claude artifact page's real CSP (one header line).
Screenshots land in tests/board/out/.
"""
import base64, hashlib, json, os, pathlib, re, shutil, subprocess, sys, tempfile, unittest, urllib.request

REPO = pathlib.Path(__file__).resolve().parents[2]
BOARD = REPO / "plugins/job-swipe/board/job-swipe.html"
BUILD = REPO / "plugins/job-swipe/skills/tailor-cvs/cv/build.py"
EXAMPLES = BUILD.parent / "examples"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
CACHE = HERE / ".cache"
CSP_FILE = os.environ.get("BOARD_CSP_FILE")  # the Claude artifact page's CSP, captured by hand; replayed only when set
ORIGIN = "https://board.test"
REQUIRE = os.environ.get("REQUIRE_BROWSER") == "1"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

FAKE_CLAUDE = r"""
(() => {
  const store = JSON.parse(%s);
  const clone = v => JSON.parse(JSON.stringify(v));
  const snapOf = (id, data) => ({id, exists: data !== undefined, data: () => clone(data)});
  function query(name, filters, order, max){
    return {
      where(f, op, v){ if(op !== "==") throw new Error("fake db: only =="); return query(name, filters.concat([[f, v]]), order, max); },
      orderBy(f, dir){ return query(name, filters, [f, dir || "asc"], max); },
      limit(n){ return query(name, filters, order, n); },
      async get(){
        let rows = Object.entries(store[name] || {}).filter(([, d]) => filters.every(([f, v]) => d[f] === v));
        if(order) rows.sort(([, a], [, b]) => (a[order[0]] > b[order[0]] ? 1 : -1) * (order[1] === "desc" ? -1 : 1));
        if(max) rows = rows.slice(0, max);
        const docs = rows.map(([id, d]) => snapOf(id, d));
        return {docs, size: docs.length, empty: !docs.length};
      },
    };
  }
  const db = {
    collection: name => query(name, [], null, null),
    doc(path){
      const [name, id] = path.split("/");
      return {
        async get(){ return snapOf(id, (store[name] || {})[id]); },
        async set(data){ (store[name] = store[name] || {})[id] = clone(data); },
        async update(patch){
          if(!(store[name] || {})[id]) throw new Error("fake db: no document " + path);
          Object.assign(store[name][id], clone(patch));
        },
      };
    },
  };
  window.__fakeStore = store;
  window.claude = {use: async what => { if(what === "db") return db; throw new Error("not available: " + what); }};
})();
"""

DATA = {
    "profile": {"me": {"name": "Alex Example", "brief": "Product manager roles in Berlin, B2B SaaS.",
                       "searchSchedule": "every day at 8:00", "cvEnabled": True, "cvSchedule": "every morning",
                       "timezone": "Europe/Berlin"}},
    "jobs": {
        "p1": {"status": "pending", "company": "Example Corp", "title": "Senior Product Manager", "location": "Berlin",
               "addedDate": "2026-10-20", "blurb": "Own the data product roadmap.", "tags": ["B2B", "SQL"],
               "url": "https://example.com/jobs/1"},
        "p2": {"status": "pending", "company": "Example Corp", "title": "Product Manager, Payments", "location": "Berlin",
               "addedDate": "2026-10-19", "blurb": "Own checkout.", "url": "https://example.com/jobs/5"},
        "l1": {"status": "liked", "company": "Example Corp", "title": "Product Manager", "location": "Berlin",
               "swipedAt": "2026-10-21T08:00:00Z", "url": "https://example.com/jobs/2", "cvAssetId": "cv1",
               "cvFileName": "Alex_Example_CV_Example_Corp.pdf", "cvCreatedAt": "2026-10-22T07:00:00Z",
               "note": "loved the team"},
        "l2": {"status": "liked", "company": "Gone GmbH", "title": "Product Owner", "location": "Hamburg",
               "swipedAt": "2026-10-20T08:00:00Z", "url": "https://example.com/jobs/3", "cvAssetId": "gone",
               "cvCreatedAt": "2026-10-01T07:00:00Z"},
        "l3": {"status": "liked", "company": "Paused AG", "title": "Product Lead", "location": "Munich",
               "swipedAt": "2026-10-19T08:00:00Z", "url": "https://example.com/jobs/4", "cvStatus": "removed",
               "cvAssetId": "", "cvCreatedAt": "2026-10-18T07:00:00Z"},
    },
}


def pdfjs_constant():
    """{"lib": (url, sha384), "worker": (url, sha384)} as pinned in the board page."""
    html = BOARD.read_text(encoding="utf-8")
    out = {}
    for part in ("lib", "worker"):
        m = re.search(part + r':\s*\{url:\s*"([^"]+)",\s*sha384:\s*"(sha384-[^"]+)"', html)
        out[part] = (m.group(1), m.group(2))
    return out


def sri(data):
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


def pinned_pdfjs():
    """The pinned pdf.js files, downloaded once into tests/board/.cache and checked against the page's hashes."""
    files = {}
    CACHE.mkdir(exist_ok=True)
    for part, (url, want) in pdfjs_constant().items():
        path = CACHE / url.rsplit("/", 1)[1]
        if not path.exists() or sri(path.read_bytes()) != want:
            with urllib.request.urlopen(url, timeout=60) as r:
                path.write_bytes(r.read())
        data = path.read_bytes()
        if sri(data) != want:
            raise AssertionError(f"{url} does not match the hash pinned in job-swipe.html")
        files[url] = data
    return files


def example_pdf():
    tmp = pathlib.Path(tempfile.mkdtemp())
    r = subprocess.run([sys.executable, str(BUILD), str(EXAMPLES / "master_cv.example.yaml"),
                        str(EXAMPLES / "job_spec.example.yaml"), str(tmp)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("example CV build failed:\n" + r.stdout + r.stderr)
    data = next((tmp / "job_spec.example").glob("*.pdf")).read_bytes()
    shutil.rmtree(tmp, ignore_errors=True)
    return data


@unittest.skipUnless(sync_playwright or REQUIRE, "needs Playwright (CI sets REQUIRE_BROWSER=1)")
class BoardViewerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not sync_playwright:
            raise AssertionError("REQUIRE_BROWSER=1 but Playwright is not installed")
        try:
            cls.pdfjs = pinned_pdfjs()
            cls.pdf = example_pdf()
        except (OSError, RuntimeError) as e:
            if REQUIRE:
                raise
            raise unittest.SkipTest(f"needs network and LaTeX: {e}")
        OUT.mkdir(exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browsers = {}

    @classmethod
    def tearDownClass(cls):
        for b in cls.browsers.values():
            b.close()
        cls.pw.stop()

    def browser(self, engine):
        if engine not in self.browsers:
            self.browsers[engine] = getattr(self.pw, engine).launch()
        return self.browsers[engine]

    def open_board(self, engine="chromium", device=None, csp=None, block_cdn=False, blob_delay_ms=0, blob_status=200):
        """A board page on its own origin; returns (page, console lines)."""
        opts = dict(self.pw.devices[device]) if device else {"viewport": {"width": 1280, "height": 800}}
        opts.pop("default_browser_type", None)
        ctx = self.browser(engine).new_context(**opts)
        self.addCleanup(ctx.close)
        ctx.add_init_script(FAKE_CLAUDE % json.dumps(json.dumps(DATA)))
        if blob_delay_ms:  # a slow network for the CV file, inside the page so the test keeps running meanwhile
            ctx.add_init_script("const f = window.fetch; window.fetch = (u, o) => String(u).includes('/_blob/') ? "
                                "new Promise(r => setTimeout(r, %d)).then(() => f(u, o)) : f(u, o);" % blob_delay_ms)
        csp = csp or (pathlib.Path(CSP_FILE).read_text().strip() if CSP_FILE else None)
        board = BOARD.read_bytes()

        def serve_board(route):
            headers = {"content-type": "text/html; charset=utf-8"}
            if csp:
                headers["content-security-policy"] = csp
            route.fulfill(status=200, headers=headers, body=board)

        def serve_blob(route):
            if blob_status != 200:
                route.fulfill(status=blob_status, body="error")
            elif route.request.url.endswith("/cv1"):
                route.fulfill(status=200, headers={"content-type": "application/pdf"}, body=self.pdf)
            else:
                route.fulfill(status=404, body="not found")

        def serve_cdn(route):
            body = self.pdfjs.get(route.request.url)
            if block_cdn or body is None:
                return route.abort()
            route.fulfill(status=200, body=body, headers={"content-type": "text/javascript",
                                                         "access-control-allow-origin": "*"})

        ctx.route(ORIGIN + "/", serve_board)
        ctx.route(ORIGIN + "/_blob/**", serve_blob)
        ctx.route("https://cdnjs.cloudflare.com/**", serve_cdn)
        page = ctx.new_page()
        lines = []
        page.on("console", lambda m: lines.append(m.text))
        page.goto(ORIGIN + "/")
        page.wait_for_selector("#cardEl")
        return page, lines

    def open_liked(self, page, company="Example Corp"):
        page.click("#btnShowLiked")
        card = page.locator(".likedCard", has_text=company)
        card.locator("[data-action=open-cv]").click()

    def assert_rendered(self, page):
        page.wait_for_selector("#cvBody canvas", timeout=20000)
        dark = page.evaluate("""() => {
          const c = document.querySelector('#cvBody canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
          let n = 0; for(let i = 0; i < d.length; i += 16) if(d[i] < 128) n++; return n; }""")
        self.assertGreater(dark, 500, "canvas is blank")

    def assert_simple_preview(self, page, lines):
        page.wait_for_selector("#cvBody iframe", timeout=20000)
        self.assertTrue(page.is_visible("#cvNotice"))
        self.assertIn("Showing a simple preview on this device.", page.inner_text("#cvNotice"))
        self.assertTrue(page.is_visible("#cvFull"))
        self.assertTrue(any(l.startswith("pdf viewer: iframe") for l in lines), lines)

    def test_cv_renders_with_verified_pdfjs_desktop(self):
        page, lines = self.open_board()
        self.open_liked(page)
        self.assert_rendered(page)
        self.assertIn("pdf viewer: verified", lines)
        self.assertTrue(page.is_hidden("#cvNotice"))
        page.screenshot(path=str(OUT / "cv-desktop-chromium.png"))

    def test_cv_renders_on_phone_webkit(self):
        page, lines = self.open_board("webkit", device="iPhone 13")
        self.open_liked(page)
        self.assert_rendered(page)
        self.assertIn("pdf viewer: verified", lines)
        page.screenshot(path=str(OUT / "cv-phone-webkit.png"))

    def test_cdn_blocked_shows_simple_preview(self):
        page, lines = self.open_board(block_cdn=True)
        self.open_liked(page)
        self.assert_simple_preview(page, lines)
        page.screenshot(path=str(OUT / "cv-cdn-blocked.png"))

    def test_tampered_library_shows_simple_preview(self):
        page, lines = self.open_board()
        lib_url = pdfjs_constant()["lib"][0]
        page.context.route(lib_url, lambda r: r.fulfill(status=200, body=b"window.pdfjsLib = {};",
                                                         headers={"content-type": "text/javascript",
                                                                  "access-control-allow-origin": "*"}))
        self.open_liked(page)
        self.assert_simple_preview(page, lines)

    def test_workers_blocked_never_hangs(self):
        page, lines = self.open_board(csp="worker-src 'none'")
        self.open_liked(page)
        page.wait_for_selector("#cvBody canvas, #cvBody iframe", timeout=20000)
        self.assertEqual(page.inner_text("#cvMsg"), "")
        page.screenshot(path=str(OUT / "cv-workers-blocked.png"))

    def test_missing_cv_explains_why(self):
        page, _ = self.open_board()
        self.open_liked(page, "Gone GmbH")
        page.wait_for_function("document.querySelector('#cvMsg').textContent.includes('isn\\'t available')")
        self.assertEqual(page.inner_text("#cvMsg"),
                         "This CV isn't available any more. It may have been deleted after 7 days. "
                         "Ask for a new one by liking the job again.")
        self.assertTrue(page.is_hidden("#cvSave"))
        self.assertNotIn("404", page.inner_text("#cvViewer"))

    def test_slow_load_says_still_working(self):
        page, _ = self.open_board(blob_delay_ms=9000)  # far past the page's 3 s "slow" mark, so CI load can't race it
        self.open_liked(page)
        self.assertEqual(page.inner_text("#cvMsg"), "Opening your CV…")
        page.wait_for_function("document.querySelector('#cvMsg').textContent.includes('Still working')", timeout=8000)
        self.assertEqual(page.get_attribute("#cvMsg", "aria-live"), "polite")
        self.assert_rendered(page)

    def test_tampered_or_broken_worker_shows_simple_preview(self):
        worker_url = pdfjs_constant()["worker"][0]
        for status, body in ((200, b"self.onmessage = () => {};"), (500, b"")):
            with self.subTest(status=status):
                page, lines = self.open_board()
                def serve(route, status=status, body=body):  # Playwright passes only the route to a 1-argument call
                    route.fulfill(status=status, body=body,
                                  headers={"content-type": "text/javascript", "access-control-allow-origin": "*"})
                page.context.route(worker_url, lambda route: serve(route))
                self.open_liked(page)
                self.assert_simple_preview(page, lines)

    def test_network_error_is_not_called_deleted(self):
        page, lines = self.open_board(blob_status=503)
        self.open_liked(page)
        page.wait_for_function("document.querySelector('#cvMsg').textContent.includes('right now')")
        self.assertEqual(page.inner_text("#cvMsg"), "Couldn't open this CV right now. Check your connection and try again.")
        self.assertTrue(any(l.startswith("cv file:") for l in lines), lines)

    def test_close_during_load_discards_late_result(self):
        page, _ = self.open_board(blob_delay_ms=1500)
        self.open_liked(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(2500)  # the delayed CV arrives after the viewer closed
        self.assertTrue(page.is_hidden("#cvViewer"))
        self.assertEqual(page.evaluate("document.querySelector('#cvBody').children.length"), 0)
        self.assertEqual(page.inner_text("#cvMsg"), "")

    def test_open_full_pdf_says_so_when_no_tab_opens(self):
        page, lines = self.open_board(block_cdn=True)
        page.evaluate("window.open = () => null")
        self.open_liked(page)
        self.assert_simple_preview(page, lines)
        page.click("#cvFull")
        self.assertEqual(page.inner_text("#cvMsg"), "This device didn't open a new tab. Use Save PDF instead.")

    def test_background_is_inert_while_viewer_is_open(self):
        page, _ = self.open_board()
        self.open_liked(page)
        self.assertTrue(page.evaluate("document.getElementById('likedPanel').inert"))
        page.keyboard.press("Escape")
        self.assertFalse(page.evaluate("document.getElementById('likedPanel').inert"))

    def test_cv_removed_by_cvs_off_says_so(self):
        page, _ = self.open_board()
        page.click("#btnShowLiked")
        card = page.locator(".likedCard", has_text="Paused AG")
        self.assertEqual(card.locator(".cvRow").inner_text(), "CV deleted when CVs were turned off")
        self.assertEqual(card.locator("[data-action=open-cv]").count(), 0)

    def stored(self, page, path):
        name, doc = path.split("/")
        return page.evaluate("([n, d]) => window.__fakeStore[n][d]", [name, doc])

    def test_note_typed_before_swiping_goes_with_that_job(self):
        page, _ = self.open_board()
        page.fill("#noteInput", "too junior")
        self.assertIn("saved with your swipe", page.inner_text("#noteRow").lower())
        page.click("#btnPass")
        page.wait_for_function("document.getElementById('whyStrip') && !document.getElementById('whyStrip').hidden")
        self.assertEqual(self.stored(page, "jobs/p1")["note"], "too junior")
        self.assertIn("Note saved: too junior", page.inner_text("#whyStrip"))
        self.assertTrue(page.is_hidden("#whyInput"))
        self.assertEqual(page.input_value("#noteInput"), "")  # the next card starts with an empty box

    def test_after_swiping_it_asks_why_for_that_job(self):
        page, _ = self.open_board()
        page.click("#btnLike")
        page.wait_for_selector("#whyInput", state="visible")
        strip = page.inner_text("#whyStrip")
        self.assertIn("Interested", strip)
        self.assertIn("Senior Product Manager", strip)
        page.fill("#whyInput", "great team")
        page.press("#whyInput", "Enter")
        page.wait_for_function("document.getElementById('whyStrip').textContent.includes('Note saved: great team')")
        self.assertEqual(self.stored(page, "jobs/p1")["note"], "great team")
        self.assertNotIn("note", self.stored(page, "jobs/p2"))
        page.screenshot(path=str(OUT / "notes-after-swipe.png"))

    def test_dont_ask_again_and_turn_it_back_on(self):
        page, _ = self.open_board()
        page.click("#btnPass")
        page.wait_for_selector("#whyNever", state="visible")
        page.click("#whyNever")
        self.assertTrue(page.is_hidden("#whyStrip"))
        self.assertIs(self.stored(page, "profile/me")["askWhyAfterSwipe"], False)
        page.click("#btnPass")
        page.wait_for_timeout(400)
        self.assertTrue(page.is_hidden("#whyStrip"))
        self.assertTrue(page.is_visible("#noteInput"))  # a note before swiping still works
        page.click("#btnShowPrefs")
        self.assertFalse(page.is_checked("#askWhyToggle"))
        page.check("#askWhyToggle")
        page.wait_for_function("window.__fakeStore.profile.me.askWhyAfterSwipe === true")
        page.screenshot(path=str(OUT / "notes-setting.png"))

    def test_undo_hides_the_why_strip(self):
        page, _ = self.open_board()
        page.click("#btnPass")
        page.wait_for_selector("#whyInput", state="visible")
        page.click("#btnUndo")
        self.assertTrue(page.is_hidden("#whyStrip"))

    def test_liked_card_shows_and_edits_the_note(self):
        page, _ = self.open_board()
        page.click("#btnShowLiked")
        card = page.locator(".likedCard", has_text="Product Manager").first
        self.assertIn("Your note: loved the team", card.inner_text())
        card.locator("[data-action=note-toggle]").click()
        card.locator("[data-note-edit]").fill("loved the team, hybrid ok")
        card.locator("[data-action=note-save]").click()
        page.wait_for_function("window.__fakeStore.jobs.l1.note === 'loved the team, hybrid ok'")
        self.assertIn("Your note: loved the team, hybrid ok", page.locator(".likedCard", has_text="loved the team").inner_text())

    def test_already_applied_is_a_labelled_card_button(self):
        page, _ = self.open_board()
        self.assertEqual(page.locator("#controls button").count(), 2)  # only pass and like stay round
        foot = page.locator("#cardEl .cardFoot")
        applied, posting = foot.locator("#btnApplied"), foot.locator("a.postingBtn")
        self.assertEqual(applied.inner_text(), "Already applied")
        self.assertIn("View full posting", posting.inner_text())
        a, b = applied.bounding_box(), posting.bounding_box()
        self.assertLess(a["x"], b["x"])  # applied on the left, posting on the right
        self.assertGreaterEqual(min(a["height"], b["height"]), 44)
        bg = page.evaluate("getComputedStyle(document.querySelector('a.postingBtn')).backgroundColor")
        accent = page.evaluate("""(() => { const d = document.createElement('div'); d.style.color = 'var(--accent)';
            document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })()""")
        self.assertEqual(bg, accent)
        applied.click()
        page.wait_for_function("window.__fakeStore.jobs.p1.status === 'applied'")
        self.assertIn("Applied", page.inner_text("#whyStrip"))
        page.screenshot(path=str(OUT / "card-footer.png"))

    def test_focus_moves_into_viewer_and_back(self):
        page, _ = self.open_board()
        self.open_liked(page)
        self.assert_rendered(page)
        self.assertEqual(page.evaluate("document.activeElement.id"), "cvClose")
        page.keyboard.press("Tab")
        self.assertEqual(page.evaluate("document.activeElement.id"), "cvSave")  # wrapped, never left the viewer
        page.keyboard.press("Shift+Tab")
        self.assertEqual(page.evaluate("document.activeElement.id"), "cvClose")
        page.keyboard.press("Escape")
        self.assertTrue(page.is_hidden("#cvViewer"))
        self.assertEqual(page.evaluate("document.activeElement.dataset.action"), "open-cv")

    def test_text_is_utf8_and_version_shows(self):
        page, _ = self.open_board()
        self.assertEqual(page.inner_text("#btnShowPrefs"), "⚙")
        page.click("#btnShowPrefs")
        row = page.locator("#scheduleRows .kv", has_text="Board version")
        self.assertEqual(row.locator("b").inner_text(), re.search(r'BOARD_VERSION = "([^"]+)"', BOARD.read_text()).group(1))
        page.set_viewport_size({"width": 390, "height": 844})
        self.assertGreaterEqual(page.locator("#btnShowPrefs").bounding_box()["height"], 44)
        page.screenshot(path=str(OUT / "prefs-390.png"))


if __name__ == "__main__":
    unittest.main()
