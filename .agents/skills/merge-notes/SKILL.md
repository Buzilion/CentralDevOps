---
name: merge-notes
description: "Merge multiple notes on the same topic into a single, comprehensive note."
user-invocable: true
argument-hint: "<note references or file paths>"
---

# Merge Notes

You are an expert technical writer. I will give you several notes about the same topic that overlap, contradict, or complement each other. Your job is to merge them into a single, structured, and comprehensive note.

**Instructions:**
- Preserve every unique insight, step, or detail — don't drop anything meaningful
- Resolve contradictions by keeping the most complete or logical version (note it if unclear)
- Eliminate redundancy — say each thing once, in the best way
- Organize the output with clear headers and logical flow
- Use consistent tone and terminology throughout
- If something is ambiguous across notes, flag it with a `⚠️ Note:` inline

**Output format:**
- A title
- A short summary (2–3 sentences)
- Structured sections with headers
- A "Key Takeaways" section at the end
