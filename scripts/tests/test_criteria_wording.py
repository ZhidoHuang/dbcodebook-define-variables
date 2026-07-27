import importlib.util
import unittest
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[1] / "check_definition_output.py"
SPEC = importlib.util.spec_from_file_location("check_definition_output", CHECKER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CriteriaWordingFixtures(unittest.TestCase):
    def assert_clean(self, text: str) -> None:
        self.assertEqual(MODULE.criteria_wording_issues(text), [])

    def assert_issue(self, text: str, expected: str) -> None:
        self.assertIn(expected, MODULE.criteria_wording_issues(text))

    def test_direct_single_question_recode(self) -> None:
        self.assert_clean(
            "“是否曾经吸烟？”回答为 [Yes] 时记为 [1]，"
            "回答为 [No] 时记为 [0]。"
        )

    def test_period_source_correspondence_is_parenthetical(self) -> None:
        self.assert_clean(
            "“是否曾经吸烟？”回答为 [Yes] 时记为 [1]，"
            "回答为 [No] 时记为 [0]。"
            "（2011-2018 使用 da059，2020 使用 da046。）"
        )

    def test_separate_numbered_source_item_is_rejected(self) -> None:
        self.assert_issue(
            "① “是否曾经吸烟？”回答为 [Yes] 时记为 [1]。"
            "② 对应原始变量：2011-2018 使用 da059，2020 使用 da046。",
            "source correspondence is a separate numbered item",
        )

    def test_database_neutral_source_item_is_rejected(self) -> None:
        self.assert_issue(
            "① 回答为 [Yes] 时记为 [1]。"
            "② 对应来源：Wave 1-10 使用 source_a，Wave 11 使用 source_b。",
            "source correspondence is a separate numbered item",
        )

    def test_supplementary_source_rule(self) -> None:
        self.assert_clean(
            "直接题没有回答时，仅当 zda059 或 zsmoke 为 [Yes]，"
            "补充记为 [1]；其余保留缺失。"
        )

    def test_questionnaire_completeness_uses_valid_responses(self) -> None:
        self.assert_clean("仅在 8 项均有有效回答时计算总分。")

    def test_derived_completeness_uses_valid_records(self) -> None:
        self.assert_clean("仅在当期 9 个单项均有有效记录时累加困难项目数。")

    def test_mechanical_valid_response_recode_is_rejected(self) -> None:
        self.assert_issue(
            "da059 的有效回答为 [Yes] 时记为 [1]，为 [No] 时记为 [0]。",
            "single-question recode uses 有效回答",
        )

    def test_mechanical_valid_record_assignment_is_rejected(self) -> None:
        self.assert_issue(
            "该变量的有效记录为 [1] 时记为 [1]。",
            "single-record assignment uses 有效记录",
        )

    def test_explicit_wording_is_rejected(self) -> None:
        self.assert_issue("仅使用明确回答。", "banned wording: 明确回答")
        self.assert_issue("仅使用明确记录。", "banned wording: 明确记录")

    def test_structured_raw_conflict_disclosure(self) -> None:
        self.assert_clean(
            "变量甲与变量乙存在原始记录矛盾。"
            "变量甲与变量乙保留原始矛盾，不做相互修正。"
            "<br>Wave 1：source_a 与 source_b，12 条。"
        )

    def test_vague_conflict_wording_is_rejected(self) -> None:
        self.assert_issue(
            "两个定义变量可能因此呈现不一致组合。",
            "raw conflict disclosure is vague",
        )

    def test_engineering_override_wording_is_rejected(self) -> None:
        self.assert_issue(
            "不用其中一组来源覆盖另一组。",
            "raw conflict disclosure uses engineering override wording",
        )

    def test_preservation_requires_no_mutual_correction(self) -> None:
        self.assert_issue(
            "两个变量保留原始矛盾。",
            "raw conflict preservation lacks no-mutual-correction statement",
        )


if __name__ == "__main__":
    unittest.main()
