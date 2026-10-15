# Theme Atlas | Indian Market Leadership

Separate Indian-equity industry and official-theme research dashboard. Public GitHub Pages deployment is generated from validated, dated daily snapshots, not intraday streaming data.

## Universe

All four thresholds are strict:

- Market cap > ₹500 crore, estimated from raw close × shares outstanding.
- 20-session mean share volume > 70,000.
- 20-session mean close × volume > ₹3 crore.
- ADR20 > 3%, using mean(100 × (high − low) / previous close), not gap-inclusive true range.

RS reference: **Nifty MidSmallcap 400**, exact dated exchange benchmark.

Classification now additionally requires **EOD close strictly above SMA50**.
Equal/below closes and stocks with fewer than50 sessions are excluded from
industry/theme memberships, returns, charts and leader lists. This is an enforced
pipeline rule, not an optional browser checkbox.

## Industry groups and official themes

Industry classification is versioned finance-provider metadata, with labelled Yahoo Finance fallback for missing names. It is **not** the official NSE four-tier classification. Initial classification metadata was retrieved on 15 October 2026; review classifications periodically, particularly after demergers and business changes. Missing names are enriched on each production run; unknowns remain visible in data health and are not guessed into an industry.

Theme membership uses official Nifty constituent CSVs, refreshed daily with a maximum 14-day own verified cache fallback. These are **index-member theme baskets**, not every Indian company with possible exposure. Themes overlap. Only members passing the user's universe filters enter the custom basket. A theme with no eligible members is visible when the minimum-stocks filter is set to All.

- [NSE industry classification framework](https://www.nseindia.com/static/products-services/industry-classification)
- [Nifty thematic index methodology](https://www.niftyindices.com/Methodology/Method_Nifty_Thematic_Indices.pdf)
- [Nifty Defence constituent example](https://www.niftyindices.com/IndexConstituent/ind_niftyindiadefence_list.csv)
- Every theme's exact constituent URL and verification date is included in the snapshot and dashboard.

## Leadership calculations

Period returns use 1/5/21/63 completed sessions. Group returns are equal-weight arithmetic means of available member period returns, **not official index returns**.

Group score (0–100), ranked separately for industries and themes:

- 55% momentum composite: 20% 1W percentile +35% 1M percentile +45% 3M percentile.
- 25% percentile of mean member 3M excess return over Nifty MidSmallcap 400.
- 20% observed percentage of the original four-filter group's known-history members above SMA50. The denominator retains below-SMA50 stocks; this breadth statistic must not degenerate to100% after trend filtering.

Stock leader score uses full-universe component percentiles: 20% 1W +30% 1M +30% 3M +20% 3M benchmark excess.

Percentile ties use average ranks. Stock leaders are ranked across the above-SMA50 universe. Stocks with50–63 bars can pass the trend gate but remain unscored until3M history is available. Industry groups require **at least2 above-SMA50 members and2 members with3M history**; themes retain3 members and3 with3M history. Both require at least70%3M coverage. One-stock industries are omitted. Industry view defaults to a2-stock minimum; themes default to3.

Rank change compares the previous published trading session under the same selection policy, not an intraday run or a different filter policy. First-session/rule-change comparisons are unavailable. Sparkline charts show a current-member equal-weight normalized basket of above-SMA50 members with64 bars, **not a historical-membership index or backtest**.

Status: Leading = positive 1M return and RS-excess percentile ≥50; Improving = other ranked groups with positive 1W; Lagging = remaining ranked groups.

## Daily operation

`.github/workflows/daily-update.yml` runs **every calendar day at 19:30 Asia/Kolkata**, cron `0 14 * * *` UTC. GitHub scheduling is best effort and may start late. Weekends/holidays retain the latest independently verified completed session. Manual dispatch with `refresh_data=true` runs a full acquisition. Code pushes rebuild only the UI.

The repository independently acquires:

- Official EQ listing: https://archives.nseindia.com/content/equities/EQUITY_L.csv
- Latest closing bars: https://archives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv
- Alternate dated UDiFF ZIP: https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip
- Benchmark/date validation: https://archives.nseindia.com/content/indices/ind_close_all_DDMMYYYY.csv
- Historical backfill and current shares: Yahoo Finance via yfinance.

Production never reads any other dashboard. Each repo owns its market cache, mappings, benchmark, history and output. Source modules were reused, not live feeds.

Guards: ≥95% listing/history coverage, ≥95% same-session coverage, ≥95% shares coverage on liquidity-qualified names, ≥95% industry classification, ≥70% configured official themes and ≥95% retained pre-trend eligible stocks. The95% retention guard is checked BEFORE applying the intentional SMA50 exclusion. Failure does not overwrite the last good snapshot. For an explicitly labelled local bootstrap preview only, classification coverage can be ≥90%.

Primary classifications are versioned metadata, not automatically reclassified business narratives. Cached theme membership may lag a reconstitution if the publisher is unavailable. Corporate-action history adjustments should be checked before trading.

GitHub Pages must be enabled with build type **GitHub Actions**. Public-repository schedules may be disabled after 60 days without repository activity; inspect Actions if timestamps stop.

## Local setup

```sh
npm ci
pip install -r pipeline/requirements.txt
python -m unittest discover -s tests -v
npm run check
python pipeline/run.py
npm run dev
npm run build
```

One-time dated local BYOD preview, never used in CI:

```sh
python pipeline/run.py --bootstrap /path/to/existing/web --offline
```

The live frontend polls its own published snapshot every 5 minutes. A Refresh button reloads public data; it does not trigger authenticated Actions. A bundled fallback is explicitly dated and labelled. All browser operations are read-only except user-initiated clipboard/download.

This is a custom research framework, not proprietary IBD code or investment advice.
