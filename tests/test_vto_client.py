from unittest.mock import Mock
import pytest
from vto_client import list_look_templates, _body


def test_list_look_templates_maps_official_fields(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = {"status": 200, "data": {"templates": [
        {"id": "look_1", "title": "Everyday", "thumb": "https://example.com/look.jpg"},
        {"id": "look_2", "category_name": "Party"},
        {"title": "Missing ID"},
    ]}}
    monkeypatch.setattr("vto_client.requests.get", lambda *args, **kwargs: response)
    result = list_look_templates("test-key", "https://example.com")
    assert result == [
        {"id": "look_1", "title": "Everyday", "thumb": "https://example.com/look.jpg"},
        {"id": "look_2", "title": "Party", "thumb": ""},
    ]


def test_vto_requires_https_base_url():
    with pytest.raises(RuntimeError, match="HTTPS"):
        list_look_templates("test-key", "http://example.com")


def test_vto_response_http_error_is_friendly():
    response = Mock(status_code=401)
    response.json.return_value = {"message": "bad token"}
    with pytest.raises(RuntimeError, match="bad token"):
        _body(response)
