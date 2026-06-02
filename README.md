# HkEquityStrategies

> ⚠️ 投资有风险，不构成投资建议，仅供学习交流用途。


## 中文

港股策略包，供 QuantStrategyLab 平台运行时加载。

### 范围

本仓库负责 `hk_equity` 非 snapshot 策略的策略目录元数据、运行入口和运行时适配契约。它不负责券商凭据、Cloud Run 部署或 snapshot 发布。

港股非 snapshot 策略和港股 snapshot 策略保持分开：

- `HkEquityStrategies`：只暴露可进入平台 runtime catalog 的非 snapshot 港股策略。当前 `hk_listed_global_etf_rotation` 和 `hk_high_dividend_low_vol_trend` 标记为 `runtime_enabled`；`hk_index_mean_reversion`、`hk_etf_regime_rotation` 只保留为研究回测，不注册为 runtime profile。
- `HkEquitySnapshotPipelines`：snapshot-backed 策略的数据管线、artifact contract、策略 helper 和发布流程。当前 snapshot profile 都只是架构 scaffold，不进入平台 live enable；其中 `hk_liquid_momentum_quality` 是港股版“动量因子选股” scaffold；`hk_composite_factor_quality_value_momentum` 是更完整的质量/价值/动量/低波多因子 scaffold；`hk_factor_mix_qvlm_risk_parity` 是带 HSI component-index / MSCI Factor Mix 证据门槛的 QVLM risk-parity 多因子 scaffold；`hk_central_soe_value_quality_select` 是带 SASAC/MOF source-list / HSI screening-capping 证据门槛的央国企/政策价值质量 scaffold；`hk_quality_growth_low_volatility` 是带 HSI QGLV 四因子 / MSCI Quality 证据门槛的质量成长低波 scaffold；`hk_residual_momentum_quality` 是残差/行业中性动量 scaffold；`hk_shareholder_yield_quality` 是股息/回购股东收益 scaffold；`hk_free_cash_flow_quality` 是 FCF yield 质量价值 scaffold。

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
| `hk_high_dividend_low_vol_trend` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

研究回测-only 候选不注册为 runtime profile：`hk_index_mean_reversion`、`hk_etf_regime_rotation`。平台侧只应允许 `get_runtime_enabled_profiles()` 返回的 profile。

### Snapshot-backed 港股策略 profile

| Profile | 输入 | 状态 | Snapshot 仓库 |
| --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_low_vol_dividend_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_liquid_momentum_quality` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_composite_factor_quality_value_momentum` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_free_cash_flow_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_factor_mix_qvlm_risk_parity` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_central_soe_value_quality_select` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_quality_growth_low_volatility` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_residual_momentum_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_shareholder_yield_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_southbound_flow_momentum` | `flow_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_ah_premium_relative_value` | `valuation_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_index_rebalance_event` | `event_calendar_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |

### Snapshot contract

The snapshot-backed artifact contract now lives in `HkEquitySnapshotPipelines/docs/artifact_contract.md`. This repository no longer owns snapshot feature-column definitions. If a snapshot profile is promoted later, validate the data source, manifest, ranking, and publication flow in the snapshot repository first.

## Runtime enablement policy

`get_runtime_enabled_profiles()` 只返回可进入平台 rollout 的 profile。目前 `hk_listed_global_etf_rotation` 和 `hk_high_dividend_low_vol_trend` 启用。

分组辅助函数：

- `get_direct_market_history_profiles()`：已注册 runtime catalog 的非 snapshot 港股策略。
- `get_snapshot_backed_profiles()`：本仓库内 snapshot-backed runtime profile；当前为空，snapshot scaffold 在 `HkEquitySnapshotPipelines`。
- `get_external_snapshot_scaffold_profiles()`：列出已在 `HkEquitySnapshotPipelines` 建好 contract/helper、但不能被平台当作 runtime profile 的 snapshot scaffold。
- `get_research_backtest_only_profiles()`：只保留研究回测、不应 live enable 的港股策略。

平台仓库负责最终运行环境选择：`hk_listed_global_etf_rotation` 和 `hk_high_dividend_low_vol_trend` 已经可以通过 Cloud Run 的 `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE` 启用；dry-run、paper/live 和账户范围由平台环境变量控制。

### 港股 live enablement 矩阵

平台侧集成、状态页和 switch-plan 工具应先读取统一矩阵，再决定哪些 profile 可以显示为可选项：

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_high_dividend_low_vol_trend --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_shareholder_yield_quality --json
```

矩阵是只读检查，不会部署或修改 Cloud Run。它把 profile 分成三类：

- `runtime_market_history`：平台可选的非 snapshot runtime profile，目前只有 `hk_listed_global_etf_rotation` 和 `hk_high_dividend_low_vol_trend`。
- `research_backtest_only`：只保留研究记录，不允许平台选择。
- `external_snapshot_scaffold`：snapshot 仓库已建 contract/helper，但仍需 `HkEquitySnapshotPipelines` promotion matrix、artifact pack 和 live evidence pack 通过后才能提升为平台 runtime profile。

矩阵也输出 `backtest_validation_policy`，作为所有港股 runtime 和 snapshot scaffold 的统一回测门槛：最大回撤不得超过 30%（profile 有更严格阈值时按更严格阈值），必须证明 point-in-time 输入、无未来函数、无 survivorship bias、无全样本收益最优选参，并覆盖至少 3 个独立 OOS fold、每个 OOS fold 最大回撤 <= 30%、单一周期收益贡献 <= 60%、年化收益/最大回撤比至少 0.50、参数敏感性/holdout 稳定性、净收益扣费、熊市/震荡/低流动性压力、HK 成本/滑点/lot-size/停牌/VCM/CAS、杠杆/做空/融资可行性、费用/滑点/价差压力后仍有正超额收益、最差月/最差调仓损失、time-under-water 恢复、与现有 live profile 的相关性和组合级风险预算、容量约束。矩阵同时输出 `evidence_uri_policy`、`evidence_freshness_policy`、`runtime_etf_product_policy`、`runtime_market_data_policy`、`execution_capacity_policy`、`dry_run_order_preview_policy`、`rollout_risk_policy`、`snapshot_required_repository_policies`（包含 `baseline_rotation_live_enablement_policy` 和 `policy_value_live_enablement_policy`）和 `snapshot_future_research_live_enablement_policy`（当前仅把 research-only `hk_earnings_revision_quality_overlay`、`hk_low_size_quality_liquidity_premium`、`hk_stock_connect_inclusion_event_flow`、`hk_short_selling_pressure_risk_overlay`、`hk_director_dealing_disclosure_quality_overlay`、`hk_dually_traded_liquid_reversal_overlay`、`hk_earnings_announcement_drift_overlay`、`hk_lottery_stock_risk_exclusion_overlay`、`hk_equity_financing_dilution_risk_overlay`、`hk_connected_transaction_governance_risk_overlay`、`hk_takeover_privatization_event_spread_overlay`、`hk_distribution_ex_date_entitlement_overlay`、`hk_ipo_lockup_overhang_event_overlay`、`hk_audit_opinion_suspension_risk_overlay`、`hk_share_repurchase_execution_signal_overlay`、`hk_liquid_pairs_cointegration_stat_arb_overlay`、`hk_macro_liquidity_inflation_rate_sensitivity_overlay`、`hk_turn_of_month_lunar_new_year_calendar_overlay`、`hk_etf_premium_discount_tracking_quality_overlay`、`hk_asset_growth_net_issuance_quality_overlay`、`hk_accrual_quality_earnings_persistence_overlay`、`hk_fscore_gross_profitability_quality_overlay`、`hk_shareholding_concentration_free_float_risk_overlay` 、`hk_amihud_liquidity_risk_capacity_overlay`、`hk_analyst_dispersion_coverage_risk_overlay` 和 `hk_financial_distress_deleveraging_risk_overlay` 暴露为非 selectable 候选），平台可据此自动要求 `https://`、`gs://` 或 `s3://` 证据 URI，并拒绝带 token/password/signature 等 secret-like query 参数、超过时效窗口、缺少逐 symbol HKEX ETP/ETF 分类、官方产品文档 URI、underlying index / reference asset 来源、NAV/iNAV 来源、tracking error / tracking difference 复核、ETF Connect / Stock Connect eligible / sell-only 状态、南向 ETF 日度成交/资金流趋势、券商南向 ETF 买单路由、跨境结算/假期/资格变更复核、杠杆/反向/合成/期货型或复杂产品复核、KID/prospectus 风险披露、多柜台货币和 creation/redemption 处理、分派/税费/费用处理、券商产品权限、交易货币/board lot、分红和 corporate-action 处理、生产行情/ETF NAV/分红/停牌审计、ADV/board-lot/odd-lot/VCM 容量校验、raw order preview / quote snapshot / fee breakdown URI 与 sha256 provenance，或缺少分阶段上线/回滚/tripwire 计划的证据。

当前首批 snapshot 推进候选由矩阵字段 `first_snapshot_candidates` 给出：`hk_low_vol_dividend_quality`、`hk_shareholder_yield_quality`、`hk_free_cash_flow_quality`。这不是 live 开关；它只是给后续生产数据、回测、dry-run 证据收集排序。
更细的 snapshot 顺序以 `HkEquitySnapshotPipelines` 的 `recommended_live_enablement_sequence` 为准；首批低换手质量/收益候选必须先通过 `quality_yield_live_enablement_policy` 的低波红利 / 股东收益 / FCF 同 universe ablation、forecast dividend yield vs trailing yield ablation、stale estimate-revision 控制、yield-trap 控制、HSHYLV/HSSCHYS-style Southbound / 三年现金分红 / payout-ratio / price-crash / high-volatility exclusion / financial-soundness screen、share-count/treasury-share 对账、FCF formula/EV inputs/reporting-date/restatement/sector-exception、HKEX next-day repurchase returns、treasury-share retention/cancellation/resale、moratorium/blackout/connected-person controls、post-buyback financing review、sector/rate-cycle stress 和 order-preview provenance；动量因子候选存在，但排在这些首批候选之后，并且必须通过 `momentum_live_enablement_policy` 的 residual/liquid/composite ablation、HSI close-to-high 与 MSCI 6/12 个月 one-month-skip risk-adjusted momentum 对齐、52-week-high vs 12-1 momentum 比较、volatility normalization、industry-neutral/quality-screen 测试、turnover buffer、sector/capacity、reversal/high-beta/suspension/Southbound stress windows 和 dry-run order-preview provenance 后才允许移除 dry-run；南向资金、AH 溢价和指数调仓 scaffold 还必须通过 `special_situation_live_enablement_policy` 的官方来源、日历/收盘对齐、HSI methodology/operation-guide 版本、schedule-file 版本、next-review notice、review-result press-release 时间戳、constituent weight/pro-forma 记录、MOC-vs-next-open 与 pro-forma-weighted ablation、fast-entry / suspension / buffer-rule exception、HKEX CAS / market-on-close random-close / two-stage price-limit / order-rejection / passive-flow imbalance 控制、signal-decay、crowding/slippage 和 dry-run order-preview provenance 检查。

### 港股运行准备检查

修改 IBKR 或 LongBridge 运行时设置前，先使用本包提供的 readiness 命令：

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

输出只是运行准备检查清单，不会直接修改 Cloud Run。检查内容包括港股市场默认值、managed symbols、direct `market_history` 要求、LongBridge weight-to-value 转换、订单预览、整数股 / lot-size 检查、HKD 现金口径和 Cloud Run 环境复核项。

Readiness JSON 同样输出 `evidence_uri_policy`、`evidence_freshness_policy`、`runtime_etf_product_policy`、`runtime_market_data_policy`、`execution_capacity_policy`、`dry_run_order_preview_policy`、`rollout_risk_policy` 和 `notification_audit_policy`，平台可在 dry-run readiness 阶段就阻止不稳定或带 secret-like query 参数的证据链接，并要求 direct `market_history` 先证明 source name、覆盖区间、稳定 `market_history_source_uri`、`market_history_quality_report_uri`、`point_in_time_data_dictionary_uri`、point-in-time、adjusted price、distribution、corporate action、stale quote、suspension/trading status、ETF NAV/iNAV 和 stamp-duty/exemption 来源；同时必须完成逐 symbol ETF 产品尽调，包括 HKEX ETP/ETF 分类、官方产品文档、underlying index / reference asset、NAV/iNAV、tracking error / tracking difference、ETF Connect / Stock Connect eligible / sell-only 状态、南向 ETF 日度成交/资金流趋势、券商南向 ETF 买单路由、跨境结算/假期/资格变更复核、杠杆/反向/合成/期货型或复杂产品复核、KID/prospectus 风险披露、多柜台货币和 creation/redemption 处理、分派/税费/费用处理、券商产品权限、交易货币/board lot、分红和 corporate-action 处理。之后再进入 ADV 容量、board-lot rounding、odd-lot avoidance、交易时段路由、VCM/price-band 控制、raw order preview / quote snapshot / fee breakdown artifact provenance、初始资金上限、kill switch、SWT/VCM runbook、扩容前观察期，以及 EN/ZH-Hans 双语通知、correlation id、脱敏和稳定 delivery-log URI 检查。

Readiness JSON 还会输出 `live_enablement_thresholds` 和 `required_live_evidence_fields`。当前非 snapshot live profile 的硬边界是：`hk_listed_global_etf_rotation` 最大回撤 30%、年化收益/最大回撤比至少 0.50、至少 3 个 OOS fold、单一周期收益贡献 <= 60%、年化换手 150%；`hk_high_dividend_low_vol_trend` 最大回撤 12%、年化收益/最大回撤比至少 0.50、至少 3 个 OOS fold、单一周期收益贡献 <= 60%、年化换手 100%。真正切到 live 前仍需提供至少 3 年 walk-forward / out-of-sample 证据、正年化收益、相对 metadata benchmark 正超额收益、survivorship/look-ahead 控制、逐 symbol ETF 产品尽调、HK 费用/征费、ETF 印花税豁免或适用税费、bid/ask spread、slippage、lot-size rounding、订单预览通知、双语通知 delivery-log 和人工审批证据。

切换到 live 前生成并校验 runtime evidence pack：

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_high_dividend_low_vol_trend \
  --platform longbridge \
  --json > runtime-live-enable-evidence.json
```

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file runtime-live-enable-evidence.json \
  --json
```

模板和校验结果也会输出同一份 `evidence_uri_policy`、`evidence_freshness_policy`、`runtime_etf_product_policy`、`runtime_market_data_policy`、`execution_capacity_policy`、`dry_run_order_preview_policy`、`rollout_risk_policy` 和 `notification_audit_policy`。通过校验的 evidence pack 不能只填布尔值：`strategy_backtest`、`runtime_readiness`、`platform_dry_run_order_preview`、`broker_permission_and_fee_verification` 和 `runtime_switch_plan` 都必须提供非空、稳定的 `evidence_uri`（允许 `https://`、`gs://`、`s3://`）和 ISO 日期格式 `evidence_generated_at`，且 URI 不能包含 token/password/signature 等 secret-like query 参数；`runtime_readiness` 必须证明 direct `market_history` 的 source name、覆盖区间、稳定 `market_history_source_uri`、`market_history_quality_report_uri`、`point_in_time_data_dictionary_uri`、adjusted price、distribution、corporate action、stale quote、suspension/trading status、ETF NAV/iNAV 和 stamp-duty/exemption 来源；`broker_permission_and_fee_verification` 必须提供 `etf_product_audit_id`、`managed_etf_symbols_audited_count`、稳定的 `etf_product_universe_audit_uri` / `official_product_document_uri` / `underlying_index_or_reference_asset_source_uri` / `nav_or_inav_source_uri` / `market_maker_or_liquidity_provider_source_uri` / `stock_connect_etf_eligibility_source_uri` / `southbound_etf_turnover_and_fund_flow_source_uri` / `distribution_tax_and_fee_treatment_source_uri` / `etf_fee_and_stamp_duty_audit_uri` / `broker_product_permission_audit_uri`，并确认 managed symbols 均为 ETP、杠杆/反向/合成/期货型或复杂产品已复核、ETF 税费/印花税处理已核验、market maker 或 liquidity provider 存在性已检查、KID/prospectus 风险披露已审阅、官方产品文档仍有效、NAV/iNAV 已对账、tracking error / tracking difference 已复核、ETF Connect / Stock Connect eligible / sell-only 状态、南向 ETF 日度成交/资金流趋势、券商南向 ETF 买单路由、跨境结算/假期/资格变更已复核、多柜台货币和 creation/redemption 已复核、商品信托单一资产/存储风险与高股息集中度/收益陷阱风险已复核、券商产品权限、交易货币/board lot、分红和 corporate-action 处理均已核验；`platform_dry_run_order_preview` 还必须证明 ADV 窗口、median daily turnover、单笔订单 ADV 占比、rebalance ADV 占比、liquidity cap、board-lot rounding、odd-lot avoidance、交易时段路由和 VCM/price-band controls 均满足门槛，并提供 `dry_run_session_id`、稳定的 `raw_order_preview_uri` / `quote_snapshot_uri` / `fee_breakdown_uri`、对应 64 位 hex sha256、非 sample artifact 证明、敏感字段脱敏、quote 覆盖全 symbols、fee breakdown 与券商预览对账、order preview 与策略决策对账，以及 `hk_live_enablement_notification.v1`、`hk_runtime_live_enablement_dry_run`、EN/ZH-Hans 文案、correlation id、敏感字段脱敏和稳定 `notification_delivery_log_uri`；`runtime_switch_plan` 必须证明分阶段上线、初始资金/单标的上限、盘中和累计回撤 tripwire、kill switch、operator notification、SWT/VCM runbook、回滚计划和扩容前观察期；`risk_approval.approval_reference` 也必须非空，便于审计和回滚。

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
- `docs/research/hk_high_dividend_low_vol_trend.md` 记录高股息 / 黄金双 ETF 趋势轮动回测。当前结论：12% 波动率目标版本全样本最大回撤低于 10%，已标记为 `runtime_enabled`，可由平台 Cloud Run 环境启用。
- `docs/research/hk_listed_global_etf_rotation.md` 记录港股上市全球 ETF 轮动回测。当前结论：波动率目标版本全样本最大回撤低于 30%，已标记为 `runtime_enabled`，可由平台 Cloud Run 环境启用；但 dry-run 移除前必须补齐 8 只 ETF 的 issuer docs、NAV/iNAV、underlying/reference asset、tracking difference、market-maker/liquidity provider、multi-counter、fee/tax、broker permission、A 股交易时段/涨跌停、Nasdaq 时区、黄金信托和原油期货 roll/margin/curve 证据。

## English

Hong Kong equity strategy package for QuantStrategyLab platform runtimes.

## Scope

This repository owns strategy catalog metadata, runtime entrypoints, and runtime adapter contracts for non-snapshot `hk_equity` strategies. It does not own broker credentials, Cloud Run deployment, or snapshot publication.

HK non-snapshot strategies and HK snapshot strategies stay separated:

- `HkEquityStrategies`: only platform runtime catalog entries for non-snapshot HK strategies. `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend` are currently `runtime_enabled`; `hk_index_mean_reversion` and `hk_etf_regime_rotation` remain research/backtest-only and are not runtime profiles.
- `HkEquitySnapshotPipelines`: snapshot-backed data pipelines, artifact contracts, strategy helpers, and publication flows. Current snapshot profiles are architecture scaffolds and must not be live-enabled by platform repositories; `hk_liquid_momentum_quality` is the HK momentum factor stock-selection scaffold; `hk_composite_factor_quality_value_momentum` is the broader quality/value/momentum/low-volatility multi-factor scaffold; `hk_factor_mix_qvlm_risk_parity` is the QVLM risk-parity multi-factor scaffold with HSI component-index and MSCI Factor Mix evidence gates; `hk_central_soe_value_quality_select` is the central-SOE / policy-value quality scaffold with SASAC/MOF source-list and HSI screening/capping evidence gates; `hk_quality_growth_low_volatility` is the quality-growth low-volatility scaffold with HSI QGLV four-factor / MSCI Quality evidence gates; `hk_residual_momentum_quality` is the residual / industry-neutral momentum scaffold; `hk_shareholder_yield_quality` is the dividend/buyback shareholder-yield scaffold; `hk_free_cash_flow_quality` is the FCF-yield quality/value scaffold.

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
| `hk_high_dividend_low_vol_trend` | `hk_equity` | `market_history` | `weight` | `ibkr`, `longbridge` | `runtime_enabled` |

Research/backtest-only candidates are not registered as runtime profiles: `hk_index_mean_reversion`, `hk_etf_regime_rotation`. Platform runtimes should only allow profiles returned by `get_runtime_enabled_profiles()`.

## Snapshot-backed HK strategy profile

| Profile | Inputs | Status | Snapshot repository |
| --- | --- | --- | --- |
| `hk_blue_chip_leader_rotation` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_low_vol_dividend_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_liquid_momentum_quality` | `feature_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_composite_factor_quality_value_momentum` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_free_cash_flow_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_factor_mix_qvlm_risk_parity` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_central_soe_value_quality_select` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_quality_growth_low_volatility` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_residual_momentum_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_shareholder_yield_quality` | `factor_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_southbound_flow_momentum` | `flow_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_ah_premium_relative_value` | `valuation_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |
| `hk_index_rebalance_event` | `event_calendar_snapshot` | `architecture_scaffold` | `HkEquitySnapshotPipelines` |

## Snapshot contract

Snapshot-backed artifact columns are documented in `HkEquitySnapshotPipelines/docs/artifact_contract.md`. Do not duplicate or mutate those contracts from this repository.

## Runtime enablement policy

`get_runtime_enabled_profiles()` returns only profiles that are eligible for platform rollout. `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend` are currently runtime-enabled HK profiles.

Grouping helpers:

- `get_direct_market_history_profiles()`: registered runtime-catalog non-snapshot HK strategies.
- `get_snapshot_backed_profiles()`: snapshot-backed runtime profiles inside this repository; currently empty because snapshot scaffolds live in `HkEquitySnapshotPipelines`.
- `get_external_snapshot_scaffold_profiles()`: snapshot scaffolds with contracts/helpers in `HkEquitySnapshotPipelines`; platform runtimes must not treat them as selectable profiles.
- `get_research_backtest_only_profiles()`: HK strategies that remain research/backtest-only and must not be live-enabled.

Platform repositories own the runtime environment selection: `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend` can be enabled through Cloud Run `RUNTIME_TARGET_JSON` / `STRATEGY_PROFILE`, while dry-run, paper/live mode, and account scope remain controlled by platform environment variables.

## HK live-enable matrix

Platform integration, status pages, and switch-plan tooling should read the unified matrix before exposing selectable profiles:

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_high_dividend_low_vol_trend --json
python scripts/print_hk_live_enablement_matrix.py --profile hk_shareholder_yield_quality --json
```

The matrix is read-only and does not deploy or mutate Cloud Run. It groups profiles into:

- `runtime_market_history`: selectable non-snapshot runtime profiles, currently `hk_listed_global_etf_rotation` and `hk_high_dividend_low_vol_trend`.
- `research_backtest_only`: research records that must not be platform-selectable.
- `external_snapshot_scaffold`: snapshot contracts/helpers exist in `HkEquitySnapshotPipelines`, but promotion still requires the snapshot promotion matrix, artifact-pack validation, and live-evidence validation before any runtime enablement.

The matrix also exposes `backtest_validation_policy`, the shared gate for all HK runtime and snapshot-scaffold profiles: max drawdown must stay at or below 30% unless a stricter profile threshold applies; evidence must prove point-in-time inputs, no look-ahead or survivorship bias, no full-sample return-based parameter selection, at least 3 independent OOS folds, each OOS fold max drawdown <= 30%, max single-period return contribution <= 60%, annual-return-to-max-drawdown ratio >= 0.50, parameter-sensitivity / holdout stability, net-of-cost returns, bear/sideways/low-liquidity stress, HK cost/slippage/lot-size/suspension/VCM/CAS, leverage/shorting/margin feasibility, positive excess return under fee/slippage/spread stress, worst-month / worst-rebalance-loss and time-under-water recovery limits, correlation to existing live profiles with an aggregate risk budget, and capacity controls. The matrix also exposes `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy`, `runtime_market_data_policy`, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, `snapshot_required_repository_policies` (including `baseline_rotation_live_enablement_policy` and `policy_value_live_enablement_policy`), and `snapshot_future_research_live_enablement_policy` (currently exposing only research-only `hk_earnings_revision_quality_overlay`, `hk_low_size_quality_liquidity_premium`, `hk_stock_connect_inclusion_event_flow`, `hk_short_selling_pressure_risk_overlay`, `hk_director_dealing_disclosure_quality_overlay`, `hk_dually_traded_liquid_reversal_overlay`, `hk_earnings_announcement_drift_overlay`, `hk_lottery_stock_risk_exclusion_overlay`, `hk_equity_financing_dilution_risk_overlay`, `hk_connected_transaction_governance_risk_overlay`, `hk_takeover_privatization_event_spread_overlay`, `hk_distribution_ex_date_entitlement_overlay`, `hk_ipo_lockup_overhang_event_overlay`, `hk_audit_opinion_suspension_risk_overlay`, `hk_share_repurchase_execution_signal_overlay`, `hk_liquid_pairs_cointegration_stat_arb_overlay`, `hk_macro_liquidity_inflation_rate_sensitivity_overlay`, `hk_turn_of_month_lunar_new_year_calendar_overlay`, `hk_etf_premium_discount_tracking_quality_overlay`, `hk_asset_growth_net_issuance_quality_overlay`, `hk_accrual_quality_earnings_persistence_overlay`, and `hk_shareholding_concentration_free_float_risk_overlay` as non-selectable candidates), so platforms can require `https://`, `gs://`, or `s3://` evidence URIs and reject evidence links that include token/password/signature-like query parameters, exceed freshness windows, miss per-symbol HKEX ETP/ETF classification, official product-document URI, underlying index / reference-asset source, NAV/iNAV source, tracking-error / tracking-difference review, ETF Connect / Stock Connect eligible or sell-only status, Southbound ETF daily turnover / fund-flow trend, broker Southbound ETF buy-route availability, cross-boundary settlement / holiday / eligibility-change review, leveraged/inverse/synthetic/futures-based or complex-product review, KID/prospectus risk review, multi-counter currency and creation/redemption handling, distribution/tax/fee treatment, broker product permission, trading-currency/board-lot/distribution/corporate-action checks, production market-data / ETF NAV / distribution / suspension audits, ADV / board-lot / odd-lot / VCM capacity checks, raw order-preview / quote-snapshot / fee-breakdown URI and sha256 provenance, or staged-rollout tripwire and rollback evidence.

The current first snapshot candidates are exposed by `first_snapshot_candidates`: `hk_low_vol_dividend_quality`, `hk_shareholder_yield_quality`, and `hk_free_cash_flow_quality`. This is not a live switch; it only prioritizes production data, backtest, and dry-run evidence work.
The detailed snapshot order comes from `HkEquitySnapshotPipelines` `recommended_live_enablement_sequence`; the first low-turnover quality/yield candidates must pass `quality_yield_live_enablement_policy` checks for low-vol dividend / shareholder-yield / FCF same-universe ablation, forecast-dividend-yield versus trailing-yield ablation, stale estimate-revision controls, yield-trap controls, HSHYLV/HSSCHYS-style Southbound eligibility, three-year cash-dividend records, payout-ratio bounds, price-crash screens, high-volatility exclusion, financial-soundness screens, share-count/treasury-share reconciliation, FCF formula/EV input/reporting-date/restatement/sector-exception handling, HKEX next-day repurchase returns, treasury-share retention/cancellation/resale, moratorium/blackout/connected-person controls, post-buyback financing review, sector/rate-cycle stress, and order-preview provenance; momentum-factor candidates exist, but they stay behind those first candidates and must pass `momentum_live_enablement_policy` checks for residual/liquid/composite ablation, HSI close-to-high versus MSCI 6/12-month one-month-skip risk-adjusted momentum reconciliation, 52-week-high versus 12-1 momentum comparison, volatility normalization, industry-neutral and quality-screen tests, turnover buffers, sector/capacity controls, reversal/high-beta/suspension/Southbound stress windows, and dry-run order-preview provenance before dry-run can be removed; Southbound-flow, AH-premium, and index-rebalance scaffolds must additionally pass `special_situation_live_enablement_policy` checks for official sources, calendar/close alignment, HSI methodology/operation-guide versioning, schedule-file versions, next-review notices, review-result press-release timestamps, constituent weight/pro-forma records, MOC-vs-next-open and pro-forma-weighted ablations, fast-entry / suspension / buffer-rule exception, HKEX CAS / market-on-close random-close / two-stage price-limit / order-rejection / passive-flow imbalance controls, signal decay, crowding/slippage, and dry-run order-preview provenance.

## HK runtime readiness

Use the packaged readiness command before changing IBKR or LongBridge runtime settings:

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_listed_global_etf_rotation --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform ibkr --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

The output is a runtime-readiness checklist, not a direct Cloud Run mutation. It covers HK market defaults, managed symbols, direct `market_history` requirements, LongBridge weight-to-value conversion, order preview, integer-share / lot-size checks, HKD cash lines, and Cloud Run environment review items.

The readiness JSON also exposes `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy`, `runtime_market_data_policy`, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, and `notification_audit_policy`, so platforms can block unstable evidence links or links with secret-like query parameters during dry-run readiness review, and require direct `market_history` proof for source name, coverage dates, stable `market_history_source_uri`, `market_history_quality_report_uri`, `point_in_time_data_dictionary_uri`, point-in-time adjusted prices, distributions, corporate actions, stale quotes, suspension/trading status, ETF NAV/iNAV, and stamp-duty/exemption sources; per-symbol ETF product due diligence for HKEX ETP/ETF classification, official product documents, underlying index / reference asset, NAV/iNAV, tracking error / tracking difference, ETF Connect / Stock Connect eligible or sell-only status, Southbound ETF daily turnover / fund-flow trend, broker Southbound ETF buy-route availability, cross-boundary settlement / holiday / eligibility-change review, leveraged/inverse/synthetic/futures-based or complex-product review, KID/prospectus risk disclosures, multi-counter currency and creation/redemption handling, distribution/tax/fee treatment, broker product permission, trading currency, board lot, distribution, and corporate actions; plus dry-run order-preview proof for ADV capacity, board-lot rounding, odd-lot avoidance, session routing, VCM/price-band controls, raw preview / quote snapshot / fee-breakdown artifact provenance, initial capital caps, kill switch, SWT/VCM runbooks, observation windows before scale-up, and bilingual EN/ZH-Hans notification delivery logs with correlation ids and redaction.

The readiness JSON also exposes `live_enablement_thresholds` and `required_live_evidence_fields`. Current hard limits are: `hk_listed_global_etf_rotation` max drawdown 30%, annual-return-to-max-drawdown ratio at least 0.50, at least 3 OOS folds, max single-period return contribution <= 60%, and annualized turnover 150%; `hk_high_dividend_low_vol_trend` max drawdown 12%, annual-return-to-max-drawdown ratio at least 0.50, at least 3 OOS folds, max single-period return contribution <= 60%, and annualized turnover 100%. A real live switch still needs at least three walk-forward / out-of-sample years, positive annual return, positive excess return versus the strategy metadata benchmark, survivorship/look-ahead controls, per-symbol ETF product due diligence, HK fees/levies, ETF stamp-duty exemption or applicable taxes, bid/ask spread, slippage, lot-size rounding, order-preview notifications, bilingual notification delivery-log proof, and operator approval.

Generate and validate a runtime evidence pack before switching to live:

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_high_dividend_low_vol_trend \
  --platform longbridge \
  --json > runtime-live-enable-evidence.json
```

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file runtime-live-enable-evidence.json \
  --json
```

The template and validation result also expose the same `evidence_uri_policy`, `evidence_freshness_policy`, `runtime_etf_product_policy`, `runtime_market_data_policy`, `execution_capacity_policy`, `dry_run_order_preview_policy`, `rollout_risk_policy`, and `notification_audit_policy`. Passing evidence packs cannot rely on booleans only: `strategy_backtest`, `runtime_readiness`, `platform_dry_run_order_preview`, `broker_permission_and_fee_verification`, and `runtime_switch_plan` must all provide non-empty stable `evidence_uri` values (`https://`, `gs://`, or `s3://`) plus ISO-date `evidence_generated_at` values, those URIs must not contain token/password/signature-like query parameters, `runtime_readiness` must satisfy production market-history provenance fields and market-data audit fields, `broker_permission_and_fee_verification` must include `etf_product_audit_id`, `managed_etf_symbols_audited_count`, stable `etf_product_universe_audit_uri` / `official_product_document_uri` / `underlying_index_or_reference_asset_source_uri` / `nav_or_inav_source_uri` / `market_maker_or_liquidity_provider_source_uri` / `stock_connect_etf_eligibility_source_uri` / `southbound_etf_turnover_and_fund_flow_source_uri` / `distribution_tax_and_fee_treatment_source_uri` / `etf_fee_and_stamp_duty_audit_uri` / `broker_product_permission_audit_uri`, and proof that all managed symbols are ETPs, leveraged/inverse/synthetic/futures-based or complex-product flags were reviewed, ETF tax/stamp-duty treatment was verified, market maker or liquidity-provider presence was checked, KID/prospectus risk disclosures were reviewed, official product documents are current, NAV/iNAV was reconciled, tracking difference was reviewed, ETF Connect / Stock Connect eligible or sell-only status, Southbound ETF daily turnover / fund-flow trend, broker Southbound ETF buy-route availability, and cross-boundary settlement / holiday / eligibility-change risks were reviewed, multi-counter currency / creation-redemption was reviewed, commodity-trust single-asset/storage risk and high-dividend concentration/yield-trap risk were reviewed, and broker permission, trading currency, board lot, distribution, and corporate-action handling were verified; `platform_dry_run_order_preview` must satisfy ADV / liquidity / board-lot / odd-lot / VCM capacity checks, include `dry_run_session_id`, stable raw order-preview / quote-snapshot / fee-breakdown artifact URIs, matching 64-character hex sha256 values, non-sample and redaction proof, quote coverage, broker fee reconciliation, strategy-decision reconciliation, and the `hk_live_enablement_notification.v1` audit schema (`hk_runtime_live_enablement_dry_run`, EN/ZH-Hans locales, correlation id, redaction, stable `notification_delivery_log_uri`), `runtime_switch_plan` must satisfy staged rollout / capital cap / tripwire / kill-switch / SWT-runbook / observation-window checks, and `risk_approval.approval_reference` must be non-empty for audit and rollback traceability.

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
- `docs/research/hk_high_dividend_low_vol_trend.md` records the high-dividend / gold two-ETF trend rotation backtest. Current conclusion: mark `runtime_enabled` because the 12% volatility-targeted version kept full-sample drawdown below 10%; platform Cloud Run environments can select it through runtime configuration.
- `docs/research/hk_listed_global_etf_rotation.md` records the HK-listed global ETF rotation backtest. Current conclusion: mark `runtime_enabled` because the volatility-targeted version kept full-sample drawdown under 30%; platform Cloud Run environments can select it through runtime configuration, but dry-run removal requires all eight ETFs' issuer documents, NAV/iNAV, underlying/reference asset, tracking difference, market-maker/liquidity provider, multi-counter, fee/tax, broker-permission, A-share trading-hour/price-band, Nasdaq time-zone, gold-trust, and crude-oil futures-roll/margin/curve evidence.
