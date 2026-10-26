from youcam_client import DEFAULT_ACTIONS, _task_state, _extract_task_id, _find_result_payload, YouCamError


def test_default_actions_are_sd_only():
    assert DEFAULT_ACTIONS
    assert all(not action.startswith("hd_") for action in DEFAULT_ACTIONS)


def test_task_state_reads_nested_status():
    assert _task_state({"data": {"task_status": "success"}}) == "success"
    assert _task_state({"data": {"task_status": "running"}}) == "running"


def test_extract_task_id_from_documented_response():
    assert _extract_task_id({"status": 200, "data": {"task_id": "abc123"}}) == "abc123"


def test_extract_task_id_missing_is_clear_error():
    try:
        _extract_task_id({"status": 200, "data": {}})
    except YouCamError as exc:
        assert exc.category == "bad_response"
    else:
        raise AssertionError("Expected missing task ID to raise YouCamError")


def test_find_result_payload_handles_data_result():
    result = _find_result_payload({"data": {"result": {"acne": 42}}})
    assert result == {"acne": 42}
