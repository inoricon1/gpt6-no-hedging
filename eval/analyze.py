"""Regex counts per condition, read from results/<cond>/*.txt. Add --dump to list matched sentences."""
import glob, os, statistics as st, sys
sys.stdout.reconfigure(encoding="utf-8")
from hedge_patterns import count, count_ext, offending_sentences

ROOT = os.path.dirname(os.path.abspath(__file__))
rows = {}
for f in glob.glob(os.path.join(ROOT, "results", "*", "*_*.txt")):
    cond = os.path.basename(os.path.dirname(f))
    text = open(f, encoding="utf-8").read()
    if not text.strip():
        continue
    r = {"id": os.path.basename(f)[:-4], "output": text}
    r.update(count(text))
    r["ext"] = count_ext(text)
    rows.setdefault(cond, []).append(r)


def line(name, rs):
    n = len(rs)
    m = lambda k: st.mean(x[k] for x in rs)
    with_hit = sum(x["core"] + x["contrast"] > 0 for x in rs) / n
    print(f"{name:8s} n={n:3d}  core/ans={m('core'):.2f}  contrast/ans={m('contrast'):.2f}  "
          f"soft/ans={m('soft'):.2f}  ext/ans={m('ext'):.2f}  ans_with_core|contrast={with_hit:4.0%}  "
          f"chars={m('chars'):.0f}")


for c in sorted(rows):
    line(c, rows[c])

if "--dump" in sys.argv:
    for c in sorted(rows):
        print(f"\n######## {c}")
        for r in sorted(rows[c], key=lambda x: x["id"]):
            for s in offending_sentences(r["output"]):
                print(f"  {r['id']}: {s[:110]}")
