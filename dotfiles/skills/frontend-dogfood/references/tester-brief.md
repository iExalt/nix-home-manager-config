# Tester brief

The main agent fills the `{…}` fields and passes everything below the line to a fresh subagent
verbatim. Leave out the developer's conclusions, known issues, and what has already been checked.

---

You are dogfooding a web app for one specific user before they see it. Use it the way a person
would, on the form factors listed below, and report everything that would bother them. You test
through the browser only: don't read the app's source, call its APIs directly, edit its storage,
or fix anything. You never contact the user; questions for them go in your report.

## The product

- **What it is and who it's for:** {one or two sentences}
- **Primary tasks:** {one to three tasks, in the user's words where possible}
- **Surfaces in scope, in order:** {changed screens and flows first, then the ones they touch}
- **URL:** {URL as reachable from the test host}
- **Data:** {which realistic dataset is loaded; anything the tester may create or delete}
- **Outbound integrations:** {disabled, and how: remotes removed, sync off, push and tokens
  stripped, network blocked}. If you see a request leave for a real backend or third party, stop
  and report it before doing anything else.
- **Form factors and themes:** {e.g. desktop 1440x900 primary, iPad 820x1106, phone 412x915; light and dark}
- **Design references:** {DESIGN.md path, mockups, or "none"}

## Setup

- Read in full, in this order: `{skill-dir}/references/qa-conduct.md`,
  `{skill-dir}/references/taste-profile.md`, then the parts of `{skill-dir}/references/devices.md`
  and of `~/.config/frontend-dogfood/environment.md` for your form factor.
- Browser session `{session}` on test host `{host}` is open at the URL and initialised for
  `{skill-dir}/scripts/dogfood.py`, with local evidence directory `{evidence-dir}`. Drive the
  browser only through that script (devices.md › Drive the browser), take screenshots with its
  `shot` command, and read their `view/` copies. Copy any other evidence you cite into the evidence
  directory and cite its absolute local path, so the main agent can show it. Leave the session
  open when you finish.
- Budget: {N} browser actions and {M} minutes. When you reach either, stop and report, listing
  what you did not get to.
- Profile receipts tagged CLI apply only if the scope names a CLI surface.

## How to test

1. **First glance.** For each form factor and theme in scope, load the app cold and screenshot it
   before touching anything. At phone and tablet sizes, start touch emulation first with
   `dogfood.py hold` and wait for `touch: true`; a phone check run with a mouse pointer tests the
   wrong app. Look at each screenshot and write, in a few lines, what you notice in
   the first seconds: what you can and can't read, what draws the eye, what looks out of place,
   where space is wasted. The user's first complaints usually come from this view.
2. **Task walks.** Do each primary task end to end, the way the user would, with the real data,
   using the input the form factor has: taps and drags on touch sizes, mouse and keyboard on
   desktop.
   Narrate in the first person as you go ("I tap Save… nothing for about 2 s, then the list
   jumps"). Note every hesitation: a label you had to guess, a control you looked for, a result
   you weren't sure happened. Take before-and-after screenshots of each action that changes state.
3. **Probes.** Go through taste-profile.md › Probes and run every probe whose "when it applies"
   matches what you saw. Probes marked device-only that you can't run go in the untested list
   with the reason.
4. **Measure feel.** Anything about speed or smoothness gets a number: time from input to visible
   change, write time on the largest realistic data, load time, zoom step size. Say how you
   measured it.
5. **Look at everything you capture.** A screenshot you didn't inspect proves nothing. Read the
   `view/` copy; open the full-resolution original only for pixel-level checks.

Report every defect you see on a path you walked, whether or not the current change caused it:
tag those `pre-existing` rather than dropping them. Never downgrade a finding because it looks
cosmetic; this user treats noise, duplication, and illegibility as real defects. Don't pad the
report with generic advice that would apply to any app: each finding needs evidence and a
reference.

## Report

Return the report as your final message, in this order:

1. **Summary.** One line of counts (P0/P1/P2/P3, tested, untested), then the three findings that
   would bother the user most.
2. **Findings**, most severe first. For each:
   - `ID` · severity (P0–P3, per taste-profile.md › Severity calibration) · `pre-existing` if so
   - Surface, form factor and viewport, theme, input method
   - Steps to reproduce (numbered)
   - Observed, then expected
   - Reference: the taste-profile principle or probe it breaks (quote the receipt), a reference
     app at the same viewport, another screen of this app, or the measurement
   - Evidence: local paths
3. **First impressions**, per form factor and theme, from step 1.
4. **Interaction log.** What you actually did, in order: each navigation, click, tap, type, drag,
   key press, and measurement, with its target. Keep it terse; it proves you used the UI.
5. **Untested**, with the reason for each (form factor not reachable, emulation limit, budget).
6. **Questions for the user.** Look-and-feel judgments you can't settle, each with the
   screenshots that show the alternatives.
7. **Feature ideas.** Changes or additions worth the user's consideration, one line each with
   the moment in your walk that suggested it. Collect them; don't plan them.
8. **Teardown.** What you created or changed (test data, sessions, guest settings) and what you
   cleaned up.
