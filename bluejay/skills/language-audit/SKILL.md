---
name: language-audit
description: Show the language distribution of a Bluejay agent's calls and flag languages where the agent struggles (higher failure/short-call rates, mis-detection, fallback to English). Use when the user wants to see the language mix of calls and how well each is handled, or invokes /bluejay:language-audit.
---

# Audit call languages

> Runs over the Bluejay MCP (`mcp__bluejay__*`). If those tools aren't available, stop and tell the user to finish setup (`npx bluejay` / set `BLUEJAY_API_KEY`).

Goal: show the language distribution of calls and flag languages where the agent struggles.

## Steps

1. **Scope.** Agent + time range.
2. **Distribution.** Query `list_call_logs` per language using `evaluation_filters: [{column: "detected_language", operator: "equals", value: "<code>"}]` (ISO 639-1: "en", "es", "fr", …). Use each query's `total` to build the language mix.
3. **Per-language health.** For the top non-English languages, compare failure/short-call rates to English. Pull a couple of transcripts in a struggling language (`get_call_log`) to see the failure mode (mis-detection, fallback to English, dead air).
4. **Report.** Table of language | volume | failure rate, plus a short note on any language the agent visibly handles worse and what to do (prompt/voice config, KB coverage in that language).

## Notes
- `detected_language` is populated per call — rely on it rather than guessing from caller numbers.
- If only English appears but the user expects multilingual traffic, that itself is a finding (detection or routing issue), not "no other languages".
