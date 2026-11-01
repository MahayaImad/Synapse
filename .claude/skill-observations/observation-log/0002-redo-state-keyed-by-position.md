---
id: 2
title: "Review Focus should list state that survives a redo/replace operation, keyed by position instead of content"
status: open
type: open-source
skill: [writing-plans]
proposes_skill: []
target_file: []
siblings_checked: "superpowers family: writing-plans added; brainstorming excluded (assumed — it does not enumerate failure modes); executing-plans excluded (executing-plans/SKILL.md 'Final Review' already relays Review Focus to the reviewer)"
area: "writing-plans 'Review Focus' / Self-Review step 4"
date: 2026-11-01
session_context: "Synapse phase 1: admin CLI with import --remplacer and a human-filled decisions file"
parked_until:
resolved:
resolution:
reference:
commands_verified: none
---

**Issue:** The plan's Review Focus covered "rerun needs --remplacer" but not what happens to human-entered state (decision choices) when the draft is redone. Choices were merged back by an id built from row position (`kind:sheet:row`), so after a re-import with different data an old human decision silently applied to a different product. Per-task TDD passed; only the final fresh reviewer caught it (Critical).

**Suggested improvement:** Add to writing-plans' Review Focus guidance: for every operation that redoes or replaces generated data (re-import, regenerate, --force), list each piece of human- or externally-entered state that survives it and how it is re-associated; positional or derived ids must be backed by a content fingerprint, with a test that the redo invalidates stale state.

**Principle:** State a human entered about generated content must be bound to that content's fingerprint, never to its position; any redo path is a place where that binding silently breaks.
