"""Independently acquire market data, classify and publish validated EOD snapshots."""
import argparse,json,logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from market_data import build,liquidity,FILTERS
from benchmark import load,NAME
from classification import acquire
from leadership import stocks,groups,pct,WINDOWS

ROOT=Path(__file__).resolve().parent.parent
PUBLIC=ROOT/"client/public/data"
LOG=logging.getLogger("theme")

def run(bootstrap=None,offline=False):
    mode="Independent per-repository EOD acquisition"
    if bootstrap:
        p=Path(bootstrap);old=json.loads((p/"data/latest.json").read_text())
        source=dict(rows=old["rows"],company_names={r["symbol"]:r.get("name",r["symbol"]) for r in old["rows"]},
                    last_trading_date=old["last_trading_date"],market_data={"bootstrap":True},filters=FILTERS)
        frames={}
        for r in old["rows"]:
            data=json.loads((p/"data/charts"/(r["symbol"]+".json")).read_text())
            f=pd.DataFrame(data["bars"]).rename(columns={"t":"date","o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"})
            f.index=pd.to_datetime(f.pop("date"));frames[r["symbol"]]=f
        # Reapply user's universe using the imported, explicitly dated prices.
        source["rows"]=[{**r,**liquidity(frames[r["symbol"]])[0]} for r in source["rows"] if liquidity(frames[r["symbol"]])[1] and r["market_cap_cr"]>500]
        mode="Dated local bootstrap preview; independent daily run pending"
    else:source,frames=build()
    session=pd.Timestamp(source["last_trading_date"])
    benchmark=(pd.read_csv(ROOT/"pipeline/benchmark_midsmall400.csv",parse_dates=["date"]).set_index("date").loc[:session] if offline else load(session))
    if benchmark.empty or benchmark.index[-1]!=session:raise RuntimeError("Benchmark session does not match EOD")
    mappings,health=acquire([r["symbol"] for r in source["rows"]],offline,preview=bool(bootstrap))
    rows=stocks(source,frames,benchmark,mappings)
    br={k:pct(benchmark.close,n) for k,n in WINDOWS.items()}
    previous=None
    archive=ROOT/"snapshots";archive.mkdir(exist_ok=True)
    earlier=sorted(p for p in archive.glob("*.json") if p.stem<str(session.date()))
    if earlier:previous=json.loads(earlier[-1].read_text())
    group_rows=groups(rows,mappings,br,previous)
    payload=dict(schema_version=1,generated_at=datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
                 last_trading_date=str(session.date()),mode=mode,benchmark=NAME,benchmark_returns=br,
                 filters=FILTERS,market_data=source["market_data"],classification_health=health,stocks=rows,groups=group_rows,
                 notes=["All group statistics use only stocks passing the four strict universe filters on the displayed session.",
                        "Industry labels are provider classifications, not official NSE basic-industry codes.",
                        "Themes use official Nifty constituent membership, not all companies with possible theme exposure. Memberships overlap.",
                        "Group returns are equal-weight arithmetic means of available member period returns. These are custom eligible baskets, not official index returns.",
                        "Leader score: 20% 1W return percentile +30% 1M +30% 3M +20% 3M benchmark-excess percentile.",
                        "Group score: 55% momentum percentile composite (20% 1W,35% 1M,45% 3M),25% benchmark-excess percentile,20% observed SMA50 breadth.",
                        "Industry and theme scores are ranked separately. Ties use average percentiles.",
                        "At least 3 members,3 stocks with 3M history,and 70% 3M coverage are required for a ranked group. Smaller samples remain visible, unranked.",
                        "New listings remain eligible; insufficient lookbacks display unavailable, not zero. Unscored stocks sort below scored leaders.",
                        "Rank change compares the previous published trading session; unavailable on the first session.",
                        "Sparkline is the equal-weight normalized path of current members with 64 bars, not a historical-membership index or backtest.",
                        "19:30 IST daily schedule is best-effort GitHub timing. Non-trading days retain the latest verified completed session.",
                        "Latest price bars are official NSE EOD; vendor historical backfill and shares supply history and market-cap estimates.",
                        "ADR20 is mean(100×(high−low)/previous close). RVOL uses the preceding20 sessions excluding the signal day.",
                        "Price-based research only. Verify corporate actions and classification before trading."])
    if not rows or len(rows)/len(source["rows"])<.95:raise RuntimeError("Less than 95% universe retained")
    text=json.dumps(payload,separators=(",",":"),allow_nan=False)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    temp=PUBLIC/"latest.next.json";temp.write_text(text);temp.replace(PUBLIC/"latest.json")
    (archive/f"{session.date()}.json").write_text(text)
    (PUBLIC/"history").mkdir(exist_ok=True)
    for p in archive.glob("*.json"):(PUBLIC/"history"/p.name).write_bytes(p.read_bytes())
    (PUBLIC/"sessions.json").write_text(json.dumps(sorted([p.stem for p in archive.glob("*.json")],reverse=True)))
    LOG.info("Theme snapshot %s: %s stocks, %s groups, %s ranked",session.date(),len(rows),len(group_rows),sum(g["rank"] is not None for g in group_rows))
    return payload

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(message)s")
    p=argparse.ArgumentParser();p.add_argument("--bootstrap");p.add_argument("--offline",action="store_true")
    a=p.parse_args();run(a.bootstrap,a.offline)
