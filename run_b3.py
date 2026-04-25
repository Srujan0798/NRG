#!/usr/bin/env python3
"""B3 full stack restart verification."""
import subprocess, json, os

log_lines = []

def do(cmd_desc, cmd_list, timeout=30):
    print(f"\n=== {cmd_desc} ===")
    try:
        r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        err = r.stderr.strip()
        combined = (out + "\n" + err).strip()[:500]
        log_lines.append(f"=== {cmd_desc} ===\n{combined}\n")
        print(combined[:300])
        return combined
    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        log_lines.append(f"=== {cmd_desc} === TIMEOUT\n")
        return ""

# Phase 2: Qdrant health
do("Qdrant health", ["curl", "-s", "http://localhost:6333/"])

# Qdrant collection
do("Qdrant collection check", ["curl", "-s", "http://localhost:6333/collections/nrg_research"])

# Backend health
r = subprocess.run([".venv/bin/python", "-c",
    "import requests; r=requests.get('http://localhost:8000/health', timeout=10); d=r.json(); print(d.get('status'), '| vectors:', d.get('retriever',{}).get('vectors_total',0), '| db:', d.get('database',{}).get('status'))"],
    capture_output=True, text=True, timeout=15)
print(f"Backend: {r.stdout.strip()}")
log_lines.append(f"Backend health: {r.stdout}\n")

# Login T1
for t, u, p in [("T1","researcher_user","researcher-pass"),("T2","gov_user","government-pass"),("T3","industry_user","industry-pass")]:
    r = subprocess.run([".venv/bin/python", "-c",
        f"import requests; r=requests.post('http://localhost:8000/login', json={{'username':'{u}','password':'{p}'}}, timeout=10); print('PASS' if r.json().get('access_token') else 'FAIL: '+str(r.status_code))"],
        capture_output=True, text=True, timeout=15)
    print(f"Login {t}: {r.stdout.strip()}")
    log_lines.append(f"Login {t} ({u}): {r.stdout}\n")

# Query test
r = subprocess.run([".venv/bin/python", "-c",
    "import requests; r=requests.post('http://localhost:8000/login', json={'username':'researcher_user','password':'researcher-pass'}, timeout=10); "
    "token=r.json()['access_token']; "
    "rq=requests.post('http://localhost:8000/query', json={'question':'How many researchers in Karnataka?'}, headers={'Authorization': f'Bearer {token}'}, timeout=90); "
    "d=rq.json(); print('status:', d.get('status'), '| response:', d.get('response','')[:300])"],
    capture_output=True, text=True, timeout=120)
print(f"Query: {r.stdout.strip()[:500]}")
log_lines.append(f"Query test: {r.stdout}\n")

# Minimax check
r = subprocess.run(["tail", "-100", "/tmp/uvicorn.log"], capture_output=True, text=True, timeout=5)
lines = [l for l in r.stdout.split('\n') if 'minimax' in l.lower() or 'mesh' in l.lower() or 'synthesizer' in l.lower()]
if lines:
    print(f"Minimax/Mesh: {lines[0][:200]}")
    log_lines.append(f"Minimax/Mesh: {lines[0]}\n")
else:
    print("Minimax: not in recent logs")

# Save evidence
os.makedirs("evidence/2026-04-25/critical_blockers", exist_ok=True)
with open("evidence/2026-04-25/critical_blockers/B3_full_restart_verification.log", "w") as f:
    f.write("\n".join(log_lines))
print("\nSaved: evidence/2026-04-25/critical_blockers/B3_full_restart_verification.log")