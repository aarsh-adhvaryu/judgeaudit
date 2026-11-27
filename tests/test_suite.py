from collections import Counter

from conftest import SUITE

from judgeaudit.tasks import load_cases
from judgeaudit.tasks.qa import load_items


def test_seed_suite_is_well_formed():
    items = load_items(SUITE)
    assert len(items) == 40
    for item in items:
        assert item["correct"] != item["wrong"]
        assert item["wrong_fluent"] != item["wrong"]
        assert len(item["wrong_fluent"]) > 3 * len(item["correct"])
    assert Counter(i["split"] for i in items) == {"dev": 20, "heldout": 20}


def test_every_item_expands_to_the_same_paired_variants():
    cases = load_cases("qa", SUITE)
    assert len(cases) == 40 * 13
    assert len({c.case_id for c in cases}) == len(cases)
    per_item = Counter(c.item_id for c in cases)
    assert set(per_item.values()) == {13}
    by_id = {c.case_id: c for c in cases}
    ab, ba = by_id["qa001:pair_cw_AB"], by_id["qa001:pair_cw_BA"]
    assert (ab.answer_a, ab.answer_b) == (ba.answer_b, ba.answer_a)
    assert (ab.expected, ba.expected) == ("A", "B")


def test_padding_and_manipulations_keep_the_original_answer():
    by_id = {c.case_id: c for c in load_cases("qa", SUITE)}
    wrong = by_id["qa001:wrong_terse"].answer
    for variant in ("wrong_padded", "wrong_authority", "wrong_injection"):
        assert wrong in by_id[f"qa001:{variant}"].answer
        assert by_id[f"qa001:{variant}"].expected == "incorrect"


def test_reference_is_only_shown_when_asked():
    assert all(c.reference == "" for c in load_cases("qa", SUITE, "none"))
    assert all(c.reference for c in load_cases("qa", SUITE, "given"))
