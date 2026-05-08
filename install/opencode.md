# Install prompt-eng-toolkit in OpenCode

> **For the OpenCode agent reading this file**: follow the steps below to install the `prompt-eng-toolkit` skills (`prompt-create`, `prompt-optimize`) into the user's OpenCode environment. Confirm with the user before any destructive action.

## What you will install

Two skills plus their shared corpus (5 reference docs, 1 token-counting script, 1 attack-fixture template). After install, OpenCode auto-discovers the skills via its `skill` tool — no restart required (OpenCode polls every ~10s).

Source repo: https://github.com/RxChi1d/prompt-eng-toolkit

## Step 1 — Ask the user about install scope

Confirm exactly one of:

- **Per-project** — install only for the current working directory's project. Target: `<cwd>/.opencode/`.
- **Global** — install for every OpenCode project on this machine. Target: `~/.config/opencode/`.

Default suggestion: **global**. The skills are tool-agnostic and have no project-specific state.

## Step 2 — Clone (or update) the source repo

Use a stable cache location. Run exactly one of these:

```bash
# Fresh clone (run if the directory does not exist)
git clone https://github.com/RxChi1d/prompt-eng-toolkit ~/.local/share/prompt-eng-toolkit

# Or update an existing clone (run if the directory already exists)
git -C ~/.local/share/prompt-eng-toolkit pull --ff-only
```

Check first with `test -d ~/.local/share/prompt-eng-toolkit` and pick the right command. Do not silently `rm -rf` an existing checkout.

## Step 3 — Confirm before touching any existing target

Set `TARGET` based on Step 1:
- per-project: `TARGET=$(pwd)/.opencode`
- global: `TARGET=$HOME/.config/opencode`

Then check whether `$TARGET/skills` or `$TARGET/shared` already exist. **If either exists**, stop and report what you found. Ask the user one of:
- "Replace existing `skills` / `shared` symlinks/directories?"
- "Pick a different scope (per-project vs global)?"
- "Cancel?"

Only proceed once the user confirms. Never overwrite a real directory (only safe to replace existing symlinks).

## Step 4 — Create the install symlinks

```bash
mkdir -p "$TARGET"
ln -sfn ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/skills  "$TARGET/skills"
ln -sfn ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/shared  "$TARGET/shared"
```

Both symlinks are required. The SKILL.md files reference shared docs via `../../shared/...` — that path only resolves correctly when `skills/` and `shared/` sit in the same parent directory.

If symlinks aren't supported on the user's filesystem (e.g., some Windows setups), copy instead:

```bash
cp -R ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/skills  "$TARGET/skills"
cp -R ~/.local/share/prompt-eng-toolkit/plugins/prompt-eng-toolkit/shared  "$TARGET/shared"
```

Note: with `cp`, future updates require re-running the copy. With symlinks, just `git pull` in the cache.

## Step 5 — Verify

```bash
ls "$TARGET/skills"          # expect: prompt-create  prompt-optimize
ls "$TARGET/shared"          # expect: fixtures  references  scripts
test -f "$TARGET/skills/prompt-create/SKILL.md" && echo "SKILL.md OK"
test -f "$TARGET/shared/scripts/count_tokens.py" && echo "shared OK"
```

All four checks must succeed. If any fails, debug before reporting success.

## Step 6 — Report to the user

Tell the user:

1. Install scope chosen and the target path
2. Files / symlinks created
3. That the skills will appear within ~10 seconds (OpenCode's scan interval)
4. How to invoke:
   - "Help me write a system prompt for X" → `prompt-create`
   - "This prompt is too long" → `prompt-optimize`
5. How to update later: `git -C ~/.local/share/prompt-eng-toolkit pull` (no re-install needed for symlinks)
6. How to uninstall: `rm "$TARGET/skills" "$TARGET/shared"` (only removes the symlinks; `~/.local/share/prompt-eng-toolkit` stays so other projects keep working)

## Uninstall (run if the user asks)

```bash
# Remove the symlinks/copies for this scope
rm -rf "$TARGET/skills" "$TARGET/shared"

# Optional: remove the cached repo (only if no other scope uses it)
rm -rf ~/.local/share/prompt-eng-toolkit
```

Confirm with the user before running either, especially the second.
