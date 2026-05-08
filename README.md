# prompt-eng-toolkit

Defense-first workflow for designing and compressing **production single-turn LLM system prompts**, packaged as a Claude Code plugin.

Two skills, one shared corpus of references / scripts / fixtures:
- **`prompt-create`** — design a new system prompt with injection defenses baked in
- **`prompt-optimize`** — compress an existing prompt while preserving (often improving) adherence

## What this is

An opinionated, vendor-agnostic, **defense-first** workflow for production single-turn task prompts (refinement, classification, extraction, formatting). Built from the consensus of Google Gemini, Anthropic Claude, and OpenAI's official 2026 prompting guides, plus a real-world failure-mode catalog from production deployment.

Every workflow step is gated:
- API key present → iterative loop against real provider APIs (validate behavior before writing to source)
- API key absent → theory-only design pass with explicit "untested" disclaimer

## What this isn't

Avoid stack-of-shovels syndrome — use the right tool:

| Use case | Better tool |
|---|---|
| Production-grade eval pipeline / regression suite | [promptfoo](https://github.com/promptfoo/promptfoo) (20k+ stars) |
| Auto-optimize via ML / DSPy / genetic algos | [AutoPrompt](https://github.com/Eladlev/AutoPrompt) / [Promptomatix](https://github.com/SalesforceAIResearch/promptomatix) |
| Catalog of named frameworks (CO-STAR / RISEN / TIDD-EC …) | [prompt-architect](https://github.com/ckelsoe/prompt-architect) |
| Web/Desktop UI tool, multi-tab playground | [linshenkx/prompt-optimizer](https://github.com/linshenkx/prompt-optimizer) (28k+ stars) |
| Improve user-prompts to Claude Code itself | [claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver) |
| User-facing prompt rewriter for 30+ AI tools | [prompt-master](https://github.com/nidhinjs/prompt-master) |

**Where this fits the stack**: use this to **author** the prompt → optionally pipe the resulting prompt into promptfoo for production-grade regression eval.

## What's inside

```
plugins/prompt-eng-toolkit/
├── skills/
│   ├── prompt-create/SKILL.md     # design workflow
│   └── prompt-optimize/SKILL.md   # compression + hardening workflow
└── shared/
    ├── references/
    │   ├── provider-guidance.md           # 3-provider official-doc consensus
    │   ├── universal-principles.md        # 10 cross-vendor rules + checklist
    │   ├── optimization-playbook.md       # compression patterns + anti-patterns
    │   ├── failure-modes-and-defenses.md  # 7 attack categories + 5-layer defense
    │   └── v4-template.md                 # block-by-block annotated template
    ├── scripts/
    │   └── count_tokens.py                # multi-provider token counter (Gemini / Anthropic / OpenAI)
    └── fixtures/
        └── attack-tests-template.yaml     # 7-category injection-test starter
```

## Install

The plugin works in three agentic CLIs. Pick the section for your tool.

### Claude Code

```
/plugin marketplace add RxChi1d/prompt-eng-toolkit
/plugin install prompt-eng-toolkit@prompt-eng-toolkit
```

Both skills auto-register. Trigger naturally — "help me write a system prompt for X" picks up `prompt-create`; "this prompt is too long" picks up `prompt-optimize`.

### Codex CLI

The repo ships canonical Codex manifests at `.agents/plugins/marketplace.json` and `plugins/prompt-eng-toolkit/.codex-plugin/plugin.json` alongside the Claude Code ones, so the same source works in both.

```bash
codex plugin marketplace add RxChi1d/prompt-eng-toolkit
codex plugin install prompt-eng-toolkit --source prompt-eng-toolkit
```

The skills are then loaded by Codex's progressive-disclosure scanner. No SKILL.md edits needed — the file format is identical to Claude Code's.

### OpenCode

OpenCode auto-discovers any `.opencode/skills/<name>/SKILL.md` (and, via its Claude Code compatibility layer, `.claude/skills/<name>/SKILL.md`). It has no marketplace concept; install is a clone + symlink.

**Per-project install:**

```bash
git clone https://github.com/RxChi1d/prompt-eng-toolkit ~/.local/share/prompt-eng-toolkit
mkdir -p .opencode
ln -s ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/skills .opencode/skills
ln -s ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/shared .opencode/shared
```

**Global install (all OpenCode projects):**

```bash
git clone https://github.com/RxChi1d/prompt-eng-toolkit ~/.local/share/prompt-eng-toolkit
mkdir -p ~/.config/opencode
ln -s ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/skills ~/.config/opencode/skills
ln -s ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/shared ~/.config/opencode/shared
```

Both `skills/` and `shared/` must symlink into the same parent so the SKILL.md `../../shared/...` relative paths resolve.

Update with `git -C ~/.local/share/prompt-eng-toolkit pull`.

---

After install (any tool), trigger the skills naturally:
- "Help me write a system prompt for X" → `prompt-create`
- "This prompt is too long, can we tighten it?" → `prompt-optimize`

## Use

Skills self-introduce when the task matches their description. To force-invoke:

```
Use prompt-create skill to design a system prompt for <task>.
```

```
Use prompt-optimize skill to compress this prompt: <paste>
```

Both skills will ask once for an API key (env-only, never written to disk). Refusing falls back to a theory-only static design / review pass with an explicit disclaimer.

## API key handling

API keys are read from environment variables in this order:
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`

Keys are **never** written to any file (skill, source, scratch, log). If keys are not set, the skills ask the user once at runtime and place the value into `os.environ` for the session only.

## Counting tokens manually

The token counter is at `<plugin-root>/shared/scripts/count_tokens.py` (substitute the absolute path your tool installed it to):

```bash
# Single file
count_tokens.py --provider gemini --model gemini-2.5-flash --file my_prompt.txt

# Before / after diff
count_tokens.py --provider anthropic --model claude-sonnet-4-5 \
  --before old.txt --after new.txt --label "system prompt"

# Multi-segment markdown table
count_tokens.py --provider openai --model gpt-5 \
  --pair "system:old_sys.txt:new_sys.txt" \
  --pair "user:old_usr.txt:new_usr.txt"
```

Counts go through the **official provider countTokens API** (or local tiktoken for OpenAI when available) — no character-based heuristics, no third-party tokenizer guessing.

## Background — what the references contain

| File | Source / Authority |
|---|---|
| `provider-guidance.md` | Direct quotes + URLs from Gemini 3 / Claude 4.5+ / GPT-5 official prompting guides (2026) |
| `universal-principles.md` | 10 cross-vendor rules, each cited to ≥2 of the 3 official guides |
| `optimization-playbook.md` | Compression priority ladder + 6 anti-patterns, derived from real-world v1→v4 case study (46% system-prompt reduction with improved adherence) |
| `failure-modes-and-defenses.md` | 7 attack categories with implementation examples + 5-layer defense architecture |
| `v4-template.md` | Block-by-block annotated reference template |

## Compatibility

| Tool | Status | Discovery path used |
|---|---|---|
| Claude Code 2.x with plugins enabled | ✅ canonical | `.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json` |
| Codex CLI (Rust rewrite, 2026+) | ✅ canonical | `.agents/plugins/marketplace.json` + `.codex-plugin/plugin.json` |
| OpenCode (sst/opencode) | ✅ via clone + symlink | `.opencode/skills/...` (or `.claude/skills/...` via compat layer) |
| Gemini CLI / Cursor / Aider | ⚠️ untested — likely works for the SKILL.md content if their loader supports the agents.md skill convention; manifest needs adapting |

Token counter requires Python 3.9+ (urllib only; `tiktoken` optional for OpenAI offline counting).

## License

MIT — see [LICENSE](./LICENSE).
