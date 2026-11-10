# Patterns

Short, adaptable snippets for the rules in [../SKILL.md](../SKILL.md). Examples use Playwright
for TypeScript; the Python API has the same calls in snake_case (`page.get_by_role`,
`expect(locator).to_have_attribute`).

## A settled signal in the app

Clear the attribute synchronously in the handler that starts the work, and set it after the last
visual change. A generation counter stops an older, slower callback from marking newer work done.

```ts
// App code: the camera frames the selected node after its details load.
let generation = 0;
async function select(node) {
  const mine = ++generation;
  map.dataset.framed = "false";              // before any await, so a test can't see the old "true"
  showInspector(node);
  await loadDetails(node.id);
  await camera.animateTo(node, { duration: 250 });
  if (mine !== generation) return;           // a newer selection owns the signal now
  requestAnimationFrame(() => {
    if (mine === generation) map.dataset.framed = "true"; // animation done; runs before the next paint
  });
}
```

```ts
// Test: tap, then wait for the app's own signal before the next step.
await page.getByRole("treeitem", { name: "Billing" }).tap();
await expect(page.getByTestId("map")).toHaveAttribute("data-framed", "true");
await page.getByRole("treeitem", { name: "Invoices" }).tap();
```

For async regions, `aria-busy="true"` while loading also helps screen readers:
`await expect(list).toHaveAttribute("aria-busy", "false")`.

## Hold a response to force a race

Make the bad interleaving happen every time instead of under load.

```ts
let release!: () => void;
const held = new Promise<void>((r) => (release = r));
await page.route("**/api/preview*", async (route) => {
  await held;               // hold the response until the test chooses
  await route.continue();
});
try {
  await page.getByRole("button", { name: "Compare" }).click();
  // ...act during the window the race needs...
} finally {
  release();                // never leave the route hanging if the test fails
}
```

Before the fix, the test should fail on every run with the response held; after it, it should
pass.

## Starve the CPU

```sh
# Linux: run the suite on two cores, fewer than CI's four. --retries=0 so a retried pass
# can't count as a pass.
taskset -c 0,1 npx playwright test --retries=0 --repeat-each=10 --workers=4 tests/edit.spec.ts
```

```ts
// Chromium, any OS: slow the page's CPU fourfold.
const cdp = await page.context().newCDPSession(page);
await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
```

Record the machine, core count, throttle and load average next to every count.

## Count failures before and after

```sh
mkdir -p runs; pass=0; fail=0
for i in $(seq 30); do
  if taskset -c 0,1 npx playwright test --retries=0 tests/edit.spec.ts > runs/$i.log 2>&1; then
    pass=$((pass + 1)); rm runs/$i.log; else fail=$((fail + 1)); fi
done
echo "fail=$fail pass=$pass"   # read each runs/*.log: an environment error is not a flake
```

## Animations off in tests

```ts
const context = await browser.newContext({ reducedMotion: "reduce" });
await context.addInitScript(() => {          // survives navigation, unlike page.addStyleTag
  addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.textContent = "*,*::before,*::after{transition:none!important;animation:none!important}";
    document.head.append(style);
  });
});
```

The first works only if the app honours `prefers-reduced-motion`; the stylesheet covers the rest.
Keep at least one test with animations on if motion is part of the behaviour.

## A coordinate tap that checks its target

When you must tap a point on a DOM element (an absolutely positioned marker, a node drawn as a
`div`), wait until it holds still and is on top, then tap.

```ts
async function stablePoint(page, selector, quietMs = 150, timeoutMs = 2000) {
  return page.evaluate(([sel, quiet, timeout]) => new Promise((resolve, reject) => {
    const el = document.querySelector(sel);
    if (!el) return reject(new Error(`no ${sel}`));
    let last = "", since = performance.now();
    const start = since;
    const tick = () => {
      const r = el.getBoundingClientRect();
      const key = [r.x, r.y, r.width, r.height].join();
      const now = performance.now();
      if (key !== last) { last = key; since = now; }
      const x = r.x + r.width / 2, y = r.y + r.height / 2;
      const hit = document.elementFromPoint(x, y);
      if (now - since >= quiet && hit && el.contains(hit)) return resolve({ x, y });
      if (now - start > timeout) return reject(new Error(`${sel} never settled or stayed covered`));
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }), [selector, quietMs, timeoutMs]);
}
const { x, y } = await stablePoint(page, "#leaf-42");
await page.touchscreen.tap(x, y);            // needs a context created with hasTouch: true
```

This is a heuristic with a gap between the check and the tap, so prefer an app signal when one
exists. It sees only DOM rects: on a canvas, `elementFromPoint` returns the canvas while the
camera moves inside it.

On a canvas, wait for the app's settled signal first (cleared synchronously by the action, as in
the first pattern), then read the position from the app's own API and tap at once:

```ts
await expect(page.getByTestId("map")).toHaveAttribute("data-framed", "true");
const p = await page.evaluate(() => mapApi.screenPosition("leaf-42"));
await page.touchscreen.tap(p.x, p.y);
```

Polling the position until two samples match is only a quiet-window heuristic: it passes
before a late pan has started, so it misses exactly the motion that comes after a slow response.
Use it only after the app's signal, or over a window longer than the app's worst-case latency.

## Check what the browser emulates

```ts
const env = await page.evaluate(() => ({
  hover: matchMedia("(hover: hover)").matches,
  coarse: matchMedia("(pointer: coarse)").matches,
  touchPoints: navigator.maxTouchPoints,
  dpr: devicePixelRatio,
  viewport: [innerWidth, innerHeight],
}));
```

A phone run should report `coarse: true` and `touchPoints > 0`; a desktop run should report
`hover: true`. Headless Chromium has reported neither hover nor a fine pointer in past runs; if
yours does, launch desktop runs headed (for example under Xvfb) or set the Blink pointer and hover
flags (`--blink-settings=primaryPointerType=4,availablePointerTypes=4,primaryHoverType=2,availableHoverTypes=2`).

Wait for web fonts before measuring geometry: `await page.evaluate(() => document.fonts.ready)`.

## Prove motion

A screenshot can't show that a spinner spins. Sample the computed transform twice.

```ts
const angle = () => page.getByTestId("spinner").evaluate((el) => getComputedStyle(el).transform);
const a = await angle(); await page.waitForTimeout(170);
const b = await angle(); await page.waitForTimeout(230);
const c = await angle();
expect(new Set([a, b, c]).size).toBeGreaterThan(1);
```

The fixed waits are the measurement intervals, not guesses about readiness; two unequal
intervals avoid sampling exactly one full rotation apart.

## Native screens over adb

```sh
adb shell uiautomator dump /sdcard/ui.xml >/dev/null && adb pull /sdcard/ui.xml ui.xml
# Read the node's bounds by resource-id, for example bounds="[48,612][1032,744]".
bounds=$(rg -o 'resource-id="com.example:id/save"[^>]*bounds="[^"]*"' ui.xml | rg -o '\[[0-9,]+\]\[[0-9,]+\]')
read x1 y1 x2 y2 <<< "$(echo "$bounds" | tr '[],' '   ')"
adb shell input tap $(( (x1 + x2) / 2 )) $(( (y1 + y2) / 2 ))
# Dump again after anything that moves layout before the next tap.
```

`uiautomator dump` fails with "could not get idle state" while anything animates, so stop idle
animations in test builds. `adb shell input` bypasses the keyboard app, so it can't test IME
behaviour. Use `iExalt:phone-debug` for device etiquette and its focus guard.
