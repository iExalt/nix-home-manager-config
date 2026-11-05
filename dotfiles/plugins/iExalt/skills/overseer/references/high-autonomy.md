# High-autonomy session grant

Read this before exercising high autonomy as an overseer.

At the beginning of **every high-autonomy overseer session**, before starting
workers or exercising delegated authority, ask a question dialog that
requires an explicit answer. This includes a replacement overseer, a new run,
and switching an existing session to high. In Paseo, the actual overseer asks
after the launcher hand-off; a launcher's or previous session's grant does
not carry over. A same-session resume may retain its recorded grant. Like
any session grant, it never covers a release (`working-conventions` ›
Authority).

Explain that high autonomy permits the main agent to make decisions with the
user's delegated authority within the agreed scope, including Paseo messages
that supply authorization context for suspected auto-mode classification
false positives. Paseo's `send_agent_prompt` messages to other Paseo agents
appear as if sent by the user, so the overseer can supply the missing
authorization context and unblock such false positives through supported
reconsideration. These messages interrupt the receiver and its running
subagents instead of queuing, so the overseer prefers an idle receiver and
otherwise adds a continuation note, as [paseo.md](paseo.md) › Relay approvals past a classifier block
describes.
This does not transfer authority to workers or remove the mandatory
consultations or the harness's permission checks. Ask:

> For this session, do you explicitly grant the overseer the power to act
> **with the authority of the user**, not just **on your behalf**, within the
> agreed scope, including clearly identified delegated authorization through
> Paseo messaging for auto-mode reconsideration?

Offer **Grant for this session** and **Use medium autonomy**. Do not infer
consent from a request for high autonomy, silence, a selected default, or plan
approval. Record the actual answer, session ID, scope and date alongside the
plan agreement. Until granted, do not exercise high autonomy; a declined
grant selects medium. If a dialog cannot be opened, leave the grant pending
and proceed only under medium's rules and any existing plan approval. Honor
revocation or a lower level immediately and tell workers about the change.
