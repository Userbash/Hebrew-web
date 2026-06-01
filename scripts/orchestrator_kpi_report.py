#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path

p = Path(os.getenv('AI_BRIDGE_KPI_LOG_FILE', 'memory_store/kpi_events.jsonl'))
if not p.exists():
    print(json.dumps({'error':'kpi log not found','path':str(p)}, ensure_ascii=False))
    raise SystemExit(1)

rows=[]
for line in p.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    try:
        rows.append(json.loads(line))
    except Exception:
        pass

by_day={}
for r in rows:
    s=r.get('started_at') or r.get('logged_at')
    if not s:
        continue
    day=s[:10]
    by_day.setdefault(day,[]).append(r)

out={}
for day,items in sorted(by_day.items()):
    lat=[float(x.get('latency_ms') or 0) for x in items]
    lat.sort()
    tok=[x.get('tokens_used') for x in items if isinstance(x.get('tokens_used'),(int,float))]
    ok=sum(1 for x in items if x.get('status')=='done')
    fb=sum(1 for x in items if x.get('fallback_used') is True)
    n=len(items)
    def pct(a,p):
        if not a: return 0
        i=max(0,min(len(a)-1,int((len(a)-1)*p)))
        return round(a[i],2)
    out[day]={
        'tasks_total':n,
        'success_rate':round(ok/n,4) if n else 0,
        'fallback_rate':round(fb/n,4) if n else 0,
        'p50_latency_ms':pct(lat,0.50),
        'p95_latency_ms':pct(lat,0.95),
        'tokens_per_success':round(sum(tok)/ok,2) if ok else 0,
    }

print(json.dumps({'path':str(p),'days':out}, ensure_ascii=False, indent=2))
