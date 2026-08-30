from pathlib import Path


QPK_REF = "1951dada893f1f05c897e6438b6c687d30b4e810"


def test_drift_workflow_builds_and_wires_lifecycle_preflight() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "drift-check.yml").read_text(encoding="utf-8")

    assert "preflight_backtests:" in workflow
    assert "python scripts/build_lifecycle_preflight.py" in workflow
    assert "--start 2020-08-27" in workflow
    assert "lifecycle-preflight-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "hk-lifecycle-inputs-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert f"uses: QuantStrategyLab/QuantPlatformKit/.github/workflows/reusable-drift-check.yml@{QPK_REF}" in workflow
    assert "strategy_domain: hk_equity" in workflow
    assert "caller_event_name: ${{ github.event_name }}" in workflow
    assert "caller_pr_head_repository: ${{ github.event.pull_request.head.repo.full_name || '' }}" in workflow
    assert "snapshot_repository: QuantStrategyLab/HkEquitySnapshotPipelines" in workflow
    assert "snapshot_checkout_path: external/HkEquitySnapshotPipelines" in workflow
    assert "snapshot_repository_ref: ${{ needs.preflight_backtests.outputs.snapshot_repository_ref }}" in workflow
    assert f"quant_platform_kit_ref: {QPK_REF}" in workflow
    assert "lifecycle_preflight_artifact: lifecycle-preflight-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "ai_gateway_service_url: ${{ vars.AI_GATEWAY_SERVICE_URL }}" in workflow
    assert "codex_audit_service_url: ${{ secrets.CODEX_AUDIT_SERVICE_URL }}" in workflow
    assert (
        "snapshot_repository_token: "
        "${{ secrets.SNAPSHOT_REPOSITORY_TOKEN || secrets.QSL_REPO_SYNC_TOKEN || github.token }}"
    ) in workflow
    assert "synthetic" not in workflow.lower()
