from storage import clear_all_user_data, get_profile, save_profile, save_checkins, get_checkins


def test_profile_persists_and_is_cleared_with_user_data(tmp_path):
    db = tmp_path / "skinwise-test.db"
    profile = {"skin_type": "Sensitive", "allergies": "fragrance", "climate": "Hot / humid"}
    save_profile(profile, db)
    assert get_profile(db) == profile
    clear_all_user_data(db)
    assert get_profile(db) == {}


def test_checkins_persist_for_streak_and_weekly_summary(tmp_path):
    db = tmp_path / "skinwise-test.db"
    save_checkins("2026-10-25", ["Cleanser"], ["Cleanser", "Moisturizer"], db)
    rows = get_checkins(db)
    assert {r["step_name"]: r["completed"] for r in rows} == {"Cleanser": 1, "Moisturizer": 0}
