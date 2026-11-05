# Follow-up

Read the section that applies: a pedantic pass with a larger verified list (SKILL.md step 5), or
the user's own review after a pass (SKILL.md step 7).

## Larger pedantic lists

Stop after verification and report before fixing anything: verified counts per severity, the top
five with screenshots, the decisions only the user can make, and what fixing will cost (chunks or
pull requests, surfaces, anything outside the UI, a rough duration). Offer scopes: P0 and P1 only,
with the rest filed (what the user chose for large passes); all of P0 to P2; or the list as a
handover. Fix only what they choose. In one audit, "fix all of it" became more than five hours of
chunks, reviews, and CI before a second round could start.

## Learning from the user's review

When the user reviews the UI after a dogfood pass, compare what they caught with what the tester
reported. For each thing they caught that the tester missed, propose an addition to
taste-profile.md: the principle with the user's words as the receipt, and a probe that would have
caught it. Show the proposed lines and edit the profile only after the user approves. Corrections
go the other way too: if the user waves off a finding the profile predicted, propose narrowing or
removing that rule.
