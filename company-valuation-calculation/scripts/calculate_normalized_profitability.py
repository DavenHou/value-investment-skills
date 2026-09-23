#!/usr/bin/env python3
"""Build bullish, neutral, and conservative normalized ROE/ROA scenarios."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from statistics import median, pstdev
from typing import Any


CYCLE_PHASES = ("trough", "recovery", "boom", "downturn")


@dataclass(frozen=True)
class Policy:
    default_history_years: int
    history_share: float
    history_half_life: float
    forecast_share: float
    forecast_half_life: float


POLICIES = {
    "stable": Policy(3, 0.50, 2.0, 0.50, 2.0),
    "cyclical": Policy(10, 0.70, 6.0, 0.30, 2.0),
    "technology": Policy(5, 0.50, 3.0, 0.50, 1.5),
}

DEFAULT_WEIGHTS = {
    "stable": ([0.125, 1 / 6, 5 / 24], [0.20, 0.20, 0.10]),
    "cyclical": (
        [0.03, 0.04, 0.05, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.13],
        [0.15, 0.10, 0.05],
    ),
    "technology": ([0.05, 0.07, 0.09, 0.12, 0.17], [0.25, 0.15, 0.10]),
}


def parse_series(raw: str) -> list[float]:
    try:
        values = [float(item.strip()) for item in raw.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("series must be comma-separated numbers") from exc
    if not values:
        raise argparse.ArgumentTypeError("series cannot be empty")
    return values


def parse_labels(raw: str) -> list[str]:
    labels = [item.strip().lower() for item in raw.split(",") if item.strip()]
    if not labels:
        raise argparse.ArgumentTypeError("labels cannot be empty")
    invalid = sorted(set(labels) - set(CYCLE_PHASES))
    if invalid:
        raise argparse.ArgumentTypeError(
            "cycle phases must be trough,recovery,boom,downturn; invalid: "
            + ",".join(invalid)
        )
    return labels


def recency_weights(count: int, share: float, half_life: float, *, future: bool) -> list[float]:
    if count <= 0 or share < 0 or half_life <= 0:
        raise ValueError("invalid weight parameters")
    distances = list(range(count)) if future else list(reversed(range(count)))
    raw = [0.5 ** (distance / half_life) for distance in distances]
    scale = share / sum(raw)
    weights = [value * scale for value in raw]
    if max(weights) > 0.25 + 1e-12:
        raise ValueError("a generated single-year weight exceeds the 25% cap")
    return weights


def weighted(values: list[float], weights: list[float]) -> float:
    if len(values) != len(weights):
        raise ValueError("values and weights must have the same length")
    return sum(value * weight for value, weight in zip(values, weights, strict=True))


def rescale_weights(weights: list[float], share: float, cap: float = 0.25) -> list[float]:
    """Rescale final-year weights and redistribute any amount above the cap."""
    if share < 0 or not weights or any(weight < 0 for weight in weights):
        raise ValueError("invalid weights or share")
    if share > len(weights) * cap + 1e-12:
        raise ValueError("requested block share cannot satisfy the 25% single-year cap")
    remaining = share
    active = set(range(len(weights)))
    result = [0.0] * len(weights)
    while active:
        active_total = sum(weights[index] for index in active)
        if active_total <= 0:
            equal = remaining / len(active)
            for index in active:
                result[index] = equal
            break
        provisional = {
            index: remaining * weights[index] / active_total for index in active
        }
        capped = [index for index, value in provisional.items() if value > cap + 1e-12]
        if not capped:
            for index, value in provisional.items():
                result[index] = value
            break
        for index in capped:
            result[index] = cap
            remaining -= cap
            active.remove(index)
    return result


def block_average(values: list[float], weights: list[float]) -> float:
    return weighted(values, weights) / sum(weights)


def lower_tail_indices(values: list[float]) -> list[int]:
    """Select the weakest ~40% of comparable history, with at least two years."""
    count = min(len(values), max(2, math.ceil(len(values) * 0.40)))
    return sorted(sorted(range(len(values)), key=lambda index: (values[index], index))[:count])


def selected_average(values: list[float], relative_weights: list[float], indices: list[int]) -> float:
    selected_values = [values[index] for index in indices]
    selected_weights = [relative_weights[index] for index in indices]
    return weighted(selected_values, selected_weights) / sum(selected_weights)


def phase_balanced_average(
    values: list[float], phases: list[str]
) -> tuple[float, dict[str, float]]:
    """Give each complete-cycle phase equal weight, then average within phases."""
    if len(values) != len(phases):
        raise ValueError("historical_phases length must match historical_roe")
    missing = [phase for phase in CYCLE_PHASES if phase not in phases]
    if missing:
        raise ValueError(
            "historical_phases must cover trough,recovery,boom,downturn; missing: "
            + ",".join(missing)
        )
    phase_averages = {
        phase: sum(value for value, label in zip(values, phases, strict=True) if label == phase)
        / phases.count(phase)
        for phase in CYCLE_PHASES
    }
    return sum(phase_averages.values()) / len(CYCLE_PHASES), phase_averages


def calculate(
    *,
    company_type: str,
    historical_roe: list[float],
    forecast_bear_roe: list[float],
    forecast_base_roe: list[float] | None = None,
    forecast_bull_roe: list[float] | None = None,
    historical_roa: list[float] | None = None,
    forecast_bear_roa: list[float] | None = None,
    forecast_base_roa: list[float] | None = None,
    forecast_bull_roa: list[float] | None = None,
    current_ttm_roe: float | None = None,
    current_ttm_roa: float | None = None,
    current_weak_roe: float | None = None,
    current_weak_roa: float | None = None,
    stable_years_comparable: str = "unknown",
    stability_policy: str = "strict",
    strict_candidate_count: int | None = None,
    minimum_candidate_count: int = 6,
    high_roe_review_status: str = "not_reviewed",
    historical_phases: list[str] | None = None,
    historical_mode: str = "conservative",
    forecast_confidence: str = "high",
    history_share: float | None = None,
    forecast_share: float | None = None,
    history_half_life: float | None = None,
    forecast_half_life: float | None = None,
) -> dict[str, Any]:
    if company_type not in POLICIES:
        raise ValueError(f"unknown company_type: {company_type}")
    if len(forecast_bear_roe) != 3:
        raise ValueError("forecast_bear_roe must contain exactly three full fiscal years")
    if company_type == "stable" and len(historical_roe) < 3:
        raise ValueError("stable companies require at least three comparable full fiscal years")
    if forecast_base_roe is not None and len(forecast_base_roe) != 3:
        raise ValueError("forecast_base_roe must contain exactly three full fiscal years")
    if forecast_bull_roe is not None and len(forecast_bull_roe) != 3:
        raise ValueError("forecast_bull_roe must contain exactly three full fiscal years")
    if historical_roa is not None and len(historical_roa) != len(historical_roe):
        raise ValueError("historical_roa length must match historical_roe")
    if forecast_bear_roa is not None and len(forecast_bear_roa) != 3:
        raise ValueError("forecast_bear_roa must contain exactly three full fiscal years")
    if forecast_base_roa is not None and len(forecast_base_roa) != 3:
        raise ValueError("forecast_base_roa must contain exactly three full fiscal years")
    if forecast_bull_roa is not None and len(forecast_bull_roa) != 3:
        raise ValueError("forecast_bull_roa must contain exactly three full fiscal years")
    if (historical_roa is None) != (forecast_bear_roa is None):
        raise ValueError("provide both historical_roa and forecast_bear_roa, or neither")
    if (forecast_base_roe is None) != (forecast_base_roa is None and historical_roa is not None):
        if historical_roa is not None:
            raise ValueError("when ROA series are supplied, provide both forecast_base_roe and forecast_base_roa, or neither")
    if historical_roa is not None and (forecast_bull_roe is None) != (forecast_bull_roa is None):
        raise ValueError("when ROA series are supplied, provide both forecast_bull_roe and forecast_bull_roa, or neither")
    if historical_roa is None and forecast_bull_roa is not None:
        raise ValueError("forecast_bull_roa requires historical_roa")
    if historical_mode not in {"conservative", "weighted"}:
        raise ValueError("historical_mode must be conservative or weighted")
    if historical_roa is None and current_weak_roa is not None:
        raise ValueError("current_weak_roa requires historical_roa and forecast_bear_roa")
    if current_ttm_roa is not None and current_ttm_roe is None:
        raise ValueError("current_ttm_roa requires current_ttm_roe")
    if stable_years_comparable not in {"confirmed", "not_confirmed", "unknown"}:
        raise ValueError(
            "stable_years_comparable must be confirmed, not_confirmed, or unknown"
        )
    if company_type != "stable" and stable_years_comparable != "unknown":
        raise ValueError("stable_years_comparable is only valid for company_type stable")
    if stability_policy not in {"strict", "controlled_relaxation"}:
        raise ValueError("stability_policy must be strict or controlled_relaxation")
    if company_type != "stable" and stability_policy != "strict":
        raise ValueError("controlled_relaxation is only valid for company_type stable")
    if minimum_candidate_count <= 0:
        raise ValueError("minimum_candidate_count must be positive")
    if strict_candidate_count is not None and strict_candidate_count < 0:
        raise ValueError("strict_candidate_count cannot be negative")
    if stability_policy == "controlled_relaxation" and strict_candidate_count is None:
        raise ValueError(
            "controlled_relaxation requires strict_candidate_count to prove candidate scarcity"
        )
    if high_roe_review_status not in {
        "not_reviewed",
        "organic_high_return",
        "usable_with_caution",
        "buyback_or_leverage_distorted",
        "insufficient",
    }:
        raise ValueError(
            "high_roe_review_status must be not_reviewed, organic_high_return, usable_with_caution, buyback_or_leverage_distorted, or insufficient"
        )
    if historical_roa is not None and current_weak_roe is not None and current_weak_roa is None:
        raise ValueError("current_weak_roa is required when current_weak_roe is supplied with ROA series")
    if historical_phases is not None and company_type != "cyclical":
        raise ValueError("historical_phases is only valid for company_type cyclical")
    if historical_phases is not None and len(historical_phases) != len(historical_roe):
        raise ValueError("historical_phases length must match historical_roe")

    policy = POLICIES[company_type]
    h_share = policy.history_share if history_share is None else history_share
    f_share = policy.forecast_share if forecast_share is None else forecast_share
    if abs(h_share + f_share - 1.0) > 1e-9:
        raise ValueError("history_share and forecast_share must sum to 1")
    if not 0 <= h_share <= 1 or not 0 <= f_share <= 1:
        raise ValueError("block shares must be in [0, 1]")

    warnings: list[str] = []
    if len(historical_roe) != policy.default_history_years:
        warnings.append(
            f"default history is {policy.default_history_years} years for {company_type}; "
            f"received {len(historical_roe)} years"
        )

    blend_usable = forecast_confidence != "low"
    if forecast_confidence == "medium" and company_type != "stable":
        f_share *= 0.75
        h_share = 1.0 - f_share
        warnings.append("medium forecast confidence: forecast block reduced to 75% of default")
    elif forecast_confidence == "medium":
        warnings.append(
            "medium forecast confidence: stable-company normalization keeps its fixed 50/50 split; confidence label only"
        )
    elif forecast_confidence == "low":
        warnings.append("low forecast confidence: history and forecast are shown separately; no blend")
    elif forecast_confidence != "high":
        raise ValueError("forecast_confidence must be high, medium, or low")

    h_half = policy.history_half_life if history_half_life is None else history_half_life
    f_half = policy.forecast_half_life if forecast_half_life is None else forecast_half_life
    default_h_weights, default_f_weights = DEFAULT_WEIGHTS[company_type]
    if len(historical_roe) == policy.default_history_years and history_half_life is None:
        h_weights = rescale_weights(default_h_weights, h_share)
    else:
        h_weights = recency_weights(len(historical_roe), h_share, h_half, future=False)
    if forecast_half_life is None:
        f_weights = rescale_weights(default_f_weights, f_share)
    else:
        f_weights = recency_weights(len(forecast_bear_roe), f_share, f_half, future=True)

    history_relative_weights = [weight / sum(h_weights) for weight in h_weights]
    weak_indices = lower_tail_indices(historical_roe)
    history_recent_roe = block_average(historical_roe, h_weights)
    cycle_phase_roe: dict[str, float] | None = None
    cycle_phase_status: str | None = None
    stable_three_year_roe = historical_roe[-3:] if company_type == "stable" else None
    stable_three_year_mean_roe = (
        sum(stable_three_year_roe) / 3 if stable_three_year_roe is not None else None
    )
    stable_three_year_sd_roe = (
        pstdev(stable_three_year_roe) if stable_three_year_roe is not None else None
    )
    stable_three_year_cv_roe = (
        abs(stable_three_year_sd_roe / stable_three_year_mean_roe) * 100.0
        if stable_three_year_mean_roe not in {None, 0}
        and stable_three_year_sd_roe is not None
        else None
    )
    stable_quantitatively_stable = (
        stable_three_year_roe is not None
        and all(value > 0 for value in stable_three_year_roe)
        and stable_three_year_cv_roe is not None
        and stable_three_year_cv_roe <= 25.0
    )
    stable_latest_to_mean_percent = (
        stable_three_year_roe[-1] / stable_three_year_mean_roe * 100.0
        if stable_three_year_roe is not None
        and stable_three_year_mean_roe not in {None, 0}
        else None
    )
    stable_relaxation_requested_and_needed = (
        company_type == "stable"
        and stability_policy == "controlled_relaxation"
        and strict_candidate_count is not None
        and strict_candidate_count < minimum_candidate_count
    )
    stable_relaxed_quantitative_eligible = (
        stable_three_year_roe is not None
        and all(value > 0 for value in stable_three_year_roe)
        and stable_three_year_cv_roe is not None
        and stable_three_year_cv_roe <= 40.0
        and stable_latest_to_mean_percent is not None
        and stable_latest_to_mean_percent >= 70.0
    )
    stable_strict_usable = (
        company_type == "stable"
        and stable_quantitatively_stable
        and stable_years_comparable == "confirmed"
    )
    stable_relaxed_usable = (
        company_type == "stable"
        and not stable_strict_usable
        and stable_relaxation_requested_and_needed
        and stable_relaxed_quantitative_eligible
        and stable_years_comparable == "confirmed"
    )
    stable_stability_tier = (
        "strict_stable"
        if stable_strict_usable
        else "relaxed_stable"
        if stable_relaxed_usable
        else "unstable"
        if company_type == "stable"
        else "not_applicable"
    )
    stable_neutral_anchor_usable = (
        stable_strict_usable or stable_relaxed_usable
        if company_type == "stable"
        else None
    )
    if company_type == "cyclical" and historical_phases is not None:
        history_neutral_roe, cycle_phase_roe = phase_balanced_average(
            historical_roe, historical_phases
        )
        cycle_phase_status = "complete_phase_balanced"
    elif company_type == "cyclical":
        history_neutral_roe = sum(historical_roe) / len(historical_roe)
        cycle_phase_status = "provisional_equal_weight"
        warnings.append(
            "cyclical neutral history uses a provisional equal-weight average because --historical-phases was not supplied; do not mark a single-point valuation valid until a complete cycle is evidenced"
        )
    elif company_type == "stable":
        history_neutral_roe = stable_three_year_mean_roe
        if stable_relaxed_usable:
            warnings.append(
                "stable-company three-year ROE uses controlled relaxation because the strict candidate pool is below the minimum; confidence and position tiers must be reduced"
            )
        elif not stable_quantitatively_stable:
            warnings.append(
                "stable-company three-year ROE did not pass the strict stability screen and no controlled relaxation is available; neutral PR is diagnostic only"
            )
        elif stable_years_comparable != "confirmed":
            warnings.append(
                "stable-company three-year business/accounting/capital-structure comparability is not confirmed; neutral PR is diagnostic only"
            )
    else:
        history_neutral_roe = history_recent_roe
    history_lower_tail_roe = selected_average(
        historical_roe, history_relative_weights, weak_indices
    )
    current_weak_roe_value = historical_roe[-1] if current_weak_roe is None else current_weak_roe
    use_current_weak = current_weak_roe_value <= history_lower_tail_roe
    history_conservative_roe = current_weak_roe_value if use_current_weak else history_lower_tail_roe
    if history_recent_roe > 0 and history_conservative_roe < history_recent_roe * 0.75:
        warnings.append(
            "historical conservative ROE anchor is more than 25% below the recent-weighted average; review comparability and prefer a range"
        )
    history_anchor_roe = (
        history_conservative_roe if historical_mode == "conservative" else history_recent_roe
    )
    cycle_five_year_low_index = (
        min(range(len(historical_roe) - 5, len(historical_roe)), key=historical_roe.__getitem__)
        if company_type == "cyclical" and len(historical_roe) >= 5
        else None
    )
    if company_type == "cyclical" and cycle_five_year_low_index is None:
        warnings.append("cyclical five-year minimum ROE needs five comparable full years; no actionable blend")
    normalized_history_anchor_roe = (
        historical_roe[cycle_five_year_low_index]
        if cycle_five_year_low_index is not None
        else history_conservative_roe if company_type == "stable" else history_anchor_roe
    )
    neutral_history_anchor_roe = (
        history_conservative_roe if company_type == "stable" else history_neutral_roe
    )
    forecast_roe = block_average(forecast_bear_roe, f_weights)
    forecast_base_roe_average = (
        block_average(forecast_base_roe, f_weights)
        if forecast_base_roe is not None
        else None
    )
    forecast_bull_roe_average = (
        block_average(forecast_bull_roe, f_weights)
        if forecast_bull_roe is not None
        else None
    )
    normalized_bear_roe = (
        h_share * normalized_history_anchor_roe + f_share * forecast_roe
        if blend_usable and (company_type != "cyclical" or cycle_five_year_low_index is not None)
        else None
    )
    cycle_60_40_roe = (
        0.60 * normalized_history_anchor_roe + 0.40 * forecast_roe
        if company_type == "cyclical" and cycle_five_year_low_index is not None and blend_usable
        else None
    )
    normalized_neutral_roe = (
        h_share * neutral_history_anchor_roe + f_share * forecast_base_roe_average
        if blend_usable and forecast_base_roe_average is not None
        else None
    )
    normalized_bull_roe = (
        h_share * neutral_history_anchor_roe + f_share * forecast_bull_roe_average
        if blend_usable and forecast_bull_roe_average is not None
        else None
    )

    high_roe_values: dict[str, float] = {
        f"historical_year_{index + 1}_of_latest_3": value
        for index, value in enumerate(historical_roe[-3:])
        if value > 40.0
    }
    if current_ttm_roe is not None and current_ttm_roe > 40.0:
        high_roe_values["current_ttm"] = current_ttm_roe
    high_roe_triggered = bool(high_roe_values)
    if not high_roe_triggered and high_roe_review_status != "not_reviewed":
        raise ValueError(
            "a non-default high_roe_review_status is only valid when current TTM or a latest-three-year ROE exceeds 40%"
        )
    high_roe_roa_evidence_complete = (
        historical_roa is not None
        and current_ttm_roa is not None
        and current_ttm_roe is not None
    )
    if high_roe_triggered and not high_roe_roa_evidence_complete:
        warnings.append(
            "ROE above 40% requires aligned current-TTM and three-year ROA evidence before the financial-engineering review can be resolved"
        )
    high_roe_review_resolved = (
        high_roe_triggered
        and high_roe_review_status
        in {
            "organic_high_return",
            "usable_with_caution",
            "buyback_or_leverage_distorted",
        }
        and high_roe_roa_evidence_complete
    )
    if high_roe_triggered and not high_roe_review_resolved:
        warnings.append(
            "ROE above 40%: PR/ROE output is diagnostic only until buybacks, equity shrinkage, leverage and ROA/ROIC/FCF are reviewed"
        )
    neutral_anchor_gate_passed = (
        stable_neutral_anchor_usable
        if company_type == "stable"
        else cycle_phase_status == "complete_phase_balanced"
        if company_type == "cyclical"
        else True
    )
    high_roe_gate_passed = (
        not high_roe_triggered
        or (
            high_roe_review_resolved
            and high_roe_review_status
            in {"organic_high_return", "usable_with_caution"}
        )
    )
    roe_pr_executable = bool(
        blend_usable and neutral_anchor_gate_passed and high_roe_gate_passed
        and (
            company_type != "cyclical"
            or (
                cycle_five_year_low_index is not None
                and historical_roe[cycle_five_year_low_index] > 0
                and normalized_bear_roe is not None
                and normalized_bear_roe > 0
            )
        )
    )

    result: dict[str, Any] = {
        "company_type": company_type,
        "forecast_confidence": forecast_confidence,
        "blend_usable": blend_usable,
        "neutral_blend_usable": bool(blend_usable and neutral_anchor_gate_passed),
        "roe_pr_executable": roe_pr_executable,
        "historical_mode": historical_mode,
        "weights": {
            "historical_oldest_to_newest": h_weights,
            "forecast_bear_nearest_to_farthest": f_weights,
            "forecast_base_nearest_to_farthest": f_weights if forecast_base_roe is not None else None,
            "forecast_bull_nearest_to_farthest": f_weights if forecast_bull_roe is not None else None,
            "history_share": h_share,
            "forecast_share": f_share,
        },
        "historical_selection": {
            "rule": "weakest_40_percent_minimum_two_years_selected_by_roe",
            "selected_year_indices_oldest_is_1": [index + 1 for index in weak_indices],
            "selected_year_count": len(weak_indices),
            "cycle_five_year_low_index_oldest_is_1": (
                cycle_five_year_low_index + 1 if cycle_five_year_low_index is not None else None
            ),
            "current_weak_source": (
                "latest_completed_historical_year" if current_weak_roe is None else "user_supplied_current_weak_run_rate"
            ),
            "anchor_source_selected_by_roe": (
                "current_weak_run_rate" if use_current_weak else "historical_lower_tail"
            ),
            "neutral_anchor_method": (
                "complete_cycle_phase_balanced"
                if cycle_phase_status == "complete_phase_balanced"
                else "complete_cycle_equal_weight_provisional"
                if cycle_phase_status == "provisional_equal_weight"
                else "historical_conservative_anchor_shared_with_bear"
                if company_type == "stable"
                else "recent_weighted"
            ),
            "cycle_phase_status": cycle_phase_status,
            "cycle_phase_labels_oldest_to_newest": historical_phases,
        },
        "stable_three_year_stability": (
            {
                "roe_values_oldest_to_newest": stable_three_year_roe,
                "equal_weight_mean_roe_percent": stable_three_year_mean_roe,
                "standard_deviation_roe_points": stable_three_year_sd_roe,
                "coefficient_of_variation_percent": stable_three_year_cv_roe,
                "cv_threshold_percent": 25.0,
                "relaxed_cv_ceiling_percent": 40.0,
                "all_years_positive": all(value > 0 for value in stable_three_year_roe),
                "quantitative_status": (
                    "strict_stable"
                    if stable_quantitatively_stable
                    else "relaxed_eligible"
                    if stable_relaxed_quantitative_eligible
                    else "unstable"
                ),
                "latest_year_to_three_year_mean_percent": stable_latest_to_mean_percent,
                "latest_year_floor_percent_of_mean": 70.0,
                "qualitative_comparability": stable_years_comparable,
                "stability_policy": stability_policy,
                "strict_candidate_count": strict_candidate_count,
                "minimum_candidate_count": minimum_candidate_count,
                "candidate_scarcity_confirmed": stable_relaxation_requested_and_needed,
                "stability_tier": stable_stability_tier,
                "neutral_anchor_usable": stable_neutral_anchor_usable,
                "position_treatment": (
                    "normal_subject_to_all_other_gates"
                    if stable_stability_tier == "strict_stable"
                    else "ordinary_entry_and_add_only_cumulative_cap_15_percent_until_reconfirmed"
                    if stable_stability_tier == "relaxed_stable"
                    else "diagnostic_only"
                ),
            }
            if company_type == "stable"
            else None
        ),
        "high_roe_review": {
            "threshold_percent": 40.0,
            "triggered": high_roe_triggered,
            "trigger_values": high_roe_values,
            "roe_reliability": (
                high_roe_review_status if high_roe_triggered else "not_triggered"
            ),
            "roa_evidence_complete": high_roe_roa_evidence_complete,
            "review_resolved": high_roe_review_resolved if high_roe_triggered else True,
            "required_checks": [
                "gross_buybacks_vs_net_share_count_change",
                "equity_shrinkage_or_negative_equity",
                "debt_financed_buybacks_and_interest_coverage",
                "equity_multiplier_vs_history",
                "roa_roic_and_free_cash_flow_per_share",
                "normalized_roe_under_normal_capital_structure",
            ],
            "pr_roe_role": (
                "diagnostic_only"
                if high_roe_triggered
                and (
                    not high_roe_review_resolved
                    or high_roe_review_status == "buyback_or_leverage_distorted"
                )
                else "usable_after_dupont_and_roa_review"
            ),
            "roa_is_primary_profitability_quality_check": high_roe_triggered,
            "roa_must_not_be_substituted_directly_into_pr_formula": True,
        },
        "roe_percent": {
            "historical_recent_weighted_average": history_recent_roe,
            "historical_neutral_anchor": history_neutral_roe,
            "cycle_phase_averages": cycle_phase_roe,
            "historical_lower_tail_weighted_average": history_lower_tail_roe,
            "current_weak_run_rate": current_weak_roe_value,
            "historical_conservative_anchor": history_conservative_roe,
            "historical_anchor_used": normalized_history_anchor_roe,
            "historical_anchor_used_for_normalized_neutral": neutral_history_anchor_roe,
            "forecast_bear_weighted_average": forecast_roe,
            "forecast_base_weighted_average": forecast_base_roe_average,
            "forecast_bull_weighted_average": forecast_bull_roe_average,
            "normalized_neutral": normalized_neutral_roe,
            "normalized_bull": normalized_bull_roe,
            "normalized_bear": normalized_bear_roe,
            "cyclical_60_40_sensitivity_non_executable": cycle_60_40_roe,
            "normalized": normalized_bear_roe,
        },
        "warnings": warnings,
    }

    if historical_roa is not None and forecast_bear_roa is not None:
        history_recent_roa = block_average(historical_roa, h_weights)
        cycle_phase_roa: dict[str, float] | None = None
        stable_three_year_roa = historical_roa[-3:] if company_type == "stable" else None
        stable_three_year_mean_roa = (
            sum(stable_three_year_roa) / 3 if stable_three_year_roa is not None else None
        )
        if company_type == "cyclical" and historical_phases is not None:
            history_neutral_roa, cycle_phase_roa = phase_balanced_average(
                historical_roa, historical_phases
            )
        elif company_type == "cyclical":
            history_neutral_roa = sum(historical_roa) / len(historical_roa)
        elif company_type == "stable":
            history_neutral_roa = stable_three_year_mean_roa
        else:
            history_neutral_roa = history_recent_roa
        history_lower_tail_roa = selected_average(
            historical_roa, history_relative_weights, weak_indices
        )
        current_weak_roa_value = historical_roa[-1] if current_weak_roa is None else current_weak_roa
        history_conservative_roa = (
            current_weak_roa_value if use_current_weak else history_lower_tail_roa
        )
        history_anchor_roa = (
            history_conservative_roa if historical_mode == "conservative" else history_recent_roa
        )
        normalized_history_anchor_roa = (
            historical_roa[cycle_five_year_low_index]
            if cycle_five_year_low_index is not None
            else history_conservative_roa if company_type == "stable" else history_anchor_roa
        )
        neutral_history_anchor_roa = (
            history_conservative_roa if company_type == "stable" else history_neutral_roa
        )
        forecast_roa = block_average(forecast_bear_roa, f_weights)
        forecast_base_roa_average = (
            block_average(forecast_base_roa, f_weights)
            if forecast_base_roa is not None
            else None
        )
        forecast_bull_roa_average = (
            block_average(forecast_bull_roa, f_weights)
            if forecast_bull_roa is not None
            else None
        )
        normalized_bear_roa = (
            h_share * normalized_history_anchor_roa + f_share * forecast_roa
            if blend_usable and (company_type != "cyclical" or cycle_five_year_low_index is not None)
            else None
        )
        cycle_60_40_roa = (
            0.60 * normalized_history_anchor_roa + 0.40 * forecast_roa
            if company_type == "cyclical" and cycle_five_year_low_index is not None and blend_usable
            else None
        )
        normalized_neutral_roa = (
            h_share * neutral_history_anchor_roa + f_share * forecast_base_roa_average
            if blend_usable and forecast_base_roa_average is not None
            else None
        )
        normalized_bull_roa = (
            h_share * neutral_history_anchor_roa + f_share * forecast_bull_roa_average
            if blend_usable and forecast_bull_roa_average is not None
            else None
        )
        result["roa_percent"] = {
            "historical_recent_weighted_average": history_recent_roa,
            "historical_neutral_anchor": history_neutral_roa,
            "cycle_phase_averages_same_roe_phases": cycle_phase_roa,
            "historical_lower_tail_weighted_average_same_roe_years": history_lower_tail_roa,
            "current_weak_run_rate": current_weak_roa_value,
            "historical_conservative_anchor": history_conservative_roa,
            "historical_anchor_used": normalized_history_anchor_roa,
            "historical_anchor_used_for_normalized_neutral": neutral_history_anchor_roa,
            "forecast_bear_weighted_average": forecast_roa,
            "forecast_base_weighted_average": forecast_base_roa_average,
            "forecast_bull_weighted_average": forecast_bull_roa_average,
            "normalized_neutral": normalized_neutral_roa,
            "normalized_bull": normalized_bull_roa,
            "normalized_bear": normalized_bear_roa,
            "cyclical_60_40_sensitivity_non_executable": cycle_60_40_roa,
            "normalized": normalized_bear_roa,
        }
        if blend_usable and normalized_bear_roa is not None and normalized_bear_roa > 0:
            leverage = normalized_bear_roe / normalized_bear_roa
            historical_ratios = [
                roe / roa
                for roe, roa in zip(historical_roe, historical_roa, strict=True)
                if roe > 0 and roa > 0
            ]
            historical_median = median(historical_ratios) if historical_ratios else None
            divergence = (
                abs(leverage / historical_median - 1.0) * 100.0
                if historical_median and historical_median > 0
                else None
            )
            result["leverage_check"] = {
                "normalized_roe_to_roa": leverage,
                "historical_median_roe_to_roa": historical_median,
                "divergence_percent": divergence,
                "review_required": divergence is not None and divergence > 25.0,
                "scenario": "bear",
            }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build bullish, neutral, and conservative normalized annual ROE/ROA. History: oldest to newest; forecast: nearest to farthest."
    )
    parser.add_argument("--company-type", choices=sorted(POLICIES), required=True)
    parser.add_argument("--historical-roe", type=parse_series, required=True)
    parser.add_argument("--forecast-bear-roe", type=parse_series, required=True)
    parser.add_argument("--forecast-base-roe", type=parse_series)
    parser.add_argument("--forecast-bull-roe", type=parse_series)
    parser.add_argument("--historical-roa", type=parse_series)
    parser.add_argument("--forecast-bear-roa", type=parse_series)
    parser.add_argument("--forecast-base-roa", type=parse_series)
    parser.add_argument("--forecast-bull-roa", type=parse_series)
    parser.add_argument("--current-ttm-roe", type=float)
    parser.add_argument("--current-ttm-roa", type=float)
    parser.add_argument("--current-weak-roe", type=float)
    parser.add_argument("--current-weak-roa", type=float)
    parser.add_argument(
        "--stable-years-comparable",
        choices=["confirmed", "not_confirmed", "unknown"],
        default="unknown",
        help="stable only; qualitative comparability of the latest three full fiscal years",
    )
    parser.add_argument(
        "--stability-policy",
        choices=["strict", "controlled_relaxation"],
        default="strict",
        help="stable only; relaxation requires a documented shortage of strict candidates",
    )
    parser.add_argument("--strict-candidate-count", type=int)
    parser.add_argument("--minimum-candidate-count", type=int, default=6)
    parser.add_argument(
        "--high-roe-review-status",
        choices=[
            "not_reviewed",
            "organic_high_return",
            "usable_with_caution",
            "buyback_or_leverage_distorted",
            "insufficient",
        ],
        default="not_reviewed",
        help="classification after reviewing ROE above 40%%; ROA/ROIC/FCF evidence is mandatory",
    )
    parser.add_argument(
        "--historical-phases",
        type=parse_labels,
        help="cyclical only; comma-separated trough,recovery,boom,downturn labels aligned to historical years",
    )
    parser.add_argument("--historical-mode", choices=["conservative", "weighted"], default="conservative")
    parser.add_argument("--forecast-confidence", choices=["high", "medium", "low"], default="high")
    parser.add_argument("--history-share", type=float)
    parser.add_argument("--forecast-share", type=float)
    parser.add_argument("--history-half-life", type=float)
    parser.add_argument("--forecast-half-life", type=float)
    args = parser.parse_args()
    try:
        result = calculate(
            company_type=args.company_type,
            historical_roe=args.historical_roe,
            forecast_bear_roe=args.forecast_bear_roe,
            forecast_base_roe=args.forecast_base_roe,
            forecast_bull_roe=args.forecast_bull_roe,
            historical_roa=args.historical_roa,
            forecast_bear_roa=args.forecast_bear_roa,
            forecast_base_roa=args.forecast_base_roa,
            forecast_bull_roa=args.forecast_bull_roa,
            current_ttm_roe=args.current_ttm_roe,
            current_ttm_roa=args.current_ttm_roa,
            current_weak_roe=args.current_weak_roe,
            current_weak_roa=args.current_weak_roa,
            stable_years_comparable=args.stable_years_comparable,
            stability_policy=args.stability_policy,
            strict_candidate_count=args.strict_candidate_count,
            minimum_candidate_count=args.minimum_candidate_count,
            high_roe_review_status=args.high_roe_review_status,
            historical_phases=args.historical_phases,
            historical_mode=args.historical_mode,
            forecast_confidence=args.forecast_confidence,
            history_share=args.history_share,
            forecast_share=args.forecast_share,
            history_half_life=args.history_half_life,
            forecast_half_life=args.forecast_half_life,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
