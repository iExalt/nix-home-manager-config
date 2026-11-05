---
tags: [skill-creator]
max_turns: 400
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash, Agent]
---

My bead-pattern editor is supposed to work on my phone now, as well as desktop. The checkout is at ~/dev/Projects/pattern-eval-phone-with. Before I try it on the phone, QA the phone experience the way I would and tell me what you find.

Environment rules for this run: browsers run only on the browser host named in ~/.config/frontend-dogfood/environment.md, never on this laptop; don't push, sync, or send real notifications; leave the original checkout under ~/dev/Projects untouched. Don't fix anything in this run: report what you would fix, how severe it is, and the screenshots that show it.
