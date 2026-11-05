# QA conduct: how the user expects a tester to behave

Receipts are the user's words; square brackets replace the names of their machines. The browser host, the virtual
tablet, and the user's own laptop, phone and tablet are described in devices.md and named in the user's environment file.
The `phone-debug` skill covers the mechanics of borrowing a device; the rules below are the etiquette.

## 1. Verify it yourself; ask the user only for judgement
- Measure what can be measured, including smoothness, frame time and latency, and never ask whether it feels smooth. "I should be consulted for visual/design look-and-feel, but you and the workers are perfectly equipped to answer mechanical questions."
- Do your own headed pass before you involve them. "I think you should try testing it for yourself on the [browser host] headfully."
- Fix or file what you notice instead of leaving it as their call or dropping it. They pasted back an agent's note that left two iPad defects as `both your call`, asking "Did we fix this?"
- Before you hand over a URL, command or checklist, run it from the user's real starting state and quote the real output. "Before asking me to try the benchmark, the worker should probably ensure that it's fully working/bug free :)"; "I don't see that line or table to be honest, here's the bottom of the output:". Any file you name must exist where they will look: "I can't find the .json files for the original placement check".
- Re-check after every fix and every action the user takes. "They should be dead now - double check."; "Check again now."

## 2. Machines and browsers
- Run headed browsers on the browser host, never on the laptop. "Please run headed tests on the [browser host]." Headless and headed runs there need no permission: "you may use ssh [browser host] for headed or headless browser testing at your leisure."
- Cap browser-host use and keep the laptop free. "limit worker processes to 7 vCPU and 16GB RAM maximum"; "The worker's Python processes are pegging my laptop at 100%."
- The laptop is only for benchmarks that need its hardware, and you ask when one is due. "I'm fine with you asking me to do the benchmarks on the laptop since that's disruptive."
- Leave the user's own Chrome alone: don't open tabs in it, read its tabs or drive it. When they asked the agent to "Clear the site data", it re-served the old review ports instead of touching their Chrome, and they interrupted: "Why are we opening localhost:7479?" Don't leave site data or service workers behind in the user's browser either. They review in Chrome on the laptop (`Chrome`, picks).
- Don't break their session. Review servers that shared a cookie across ports unpaired them in the middle of testing: "I was interrupted in the middle of testing".

## 3. Phone and tablet etiquette
- Use the browser host and the virtual tablet first, and borrow a real device only when nothing else can answer the question. "We have a [virtual Android tablet]. Only ask for the phone/iPad/laptop if absolutely necessary." This supersedes "Alright, lets do it all on my device.", from before the tablet existed. When you do need a device, batch the checks into one request and say when you are done. With one free port, they swap cables: "let me know when the iPad run is done and I can switch it out with the phone."
- Time-box each borrow and keep input inside the page under test. "Keep your test to <10m to give me the phone back."; "you should always ensure only the app/web page under test receives input events". When you finish, return to the app that was open before.
- Keep the device awake without asking them, then restore its settings. "it's disruptive to always have to unlock the phone"; "Please remember to bump the lock screen/sleep timeouts while you work and restore them once you're done."
- Control rotation yourself where you can. "It's disruptive to have to rotate my mobile devices."
- When a physical step is needed (unlock, trust, USB debugging, rotate), diagnose first, ask once, then wait for their reply ("Trusted, go ahead.").

## 4. Test data, cleanup and side effects
- Test on an isolated copy of real data, never on the live store. "(In a cloned/isolated checkout of course)". For remote state, use the named sandbox they gave you: "using [a sandbox remote] as remote storage (clean it up after)".
- Clean up in teardown, whether the run passes or fails, including projects, settings and tabs left in the user's real folders. "Please clean up - once, as a one-time cleanup - and always, after the test is done."; "Clean up your worktree too." Test pages must not write into the user's real saved preferences.
- No real OS notifications or other outward effects without a good reason and asking first. "Please avoid sending real/true macOS notifications without good reason + asking me first." Record or stub them instead; scripted journeys never raise them (SKILL.md step 2).
- Try irreversible actions on a trial run first, and show the result before the real one. "Hold on, let's do some trial imports first before we do the real deal."
- Keep anything identifying out of public repositories, including screenshots, fixtures and host names. "Never put anything identifying or anything that shouldn't be public there." Never read or print secrets: "WITHOUT reading the secrets".

## 5. Presenting evidence
- Put images in the chat itself; if the user is on a phone, send screenshots, not a page that opens on the Mac. "I'm on mobile, so close the browser walk through and just send it as screenshots."; "Can you give me some screenshots as a walk through of the UI?"
- Show pictures before asking them to choose. "I need to see what they actually look like"; "can you show images of boxes vs threads?" Include today's version: "Do both and compare against today."
- Galleries default to the real project data, with fixtures only for edge cases the real data lacks. "Whenever you show me a gallery demo, let's default to using the real acyclic task DAG".
- Keep artefacts sharp, uncluttered and in one tab. "Turn it into a real gallery so when I click on a small thumbnail it pops up the image at full res."; "The 2026-10-31-compare folder is very cluttered".
- On a phone, give them one tappable link per variant. "remember, I'm on mobile now so it's annoying to copy-paste." When they want to try the UI themselves, offer a live server on a throwaway copy and keep it up until they are done: they picked `Keep it on during M7's reviews` over the recommended option (pick).

## 6. Reporting
- Cover three things: your opinion of the UI, the bugs you found, and features worth adding. "It should report what it thinks of the UI, any bugs it encounters, and any potential valuable new features/changes." Fix bugs; collect feature ideas for the user to decide on: "(don't plan them yet, collect them and I'll decide when to cut a milestone for them)".
- Lead with what you need from them, in plain words, and explain jargon. "It's not clear what you're waiting for."; "I don't quite understand your caveats"; "What's the G1 question?"
- Give phone reviewers a short numbered checklist, which they answer item by item (`1. Cellular`).
- Batch the findings and don't flood them. "I'm getting a little overwhelmed with the cards, can you brain dump them".
