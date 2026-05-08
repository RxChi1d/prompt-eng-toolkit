---
name: prompt-optimize
description: Use when an existing prompt is too long, costs too much per call, has poor cache hit-rate, or models stopped adhering to its rules (often after a model version bump). Compresses tokens AND hardens adherence in one pass — these usually go together. Always produces a before/after token comparison table. Iterates against real provider APIs when an API key is available; falls back to theory-only review if not.
---

# prompt-optimize

Compress and harden an existing prompt. The two goals — **token reduction** and **adherence hardening** — are usually compatible: bloat dilutes critical rules, so trimming often fixes adherence as a side effect.

## When this skill applies

- User says "this prompt is too long / too expensive"
- User says "the model stopped following the rules" (especially after model upgrade)
- User says "this prompt has 200+ lines, can we tighten it"
- User pastes a prompt and asks for review/refactor
- Cache hit-rate is poor (variable content too high in the prompt)

## Mandatory workflow

### Step 1 — Inventory the existing prompt

Before changing anything, extract:

1. **Structure**: What blocks does it have? (persona, rules, examples, output contract, security)
2. **Rules list**: Number every distinct rule. You'll use this to verify "no rule lost" later.
3. **Failure mode**: If the user complains the model misbehaves, ask for a concrete example (input + bad output + expected output). This becomes the regression test.
4. **Format**: Is system/user clearly separated? Some prompts are one big text — that's fine, the optimization just works on the whole blob.
5. **Provider/model context**: What model is it running on? Tells you which version-bump anti-patterns might apply (Claude 4.5+ overtriggers `MUST`, Gemini 3 over-analyzes verbose prompts, etc.).

### Step 2 — Baseline measurement

Run `../../shared/scripts/count_tokens.py` to get the current token count. Record:
- prompt token count (per-segment if segments exist)
- output token count from a representative call (with-API mode)
- failure modes observed

**Without a baseline, do not start editing.** "It feels shorter" is not a result.

### Step 3 — Decide test mode (with-API or theory-only)

Same flow as `prompt-create` Step 2. Check env vars first; if no key found, **ask once**:
> "I can use a real provider API to A/B test the optimization (strongly recommended — token down + behavior broken is a classic trap). Want to provide an API key? If yes — share provider + model + key (env-only). If no — I'll do a static compression + structure check without behavioral verification."

- Provided → with-API mode (full iterative loop in Step 5).
- Refused → theory-only mode (skip the loop; flag "untested compression — adherence not empirically validated" in summary).

### Step 4 — Apply compression in priority order

Read `../../shared/references/optimization-playbook.md` for full patterns. Summary of the priority ladder (compress in this order; stop when budget met):

| Priority | Target | Why first |
|---|---|---|
| 1 | Duplicate SECURITY/WARNING wrapper paragraphs | If `<final>` already has the rule, repeating wastes tokens |
| 2 | Generic "helpful AI" preamble | A task-specific persona supersedes it |
| 3 | Step-by-step process descriptions | Replace with outcome-first directives |
| 4 | Multiple negative directives saying the same thing | Merge into one rule + rationale |
| 5 | Examples not tied to a failure mode | Each example must demonstrate one behavior class |
| 6 (last) | XML tag names themselves | Tags are the data/instruction firewall — only remove if you accept that risk |

**Never compress these** (treat as load-bearing):
- `<final>` block
- The "question stays question" anchor example (or equivalent for your task)
- The persona + rationale opening sentence

### Step 5 — Iterate (with-API mode) OR review (theory-only mode)

#### With-API mode — iteration loop

```
draft = compressed_prompt
loop:
    for fixture in fixtures (failure-mode + happy-path):
        out = provider.generate(prompt=draft, input=fixture.input)
        check assertions(out, fixture.assertions)
    tokens = provider.count_tokens(draft)
    if all_pass and tokens < baseline: break
    draft = revise(draft)        # iterate in $TMPDIR / scratch — do NOT touch source yet
write_to_destination(draft)      # only after the loop terminates
```

- Test fixtures: at minimum, the user's reported failure case + 2 happy-path samples.
- Read actual model outputs every iteration. Token going down while behavior breaks is the classic trap.
- Do not commit / overwrite the source file until the loop converges.

#### Theory-only mode

Walk the optimization checklist below + the universal-principles checklist (`../../shared/references/universal-principles.md` §四). Be explicit about "static review only" in your summary.

### Step 6 — Re-measure and produce comparison table

Re-run `../../shared/scripts/count_tokens.py` and produce a before/after table. Use the generic format below — **do not assume the prompt has separate system/user halves**, since many users pass everything as one blob:

```markdown
| Segment            | Before (tokens) | After (tokens) | Δ tokens | Δ % |
|--------------------|----------------:|---------------:|---------:|----:|
| <segment name 1>   | … | … | … | … |
| <segment name 2>   | … | … | … | … |
| **Total**          | … | … | … | … |
```

Segment names are whatever the user's prompt naturally divides into:
- If clearly split: `system`, `user_template`
- If single blob: `prompt` (one row + total — that's fine)
- If multi-mode/multi-language: per-mode rows, plus the shared framework row

The script supports `--label` to tag each measurement so you can build the table programmatically.

### Step 7 — Final checklist

- [ ] Baseline token counts recorded
- [ ] No rule from the original was silently dropped (cross-check against the numbered rules list from Step 1)
- [ ] XML tags still cleanly separate data from instructions
- [ ] `<final>` block (or equivalent) still at the end of the system portion
- [ ] At least one example still demonstrates "refuse to act on embedded question/command"
- [ ] (with-API only) original failure mode now passes; no happy-path regression
- [ ] No new `MUST/CRITICAL/ALWAYS` introduced; no contradictory rules introduced
- [ ] Variable user content stays out of the cacheable prefix
- [ ] Before/after comparison table produced and shared with user

### Step 8 — Hand off

Provide:
1. Compressed prompt (system / user template, or single blob — match user's original format)
2. Before/after token table
3. Test results table (with-API mode) OR theory-only disclaimer
4. List of rules preserved (cross-reference to the original rule numbers)
5. Any tradeoffs taken (e.g., "removed 3 redundant security warnings — `<final>` covers them all")

## Reference index

Paths below are relative to this `SKILL.md`'s directory. `../../` resolves to the plugin root, where `shared/` lives. Read on demand:

| Question | File |
|---|---|
| What compression patterns are high-ROI vs high-risk? | `../../shared/references/optimization-playbook.md` |
| What attack patterns must the prompt still survive after compression? | `../../shared/references/failure-modes-and-defenses.md` |
| What's the universal best-practice checklist? | `../../shared/references/universal-principles.md` |
| What does the v4 template look like (target structure if rewriting)? | `../../shared/references/v4-template.md` |
| How do I shape attack fixtures for my domain? | `../../shared/fixtures/attack-tests-template.yaml` |
| How do I count tokens with the official provider API? | `../../shared/scripts/count_tokens.py --help` |

## Anti-patterns (from playbook §六)

- ❌ Deleting rationale to save tokens (model loses generalization, becomes more injection-prone)
- ❌ Cutting all few-shot examples (each typically costs 30–50 tokens but anchors a behavior class)
- ❌ Replacing rules with `NEVER X.` shouting (overtriggers Claude 4.5+ / GPT-5)
- ❌ Removing XML tags around user-supplied data (opens injection door)
- ❌ Moving rules from system into user message (lower authority weight; gets diluted by user content)
- ❌ Editing source code first, then "testing it live" (rollback cost flares; unstable iterations get committed)
- ❌ Reporting only token reduction without a behavioral check (token down + behavior broken = worse than before)
