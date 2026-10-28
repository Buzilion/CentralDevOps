---
name: enhance-note
description: "Turn a messy, incomplete, or poorly structured note into a clear, useful working document without inventing facts."
user-invocable: true
argument-hint: "<note text, file path, or topic>"
---

# Enhance Note

Rewrite a rough technical note into a clean working document without inventing facts. Preserve meaning, keep every unique detail, and make the note easier to resume later.

## Process

1. Read the full note before rewriting.
2. Infer the note type, audience, and purpose from the content.
3. Preserve all concrete facts, decisions, actions, commands, paths, risks, open questions, contradictions, and uncertainty.
4. Clean the wording:
	- remove obvious redundancy
	- rewrite unclear phrasing in plain language
	- expand shorthand only when the meaning is clear
	- normalize terminology
	- turn fragments into concise bullets, steps, or short paragraphs
	- keep code snippets, commands, paths, and technical terms intact
5. Rebuild only the structure the note needs. Prefer compact sections such as:
	- Title
	- Summary
	- Context
	- Key Points
	- Decisions
	- Action Items
	- Risks or Concerns
	- Open Questions
	- Next Steps
	- References
	- Key Takeaways
6. Handle gaps safely:
	- if the note is too fragmentary to interpret, organize the fragments rather than guessing
	- never invent facts, decisions, dates, owners, or technical details
	- mark implied but unstated content as `Assumption:`
	- add `Open Question:` when missing information blocks understanding
	- surface contradictions clearly
	- keep uncertainty visible

## Output

Return the full rewritten note only.

The result should:

- be cleaner and easier to reuse
- preserve all meaningful content
- make implicit structure explicit
- keep TODOs, checklists, decisions, and unresolved questions visible
- stay concise unless the source needs more detail
- make only minimal improvements if the note is already good
