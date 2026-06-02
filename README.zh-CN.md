# HkEquityStrategies

[English README](./README.md)

> 风险提示：本仓库仅用于工程实现、研究和运行审查，不构成投资建议。

`HkEquityStrategies` 是 QuantStrategyLab 港股非 snapshot 策略仓库。
它沿用 `UsEquityStrategies` 的边界：本仓库只负责纯策略逻辑、目录元数据、运行入口和 readiness / evidence 检查；券商仓库负责行情接入、账户状态、订单路由、密钥、部署和通知。

## 仓库边界

本仓库负责：

- 消费 direct `market_history` 的非 snapshot `hk_equity` 策略实现
- manifest/catalog 支撑的 runtime entrypoint
- 平台无关的 `StrategyDecision` 生成
- 港股 runtime readiness 与 live-enable evidence 校验工具
- 非 snapshot 港股策略研究记录

本仓库不负责：

- snapshot-backed 策略 artifact 生成
- 券商凭据或账户对账
- 下单或券商专项 order preview
- Cloud Run / Google Run 服务部署
- Telegram 或券商通知投递

Snapshot-backed 港股策略已经单独放在 [`../HkEquitySnapshotPipelines`](../HkEquitySnapshotPipelines)。不要在本 README 里继续堆 snapshot artifact contract 或 snapshot profile 列表；这些内容统一保留在 snapshot 仓库。

## 当前 runtime profile

| Canonical profile | 展示名 | 输入 | 兼容平台 | 频率 | 基准 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `hk_high_dividend_low_vol_trend` | HK High Dividend Low-Volatility Trend | `market_history` | `InteractiveBrokersPlatform`, `LongBridgePlatform` | monthly review | `03110` | `runtime_enabled` |
| `hk_listed_global_etf_rotation` | HK-listed Global ETF Rotation | `market_history` | `InteractiveBrokersPlatform`, `LongBridgePlatform` | monthly review | `02800` | `runtime_enabled` |

以下 profile 只保留为研究/回测记录，不进入 runtime catalog：

- `hk_index_mean_reversion`
- `hk_etf_regime_rotation`

平台仓库只应该暴露 `get_runtime_enabled_profiles()` 返回的 profile。

## 策略索引

### `hk_high_dividend_low_vol_trend`

- 目标：作为首个 live-enable 候选的低回撤港股 ETF 轮动策略。
- 标的范围：港股上市高股息 ETF 与黄金 ETF。
- 信号方式：月度趋势轮动，并使用波动率目标控制仓位。
- 风险目标：12% 年化波动率目标。
- 当前角色：优先级最高的非 snapshot runtime 候选；真实下单前仍必须补齐券商 dry-run 证据和人工审批。

研究记录：[`docs/research/hk_high_dividend_low_vol_trend.md`](./docs/research/hk_high_dividend_low_vol_trend.md)

### `hk_listed_global_etf_rotation`

- 目标：用港股上市 ETF 做本地股票、海外股票、黄金、原油等资产轮动。
- 输入：直接日频 `market_history`。
- 信号方式：月度检查、动量/趋势过滤、波动率目标配置。
- 当前角色：第二优先级非 snapshot runtime 候选；真实下单前需要 ETF 产品证据、NAV/iNAV 复核、流动性检查和 dry-run order preview。

研究记录：[`docs/research/hk_listed_global_etf_rotation.md`](./docs/research/hk_listed_global_etf_rotation.md)

## Runtime enablement 门槛

Live-enable 排名只是后续工作队列，不是投资推荐。
策略在生产下单前必须通过 evidence gate：

- 最大回撤 `<= 30%`；如果 profile 自己有更严格阈值，则按更严格阈值执行
- point-in-time 数据、无未来函数、无 survivorship bias 证明
- 至少 3 个独立样本外 fold
- 扣费后收益，以及港股滑点、lot-size、停牌、VCM、CAS 检查
- 券商权限、ETF 产品、NAV/iNAV、费用、税费和流动性证据
- dry-run order preview，且 artifact URI 稳定并带 sha256 provenance
- 中英文双语通知与 delivery-log 证据
- 分阶段上线、tripwire、kill switch、回滚计划和人工审批

请优先使用工具输出，不要手工解读 README：

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

这些命令默认是只读检查；不会修改 Cloud Run 或券商状态。

## 本地 smoke 命令

```bash
python -m pytest -q
```

运行 ETF 轮动策略的合成 dry-run smoke：

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## 文档

- [`docs/platform_integration.md`](./docs/platform_integration.md)：IBKR 和 LongBridge 平台集成说明。
- [`docs/research/hk_high_dividend_low_vol_trend.md`](./docs/research/hk_high_dividend_low_vol_trend.md)：高股息 / 黄金趋势轮动研究。
- [`docs/research/hk_listed_global_etf_rotation.md`](./docs/research/hk_listed_global_etf_rotation.md)：港股上市全球 ETF 轮动研究。
- [`docs/research/hk_index_mean_reversion.md`](./docs/research/hk_index_mean_reversion.md)：恒指 / 恒科均值回归研究-only 记录。
- [`docs/research/hk_etf_regime_rotation.md`](./docs/research/hk_etf_regime_rotation.md)：早期 ETF regime rotation 研究-only 记录。
- [`docs/research/hk_quant_strategy_ideas.md`](./docs/research/hk_quant_strategy_ideas.md)：港股策略想法清单。

## 相关仓库

- [`../HkEquitySnapshotPipelines`](../HkEquitySnapshotPipelines)：snapshot-backed 港股策略 artifact 和 scaffold helper。
- [`../QuantPlatformKit`](../QuantPlatformKit)：共享策略 contract 与 component loader。
- `InteractiveBrokersPlatform` / `LongBridgePlatform`：券商 runtime、部署、订单路由和通知归属。
