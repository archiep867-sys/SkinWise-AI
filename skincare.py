"""SkinWise routine helpers.

This module deliberately avoids diagnosis. API fields are retained as raw data unless
their meaning is explicitly mapped from the user's official YouCam API schema.
"""
from typing import Any


def demo_analysis(skin_type, concerns):
    labels = list(concerns or ["General skin maintenance"])
    return {
        "metrics": [{"label": "Demo preview", "value": "Not measured", "description": "No skin score was computed."}],
        "summary": "Illustrative preview for " + ", ".join(labels) + ". The uploaded photo was not analyzed.",
        "concerns": labels,
        "raw_response": None,
    }


def parse_analysis(raw: Any) -> dict:
    """Normalize documented YouCam result JSON while preserving the original payload.

    The exact response may vary by API version/format, so this recursively reads numeric
    fields whose names match the documented skin-analysis actions and never invents missing scores.
    """
    if not isinstance(raw, dict):
        raise TypeError("Expected a JSON object from YouCam")

    data = raw.get("result") if isinstance(raw.get("result"), dict) else raw
    if isinstance(data.get("data"), dict):
        inner = data["data"]
        if any(k in inner for k in ("score_info", "results", "scores", "acne", "skin_type")):
            data = inner

    known_labels = {
        "acne": "Acne", "age_spot": "Spots / pigmentation", "dark_circle_v2": "Dark circles",
        "dark_circle": "Dark circles", "eye_bag": "Eye bags", "eye_bags": "Eye bags",
        "firmness": "Firmness", "moisture": "Moisture", "oiliness": "Oiliness",
        "pore": "Pores", "pores": "Pores", "radiance": "Radiance", "redness": "Redness",
        "skin_type": "Skin type", "texture": "Texture", "wrinkle": "Wrinkles",
        "tear_trough": "Tear trough", "droopy_upper_eyelid": "Upper eyelid", "droopy_lower_eyelid": "Lower eyelid",
        "hd_acne": "Acne", "hd_age_spot": "Spots / pigmentation", "hd_dark_circle": "Dark circles",
        "hd_eye_bag": "Eye bags", "hd_firmness": "Firmness", "hd_moisture": "Moisture",
        "hd_oiliness": "Oiliness", "hd_pore": "Pores", "hd_radiance": "Radiance",
        "hd_redness": "Redness", "hd_skin_type": "Skin type", "hd_texture": "Texture", "hd_wrinkle": "Wrinkles",
        "hd_tear_trough": "Tear trough", "score": "Overall score", "overall_score": "Overall score",
    }
    found: dict[str, Any] = {}

    def walk(obj: Any, parent: str = "") -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                normalized = str(key).lower().replace("-", "_").replace(" ", "_")
                if normalized in known_labels and isinstance(value, (int, float)) and not isinstance(value, bool):
                    found[normalized] = value
                elif normalized in known_labels and isinstance(value, dict):
                    for subkey in ("score", "value", "result", "severity"):
                        candidate = value.get(subkey)
                        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                            found[normalized] = candidate
                            break
                walk(value, normalized)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, parent)

    walk(data)
    metrics = []
    for key, value in found.items():
        label = known_labels[key]
        metrics.append({
            "label": label,
            "value": value,
            "description": "Score returned by YouCam. Interpret using the API version's score definition; this is not a diagnosis.",
            "field": key,
        })
    # Do not list the same concern twice if both alias and nested result keys exist.
    unique = {}
    for metric in metrics:
        unique[metric["label"]] = metric
    metrics = list(unique.values())
    concern_metrics = [m for m in metrics if m["label"] != "Overall score" and isinstance(m["value"], (int, float))]
    top = sorted(concern_metrics, key=lambda m: m["value"], reverse=True)[:3]
    if top:
        top_summary = ", ".join(f"{m['label']} ({m['value']:g})" for m in top)
        summary = "Top returned concern scores: " + top_summary + ". These are the highest numeric values in the response, not a medical severity ranking. Check the API's score definition before interpreting them."
    else:
        summary = "YouCam returned a response, but no supported numeric concern scores were found in the expected fields. Inspect the raw response and update the mapping to match your account's API schema."
    concerns = [m["label"] for m in top]
    if not concerns:
        for key in ("concerns", "skin_concerns", "results"):
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, list):
                concerns = [str(item.get("name", item.get("label", "")) if isinstance(item, dict) else item) for item in value[:3]]
                concerns = [item for item in concerns if item]
                if concerns:
                    break
    return {"summary": summary, "concerns": concerns, "metrics": metrics, "raw_response": raw}


def build_routine(analysis, budget, skin_type, concerns, sensitivity, style, avoid=None):
    focus = set(concerns or analysis.get("concerns", []))
    avoid = set(avoid or [])
    sensitive = sensitivity == "High" or skin_type == "Sensitive"
    very_cautious = sensitive or "Known personal trigger (unspecified)" in avoid
    morning = [
        {"step": 1, "name": "Gentle cleanser", "why": "Use a mild, non-stripping cleanser. If your skin feels dry in the morning, rinsing with water may be enough."},
        {"step": 2, "name": "Moisturizer", "why": "Choose a comfortable, preferably fragrance-free moisturizer. A lighter texture may feel better on oily skin; a richer cream may suit dry skin."},
        {"step": 3, "name": "Broad-spectrum SPF 30+ sunscreen", "why": "Use as the final morning step and reapply as directed when outdoors. Sun protection helps reduce UV damage and worsening of dark spots."},
    ]
    evening = [
        {"step": 1, "name": "Gentle cleanser", "why": "Remove sunscreen, makeup, sweat, and daily buildup without scrubbing."},
        {"step": 2, "name": "Moisturizer", "why": "Support comfort and the skin barrier before considering optional active ingredients."},
    ]
    if style.startswith("Balanced") and not very_cautious:
        if "Acne / breakouts" in focus and "Exfoliating acids" not in avoid and "Retinoids" not in avoid:
            evening.insert(1, {"step": 2, "name": "Optional acne-focused product", "why": "Consider a single suitable over-the-counter product only if tolerated; follow its label and avoid starting multiple actives together."})
        elif "Dark spots" in focus and "Exfoliating acids" not in avoid:
            morning.insert(2, {"step": 3, "name": "Optional niacinamide product", "why": "Consider only if tolerated. Sunscreen remains important for preventing dark spots from worsening."})
    if "Fragrance" in avoid or "Essential oils" in avoid or very_cautious:
        for step in morning + evening:
            step["why"] += " Prefer fragrance-free formulas and check the full ingredient list for personal triggers."
    if sensitive:
        evening = [
            {"step": 1, "name": "Gentle cleanser", "why": "Avoid scrubs, fragrance, and hot water; skip cleansing in the morning if it increases dryness."},
            {"step": 2, "name": "Barrier-supporting moisturizer", "why": "Keep the routine simple and pause products that sting or worsen redness."},
        ]
        morning = [
            {"step": 1, "name": "Gentle rinse or cleanser", "why": "Choose the gentlest option your skin comfortably tolerates."},
            {"step": 2, "name": "Barrier-supporting moisturizer", "why": "Prefer a simple, fragrance-free formula if tolerated."},
            {"step": 3, "name": "Broad-spectrum SPF 30+ sunscreen", "why": "Choose a sunscreen that does not irritate you; sun protection helps prevent UV damage."},
        ]
    next_steps = [
        "Patch-test new products and introduce only one new product at a time.",
        "Keep the routine consistent before deciding whether it suits you.",
        "Seek advice from a qualified dermatologist for persistent, painful, severe, or worsening symptoms.",
    ]
    if very_cautious:
        next_steps.insert(0, "Keep the routine basic while skin is reactive; avoid adding new actives without professional advice.")
    if budget == "Under ₹500":
        next_steps.append("Prioritize a cleanser (if needed), moisturizer, and sunscreen; buy within your budget and do not feel you need every category.")
    else:
        next_steps.append("A higher price does not guarantee better results; prioritize tolerability, ingredients, and consistency.")
    return {
        "morning": morning,
        "evening": evening,
        "next_steps": next_steps,
        "budget_note": budget,
        "focus_areas": sorted(focus),
        "avoided_categories": sorted(avoid),
    }


def make_budget_guide(budget, skin_type, sensitivity):
    notes = {
        "Under ₹500": [
            ("Priority 1", "Choose a sunscreen you can use consistently; check the label and local price."),
            ("Priority 2", "Use one simple moisturizer suited to how your skin feels."),
            ("Priority 3", "A gentle cleanser is useful if you need it; avoid buying several actives at once."),
        ],
        "₹500–₹1,000": [
            ("Core", "Aim for a sunscreen and moisturizer first, then add a gentle cleanser if needed."),
            ("Optional", "Only consider one targeted product after the basics are comfortable."),
            ("Save", "Compare cost per use and ingredient lists; no brand or price guarantees results."),
        ],
        "₹1,000–₹2,000": [
            ("Core", "Build around sunscreen, moisturizer, and a gentle cleanser that suits your skin."),
            ("Optional", "Keep room for one targeted product only if your skin tolerates the basics."),
            ("Avoid waste", "Do not buy several products that target the same concern at once."),
        ],
        "₹2,000+": [
            ("Core", "Spending more is optional; reliable basics still matter most."),
            ("Optional", "Prioritize formula suitability and evidence over packaging or premium claims."),
            ("Save", "Keep a simple routine rather than filling every step with a separate product."),
        ],
    }
    return [{"category": a, "guidance": b} for a, b in notes[budget]]


def routine_coach_reply(question, sensitivity, skin_type, avoid, budget):
    q = question.lower()
    cautious = sensitivity == "High" or skin_type == "Sensitive" or "Known personal trigger (unspecified)" in avoid
    if any(term in q for term in ["irritat", "burn", "sting", "reaction", "rash"]):
        return "Stop the newest product for now and keep the routine gentle. If symptoms are severe, spreading, painful, involve swelling or breathing difficulty, or do not settle, seek appropriate medical care. I can't diagnose a reaction."
    if any(term in q for term in ["introduc", "start", "new product", "patch test"]):
        return "Patch-test according to the product label, introduce one new product at a time, and start less frequently than the label's maximum if you are unsure. Do not combine several new actives at once. " + ("Because you selected a sensitive/high-sensitivity profile, keep the routine basic and consider professional advice before adding actives." if cautious else "Stop if it causes persistent irritation.")
    if any(term in q for term in ["budget", "cheap", "cost", "money", "₹", "rupee"]):
        return f"Your selected budget is {budget}. Prioritize sunscreen and moisturizer, then a gentle cleanser if needed. Skip optional serums until the basics are affordable and comfortable."
    if any(term in q for term in ["sunscreen", "spf", "sun"]):
        return "Use a broad-spectrum SPF 30+ sunscreen as directed on its label and reapply as directed, especially outdoors. Choose one you can apply consistently and tolerate; it helps limit UV damage and dark spots worsening."
    if any(term in q for term in ["acne", "breakout", "pimple"]):
        return "Keep cleansing gentle, avoid scrubbing or picking, and introduce at most one targeted over-the-counter product at a time. Painful, scarring, persistent, or worsening acne deserves advice from a qualified dermatologist."
    if any(term in q for term in ["dark spot", "pigment", "spot"]):
        return "Daily sun protection is an important first step because UV exposure can worsen dark spots. Avoid aggressive exfoliation, introduce any optional product slowly, and seek professional advice for changing or concerning spots."
    return "A useful rule is to keep the routine simple: gentle cleansing as needed, moisturizer, and daytime sunscreen. Add one change at a time, patch-test, and avoid products that irritate you. I provide general education, not diagnosis."
