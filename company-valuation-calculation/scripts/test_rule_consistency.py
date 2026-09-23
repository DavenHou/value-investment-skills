#!/usr/bin/env python3
"""Document-level guards for the single-decision-PR rule.

The 2026-09 handoff bug was not a code bug: the skill documents carried two
incompatible definitions of the action PR at the same time, so the model picked
whichever file it read first. These tests read the markdown itself.

Run from this directory:  python3 test_rule_consistency.py
"""

import pathlib
import re
import unittest

from calculate_valuation import recomputed_roe, trailing_twelve_month_eps

INVESTMENT_ROOT = pathlib.Path(__file__).resolve().parents[2]
VALUATION = INVESTMENT_ROOT / "company-valuation-calculation"
SIZING = INVESTMENT_ROOT / "portfolio-position-sizing"
EXIT = INVESTMENT_ROOT / "fundamental-exit-monitoring"
BACKGROUND = INVESTMENT_ROOT / "company-background-research"
PIPELINE = INVESTMENT_ROOT / "value-investment-pipeline"
FORECAST = INVESTMENT_ROOT / "company-earnings-forecast"
CASH = INVESTMENT_ROOT / "pure-cash-coverage"
INDEX_DOC = PIPELINE / "SKILL.md"
ACTIVE_SKILLS = (BACKGROUND, FORECAST, VALUATION, EXIT, SIZING, CASH, PIPELINE)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_files() -> list[pathlib.Path]:
    return sorted(path for root in ACTIVE_SKILLS for path in root.rglob("*.md"))


class SingleDecisionPrRuleTests(unittest.TestCase):
    def test_weighted_decision_pr_is_gone_everywhere(self):
        """v2 retired the scenario-weighting formula entirely."""
        offenders = [
            path for path in markdown_files()
            if re.search(r"决策PR\s*=\s*中性权重", read(path))
        ]
        self.assertEqual(offenders, [], "the retired weighted decision-PR formula is still present")

    def test_formula_is_selected_by_company_type(self):
        text = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertRegex(text, r"周期股\s+决策PR\s*=\s*100 × 同期PB")
        self.assertRegex(text, r"非周期\s+决策PR\s*=\s*PE_TTM ÷ 执行ROE")
        self.assertIn("single-decision-pr-v2", text)
        for company_type in ("周期股", "稳定价值", "科技", "金融"):
            self.assertIn(company_type, text)

    def test_cyclical_forecast_is_explicitly_in_second_formula(self):
        text = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("周期股预测进入第二公式", text)
        self.assertIn("预测高于历史低年时", text)
        self.assertIn("峰值日已有可追溯预测", text)

    def test_forecast_handoff_is_used_without_recomputing_weights(self):
        text = read(VALUATION / "references" / "scenario-weighting.md")
        guard = text[text.index("### 1.1"): text.index("### 1.2")]
        self.assertIn("取最低的那个进分母", guard)
        self.assertIn("正式所选档归一ROE", guard)
        self.assertIn("正式所选档归一ROE按methodology.md的对应情景交接", guard)
        self.assertIn("正式归一ROE只读取methodology.md交接", guard)
        self.assertIn("不得拿今天的预测回填", text)

    def test_forecast_has_exactly_one_buy_side_entry(self):
        """预测进买入端只剩正式悲观归一ROE一个入口。"""
        text = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("预测影响买入端的**唯一入口**", text)
        self.assertIn("周期股预测若显示回升", text)
        self.assertIn("已废止：前瞻位置层", text)
        # 旧状态名只允许出现在那条"已废止"说明里，不得回到规则正文
        block = text[text.index("## 2. 预测的入口"):text.index("## 3.")]
        body = "\n".join(l for l in block.splitlines() if not l.startswith(">"))
        for token in ("structural_decline", "upturn_confirmed", "forecast_only",
                      "forward_position"):
            self.assertNotIn(token, body, f"{token} 不该出现在规则正文")

    def test_historical_peaks_use_the_same_formula(self):
        exit_text = read(EXIT / "references" / "methodology.md")
        self.assertIn("退出主口径必须与建仓决策PR按同一类型公式复算", exit_text)
        self.assertIn("周期股用 `100 × 同期PB ÷ 执行ROE²`", exit_text)
        self.assertIn("非周期股用 `PE_TTM ÷ 执行ROE`", exit_text)

    def test_downstream_skills_consume_rather_than_recompute(self):
        sizing = read(SIZING / "SKILL.md")
        self.assertIn("建仓决策只使用估值交接中的唯一`决策PR`", sizing)
        self.assertNotIn("建仓决策使用动态权重后的决策PR", sizing)
        self.assertNotIn("forward_position", sizing)  # 已废止

    def test_pipeline_declares_one_action_line(self):
        fmt = read(PIPELINE / "references" / "user-company-query-format.md")
        self.assertIn("`执行PR＝决策PR`", fmt)
        self.assertIn("不产生动作许可", fmt)

    def test_quick_decision_card_is_the_fixed_twelve_row_template(self):
        fmt = read(PIPELINE / "references" / "user-company-query-format.md")
        block = fmt[fmt.index("### 核心决策卡固定模板"):fmt.index("### 估值价格带")]
        labels = [
            line.split("|")[1].strip()
            for line in block.splitlines()
            if line.startswith("| ") and not line.startswith("| 项目")
        ]
        self.assertEqual(labels, [
            "收盘价", "归母 TTM EPS", "归母 PE_TTM", "归母 ROE_TTM",
            "归母 ROA_TTM", "TTM扣非净利润同比", "重大业绩下滑保护",
            "决策 PR", "修正系数", "PB", "当前动作", "仓位建议",
        ])
        self.assertIn("未扣非的GAAP／法定归母口径", block)
        self.assertIn("正式主值使用未扣非的GAAP／法定归母净利润", read(VALUATION / "references" / "methodology.md"))
        self.assertNotIn("取对建仓更保守的结果", read(PIPELINE / "SKILL.md"))
        self.assertNotIn("执行值取更保守的一侧", read(PIPELINE / "references" / "execution.md"))
        self.assertIn("| 仓位建议 | `不输出` |", block)
        for path in (PIPELINE / "SKILL.md", PIPELINE / "references" / "fast-path-and-cache.md"):
            text = read(path)
            self.assertIn("判断”单元格", text)
            self.assertNotIn("增加一行“限制／有效性”", text)
            self.assertNotIn("卡内一行限制说明", text)

    def test_only_one_diagnostic_value_survives(self):
        """诊断值从三个砍到一个；当前运行率PR 与含预测中性PR 已废止。"""
        text = read(VALUATION / "references" / "scenario-weighting.md")
        block = text[text.index("## 4. 诊断值"):text.index("## 5.")]
        self.assertIn("只保留一个", block)
        self.assertIn("核验PR", block)
        self.assertIn("当前运行率PR仍用于周期股锚分歧诊断", block)
        self.assertIn("其他情景PR", block)

    def test_schema_is_one_compact_table(self):
        """output-schema 从 344 行 YAML 压成一张表；必须仍钉住关键字段。"""
        schema = read(VALUATION / "references" / "output-schema.md")
        self.assertLess(len(schema), 2000, "output-schema 又长回去了")
        for field in ("决策PR", "归一化估值位置", "governed_by", "8PB 闸门",
                      "校准项全清单", "核验PR", "历史峰值PR", "最坏情况", "缺口清单"):
            self.assertIn(field, schema, f"缺字段: {field}")
        self.assertNotIn("forward_position", schema)

    def test_migration_notes_conflict_is_resolved(self):
        """MIGRATION_NOTES flagged these files as still carrying the old rule."""
        stale = "中性/悲观 PR 加权形成执行 PR"
        for path in markdown_files():
            self.assertNotIn(stale, read(path), f"{path} still carries the retired wording")

    # ---- 与原始视频转稿对齐的规则（2026-09-13 校准）----

    def test_8pb_is_a_pb_gate_not_a_pr_scale(self):
        """8PB 只禁建仓，不得被换算成 PR 刻度塞进 E。"""
        meth = read(VALUATION / "references" / "methodology.md")
        self.assertIn("8PB", meth)
        self.assertIn("当前PB > 8 → 不得建仓", meth)
        self.assertIn("已废止", meth)
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("PB > 8 一律不建仓", sw)
        self.assertIn("不是估值刻度", sw)
        # E 的上界必须是个股历史峰值，不是 800/ROE²
        for path in (sw, read(VALUATION / "references" / "cross-market-calibration.md")):
            self.assertIn("个股历史峰值", path)
        offenders = [p for p in markdown_files()
                     if "E = min(E_market, 800" in read(p).replace("÷", "/")
                     or "min(市场高估线, 800" in read(p)]
        self.assertEqual(offenders, [], "8PB 仍被当作 E 的上界")

    def test_selected_forecast_roe_for_every_type(self):
        """各类型使用所选档预测，并保留当前可比ROE取低。"""
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("min(正式所选档归一ROE, 当前可比TTM)", sw)
        self.assertIn("min(历史多年平均ROE, 当前ROE_TTM, 正式所选档归一ROE)", sw)
        self.assertIn("取最低的那个进分母", sw)
        self.assertIn("中远海控案例", sw)

    def test_pb_form_is_cyclical_only(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("PB形第二公式", sw)
        self.assertIn("非周期   决策PR = PE_TTM ÷ 执行ROE", sw)
        self.assertIn("取最低＝取最高估", sw)

    def test_historical_peak_caps_the_high_line(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("E = min(市场高估线, 历史峰值PR)", sw)
        self.assertIn("historical_peak_status", sw)

    def test_buy_and_sell_share_one_market_coefficient(self):
        """MIGRATION_NOTES 第 23 条：市场系数 c 同乘买入线与高估线，两端同尺。

        本测试取代 test_buy_thresholds_are_not_scaled_by_market（2026-09-13 立，
        2026-09-15 被第 23 条推翻）。推翻理由见 MIGRATION_NOTES 第 23 条：只乘卖出端
        会让首仓的归一化位置变成 0.50/c，持有区间被市场折价单方面吃掉。
        """
        for path in (VALUATION / "references" / "scenario-weighting.md",
                     VALUATION / "references" / "cross-market-calibration.md",
                     SIZING / "references" / "user-policy.md"):
            text = read(path)
            self.assertIn("取更严", text)
        # 旧表述必须彻底消失，防止"买入线不乘系数"回潮
        for phrase in ("不乘市场系数", "买入档全市场同值", "买入线不乘系数"):
            offenders = [p for p in markdown_files() if phrase in read(p)]
            self.assertEqual(offenders, [], "旧的买入线免乘表述仍在：%s" % phrase)
        # 0.90 是港股专属，不得外溢到 A 股／美股
        cm = read(VALUATION / "references" / "cross-market-calibration.md")
        self.assertIn("A股／美股   c = 1.00", cm)
        self.assertIn("不得外溢", cm)
        valuation_code = read(VALUATION / "scripts" / "calculate_valuation.py")
        position_code = read(SIZING / "scripts" / "calculate_position.py")
        self.assertIn("market_coefficient(", valuation_code)
        self.assertNotIn("market_pr_factor = 0.8", valuation_code)
        self.assertIn("由估值 skill 计算，仓位 skill 只消费", position_code)
        self.assertNotIn("def buy_side_c", position_code)
        self.assertNotIn("仅用于买入端", position_code)

    def test_quality_downgrade_band(self):
        """第 20/22/27 条：55–59 降级档，只看总分，买入线不随质量分下调。"""
        sc = read(BACKGROUND / "references" / "scorecard.md")
        self.assertIn("pass_downgraded", sc)
        self.assertIn("55–59", sc)
        self.assertIn("<55", sc)
        self.assertIn("只看总分，单项维度不设闸门", sc)
        self.assertIn("不走估值阈值", sc)
        # 第 27 条废止维度硬线：旧的"任一不达即 fail"表述不得回潮
        self.assertNotIn("两项及以上失守直接", sc)
        cap = read(SIZING / "references" / "user-policy.md")
        self.assertIn("| < 55 |", cap)
        self.assertIn("| 55–59 |", cap)
        offenders = [p for p in markdown_files() if "0.40／0.30／0.25" in read(p)]
        self.assertEqual(offenders, [], "降级档买入线缩放未还原")

    def test_prescreen_runs_before_quality_gate(self):
        """第 26 条：前置快筛是第 0 步，排在质量闸门之前。"""
        idx = read(INDEX_DOC).split("## 运行流水线", 1)[1]
        self.assertIn("五步流程", idx)
        self.assertIn("前置快筛", idx)
        self.assertLess(idx.index("前置快筛"), idx.index("质量闸门"),
                        "前置快筛必须排在质量闸门之前")
        for phrase in ("PB > 8", "核验PR", "周期股禁用 0b", "已有持仓复查不走此步"):
            self.assertIn(phrase, idx, "第 0 步缺少必备条款：%s" % phrase)

    def test_index_doc_carries_no_retired_market_coefficient(self):
        """索引文档不能保留旧市场系数，也不应复制估值公式。"""
        idx = read(INDEX_DOC)
        for phrase in ("不乘市场系数", "买入线市场系数恒为 1.0", "H 0.80 或 0.72"):
            self.assertNotIn(phrase, idx, "索引文档仍带已作废的市场系数表述：%s" % phrase)
        self.assertIn("港股市场系数及买卖两端刻度也以估值 skill 为准", idx)
        self.assertNotIn("c = 0.90 ×", idx)

    def test_verification_pr_is_lower_bound(self):
        """第 26 条 0b 的数学前提：ROE_TTM 必须留在执行ROE 的取低集合里。

        只要 执行ROE ≤ ROE_TTM，就有 决策PR ≥ 核验PR，0b 才是单向闸门。
        """
        idx = read(INDEX_DOC)
        self.assertIn("ROE_TTM", idx,
                      "执行ROE 取低集合里少了 ROE_TTM，0b 的下界性质即失效")
        self.assertIn("min(历史多年平均ROE, 当前ROE_TTM, 正式所选档归一ROE)",
                      read(VALUATION / "references" / "scenario-weighting.md"))
        # 数值守卫：用已归档的实测值复核下界关系
        cases = [  # (PE_TTM, ROE_TTM, 执行ROE, 已归档决策PR, 已归档核验PR)
            (7.8146, 13.050, 12.614, 0.6195, 0.5988),   # 新奥能源 02688
            (13.812, 20.573, 20.573, 0.6714, 0.6714),   # 腾讯 00700
            (25.222, 7.015, 7.015, 3.5952, 3.5952),     # 阿里 09988
            (6.442, 12.306, 11.389, 0.5656, 0.5235),    # 特步 01368
        ]
        for pe, roe_ttm, exe, dec, ver in cases:
            self.assertLessEqual(exe, roe_ttm + 1e-9, "执行ROE 超过了 ROE_TTM")
            self.assertAlmostEqual(pe / exe, dec, places=3)
            self.assertAlmostEqual(pe / roe_ttm, ver, places=3)
            self.assertGreaterEqual(dec, ver - 1e-9, "决策PR 跌破核验PR，0b 会误杀")

    def test_buyback_distortion_requires_recomputed_roe(self):
        """MIGRATION_NOTES 第 25 条：净资产收缩时必须算重算ROE，ROIC 不绑定不等于放行。"""
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("回购型失真", sw)
        self.assertIn("重算ROE", sw)
        self.assertIn("回扣窗口与该企业类型的执行ROE 历史窗口一致", sw)
        self.assertIn("ROIC 对“回购做小净资产”是盲的", sw)
        skill = read(VALUATION / "SKILL.md")
        self.assertIn("重算ROE", skill)

    def test_normal_capital_roe_has_one_implementation(self):
        implementations = [
            path
            for root in (VALUATION, SIZING, PIPELINE)
            for path in root.rglob("*.py")
            if re.search(r"^def recomputed_roe\(", read(path), re.MULTILINE)
        ]
        self.assertEqual(
            implementations,
            [VALUATION / "scripts" / "calculate_valuation.py"],
            "正常资本ROE只能在估值skill实现，下游必须消费交接",
        )

    def test_recomputed_roe_numeric_deckers(self):
        """数值守卫：DECK 全部输入锁定在 2026-06-30，不得再混用 March 权益或前瞻EPS。"""
        ttm_eps = trailing_twelve_month_eps(
            latest_full_year_diluted_eps=7.02,
            prior_comparable_ytd_diluted_eps=0.93,
            current_ytd_diluted_eps=0.94,
        )
        normal = recomputed_roe(
            ttm_net_income=1014.840,
            ending_equity=2301.682,
            cumulative_buyback=2369.750,
            company_type="stable",
            financial_cutoff_date="2026-06-30",
            buyback_window_start_date="2023-07-01",
            buyback_window_end_date="2026-06-30",
        )
        pe_ttm = 78.43 / ttm_eps
        self.assertAlmostEqual(ttm_eps, 7.03)
        self.assertAlmostEqual(normal["recomputed_roe_percent"], 21.7243877252)
        self.assertAlmostEqual(pe_ttm / normal["recomputed_roe_percent"], 0.5135459928)
        self.assertLess(normal["implied_pb_at_pr_one"], 8.0)

    def test_payout_correction_has_yield_gate(self):
        """MIGRATION_NOTES 第 24 条：N 只对股息率 > 4% 的红利股适用；D<=0 时 N=1。"""
        meth = read(VALUATION / "references" / "methodology.md")
        self.assertIn("股息率 > 4%", meth)
        self.assertIn("不是 2", meth)

    def test_regime_split_defaults_to_halving(self):
        """中远海控案例的结论是减仓一半，不是'不得机械减半'。"""
        for path in (VALUATION / "references" / "scenario-weighting.md",
                     EXIT / "references" / "methodology.md"):
            self.assertIn("减仓一半", read(path))
        offenders = [p for p in markdown_files()
                     if "不得机械解释为固定减仓50%" in read(p)]
        self.assertEqual(offenders, [], "旧的'禁止减半'表述仍未清除")

    def test_payout_adjustment_excludes_cyclical_tech_growth(self):
        meth = read(VALUATION / "references" / "methodology.md")
        block = meth[meth.index("修正系数 N 的适用边界"):]
        for t in ("周期股", "科技股", "成长股"):
            self.assertIn(t, block[:800])
        self.assertIn("不使用", block[:800])

    def test_cyclical_roe_is_conservative_first(self):
        meth = read(VALUATION / "references" / "methodology.md")
        self.assertIn("尽量保守", meth)
        self.assertIn("景气周期里 ROE 最低的一年", meth)

    def test_ttm_roe_default_matches_source_method(self):
        meth = read(VALUATION / "references" / "methodology.md")
        self.assertIn("最近四个单季度的净资产收益率直接相加", meth)

    def test_fifty_percent_is_not_a_position_gate(self):
        pol = read(SIZING / "references" / "user-policy.md")
        self.assertIn("不是仓位硬闸门", pol)
        self.assertIn("止损退出", pol)


    def test_three_buy_tiers_everywhere(self):
        """买入档收敛为 0.50/0.40/0.30 三档，旧的四档表述必须消失。"""
        offenders = [p for p in markdown_files()
                     if re.search(r"0\.55\s*[／/]\s*0\.50", read(p))]
        self.assertEqual(offenders, [], "旧的四档买入线仍在")
        for path in (VALUATION / "references" / "scenario-weighting.md",
                     SIZING / "references" / "user-policy.md",
                     SIZING / "SKILL.md"):
            text = read(path)
            for tier in ("0.50", "0.40", "0.30"):
                self.assertIn(tier, text, f"{path} 缺少买入档 {tier}")

    def test_normalized_scale_puts_sell_line_at_one(self):
        for path in (VALUATION / "references" / "scenario-weighting.md",
                     SIZING / "references" / "user-policy.md",
                     EXIT / "references" / "methodology.md"):
            text = read(path)
            self.assertIn("归一化", text)
            self.assertIn("1.0", text)
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertRegex(sw, r"估值位置\s*=\s*决策PR\s*÷\s*E")

    def test_sell_ladder_is_080_090_100(self):
        for path in (VALUATION / "references" / "scenario-weighting.md",
                     SIZING / "references" / "user-policy.md",
                     EXIT / "references" / "methodology.md"):
            text = read(path)
            for level in ("0.80", "0.90", "1.00"):
                self.assertIn(level, text, f"{path} 缺少卖出档 {level}")


    def test_four_step_flow_is_declared(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        for step in ("第1步 质量闸门", "第2步 估值", "第3步 退出", "第4步 仓位"):
            self.assertIn(step, sw)
        self.assertIn("正式归一ROE档位直接消费methodology.md交接", sw)

    def test_stable_normalization_uses_shared_conservative_anchor_fifty_fifty(self):
        meth = read(VALUATION / "references" / "methodology.md")
        self.assertIn("50% × 历史悲观ROE锚 + 20% × F1基准ROE", meth)
        self.assertIn("20% × F2基准ROE + 10% × F3基准ROE", meth)
        self.assertIn("50% × 历史悲观ROE锚 + 20% × F1熊市ROE", meth)
        self.assertNotIn("60% × 三年等权平均ROE", meth)
        self.assertNotIn("mean(过去几年实际ROE + 熊市F1–F3预测ROE)", read(VALUATION / "references" / "scenario-weighting.md"))

    def test_forecast_enters_only_through_the_selected_normalized_roe(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("正式所选档归一ROE", sw)
        self.assertIn("预测影响买入端的**唯一入口**", sw)
        self.assertIn("历史峰值PR必须有峰值日当时可得", sw)

    def test_roic_replaces_roe_on_buyback_distortion(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("ROIC", sw)
        self.assertIn("buyback_or_leverage_distorted", sw)
        self.assertIn("个股历史峰值PR 必须用同一口径重算", sw)

    def test_quality_score_sets_the_position_cap(self):
        pol = read(SIZING / "references" / "user-policy.md")
        self.assertIn("仓位上限由质量分决定", pol)
        for band in ("10%", "20%", "28%", "35%"):
            self.assertIn(band, pol)
        self.assertIn("等比缩放", pol)
        self.assertIn("不能截断", pol)
        self.assertIn("最坏情况预估", pol)
        # 校准项必须强制全打印，含未触发的
        self.assertIn("校准项必须全部打印", pol)
        for item in ("E_market", "clamp(50/D, 1, 2)", "买入线是否已乘 `c`"):
            self.assertIn(item, pol)


    def test_eight_pb_is_one_line_not_a_regime(self):
        """8PB 只有一条判断：PB>8 不建仓。不得再长出分档闸门。"""
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("当前PB > 8  →  不建仓", sw)
        self.assertIn("就这一条", sw)
        self.assertIn("卖出看归一化估值位置，不看PB", sw)
        for gone in ("boundary_high_roe", "out_of_scope_high_roe", "适用域闸门"):
            offenders = [p for p in markdown_files() if gone in read(p)]
            self.assertEqual(offenders, [], f"已废止的 {gone} 仍在文档中")

    def test_buy_uses_the_stricter_of_two_readings(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("两个读数取更严", sw)
        self.assertIn("任一条不达标就不开档", sw)
        self.assertIn("governed_by", sw)

    def test_roic_joins_the_min_set_rather_than_replacing(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("不是“单方面顶替”", sw)
        self.assertIn("只有它更低时才能收紧", sw)


    def test_peak_rebuild_procedure_is_documented(self):
        sw = read(VALUATION / "references" / "scenario-weighting.md")
        self.assertIn("逐峰值日重建的做法", sw)
        self.assertIn("按发布日而非报告期截止日", sw)
        self.assertIn("周期股缺预测证据时该峰值记`insufficient`", sw)
        # 实测值必须钉住，防止再用"年度最高PB ÷ 当年ROE"的近似回填
        self.assertIn("1.7727", sw)
        self.assertIn("1.6638", sw)

    def test_no_stale_claim_that_gree_never_reached_one(self):
        stale = ["格力历年峰值约 0.46", "格力历史峰值 PR 约 0.59", "历史上从未涨到 PR 1.0 的股票（格力"]
        for path in markdown_files():
            text = read(path)
            for bad in stale:
                self.assertNotIn(bad, text, f"{path} 仍带着已被证伪的格力峰值")


if __name__ == "__main__":
    unittest.main()
