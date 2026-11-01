---
id: 1
title: "Specs over messy external data should measure each rule's yield on real samples before approval"
status: open
type: open-source
skill: [brainstorming, writing-plans]
proposes_skill: []
target_file: []
siblings_checked: "superpowers family: brainstorming, writing-plans added; executing-plans excluded (it already rules on plan defects via ledger, executing-plans/SKILL.md 'Rulings, not stalls')"
area: "brainstorming 'Look Before You Ask' / writing-plans 'Review Focus'"
date: 2026-11-01
session_context: "Synapse phase 1: designing the import of a government monthly Excel drug list"
parked_until:
resolved:
resolution:
reference:
commands_verified: none
---

**Issue:** The approved design fixed rules (unknown date in "DATE DE RETRAIT" = anomaly; any product in two sheets = admin case) after inspecting headers and a few rows only. Running the implemented pipeline on the real files showed the rules' yield: 1,132 anomalies per month (the column mostly holds a withdrawal *type*, not a date) and 40 admin cases per month (36 being an unambiguous non-renewed+withdrawn overlap). Both rules had to be overturned mid-execution by rulings.

**Suggested improvement:** In brainstorming (Look Before You Ask) and writing-plans (Review Focus), when the spec governs messy external data, require a quick yield measurement: for each proposed validation/escalation rule, count how many records it would flag on a real sample, and put the counts in the spec. A rule whose yield is in the hundreds per run is a design smell to resolve before approval.

**Principle:** A rule about data is only designed once you know how often it fires on real data; measure the yield of every escalation rule before asking a human to approve it.
