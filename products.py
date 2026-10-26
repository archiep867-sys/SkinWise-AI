"""Curated Indian skincare product catalogue.

Prices are indicative INR snapshots, not live offers. Links open retailer searches so
users can verify the exact SKU, current price, size, stock, and ingredient label.
Ingredient highlights are a shopping aid only; formulas can change, so check packaging.
"""
from datetime import date
from urllib.parse import quote_plus

PRICE_CHECKED = "2026-10-26 (indicative; verify retailer price)"
CATALOG_SOURCE = "https://www.nykaa.com/"

_RAW_PRODUCTS = [
# Minimalist
("Minimalist 2% Salicylic Acid + LHA Cleanser", "cleanser", 299, "Salicylic acid, LHA", ["Oily", "Combination"], ["Acne / breakouts", "Oiliness"], ["Exfoliating acids"], "moderate", "https://www.nykaa.com/search/result/?q=Minimalist%202%25%20Salicylic%20Acid%20LHA%20Cleanser"),
("Minimalist Oat Extract Gentle Cleanser", "cleanser", 299, "Oat extract; verify full INCI", ["Dry", "Combination", "Normal", "Sensitive", "Oily"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Minimalist%20Oat%20Extract%20Gentle%20Cleanser"),
("Minimalist Vitamin B5 10% Moisturizer", "moisturizer", 349, "Vitamin B5; humectants", ["Oily", "Combination", "Normal"], ["Dryness", "Oiliness"], [], "low", "https://www.nykaa.com/search/result/?q=Minimalist%20Vitamin%20B5%20Moisturizer"),
("Minimalist 5% Marula Oil Moisturizer", "moisturizer", 299, "Marula oil", ["Dry", "Normal"], ["Dryness"], [], "low", "https://www.nykaa.com/search/result/?q=Minimalist%205%25%20Marula%20Oil%20Moisturizer"),
("Minimalist SPF 50 PA++++ Sunscreen", "sunscreen", 399, "UV filters; check exact formula", ["Dry", "Combination", "Normal", "Sensitive", "Oily"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Minimalist%20SPF%2050%20Sunscreen"),
("Minimalist 10% Niacinamide Face Serum", "targeted", 599, "Niacinamide", ["Oily", "Combination", "Normal"], ["Oiliness", "Acne / breakouts", "Dark spots"], [], "moderate", "https://www.nykaa.com/search/result/?q=Minimalist%2010%25%20Niacinamide%20Serum"),
("Minimalist 2% Alpha Arbutin Serum", "targeted", 599, "Alpha arbutin", ["Oily", "Dry", "Combination", "Normal"], ["Dark spots"], [], "moderate", "https://www.nykaa.com/search/result/?q=Minimalist%202%25%20Alpha%20Arbutin%20Serum"),
("Minimalist 0.3% Retinol Face Serum", "targeted", 649, "Retinol", ["Oily", "Dry", "Combination", "Normal"], ["Fine lines", "Uneven texture"], ["Retinoids"], "high", "https://www.nykaa.com/search/result/?q=Minimalist%200.3%25%20Retinol%20Serum"),
# Cetaphil
("Cetaphil Gentle Skin Cleanser", "cleanser", 350, "Glycerin; niacinamide and panthenol in some versions", ["Dry", "Sensitive", "Normal"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Cetaphil%20Gentle%20Skin%20Cleanser"),
("Cetaphil Moisturising Cream", "moisturizer", 399, "Glycerin; emollients", ["Dry", "Sensitive", "Normal"], ["Dryness"], [], "low", "https://www.nykaa.com/search/result/?q=Cetaphil%20Moisturising%20Cream"),
("Cetaphil Sun SPF 50+ Light Gel", "sunscreen", 999, "UV filters; check current label", ["Oily", "Combination", "Normal"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Cetaphil%20Sun%20SPF%2050%20Light%20Gel"),
# Neutrogena
("Neutrogena Hydro Boost Water Gel", "moisturizer", 950, "Hyaluronic acid; check fragrance on current label", ["Oily", "Combination", "Normal"], ["Dryness", "Oiliness"], ["Fragrance"], "low", "https://www.nykaa.com/search/result/?q=Neutrogena%20Hydro%20Boost%20Water%20Gel"),
("Neutrogena Ultra Sheer Dry Touch SPF 50+", "sunscreen", 650, "UV filters; check current label", ["Oily", "Combination", "Normal"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Neutrogena%20Ultra%20Sheer%20SPF%2050"),
("Neutrogena Oil-Free Acne Wash", "cleanser", 650, "Salicylic acid", ["Oily", "Combination"], ["Acne / breakouts", "Oiliness"], ["Exfoliating acids"], "moderate", "https://www.nykaa.com/search/result/?q=Neutrogena%20Oil%20Free%20Acne%20Wash"),
# Simple
("Simple Kind to Skin Refreshing Facial Wash", "cleanser", 385, "Pro-vitamin B5; vitamin E", ["Oily", "Combination", "Normal", "Sensitive"], ["Oiliness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Simple%20Kind%20to%20Skin%20Refreshing%20Facial%20Wash"),
("Simple Kind to Skin Hydrating Light Moisturiser", "moisturizer", 425, "Glycerin; pro-vitamin B5", ["Oily", "Combination", "Normal", "Sensitive"], ["Dryness"], [], "low", "https://www.nykaa.com/search/result/?q=Simple%20Hydrating%20Light%20Moisturiser"),
("Simple Kind to Skin Micellar Water", "cleanser", 375, "Micellar cleansing agents; check label", ["Dry", "Combination", "Normal", "Sensitive", "Oily"], ["Uneven texture"], [], "low", "https://www.nykaa.com/search/result/?q=Simple%20Kind%20to%20Skin%20Micellar%20Water"),
# Dot & Key
("Dot & Key Barrier Repair Moisturizer", "moisturizer", 495, "Ceramides; verify exact version", ["Dry", "Combination", "Normal"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Dot%20and%20Key%20Barrier%20Repair%20Moisturizer"),
("Dot & Key Watermelon Cooling Sunscreen SPF 50", "sunscreen", 495, "UV filters; watermelon extract", ["Oily", "Combination", "Normal"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Dot%20and%20Key%20Watermelon%20Sunscreen%20SPF%2050"),
("Dot & Key Cica Calming Night Gel", "moisturizer", 495, "Centella asiatica (cica); verify exact version", ["Oily", "Combination", "Sensitive"], ["Redness", "Dryness"], [], "low", "https://www.nykaa.com/search/result/?q=Dot%20and%20Key%20Cica%20Calming%20Night%20Gel"),
# The Derma Co
("The Derma Co 1% Hyaluronic Sunscreen Aqua Gel SPF 50", "sunscreen", 499, "Hyaluronic acid; UV filters", ["Oily", "Combination", "Normal"], ["Dryness", "Dark spots"], [], "low", "https://www.nykaa.com/search/result/?q=The%20Derma%20Co%201%25%20Hyaluronic%20Sunscreen"),
("The Derma Co 2% Salicylic Acid Face Serum", "targeted", 499, "Salicylic acid", ["Oily", "Combination"], ["Acne / breakouts", "Oiliness"], ["Exfoliating acids"], "moderate", "https://www.nykaa.com/search/result/?q=The%20Derma%20Co%202%25%20Salicylic%20Acid%20Serum"),
("The Derma Co 5% Niacinamide Face Serum", "targeted", 499, "Niacinamide", ["Oily", "Combination", "Normal"], ["Oiliness", "Dark spots"], [], "moderate", "https://www.nykaa.com/search/result/?q=The%20Derma%20Co%205%25%20Niacinamide%20Serum"),
# Re'equil
("Re'equil Oil Free Moisturiser", "moisturizer", 395, "Humectants; check full label", ["Oily", "Combination"], ["Oiliness", "Dryness"], [], "low", "https://www.nykaa.com/search/result/?q=Reequil%20Oil%20Free%20Moisturiser"),
("Re'equil Ultra Matte Dry Touch Sunscreen SPF 50", "sunscreen", 695, "UV filters; check current label", ["Oily", "Combination", "Normal"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Reequil%20Ultra%20Matte%20Sunscreen%20SPF%2050"),
("Re'equil Ceramide & Hyaluronic Acid Moisturiser", "moisturizer", 450, "Ceramides; hyaluronic acid", ["Dry", "Normal", "Sensitive"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Reequil%20Ceramide%20Hyaluronic%20Acid%20Moisturiser"),
# Plum
("Plum Green Tea Pore Cleansing Face Wash", "cleanser", 345, "Green tea; check exfoliating components", ["Oily", "Combination"], ["Oiliness", "Acne / breakouts"], [], "low", "https://www.nykaa.com/search/result/?q=Plum%20Green%20Tea%20Pore%20Cleansing%20Face%20Wash"),
("Plum 2% Niacinamide Face Serum", "targeted", 499, "Niacinamide", ["Oily", "Combination", "Normal"], ["Oiliness", "Dark spots"], [], "moderate", "https://www.nykaa.com/search/result/?q=Plum%202%25%20Niacinamide%20Serum"),
("Plum Green Tea Oil-Free Moisturizer", "moisturizer", 470, "Green tea; verify fragrance on label", ["Oily", "Combination"], ["Oiliness"], ["Fragrance"], "low", "https://www.nykaa.com/search/result/?q=Plum%20Green%20Tea%20Oil%20Free%20Moisturizer"),
# Bioderma / La Roche Posay / Fixderma
("Bioderma Atoderm Creme", "moisturizer", 599, "Glycerin; emollients", ["Dry", "Sensitive", "Normal"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=Bioderma%20Atoderm%20Creme"),
("Fixderma Shadow SPF 50+ Gel", "sunscreen", 450, "UV filters; check current label", ["Oily", "Combination", "Normal"], ["Dark spots", "Fine lines"], [], "low", "https://www.nykaa.com/search/result/?q=Fixderma%20Shadow%20SPF%2050%20Gel"),
("La Roche-Posay Cicaplast Baume B5", "moisturizer", 1500, "Panthenol (B5); madecassoside", ["Dry", "Sensitive", "Normal"], ["Dryness", "Redness"], [], "low", "https://www.nykaa.com/search/result/?q=La%20Roche%20Posay%20Cicaplast%20Baume%20B5"),
]

PRODUCTS = []
for i, row in enumerate(_RAW_PRODUCTS, 1):
    name, category, price, ingredients, skin_types, concerns, avoid_tags, active_level, buy_link = row
    PRODUCTS.append({
        "id": f"product-{i:02d}", "name": name, "brand": name.split()[0], "category": category,
        "price_inr": price, "key_ingredients": ingredients, "skin_types": skin_types,
        "concerns": concerns, "tags": [], "avoid_tags": avoid_tags, "active_level": active_level,
        "why": f"Consider for {', '.join(concerns) if concerns else category}; check the current ingredient label and suitability before buying.",
        "buy_link": buy_link,
    })


def recommend_products(skin_type: str, concerns: list[str], sensitivity: str, avoid: list[str], budget_label: str) -> dict:
    budget_caps = {"Under ₹500": 500, "₹500–₹1,000": 1000, "₹1,000–₹2,000": 2000, "₹2,000+": 5000}
    cap = budget_caps.get(budget_label, 1000)
    cautious = skin_type == "Sensitive" or sensitivity in ("High", "Moderate")
    eligible = []
    for product in PRODUCTS:
        if any(tag in (avoid or []) for tag in product["avoid_tags"]):
            continue
        if cautious and product["active_level"] in ("moderate", "high"):
            continue
        if skin_type not in ("Not sure", "Sensitive") and skin_type not in product["skin_types"]:
            continue
        score = (3 if product["category"] in ("cleanser", "moisturizer", "sunscreen") else 0)
        score += 2 * len(set(product["concerns"]) & set(concerns or []))
        eligible.append({**product, "match_score": score})
    order = {"sunscreen": 0, "moisturizer": 1, "cleanser": 2, "targeted": 3}
    eligible.sort(key=lambda p: (order.get(p["category"], 9), -p["match_score"], p["price_inr"]))
    chosen, total, used_categories = [], 0, set()
    for product in eligible:
        if product["category"] == "targeted" and (cautious or not chosen):
            continue
        if product["category"] in used_categories:
            continue
        if total + product["price_inr"] <= cap:
            chosen.append(product)
            used_categories.add(product["category"])
            total += product["price_inr"]
    return {
        "products": chosen, "total_inr": total, "budget_cap_inr": cap,
        "within_budget": total <= cap, "price_checked": PRICE_CHECKED,
        "source_url": CATALOG_SOURCE, "catalogue_count": len(PRODUCTS),
    }
