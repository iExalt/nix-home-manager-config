---
name: fix-skill
description: Delegate changes to a skill being used in the current conversation, then immediately reload the updated instructions in the main agent and affected collaborators. Use when the user wants to fix or refine the skill itself without moving to a separate thread.
---

# Fix Skill

Keep the current task in the main thread and delegate the skill edit to one
subagent. Infer the target skill and requested change from the conversation;
ask only if either is ambiguous.

## Delegate the edit

Spawn a subagent with a focused brief: the target skill name and known source
path, the user's requested change, relevant examples or constraints from this
thread, and the main agent's address. Avoid copying unrelated task history.
Tell the subagent to:

1. Locate the authoritative source, starting with
   `$HOME/dev/Projects/nix-home-manager-config/dotfiles/skills/<skill>/SKILL.md`.
   Resolve the active skill's symlink or catalog location when necessary; do
   not edit a generated or installed copy when a maintained source exists.
   If multiple copies disagree, establish which one the current thread uses.
2. Read the applicable `AGENTS.md` files from the source repository root down
   to the target skill. When editing skills in
   `$HOME/dev/Projects/nix-home-manager-config/dotfiles/skills`, explicitly read
   `$HOME/dev/Projects/nix-home-manager-config/dotfiles/AGENTS.md`. Do not assume
   these instructions were automatically loaded when invoked from another
   repository. Read the Git state, full skill, and relevant supporting files.
   Use the available skill-creation guidance. Maintain a checklist and make
   the requested scoped edit while preserving unrelated work.
3. Validate the skill and any changed executable behavior. Follow the source
   repository's provisioning and publication rules, including Home Manager
   reload for added, removed, or renamed skills and scoped commits/pushes where
   authorized. Report failures separately from completed edits.
4. Return the skill name, authoritative path, revision or content fingerprint,
   brief diff summary, validation result, and provisioning/publication status.
   End a successful handoff with: `Immediately run /reload-skill <skill> using
   the source path and diff summary above before continuing skill-dependent work.`

The main agent can continue independent work while the edit runs. Avoid new
decisions based on the instructions being changed; park affected collaborators
at a safe boundary if needed. Route any necessary user clarification through
the main agent. If subagents are unavailable, report the limitation instead of
claiming delegation or silently substituting an in-thread edit.

## Reload before resuming

On the completion handoff, immediately apply [reload-skill](../reload-skill/SKILL.md)
to the reported source and pass along the diff summary. Do not merely print the
command or ask the user to invoke it. If programmatic slash commands are not
supported, read that skill and execute its instructions directly.

If validation or provisioning failed, resolve the blocker before treating the
updated skill as ready. A publication-only failure does not prevent rereading
validated local instructions; report that publication remains incomplete.
Resume affected work after the reload and required acknowledgments, and give
the user a concise summary of the change and any remaining limitation.
