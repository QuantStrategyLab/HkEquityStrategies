from pathlib import Path


QPK_REF = "eae362bd3e3fad5be59a7615eeba10be839a9934"
WORKFLOW_REF = "6aa877406037f02326f658cde54dd5b4080494be"


def test_drift_workflow_builds_and_wires_lifecycle_preflight() -> None:
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "drift-check.yml").read_text(encoding="utf-8")

    assert "preflight_backtests:" in workflow
    assert "python scripts/build_lifecycle_preflight.py" in workflow
    assert "--start 2020-08-27" in workflow
    assert "lifecycle-preflight-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "hk-lifecycle-inputs-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert f"uses: QuantStrategyLab/QuantPlatformKit/.github/workflows/reusable-drift-check.yml@{WORKFLOW_REF}" in workflow
    assert "strategy_domain: hk_equity" in workflow
    assert "caller_event_name: ${{ github.event_name }}" in workflow
    assert "caller_pr_head_repository: ${{ github.event.pull_request.head.repo.full_name || '' }}" in workflow
    assert "snapshot_repository: QuantStrategyLab/HkEquitySnapshotPipelines" in workflow
    assert "snapshot_checkout_path: external/HkEquitySnapshotPipelines" in workflow
    assert "snapshot_repository_ref: ${{ needs.preflight_backtests.outputs.snapshot_repository_ref }}" in workflow
    assert f"quant_platform_kit_ref: {QPK_REF}" in workflow
    assert "lifecycle_preflight_artifact: lifecycle-preflight-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    # Retired v1 Codex/GPT/Claude reviewer wiring must not return.
    assert "codex_audit_service_url" not in workflow
    assert "ai_gateway_service_url" not in workflow
    assert "ai_service_url: ${{ vars.AI_SERVICE_URL }}" in workflow
    assert "ai_service_audience: ${{ vars.AI_SERVICE_AUDIENCE }}" in workflow
    assert "ai_service_reviewers_json: ${{ vars.AI_SERVICE_REVIEWERS_JSON }}" in workflow
    assert (
        "snapshot_repository_token: "
        "${{ secrets.SNAPSHOT_REPOSITORY_TOKEN || secrets.QSL_REPO_SYNC_TOKEN || github.token }}"
    ) in workflow
    assert "synthetic" not in workflow.lower()
