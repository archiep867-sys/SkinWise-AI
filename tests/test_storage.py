from storage import add_journal_entry, clear_all_user_data, get_checkins, get_journal_entries, save_checkins


def test_clear_all_user_data_removes_journal_and_checkins(tmp_path):
    db = tmp_path / "test.db"
    add_journal_entry({"date": "2026-10-26", "note": "test"}, db_path=db)
    save_checkins("2026-10-26", ["Cleanser"], ["Cleanser", "Moisturizer"], db_path=db)
    assert get_journal_entries(db_path=db)
    assert get_checkins(db_path=db)

    clear_all_user_data(db_path=db)

    assert get_journal_entries(db_path=db) == []
    assert get_checkins(db_path=db) == []


def test_scan_and_routine_persistence(tmp_path):
    from storage import save_scan, get_scans, save_routine, get_routines, clear_all_user_data
    db = tmp_path / "skinwise.sqlite"
    save_scan({"date": "2026-10-26", "source": "YouCam", "concerns": ["Acne"]}, db)
    save_routine({"date": "2026-10-26", "profile": {"budget": "Under ₹500"}}, db)
    assert get_scans(db)[0]["concerns"] == ["Acne"]
    assert get_routines(db)[0]["profile"]["budget"] == "Under ₹500"
    clear_all_user_data(db)
    assert get_scans(db) == []
    assert get_routines(db) == []
