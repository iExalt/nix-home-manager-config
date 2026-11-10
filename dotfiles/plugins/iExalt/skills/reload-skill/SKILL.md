---
name: reload-skill
description: Carefully reread a skill from its current source and recursively refresh affected subagents and peers. Use after a skill changes or when asked to reload skill instructions, optionally with a diff summary.
---

# Reload Skill

Accept a skill name or source path and an optional diff summary, or infer the
target from the conversation when clear. This reload refreshes agent
instructions; it does not edit files or run Home Manager.

## Reread and reconcile

1. Resolve the current authoritative `SKILL.md` from the supplied path or skill
   catalog, following symlinks. For personal skills, also check
   `$HOME/dev/Projects/nix-home-manager-config/dotfiles/plugins/iExalt/skills/<skill>/SKILL.md`.
   Confirm it is the intended skill rather than a stale duplicate.
2. Read the entire current file from its source, even if an older version is
   already in context. A diff summary focuses attention but never substitutes
   for the full text. Reread changed supporting instructions relevant to the
   active task, and follow newly applicable references.
3. Identify what changes for the current task, including removed requirements.
   Replace superseded skill guidance in the working plan while preserving
   higher-priority instructions and the user's scope and authorization.
   Reassess pending decisions or work affected by the change; do not restart
   unrelated completed work.
4. Name the next action the change affects and how it now runs. Stop or
   replace commands, helpers and monitors the change supersedes before
   resuming, so the old routine doesn't keep running.

## Propagate through the active team

Use the available agent and session tools to find existing subagents and peers
whose ongoing work uses this skill, including agents holding delegated copies
of its instructions. Do not spawn agents just to reload a skill.

Send each affected collaborator the skill name, resolved source path, current
revision or content fingerprint, optional diff summary, and this instruction:

> Before continuing work governed by this skill, read its complete current
> source and relevant changed references. Reconcile your plan with it, then
> forward this same reload request to your affected subagents and peers.
> Acknowledge which revision you read, any impact on your work, and whether
> downstream reloads are complete or blocked.

Tag the request with one reload identifier, such as the source path plus
content hash, and process each identifier once: forward it to affected
collaborators other than the sender, collect their acknowledgments and report
them to the first sender, and answer a duplicate with only your local reread,
so peer links cannot loop or deadlock. A change that lands mid-propagation
starts a new reload under a new identifier.

Wait for affected collaborators to acknowledge the reread before relying on
their skill-dependent output; independent work may continue. For inaccessible
or stopped sessions, report the gap and require a reload if their work resumes;
do not claim that sending a message proves it was read. Give future agents the
current source when delegating skill-dependent work.

Confirm briefly, in a few lines: the source and revision reread, the material
effect on the task, and whether team propagation completed, was unnecessary,
or remains blocked. Don't summarize the skill; expand only when the user asks
for the diff or must decide something.
