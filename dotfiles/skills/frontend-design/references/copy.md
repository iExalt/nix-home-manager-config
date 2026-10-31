# Interface copy

Merged from Anthropic's `frontend-design` skill ("More on writing in design", Apache-2.0),
Impeccable's `clarify` command (Apache-2.0), and Vercel's Web Interface Guidelines copywriting and
content rules (MIT). The opening principles are Anthropic's text verbatim; the rest is trimmed and
deduplicated.

## Principles

Words appear in a design for one reason: to make it easier to understand and use. They are design
content, not decoration. Bring the same intentionality and minimalism to copywriting that you would
bring to spacing and color. Before writing anything, ask what the design needs to say, and how it
can best be said to help the person navigate the experience.

Write from the end user's perspective. Name things by what users will understand in simple
language, not by how the system is built. A user manages notifications, not webhook config.
Describe what something is or does in plain terms rather than selling it. Being specific and
legible to new users is always better than being clever.

Use active voice as default. A CTA says exactly what happens when it is used: "Save changes," not
"Submit." An action keeps the same name through the whole flow, so the button that says "Publish"
produces a toast that says "Published." The vocabulary of an interface is the signposting for
someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to
fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never
vague about what happened. An empty screen is an invitation to act.

Keep the tone conversational: plain verbs, sentence case, no filler, with tone matched to the brand
and the audience. Let each written element do exactly one job.

## Message hierarchy

For each state, decide:

1. the one fact the user needs now;
2. the action available next;
3. supporting context that changes the decision;
4. the appropriate tone for this moment.

Say each idea once. If the heading already explains the state, the introduction should add new
information or disappear.

## By function

- **Actions.** Specific verb and object when the outcome is not obvious: "Save API key", not
  "Continue". Labels describe what will happen, not the gesture. Menu items that open a follow-up
  step end with an ellipsis ("Rename…").
- **Destructive actions.** Name the object and consequence. Prefer Undo over confirmation when
  recovery is safe; when confirmation is necessary, name the action on both the message and the
  button instead of "Yes", "OK", or "Submit".
- **Forms.** Persistent labels; placeholders are example values or patterns ending in an ellipsis
  (`+1 (123) 456-7890…`), never the label. State format and eligibility requirements before
  submission. Validation says what needs attention and how to fix it without blaming the user.
- **Errors.** What failed, why when known and useful, and how to recover: "Your API key is
  incorrect or expired. Generate a new key in Settings → API keys," not "Invalid API key." Never
  promise a cause or resolution the system cannot know. Treat privacy, payment, deletion, access
  loss, and blocked work seriously; warmth is welcome, jokes are not.
- **Loading.** Name the real operation and end with an ellipsis: "Saving…", "Generating report…".
- **Empty.** Distinguish first use, no results, filters, permissions, and failure, and give the next
  action.
- **Success.** Confirm the outcome briefly.
- **Help.** Prefer inline explanation; tooltips are a last resort. Helper text answers an implicit
  question instead of restating the control. Link text makes sense out of context.

## Mechanics

- Sentence case for headings, buttons, and labels unless the project already uses another
  convention consistently. (Vercel's house style is Title Case; that is a brand choice, not a
  usability rule.)
- Second person ("your projects"); avoid first person from the product ("I", "we") in UI chrome.
- Numerals for counts ("8 deployments"); a non-breaking space between a number and its unit
  (`10&nbsp;MB`) and inside shortcuts (`⌘&nbsp;K`).
- Typographic characters: `…` not `...`, curly quotes “ ” not straight quotes.
- Consistent currency precision within a context (0 or 2 decimals, never mixed).
- Keep nouns consistent: introduce as few unique terms as possible, and keep a short glossary when
  terms span the product.
- Avoid the generated-page tells: an accent on a single word in a headline, ALL-CAPS labels,
  eyebrow labels above every heading, `A · B · C` meta strings, and `→` appended to every link.

## Accessibility and localization

- Accessible names match visible labels and outcomes; icon-only controls need an `aria-label`.
- Do not rely on color, punctuation, or icons alone to carry the message.
- Alt text conveys the image's information; decorative images get `alt=""`.
- Write complete, translatable messages; keep variables structured so translators can reorder them;
  allow for expansion instead of abbreviating early.

## Verify

Read the whole flow in context, at the target widths and at 200% zoom, with long names and dynamic
values. The final copy is as short as it can be without removing meaning or recovery.
