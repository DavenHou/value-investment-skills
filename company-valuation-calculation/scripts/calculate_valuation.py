#!/usr/bin/env python3
"""Deterministic calculator for the market-earnings-rate framework.

Use the explicit TTM inputs for the stable-company current snapshot. Generic
PE/ROE inputs remain available for normalized scenarios and backward
compatibility, but are labelled as non-TTM.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, timedelta
from typing import Any


def positive(name: str, value: float | None) -> float | None:
    if value is not None and (not math.isfinite(value) or value <= 0):
        raise ValueError(f"{name} must be greater than zero")
    return value


BUYBACK_WINDOW_YEARS = {
    "stable": 3,
    "financial": 3,
    "technology": 5,
    "growth": 5,
    "hybrid_platform": 5,
}

MAJOR_EARNINGS_DECLINE_THRESHOLD = -0.20
NEUTRAL_DIVIDEND_YIELD_THRESHOLD = 5.0
BULL_DIVIDEND_YIELD_THRESHOLD = 6.0


def major_earnings_decline_protection(
    current_quarter_core_profits: list[float] | None,
    prior_quarter_core_profits: list[float] | None,
) -> dict[str, Any]:
    """Check filed four-quarter deducting-nonrecurring net profit totals."""
    if current_quarter_core_profits is None or prior_quarter_core_profits is None:
        return {"yoy_percent": None, "status": "数据不足，无法判断", "triggered": False}
    if len(current_quarter_core_profits) != 4 or len(prior_quarter_core_profits) != 4:
        return {"yoy_percent": None, "status": "数据不足，无法判断", "triggered": False}
    if not all(isinstance(value, (int, float)) and math.isfinite(value)
               for value in current_quarter_core_profits + prior_quarter_core_profits):
        return {"yoy_percent": None, "status": "数据不足，无法判断", "triggered": False}
    current_ttm_core_profit = sum(current_quarter_core_profits)
    prior_ttm_core_profit = sum(prior_quarter_core_profits)
    if prior_ttm_core_profit <= 0:
        return {"yoy_percent": None, "status": "基期异常，无法使用正常同比判断", "triggered": False}
    yoy = (current_ttm_core_profit - prior_ttm_core_profit) / abs(prior_ttm_core_profit)
    triggered = yoy <= MAJOR_EARNINGS_DECLINE_THRESHOLD
    return {
        "current_ttm_core_profit": current_ttm_core_profit,
        "prior_ttm_core_profit": prior_ttm_core_profit,
        "yoy_percent": yoy * 100,
        "status": "已触发" if triggered else "未触发",
        "triggered": triggered,
        "note": (f"TTM扣非净利润同比下降≥{-MAJOR_EARNINGS_DECLINE_THRESHOLD:.0%}，"
                 "估值切换至悲观预测。") if triggered else None,
    }


def trailing_twelve_month_eps(
    *,
    latest_full_year_diluted_eps: float,
    prior_comparable_ytd_diluted_eps: float,
    current_ytd_diluted_eps: float,
) -> float:
    """Build actual TTM EPS from filed periods; forecasts are not valid inputs."""
    values = (
        latest_full_year_diluted_eps,
        prior_comparable_ytd_diluted_eps,
        current_ytd_diluted_eps,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("TTM EPS inputs must be finite")
    result = latest_full_year_diluted_eps - prior_comparable_ytd_diluted_eps + current_ytd_diluted_eps
    if result <= 0:
        raise ValueError("TTM diluted EPS must be greater than zero")
    return result


def _iso_date(name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be YYYY-MM-DD") from exc


def _rolling_window_start(cutoff: date, years: int) -> date:
    try:
        anchor = cutoff.replace(year=cutoff.year - years)
    except ValueError:  # February 29 -> February 28 in a non-leap anchor year.
        anchor = cutoff.replace(year=cutoff.year - years, day=28)
    return anchor + timedelta(days=1)


def recomputed_roe(
    *,
    ttm_net_income: float,
    ending_equity: float,
    cumulative_buyback: float,
    company_type: str,
    financial_cutoff_date: str,
    buyback_window_start_date: str,
    buyback_window_end_date: str,
) -> dict[str, Any]:
    """Rebuild ROE on one cutoff-locked normal-capital basis."""
    if company_type == "cyclical":
        return {"applies": False, "note": "周期股不适用正常资本结构ROE重算"}
    years = BUYBACK_WINDOW_YEARS.get(company_type)
    if years is None:
        raise ValueError(f"unsupported company_type: {company_type}")
    cutoff = _iso_date("financial_cutoff_date", financial_cutoff_date)
    window_start = _iso_date("buyback_window_start_date", buyback_window_start_date)
    window_end = _iso_date("buyback_window_end_date", buyback_window_end_date)
    if window_end != cutoff:
        raise ValueError("buyback window end must equal financial cutoff date")
    expected_start = _rolling_window_start(cutoff, years)
    if window_start != expected_start:
        raise ValueError(
            f"buyback window must be the exact rolling {years}-year window "
            f"{expected_start.isoformat()}..{cutoff.isoformat()}"
        )
    positive("ttm_net_income", ttm_net_income)
    if not math.isfinite(ending_equity) or not math.isfinite(cumulative_buyback):
        raise ValueError("equity and buyback inputs must be finite")
    if cumulative_buyback < 0:
        raise ValueError("cumulative_buyback must be non-negative")
    equity_base = ending_equity + cumulative_buyback
    if equity_base <= 0:
        raise ValueError("recomputed equity base must be positive")
    roe = ttm_net_income / equity_base * 100.0
    return {
        "applies": True,
        "policy_version": "cutoff-locked-normal-capital-roe-v1",
        "financial_cutoff_date": cutoff.isoformat(),
        "buyback_window_start_date": window_start.isoformat(),
        "buyback_window_end_date": window_end.isoformat(),
        "window_years": years,
        "ttm_net_income": ttm_net_income,
        "ending_equity": ending_equity,
        "cumulative_buyback": cumulative_buyback,
        "equity_base": equity_base,
        "recomputed_roe_percent": roe,
        "implied_pb_at_pr_one": roe**2 / 100.0,
        "distortion_explained": roe**2 / 100.0 <= 8.0,
        "calculation_basis_id": (
            f"{cutoff.isoformat()}|{window_start.isoformat()}..{window_end.isoformat()}"
            f"|ni={ttm_net_income}|equity={ending_equity}|buyback={cumulative_buyback}"
        ),
    }


def market_coefficient(
    *,
    listing_market: str | None,
    dividend_yield_percent: float | None,
    tax_percent: float | None = None,
) -> float:
    """Return the shared buy/sell market coefficient ``c``."""
    if dividend_yield_percent is not None and (
        not math.isfinite(dividend_yield_percent) or dividend_yield_percent < 0
    ):
        raise ValueError("dividend_yield_percent must be finite and non-negative")
    if listing_market != "hk":
        return 1.0
    tax_rate = (20.0 if tax_percent is None else tax_percent) / 100.0
    if dividend_yield_percent is None:
        return 0.90
    coefficient = 0.90 * (1.0 - dividend_yield_percent * tax_rate / 10.0)
    if coefficient <= 0:
        raise ValueError("market coefficient must be greater than zero")
    return round(coefficient, 4)


def select_decision_roe(
    *,
    company_type: str,
    normalized_roe_percent: float | None,
    current_ttm_roe_percent: float | None,
    historical_roe_percent: float | None = None,
    pessimistic_anchor_roe_percent: float | None = None,
    normal_capital_roe_percent: float | None = None,
    roic_percent: float | None = None,
    buyback_distortion: bool = False,
    forecast_tier: str = "bear",
) -> dict[str, Any] | None:
    """One action-line ROE for every company type.

    Cyclicals consume the formal five-year-low plus bear-forecast handoff.
    A weaker current TTM can still tighten the denominator.
    """
    if normalized_roe_percent is None:
        return None
    positive("normalized_roe_percent", normalized_roe_percent)
    positive("historical_roe_percent", historical_roe_percent)
    if company_type == "cyclical":
        if forecast_tier == "unselected":
            return None
        if forecast_tier == "bear" and pessimistic_anchor_roe_percent is None:
            return None
        if forecast_tier == "bear":
            positive("pessimistic_anchor_roe_percent", pessimistic_anchor_roe_percent)
            candidates = {"five_year_low_plus_bear_forecast": pessimistic_anchor_roe_percent}
        else:
            candidates = {f"{forecast_tier}_normalized_forecast": normalized_roe_percent}
        if current_ttm_roe_percent is not None:
            positive("current_ttm_roe_percent", current_ttm_roe_percent)
            candidates["ttm"] = current_ttm_roe_percent
        out = _finish_roe(
            decision_roe=min(candidates.values()),
            candidates=candidates,
            normalized_roe_percent=normalized_roe_percent,
            current_ttm_roe_percent=current_ttm_roe_percent,
            gap_percent=None,
            guard_applicable=False,
            pessimistic_anchor_roe_percent=None,  # 已作为周期股第一候选
            normal_capital_roe_percent=None,
            roic_percent=roic_percent,
            buyback_distortion=buyback_distortion,
        )
        out["pessimistic_anchor_applies"] = forecast_tier == "bear"
        out["cycle_anchor_candidates"] = out["anchor_candidates"]
        return out
    if current_ttm_roe_percent is None:
        candidates = {"normalized": normalized_roe_percent}
        if historical_roe_percent is not None:
            candidates["historical"] = historical_roe_percent
        return _finish_roe(
            decision_roe=min(candidates.values()),
            candidates=candidates,
            normalized_roe_percent=normalized_roe_percent,
            current_ttm_roe_percent=None,
            gap_percent=None,
            guard_applicable=True,
            pessimistic_anchor_roe_percent=pessimistic_anchor_roe_percent,
            normal_capital_roe_percent=normal_capital_roe_percent,
            roic_percent=roic_percent,
            buyback_distortion=buyback_distortion,
        )
    positive("current_ttm_roe_percent", current_ttm_roe_percent)
    gap = (normalized_roe_percent - current_ttm_roe_percent) / normalized_roe_percent
    candidates = {"normalized": normalized_roe_percent, "ttm": current_ttm_roe_percent}
    if historical_roe_percent is not None:
        candidates["historical"] = historical_roe_percent
    decision_roe = min(candidates.values())
    return _finish_roe(
        decision_roe=decision_roe,
        candidates=candidates,
        normalized_roe_percent=normalized_roe_percent,
        current_ttm_roe_percent=current_ttm_roe_percent,
        gap_percent=gap * 100.0,
        guard_applicable=True,
        pessimistic_anchor_roe_percent=pessimistic_anchor_roe_percent,
        normal_capital_roe_percent=normal_capital_roe_percent,
        roic_percent=roic_percent,
        buyback_distortion=buyback_distortion,
    )


def _finish_roe(
    *,
    decision_roe: float,
    candidates: dict[str, float],
    normalized_roe_percent: float,
    current_ttm_roe_percent: float | None,
    gap_percent: float | None,
    guard_applicable: bool,
    pessimistic_anchor_roe_percent: float | None,
    normal_capital_roe_percent: float | None,
    roic_percent: float | None,
    buyback_distortion: bool,
) -> dict[str, Any]:
    """收尾：悲观锚与可用 ROIC 一起取低。"""
    candidates = dict(candidates)
    if normal_capital_roe_percent is not None:
        positive("normal_capital_roe_percent", normal_capital_roe_percent)
        candidates["normal_capital"] = normal_capital_roe_percent
        decision_roe = min(decision_roe, normal_capital_roe_percent)
    if pessimistic_anchor_roe_percent is not None:
        positive("pessimistic_anchor_roe_percent", pessimistic_anchor_roe_percent)
        candidates["pessimistic"] = pessimistic_anchor_roe_percent
        decision_roe = min(decision_roe, pessimistic_anchor_roe_percent)
    basis = "roe"
    if buyback_distortion:
        if roic_percent is None:
            return {
                "decision_roe_percent": None,
                "decision_roe_status": "insufficient",
                "missing_inputs": ["roic_percent"],
                "normalized_roe_percent": normalized_roe_percent,
                "buyback_distortion": True,
                "note": "确认财技失真但未提供 ROIC，无法出价",
            }
        positive("roic_percent", roic_percent)
        # 回购不改变投入资本回报，ROIC 是未被净资产收缩放大的那个数。
        candidates["roic"] = roic_percent
        decision_roe = min(decision_roe, roic_percent)
        basis = "roic"
    chosen = min(candidates, key=lambda k: candidates[k])
    return {
        "decision_roe_percent": decision_roe,
        "decision_roe_status": "valid",
        "decision_roe_basis": basis,
        "conservative_anchor_used": chosen,
        "anchor_candidates": candidates,
        "normalized_roe_percent": normalized_roe_percent,
        "current_ttm_roe_percent": current_ttm_roe_percent,
        "no_mean_reversion_guard": (
            current_ttm_roe_percent is not None
            and decision_roe == current_ttm_roe_percent
            and current_ttm_roe_percent < normalized_roe_percent
        ),
        "guard_applicable": guard_applicable,
        "gap_percent": gap_percent,
        "material_gap_review_required": gap_percent is not None and gap_percent > 20.0,
        "buyback_distortion": buyback_distortion,
        "normal_capital_roe_percent": normal_capital_roe_percent,
        "forecast_enters_denominator_tighten_only": pessimistic_anchor_roe_percent is not None,
    }



def blended_pessimistic_anchor(
    history_roe_percents: list[float] | None,
    bear_forecast_roe_percents: list[float] | None,
    current_weak_roe_percent: float | None = None,
) -> dict[str, Any] | None:
    """Backward-compatible adapter to the formal normalized-profitability rule."""
    hist = list(history_roe_percents or [])
    bear = list(bear_forecast_roe_percents or [])
    if not hist or not bear:
        return {
            "pessimistic_anchor_roe_percent": None,
            "status": "insufficient",
            "missing": ([] if hist else ["history_roe_percents"])
            + ([] if bear else ["bear_forecast_roe_percents"]),
        }
    for v in hist + bear:
        positive("anchor_roe_percent", v)
    if len(hist) != 3 or len(bear) != 3:
        return {
            "pessimistic_anchor_roe_percent": None,
            "status": "insufficient",
            "missing": ["three_comparable_history_years_and_three_bear_forecast_years"],
        }
    from calculate_normalized_profitability import calculate as normalize

    normalized = normalize(
        company_type="stable",
        historical_roe=hist,
        forecast_bear_roe=bear,
        current_weak_roe=current_weak_roe_percent,
        stable_years_comparable="confirmed",
    )
    return {
        "pessimistic_anchor_roe_percent": normalized["roe_percent"]["normalized_bear"],
        "status": "valid",
        "history_years": len(hist),
        "bear_forecast_years": len(bear),
        "basis": "formal_normalized_bear_roe_handoff",
        "applies_to": "non_cyclical_only",
    }



PB_CEILING = 8.0


def pb_gate(pb: float | None) -> dict[str, Any]:
    """8PB 建仓禁令。就一行：PB 超过 8 不建仓，没超就往下走。"""
    if pb is None:
        return {"status": "pb_unknown", "pb": None, "action": "no_new_position"}
    if pb > PB_CEILING:
        return {"status": "blocked", "pb": pb, "action": "no_new_position"}
    return {"status": "clear", "pb": pb, "action": "proceed"}


def buy_tier(raw_pr: float | None, normalized_position: float | None) -> dict[str, Any]:
    """买入档：原始决策PR 与 归一化估值位置**两个都算，取更严的那个**。

    原始PR 守的是绝对便宜（PR 0.3 在哪个市场都是 0.3，捡烟蒂的底线）；
    归一化守的是相对自身历史的位置（一只历史峰值只有 0.59 的股票，
    原始 0.46 其实已经在它自己天花板的 78%）。任一条不达标就不开档，
    与全套"保守优先"一致。
    """
    tiers = [(0.30, "深度价值", "20%-35%"), (0.40, "主要加仓", "10%-15%"),
             (0.50, "首仓", "4%-6%")]
    if raw_pr is None:
        return {"tier": None, "status": "insufficient", "missing": ["decision_pr"]}
    readings = {"raw_pr": raw_pr}
    if normalized_position is not None:
        readings["normalized_position"] = normalized_position
    governing = max(readings.values())          # 取更严＝取更贵的那个读数
    for line, name, budget in tiers:
        if governing <= line:
            return {
                "tier": name, "tier_line": line, "cumulative_budget": budget,
                "status": "eligible", "readings": readings,
                "governing_reading": governing,
                "governed_by": max(readings, key=lambda k: readings[k]),
            }
    return {
        "tier": None, "status": "above_all_tiers", "readings": readings,
        "governing_reading": governing,
        "governed_by": max(readings, key=lambda k: readings[k]),
    }


def classify_cycle_anchor_conflict(
    *,
    pb: float | None,
    current_run_rate_roe_percent: float | None,
    decision_roe_percent: float | None,
    bear_roe_percent: float | None,
    market_pr_factor: float,
    effective_high_pr: float | None = None,
    normalized_roe_percent: float | None = None,
) -> dict[str, Any] | None:
    """周期股双锚割裂闸门。

    决策ROE 现在是保守优先（取最低锚），所以冲突判定必须显式并列
    **跨周期归一化锚** 与 **当前运行率锚**，否则两者会塌缩成同一个数。
    触发判定走归一化刻度：高锚 >= 0.80（已进兑现区）而低锚 <= 0.50
    （仍在首仓区）即为 regime_split —— 原始资料中远海控 A 0.977／0.535
    正是这一形态，作者的动作是减仓一半。
    """
    values = {
        "current_run_rate": current_run_rate_roe_percent,
        "normalized": normalized_roe_percent
        if normalized_roe_percent is not None
        else decision_roe_percent,
        "bear": bear_roe_percent,
    }
    if all(value is None for value in values.values()):
        return None

    missing = (["pb"] if pb is None else []) + [
        name for name, value in values.items() if value is None
    ]
    if missing:
        return {
            "status": "insufficient",
            "missing_inputs": missing,
            "action_effect": "no_new_position",
        }

    assert pb is not None
    for name, value in values.items():
        positive(f"cycle_{name}_roe_percent", value)
    pr_by_anchor = {
        name: 100.0 * pb / float(value) ** 2
        for name, value in values.items()
    }
    e = effective_high_pr or market_pr_factor
    normalized_by_anchor = {name: pr / e for name, pr in pr_by_anchor.items()}
    lowest = min(pr_by_anchor.values())
    highest = max(pr_by_anchor.values())
    divergence = (highest - lowest) / lowest
    realize_line = 0.80          # 归一化：开始兑现
    first_entry_normalized = 0.50
    first_entry_pr = first_entry_normalized * e

    if (max(normalized_by_anchor.values()) >= realize_line
            and min(normalized_by_anchor.values()) <= first_entry_normalized):
        status = "regime_split"
        action_effect = "pause_new_positions_and_halve_existing"
    elif divergence > 0.50:
        status = "material_gap"
        action_effect = "information_risk_initial_position_cap_4_percent"
    else:
        status = "aligned"
        action_effect = "normal"

    return {
        "status": status,
        "decision_pr": pr_by_anchor["current_run_rate"]
        if current_run_rate_roe_percent is not None
        else pr_by_anchor["normalized"],
        "pr_by_anchor": pr_by_anchor,
        "normalized_by_anchor": normalized_by_anchor,
        "divergence_percent": divergence * 100.0,
        "first_entry_pr": first_entry_pr,
        "first_entry_normalized": first_entry_normalized,
        "realize_line_normalized": realize_line,
        "effective_high_pr": e,
        "action_effect": action_effect,
        "default_half_sale_on_regime_split": status == "regime_split",
        "fixed_half_sale_rule": False,
    }


def calculate(
    *,
    roe_percent: float | None = None,
    pe: float | None = None,
    roe_ttm_percent: float | None = None,
    pe_ttm: float | None = None,
    pb: float | None = None,
    payout_percent: float | None = None,
    dividend_yield_percent: float | None = None,
    current_price: float | None = None,
    targets: list[float] | None = None,
    base_high_pr: float | None = None,
    tax_percent: float | None = None,
    listing_market: str | None = None,
    company_type: str = "cyclical",
    normalized_roe_percent: float | None = None,
    historical_roe_percent: float | None = None,
    cycle_current_run_rate_roe_percent: float | None = None,
    cycle_bear_roe_percent: float | None = None,
    historical_peak_pr: float | None = None,
    historical_peak_asof_forecast_verified: bool = False,
    pessimistic_anchor_roe_percent: float | None = None,
    optimistic_normalized_roe_percent: float | None = None,
    normal_capital_roe_percent: float | None = None,
    roic_percent: float | None = None,
    buyback_distortion: bool = False,
    current_quarter_core_profits: list[float] | None = None,
    prior_quarter_core_profits: list[float] | None = None,
) -> dict[str, Any]:
    if roe_percent is not None and roe_ttm_percent is not None:
        raise ValueError("provide only one of roe_percent or roe_ttm_percent")
    if pe is not None and pe_ttm is not None:
        raise ValueError("provide only one of pe or pe_ttm")
    if (roe_ttm_percent is None) != (pe_ttm is None):
        raise ValueError("pe_ttm and roe_ttm_percent must be provided together")

    effective_roe = roe_ttm_percent if roe_ttm_percent is not None else roe_percent
    effective_pe = pe_ttm if pe_ttm is not None else pe
    if effective_roe is None:
        raise ValueError("provide roe_ttm_percent for a TTM snapshot or roe_percent for a scenario")

    positive("effective_roe_percent", effective_roe)
    positive("effective_pe", effective_pe)
    positive("pb", pb)
    positive("payout_percent", payout_percent)
    positive("current_price", current_price)
    if effective_pe is None and pb is None:
        raise ValueError("provide at least one of pe or pb")
    if tax_percent is not None and not 0 <= tax_percent < 100:
        raise ValueError("tax_percent must be in [0, 100)")

    base_targets = targets or [0.3, 0.4, 0.5, 0.8, 0.9, 1.0]
    for target in base_targets:
        positive("target", target)
    if listing_market not in {None, "us", "a", "hk"}:
        raise ValueError("listing_market must be one of: us, a, hk")
    market_pr_factor = market_coefficient(
        listing_market=listing_market,
        dividend_yield_percent=dividend_yield_percent,
        tax_percent=tax_percent,
    )

    if company_type not in {"cyclical", "stable", "technology", "financial"}:
        raise ValueError("invalid company_type")

    decline_protection = major_earnings_decline_protection(
        current_quarter_core_profits, prior_quarter_core_profits
    )
    if dividend_yield_percent is None and pessimistic_anchor_roe_percent is None and not decline_protection["triggered"]:
        forecast_tier = "unselected"
    elif decline_protection["triggered"] or dividend_yield_percent is None or dividend_yield_percent <= NEUTRAL_DIVIDEND_YIELD_THRESHOLD:
        forecast_tier = "bear"
    elif dividend_yield_percent > BULL_DIVIDEND_YIELD_THRESHOLD:
        forecast_tier = "bull"
    else:
        forecast_tier = "neutral"
    selected_normalized_roe = {
        "bear": pessimistic_anchor_roe_percent,
        "neutral": normalized_roe_percent,
        "bull": optimistic_normalized_roe_percent,
        "unselected": normalized_roe_percent,
    }[forecast_tier]
    selected_pessimistic_roe = (
        pessimistic_anchor_roe_percent if forecast_tier == "bear" else None
    )

    roe_selection = select_decision_roe(
        company_type=company_type,
        normalized_roe_percent=selected_normalized_roe,
        historical_roe_percent=historical_roe_percent,
        current_ttm_roe_percent=(
            roe_ttm_percent
            if roe_ttm_percent is not None
            else cycle_current_run_rate_roe_percent
            if company_type == "cyclical"
            else None
        ),
        pessimistic_anchor_roe_percent=selected_pessimistic_roe,
        normal_capital_roe_percent=normal_capital_roe_percent,
        roic_percent=roic_percent,
        buyback_distortion=buyback_distortion,
        forecast_tier=forecast_tier,
    )
    decision_roe = roe_selection["decision_roe_percent"] if roe_selection else None

    # 高估线 E = min(市场股息税分档, 个股历史峰值PR)。
    # 8PB 不再进入 E —— 它是一条独立的建仓禁令（PB>8 不建仓），把它换算成
    # PR 刻度会把高ROE股的整条卖出梯压扁，并制造"原始很便宜／归一化不便宜"的
    # 自相矛盾读数。个股历史峰值才是卖点的真实天花板：历史上从未到过 PR 1.0
    # 的股票，用 1.0 当清仓线等于永不卖出。
    e_market = base_high_pr if base_high_pr is not None else market_pr_factor
    peak_usable = historical_peak_pr is not None and (
        company_type != "cyclical" or historical_peak_asof_forecast_verified
    )
    if historical_peak_pr is not None:
        positive("historical_peak_pr", historical_peak_pr)
    if peak_usable:
        effective_high_pr = min(e_market, historical_peak_pr)
        binding = "historical_peak" if historical_peak_pr < e_market else "market_dividend_tax"
        peak_status = "available"
    else:
        effective_high_pr = e_market
        binding = "market_dividend_tax"
        peak_status = (
            "unverified_asof_forecast_fallback_to_market_line"
            if historical_peak_pr is not None
            else "insufficient_fallback_to_market_line"
        )
    high_pr_line = {
        "e_market": e_market,
        "historical_peak_pr": historical_peak_pr,
        "historical_peak_status": peak_status,
        "historical_peak_excludes_forecast": company_type != "cyclical",
        "historical_peak_asof_forecast_verified": historical_peak_asof_forecast_verified,
        "effective_high_pr": effective_high_pr,
        "binding_constraint": binding,
        "eight_pb_is_a_pb_gate_not_a_pr_scale": True,
    }

    # 买入和卖出共用归一化刻度：基础线乘 E 还原成原始 PR。
    # E 已包含市场系数 c，并在个股历史峰值更低时取严。
    buy_target_bases = [t for t in base_targets if t <= 0.5]
    buy_targets = {
        str(t): round(t * effective_high_pr, 10)
        for t in buy_target_bases
    }
    sell_targets = {
        f"norm_{t}": round(t * effective_high_pr, 10)
        for t in base_targets
        if t > 0.5
    }
    targets = list(buy_targets.values()) + list(sell_targets.values())
    target_scale = {
        **{f"buy_norm_{t}": f"x_E({effective_high_pr:.4f})={buy_targets[str(t)]:.4f}"
           for t in buy_target_bases},
        **{k: f"sell_normalized_{k.split('_')[1]}_x_E({effective_high_pr:.4f})"
           for k in sell_targets},
    }

    cycle_anchor_conflict = classify_cycle_anchor_conflict(
        pb=pb,
        current_run_rate_roe_percent=cycle_current_run_rate_roe_percent,
        decision_roe_percent=decision_roe,
        bear_roe_percent=(
            cycle_bear_roe_percent
            if cycle_bear_roe_percent is not None
            else pessimistic_anchor_roe_percent if company_type == "cyclical" else None
        ),
        market_pr_factor=market_pr_factor,
        effective_high_pr=effective_high_pr,
        normalized_roe_percent=normalized_roe_percent,
    )


    decision: dict[str, Any] | None = None
    # 公式选择：PB 形（第二公式）是周期股专用；非周期用 PE 形。
    if company_type == "cyclical":
        decision_basis = "cyclical_pb_form"
        decision_input_ok = pb is not None and decision_roe is not None
        decision_pr_value = 100.0 * pb / decision_roe**2 if decision_input_ok else None
        missing_for_decision = ["pb"] if pb is None else []
    else:
        decision_basis = "non_cyclical_pe_form"
        decision_input_ok = effective_pe is not None and decision_roe is not None
        decision_pr_value = effective_pe / decision_roe if decision_input_ok else None
        missing_for_decision = ["pe_ttm"] if effective_pe is None else []
    if decision_input_ok and decision_roe is not None:
        decision_pr = decision_pr_value
        decision = {
            "policy_version": "single-decision-pr-v2",
            "company_type": company_type,
            "forecast_tier": forecast_tier,
            "forecast_roe_percent": selected_normalized_roe,
            **roe_selection,
            "decision_pr": decision_pr,
            "decision_pr_basis": decision_basis,
            "decision_pr_formula": (
                "100 × 同期PB ÷ 执行ROE²（周期股专用第二公式）"
                if company_type == "cyclical"
                else "PE_TTM ÷ 执行ROE（非周期）"
            ),
            "high_pr_line": high_pr_line,
            "normalized_position": decision_pr / effective_high_pr,
            "normalized_position_note": "决策PR ÷ E；1.0 永远是高估线，仅用于显示与横向比较",
            "pb_gate": pb_gate(pb),
            "buy_tier": buy_tier(decision_pr, decision_pr / effective_high_pr),
            "no_new_position_over_8pb": (pb is not None and pb > 8.0),
            "decision_pr_status": "valid",
            "forecast_in_action_line": company_type == "cyclical",
            "recomputable_at_historical_peaks": (
                company_type != "cyclical" or historical_peak_asof_forecast_verified
            ),
            "second_action_pr_present": False,
            "target_pb": {
                str(target): target * decision_roe**2 / 100.0
                for target in targets
            } if company_type == "cyclical" else None,
        }
        if current_price is not None:
            # 买入档与卖出档分开记名：卖出档 ×E 之后可能与某个买入档撞成同一个键
            decision["target_price"] = {
                "buy": {label: current_price * target / decision_pr
                        for label, target in buy_targets.items()},
                "sell": {k: current_price * v / decision_pr
                         for k, v in sell_targets.items()},
            }
    elif decision_roe is not None:
        decision = {
            "policy_version": "single-decision-pr-v2",
            "decision_pr": None,
            "decision_pr_status": "insufficient",
            "missing_inputs": missing_for_decision or ["pb"],
        }
    elif company_type == "cyclical":
        decision = {
            "policy_version": "single-decision-pr-v2",
            "decision_pr": None,
            "decision_pr_status": "insufficient",
            "missing_inputs": [f"formal_{'bear' if forecast_tier == 'unselected' else forecast_tier}_roe_handoff"],
        }

    base: dict[str, float] = {}
    if effective_pe is not None:
        pe_key = "from_pe_ttm" if pe_ttm is not None else "from_pe"
        base[pe_key] = effective_pe / effective_roe
    if pb is not None:
        base["from_pb"] = 100.0 * pb / (effective_roe**2)
    if effective_pe is not None and pb is not None:
        base["from_pe_pb_identity"] = effective_pe**2 / (100.0 * pb)
        base["implied_roe_percent_from_pe_pb"] = 100.0 * pb / effective_pe

    n = None
    if dividend_yield_percent is not None:
        n = 1.0
        if dividend_yield_percent > 4.0 and payout_percent is not None:
            n = min(2.0, max(1.0, 50.0 / payout_percent))

    adjusted = None
    if n is not None:
        adjusted = {
            key: value * n
            for key, value in base.items()
            if key.startswith("from_")
        }

    fair_multiples = {
        "pe_at_pr_1": effective_roe,
        "pb_at_pr_1": effective_roe**2 / 100.0,
    }
    if n is not None:
        fair_multiples.update(
            {
                "pe_at_adjusted_pr_1": effective_roe / n,
                "pb_at_adjusted_pr_1": effective_roe**2 / (100.0 * n),
            }
        )

    target_map: dict[str, Any] = {}
    for target in targets:
        entry: dict[str, Any] = {
            "target_pe_base": target * effective_roe,
            "target_pb_base": target * effective_roe**2 / 100.0,
        }
        if n is not None:
            entry["target_pe_adjusted"] = target * effective_roe / n
            entry["target_pb_adjusted"] = target * effective_roe**2 / (100.0 * n)
        if current_price is not None:
            entry["prices_from_base_pr"] = {
                key: current_price * target / value
                for key, value in base.items()
                if key.startswith("from_")
            }
            if adjusted is not None:
                entry["prices_from_adjusted_pr"] = {
                    key: current_price * target / value
                    for key, value in adjusted.items()
                }
        target_map[str(target)] = entry

    return {
        "major_earnings_decline_protection": decline_protection,
        "forecast_tier_selection": {
            "dividend_yield_percent": dividend_yield_percent,
            "tier": forecast_tier,
            "selected_roe_percent": selected_normalized_roe,
            "status": ("unselected" if forecast_tier == "unselected" else
                       "valid" if selected_normalized_roe is not None else "insufficient"),
            "overridden_by_major_decline": decline_protection["triggered"],
        },
        "inputs": {
            "roe_percent": roe_percent,
            "roe_ttm_percent": roe_ttm_percent,
            "pe": pe,
            "pe_ttm": pe_ttm,
            "pb": pb,
            "payout_percent": payout_percent,
            "dividend_yield_percent": dividend_yield_percent,
            "current_price": current_price,
            "base_targets": base_targets,
            "resolved_targets": targets,
            "buy_targets_normalized_to_raw": buy_targets,
            "sell_targets_normalized_to_raw": sell_targets,
            "target_scale": target_scale,
            "base_high_pr": base_high_pr,
            "tax_percent": tax_percent,
            "listing_market": listing_market,
            "market_pr_factor": market_pr_factor,
            "cycle_current_run_rate_roe_percent": cycle_current_run_rate_roe_percent,
            "company_type": company_type,
            "normalized_roe_percent": normalized_roe_percent,
            "historical_roe_percent": historical_roe_percent,
            "optimistic_normalized_roe_percent": optimistic_normalized_roe_percent,
            "current_quarter_core_profits": current_quarter_core_profits,
            "prior_quarter_core_profits": prior_quarter_core_profits,
            "cycle_bear_roe_percent": cycle_bear_roe_percent,
            "historical_peak_asof_forecast_verified": historical_peak_asof_forecast_verified,
            "normal_capital_roe_percent": normal_capital_roe_percent,
        },
        "calculation_basis": "aligned_ttm" if pe_ttm is not None else "normalized_or_unspecified_period",
        "base_pr": base,
        "payout_adjustment_n": n,
        "adjusted_pr": adjusted,
        "fair_multiples": fair_multiples,
        "high_pr_line": high_pr_line,
        "decision": decision,
        "cycle_anchor_conflict": cycle_anchor_conflict,
        "target_map": target_map,
    }


def parse_targets(raw: str) -> list[float]:
    try:
        return [float(item.strip()) for item in raw.split(",") if item.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("targets must be comma-separated numbers") from exc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate PR metrics. Enter ROE as percentage points: 31% -> 31."
    )
    roe_group = parser.add_mutually_exclusive_group(required=True)
    roe_group.add_argument("--roe-ttm-percent", type=float)
    roe_group.add_argument("--roe-percent", type=float)
    pe_group = parser.add_mutually_exclusive_group()
    pe_group.add_argument("--pe-ttm", type=float)
    pe_group.add_argument("--pe", type=float)
    parser.add_argument("--pb", type=float)
    parser.add_argument("--payout-percent", type=float)
    parser.add_argument("--dividend-yield-percent", type=float)
    parser.add_argument("--current-price", type=float)
    parser.add_argument(
        "--targets", type=parse_targets, default=parse_targets("0.3,0.4,0.5,0.8,0.9,1.0")
    )
    parser.add_argument("--base-high-pr", type=float)
    parser.add_argument("--tax-percent", type=float)
    parser.add_argument("--listing-market", choices=("us", "a", "hk"))
    parser.add_argument("--cycle-current-run-rate-roe-percent", type=float)
    parser.add_argument("--company-type", default="cyclical",
                        choices=["cyclical", "stable", "technology", "financial"])
    parser.add_argument("--normalized-roe-percent", type=float,
                        help="neutral ROE handoff; cyclical decision additionally requires formal bearish ROE")
    parser.add_argument("--historical-roe-percent", type=float,
                        help="noncyclical comparable historical ROE anchor")
    parser.add_argument("--cycle-bear-roe-percent", type=float)
    parser.add_argument("--pessimistic-anchor-roe-percent", type=float,
                        help="formal normalized bear ROE handoff; required for cyclical decision PR")
    parser.add_argument("--optimistic-normalized-roe-percent", type=float,
                        help="formal normalized bull ROE handoff used when dividend yield exceeds 6 percent")
    parser.add_argument("--historical-peak-pr", type=float)
    parser.add_argument("--historical-peak-asof-forecast-verified", action="store_true")
    parser.add_argument("--normal-capital-roe-percent", type=float)
    parser.add_argument("--current-quarter-core-profits", type=parse_targets,
                        help="latest four quarterly deducting-nonrecurring net profits, comma separated")
    parser.add_argument("--prior-quarter-core-profits", type=parse_targets,
                        help="matching four quarters one year earlier, comma separated")
    args = parser.parse_args()

    try:
        result = calculate(
            roe_percent=args.roe_percent,
            pe=args.pe,
            roe_ttm_percent=args.roe_ttm_percent,
            pe_ttm=args.pe_ttm,
            pb=args.pb,
            payout_percent=args.payout_percent,
            dividend_yield_percent=args.dividend_yield_percent,
            current_price=args.current_price,
            targets=args.targets,
            base_high_pr=args.base_high_pr,
            tax_percent=args.tax_percent,
            listing_market=args.listing_market,
            cycle_current_run_rate_roe_percent=args.cycle_current_run_rate_roe_percent,
            company_type=args.company_type,
            normalized_roe_percent=args.normalized_roe_percent,
            historical_roe_percent=args.historical_roe_percent,
            cycle_bear_roe_percent=args.cycle_bear_roe_percent,
            pessimistic_anchor_roe_percent=args.pessimistic_anchor_roe_percent,
            optimistic_normalized_roe_percent=args.optimistic_normalized_roe_percent,
            historical_peak_pr=args.historical_peak_pr,
            historical_peak_asof_forecast_verified=args.historical_peak_asof_forecast_verified,
            normal_capital_roe_percent=args.normal_capital_roe_percent,
            current_quarter_core_profits=args.current_quarter_core_profits,
            prior_quarter_core_profits=args.prior_quarter_core_profits,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def peak_rebuild_needed(
    *,
    max_historical_pe: float | None,
    min_plausible_decision_roe_percent: float | None,
    e_market: float = 1.0,
) -> dict[str, Any]:
    """逐峰值日重建之前的粗筛：先判断这只股票有没有可能把 E 压低。

    `E = min(E_market, 历史峰值PR)`，所以只有 **峰值PR < E_market** 时重建
    才会改变任何结果。峰值PR 的下界可以两秒钟估出来：

        峰值PR 下界 ≈ 历史最高PE ÷ 该股历史上可能出现的最低执行ROE

    下界已经超过 E_market 就直接跳过——重建出的真值只会更高。实测格力
    1.77、DECK 1.66、盐津铺子 9.20 全部如此，三战三无用。真正会被咬住的
    是长期低估值板块（银行、保险、公用、地产）：ROE 11% 却常年 PE 6，
    峰值PR 可能只有 0.7–0.8。
    """
    if max_historical_pe is None or min_plausible_decision_roe_percent is None:
        return {"rebuild": True, "reason": "insufficient_screen_inputs",
                "lower_bound_peak_pr": None, "e_market": e_market}
    positive("max_historical_pe", max_historical_pe)
    positive("min_plausible_decision_roe_percent", min_plausible_decision_roe_percent)
    lb = max_historical_pe / min_plausible_decision_roe_percent
    if lb >= e_market:
        return {"rebuild": False, "reason": "peak_cannot_bind",
                "lower_bound_peak_pr": lb, "e_market": e_market,
                "note": f"峰值PR 下界 {lb:.2f} ≥ 市场线 {e_market:.2f}，E 必取市场线，重建无意义"}
    return {"rebuild": True, "reason": "peak_may_bind",
            "lower_bound_peak_pr": lb, "e_market": e_market,
            "note": f"峰值PR 下界 {lb:.2f} < 市场线 {e_market:.2f}，需要逐峰值日重建"}


if __name__ == "__main__":
    main()
