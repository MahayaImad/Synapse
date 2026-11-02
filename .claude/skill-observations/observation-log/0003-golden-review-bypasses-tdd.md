---
id: 3
title: "Visual review of goldens leads to fixes written before a failing test"
status: open
type: open-source
skill: [test-driven-development, executing-plans]
proposes_skill: []
target_file: []
siblings_checked: "superpowers family: test-driven-development and executing-plans added; systematic-debugging excluded (it governs bug hunts, not visual review findings — systematic-debugging/SKILL.md assumed)"
area: "TDD 'Write the failing test first' during visual (golden) review steps"
date: 2026-11-02
session_context: "Synapse Flutter app, Task 9: reviewing golden screenshots revealed a too-dark status colour; the theme constant was changed first, the test added after"
parked_until:
resolved:
resolution:
reference:
commands_verified: "run: theme test against old value → FAIL, new value → PASS (verified after the fact)"
---

**Issue:** The plan step said "goldens, then look at them". Looking at a rendered screenshot produces findings in a visual form (too dark, line break in the wrong place); the fastest reaction is to tweak the constant and regenerate the golden. The TDD rule was written down and loaded, but the golden-review step has no checkpoint that forces "assertion first", and regenerating goldens (`--update-goldens`) makes any visual change pass by construction.

**Suggested improvement:** In test-driven-development (and executing-plans' task loop), add a rule for visual review: every finding from looking at a golden is first expressed as a non-golden assertion (contrast, luminance range, maxLines, no break after a character) that fails, and only then is the golden regenerated. Note that `--update-goldens` is never evidence.

**Principle:** A screenshot comparison cannot be RED for a change you just made; turn each visual finding into a measurable assertion before touching the code.
