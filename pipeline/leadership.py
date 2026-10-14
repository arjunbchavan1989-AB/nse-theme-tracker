"""Transparent, current-universe leadership composites. Not an investable index."""
import math
import numpy as np
import pandas as pd
WINDOWS={"d1":1,"w1":5,"m1":21,"m3":63}

def number(v):
    return round(float(v),4) if v is not None and math.isfinite(float(v)) else None

def pct(series,n):
    return number((series.iloc[-1]/series.iloc[-n-1]-1)*100) if len(series)>n else None

def stocks(source,frames,benchmark,mappings):
    rows=[]
    for parent in source["rows"]:
        symbol=parent["symbol"];f=frames.get(symbol)
        if f is None or len(f)<21:continue
        c=f.Close;meta=mappings["industries"].get(symbol,{})
        aligned=pd.concat([c.rename("s"),benchmark.close.rename("b")],axis=1,join="inner").dropna()
        if aligned.empty or aligned.index[-1]!=c.index[-1]:raise ValueError("Stock/benchmark session mismatch")
        ret={k:pct(c,n) for k,n in WINDOWS.items()}
        rs=number((aligned.s.iloc[-1]/aligned.s.iloc[-64]-aligned.b.iloc[-1]/aligned.b.iloc[-64])*100) if len(aligned)>=64 else None
        ma=c.rolling(50).mean()
        rows.append({**parent,"name":source.get("company_names",{}).get(symbol,parent.get("name",symbol)),
                     **ret,"rs_excess":rs,"above50":int(c.iloc[-1]>ma.iloc[-1])*100 if len(c)>=50 else None,
                     "near_high":int(c.iloc[-1]>=.9*f.High.tail(252).max())*100 if len(f)>=252 else None,
                     "rvol":number(f.Volume.iloc[-1]/f.Volume.iloc[-21:-1].mean()),
                     "industry":meta.get("industry") or "Unclassified","sector":meta.get("sector") or "Unclassified",
                     "classification_source":meta.get("source","Missing"),"classification_date":meta.get("date",""),
                     "themes":[name for name,t in mappings["themes"].items() if symbol in t["symbols"]],
                     "history_bars":len(f),"spark":[number(v/c.iloc[-min(len(c),64)]*100) for v in c.tail(64)],"score":None})
    ranked=[r for r in rows if all(r[k] is not None for k in ("w1","m1","m3","rs_excess"))]
    if ranked:
        df=pd.DataFrame(ranked)
        # Rank each component across the full filtered stock universe.
        score=.2*df.w1.rank(pct=True)+.3*df.m1.rank(pct=True)+.3*df.m3.rank(pct=True)+.2*df.rs_excess.rank(pct=True)
        for r,v in zip(ranked,score):r["score"]=number(v*100)
    return rows

def aggregate(rows,kind,name,benchmark_returns,source_url="",mapping_date=""):
    metrics={};coverage={}
    for k in WINDOWS:
        values=[r[k] for r in rows if r[k] is not None]
        metrics[k]=number(np.mean(values)) if values else None
        coverage[k]=len(values)
    above=[r["above50"] for r in rows if r["above50"] is not None]
    near=[r["near_high"] for r in rows if r["near_high"] is not None]
    rs=[r["rs_excess"] for r in rows if r["rs_excess"] is not None]
    # Fixed current-member basket, common aligned 64 bars. No membership backtest.
    sparks=[r["spark"] for r in rows if len(r["spark"])==64]
    spark=[number(x) for x in np.mean(sparks,axis=0)] if sparks else []
    return dict(id=kind+":"+name,name=name,kind=kind,members=[r["symbol"] for r in rows],count=len(rows),
                **metrics,rs_excess=number(np.mean(rs)) if rs else None,
                above50=number(np.mean(above)) if above else None,near_high=number(np.mean(near)) if near else None,
                rvol=number(np.median([r["rvol"] for r in rows if r["rvol"] is not None])) if rows else None,
                spark=spark,score=None,rank=None,rank_change=None,status="Limited sample",momentum=None,breadth=None,
                leadership=None,coverage_m3=coverage["m3"],source_url=source_url,mapping_date=mapping_date,
                leaders=[r["symbol"] for r in sorted(rows,key=lambda r:(r["score"] is not None,r["score"] or -1,r["m1"] or -999,r["symbol"]),reverse=True)[:10]])

def groups(rows,mappings,benchmark_returns,previous=None):
    output=[]
    for name in sorted({r["industry"] for r in rows if r["industry"]!="Unclassified"}):
        members=[r for r in rows if r["industry"]==name]
        output.append(aggregate(members,"industry",name,benchmark_returns))
    for name,t in mappings["themes"].items():
        members=[r for r in rows if name in r["themes"]]
        output.append(aggregate(members,"theme",name,benchmark_returns,t["url"],t["date"]))
    for kind in ("industry","theme"):
        eligible=[g for g in output if g["kind"]==kind and g["count"]>=3 and
                  g["coverage_m3"]>=3 and g["coverage_m3"]/g["count"]>=.7 and
                  all(g[k] is not None for k in ("w1","m1","m3","rs_excess","above50"))]
        if not eligible:continue
        df=pd.DataFrame(eligible)
        momentum=(.2*df.w1.rank(pct=True)+.35*df.m1.rank(pct=True)+.45*df.m3.rank(pct=True))*100
        relative=df.rs_excess.rank(pct=True)*100
        # Breadth is an observed percentage, not another opaque percentile.
        scores=.55*momentum+.25*relative+.2*df.above50
        for g,m,r,s in zip(eligible,momentum,relative,scores):
            g.update(momentum=number(m),leadership=number(r),breadth=g["above50"],score=number(s))
            g["status"]="Leading" if r>=50 and g["m1"]>0 else "Improving" if g["w1"]>0 else "Lagging"
        eligible.sort(key=lambda g:(-g["score"],g["name"]))
        old={g["id"]:g for g in (previous or {}).get("groups",[])}
        for rank,g in enumerate(eligible,1):
            g["rank"]=rank
            before=old.get(g["id"],{}).get("rank")
            g["rank_change"]=before-rank if before is not None else None
    return output
