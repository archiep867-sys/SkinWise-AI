import pytest
from skincare import build_routine, demo_analysis, make_budget_guide, parse_analysis, routine_coach_reply


def test_demo_is_explicitly_not_measured():
    result = demo_analysis("Oily", ["Acne / breakouts"])
    assert "not analyzed" in result["summary"].lower()
    assert result["metrics"][0]["value"] == "Not measured"


def test_routine_includes_sunscreen_and_moisturizer():
    plan = build_routine({}, "Under ₹500", "Oily", ["Dark spots"], "Low", "Simple (essentials first)")
    names = [x["name"].lower() for x in plan["morning"]]
    assert any("sunscreen" in x for x in names)
    assert any("moisturizer" in x for x in names)


def test_sensitive_profile_avoids_optional_active():
    plan = build_routine({}, "₹500–₹1,000", "Sensitive", ["Acne / breakouts"], "High", "Balanced (one optional extra)")
    names = [x["name"] for x in plan["morning"] + plan["evening"]]
    assert not any("optional acne" in x.lower() or "niacinamide" in x.lower() for x in names)


def test_avoid_acids_disables_optional_active():
    plan = build_routine({}, "₹500–₹1,000", "Oily", ["Acne / breakouts"], "Low", "Balanced (one optional extra)", ["Exfoliating acids"])
    names = [x["name"] for x in plan["morning"] + plan["evening"]]
    assert not any("optional acne" in x.lower() for x in names)


def test_parse_analysis_preserves_raw_response():
    raw = {"score": 72, "concerns": [{"name": "dryness"}], "unmapped": "value"}
    parsed = parse_analysis(raw)
    assert parsed["raw_response"] == raw
    assert parsed["concerns"] == ["dryness"]


def test_parse_rejects_non_object():
    with pytest.raises(TypeError):
        parse_analysis(["not", "an", "object"])


def test_budget_guide_has_three_priorities():
    assert len(make_budget_guide("Under ₹500", "Oily", "Low")) == 3


def test_coach_escalates_irritation_cautiously():
    answer = routine_coach_reply("my skin is burning", "High", "Sensitive", [], "Under ₹500")
    assert "Stop the newest product" in answer
