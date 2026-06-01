# HkEquityStrategies

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。


## 中文

港股策略包，供 QuantStrategyLab 平台运行时加载。

### 范围

本仓库负责 `hk_equity` 非 snapshot 策略的策略目录元数据、运行入口和运行时适配契约。它不负责券商凭据、Cloud Run 部署或 snapshot 发布。

港股非 snapshot 策略和港股 snapshot 策略保持分开：

- `HkEquityStrategies`：只暴露可进入平台 runtime catalog 的非 snapshot 港股策略。当前只有 `hk_listed_global_etf_rotation` 标记为 `runtime_enabled`；`hk_index_mean_reversion`、`hk_etf_regime_rotation` 只保留为研究回测，不注册为 runtime profile。
- `HkEquitySnapshotPipelines`：snapshot-backed 策略的数据管线、artifact contract、策略 helper 和发布流程。当前 `hk_blue_chip_leader_rotation` 只是 snapshot 架构占位，不进入平台 live enable。

可兼容的运行平台：

- `InteractiveBrokersPlatform`，使用 `IBKR_MARKET=HK` / `SEHK` / `HKD`。
- `LongBridgePlatform`，使用 `ACCOUNT_REGION=HK` 或 `LONGBRIDGE_MARKET=HK`。

### 架构

```text
Platform market-data feed
  -> non-snapshot profile 的 direct market_history
HkEquityStrategies
  -> 非 snapshot 策略目录 + 入口 + runtime adapter
HkEquitySnapshotPipelines
  -> snapshot-backed profile 的特征快照 CSV + manifest + 发布/研究回测
InteractiveBrokersPlatform / LongBridgePlatform
  -> 加载策略包，提供必要输入，并执行券商订单
```

本包沿用 `UsEquityStrategies` 的边界：策略只返回平台无关的 `StrategyDecision`；平台仓库负责行情、组合快照、订单转换、通知和运行报告。

### 非 snapshot 港股策略 profile

| Profile | 领域 | 输入 | 目标模式 | 平台 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `hk_listed_global_etf_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

研究回测-only 候选不注册为 runtime profile：`hk_index_mean_reversion`、`hk_etf_regime_rotation`。平台侧只应允许 `get_runtime_enabled_profiles()` 返回的 profile。

### Snapshot-backed 港股策略 profile

| Profile | 输入 | 状态 | Snapshot 仓库 |
| --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |

### Snapshot contract

The snapshot-backed artifact contract now lives in `HkEquitySnapshotPipelines/docs/artifact_contract.md`. This repository no longer owns snapshot feature-column definitions. If a snapshot profile is promoted later, validate the data source, manifest, ranking, and publication flow in the snapshot repository first.

## Runtime enablement policy

`get_runtime_enabled_profiles()` 只返回可进入平台 rollout 的 profile。目前只有 `hk_listed_global_etf_rotation` 启用。

分组辅助函数：

- `get_direct_market_history_profiles()`：已注册 runtime catalog 的非 snapshot 港股策略。
- `get_snapshot_backed_profiles()`：本仓库内 snapshot-backed runtime profile；当前为空，snapshot scaffold 在 `HkEquitySnapshotPipelines`。
- `get_research_backtest_only_profiles()`：只保留研究回测、不应 live enable 的港股策略。

平台仓库负责最终运行环境选择：`hk_listed_global_etf_rotation` 已经可以通过 Cloud Run 的 `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE` 启用；dry-run、paper/live 和账户范围由平台环境变量控制。

### 港股运行准备检查

修改 IBKR 或 LongBridge 运行时设置前，先使用本包提供的 readiness 命令：

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

输出只是运行准备检查清单，不会直接修改 Cloud Run。检查内容包括港股市场默认值、managed symbols、direct `market_history` 要求、LongBridge weight-to-value 转换、订单预览、整数股 / lot-size 检查、HKD 现金口径和 Cloud Run 环境复核项。

券商专项验证前，先运行本地 smoke。它使用合成行情，不会连接 IBKR、LongBridge、Google Cloud 或任何真实账户：

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

### 本地验证

```bash
python -m pytest -q
```

### 研究记录

- `docs/research/hk_index_mean_reversion.md` 记录恒生指数 / 恒生科技 ETF 均值回归回测。当前结论：保留为研究回测-only，暂不注册 runtime profile。
- `docs/research/hk_etf_regime_rotation.md` 记录港股上市 ETF regime rotation 回测。当前结论：结果有潜力，但 2021-2023 训练期为负，仍保持研究回测-only。
- `docs/research/hk_listed_global_etf_rotation.md` 记录港股上市全球 ETF 轮动回测。当前结论：波动率目标版本全样本最大回撤低于 30%，已标记为 `runtime_enabled`，可由平台 Cloud Run 环境启用。

## English

Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for non-snapshot `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

HK non-snapshot strategies and HK snapshot strategies stay separated:

- `HkEquityStrategies`: only platform runtime catalog entries for non-snapshot HK strategies. `hk_listed_global_etf_rotation` is currently the only `runtime_enabled` profile; `hk_index_mean_reversion` and `hk_etf_regime_rotation` remain research/backtest-only and are not runtime profiles.
- `HkEquitySnapshotPipelines`: snapshot-backed data pipelines, artifact contracts, strategy helpers, and publication flows. `hk_blue_chip_leader_rotation` remains a snapshot architecture scaffold and must not be live-enabled by platform repositories.

Runtime-compatible platforms:

- `InteractiveBrokersPlatform` with `IBKR_MARKET=HK` / `SEHK` / `HKD`.
- `LongBridgePlatform` with `ACCOUNT_REGION=HK` or `LONGBRIDGE_MARKET=HK`.

## Architecture

```text
Platform market-data feed
  -> direct market_history for non-snapshot profiles
HkEquityStrategies
  -> non-snapshot catalog + entrypoint + runtime adapter
HkEquitySnapshotPipelines
  -> feature snapshot CSV + manifest + publish/research flow for snapshot-backed profiles
InteractiveBrokersPlatform / LongBridgePlatform
  -> load the strategy package, provide required inputs, and execute broker orders
```

The package follows the same boundary as `UsEquityStrategies`: strategies return platform-neutral `StrategyDecision` objects; platform repositories own market data, portfolio snapshots, order conversion, notifications, and runtime reports.

## Non-snapshot HK strategy profiles

| Profile | Domain | Inputs | Target mode | Platforms | Status |
| --- | --- | --- | --- | --- | --- |
| `hk_listed_global_etf_rotation` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

Research/backtest-only candidates are not registered as runtime profiles: `hk_index_mean_reversion`, `hk_etf_regime_rotation`. Platform runtimes should only allow profiles returned by `get_runtime_enabled_profiles()`.

## Snapshot-backed HK strategy profile

| Profile | Inputs | Status | Snapshot repository |
| --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |

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

`get_runtime_enabled_profiles()` returns only profiles that are eligible for platform rollout. `hk_listed_global_etf_rotation` is currently the only runtime-enabled HK profile.

Grouping helpers:

- `get_direct_market_history_profiles()`: registered runtime-catalog non-snapshot HK strategies.
- `get_snapshot_backed_profiles()`: snapshot-backed runtime profiles inside this repository; currently empty because snapshot scaffolds live in `HkEquitySnapshotPipelines`.
- `get_research_backtest_only_profiles()`: HK strategies that remain research/backtest-only and must not be live-enabled.

Platform repositories own the runtime environment selection: `hk_listed_global_etf_rotation` can be enabled through Cloud Run `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE`, while dry-run, paper/live mode, and account scope remain controlled by platform environment variables.

## HK runtime readiness

Use the packaged readiness command before changing IBKR or LongBridge runtime settings:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
```

The output is a runtime-readiness checklist, not a direct Cloud Run mutation. It covers HK market defaults, managed symbols, direct `market_history` requirements, LongBridge weight-to-value conversion, order preview, integer-share / lot-size checks, HKD cash lines, and Cloud Run environment review items.

Run the local smoke before broker-specific verification. It uses synthetic market history and does not connect to IBKR, LongBridge, Google Cloud, or any live account:

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## Local validation

```bash
python -m pytest -q
```

## Research notes

- `docs/research/hk_index_mean_reversion.md` records the HSI / Hang Seng TECH ETF mean-reversion backtest. Current conclusion: keep as research/backtest-only; do not register as a runtime profile yet.
- `docs/research/hk_etf_regime_rotation.md` records the HK-listed ETF regime rotation backtest. Current conclusion: promising but still keep as research/backtest-only because the 2021-2023 train period was negative.
- `docs/research/hk_listed_global_etf_rotation.md` records the HK-listed global ETF rotation backtest. Current conclusion: mark `runtime_enabled` because the volatility-targeted version kept full-sample drawdown under 30%; platform Cloud Run environments can select it through runtime configuration.
