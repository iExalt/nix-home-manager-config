# Visual direction and craft

Merged from Anthropic's `frontend-design` skill (Apache-2.0) and Impeccable's craft floor,
Operate-mode depth, and new-work triage ("Decide what is already true") (Apache-2.0; trimmed and
deduplicated). Anthropic's design principles, calibration list, planning process, and restraint
paragraph are copied verbatim, with three exceptions: the studio-persona opening is dropped, the
"Consider written content carefully" paragraph is replaced by a pointer to copy.md, and the
restraint paragraph's quality-floor sentence moved into "Craft floor". One-line **Override**
pointers mark where SKILL.md › Conflicts differs. Load this when choosing or changing a visual
direction, and skim "Craft floor" before any UI edit.

The user's priorities win over novelty: on task surfaces, clarity, consistency, and task efficiency
come first, and distinctiveness shows up as precision. Where the brief or DESIGN.md pins a visual
direction, follow it exactly, including when it asks for one of the looks listed under
"Calibration".

## Decide what is already true

Read DESIGN.md, representative code, tokens, components, and assets before choosing anything.

- **Established world:** inherit it. A missing DESIGN.md does not erase a coherent identity already
  in code; document that identity instead of inventing a replacement.
- **Incomplete brand:** preserve confirmed assets and recognizable traits, then extend the system
  with the user for this surface.
- **Redesign:** preserve product truth, content, function, and constraints; replace the old visual
  world rather than polishing it. Never split the difference into polish on the discarded look.
- **No visual authority:** create a direction with the user using the process below.

A section, component, feature, or state inside an established surface inherits that surface. Never
turn a local addition into a new identity exercise.

## Ground the design in the subject

If the brief does not identify what the product or subject matter is, identify it yourself before designing, and confirm with the client. You can come up with one concrete subject, the design's audience, and the design's primary job, as a proposal. If there's any information in your memory about the client's preferences or context about what they're building, use that as a hint. The subject's industry, subject matter, materials, and vernacular are where distinctive visual choices come from — a design for a toy for girls aged 8–11 will be very aesthetically different from a dashboard for financial analysts. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is the first thing viewers will see. Open with the most characteristic thing in the subject's world, in the form that is most appropriate: a headline, an image, an animation, a live demo, an interactive moment, or other treatments. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the default treatment, so only use it if that's truly the best option.

Typography carries the personality of the page. You don't need a different typeface for display or headline text and body content: use one family or two, and if two, make them clearly distinct.

Choose your typefaces deliberately, not the default families you would reach for on any other project, and set a clear type scale following the default guidance of The Elements of Typographic Style with intentional weights, widths, and spacing. When type is used as a headline or visual element, use the type treatment itself as an active part of the design, not a neutral delivery vehicle for the content.

> **Override:** see SKILL.md › Conflicts › Typefaces.

Default to line lengths of less than 80 characters. Serif typefaces can have slightly longer line lengths; give serif body text slightly more line-height than a sans-serif.

> **Override:** see SKILL.md › Conflicts › Line length.

Avoid these default typographic treatments; they are the commonest tells of a generated page:
- Accenting just a single word or phrase in a headline, like putting one word in italic/bold or a different color.
- Using all caps for labels.
- Adding unnecessary typographic labels above content.

Visual structure is information. Structural devices like outlines, borders, numbering, eyebrows, dividers, labels, etc., encode useful information about the content rather than decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence — like a stepped process or a timeline. Before adding numbered markers, check the content really is a sequence.

Use non-user-triggered motion sparingly and deliberately, only to draw attention. A single orchestrated moment — one page-load sequence or one reveal — lands better than scattered effects; fade-and-slide-up entrances on each section and hover transitions on every card are the generic default and read as AI-generated. Motion that answers a person's action (opening, expanding, confirming) is welcome when it shows what changed.

> **Override:** see SKILL.md › Conflicts › Motion.

For copy, see [copy.md](copy.md).

## Calibration: the generated-design defaults

For calibration, AI-generated design right now clusters around some traits:
1. a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta or warm-clay accent (often near #D97757 — Anthropic's own Claude-interaction accent, so on a user's brief it reads as a tell);
2. a near-black background with a single bright acid-green or vermilion accent;
3. a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns;
4. the SaaS-card kit: content chopped into identical rounded cards, one border-radius on everything regardless of hierarchy, the same soft grey shadow (rgba(0,0,0,.1)) under each, and gradient washes as decoration;
5. template chrome that appears whatever the subject: a tracked-out ALL-CAPS eyebrow label above every heading; meta strings joined with middle dots ('A · B · C'); labels built as 'WORD — fragment' with a spaced em dash; tinted near-black (#0B0B0B, #111) standing in for black; a monospace face for small data labels; a '→' appended to link and button text.

All traits are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. As with a hired human designer, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Impeccable adds these defaults to the list. Each is legitimate only when the brief earns it:

- Same-size cards of icon plus heading plus text as the page structure. Cards are the lazy
  container; nested cards are always wrong.
  > **Override:** see SKILL.md › Conflicts › Cards.
- Gradient text; glass and blur as decoration; a colored `border-left` above 1px on cards, list
  items, or alerts; hard zero-blur offset shadows outside a world that is actually neobrutalist;
  zero-offset colored glows used as depth.
- Monospace as a costume for "technical" rather than for code, data, or measurement.
  > **Override:** see SKILL.md › Conflicts › Monospace.
- Eyebrow or kicker labels above headings; a system display face (Impact, Arial Black, the
  platform sans) as the display voice of a Persuade or Experience page; sketch-style SVG
  illustration; decorative `repeating-linear-gradient` stripes or grid overlays without a real
  canvas, map, or blueprint under them; geometric masks approximating a photographic subject's
  outline. Impeccable bans eyebrows outright; the rest are its Refuse-list defaults or Codex-only
  rules.
  > **Override:** see SKILL.md › Conflicts › Generated-look defaults.
- Unicode glyphs or emoji standing in for an icon system. Use a real icon library or authored SVG
  in one consistent stroke and weight.
- Sparklines, progress rings, and soft-shadowed rounded rectangles standing in for content.
- A modal for a task that needs neither interruption nor protected focus.
- Light or dark picked by category. Pick it from the use scene: who, where, under what ambient
  light.

## Process: plan, review against the brief, build, critique

Work in two passes. First, brainstorm a short design plan based on the client's design brief: create a compact token system with color, type, layout, and principles.
- Color: describe the core base palette as 4–6 named hex values.
- Type: the typefaces and their roles.
- Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Include alignment guidance; should the content be left aligned, center aligned, justified?
- Principles: the high-level guidance for what makes this page unique.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan.

On task surfaces (Operate mode in SKILL.md), keep the plan to the shell: navigation, work areas and
what each is for, the data the visitor reads first and its states, and one signature move. The
visual world lends type, palette, density, and that move; it never supplies the layout, navigation
model, or controls, which stay the platform's standard ones.

Record the agreed plan in DESIGN.md (see [design-record.md](design-record.md)) once the user
accepts it.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and an element-based selector like .cta). This can happen often with padding/margin between sections.

## Restraint and self-critique

Spend your boldness in one place. Let one element be the memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Critique your own work as you build, taking screenshots to review if your environment supports it — a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creatives have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## Craft floor

Check these on the built result, together, in each look at the render.

- **Contrast:** body and placeholder text ≥4.5:1, large text ≥3:1 (WCAG AA). On colored surfaces,
  tint secondary text from that hue rather than using gray. Interactive states (hover, active,
  focus) have more contrast than the rest state.
- **Depth:** shadows carry an offset and a soft blur; layered shadows (ambient plus direct) read
  more natural. Borders with shadows: see SKILL.md › Conflicts › Elevation.
  Nested radii: a child's radius is no larger than its parent's.
- **Spacing:** tight groups, generous separation, more space above a heading than below it. Align
  every element to something intentional: a grid, baseline, edge, or optical center.
- **Type:** body measure per SKILL.md › Conflicts › Line length, display at most 6rem,
  letter-spacing no tighter than -0.04em, balanced headings (`text-wrap: balance`), obvious scale
  and weight steps, numbers per Conflicts › Monospace. Run the real copy at every breakpoint and fix
  what overflows.
- **Motion:** how much and which properties, per SKILL.md › Conflicts › Motion; never scattered
  effects. Exponential ease-out from an already-visible default. Honor `prefers-reduced-motion` with
  a reduced variant that still shows state changes.
- **States:** hover, focus, active, disabled, loading, error, empty, plus real content, working
  controls, and responsive composition. See [states-and-edge-cases.md](states-and-edge-cases.md).
- **Browser surfaces:** selection color, caret, focus rings, underline offset, scrollbars, and
  `color-scheme`/`theme-color` all ship with defaults that belong to no design system. Theme them
  from the palette, but keep them standard in function.
- **Palette:** harmonious, with a small set of named roles; every color has a job.
- **Coverage:** every brief requirement is present and findable within seconds.

Build to this floor without announcing it: the user sees the result, not the checklist.

## Task surfaces (Operate and Read)

Familiarity is often a feature here. The test is whether a category-fluent user can trust the
interface immediately or must pause at every subtly-off component. Product UI's failure mode isn't
flatness, it's strangeness without purpose: over-decorated buttons, mismatched form controls,
gratuitous motion, display fonts where labels should be, invented affordances for standard tasks.
The tool should disappear into the task.

- **Typography.** One well-tuned sans family is often right. Use a fixed rem scale with a tight
  ratio (1.125–1.2), not fluid headings. Titles that come from user or system data (issue titles,
  error strings, file paths) stay at a modest heading size and wrap or clamp on narrow screens.
  Measure per SKILL.md › Conflicts › Line length.
- **Color.** Restrained by default. The accent marks primary actions, current selection, and state
  only, not decoration. Standardize a semantic state vocabulary: hover, focus, active, disabled,
  selected, loading, error, warning, success, info. A second neutral layer separates sidebars,
  toolbars, and panels from content. Don't rely on color alone; pair it with text or an icon.
- **Layout.** Responsive behavior is structural (collapse the sidebar, reflow the table, change
  columns), not fluid typography. Overlays escape their container: use `<dialog>`, the popover API,
  `position: fixed`, or a portal so dropdowns are not clipped by `overflow` ancestors.
- **Components.** Every interactive component has default, hover, focus, active, disabled,
  loading, and error states. Same button shape, same form-control vocabulary, same icon style
  everywhere; if the save button looks different in two places, one is wrong. Skeletons, not
  spinners, inside content. Empty states teach the interface.
- **Motion.** Motion conveys state, not decoration; timing and page-load rules per SKILL.md ›
  Conflicts › Motion.
- **Permissions.** Task surfaces can afford system fonts, standard navigation (top bar plus side
  nav, breadcrumbs, tabs, command palettes), density when users need it, and consistency over
  surprise. Save delight for moments, not pages.
