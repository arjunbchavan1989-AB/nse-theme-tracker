# Theme Atlas verification inventory

## Above-SMA50 /two-stock industry change

- Required: every classified/displayed/copied stock has EOD close>SMA50 and enough history; equality and missing SMA50 cannot pass.
- Required: two-stock industries appear and can rank; one-stock industries disappear; themes retain the existing three-stock rank minimum.
- Required: default industry filter2; switching theme/industry restores3/2; search-reset must not restore an invalid0-stock industry setting.
- Required: group memberships, returns, top10 and percentile scores use the filtered stock universe.
- Required: breadth remains the original four-filter group proportion, labelled Base breadth; main KPI uses the original known-SMA50 denominator.
- Required: pre-trend coverage guard is not wrongly evaluated after deliberate SMA50 exclusions; daily schedule remains19:30 IST.
- Exploratory: exactly equal close/SMA50, unknown SMA50, a two-member industry shrinking to one and policy-change rank comparisons.
- Verification plan: regression tests, strict TypeScript/build, independent GitHub refresh, public desktop/mobile screenshots, top10 clipboard, filter round-trip and empty-search reset.
- Executed regression:34 Python tests passed, including strict SMA50 equality, below/missing rejection, empty trend universe, two-member industry ranking and unchanged three-member theme ranking.
- Browser controls verified industry default2 →theme default3 →industry2 and empty-search Reset→2. The old optional SMA50 checkbox is absent and replaced by an enforced-rule badge.

## Required signoff

- Independent daily workflow, 14:00 UTC /19:30 IST; verified run and Pages URL.
- Four universe thresholds; exact MidSmallcap400 benchmark.
- Industry and theme navigation; sortable leading groups; min-members filter.
- Top10 stock leaders of selected group; fewer-than10 case; unscored stock handling.
- Search group by name/member; no-results reset; stock search and reset.
- Stock sort by leader score/1M/3M/RVOL/day; SMA50 and Show all toggles.
- Table/heatmap round trip; heatmap selection updates leader panel.
- Copy visible top10 /all, TradingView punctuation, blocked clipboard fallback.
- Group and stock CSV downloads with dated filenames.
- Stock TradingView links.
- Session selector, archive warning and previous-session rank change unavailable if first session.
- Refresh behavior, fallback badge, first-run bootstrap label and failure state.
- Methodology and data-health pages.
- Light/dark desktop/mobile; no document overflow; intended horizontal table scroll.
- Keyboard controls, status dismissal, menu Escape and clipboard-dialog Escape.
- Unit regressions: returns, missing values, sample sizes, ties, overlap, official date validation.

## Exploratory cases

- Empty group after aggressive search /minimum10, reset and reselect.
- Sparse theme with fewer than10 stocks; All minimum reveals zero-member groups.
- Blocked clipboard and failed remote feed do not silently report success/currentness.
- Repeat same-session run does not manufacture rank-change observations.

## Evidence

Results and exclusions are recorded below after execution.

## Executed checks, 15 October 2026 IST

- 27 Python tests passed: leadership arithmetic, missing lookbacks, short-history retention, group sample gates, rank change, tie order, top10 cap, overlapping themes and official NSE date/calendar safeguards.
- TypeScript strict check and Vite production build passed. Full npm dependency audit: zero vulnerabilities.
- First full independent production run [38638357358](https://github.com/arjunbchavan1989-AB/nse-theme-tracker/actions/runs/38638357358) completed successfully, including Pages deployment.
- All 835 production rows independently asserted against all four strict thresholds; all 148 groups checked for membership/count consistency, valid sample gates and top10 subsets.
- 45 stocks with fewer than100 bars retained. Missing long lookbacks do not create zero returns or fake scores.
- 100% industry-classification coverage in first independent snapshot. Official Housing legacy CSV schema corrected and regression-tested; cached production rerun dispatched to verify the additional theme.
- Industry/theme switch, group-name search and no-results reset; stock-name search and reset; minimum-member selection; ascending/descending return sorts; stock 3M sort; SMA50 filter and Show all round trips passed through actual browser controls.
- Table/heatmap round trip and Manufacturing/Defence selection updated the leader panel.
- TradingView clipboard copied exactly the displayed10 symbols on a qualifying theme. Sparse industry copied9 without padding.
- Isolated blocked-clipboard fixture opened manual textarea, preserved symbols, trapped keyboard Tab and closed with Escape.
- Both group CSV and stock CSV downloads had dated filenames. String cells are protected from spreadsheet formula injection.
- Remote GitHub feed failure fixture showed explicit bundled dated fallback. Refresh stated it reloads data and does not start Actions.
- Archive/latest session selector round trip and archive warning passed using the first available dated snapshot. Real multi-session archive and live rank-change comparison cannot be exercised until another trading session exists; arithmetic is unit-tested.
- Methodology and data-health pages inspected in desktop light/dark. Navigation resets main scroll to top.
- Desktop1536×1050 and mobile390×844 inspected visually; no document horizontal overflow or JavaScript page errors. Group tables intentionally scroll horizontally on narrow displays.
- Mobile navigation closed normally; selecting a group scrolled its leader panel into view. Waited for the navigation transition and smooth scroll to settle before final visual signoff.
- Public [GitHub Pages site](https://arjunbchavan1989-ab.github.io/nse-theme-tracker/) loaded with independent snapshot, no bootstrap warning and no document overflow.
- Static review found no dangerous HTML rendering, eval, embedded credentials, backend mutations or storage of account data. JS dependencies are bundled, not loaded from script CDNs.
- Cached independent refresh [38639121481](https://github.com/arjunbchavan1989-AB/nse-theme-tracker/actions/runs/38639121481) completed successfully, including Pages deployment. The corrected official legacy constituent schema is now exercised in production.
- Deployment validator identified a genuinely clipped terminal column at narrow desktop; changed to a stacked research layout at ≤1380px, added explicit horizontal table-navigation controls and separated shown/ranked/limited counts.
- 1366px regression: table width1064px equals its container1064px, no clipped terminal column or document overflow; visible counts explicitly say67 shown /66 ranked /1 limited for that snapshot.
- Mobile right/left table-navigation controls moved the inner scroll container and returned to the start. Desktop leader panel now has explicit independent vertical scrolling when its content exceeds viewport height.

## Known limitations

- Theme baskets contain official index constituents only, not every possible thematic beneficiary. Industries are provider labels, not official NSE basic-industry codes.
- Initial primary industry metadata is versioned; daily runs fill missing mappings but do not automatically reassess every existing company's business classification.
- Shares and historical prices have incomplete provider coverage, reported transparently. Failed validation retains the last good snapshot.
- Current-member normalized charts are not historical-membership backtests. Corporate actions need independent review.
- GitHub scheduling is best effort, not an exact-to-the-minute service guarantee.
