"""Aggregate blind-judge scores per condition. usage: python judge_agg.py [tag ...] [--dump]"""
import glob, json, os, statistics as st, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
tags = [a for a in sys.argv[1:] if not a.startswith("--")] or [""]
by = {}
for tag in tags:
    key = json.load(open(os.path.join(ROOT, "results", "judge_key%s.json" % tag)))
    for f in glob.glob(os.path.join(ROOT, "results", "judge%s_[0-9]*.json" % tag)):
        for it in json.load(open(f, encoding="utf-8"))["items"]:
            c, q, s = key[it["id"]]
            it.update(cond=c, qid=q, sample=s)
            by.setdefault(c, []).append(it)

for c in sorted(by):
    rs = by[c]
    m = lambda k: st.mean(x[k] for x in rs)
    print(f"{c}: n={len(rs)} hedge/ans={m('hedge_count'):.2f} "
          f"ans_with_hedge={sum(x['hedge_count'] > 0 for x in rs) / len(rs):.0%} "
          f"verdict_first={sum(x['verdict_first'] for x in rs) / len(rs):.0%} "
          f"substance={m('substance'):.2f} directness={m('directness'):.2f}")

if "--dump" in sys.argv:
    for c in sorted(by):
        print("\n####", c)
        for x in sorted(by[c], key=lambda x: x["qid"]):
            for h in x["hedge_sentences"]:
                print(f"  {x['qid']}_{x['sample']}: {h[:100]}")
