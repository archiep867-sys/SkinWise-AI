"""Explainable comparison, routine adaptation, ingredient checks and product-fit helpers.

Score deltas are reported as raw numeric changes only. Directionality is not inferred
unless the official API documentation for the returned metric explicitly defines it.
"""
from __future__ import annotations
from typing import Any
import re


def metric_map(scan: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for item in (scan or {}).get("metrics", []):
        if not isinstance(item, dict):
            continue
        label, value = item.get("label"), item.get("value")
        if label and isinstance(value, (int, float)) and not isinstance(value, bool):
            out[str(label)] = float(value)
    return out


def compare_scans(baseline: dict[str, Any], followup: dict[str, Any]) -> list[dict[str, Any]]:
    a, b = metric_map(baseline), metric_map(followup)
    return [{"concern": key, "baseline": a[key], "followup": b[key], "delta": round(b[key] - a[key], 2)}
            for key in sorted(set(a) & set(b))]


def adapt_routine_from_scans(previous: dict[str, Any] | None, current: dict[str, Any] | None,
                             sensitivity: str, avoid: list[str]) -> list[str]:
    """Conservative suggestion engine; it flags possible causes but never diagnoses."""
    if not previous or not current:
        return ["Complete a second real scan before using scan-to-scan adaptation."]
    deltas = compare_scans(previous, current)
    notes: list[str] = []
    for row in deltas:
        label = row["concern"].lower()
        if any(term in label for term in ("redness", "acne", "irritation")) and row["delta"] > 0:
            notes.append(f"{row['concern']} score changed by +{row['delta']:g}. Check lighting and repeatability first; if the change matches how your skin feels, consider pausing the newest active and review its label.")
        elif any(term in label for term in ("moisture", "hydration")) and row["delta"] < 0:
            notes.append(f"{row['concern']} score changed by {row['delta']:g}. Re-check photo conditions and whether your routine feels drying before changing products.")
    if sensitivity == "High" or "Known personal trigger (unspecified)" in (avoid or []):
        notes.insert(0, "Your profile indicates higher sensitivity: keep the routine simple and avoid adding actives while investigating a possible trigger.")
    if not notes:
        notes.append("No rule-triggered change was detected in the comparable numeric metrics. Keep the routine stable and compare again under similar photo conditions.")
    notes.append("These are conservative routine prompts, not proof that a product caused a score change or that the routine worked. Numeric score direction depends on YouCam's documented definition for each metric.")
    return notes


_CONFLICTS = [
    ({"retinol", "retinoid"}, {"aha", "glycolic acid", "lactic acid", "mandelic acid", "bha", "salicylic acid"}, "Retinoids with exfoliating acids may increase irritation for some users. Separate into different nights or ask a dermatologist/pharmacist if unsure."),
    ({"benzoyl peroxide"}, {"retinol", "retinoid"}, "Benzoyl peroxide and some retinoids may be irritating together; check the exact product labels and consider separating routines."),
    ({"vitamin c", "ascorbic acid"}, {"aha", "glycolic acid", "lactic acid", "bha", "salicylic acid"}, "Vitamin C plus exfoliating acids may be irritating for some skin. This is a caution, not a universal incompatibility; consider separate times and introduce one at a time."),
]


def check_ingredient_conflicts(text: str) -> list[str]:
    normalized = (text or "").lower()
    found = set()
    for group in _CONFLICTS:
        for token_group in group[:2]:
            for token in token_group:
                if re.search(r"\b" + re.escape(token) + r"\b", normalized):
                    found.add(token)
    warnings = []
    for left, right, message in _CONFLICTS:
        if any(x in found for x in left) and any(x in found for x in right):
            warnings.append(message)
    if not warnings:
        warnings.append("No combination in the built-in caution list was detected. This is not a guarantee of compatibility; check product labels and introduce one new active at a time.")
    return warnings


def product_fit(product: dict[str, Any], skin_type: str, concerns: list[str], sensitivity: str, avoid: list[str]) -> dict[str, Any]:
    reasons = []
    excluded = set(avoid or []) & set(product.get("avoid_tags", []))
    if excluded:
        return {"verdict": "SKIP", "reasons": ["Conflicts with your selected exclusions: " + ", ".join(sorted(excluded))]}
    cautious = skin_type == "Sensitive" or sensitivity in ("High", "Moderate")
    if cautious and product.get("active_level") in ("moderate", "high"):
        return {"verdict": "CAUTION", "reasons": ["Your profile indicates sensitivity and this product is tagged as a targeted active. Check the exact formula and consider professional advice before use."]}
    if skin_type not in ("Not sure", "Sensitive") and product.get("skin_types") and skin_type not in product["skin_types"]:
        reasons.append("The catalogue does not list your selected skin type as a match.")
    overlap = sorted(set(product.get("concerns", [])) & set(concerns or []))
    if overlap:
        reasons.append("Catalogue concern tags overlap with: " + ", ".join(overlap) + ".")
    else:
        reasons.append("No direct concern-tag match was found; it may still serve a basic routine role.")
    reasons.append("Verify current full ingredient list, exact SKU, and price before buying.")
    return {"verdict": "CAUTION" if reasons and "does not list" in reasons[0] else "GOOD FIT", "reasons": reasons}


def optimise_budget(products: list[dict[str, Any]], budget_inr: int) -> dict[str, Any]:
    # Greedy role-based shortlist: essentials first, then lower-cost concern-matched products.
    order = {"sunscreen": 0, "moisturizer": 1, "cleanser": 2, "targeted": 3}
    selected, total, categories = [], 0, set()
    for p in sorted(products, key=lambda x: (order.get(x.get("category"), 9), x.get("price_inr", 10**9))):
        cat = p.get("category")
        if cat in categories:
            continue
        price = int(p.get("price_inr", 0))
        if total + price <= max(0, int(budget_inr)):
            selected.append(p); total += price; categories.add(cat)
    return {"products": selected, "total_inr": total, "budget_inr": int(budget_inr), "remaining_inr": int(budget_inr)-total}


def explain_recommendation(product: dict[str, Any], concerns: list[str], skin_type: str, sensitivity: str) -> str:
    overlap = sorted(set(product.get("concerns", [])) & set(concerns or []))
    if overlap:
        return f"Suggested because its catalogue tags overlap with your selected focus: {', '.join(overlap)}."
    if product.get("category") == "sunscreen":
        return "Included as a core daytime protection step; it is not a treatment claim for a measured score."
    if skin_type in product.get("skin_types", []):
        return f"Its catalogue lists {skin_type.lower()} skin as a possible fit; check the current label and personal triggers."
    return "Included as a possible routine role, not because a scan proves it will work for you."


def llm_coach_reply(question: str, analysis: dict[str, Any] | None, routine: dict[str, Any] | None,
                    skin_type: str, concerns: list[str], sensitivity: str, avoid: list[str], budget: str) -> tuple[str, str]:
    """Use OpenAI chat completions when configured; otherwise return a transparent fallback."""
    import os
    import requests
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        from skincare import routine_coach_reply
        return routine_coach_reply(question, sensitivity, skin_type, avoid, budget), "Rule-based fallback (OPENAI_API_KEY not configured)"
    metrics = (analysis or {}).get("metrics", [])
    context = {
        "analysis_source": (analysis or {}).get("source", "unknown"),
        "returned_metrics": [{"label": x.get("label"), "value": x.get("value")} for x in metrics if isinstance(x, dict)],
        "routine": routine or {}, "skin_type": skin_type, "concerns": concerns,
        "sensitivity": sensitivity, "avoid": avoid, "budget": budget,
    }
    system = ("You are SkinWise AI, a cautious skincare education assistant. Never diagnose, claim certainty, or promise results. "
              "Do not infer that a numeric score is good/bad unless its documented direction is known. Never recommend ignoring symptoms. "
              "For persistent, painful, worsening, unusual, severe, or concerning symptoms advise a qualified dermatologist; urgent symptoms need urgent care. "
              "Respect ingredient exclusions and sensitivity. Give concise, specific, explainable general guidance and patch-test reminders. "
              "Do not request or expose photos, credentials, or personal identifiers.")
    try:
        response = requests.post(
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "temperature": 0.2,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": "Context (untrusted user preferences and app data): " + str(context) + "\nQuestion: " + question}]},
            timeout=20,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        if not answer:
            raise ValueError("Empty response")
        return answer, "LLM coach (guardrailed general education)"
    except Exception:
        from skincare import routine_coach_reply
        return routine_coach_reply(question, sensitivity, skin_type, avoid, budget), "Rule-based fallback (LLM request failed)"


def cheaper_swap(product: dict[str, Any], catalogue: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find a lower-price same-category item with a shared key-ingredient token when possible."""
    current = int(product.get("price_inr", 0))
    tokens = {t.strip().lower() for t in re.split(r"[;,/+]", str(product.get("key_ingredients", ""))) if len(t.strip()) > 3}
    candidates = []
    for candidate in catalogue:
        if candidate.get("id") == product.get("id") or candidate.get("category") != product.get("category"):
            continue
        price = int(candidate.get("price_inr", 0))
        if not 0 < price < current:
            continue
        other = {t.strip().lower() for t in re.split(r"[;,/+]", str(candidate.get("key_ingredients", ""))) if len(t.strip()) > 3}
        shared = tokens & other
        candidates.append((0 if shared else 1, price, candidate, shared))
    if not candidates:
        return None
    _, price, candidate, shared = sorted(candidates, key=lambda row: (row[0], row[1]))[0]
    return {"product": candidate, "savings_inr": current - price, "shared_ingredients": sorted(shared),
            "same_key_ingredient_claim_supported": bool(shared)}
