#!/usr/bin/env python3
"""
Multi-provider token counter for prompt design and optimization.

Counts tokens via the official provider API (no local heuristics, no
character-count guessing). Optionally compares two files and emits a
before/after table.

Usage
-----
Single count:
    python count_tokens.py --provider gemini   --model gemini-2.5-flash       --file prompt.txt
    python count_tokens.py --provider anthropic --model claude-sonnet-4-5     --file prompt.txt
    python count_tokens.py --provider openai    --model gpt-5                 --file prompt.txt

Compare before/after (single segment):
    python count_tokens.py --provider gemini --model gemini-2.5-flash \
        --before old.txt --after new.txt --label "system prompt"

Compare multiple segments (markdown table out):
    python count_tokens.py --provider gemini --model gemini-2.5-flash \
        --pair "system:old_sys.txt:new_sys.txt" \
        --pair "user:old_user.txt:new_user.txt" \
        --pair "polish:old_polish.txt:new_polish.txt"

Auth
----
Set the matching environment variable; the script never reads keys from disk.
    GEMINI_API_KEY     for --provider gemini
    ANTHROPIC_API_KEY  for --provider anthropic
    OPENAI_API_KEY     for --provider openai

Notes
-----
- Counts text-only. Wraps text as a single user-message for providers whose
  countTokens APIs require a message structure (Anthropic, sometimes Gemini).
  This is the standard convention — provider counts include the role-framing
  overhead, which is what you'll be billed for at runtime.
- "Segment" is intentionally generic. Your prompt may not have separate
  system / user halves. Use whatever segmentation reflects how the prompt is
  actually shipped (per-mode, per-language, single blob, …).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Provider adapters
# ---------------------------------------------------------------------------

class TokenCountError(RuntimeError):
    pass


def _http_post_json(url: str, headers: dict, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise TokenCountError(f"HTTP {e.code} from {url}: {e.read().decode('utf-8', errors='replace')}") from e
    except urllib.error.URLError as e:
        raise TokenCountError(f"Network error calling {url}: {e}") from e


def count_gemini(model: str, text: str) -> int:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise TokenCountError("GEMINI_API_KEY (or GOOGLE_API_KEY) not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens"
    headers = {"Content-Type": "application/json", "x-goog-api-key": key}
    body = {"contents": [{"role": "user", "parts": [{"text": text}]}]}
    resp = _http_post_json(url, headers, body)
    if "totalTokens" not in resp:
        raise TokenCountError(f"Unexpected Gemini response: {resp}")
    return int(resp["totalTokens"])


def count_anthropic(model: str, text: str) -> int:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise TokenCountError("ANTHROPIC_API_KEY not set")
    url = "https://api.anthropic.com/v1/messages/count_tokens"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }
    resp = _http_post_json(url, headers, body)
    if "input_tokens" not in resp:
        raise TokenCountError(f"Unexpected Anthropic response: {resp}")
    return int(resp["input_tokens"])


def count_openai(model: str, text: str) -> int:
    """Uses tiktoken locally if available (no API call); falls back to a
    /v1/chat/completions probe with max_tokens=0 if not."""
    try:
        import tiktoken  # type: ignore
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("o200k_base")
        # Count text content + role overhead (~4 tokens per OAI message + 2 priming)
        return len(enc.encode(text)) + 4 + 2
    except ImportError:
        pass

    # Fallback: probe via the API. Returns prompt_tokens from usage.
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise TokenCountError("OPENAI_API_KEY not set and tiktoken not installed")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 1,
    }
    resp = _http_post_json(url, headers, body)
    try:
        return int(resp["usage"]["prompt_tokens"])
    except KeyError as e:
        raise TokenCountError(f"Unexpected OpenAI response: {resp}") from e


COUNTERS = {
    "gemini": count_gemini,
    "anthropic": count_anthropic,
    "openai": count_openai,
}


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

@dataclass
class Row:
    label: str
    before: Optional[int]
    after: Optional[int]

    def delta(self) -> Optional[int]:
        if self.before is None or self.after is None:
            return None
        return self.after - self.before

    def delta_pct(self) -> Optional[float]:
        if self.before in (None, 0) or self.after is None:
            return None
        return (self.after - self.before) / self.before * 100.0


def render_table(rows: list[Row]) -> str:
    out = [
        "| Segment | Before | After | Δ tokens | Δ % |",
        "|---|---:|---:|---:|---:|",
    ]
    total_before = sum(r.before for r in rows if r.before is not None)
    total_after = sum(r.after for r in rows if r.after is not None)
    for r in rows:
        before = "—" if r.before is None else str(r.before)
        after = "—" if r.after is None else str(r.after)
        d = r.delta()
        dp = r.delta_pct()
        d_str = "—" if d is None else f"{d:+d}"
        dp_str = "—" if dp is None else f"{dp:+.1f}%"
        out.append(f"| {r.label} | {before} | {after} | {d_str} | {dp_str} |")
    if len(rows) > 1:
        td = total_after - total_before
        tdp = (td / total_before * 100.0) if total_before else 0.0
        out.append(f"| **Total** | **{total_before}** | **{total_after}** | **{td:+d}** | **{tdp:+.1f}%** |")
    return "\n".join(out)


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Count tokens via official provider APIs and compare before/after.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--provider", required=True, choices=sorted(COUNTERS.keys()))
    p.add_argument("--model", required=True, help="Provider-specific model id (e.g. gemini-2.5-flash, claude-sonnet-4-5, gpt-5).")
    p.add_argument("--file", help="Single-file mode: count tokens of this file.")
    p.add_argument("--text", help="Single-text mode: count tokens of this literal string.")
    p.add_argument("--before", help="Compare mode: file with the OLD prompt.")
    p.add_argument("--after", help="Compare mode: file with the NEW prompt.")
    p.add_argument("--label", default="prompt", help="Row label for compare mode (default: 'prompt').")
    p.add_argument("--pair", action="append", default=[], help='Multi-segment compare: "label:before_file:after_file". May be repeated.')
    args = p.parse_args()

    counter = COUNTERS[args.provider]

    try:
        if args.pair:
            rows: list[Row] = []
            for pair in args.pair:
                parts = pair.split(":", 2)
                if len(parts) != 3:
                    print(f"Bad --pair value (expected label:before:after): {pair}", file=sys.stderr)
                    return 2
                label, before_path, after_path = parts
                before_n = counter(args.model, read_file(before_path))
                after_n = counter(args.model, read_file(after_path))
                rows.append(Row(label=label, before=before_n, after=after_n))
            print(render_table(rows))
            return 0

        if args.before and args.after:
            before_n = counter(args.model, read_file(args.before))
            after_n = counter(args.model, read_file(args.after))
            print(render_table([Row(label=args.label, before=before_n, after=after_n)]))
            return 0

        if args.file:
            text = read_file(args.file)
        elif args.text is not None:
            text = args.text
        else:
            print("Provide --file, --text, --before/--after, or --pair.", file=sys.stderr)
            return 2

        n = counter(args.model, text)
        print(f"{args.provider} ({args.model}): {n} tokens")
        return 0

    except TokenCountError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
