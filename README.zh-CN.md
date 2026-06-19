# HkEquityStrategies

[English README](README.md)

> 投资有风险。本项目不构成投资建议，仅用于学习、研究和工程审阅。

## 这个仓库是什么

`HkEquityStrategies` 是 QuantStrategyLab 的港股策略包，提供港股策略实现、manifest、catalog metadata、runtime adapter 和 live-enablement 检查，供支持港股的执行平台复用。

这是策略层，不是券商或部署层。本仓库不保存券商凭据，不自行下单，不发布 snapshot artifact，也不能在缺少外部证据的情况下决定某个 profile 是否适合 live。

## 当前 runtime 面

本分支精简了 canonical profile 名。旧名称不再保留为 alias，因此平台仓库应通过 `STRATEGY_PROFILE` 或 `RUNTIME_TARGET_JSON` 使用下面的新名字。

### 普通 runtime 策略

这些 profile 使用平台提供的 `market_history`，不需要先生成单独的 snapshot artifact，也能通过策略入口生成目标权重。

| Profile | 名称 | 输入 | 基准 | 当前角色 |
| --- | --- | --- | --- | --- |
| `hk_global_etf_tactical_rotation` | HK Global ETF Tactical Rotation | `market_history` | `02800` | 保留的港股 ETF runtime profile，覆盖更宽 ETF 范围，产品检查也更重。 |

### Snapshot-backed runtime 策略

策略包只暴露一个已提升的 snapshot-backed runtime entrypoint。`HkEquitySnapshotPipelines` 负责 artifact contract、生产数据 lineage 和 promotion 证据。

| Profile | 名称 | 输入 | 基准 | 当前角色 |
| --- | --- | --- | --- | --- |
| `hk_low_vol_dividend_quality_snapshot` | HK Low-Vol Dividend Quality Snapshot | `feature_snapshot` + manifest | `02800` | 保留的港股 snapshot-backed runtime 候选；仍需要 point-in-time 数据 lineage 和 promotion 证据。 |

### 已移除研究 profile

被拒绝的研究原型不再进入公开 catalog、manifest、entrypoint、runtime adapter 或 snapshot contract。平台仓库只应该暴露 `get_runtime_enabled_profiles()` 返回的 profile。

保留和剔除原因见 [`docs/research/hk_strategy_selection_20260603.md`](docs/research/hk_strategy_selection_20260603.md)。

## 表现和证据边界

本仓库里的研究数字是 review 证据，不是收益承诺。启用或调整 live profile 前，需要重新运行相关研究或 readiness 命令，并在适用场景下检查短、中、长周期：

- 收益和相对基准收益
- 最大回撤和回撤稳定性
- 换手、费用、lot-size、滑点、停牌、VCM 和 CAS 表现
- 数据新鲜度和 artifact 版本
- 券商 dry-run order preview、中英文通知日志、上线控制和人工审批

如果证据过期、不完整，或者 profile 不在 `get_runtime_enabled_profiles()` 返回值里，就不要放进 live runtime settings。

## 快速开始

```bash
python -m pip install -e '.[test]'
python -m pytest -q
```

## 查看 runtime readiness

以下命令默认只读；除非显式传入 evidence file，否则不会修改配置或下单：

```bash
python scripts/print_hk_live_enablement_matrix.py --json
python scripts/print_hk_runtime_readiness.py --profile hk_global_etf_tactical_rotation --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality_snapshot --platform longbridge --json
python scripts/validate_hk_runtime_live_enablement.py --print-template --profile hk_global_etf_tactical_rotation --platform longbridge --json
```

普通 ETF 轮动路径的本地 smoke：

```bash
python scripts/smoke_hk_global_etf_tactical_rotation_dry_run.py --json
```

## 如何接到执行平台

执行平台通过 strategy loader 和 runtime metadata 消费本策略包。券商凭据、行情权限、账户状态、dry-run/live 开关、下单、通知、部署配置和回滚控制都属于平台仓库。

当前支持港股 runtime 的平台包括：

- `InteractiveBrokersPlatform`
- `LongBridgePlatform`

## 安全部署

1. 券商凭据和账户标识不要放进 Git。
2. dry-run、paper、live 开关放在平台仓库里控制。
3. 启用定时执行前，先确认策略证据和平台 dry-run 输出。
4. 检查生成订单、通知、artifact URI 和回滚设置。
5. 先小规模分阶段运行，并在平台仓库保留 kill switch 操作说明。

## 仓库结构

- `src/`：策略实现、manifest、catalog metadata、runtime adapter 和 readiness policy。
- `tests/`：单元测试、契约测试和回归测试。
- `docs/`：平台集成说明、策略研究和 live-enablement 证据指南。
- `scripts/`：本地研究、smoke、readiness 和证据辅助工具。

## 延伸文档

- [`docs/platform_integration.md`](docs/platform_integration.md)
- [`docs/research/hk_strategy_selection_20260603.md`](docs/research/hk_strategy_selection_20260603.md)
- [`docs/research/hk_global_etf_tactical_rotation.md`](docs/research/hk_global_etf_tactical_rotation.md)
- [`docs/hk_low_vol_dividend_quality_snapshot_live_enablement.zh-CN.md`](docs/hk_low_vol_dividend_quality_snapshot_live_enablement.zh-CN.md)

## 安全和贡献说明

- 不要提交密钥、token、Cookie、券商凭据、账户标识或私人订单数据。
- 行为改动尽量小，并附上测试或可复现证据命令。
- 没有通过文档化 evidence gate 前，不要把研究 profile 提升到 live runtime settings。

## 社区和安全

- 贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，确认 PR 范围、本地校验和文档要求。
- 讨论、issue 和 review 请遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
- 涉及密钥、自动化、券商/交易所或云资源的漏洞请按 [SECURITY.md](SECURITY.md) 私密报告；不要为 secret 或实盘风险开公开 issue。

## 许可证

详见 [LICENSE](LICENSE)。
