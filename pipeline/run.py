"""Independently acquire market data, classify and publish validated EOD snapshots."""
import argparse,json,logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from market_data import build,liquidity,FILTERS
from benchmark import load,NAME
from classification import acquire
from leadership import stocks,groups,pct,WINDOWS,above_sma50

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
    base_rows=stocks(source,frames,benchmark,mappings)
    if not base_rows or len(base_rows)/len(source["rows"])<.95:raise RuntimeError("Less than 95% pre-trend universe retained")
    rows=above_sma50(base_rows)
    policy=dict(id="above_sma50_industry2_v1",close_above_sma50=True,industry_min_members=2,theme_min_members=3,
                breadth_denominator="Original four-filter group members with known SMA50",
                stock_score_universe="Above-SMA50 stocks passing all four base filters")
    br={k:pct(benchmark.close,n) for k,n in WINDOWS.items()}
    previous=None
    archive=ROOT/"snapshots";archive.mkdir(exist_ok=True)
    earlier=sorted(p for p in archive.glob("*.json") if p.stem<str(session.date()))
    if earlier:previous=json.loads(earlier[-1].read_text())
    if previous and previous.get("selection_policy",{}).get("id")!=policy["id"]:previous=None
    group_rows=groups(rows,mappings,br,previous,breadth_rows=base_rows)
    market_health={**source["market_data"],"base_universe_count":len(base_rows),"above_sma50_count":len(rows),
                   "excluded_at_or_below_sma50":sum(r["above50"]==0 for r in base_rows),
                   "excluded_sma50_unavailable":sum(r["above50"] is None for r in base_rows)}
    payload=dict(schema_version=1,generated_at=datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
                 last_trading_date=str(session.date()),mode=mode,benchmark=NAME,benchmark_returns=br,
                 filters={**FILTERS,"close_above_sma50":True},selection_policy=policy,
                 market_data=market_health,classification_health=health,stocks=rows,groups=group_rows,
                 notes=["Classified stocks must pass all four base filters AND close strictly above SMA50. Equality, below-SMA50 closes and insufficient 50-bar history are excluded.",
                        "Industry labels are provider classifications, not official NSE basic-industry codes.",
                        "Themes use official Nifty constituent membership, not all companies with possible theme exposure. Memberships overlap.",
                        "Group returns are equal-weight arithmetic means of available member period returns. These are custom eligible baskets, not official index returns.",
                        "Leader score: 20% 1W return percentile +30% 1M +30% 3M +20% 3M benchmark-excess percentile.",
                        "Group score: 55% momentum percentile composite (20% 1W,35% 1M,45% 3M),25% benchmark-excess percentile,20% original four-filter group SMA50 breadth.",
                        "Industry and theme scores are ranked separately. Ties use average percentiles.",
                        "Industries require at least 2 above-SMA50 members and 2 with 3M history; themes retain 3 members and 3 with 3M history. Both require at least 70% 3M coverage. One-stock industries are omitted.",
                        "Stocks require 50 bars to assess SMA50. Those with 50–63 bars can qualify but remain unscored until 3M data is available.",
                        "Breadth uses original four-filter group members with known SMA50, including those below it; returns, charts, counts and leaders use only the above-SMA50 subset.",
                        "Rank change compares the previous published trading session under the same selection policy; unavailable across a rule change.",
                        "Sparkline is the equal-weight normalized path of current members with 64 bars, not a historical-membership index or backtest.",
                        "19:30 IST daily schedule is best-effort GitHub timing. Non-trading days retain the latest verified completed session.",
                        "Latest price bars are official NSE EOD; vendor historical backfill and shares supply history and market-cap estimates.",
                        "ADR20 is mean(100×(high−low)/previous close). RVOL uses the preceding20 sessions excluding the signal day.",
                        "Price-based research only. Verify corporate actions and classification before trading."])
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
