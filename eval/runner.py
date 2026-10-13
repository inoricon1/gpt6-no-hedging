"""Run every prompt in a question set under one or more conditions with `codex exec`.

usage: python runner.py <cond[,cond...]> <samples> [workers]
  cond    a folder name under conditions/ (its AGENTS.md is loaded as project instructions);
          a suffix after "-" only renames the result folder, e.g. P2b-L uses conditions/P2b
  env     CODEX_BIN  path to codex (default: codex)
          MODEL      default gpt-6.1-sol
          EFFORT     default high
          PROMPTS    question file (default prompts.json)
Conditions P3 and H also enable ../hooks/hedge_gate.py as a Stop hook.
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

CODEX = os.environ.get("CODEX_BIN", "codex")
MODEL = os.environ.get("MODEL", "gpt-6.1-sol")
EFFORT = os.environ.get("EFFORT", "high")
ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPTS = json.load(open(os.path.join(ROOT, os.environ.get("PROMPTS", "prompts.json")), encoding="utf-8"))
GATE = os.path.join(ROOT, "..", "hooks", "hedge_gate.py").replace("\\", "/")
HOOK_CONDS = ("P3", "H")


def run(job):
    cond, p, s = job
    base = cond.split("-")[0]
    outdir = os.path.join(ROOT, "results", cond)
    os.makedirs(outdir, exist_ok=True)
    rec_path = os.path.join(outdir, "%s_%d.json" % (p["id"], s))
    if os.path.exists(rec_path):
        return
    wd = os.path.join(ROOT, "conditions", base)
    os.makedirs(wd, exist_ok=True)
    last = os.path.join(outdir, "%s_%d.txt" % (p["id"], s))
    args = [CODEX, "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
            "-m", MODEL, "-c", 'model_reasoning_effort="%s"' % EFFORT,
            "-s", "read-only", "-C", wd, "-o", last]
    env = dict(os.environ)
    if base in HOOK_CONDS:
        args += ["--dangerously-bypass-hook-trust", "-c",
                 'hooks.Stop=[{hooks=[{type="command",command="python \\"%s\\"",timeout=30}]}]' % GATE]
        env["HEDGE_GATE_LOG"] = os.path.join(ROOT, "results", "gate_log.jsonl")
    args.append(p["text"])
    t0 = time.time()
    r = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                       encoding="utf-8", errors="replace", env=env, timeout=900)
    m = re.search(r"session id: (\S+)", r.stderr + r.stdout)
    out = open(last, encoding="utf-8").read() if os.path.exists(last) else ""
    rec = {"cond": cond, "qid": p["id"], "sample": s, "rc": r.returncode,
           "session": m.group(1) if m else None, "secs": round(time.time() - t0, 1),
           "blocked": "Stop Blocked" in (r.stderr + r.stdout), "output": out,
           "err_tail": r.stderr[-800:] if r.returncode else ""}
    json.dump(rec, open(rec_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(cond, p["id"], s, r.returncode, rec["secs"], flush=True)


if __name__ == "__main__":
    conds = sys.argv[1].split(",")
    samples = int(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    jobs = [(c, p, s) for s in range(samples) for p in PROMPTS for c in conds]
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, jobs))
    print("DONE")
