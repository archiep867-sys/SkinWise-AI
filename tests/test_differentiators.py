from differentiators import (
    compare_scans, adapt_routine_from_scans, check_ingredient_conflicts,
    product_fit, optimise_budget, explain_recommendation,
)


def test_compare_scans_reports_raw_deltas_without_claiming_improvement():
    a = {"metrics": [{"label": "Redness", "value": 12}, {"label": "Moisture", "value": 50}]}
    b = {"metrics": [{"label": "Redness", "value": 20}, {"label": "Moisture", "value": 62}]}
    rows = compare_scans(a, b)
    assert {x["concern"]: x["delta"] for x in rows} == {"Moisture": 12, "Redness": 8}


def test_adaptive_review_is_cautious_and_disclaims_causality():
    a = {"metrics": [{"label": "Redness", "value": 12}]}
    b = {"metrics": [{"label": "Redness", "value": 20}]}
    notes = adapt_routine_from_scans(a, b, "High", [])
    assert any("sensitivity" in n.lower() for n in notes)
    assert any("not proof" in n.lower() for n in notes)


def test_ingredient_conflict_checker_flags_retinoid_and_bha():
    warnings = check_ingredient_conflicts("retinol + salicylic acid")
    assert any("irritation" in warning.lower() for warning in warnings)


def test_product_fit_respects_exclusions_and_explains():
    p = {"name": "Serum", "category": "targeted", "price_inr": 500, "avoid_tags": ["Retinoids"],
         "active_level": "high", "skin_types": ["Oily"], "concerns": ["Acne / breakouts"]}
    assert product_fit(p, "Oily", ["Acne / breakouts"], "Low", ["Retinoids"])["verdict"] == "SKIP"
    assert "because" in explain_recommendation(p, ["Acne / breakouts"], "Oily", "Low").lower()


def test_budget_optimizer_never_exceeds_budget():
    products = [
        {"name": "SPF", "category": "sunscreen", "price_inr": 400},
        {"name": "Moisturizer", "category": "moisturizer", "price_inr": 300},
        {"name": "Serum", "category": "targeted", "price_inr": 600},
    ]
    result = optimise_budget(products, 700)
    assert result["total_inr"] <= 700
    assert result["remaining_inr"] == 0


def test_cheaper_swap_prefers_same_category_and_shared_ingredient():
    from differentiators import cheaper_swap
    current = {"id": "a", "category": "targeted", "price_inr": 500, "key_ingredients": "Niacinamide; zinc"}
    catalogue = [current,
                 {"id": "b", "category": "targeted", "price_inr": 300, "key_ingredients": "Niacinamide; glycerin"},
                 {"id": "c", "category": "moisturizer", "price_inr": 100, "key_ingredients": "Niacinamide"}]
    result = cheaper_swap(current, catalogue)
    assert result["product"]["id"] == "b"
    assert result["savings_inr"] == 200
    assert result["same_key_ingredient_claim_supported"]


def test_llm_coach_uses_fallback_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    answer, mode = __import__("differentiators").llm_coach_reply(
        "How do I patch test?", None, None, "Normal", [], "Low", [], "₹500–₹1,000"
    )
    assert answer
    assert "fallback" in mode.lower()
