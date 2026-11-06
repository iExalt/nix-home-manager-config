"""Journey: on a phone-class CPU, select two nodes in turn and check the inspector follows."""
from playwright.sync_api import expect, sync_playwright

PHONE_CPU_SLOWDOWN = 6  # the phone profile: a mid-range phone is about six times slower


def tap_node(page, node_id, label):
    # Nodes are drawn on a canvas in the real app, so tests find them through the map's API.
    pos = page.evaluate("id => mapApi.screenPosition(id)", node_id)
    page.mouse.move(pos["x"], pos["y"])
    expect(page.get_by_role("tooltip")).to_have_text(f"Open {label}")
    page.mouse.click(pos["x"], pos["y"])


def test_select_two_nodes(app_url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 800, "height": 500})
        cdp = page.context.new_cdp_session(page)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": PHONE_CPU_SLOWDOWN})
        page.goto(app_url)
        tap_node(page, "a", "Alpha")
        expect(page.locator("#inspector-title")).to_have_text("Alpha")
        tap_node(page, "b", "Bravo")
        expect(page.locator("#inspector-title")).to_have_text("Bravo")
        browser.close()
