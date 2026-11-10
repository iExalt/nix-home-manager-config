---
name: fix-skill
description: Delegate changes to a skill being used in the current conversation, then immediately reload the updated instructions in the main agent and affected collaborators. Use when the user wants to fix or refine the skill itself without moving to a separate thread.
---

# Fix Skill

Keep the current task in the main thread and delegate the skill edit to one
subagent. Infer the target skill and requested change from the conversation;
ask only if either is ambiguous.

## Delegate the edit

Spawn a native subagent, routed per `iExalt:working-conventions` › Model
routing ("Pilot: implementation" row). Give it a focused brief without
unrelated task history: the target skill name and known source path, the
user's requested change, relevant examples or constraints from this thread,
and the main agent's address. Tell the subagent to:

1. Locate the authoritative source, starting with
   `$HOME/dev/Projects/nix-home-manager-config/dotfiles/plugins/iExalt/skills/<skill>/SKILL.md`.
   Resolve the active skill's symlink or catalog location when necessary. Do
   not edit a generated or installed copy when a maintained source exists.
   If copies disagree, establish which one the current thread uses.
2. Read every `AGENTS.md` from the source repository root down to the target
   skill, because they aren't loaded when invoked from another repository.
   Read the Git state, the full skill, and relevant supporting files. Use the
   available skill-creation guidance, and make the requested scoped edit
   while preserving unrelated work.
3. Validate the skill and any changed executable behavior, then provision and
   publish as those `AGENTS.md` files direct, following `working-conventions`
   › Publication. Report failures separately from completed edits.
4. Return the skill name, authoritative path, revision or content fingerprint,
   brief diff summary, validation result, and provisioning/publication status.
   End a successful handoff with: `Immediately run /iExalt:reload-skill <skill> using
   the source path and diff summary above before continuing skill-dependent work.`

The main agent can continue independent work while the edit runs. Avoid new
decisions based on the instructions being changed, and park affected
collaborators at a safe boundary if needed. Route any user clarification
through the main agent. If subagents are unavailable, report the limitation
instead of claiming delegation or silently substituting an in-thread edit.

## Reload before resuming

On the completion handoff, immediately apply [reload-skill](../reload-skill/SKILL.md)
to the reported source with the diff summary. If programmatic slash commands are
not supported, read that skill and follow its instructions directly.

If validation or provisioning failed, resolve the blocker before treating the
updated skill as ready. A publication-only failure does not block rereading
validated local instructions; report that publication remains incomplete.
Resume affected work after the reload and required acknowledgments, and give
the user a concise summary of the change and any remaining limitation.
