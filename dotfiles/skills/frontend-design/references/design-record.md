# Design record (DESIGN.md)

The design record carries agreed decisions from one session to the next, so later work stays
consistent without re-asking the user. It merges Impeccable's PRODUCT.md and DESIGN.md (Apache-2.0)
into one file. The visual sections keep the names and relative order of Impeccable's DESIGN.md:
Overview, Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts. The
user sections adapt PRODUCT.md, and Interaction conventions, Voice & copy, Open decisions, and
Decision log are additions. Impeccable's YAML token frontmatter is omitted. If you adopt
Impeccable's tooling, run its `document` command to regenerate a compatible DESIGN.md from this one.

## Rules

- **Location.** Use `DESIGN.md` at the frontend's root (the app or package directory, or the
  repository root for a single-app repo). If the project already keeps PRODUCT.md and DESIGN.md
  apart, keep them apart. Ask before overwriting someone else's existing DESIGN.md.
- **Write only confirmed facts and agreed decisions.** Mark provisional choices `(provisional)` and
  open questions under "Open decisions". Omit sections that do not apply rather than filling them
  with generic prose.
- **Describe, then give the value.** "Gently curved edges (8px radius)" beats `rounded-lg`. Explain
  where and why a token is used, not just what it is. Reference token names when the code has them
  rather than duplicating values that will drift.
- **Use named rules.** `**The One Accent Rule.** The accent marks primary actions and current
  selection only.` Named rules are short, memorable, and easy for later agents to cite.
- **Record what's reused.** Don't document one-offs or invent components that don't exist.
- **Update it in the same change as the code** when a convention changes, and log the user's
  feedback that caused the change.

## Template

```markdown
# Design

## Users
<!-- Who uses this, in what situation and state of mind, and how often. -->

## Primary tasks
<!-- The 1–5 things users come to do, most important first, with what success looks like. -->

## Product principles
<!-- 3–5 durable priorities from the user, such as "task efficiency over novelty". -->

## Accessibility & inclusion
<!-- Required standard (default: WCAG 2.2 AA), known user needs, supported input methods. -->

## Overview
<!-- The visual direction in two or three sentences; the mode (Operate, Read, Persuade,
Experience) for each surface. -->

## Colors
<!-- Grouped by role: primary, secondary, neutral, semantic states. Hex values and where each is
used. -->

## Typography
<!-- Families and roles, scale steps, weights, measure. -->

## Layout
<!-- Grid, spacing scale, breakpoints and what changes at each, density. -->

## Elevation & Depth
<!-- Border or shadow vocabulary, layering, overlays. -->

## Shapes
<!-- Radius scale and where each applies. -->

## Components
<!-- Buttons, inputs, tables, navigation, status indicators: variants, states, behavior. -->

## Interaction conventions
<!-- Agreed behaviors: destructive actions (undo vs confirm), save model, keyboard shortcuts,
loading and empty patterns, how agent runs show status, approval, cancel, and retry. -->

## Voice & copy
<!-- Case convention, terminology glossary, tone for errors and success. -->

## Do's and Don'ts
<!-- Named rules and anti-patterns specific to this product. -->

## Open decisions
<!-- Questions for the user, with the current provisional choice. -->

## Decision log
<!-- YYYY-MM-DD — decision — reason (often the user's feedback). -->
```
