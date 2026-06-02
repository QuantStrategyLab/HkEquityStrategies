# 港股低波股息质量策略 live-enable 操作清单

本文档用于把 `hk_low_vol_dividend_quality` 推进到真正可 live-enable 的状态。当前策略已经进入 HK 策略包 runtime catalog，但在所有证据门槛通过前，真实下单必须继续保持 dry-run。

## 仓库合并顺序

1. 先合并 `HkEquitySnapshotPipelines` 的 snapshot proxy-cycle / promotion evidence PR。
2. 再合并 `HkEquityStrategies` 的 runtime strategy / readiness / evidence gate PR。
3. 合并后为 `HkEquityStrategies` 创建 release tag。
4. `LongBridgePlatform` 和 `InteractiveBrokersPlatform` 将 `requirements.txt` 从临时 commit SHA 改为 release tag 后，再合并平台 PR。

不要因为包代码合并了就移除平台 dry-run。

## 运行时输入

`hk_low_vol_dividend_quality` 是 snapshot-backed 策略，运行时必须提供：

- `hk_low_vol_dividend_quality_factor_snapshot_latest.csv`
- `hk_low_vol_dividend_quality_factor_snapshot_latest.csv.manifest.json`
- `HkEquitySnapshotPipelines` 产出的 point-in-time lineage / artifact-pack validation 证据

真实 artifact 发布前，平台环境变量应保持占位和 dry-run：

```bash
# LongBridge
LONGBRIDGE_FEATURE_SNAPSHOT_PATH=<required>
LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH=<required>
LONGBRIDGE_DRY_RUN_ONLY=true

# IBKR
IBKR_FEATURE_SNAPSHOT_PATH=<required>
IBKR_FEATURE_SNAPSHOT_MANIFEST_PATH=<required>
IBKR_DRY_RUN_ONLY=true
```

artifact 发布后，只能使用稳定的 `gs://`、`s3://` 或 `https://` URI，且 URI 不能包含 token、signature、password 等疑似敏感 query 参数。

## 上线前验证命令

渲染两个平台的 readiness：

```bash
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality --platform longbridge --json
python scripts/print_hk_runtime_readiness.py --profile hk_low_vol_dividend_quality --platform ibkr --json
```

生成 evidence template：

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_low_vol_dividend_quality \
  --platform longbridge \
  --json > live-enable-evidence.longbridge.json

python scripts/validate_hk_runtime_live_enablement.py \
  --print-template \
  --profile hk_low_vol_dividend_quality \
  --platform ibkr \
  --json > live-enable-evidence.ibkr.json
```

验证填好的 evidence pack：

```bash
python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file live-enable-evidence.longbridge.json \
  --json

python scripts/validate_hk_runtime_live_enablement.py \
  --evidence-file live-enable-evidence.ibkr.json \
  --json
```

只有结果为 `validation_status=passed` 且 `live_enablement_allowed=true` 时，才允许进入 dry-run removal 决策。

## 必需证据

证据包必须证明：

- 至少 3 个独立 OOS fold 的 out-of-sample / walk-forward 回测
- 最大回撤 <= 30%
- 年化收益 / 最大回撤 >= 0.50
- 单一期贡献 <= 60%
- 年化换手 <= 100%
- 年化收益为正，且相对 `02800` 的超额收益为正
- factor snapshot 是 point-in-time，无未来函数、无幸存者偏差、无全样本调参
- factor snapshot artifact、manifest、contract version、lineage URI 均通过验证
- 使用港股单票权益尽调，不使用 ETF 尽调字段替代
- Stock Connect eligibility 或券商直连交易路径证据
- board lot、交易币种、公司行动、停牌/交易状态、股息/派息、费用/印花税、券商权限证据
- dry-run order preview 无碎股、lot size、币种、symbol mapping 错误
- raw order preview、quote snapshot、fee breakdown artifact 及 sha256 provenance
- liquidity/ADV、board-lot、odd-lot、market session、VCM/price-band、equity spread/trading-status guard
- EN/ZH-Hans 双语通知 delivery log，且敏感字段已脱敏
- staged rollout、rollback、kill switch、tripwire、恶劣天气交易、VCM cooling-off 处理
- operator approval、live rollout approval、dry-run removal approval 引用

## 平台 switch-plan smoke check

LongBridge：

```bash
cd ../LongBridgePlatform
.venv/bin/python scripts/print_strategy_switch_env_plan.py \
  --profile hk_low_vol_dividend_quality \
  --account-region HK \
  --dry-run-only \
  --json
```

IBKR：

```bash
cd ../InteractiveBrokersPlatform
.venv/bin/python scripts/print_strategy_switch_env_plan.py \
  --profile hk_low_vol_dividend_quality \
  --dry-run-only \
  --deployment-selector hk-verify \
  --account-scope HK \
  --service-name interactive-brokers-hk-verify-service \
  --json
```

两个命令都必须显示：

- `enabled=true`
- `input_mode=feature_snapshot`
- feature snapshot path 和 manifest path 必填
- artifact hint 指向 `hk_low_vol_dividend_quality_factor_snapshot_latest.csv`

## 最终 dry-run removal gate

只有满足以下条件，才允许移除 dry-run：

1. 四个仓库 PR 已按依赖顺序合并；
2. 平台依赖已指向合并后的 HK 策略 release tag；
3. 生产 factor snapshot artifact、manifest、lineage 已发布；
4. 两个平台 switch plan 均指向已发布 artifact URI；
5. 已捕获 dry-run order preview 和双语通知日志；
6. 目标平台 evidence pack 通过 validator；
7. 已记录 operator approval 引用。

在此之前，继续保持 `LONGBRIDGE_DRY_RUN_ONLY=true` 和 `IBKR_DRY_RUN_ONLY=true`。
