"""Codex Stop hook: when the final answer contains negative scope disclaimers, ask the model to rewrite it once.
Codex Stop hook：回答里出现否定式边界声明时，让模型重写一次。

Reads the Stop event JSON from stdin and scans last_assistant_message (Chinese and English patterns).
On a hit it prints {"decision": "block", "reason": ...}; Codex feeds the reason back as a new user turn.
When stop_hook_active is true it lets the turn end, so each turn is rewritten at most once.
Set HEDGE_GATE_LOG=<file> to log every trigger.
"""
import json
import os
import re
import sys

ZH_CORE = re.compile(
    r"不代表|并不代表|不等于|不等同|不能等同|不必然|不一定意味着|不意味着|并不意味|"
    r"不能说明|无法说明|不足以说明|说明不了|并不说明|不能证明|无法证明|不足以证明|证明不了|"
    r"不能认为|不能据此|不能直接(?:得出|推出|说明|认定|下结论|归因)|推不出|不能推出|无法推出|"
    r"不能断定|无法断定|不能简单(?:地)?|不宜简单|不构成|不能当(?:作|成)|不能归因|无法归因"
)
ZH_CONTRAST = re.compile(r"不是[^。！？\n]{1,40}?而是|而不是|而非|并非")

_NEG = r"(?:doesn['’]t|does not|don['’]t|do not|isn['’]t|is not|aren['’]t|are not|won['’]t|will not)"
EN_CORE = re.compile(
    _NEG + r"\s+(?:necessarily\s+|automatically\s+)?(?:mean|imply|prove|show|indicate|guarantee|equal|tell us)\b"
    r"|\bisn['’]t the same as\b|\bnot necessarily\b"
    r"|\b(?:we |you )?can(?:not|['’]t)\s+(?:conclude|infer|assume|say for sure)\b"
    r"|\b(?:on its own|by itself|alone)\b[^.!?\n]{0,40}\b(?:isn['’]t|is not|doesn['’]t|does not|can['’]t|cannot)\b"
    r"|^\s*(?:That said|It['’]s worth noting|Keep in mind|Of course),",
    re.I | re.M,
)
EN_CONTRAST = re.compile(
    r"\b(?:it['’]s|this is|that['’]s) not (?:about |just )?[^.!?\n]{1,40}?[,;—–-]+\s*(?:it['’]s|but)\b"
    r"|\bisn['’]t (?:about |just )?[^.!?\n]{1,40}?[.;—–-]+\s*it['’]s\b"
    r"|\b(?:this|it|that)\s+(?:isn['’]t|is not)\s+(?:really\s+|just\s+)?about\b",
    re.I,
)

PATTERNS = (ZH_CORE, ZH_CONTRAST, EN_CORE, EN_CONTRAST)
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
SPLIT = re.compile(r"(?<=[。！？；;\n])|(?<=[.!?])\s+")
CJK = re.compile(r"[一-鿿]")

REASON_ZH = """你上一条回答里有 {n} 处否定式边界声明：
{items}

把整条回答重写一遍：
- 这些句子改成正向陈述：据此能得出什么、还缺什么证据、怎么补上。
- 如果某一处是在直接回答用户提出的"A 是不是等于 B"，保留那一句。
- 其余内容和结论保持不变，长度不要增加。
只输出重写后的完整回答，不要提到这次改写。"""

REASON_EN = """Your last answer contains {n} negative scope disclaimer(s):
{items}

Rewrite the whole answer:
- Turn these sentences into positive statements: what the evidence supports, what is still missing, and how to get it.
- If one of them is the direct answer to an "Is A the same as B?" question the user asked, keep that sentence.
- Keep everything else and every conclusion the same, and don't make it longer.
Output only the rewritten answer and don't mention the rewrite."""


def find_hits(message):
    text = CODE.sub(" ", message or "")
    return [s.strip() for s in SPLIT.split(text)
            if s and s.strip() and any(p.search(s) for p in PATTERNS)]


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    try:
        event = json.load(sys.stdin)
    except Exception:
        return
    if event.get("stop_hook_active"):
        return
    message = event.get("last_assistant_message") or ""
    hits = find_hits(message)
    if not hits:
        return

    log = os.environ.get("HEDGE_GATE_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"session_id": event.get("session_id"), "hits": hits,
                                "first_message": message}, ensure_ascii=False) + "\n")

    chinese = len(CJK.findall(message)) * 3 > len(message)
    template, quote = (REASON_ZH, "- 「%s」") if chinese else (REASON_EN, '- "%s"')
    items = "\n".join(quote % s[:160] for s in hits[:12])
    print(json.dumps({"decision": "block", "reason": template.format(n=len(hits), items=items)}))


if __name__ == "__main__":
    main()
