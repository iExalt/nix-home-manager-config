# Notices

This skill merges and adapts material from three sources. Content was selected, trimmed,
deduplicated, and reorganized around one workflow; agentic-interface guidance, the conflicts
section, and `scripts/browser_check.py` are additions. Where this skill overrides upstream wording,
a one-line **Override** pointer leads to `SKILL.md` › Conflicts.

- **`SKILL.md`** adapts Impeccable's `SKILL.src.md` (core principles, ground rules, modes) and
  `reference/shape.md` (discovery questions and cadence).
- **`references/`** name their sources in their opening paragraphs: `visual-direction.md`
  (Anthropic; Impeccable `craft-floor.md`, `operate.md`, `new-work.md`), `critique.md` (Impeccable
  `critique.md`, `audit.md`), `states-and-edge-cases.md` (Impeccable `harden.md`, `onboard.md`;
  Vercel), `copy.md` (Anthropic; Impeccable `clarify.md`; Vercel), `design-record.md` (Impeccable
  `init.md`, `document.md`), and `web-interface-guidelines.md` (Vercel, verbatim).
- **Not used** from Impeccable: its CLI and the references that depend on it (`live`, `live-setup`,
  `generate`, `hooks`, `doctor`, `region-map`, `visualize`, `routing`, the `mode-*.md` comp rules),
  the single-purpose playbooks (`polish`, `bolder`, `quieter`, `distill`, `animate`, `colorize`,
  `typeset`, `layout`, `delight`, `overdrive`, `adapt`, `optimize`, `extract`, `component-review`,
  `craft`), native iOS/Android guidance, and the subagent definitions. Their key rules are folded
  into the references where they apply. Impeccable's craft-floor Refuse list is kept
  as defaults, its outright eyebrow ban is relaxed, and its Codex-only sketch-SVG and stripe/grid
  rules now apply to every agent; see `SKILL.md` › Conflicts › Generated-look defaults. Its
  Codex-only card-radius rule (12–16px, pills for small controls) also applies everywhere. operate.md's
  "Product constraints" are carried by `visual-direction.md` › Task surfaces and `SKILL.md` ›
  Conflicts (Typefaces, Native controls, Motion). Not carried over: Impeccable's randomized
  concept seeding and comp generation, which need its CLI.

| Source | Revision | License | Copyright |
|---|---|---|---|
| [Impeccable](https://github.com/pbakaus/impeccable) (`skill/`) | `b7a89176e4e87422b40f98adabceb051dbb5448b` | Apache-2.0 ([text](licenses/APACHE-2.0.txt)) | Copyright 2025 Paul Bakaus |
| [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | `ca45fc496a3436251f191354091d557da31c15b5` | Apache-2.0 ([text](licenses/APACHE-2.0.txt)) | Anthropic, PBC |
| [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines) | `434b7f91364665f2f733b310ec54809bf8f37937` | MIT ([text](licenses/MIT-vercel-web-interface-guidelines.txt)) | Copyright (c) 2025 Vercel Labs |

The Anthropic text is byte-identical to the copy this skill replaced, previously pinned from
`anthropics/claude-code@2bfb629dfaff0c8318047a4beb93cf1dc5b58b18`
(`plugins/frontend-design/skills/frontend-design`).
