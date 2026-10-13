"""Blind LLM judge: shuffles answers from the given conditions, hides the condition, scores them in batches.

usage: python judge.py <cond[,cond...]> [tag]
Writes results/judge_key<tag>.json (id -> condition) and results/judge<tag>_NN.json.
"""
import glob, json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
CODEX = os.environ.get("CODEX_BIN", "codex")
MODEL = os.environ.get("MODEL", "gpt-6.1-sol")
P = {p["id"]: p["text"] for fn in ("prompts.json", "prompts_long.json")
     for p in json.load(open(os.path.join(ROOT, fn), encoding="utf-8"))}
CONDS = sys.argv[1].split(",")
TAG = sys.argv[2] if len(sys.argv) > 2 else ""

recs = []
for c in CONDS:
    for f in sorted(glob.glob(os.path.join(ROOT, "results", c, "*_*.txt"))):
        text = open(f, encoding="utf-8").read()
        qid, s = os.path.basename(f)[:-4].split("_")
        if text.strip():
            recs.append({"cond": c, "qid": qid, "sample": int(s), "output": text})
random.seed(7)
random.shuffle(recs)
key = {"a%03d" % i: (r["cond"], r["qid"], r["sample"]) for i, r in enumerate(recs)}
json.dump(key, open(os.path.join(ROOT, "results", "judge_key%s.json" % TAG), "w"), indent=0)
rubric = open(os.path.join(ROOT, "judge_prompt.md"), encoding="utf-8").read()
wd = os.path.join(ROOT, "judge_wd")
os.makedirs(wd, exist_ok=True)
BS = 4 if TAG.endswith("L") else 8
batches = [list(range(i, min(i + BS, len(recs)))) for i in range(0, len(recs), BS)]


def run(bi):
    out = os.path.join(ROOT, "results", "judge%s_%02d.json" % (TAG, bi))
    if os.path.exists(out):
        return
    body = rubric + "\n\n"
    for i in batches[bi]:
        r = recs[i]
        body += "=== id: a%03d\n【问题】%s\n【回答】\n%s\n\n" % (i, P[r["qid"]], r["output"])
    args = [CODEX, "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
            "-m", MODEL, "-c", 'model_reasoning_effort="medium"', "-s", "read-only",
            "-C", wd, "--output-schema", os.path.join(ROOT, "judge_schema.json"), "-o", out, "-"]
    r = subprocess.run(args, input=body, capture_output=True, encoding="utf-8", errors="replace", timeout=900)
    print("batch", bi, r.returncode, flush=True)


if __name__ == "__main__":
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(run, range(len(batches))))
    print("JUDGE DONE")
