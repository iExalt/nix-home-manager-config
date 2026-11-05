# Close a finished campaign

Read this once the user confirms the campaign's final gate is met, or closes
it with a caveat they accept; never decide that yourself. Closing keeps the
campaign's working documents from crowding the repository's current docs:

1. Record the closure in the status document and the script's revision log:
   the date, the evidence or accepted caveat, and the user's words.
2. Fold what is still true into the repository's living docs. Write it as
   current-state reference: what the system does and why, without the
   campaign's play-by-play, step numbers, thread names or decision IDs. Re-read
   the living docs the campaign touched and align them with each other.
3. Move the plan, roadmap, script and status document to
   `docs/complete-campaigns/<campaign-name>/`, or the repository's own
   equivalent, and fix their relative links. For workstreams, check that every
   workstream issue is closed. Then close and unpin the readiness summary with
   a final comment linking the moved documents.
4. Delete the campaign's temporary records: dated run records, and the probe
   scripts and fixtures kept only as evidence. Before deleting, pin the last
   commit that has them and re-point every surviving link and code comment at
   that commit (a permalink, or `git show <commit>:<path>`) or at the living
   doc that now holds the fact. Ask before deleting anything the repository's
   instructions protect or a maintained check still reads.
5. If the repository's agent instructions don't say where finished campaigns
   go, add it. Remove instructions that point agents at the campaign's
   documents or tick rule.
6. Run the repository's checks, including link and Markdown checks, and
   publish as in "Publish and link": the move and deletion in one commit, the
   living-doc rewrite in another.
