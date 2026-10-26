from products import recommend_products
from storage import add_journal_entry, clear_journal, get_journal_entries, save_checkins, get_checkins


def test_product_shortlist_respects_budget_and_exclusions():
    result = recommend_products("Oily", ["Acne / breakouts"], "Low", ["Exfoliating acids"], "₹500–₹1,000")
    assert result["total_inr"] <= result["budget_cap_inr"]
    assert all("exfoliating-acids" not in product["tags"] for product in result["products"])
    assert result["price_checked"]


def test_sensitive_profile_avoids_moderate_active_products():
    result = recommend_products("Sensitive", ["Acne / breakouts"], "High", [], "₹1,000–₹2,000")
    assert all(product["active_level"] == "low" for product in result["products"])
    assert not any(product["category"] == "targeted" for product in result["products"])


def test_journal_and_checkins_persist(tmp_path):
    db = tmp_path / "test_skinwise.db"
    add_journal_entry({"date": "2026-10-26", "source": "Journal entry", "skin_feel": "Comfortable"}, db)
    assert get_journal_entries(db)[0]["skin_feel"] == "Comfortable"
    save_checkins("2026-10-26", ["Cleanser"], ["Cleanser", "Moisturizer"], db)
    checkins = get_checkins(db)
    assert {x["step_name"]: x["completed"] for x in checkins} == {"Cleanser": 1, "Moisturizer": 0}
    clear_journal(db)
    assert get_journal_entries(db) == []


def test_catalog_has_at_least_30_real_product_entries_with_buy_links():
    from products import PRODUCTS
    assert len(PRODUCTS) >= 30
    assert all(p["buy_link"].startswith("https://") for p in PRODUCTS)
    assert all(p["price_inr"] > 0 and p["key_ingredients"] for p in PRODUCTS)
