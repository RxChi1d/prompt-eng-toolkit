# 三家 Provider 官方文件規範整理

整理自三家官方 prompting guide（2026 年 5 月版本）。每段附上原始 URL，引用為英文原文以保留權威性。

---

## 1. Google Gemini（重點：Gemini 3.x）

### 1.1 Prompt 結構

**`systemInstruction` 應放**：
1. Role / persona 定義
2. 行為約束與規則
3. 輸出格式要求

**User content 應放**（依序）：
1. Context / source material（要處理的資料）
2. Main task instruction
3. Negative / formatting / quantitative constraints（**放在最末**）

### 1.2 關鍵原則

- **負向約束放在指令的最後**。長 prompt 中過早出現的負向約束會被模型在處理過程中丟棄。
- **使用任務專屬 persona**。模型會嚴肅對待被指派的角色。
- **使用 grounding language**：明示「provided material is the only source of truth」。
- **指令要直接、有邏輯**。避免說服性語言、避免冗長 prompt engineering 修辭。Gemini 3 是 reasoning-focused 模型，會 over-analyze 老式的繁複 prompt。
- **不要用過度寬泛的負向指令**（例如「do not infer」「do not guess」）。這會讓模型 over-index，連合理推論都被壓抑。
- **不要降溫度**。Gemini 3 在 temperature 1.0 表現最佳；降溫度會引發 looping 或品質下降。
- **盡量短**。Gemini 3「prefers direct, efficient answers」「may over-analyze verbose prompts」。
- **不要在 system 與 user 重複同一條規則**。系統指令 persists across turns，重複只是浪費 token。

### 1.3 官方原文引述

> "Negative constraints should be placed at the end of the instruction."
> — Vertex AI Gemini 3 prompting guide
> https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/gemini-3-prompting-guide

> "Be concise in your input prompts. Gemini 3 responds best to direct, clear instructions. It may over-analyze verbose or overly complex prompt engineering techniques used for older models."
> — Gemini 3 Developer Guide
> https://ai.google.dev/gemini-api/docs/gemini-3

> "Place essential behavioral constraints, role definitions (persona), and output format requirements in the System Instruction or at the very beginning of the user prompt."
> — Gemini API prompt design strategies
> https://ai.google.dev/gemini-api/docs/prompting-strategies

### 1.4 反模式（Anti-patterns）

- 把 critical / negative 規則放在 system prompt 開頭
- 用 `MUST` / `CRITICAL` / `ALWAYS` 等大寫情緒化詞彙
- 為 transcript / data 任務降溫度
- 在 user message 重複 system 已有的規則
- 把 sensitive 規則只放在 system instruction，當作安全保證

---

## 2. Anthropic Claude（重點：Sonnet 4.5+ / Opus 4.5+）

### 2.1 Prompt 結構

**System prompt 內容（依序）**：
1. Role / persona 一句
2. 任務描述與行為約束（用具名 XML 區塊：`<task_rules>`、`<constraints>` 等）
3. 輸出格式規則
4. 負向約束（附上 rationale）
5. Few-shot 範例（包進 `<examples><example>...</example></examples>`）

**User turn 內容**：
1. 長 data / documents 放**頂部**，包進 semantic XML tag（`<transcript>`、`<document>`）
2. Query / 指令放**最末**

### 2.2 關鍵原則

- **XML tags 是 data ↔ instructions 防火牆的主要機制**。Anthropic 推薦 tag 名稱：`<instructions>`、`<context>`、`<input>`、`<document>`（含 `<source>`、`<document_content>` 子標籤）、`<example>` / `<examples>`、`<thinking>`、`<answer>`。
- **避免 `MUST` / `ALWAYS` / `CRITICAL`**。Claude 4.5+ 會 overtrigger，造成過度反應而非更嚴格遵守。改用中性祈使句「Do X when Y」。
- **提供 rationale 比單純禁令更有效**。例：「Your response will be read aloud by TTS, so never use ellipses since TTS won't know how to pronounce them」優於「NEVER use ellipses」。模型會從解釋中 generalize 出邊界。
- **正向框架優於負向**。「Write in flowing prose paragraphs」優於「Do not use bullet points」。
- **Long-context 任務的 30% 法則**：data 在頂部、query 在末端，可提升 ~30% 品質。
- **Scope 要明確**。Opus 4.7 不會 silently generalize；要套用到全部就明寫「Apply this to every section, not just the first」。
- **Prefilled assistant responses 已被 Claude 4.6+ 棄用**。改用 system prompt 直接寫「Respond directly without preamble」。
- **Prompt 風格會影響輸出風格**。想要純文字輸出，就不要在 prompt 裡用 markdown。
- **Claude 4.5+ 的「context wins」傾向**：當 system 指令與 user 內容隱含目標衝突時，模型會做 contextual 判斷而非嚴格遵守。需要用 XML 顯式分離 + 在資料附近重申約束。

### 2.3 官方原文引述

> "Claude Opus 4.5 and Claude Opus 4.6 are also more responsive to the system prompt than previous models. If your prompts were designed to reduce undertriggering on tools or skills, these models may now overtrigger. The fix is to dial back any aggressive language. Where you might have said 'CRITICAL: You MUST use this tool when...', you can use more normal prompting like 'Use this tool when...'"
> — Anthropic prompting best practices
> https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

> "Put longform data at the top: Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. Queries at the end can improve response quality by up to 30% in tests."
> — same URL

> "XML tags help Claude parse complex prompts unambiguously, especially when your prompt mixes instructions, context, examples, and variable inputs. Wrapping each type of content in its own tag (e.g. `<instructions>`, `<context>`, `<input>`) reduces misinterpretation."
> — same URL

> "Claude Opus 4.7 interprets prompts more literally and explicitly than Claude Opus 4.6... It will not silently generalize an instruction from one item to another, and it will not infer requests you didn't make."
> — same URL

### 2.4 反模式

- 用 `MUST` / `CRITICAL` / `ALWAYS` 來「加強」規則
- 全部用負向指令而沒有正向替代
- 短 prompt 也把 data 放頂部（30% 法則只適用於 long-context）
- 仰賴 prefilled assistant response（已棄用）
- 把約束只寫在 system 而不在資料附近重申
- 用 markdown-heavy system prompt 卻期望純文字輸出
- 使用「be careful with this」這種模糊指令（Opus 4.7 不會推測 scope）

---

## 3. OpenAI（重點：GPT-5.x，含所有 OpenAI-compatible 服務）

OpenAI-compatible 服務涵蓋：OpenAI、Groq、Cerebras、Mistral、OpenRouter、NVIDIA、Ollama、LM Studio。本節原則皆適用。

### 3.1 Prompt 結構

`developer` / `system` message 內部排序：

1. **Identity** — 1–2 句，角色定義
2. **Instructions** — 規則，用 XML tag 分組（`<constraints>`、`<output_spec>` 等）
   - 內部子順序：safety / invariant 規則 → 行為規則 → 輸出格式契約 → stopping / completion 條件
3. **Examples** — Few-shot
4. **Context** — 靜態背景資訊

`user` message 只放實際輸入資料。

### 3.2 關鍵原則

- **規則放在 `developer` / `system` role，不要放在 `user` role**。Developer messages 「prioritized ahead of user messages」——這是 instruction hierarchy 最直接的執行機制。
- **XML 標籤提升 instruction adherence**。實證：「`<[instruction]_spec>` 結構顯著提升模型對指令的遵守度」。
- **Outcome-first，不要 process-heavy**。定義「想要的最終輸出」優於列出「step 1, step 2, step 3」。
- **`NEVER` / `MUST` 只用在真正的 invariant**。過度使用會稀釋強調。
- **負向指令要立即配對正向替代**。「Do NOT X」要緊跟「instead, do Y」，不要分開放在不同的 constraint list。
- **明確輸出契約**：「output only the requested format; do not add prose or markdown fences unless requested」。輸出規則寫得鬆會被填入 unwanted behavior。
- **長對話中規則會 drift**。GPT-5 對 markdown 指令的遵守度會在長對話衰退；建議每 3–5 user turns 重附一次規則。
- **Prompt caching 友善排序**：穩定不變的內容放最前面。會變的內容（user 資料）放後面。
- **避免相互矛盾的指令**：會引起 reasoning inefficiency 與行為漂移。

### 3.3 官方原文引述

> "`developer` messages are instructions provided by the application developer, prioritized ahead of `user` messages."
> — OpenAI prompt engineering guide
> https://developers.openai.com/api/docs/guides/prompt-engineering

> "Markdown headers and lists can be helpful to mark distinct sections of a prompt, and to communicate hierarchy to the model... XML tags can help delineate where one piece of content begins and ends."
> — same URL

> "Structured XML specs like `<[instruction]_spec>` improved instruction adherence on their prompts and allows them to clearly reference previous categories and sections."
> — GPT-5 prompting guide
> https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide

> "Occasionally, adherence to Markdown instructions specified in the system prompt can degrade over the course of a long conversation. In the event that you experience this, we've seen consistent adherence from appending a Markdown instruction every 3-5 user messages."
> — same URL

### 3.4 反模式

- 把規則放在 `user` message
- 全用 step-by-step 過程指令而沒有 outcome 契約
- 過度使用 `MUST` / `NEVER` / `ALWAYS`
- 規則與資料混在同一個區塊沒有 XML 分隔
- 同一份 prompt 裡有相互矛盾的指令
- 在輸出契約沒寫清楚的情況下期望模型自行剋制
- 把易變內容（變數、user 資料）放在 prompt 開頭破壞 cache
- 長 agent 對話只仰賴 markdown 格式而不重申規則

---

## 4. 三家差異速查表

| 議題 | Gemini 3 | Claude 4.5+ | GPT-5 |
|---|---|---|---|
| 強烈詞彙（MUST/NEVER） | 可用但避免太寬泛 | **避免**，改用中性祈使句 | 只用於真正 invariant |
| XML tags | 接受、有效 | **強烈推薦** | **強烈推薦** |
| 數據位置 | context 先、constraints 後 | 長 data 頂部、query 末端 | user msg 只放 data |
| Critical 約束位置 | **prompt 最末** | 用 XML 區塊 + 配 rationale | 子順序最後（stopping rules） |
| 溫度建議 | **保持 1.0**（API 預設） | 任務需要決定 | 任務需要決定 |
| 思考預算 | LOW for 確定性任務 | 自動觸發 adaptive thinking | minimal / low for 簡單任務 |
| 重複規則於 user turn | 不建議 | 建議在資料附近重申 | 長對話需 3–5 turns 重附 |
| Prompt cache | 不特別強調 | 不特別強調 | 穩定內容前置以利 caching |

---

## 5. 文件版本與更新

本檔案內容截自 2026 年 5 月。Provider 官方 prompting guide 持續更新：

| Provider | 主要 URL | 更新頻率 |
|---|---|---|
| Google | `ai.google.dev/gemini-api/docs/gemini-3` 、 `docs.cloud.google.com/vertex-ai/generative-ai/docs/start/gemini-3-prompting-guide` | 模型版號發布時更新 |
| Anthropic | `platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices` 、 `platform.claude.com/docs/en/release-notes/system-prompts` | Sonnet / Opus 大版號更新時 |
| OpenAI | `developers.openai.com/api/docs/guides/prompt-engineering` 、 `developers.openai.com/cookbook/examples/gpt-5/*` | GPT 主要版本發布時 |

新版本發布時建議重讀。模型行為（特別是 instruction adherence）在大版號之間可能顯著變化。
