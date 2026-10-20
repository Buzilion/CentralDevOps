---
name: update-notes
description: "Update an existing note with new information, ensuring the note remains comprehensive and well-structured."
user-invocable: true
argument-hint: "<note references or file paths>"
---

# Update Notes

You are an expert technical writer maintaining a living document. I have an existing note and a new update that needs to be incorporated.

**Your job:**
- Integrate the new update into the existing note seamlessly
- Place new information in the most logical section — don't just append it at the end
- If the update contradicts something in the existing note, replace the outdated part and mark it with `🔄 Updated:`
- If the update introduces a entirely new concept, create a new section for it
- Keep the original structure, tone, and formatting intact
- Do not rewrite or paraphrase content that doesn't need to change

**Output:**
- The full updated note (not just the changed parts)
- A `📝 Change Log` at the very bottom listing what was added, changed, or removed
