# HkEquityStrategies

[English README](README.md)

> 投资有风险。本项目不构成投资建议，仅用于学习、研究和工程审阅。

## 这个仓库是什么

`HkEquityStrategies` 是 QuantStrategyLab 的港股策略包，为 Interactive Brokers、LongBridge 等支持港股的执行平台提供可复用策略实现、目录元数据、运行入口和 readiness 检查。

这是策略层，不是券商或部署层。本仓库不保存券商凭据，不自行下单，不发布 snapshot artifact，也不能在缺少外部证据的情况下决定某个 profile 是否适合 live。

## 策略 profile

### 普通 runtime 策略

这些 profile 直接使用 market-history 输入，不需要先生成单独的 feature-snapshot artifact，也能通过策略入口生成目标权重。

| Profile | 名称 | 输入 | 当前角色 |
| --- | --- | --- | --- |
| `hk_high_dividend_low_vol_trend` | HK High Dividend Low-Volatility Trend | `market_history` | runtime-enabled 的优先港股 ETF profile；真实下单前仍需要 dry-run 和人工审批证据。 |
| `hk_listed_global_etf_rotation` | HK-listed Global ETF Rotation | `market_history` | runtime-enabled 的第二港股 ETF profile，覆盖更宽 ETF 范围，需要额外产品审查。 |

### Snapshot-backed 策略

这些 profile 依赖 `HkEquitySnapshotPipelines` 生成并验证的 artifact。策略包只暴露运行入口，snapshot 仓库负责 artifact contract、数据 lineage 和 promotion 证据。

| Profile | 名称 | 输入 | 当前角色 |
| --- | --- | --- | --- |
| `hk_low_vol_dividend_quality` | HK Low-Volatility Dividend Quality | `feature_snapshot` | 策略包层面 runtime-enabled；在 artifact、券商、通知和人工审批证据通过前，只应 dry-run。 |

### 研究侧和外部 scaffold profile

以下 profile 只用于研究复现或后续评审，不应该作为当前可配置 live profile 暴露给平台：

- `hk_index_mean_reversion`
- `hk_etf_regime_rotation`
- `hk_shareholder_yield_quality`、`hk_free_cash_flow_quality` 等由 `HkEquitySnapshotPipelines` 跟踪的 external snapshot scaffold 候选

下游平台判断哪些 profile 可以配置运行时，应以 `get_runtime_enabled_profiles()` 为准。

## 如何接到执行平台

执行平台通过 strategy loader 和 runtime metadata 消费本策略包。券商凭据、行情权限、账户状态、dry-run/live 开关、下单、通知、部署配置和回滚控制都属于平台仓库。

当前支持港股 runtime 的平台包括：

- `InteractiveBrokersPlatform`
- `LongBridgePlatform`

## 策略证据和 live enablement

README 是项目地图，不是固定表现报告。启用或调整 live profile 前，需要重新运行相关研究、snapshot 或 readiness 工具，并在适用场景下检查短、中、长周期：

- 收益和相对基准收益
- 最大回撤和回撤稳定性
- 换手、费用、lot-size、滑点、停牌、VCM 和 CAS 表现
- 数据新鲜度和 artifact 版本
- dry-run order preview、中英文通知日志、上线控制和人工审批

如果证据过期、不完整，或者 profile 仍是 research-only，就不要放进 live runtime settings。

## 快速开始

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

## 查看 runtime readiness

以下命令默认只读；除非显式传入 evidence file，否则不会修改配置或下单：

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_high_dividend_low_vol_trend --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_high_dividend_low_vol_trend --platform longbridge --json
```

ETF 轮动路径的本地 smoke：

```bash
python scripts/smoke_hk_listed_global_etf_rotation_dry_run.py --json
```

## 安全部署

1. 券商凭据和账户标识不要放进 Git。
2. dry-run、paper、live 开关放在平台仓库里控制。
3. 启用定时执行前，先确认策略证据和平台 dry-run 输出。
4. 检查生成订单、通知、artifact URI 和回滚设置。
5. 先小规模分阶段运行，并在平台仓库保留 kill switch 操作说明。

## 仓库结构

- `src/`：策略实现、目录元数据、入口和 readiness policy。
- `tests/`：单元测试、契约测试和回归测试。
- `docs/`：平台集成说明和 live-enablement 证据指南。
- `scripts/`：本地研究、smoke、readiness 和证据辅助工具。

## 延伸文档

- [`docs/platform_integration.md`](docs/platform_integration.md)
- [`docs/hk_low_vol_dividend_quality_live_enablement.zh-CN.md`](docs/hk_low_vol_dividend_quality_live_enablement.zh-CN.md)
- [`docs/research/hk_high_dividend_low_vol_trend.md`](docs/research/hk_high_dividend_low_vol_trend.md)
- [`docs/research/hk_listed_global_etf_rotation.md`](docs/research/hk_listed_global_etf_rotation.md)
- [`docs/research/hk_index_mean_reversion.md`](docs/research/hk_index_mean_reversion.md)
- [`docs/research/hk_etf_regime_rotation.md`](docs/research/hk_etf_regime_rotation.md)
- [`docs/research/hk_quant_strategy_ideas.md`](docs/research/hk_quant_strategy_ideas.md)

## 安全和贡献说明

- 不要提交密钥、token、Cookie、券商凭据、账户标识或私人订单数据。
- 行为改动尽量小，并附上测试或可复现证据命令。
- 没有通过文档化 evidence gate 前，不要把研究 profile 提升到 live runtime settings。

## 许可证

详见 [LICENSE](LICENSE)。
