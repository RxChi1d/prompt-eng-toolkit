# prompt-eng-toolkit (plugin)

Plugin payload for the [prompt-eng-toolkit marketplace](../../README.md). Two skills + shared references / scripts / fixtures for designing and compressing production single-turn LLM system prompts.

See the [marketplace README](../../README.md) for install instructions, positioning vs. alternatives (promptfoo, AutoPrompt, prompt-architect, linshenkx/prompt-optimizer, …), and usage examples.

## Skills

- **[prompt-create/](./skills/prompt-create/SKILL.md)** — design a new system prompt with injection defenses
- **[prompt-optimize/](./skills/prompt-optimize/SKILL.md)** — compress and harden an existing prompt

## Shared corpus

- **[shared/references/](./shared/references/)** — 5 markdown files (3-provider doc consensus, universal principles, optimization playbook, failure-mode catalog, v4 template)
- **[shared/scripts/count_tokens.py](./shared/scripts/count_tokens.py)** — multi-provider token counter via official APIs
- **[shared/fixtures/attack-tests-template.yaml](./shared/fixtures/attack-tests-template.yaml)** — 7-category injection-test starter
