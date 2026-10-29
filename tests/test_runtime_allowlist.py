from hk_equity_strategies.catalog import get_runtime_enabled_profiles
from hk_equity_strategies.runtime_allowlist import get_runtime_selectable_profiles


def test_legacy_runtime_entrypoint_reads_explicit_allowlist():
    assert get_runtime_enabled_profiles() == get_runtime_selectable_profiles()


def test_combo_is_not_runtime_selectable():
    assert "hk_equity_combo" not in get_runtime_selectable_profiles()


def test_retired_profiles_are_not_selectable_but_remain_resolvable():
    from hk_equity_strategies.catalog import get_strategy_definition, resolve_canonical_profile

    assert get_runtime_enabled_profiles() == frozenset()
    for profile in ("hk_global_etf_tactical_rotation", "hk_low_vol_dividend_quality_snapshot"):
        assert resolve_canonical_profile(profile.replace("_", "-")) == profile
        assert get_strategy_definition(profile).profile == profile
        assert profile not in get_runtime_selectable_profiles()
