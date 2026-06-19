# HK Quant Strategy Ideas - Current Decision Record

This file is intentionally short. Earlier broad idea lists were useful for exploration, but the package now keeps only strategies that survived current backtest and evidence checks.

Risk notice: this is research documentation only and is not investment advice.

## Current package decision

Use [`hk_strategy_selection_20260603.md`](./hk_strategy_selection_20260603.md) as the authoritative ranking.

Retained profiles:

1. `hk_global_etf_tactical_rotation` - retained non-snapshot runtime candidate with broader ETF exposure and product-complexity risk.
2. `hk_low_vol_dividend_quality_snapshot` - only retained snapshot-backed candidate; still requires production point-in-time evidence before real orders.

## Ideas not kept in the package surface

The following ideas should not appear as runtime catalog entries, snapshot contracts, sample builders, or platform-selectable profiles unless a future research PR adds fresh point-in-time data and passes the current gates:

- HSI/HSTECH mean reversion and leveraged mean-reversion variants;
- broad ETF regime-rotation baseline superseded by the retained ETF strategy;
- shareholder-yield, free-cash-flow, residual/liquid momentum, composite QVM, factor-mix, AH-premium, Southbound-flow, event/rebalance and central-SOE snapshot scaffolds;
- raw overlay ideas involving short selling, derivatives, margin financing, governance events, connected transactions, suspensions, ESG, analyst dispersion, liquidity premia or macro timing.

## Reopen rule

A rejected idea can only return through a dedicated research PR with:

- no-lookahead and survivorship-safe data lineage;
- long, medium and short window backtests with max drawdown <= 30%;
- positive train and out-of-sample evidence after HK costs;
- same-universe ablation versus retained profiles;
- broker/platform dry-run evidence plan for IBKR and LongBridge;
- bilingual notification and rollout evidence requirements.
