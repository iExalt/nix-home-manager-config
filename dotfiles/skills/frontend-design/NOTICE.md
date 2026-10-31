# Notices

This skill merges and adapts material from three sources. Files under `references/` name the
source of their content in their opening paragraph. Changes: content was selected, trimmed,
deduplicated, and reorganized around one workflow. Steps that need Impeccable's CLI were removed,
as were Impeccable's single-purpose command playbooks (bolder, quieter, animate, typeset, colorize,
layout, adapt, optimize, delight, overdrive, distill, extract) and its native iOS/Android guidance;
their key rules are folded into the references. Rules overridden by this skill are marked inline.
Agentic-interface guidance, conflict resolutions, and `scripts/browser_check.py` were added.

| Source | Revision | License | Copyright |
|---|---|---|---|
| [Impeccable](https://github.com/pbakaus/impeccable) (`skill/`) | `b7a89176e4e87422b40f98adabceb051dbb5448b` | Apache-2.0 ([text](licenses/APACHE-2.0.txt)) | Copyright 2025 Paul Bakaus |
| [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | `ca45fc496a3436251f191354091d557da31c15b5` | Apache-2.0 ([text](licenses/APACHE-2.0.txt)) | Anthropic, PBC |
| [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines) | `434b7f91364665f2f733b310ec54809bf8f37937` | MIT ([text](licenses/MIT-vercel-web-interface-guidelines.txt)) | Copyright (c) 2025 Vercel Labs |

The Anthropic text is byte-identical to the copy this skill replaced, previously pinned from
`anthropics/claude-code@2bfb629dfaff0c8318047a4beb93cf1dc5b58b18`
(`plugins/frontend-design/skills/frontend-design`).
