# Taste profile: the user

Load this whole file before a dogfood run. It says what this user notices in a finished UI, so you can find it first.
Receipts are the user's own words. Strength marks: no mark means explicit and seen more than once
or in both projects; **(once)** means one explicit remark; **(picks)** means it rests on options they chose from an
agent's list, which is weak evidence. Illustrations come from a bead-pattern editor (canvas grid, colour
palette, bill of materials, image import; desktop, iPad, phone) and Acyclic (work-orchestration PWA with a graph Map,
panels and a needs-you queue, plus a CLI).

## 1. Who is judging

- A backend engineer who expects you to bring the design vocabulary: "As I mentioned before I'm no front-end engineer."; "I'm not a UX guy so I don't know what a better option would be." They often feel a problem before they can name it: "I can't quite put into words why the app doesn't feel good to use unfortunately." Name it for them, with a screenshot.
- They judge by using the UI on their own devices: a laptop in Chrome (Firefox also supported), an Android phone, and an iPad with a pen; the user's environment file (see devices.md) lists the models. Which device is primary depends on the project (the pattern editor started desktop-first, Acyclic is phone-first), so read the brief.
- What they look at first: whether the first view is readable without zooming, whether the dark theme is really dark, where space is wasted, whether states can be told apart, whether anything is repeated or noisy, and whether the first click responds at once.
- How they talk: acceptance is terse (`Sure`, `Yep.`, `LGTM now.`); rejection is blunt (`Not good.`, `not usable`, `far too`, `???`, `Whoa Nelly`). Many defect reports arrive as puzzled questions, such as "Why does clicking draw a black circle on the map?" Treat any question of that kind as a bug. Hedged ideas really are hedges: "Not a demand, but something for us to consider."
- Reference points: Paint for instant direct drawing and opening on a blank canvas; Linear for a quiet professional web app with comfortable reading size; Termius for a phone terminal that feels native; GitHub for plain-text progress; the Claude and ChatGPT phone apps for chat-first entry; docker, git, aws, uv and cargo for polished defaults, grouped help and helpful errors. Paseo is the negative reference for its phone terminal and cost tracking. Compare against a reference at the same viewport rather than against your own taste.
- They change their minds once they see the real thing (section 5). The latest ruling wins, and a rule they stated before seeing a build is only a hypothesis.

## 2. Principles

### First-glance legibility and density
- The default or fitted view is what gets judged, so it has to be readable without pan or zoom. "First view text is far too small."; "much more legible without requiring me to pan and zoom a bunch now".
- Judge text size and contrast against Linear, not by eye alone. "compare with a screenshot of Linear at the same browser dimensions"; "I still need to strain harder to read it than Linear."
- Put what needs action first, top-left, and keep lists in the same order as the layout they describe. "the first threads I/we need to action on to kickstart the project".
- Large sets should be scanned, not scrolled: a hue-sorted grid with neutrals grouped, and lists in natural order. "rather than making me scroll through a huge list?"; "The lists should be sorted in a meaningful order i.e H1-H9 --> H10-H19 etc."
- A flat list of many top-level entries overwhelms them, so group it. "That's far to many top level commands, let's implement some command groups please". (once; CLI, but it applies to menus and toolbars too)

### Quiet visual design and noise
- The target is quiet and Linear-like, and they name clutter outright. "it's still very, very visually noisy/cluttered."; "Linear has some smashing good ideas - let's crib from them."
- Show each fact once per entry. "I don't like e.g the green 1 duplication at all." An agent had dismissed this one as cosmetic.
- Quieting one area can clutter another, so re-check the whole app after a restyle. "We redesigned the task view to be quieter, and now the `Needs you` panel is too cluttered."
- Child rows read as subordinate to their heading: smaller or muted, and set tighter. "The thread title should be more prominent, of course. The line spacing between each item should also be smaller to accentuate its subordinate nature."
- An accent that doesn't belong to the visual language reads as wrong. "it looks out of place in the new Linear-ish UI."
- Unstyled defaults on one long page read to them as `engineer UI`: "I think we definitely need to do a pass to rearrange the tools/layout of the page, tweak font size, etc."
- Where the UI depicts physical things, faithful beats decorative. "The `fused` bead looks closest to, well, a fused perler bead."; "looks a little duller/flatter than the bolder palette of the Mard beads".

### Colour, theme and dark mode
- Dark mode has to be dark everywhere, the main work surface included. "The main canvas area is still blindingly white/grey when using the dark theme. Not good."
- The theme follows the system, with a manual override kept out of prime space: `Follow the system` was picked in both projects against the recommendation, and `Move into more` was picked for the toggle. (picks)
- Selected and highlighted states have to look right in both themes. "The highlight on the selected task doesn't look good in light nor dark mode".
- Categorical colours should step continuously and never repeat. "Shouldn't hue degrees be continuous?"; "so that we don't have identical colours?"
- A colour that shows membership is always on, not only on selection. "We should always colour each task according to its thread, not just when they're clicked on/highlighted."
- Encoding colour error with a single-hue ramp loses the direction of the error. "the heatmap should be a bit redder for that pixel, rather than a single-color gradient." (once)

### Immediacy, latency and feel
- Direct manipulation should land in the same frame, like Paint. "Sub 100ms response times should be table stakes - why does clicking a cell take 300ms???"; "The app should feel like Paint."
- The bar is a frame, not 100 ms: "100ms is not even an acceptable floor, to be honest. I should be able to drag my cursor over the canvas, drawing a line of beads, more or less instantly."
- Feel can be measured, so measure it instead of asking about it. "Yes, this is a look-and-feel question, but it's something that can be measured and tested."
- Write latency is judged separately from render speed. "Panning and zooming is fine. It takes far too long to add a new item though, a few seconds of delay."; "7s is indeed far too long to wait for simple CLI operations on 3500 items, let alone more."
- Load time and layout time on the phone count as well, and so does a cold load. "take far too long to lay out"; "Why does it take so long to load the app".
- Zoom steps can feel sluggish: about 3% per wheel notch was too slow and about 12% felt better. "Zooming is a bit too sluggish - how much does each scroll wheel tick/increment zoom by?" (once)
- Dropped or doubled keystrokes make a UI unusable. "Keys press more than once when I hit them once."
- A setting changes on screen at once and syncs in the background; a loading state after a change is a defect. "Changing one of those settings causes a brief loading screen - not good. I think the change should be reflected in the UI immediately and sync in the background to not lock the UI."
- Don't buy speed with a worse desktop look; fall back only on touch devices. "Can we only drop down to the fast behavior on non-desktop devices?" (once)

### Direct manipulation, gestures and input methods
- On touch, pinch zooms every zoomable surface in every mode. "Pinch to zoom isn't supported on mobile - that's a P0."
- A one-finger drag pans, even when it starts on an item, and moving an item needs an explicit mode. "it kept dragging the boxes instead of panning."
- The pointer target tracks the cursor while the button is held, Escape releases it, and a middle-click drag pans. "The targeted pixel should move with the cursor until the mouse clicks on a pixel."; "can we make middle-click-drags on the canvas pan?"
- On desktop, hovering reveals relationships; making the user click is worse. "I really like how hovering over a thread in the threads view showed the connections, whereas we have to click to see them on the map."
- Pressing must leave no stray default feedback, whether a library focus ring, a tap flash or a circle. "Why does clicking draw a black circle on the map?"
- Edit modes have to work with a finger. "I can't test link well out on the phone."
- A toggle in a menu leaves the menu open. "When I open the triple dot menu and touch a checkbox, it closes the menu. I don't think this is good UX."
- Keyboard furniture (key chips, shortcut hints) stays off a touch device until a physical keyboard is used. "Don't show keyboard shortcuts ... on mobile unless a keyboard is plugged in."
- The soft keyboard must not cover primary actions. "Save and cancel are hidden a bit behind the text prediction bar for my keyboard."
- With a pen, the pen paints and the finger moves the view once a pen has been seen; they kept this as built and declined a palm guard. (picks)

### Panes, layout and wasted space by device class
- Desktop should use its width and show several panes, not a stretched phone layout. "there's a ton of void space on the right, even when the `Needs you` panel is open."; they asked that desktop be less `mobile-y`.
- On a tablet, panels stay proportionate and no dead bands of chrome are allowed. "The right panel is far too wide for the iPad"; "On an iPad, we shouldn't waste space like that."
- On a phone, every stacked pane has to be usable on its own: about 136 px panes on a 360 px phone got "No, that's not usable."
- Chrome and panels leave the main surface most of the screen. Size controls by their touch target, not by padding added around it, and judge the elements, not only the text, against Linear and Slack on the same phone. "the Acyclic UI just seems comically... big? It's like if I turned my Android UI scale all the way to "old person size""; "This hurts especially when browsing half the map and half an item - the map doesn't have a lot of space."
- Open straight onto the working surface, put secondary flows in dialogs, and restore the last session. "When I navigate to the app I want to land on the blank canvas."; "can we reload the user's last project if they had one open?"
- Collapsible panels: the control sits inside its panel, a cue shows how to bring the panel back, and hide and show sit in the same spot. "Can we make both the sidebars collapsible from a button inside each sidebar, not at the very top?"; "Not a fan of the hide arrow being at the bottom but the show arrow being at the top."
- Diagrams should be orderly, mostly vertical and shaped to the screen. "it should roughly fit the screen's aspect ratio."; "or better yet, it should be centered since both columns". (the second is a nitpick)
- Sibling labels align and centre alike, checked in pixels. "color picker isn't centered like the other tool names"; "Can you check the pixels?"
- Icons and badges centre on the text they sit beside, not on its line box. "the alignment of the colored thread circle seems to be a smidgen too low? The alignment of the icons for task state also seem to sit below the text line."

### Defaults, automation, undo vs confirm
- Don't make the user choose what the app can detect: detect it, then let them override. "I should not have to choose what type of image I'm importing, the application ought to try to figure it out, and if it gets it wrong, users can manually pick."
- Imperfect input degrades the result but doesn't block it. "we should use them as a guideline for bead types, but they shouldn't block us."; "In that case we shouldn't mark all beads as uncertain."
- Make bulk actions one click and undoable, with undo preferred over a dialog. "Undo/redo bulk actions works and is fast." They chose `No dialog` for bulk accept (picks).
- Discarding the user's own edits needs a confirmation or a one-step undo. "Features work, but I don't think I was ever asked before resetting."
- Lots of manual input is itself a failure. "It required a completely excessive amount of user input".
- Prune features that are marginal or mechanical. "I think we added a few too many features that aren't useful out of the box"; "Honestly, word matching is worthless." (CLI)

### State clarity and self-evident meaning
- States should be distinguishable at a glance. "We need to be able to tell between completed, in progress, ready to start, and blocked phases/tasks."; on the redesign, "there's nothing to tell them apart."
- Show uncertainty plainly. "make sure it's displayed in a striking way so the user knows what they might have to edit."
- Derived and summary state must be correct on real data. "all threads are marked as state backlog even though some of them are in progress".
- A first-timer should understand every mark, section and control. "I needed to infer from context what the sections meant."; "it's super unclear what the little red dot for `Tracker-assigned ids` means"; "I have no idea what `Starts with` means in the context of a thread.".
- Only one thing should look selected or focused at a time. "doesn't un-white-outline nor un-radiobutton the original"; "I can focus on a phase but also a thread at the same time - I think this is confusing."
- Counts and labels must match what is visible. "Why do these `Needs you` items say Approve X items when I can only see one linked?" Hide a zero count: "Yes, hide the 0."
- Selection should propagate to related views. "When I click on a task, it should highlight the thread it's in on the left as well as the phase it's in."
- A queue entry should be actionable without a second lookup. "Yup, needs should show output similar to `acyclic list`." (CLI)

### Consistency and papercuts
- Papercuts are the quality bar. "All these small items are the difference between perfection and a CLI that's a joy to use versus death by a thousand papercuts."
- Use one name per concept on every surface (section 5, `Needs you`).
- Repeated rows keep the same element order, and lists follow the canvas order. "Let's flip the order of the icon, title, thread ID to thread ID, title, icon to match the left bar."; "It doesn't match the left to right/top to bottom layout of the phases on the map itself".
- A navigation behaviour works from every entry point, not just one. "Clicking threads on the left bar still doesn't take me to the map and focus on the thread. Is that intentional?"
- Something the user creates is shown where it landed. "Creating an item shold change tabs to the map and show me where the item was placed."
- Follow the conventions of polished tools. "Bare `acyclic` shouldn't print an error message, it should print `--help` to be consistent with other CLI tools."

### Copy and labels
- Labels say what happens in plain words. "`Project management: its agent's edits to approved scope apply at once` is also a meaningless/super confusing checkbox"; "What's the difference between the various `import as` modes?"
- Errors and status are written for humans, never as leaked plumbing or key names. "The whole unblock tab is a bit confusing."; "What does `waiting step-2-5 why open` mean?"; they asked for RFC3339 timestamps over unix time.
- Plain text beats glyphs for progress. "Alright, no glyphs, let's go with GH and use text."
- User content renders faithfully, including backticks, code and long ids. "it's showing weird accents on the vowels."
- Short labels win unless they collide with another term. They first picked `Review`, then chose `Needs you` everywhere. They also preferred precise categories to collapsed ones (`Exact seven`). (picks)

## 3. Severity calibration

- **P0, unusable or blocking on a target device.** This covers a missing core gesture ("isn't supported on mobile - that's a P0"), a view that can't be used at a supported size ("No, that's not usable."), a blank page at the URL handed over ("just a blank page"), doubled keystrokes ("unusable and glitchy"), core edits far over a frame budget ("why does clicking a cell take 300ms???"), silent data loss ("This seems like a bug."), and a core step the user can't complete ("Bug: after choosing a color for placement, I can't pick another").
- **P1, noticed at first look; fix before handover.** This covers unreadable first views, bright surfaces in dark mode ("when using the dark theme. Not good."), states that can't be told apart, wasted space on tablet or desktop, actions under the keyboard, writes that take seconds, duplication and noise ("the green 1 duplication at all"), navigation that half works, and unexplained marks or jargon. Agents have tended to file these as cosmetic. This user does not.
- **P2, papercuts.** This covers misalignment of a few pixels, order mismatches, off-centre labels, mis-rendered inline code, zoom step size and visible zero counts. They want these fixed in the same pass, not filed: "No need for tracker items, just discuss and fix them." Anything you notice and leave for later comes back: "Did we fix this?"
- **P3, note it and don't push.** This covers hedged ideas ("Not a demand"), polish they decline ("Nah, it's fine."), rare real-device edge cases already accepted as known (`No fix; note it`, picks), slowness specific to one machine ("Let's mark the finding down but leave it for now."), environment checks they waived ("Let's skip the outdoor and night checks"), and scope they have no use for ("I don't have a use case for non ASCII/Latin titles").
- Large issues outside the current change are real but get their own item: "Big one. Add that as a side item". Interim acceptance is not the final bar: "Much much better, I think that'll do for now." came at 300 ms, and the target was still Paint. Gate on realistic workloads, not the largest synthetic ones (they chose `Art 104 × 104` for the phone gate, picks).

## 4. Probes

Format: **when it applies** / device and input / action / check. Run each on real data first (section 4 of qa-conduct).

1. **Any URL you hand over.** Fresh browser profile, desktop. Open exactly that URL (both `localhost` and `127.0.0.1`), wait for network idle, then repeat after a server restart or dependency change. Fail on a blank page, any console error, any non-2xx module request, or a slow cold load.
2. **Opening the app.** Desktop and phone, cold. Count clicks to the working surface; any splash, landing or picker in between is a finding. Reload mid-task and check that the last project or view comes back.
3. **First view legibility.** Phone at 360-412 px portrait, laptop at 1280-1440 px. Load real-size data and read the first fitted view. Screenshot a reference app (Linear) at the same viewport and compare size and contrast; that comparison is the check. As a rough tripwire, text computing below about 11 px on screen is suspect (heuristic, not the user's number).
4. **Edge content and scrollbars.** macOS with scroll bars set to always show, or Chromium with classic scrollbars, since Playwright's overlay scrollbars hide this. Scroll a larger-than-viewport surface to each edge and check that rulers, last columns and sticky footers stay unclipped.
5. **Dark theme.** Desktop and phone, theme set to dark both manually and via the system. Take a full-window screenshot and flag any large light region (canvas surround, board, rulers, table rows, code blocks). Also check selected and hover highlights in both themes. Judge by eye; pixel-equality specs have encoded this defect before.
6. **Noise and duplication.** Every list entry, card and panel, at desktop and phone width. Check that no fact (badge, number, title, colour) appears twice in one entry, that neighbouring rows share the same background treatment, that no accent clashes with the palette, and that zero counts are hidden. Re-check every panel after any restyle.
7. **Self-evident meaning.** Run a first-time walk with no docs, on real data. For every section heading, dot, badge, checkbox, mode option and error message, write what you think it means. Anything you can't state, or that uses internal names or harness errors, is a finding. Optionally have a cheaper model do the same walk.
8. **State at a glance.** Overview zoom on real data with every state present (done, in progress, ready, blocked, archived, unsure). Name each item's state without opening it, then repeat in greyscale to catch colour-only cues. Cross-check every parent's derived state against its children.
9. **Counts versus content.** Any badge or button carrying a number. Compare the number with the items it refers to and with what is visible.
10. **Single selection.** Radio groups, auto-detected options, focus and selection across sidebar and canvas. After auto-detection or a second selection, exactly one option should look selected, with consistent outline, radio and highlight. Two focus scopes at once is a finding.
11. **Selecting twice in a row.** Every picker, combobox and filterable list. Pick A, reopen and pick B, then click the selected item again. The full list must be offered each time, and a repeat click must not silently toggle state.
12. **Large-set pickers and lists.** Any list over about one screen. Count the scroll screens needed to reach a target item. Check grouping (hue, neutrals first) and natural sort (A2 before A10).
13. **Click-to-response latency.** Emulatable. Headless Chromium and Firefox on the browser host, with real-size data, plus a 4x CPU throttle; laptop-GPU numbers come only from a benchmark the user chooses to run (qa-conduct section 2). Click a cell or item, then drag quickly across many. The change should land in the same frame and lines should be continuous, with dependent counts updating at once. Record p95 against 16 ms, not 100 ms.
14. **Write latency on big data.** Emulatable with throttling; confirm on device when available. Phone or 4x throttle, the largest realistic dataset. Time each write (add, move, link, save) from tap to visible result with the form closed, separately from pan and zoom smoothness. Seconds is P1.
15. **Load and layout time.** Device-only for the real number; throttled emulation gives a lower bound. Real phone over cellular, or throttled CPU and network. Time from navigation to the first usable view. Don't trust laptop timings.
16. **Pointer tracking.** Desktop mouse. Press and hold, then drag across cells, off the edge and back, and over rulers. Hover targets should track every frame, Escape should release, and a middle-drag should pan. Screenshot during pointer-down to catch stray press circles, focus rings or tap flashes.
17. **Wheel and trackpad zoom.** Emulatable. Send synthetic `mouse.wheel` steps (deltaY 100) and ctrl+wheel as a stand-in for trackpad pinch; measure the scale ratio per step and check that zoom anchors at the pointer. About 3% per notch was too sluggish and about 12% got "Zoom feels better." (once).
18. **Touch gestures.** One-finger drags emulate well; pinch needs CDP multi-touch or a device, and pen needs a device. Phone and tablet (real device or touch emulation). With every tool or mode active, pinch-zoom on the canvas, then make a one-finger drag that starts on an item. The view should zoom about the midpoint and pan from anywhere, items should move only in an explicit mode, and link or move targets should be finger-sized. If there is a pen, check that pen and finger roles match the design.
19. **Soft keyboard.** Device-only; in emulation, shrink the visual viewport by a keyboard's height as an approximation and report the rest as untested. Android Chrome with Gboard (prediction bar on), on every form. Focus a field and check that Save, Cancel and Submit stay visible above the bar. Close the keyboard and drag within about 200 ms and again after 1 s: the view must not re-fit under the finger.
20. **Typing fidelity.** Device-only. Text inputs or terminals on Android with Gboard autocorrect and swipe typing, plus 300 ms added latency. Type, backspace into a committed word and swipe a word. Each character should appear once and the screen should match the backing value.
21. **Phone stacked panes.** Phone at 360x640 (largest display size). Open every multi-pane mode and measure each pane's usable height and try to do that pane's job in it; a pane you can't work in is a finding (about 200 px is a heuristic tripwire, not the user's number).
22. **Tablet proportions.** iPad upright 820x1106 and sideways 1180x746. Measure side-panel widths against the canvas and the gap between the title bar and the content, then read every toolbar label for clipping and centring. Empty halves of sheets are findings.
23. **Desktop width.** 1440x900 and 1920x1080 with panels open and closed. Content should fill the width with no large void, and the layout should be multi-pane rather than a phone column.
24. **Collapsible panels.** Desktop and tablet. Fold each panel: the control sits inside the panel, a visible cue shows how to bring it back, the unfold control is where the fold control was, and the main surface doesn't jump.
25. **Order and naming consistency.** All surfaces (lists, panels, notifications, dialogs, CLI output, docs). Grep the visible strings for two names for one concept, compare element order in repeated rows, and compare sidebar order with the canvas reading order.
26. **Navigation from every entry point.** Click the same entity from the overview, sidebar, queue and canvas. Each should land on the same focused view with the panel open.
27. **Relationship highlighting.** Desktop and phone. Select, and on desktop hover, each entity in every view. Its links, group (thread) and parent (phase) should highlight in its colour everywhere, membership colour should be on even without selection, and on desktop hover alone should reveal connections.
28. **Text rendering.** Real titles with backticks, inline code, long ids and URLs, at 1x and 2x DPR. Look for combining-mark artefacts, split columns, overflow and clipping on phone.
29. **Pixel alignment.** Screenshot at 2x or 3x DPR. Measure label and value baselines in rows whose value starts with an icon or badge, and check that sibling labels are centred alike. Measure each icon's and badge's vertical centre against the x-height centre of the text beside it; more than 1 px off is a finding.
30. **Destructive and bulk actions.** Make an edit and let it sync, then trigger reset, re-apply or clear. Expect a confirmation or one-step undo, including while edits are still in flight. Bulk actions should be one click, undoable and fast.
31. **Imperfect and real inputs.** Every sample the project ships, plus degraded variants (cropped, missing legend, empty fields). Nothing should block. Compare the result against the source (counts, hardest regions, colour profile and saturation). Every cell or field marked uncertain is a finding.
32. **Browser state restore.** Desktop Chrome. Duplicate the tab and use back and forward after a file was chosen. Controls must be enabled or the form reset.
33. **Colour sequences.** Any categorical colouring. List hues in order and check that steps are continuous with no identical pairs.
34. **Screen share of the main surface.** Phone at 412x915. With each panel at its first height, and with each menu open, measure the share of the screen left to the main surface (Map, canvas, list). Under about 55% is a finding; so are menu rows or panel facts spaced well beyond their 44 px target. Compare element sizes with Linear or Slack on the same viewport.
35. **Menu toggles.** Every menu holding a checkbox, switch or select. Flip each one, by tap and by keyboard; the menu must stay open and show the new value at once.
36. **Heading and child hierarchy.** Every grouped list (a queue entry's items, a panel's sections). Compare the heading's size, weight and colour with its rows' and the row pitch with the heading's gap. Equal treatment is a finding.
37. **Settings latency.** Every setting and small edit in panels and menus. Time from the change to the screen showing it; any loading state, spinner or lock of the surrounding UI is a finding.
38. **Created things shown.** Add each kind of thing from every view and form factor. The app should go to where it landed, selected and in view.
39. **Keyboard furniture on touch.** Phone and tablet with touch emulation and no key events. Open search, menus and panels; key chips or shortcut hints are a finding. Then press a key on a hardware keyboard and check that they appear.

## 5. Conflicts, reversals and conditions (by date)

- **2026-10-03 to 10-04, accessibility.** They first said "Don't worry about silly compatibility things like IE6 or ARIA for now.", then picked shortcuts, focus and contrast for M7 (picks). Check keyboard focus and contrast; don't file deep ARIA or legacy-browser findings unless the brief asks.
- **2026-10-03 onward, device priority.** "The webapp is mainly for desktop browser usage", then tablet and phone became full targets for the pattern editor. Acyclic is phone-first: "I gravitated towards Paseo because it supports remote access from my phone". Take priority from the project brief.
- **2026-10-04, transparency.** They asked for all-transparent table rows, then the same day accepted solid sidebars: "that's OK." The goal was a consistent background, not transparency itself.
- **2026-10-04, confirm vs undo.** Reset without asking was a bug, while bulk accept got no dialog (picks). Discarding the user's own work needs a confirm or undo; applying suggestions needs only undo.
- **2026-10-04, latency.** 300 ms was accepted for now while Paint stayed the target. Interim acceptance is not a pass.
- **2026-10-04 to 10-05, panel controls.** Inside the panel, then an arrow to re-expand, then both arrows at the top. Expect several rounds; check all three conditions together (probe 24).
- **2026-10-12, space.** "On an iPad, we shouldn't waste space like that." versus "Nah, it's fine." for slack left by whole-number Fit steps. Bands of empty chrome are defects; small slack around content is fine.
- **2026-10-16 to 10-17, output default (CLI).** They wanted JSON by default, then approved pretty output in a terminal with JSON when piped. Human-facing defaults should be readable.
- **2026-10-17, local echo.** They called it a "killer feature" in the morning, then said "I can't tell the difference between echo off and on" the same day. They care about typing feel; measure it rather than A/B it blind.
- **2026-10-24 to 10-25, real device vs emulator.** Offered an emulator, they said "Alright, lets do it all on my device." Superseded on 2026-10-31 once a virtual Android tablet was available: borrow their phone, iPad or laptop only if absolutely necessary (qa-conduct section 3).
- **2026-10-30 to 10-31, naming.** They picked `Review` for the queue button, then `Needs you` everywhere once the collision was shown (picks). Consistency beats brevity.
- **2026-10-30 to 10-31, attention marker.** They proposed "an amber exclamation mark instead of a number", then rejected it as out of place in the quieter UI. A signal has to fit the current visual language.
- **2026-10-30 to 10-31, anytime column.** Right, then "Actually, let's move anytime stuff to the *left* rather than the right". Layout side preferences are unstable; flag them, don't enforce them.
- **2026-10-31, font.** They chose Inter, then "Inter looks a bit cold :joy: I take that back." Decide type from rendered screenshots, never from names.
- **2026-10-31 to 11-01, theme.** The app followed the system with no override; on 2026-11-01 they asked for a light/dark switch on the phone and chose System / Light / Dark in the menu, System by default.
- **2026-11-01, Needs you.** A layer over any view was the design; after using it they said "it feels like it should probably get its own view like overview/map/threads?" and chose a view.
