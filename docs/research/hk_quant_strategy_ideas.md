# HK Quant Strategy Ideas Backlog

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。

Research date: 2026-06-01

This note summarizes strategy directions that look more suitable for Hong Kong equities after reviewing market structure, official data sources, and academic evidence. It is a research backlog. Do not mark any new strategy here as `runtime_enabled` without a dedicated backtest, platform feed validation, and paper-trading period; `hk_listed_global_etf_rotation` is the first exception promoted after a dedicated backtest kept drawdown below 30%.

## Market constraints that matter

- **Trading costs are material.** HKEX lists per-side SFC transaction levy, AFRC transaction levy, trading fee, and stamp duty. Stamp duty is generally 0.1% per side unless a security is exempt, so single-name high-turnover strategies need a much stronger edge than US equities. Reference: https://www.hkex.com.hk/Services/Rules-and-Forms-and-Fees/Fees/Securities-%28Hong-Kong%29/Trading/Transaction?sc_lang=en
- **Shorting is constrained.** HKEX regulated short selling must be covered, only applies to designated securities, and must observe the tick rule. The designated list is revised quarterly. Reference: https://www.hkex.com.hk/services/trading/securities/overview/regulated-short-selling?sc_lang=en
- **Stock Connect flows are a useful signal source.** HKEX publishes Stock Connect statistics, including historical daily/monthly data and top shareholdings. Reference: https://www.hkex.com.hk/mutual-market/stock-connect/statistics?sc_lang=en
- **Southbound participation is large enough to matter.** HKEX's 10-year Connect report says Southbound average daily turnover in Q1-Q3 2024 was HK$38.3B, or 16.9% of Hong Kong market turnover; Southbound ETF average daily turnover reached HK$2.53B in Q3 2024. Reference: https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Connect-Hub/Connect-White-Paper/HKEX_10_Years_Connect_final_EN.pdf
- **Index reviews create tradable event calendars.** Hang Seng Indexes uses quarterly data cutoffs at the end of March, June, September, and December, with review results announced within 8 weeks. Reference: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_methodology_guide_e.pdf
- **A/H premium is a Hong Kong-specific relative-value signal.** The Hang Seng Stock Connect China AH Premium Index tracks the price premium or discount of A shares over H shares for liquid AH companies eligible under Stock Connect. References: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/ahpremiume.pdf and https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/methodologies/index_operation_guide_e.pdf
- **Short-horizon reversal exists but is cost-sensitive.** Applied Economics evidence on Hong Kong weekly data reports reversal/continuance effects, but also notes that trading costs would largely overwhelm available profits in most cases. Reference: https://ideas.repec.org/a/taf/applec/v46y2014i12p1335-1349.html
- **Low-volatility / high-dividend styles are natural HK candidates.** Hang Seng Low Volatility Index selects 40 low-volatility large/mid-cap HK-listed companies with positive earnings and dividend records. Reference: https://www.hsi.com.hk/static/uploads/contents/en/dl_centre/factsheets/hslvie.pdf

## Recommended research candidates

| Priority | Candidate profile | Main inputs | Why it fits HK | Main risk | Suggested status |
| ---: | --- | --- | --- | --- | --- |
| 1 | `hk_etf_regime_rotation` | `market_history` | Low turnover, liquid ETF universe, avoids single-name borrow and disclosure problems | ETF choice and stamp-duty exemption must be checked per symbol | implemented as `research_candidate` |
| 2 | `hk_low_vol_dividend_quality` | `factor_snapshot` | Matches HK's high dividend / low volatility style, slower rebalance can absorb costs | Needs reliable fundamentals, dividend history, and corporate action handling | `architecture_scaffold` first |
| 3 | `hk_southbound_flow_momentum` | `flow_snapshot` + `market_history` | Southbound flows are large and observable; can capture mainland demand pressure | Data ingestion and crowding; flow may be noisy around holidays/policy events | `research_candidate` after data collector |
| 4 | `hk_index_rebalance_event` | `event_calendar` + `market_history` | Official quarterly index review schedule creates repeatable events | Capacity and slippage near rebalance; event sample size is small | `research_candidate` after event DB |
| 5 | `hk_ah_premium_relative_value` | `ah_premium_snapshot` + `market_history` | A/H premium is HK-specific and economically meaningful | True arbitrage may require A-share access/shorting; use as H-share valuation filter first | `research_candidate` after data validation |
| 6 | `hk_weekly_reversal_liquid_largecap` | `market_history` | Academic evidence supports weekly reversal/continuance, especially after extremes | Costs may erase edge; only viable on very liquid names with turnover caps | low priority research only |
| 7 | `hk_pairs_or_adr_hk_spread` | intraday/daily prices, FX, borrow | Some dual-listed/ADR names offer relative-value structure | Time-zone gaps, borrow, short-sale rules, conversion mechanics | defer |
| 8 | `hk_intraday_gap_reversion` | intraday bars/order book | HK often gaps on overnight China/US news | Needs high-quality data and strong slippage model; high operational risk | defer |

## Candidate sketches

### 1. ETF regime rotation

Start with liquid ETFs only, for example broad Hong Kong, H-share/China enterprise, Hang Seng TECH, gold/bond/money-market parking instruments if available and supported by platforms.

Possible signals:

- 6-12 month time-series momentum.
- 20-60 day realized volatility target.
- 200-day moving-average risk-off filter.
- Cross-sectional ranking across ETFs, capped at 2-3 holdings.

Why first: it uses the same `market_history` input style as `hk_index_mean_reversion`, is easier to backtest cleanly, and avoids single-name borrow and fundamental data issues.

Follow-up research added on 2026-06-01: `docs/research/hk_listed_global_etf_rotation.md` tests a HKEX-listed global ETF universe using `02834` Nasdaq 100, `02840` gold, `03175` crude-oil futures ETF, local HK/China ETFs, and `03110` high-dividend ETF. The selected monthly top-2 version adds a 16% volatility target and improved full-sample annualized return to 18.84% with -20.51% max drawdown, so it is implemented as `runtime_enabled` `hk_listed_global_etf_rotation`. `03010` Asia ex-Japan still needs data cleaning and `03195` S&P 500 has too short a sample for this baseline. Production Cloud Run remains unchanged until an explicit rollout.

### 2. Low-volatility dividend quality rotation

Monthly or quarterly rotation among liquid Hong Kong large/mid caps:

- dividend yield, dividend stability, positive earnings;
- low realized volatility / low beta;
- liquidity and market-cap filters;
- sector caps to avoid over-concentration in banks, utilities, property, or telecom.

This should be snapshot-backed, similar to `hk_blue_chip_leader_rotation`, but with dividend/fundamental columns added. It is probably better suited to HK than pure short-term price momentum.

### 3. Southbound flow momentum

Build a `flow_snapshot` pipeline from HKEX Stock Connect daily statistics and top shareholdings:

- Southbound net buy / turnover percentile;
- change in Southbound shareholding as % of issued shares;
- flow persistence over 5/20/60 trading days;
- combine with price momentum and liquidity filters.

Execution should be weekly, not daily, to reduce noise and costs.

### 4. Index rebalance event strategy

Use Hang Seng Indexes quarterly review schedule and official announcements:

- predicted adds/removes before announcement if methodology inputs are available;
- post-announcement drift into effective date;
- avoid names with poor liquidity or known borrow/shorting constraints.

This should be treated as event research with strict sample controls because the number of events is limited.

### 5. A/H premium relative-value filter

Do not start with true long-short arbitrage unless A-share access, borrow, and settlement are confirmed. Safer first version:

- use AH premium percentile as a valuation/regime filter for H-share exposure;
- when A/H premium is high, favor H-shares with stable fundamentals and Southbound support;
- when premium compresses sharply, reduce exposure or switch to broad ETFs.

## Implementation recommendation

Do not build all of these now. The clean sequence is:

1. Keep `hk_etf_regime_rotation` as a disabled `research_candidate` and re-run after platform feed validation.
2. Add a `flow_snapshot` pipeline before attempting Southbound flow strategies.
3. Extend snapshot schema for dividend/quality only after confirming a reliable fundamentals source.
4. Keep every new profile disabled unless it passes out-of-sample and paper-trading checks.

## Backtest rules to avoid overfitting

- Use walk-forward splits and keep a final untouched out-of-sample period.
- Use realistic HK fees: stamp duty exemption should be determined per symbol; do not assume ETF or stock costs are the same.
- Include lot-size rounding, slippage, holidays, suspended securities, and corporate actions.
- Prefer weekly/monthly turnover unless the edge is very strong after costs.
- Compare against simple benchmarks: `02800`, `3033`, static ETF mix, and cash/short-duration parking instruments where available.
