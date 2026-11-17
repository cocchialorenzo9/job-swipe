"""Screenshots of the reference board for the board spec (plugins/job-swipe/references/board-screens/).

Uses the same fake storage and example data as test_board_visual.py. Run it again after any design change:

    python3 tests/board/capture_spec_screens.py        (needs: pip install playwright; playwright install chromium)
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_board_visual import BOARD, DATA, FAKE_CLAUDE, ORIGIN, REPO, example_pdf, pinned_pdfjs  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = REPO / "plugins/job-swipe/references/board-screens"
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2}


def open_board(pw, scheme, pdf, pdfjs, data=DATA):
    ctx = pw.chromium.launch().new_context(color_scheme=scheme, **PHONE)
    ctx.add_init_script(FAKE_CLAUDE % json.dumps(json.dumps(data)))
    ctx.route(ORIGIN + "/", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"},
                                                body=BOARD.read_bytes()))
    ctx.route(ORIGIN + "/_blob/**", lambda r: r.fulfill(status=200, headers={"content-type": "application/pdf"}, body=pdf)
              if r.request.url.endswith("/cv1") else r.fulfill(status=404, body="not found"))
    ctx.route("https://cdnjs.cloudflare.com/**", lambda r: r.fulfill(
        status=200, body=pdfjs[r.request.url], headers={"content-type": "text/javascript",
                                                        "access-control-allow-origin": "*"}))
    page = ctx.new_page()
    page.goto(ORIGIN + "/")
    return page


def click(page, sel):
    """A DOM click: the swipe animation can leave the pointer target busy for a moment."""
    page.locator(sel).dispatch_event("click")


def shot(page, name):
    page.wait_for_timeout(400)  # let transitions finish
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdf, pdfjs = example_pdf(), pinned_pdfjs()
    empty = {"profile": DATA["profile"], "jobs": {k: v for k, v in DATA["jobs"].items() if v["status"] != "pending"}}
    with sync_playwright() as pw:
        for scheme in ("light", "dark"):
            page = open_board(pw, scheme, pdf, pdfjs)
            page.wait_for_selector("#cardEl")
            shot(page, f"swipe-card-{scheme}")
            page.click("#btnShowLiked"); page.wait_for_selector(".likedCard")
            shot(page, f"tab-interested-{scheme}")
        page = open_board(pw, "light", pdf, pdfjs)
        page.wait_for_selector("#cardEl")
        page.click("#btnLike"); page.wait_for_selector("#whyStrip:not([hidden])")
        shot(page, "swipe-why-strip-light")
        click(page, "#btnShowLiked"); page.wait_for_selector(".likedCard"); click(page, "#tabApplied"); page.wait_for_selector(".likedCard:has-text('Applied Inc')")
        shot(page, "tab-applied-light")
        click(page, "#tabPassed"); page.wait_for_selector(".likedCard:has-text('Far Away')")
        shot(page, "tab-passed-light")
        click(page, "#tabLiked"); page.wait_for_selector(".likedCard:has-text('Example Corp')")
        page.locator(".likedCard", has_text="Example Corp").locator("[data-action=open-cv]").click()
        page.wait_for_selector("#cvBody canvas", timeout=20000)
        shot(page, "cv-viewer-light")
        page = open_board(pw, "light", pdf, pdfjs)
        page.wait_for_selector("#cardEl")
        page.click("#btnShowPrefs"); page.wait_for_selector("#scheduleRows .kv")
        shot(page, "preferences-light")
        page = open_board(pw, "light", pdf, pdfjs, data=empty)
        page.wait_for_selector(".empty:has-text('caught up')")
        shot(page, "swipe-empty-light")
    print("\n".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
