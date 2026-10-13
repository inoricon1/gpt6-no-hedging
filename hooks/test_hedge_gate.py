"""Offline checks for hedge_gate.py. Run: python test_hedge_gate.py"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hedge_gate import find_hits

SHOULD_HIT = [
    "日活上涨不代表新功能有效。",
    "覆盖率高不等于没有 bug。",
    "这不是数据库的问题，而是网络的问题。",
    "仅凭这个数字，不能据此决定上线。",
    "The DAU increase doesn't necessarily mean the feature worked.",
    "High coverage does not guarantee correctness.",
    "Stars alone isn't a measure of quality.",
    "We can't conclude anything from three runs.",
    "It's not a database issue, it's the network.",
    "That said, you should still run more benchmarks.",
    "This isn't about speed. It's about correctness.",
]
SHOULD_PASS = [
    "现在看不出新功能的作用，大盘同期也在涨。",
    "问题出在网络上：TCP 重传率从 0.1% 升到 3%。",
    "The market grew too, so measure the feature against a control group.",
    "Stars measure attention. Check the maintenance history before adopting it.",
    "Most likely lock contention; pg_stat_activity will confirm it.",
    "Use `x not in result` only on small lists.",
    "```python\nif x is not None and not necessarily_slow(x):\n    pass\n```",
]

fails = 0
for s in SHOULD_HIT:
    if not find_hits(s):
        print("MISSED:", s); fails += 1
for s in SHOULD_PASS:
    if find_hits(s):
        print("FALSE POSITIVE:", s, find_hits(s)); fails += 1

gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hedge_gate.py")
def run(event):
    r = subprocess.run([sys.executable, gate], input=json.dumps(event), capture_output=True,
                       encoding="utf-8")
    return r.stdout.strip()

out = run({"stop_hook_active": False, "last_assistant_message": SHOULD_HIT[0]})
if json.loads(out).get("decision") != "block" or "否定式边界声明" not in json.loads(out)["reason"]:
    print("zh block failed:", out); fails += 1
out = run({"stop_hook_active": False, "last_assistant_message": SHOULD_HIT[4]})
if json.loads(out).get("decision") != "block" or "negative scope" not in json.loads(out)["reason"]:
    print("en block failed:", out); fails += 1
if run({"stop_hook_active": True, "last_assistant_message": SHOULD_HIT[0]}):
    print("stop_hook_active not respected"); fails += 1
if run({"stop_hook_active": False, "last_assistant_message": SHOULD_PASS[0]}):
    print("clean answer was blocked"); fails += 1

print("FAILURES:", fails)
sys.exit(1 if fails else 0)
