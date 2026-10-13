# gpt6-no-hedging

[中文](README.zh-CN.md) | English

A tested instruction file that stops GPT-6 models from padding every answer with negative scope disclaimers: "this doesn't necessarily mean…", "that alone doesn't prove…", "it's not X, it's Y". In Chinese the same habit shows up as 不代表 / 不能说明 / 不等于 / 不能据此 / 不是……而是…….

## The problem

GPT-6 series models (Sol, Astra, Luna) attach caveats to almost every analytical answer. Codex's built-in system prompt for gpt-6.1-sol already says, in English, "Do not use contrastive framing such as 'X, not Y'" and "avoid vague qualifiers", and the habit survives anyway. Users on linux.do and the OpenAI community forum report the same thing, and a plain list of banned phrases only moves the hedge somewhere else (see results below).

## Quick start

| Where | What to do |
|---|---|
| Codex (CLI / desktop) | Copy [`prompts/AGENTS.zh-CN.md`](prompts/AGENTS.zh-CN.md) or [`prompts/AGENTS.en.md`](prompts/AGENTS.en.md) to `~/.codex/AGENTS.md` (global) or to `AGENTS.md` in your repo |
| ChatGPT web / app | Settings → Personalization → Custom instructions → paste the file into "How would you like ChatGPT to respond?" (the Chinese file is 988 characters, under the 1500 limit) |
| API | Put the file in the system / developer message |

Use the Chinese file if the model answers you in Chinese, the English file if it answers in English.

## Results

Model `gpt-6.1-sol`, reasoning effort `high`, Codex CLI 0.162, 2026-10-12. 12 short Chinese questions that invite caveats (A/B tests, benchmarks, coverage, correlation studies, an interpersonal question, debugging) plus 4 long-form analysis questions, 2 samples per question per group.

**Blind judge** (gpt-6.1-sol, answers shuffled and condition hidden; it quotes every sentence whose job is to limit or disclaim, regardless of wording):

| Group | Hedge sentences per answer | Answers with any | Directness (1-5) | Substance (1-5) |
|---|---|---|---|---|
| No instructions | 2.42 | 88% | 4.21 | 4.92 |
| Plain banned-phrase list | 1.12 | 88% | 4.29 | 4.67 |
| v1 of this prompt | 0.17 | 17% | 4.83 | 4.92 |
| v1 + Stop hook | 0.21 | 17% | 4.83 | 4.88 |
| **v2 (the file in `prompts/`)** | 0 regex hits; manual review of all 24 answers found essentially none | — | — | same as baseline on manual review |

The judge run for v2 did not happen because the account hit its Codex usage limit; v2 was checked by regex and by reading every answer.

**Long-form analysis questions**: without instructions, answers averaged 3.75 disclaimer / contrast patterns each and 8 of 8 had them; v1 and v2 both had 0.

**Template side effects** (how many of 24 answers contain the phrase):

| Phrase | No instructions | Banned list | v1 | v2 |
|---|---|---|---|---|
| 置信度 ("confidence") | 0 | 17 | 0 | 0 |
| 下一步 ("next step") | 1 | 2 | 12 | 0 |
| 缺口 ("gap") | 0 | 0 | 4 | 0 |

Raw answers for every run are in [`eval/results/`](eval/results/).

## What made the difference

1. **A banned list alone fails.** The model drops the listed words and invents a new ritual: 17 of 24 answers ended with "confidence is low because…".
2. **Explain why the reader dislikes it.** The prompt says the reader already knows the textbook caveats and treats them as noise that lowers answer quality.
3. **Define the pattern by what it does.** "A sentence whose job is to say what a fact does not show", with paraphrases such as "remains to be verified" counted as the same thing, so swapping synonyms doesn't get around it.
4. **Show before/after rewrites** into positive statements: what the evidence supports, what data is missing, how to get it.
5. **Give no quotable stock phrases.** v1 suggested "next step" and "the key gap", and the model pasted them into half of its answers. v2 removed them and added "no fixed template".

## Optional: Stop hook

[`hooks/hedge_gate.py`](hooks/hedge_gate.py) is a Codex Stop hook that scans the final answer (Chinese and English patterns) and, on a hit, asks the model to rewrite it once. Install by copying it to `~/.codex/hooks/` and merging [`hooks/hooks.json`](hooks/hooks.json) into `~/.codex/hooks.json`, then trust it with `/hooks` in the CLI.

It is not recommended on its own. With the hook and no prompt, it fired on 13 of 24 answers and cut pattern hits from 1.38 to 0.15 per triggered answer, but the model mostly rephrased "doesn't show" into "still needs verification", added about 8 seconds per answer, and the user sees both the original and the rewritten reply. With the v2 prompt installed it never fired. `python hooks/test_hedge_gate.py` runs its offline tests.

## Reproduce

```bash
cd eval
export CODEX_BIN=codex           # path to the Codex CLI
python runner.py B0,P1,P2,P2b 2  # conditions/<name>/AGENTS.md is loaded; B0 has none
PROMPTS=prompts_long.json python runner.py B0-L,P2b-L 2
python analyze.py                # regex counts
python judge.py B0,P1,P2,P2b     # blind judge
python judge_agg.py
```

Each run uses `codex exec --ignore-user-config --ephemeral -s read-only`, so your own config and AGENTS.md are left out.

## Limitations

- **The English prompt is untested.** All measurements above use the Chinese prompt and Chinese questions. The English file mirrors the same structure for English hedges.
- Sample size is small (24 short + 8 long answers per group, one model).
- Occasional over-correction: one benchmark answer became a bare "Yes, it's faster" and dropped the advice to run more rounds. If that matters to you, delete the sentence "Nobody here penalizes you for reaching a conclusion" (untested change).
- ChatGPT web was not tested; only Codex.
