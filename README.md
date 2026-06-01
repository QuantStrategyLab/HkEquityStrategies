# HkEquityStrategies

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。


## 中文

港股策略包，供 QuantStrategyLab 平台运行时加载。

### 范围

本仓库负责 `hk_equity` 策略的策略目录元数据、运行入口和运行时适配契约。它不负责券商凭据、Cloud Run 部署或 snapshot 发布。

当前第一个 snapshot 架构占位 profile 是 `hk_blue_chip_leader_rotation`。本仓库也包含直接使用 `market_history` 的 profile：`hk_index_mean_reversion`、`hk_etf_regime_rotation` 和 `hk_listed_global_etf_rotation`。其中 `hk_listed_global_etf_rotation` 已标记为 `runtime_enabled`，因为波动率目标版本的全样本最大回撤低于 30%；其他港股 profile 仍保持禁用。

可兼容的运行平台：

- `InteractiveBrokersPlatform`，使用 `IBKR_MARKET=HK` / `SEHK` / `HKD`。
- `LongBridgePlatform`，使用 `ACCOUNT_REGION=HK` 或 `LONGBRIDGE_MARKET=HK`。

### 架构

```text
HkEquitySnapshotPipelines
  -> snapshot-backed profile 的特征快照 CSV + manifest
Platform market-data feed
  -> non-snapshot profile 的 direct market_history
HkEquityStrategies
  -> 策略目录 + 入口 + runtime adapter
InteractiveBrokersPlatform / LongBridgePlatform
  -> 加载策略包，提供必要输入，并执行券商订单
```

本包沿用 `UsEquityStrategies` 的边界：策略只返回平台无关的 `StrategyDecision`；平台仓库负责行情、组合快照、订单转换、通知和运行报告。

### 运行时 profile

| Profile | 领域 | 输入 | 目标模式 | 平台 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `hk_equity` | `feature_snapshot` | `weight` | `ibkr`, `longbridge` | `architecture_scaffold` |
| `hk_index_mean_reversion` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_etf_regime_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_listed_global_etf_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

### Snapshot contract

草案必填特征列：

- `symbol`
- `sector`
- `close_hkd`
- `adv20_hkd`
- `history_days`
- `mom_3m`
- `mom_6m`
- `mom_12_1`
- `rel_mom_6m_vs_benchmark`
- `high_252_gap`
- `sma200_gap`
- `vol_63`
- `maxdd_126`

草案推荐但非必填列：`as_of`、`snapshot_date`、`market_cap_hkd`、`lot_size`、`eligible`。

### Runtime enablement policy

`get_runtime_enabled_profiles()` 只返回可进入平台 rollout 的 profile。目前只有 `hk_listed_global_etf_rotation` 启用；`hk_blue_chip_leader_rotation`、`hk_index_mean_reversion`、`hk_etf_regime_rotation` 仍保持禁用。平台仓库仍负责最终生产 rollout 决策：除非部署账号、港股市场覆盖参数、dry-run 检查和人工审批都已完成，不要把生产 Cloud Run 的 `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE` 改成港股 profile。

### 港股运行准备检查

修改 IBKR 或 LongBridge 运行时设置前，先使用本包提供的 readiness 命令：

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

输出只是 dry-run 检查清单，不会触发部署。检查内容包括港股市场默认值、managed symbols、direct `market_history` 要求、LongBridge weight-to-value 转换、订单预览、整数股 / lot-size 检查、HKD 现金口径和 Cloud Run rollout 防护。

券商专项验证前，先运行本地 smoke。它使用合成行情，不会连接 IBKR、LongBridge、Google Cloud 或任何真实账户：

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

### 本地验证

```bash
python -m pytest -q
```

### 研究记录

- `docs/research/hk_index_mean_reversion.md` 记录恒生指数 / 恒生科技 ETF 均值回归回测。当前结论：保留为 `research_candidate`，暂不启用实盘。
- `docs/research/hk_etf_regime_rotation.md` 记录港股上市 ETF regime rotation 回测。当前结论：结果有潜力，但 2021-2023 训练期为负，仍保持 `research_candidate`。
- `docs/research/hk_listed_global_etf_rotation.md` 记录港股上市全球 ETF 轮动回测。当前结论：波动率目标版本全样本最大回撤低于 30%，标记为 `runtime_enabled`；生产 Cloud Run 仍保持不变，直到明确 rollout。

## English

Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

The first profile scaffold is `hk_blue_chip_leader_rotation`. This repo also contains direct `market_history` profiles: `hk_index_mean_reversion`, `hk_etf_regime_rotation`, and `hk_listed_global_etf_rotation`. `hk_listed_global_etf_rotation` is `runtime_enabled` after the volatility-targeted backtest kept full-sample drawdown below 30%; the other HK profiles remain disabled.

Runtime-compatible platforms:

- `InteractiveBrokersPlatform` with `IBKR_MARKET=HK` / `SEHK` / `HKD`.
- `LongBridgePlatform` with `ACCOUNT_REGION=HK` or `LONGBRIDGE_MARKET=HK`.

## Architecture

```text
HkEquitySnapshotPipelines
  -> feature snapshot CSV + manifest for snapshot-backed profiles
Platform market-data feed
  -> direct market_history for non-snapshot profiles
HkEquityStrategies
  -> catalog + entrypoint + runtime adapter
InteractiveBrokersPlatform / LongBridgePlatform
  -> load the strategy package, provide required inputs, and execute broker orders
```

The package follows the same boundary as `UsEquityStrategies`: strategies return platform-neutral `StrategyDecision` objects; platform repositories own market data, portfolio snapshots, order conversion, notifications, and runtime reports.

## Runtime profile

| Profile | Domain | Inputs | Target mode | Platforms | Status |
| --- | --- | --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `hk_equity` | `feature_snapshot` | `weight` | `ibkr`, `longbridge` | `architecture_scaffold` |
| `hk_index_mean_reversion` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_etf_regime_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `research_candidate` |
| `hk_listed_global_etf_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

## Snapshot contract

Draft required feature columns:

- `symbol`
- `sector`
- `close_hkd`
- `adv20_hkd`
- `history_days`
- `mom_3m`
- `mom_6m`
- `mom_12_1`
- `rel_mom_6m_vs_benchmark`
- `high_252_gap`
- `sma200_gap`
- `vol_63`
- `maxdd_126`

Draft optional but recommended columns: `as_of`, `snapshot_date`, `market_cap_hkd`, `lot_size`, `eligible`.

## Runtime enablement policy

`get_runtime_enabled_profiles()` returns only profiles that are eligible for platform rollout. `hk_listed_global_etf_rotation` is currently runtime-enabled, while `hk_blue_chip_leader_rotation`, `hk_index_mean_reversion`, and `hk_etf_regime_rotation` remain disabled. Platform repositories still own the production rollout decision: do not change production Cloud Run `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE` to a HK profile unless the deployment account, HK market overrides, dry-run checks, and operator approval are in place.

## HK runtime readiness

Use the packaged readiness command before changing IBKR or LongBridge runtime settings:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

The output is a dry-run checklist, not a deployment action. It covers HK market defaults, managed symbols, direct `market_history` requirements, LongBridge weight-to-value conversion, order preview, integer-share / lot-size checks, HKD cash lines, and the Cloud Run rollout guard.

Run the local smoke before broker-specific verification. It uses synthetic market history and does not connect to IBKR, LongBridge, Google Cloud, or any live account:

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## Local validation

```bash
python -m pytest -q
```

## Research notes

- `docs/research/hk_index_mean_reversion.md` records the HSI / Hang Seng TECH ETF mean-reversion backtest. Current conclusion: keep as `research_candidate`; do not enable live trading yet.
- `docs/research/hk_etf_regime_rotation.md` records the HK-listed ETF regime rotation backtest. Current conclusion: promising but still keep as `research_candidate` because the 2021-2023 train period was negative.
- `docs/research/hk_listed_global_etf_rotation.md` records the HK-listed global ETF rotation backtest. Current conclusion: mark `runtime_enabled` because the volatility-targeted version kept full-sample drawdown under 30%; production Cloud Run remains unchanged until an explicit rollout.
