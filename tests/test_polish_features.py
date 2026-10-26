from datetime import date
from polish_features import photo_capture_tips, climate_season_guidance, build_report_pdf


def test_photo_capture_tips_cover_lighting_angle_distance():
    text = " ".join(photo_capture_tips()).lower()
    assert "lighting" in text
    assert "angle" in text
    assert "distance" in text


def test_mumbai_monsoon_guidance_mentions_sunscreen_and_humidity():
    result = climate_season_guidance("Hot / humid", month=7, location="Mumbai")
    assert "Monsoon" in result["season"]
    assert any("sunscreen" in tip.lower() for tip in result["tips"])
    assert "does not fetch live weather" in result["disclaimer"]


def test_general_climate_guidance_is_available():
    result = climate_season_guidance("Cold / dry", month=1, location="General")
    assert result["tips"]


def test_pdf_report_is_valid_pdf_bytes():
    data = build_report_pdf({
        "date": date.today().isoformat(), "source": "Demo",
        "profile": {"skin_type": "Combination", "concerns": ["Dryness"], "climate": "Hot / humid"},
        "routine": {"morning": [{"step": 1, "name": "Cleanser", "why": "Gentle daily cleanse"}], "evening": []},
        "climate_guidance": climate_season_guidance("Hot / humid", month=7, location="Mumbai"),
        "progress": {"streak": 2, "days_this_week": 3, "steps_completed": 5, "steps_total": 7},
        "note": "Keep it simple & gentle",
    })
    assert data.startswith(b"%PDF-")
    assert len(data) > 500
