"""Optional YouCam AI Look Virtual Try-On client (v2.0)."""
from __future__ import annotations
import time
from typing import Any
from urllib.parse import urlparse
import requests


def _body(response: requests.Response) -> dict[str, Any]:
    try:
        value = response.json()
    except ValueError as exc:
        raise RuntimeError("YouCam VTO returned an unreadable response.") from exc
    if not isinstance(value, dict):
        raise RuntimeError("YouCam VTO returned an unexpected response format.")
    if response.status_code >= 400:
        message = value.get("message") or value.get("error") or value.get("error_code") or f"HTTP {response.status_code}"
        raise RuntimeError(f"YouCam VTO request failed: {str(message)[:180]}")
    return value


def list_look_templates(api_key: str, base_url: str, timeout: int = 20) -> list[dict[str, str]]:
    base = base_url.rstrip("/")
    if not api_key.strip() or urlparse(base).scheme != "https":
        raise RuntimeError("Configure a YouCam API key and HTTPS API base URL first.")
    response = requests.get(f"{base}/s2s/v2.0/task/template/look-vto", headers={"Authorization": f"Bearer {api_key}"}, params={"page_size": 50}, timeout=timeout)
    body = _body(response)
    data = body.get("data", {})
    templates = data.get("templates", []) if isinstance(data, dict) else []
    return [{"id": str(t.get("id", "")), "title": str(t.get("title") or t.get("category_name") or t.get("id") or "Look"), "thumb": str(t.get("thumb", ""))} for t in templates if isinstance(t, dict) and t.get("id")]


def _upload_image(api_key: str, base: str, image_bytes: bytes, filename: str, mime: str, timeout: int) -> str:
    response = requests.post(f"{base}/s2s/v2.0/file", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"files": [{"content_type": mime, "file_name": filename, "file_size": len(image_bytes)}]}, timeout=timeout)
    body = _body(response)
    files = body.get("data", {}).get("files", [])
    if not files or not isinstance(files[0], dict):
        raise RuntimeError("YouCam did not return an upload destination for the VTO photo.")
    item = files[0]
    file_id = item.get("file_id")
    requests_info = item.get("requests", [])
    upload = requests_info[0] if requests_info and isinstance(requests_info[0], dict) else {}
    upload_url = upload.get("url")
    if not file_id or not upload_url:
        raise RuntimeError("YouCam VTO File API response was missing upload details.")
    upload_headers = dict(upload.get("headers", {}))
    upload_headers.setdefault("Content-Type", mime)
    uploaded = requests.request(str(upload.get("method", "PUT")).upper(), upload_url, headers=upload_headers, data=image_bytes, timeout=timeout)
    if uploaded.status_code >= 400:
        raise RuntimeError("The VTO photo upload failed; try another JPG or PNG.")
    return str(file_id)


def run_look_vto(api_key: str, base_url: str, image_bytes: bytes, filename: str, mime: str, template_id: str, timeout_seconds: int = 120, poll_interval: float = 2.5) -> dict[str, str]:
    """Upload a user-consented selfie, run AI Look VTO, and return the rendered image URL."""
    base = base_url.rstrip("/")
    if not api_key.strip() or urlparse(base).scheme != "https":
        raise RuntimeError("Configure a YouCam API key and HTTPS API base URL first.")
    file_id = _upload_image(api_key, base, image_bytes, filename, mime, 30)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    started = requests.post(f"{base}/s2s/v2.0/task/look-vto", headers=headers, json={"src_file_id": file_id, "template_id": template_id}, timeout=(10, 30))
    start_body = _body(started)
    task_id = start_body.get("data", {}).get("task_id")
    if not task_id:
        raise RuntimeError("YouCam did not return a task ID for the look preview.")
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        time.sleep(min(poll_interval, max(0.1, deadline - time.monotonic())))
        response = requests.get(f"{base}/s2s/v2.0/task/look-vto/{task_id}", headers={"Authorization": f"Bearer {api_key}"}, timeout=(10, 30))
        body = _body(response)
        data = body.get("data", {}) if isinstance(body.get("data"), dict) else {}
        state = str(data.get("task_status", body.get("task_status", ""))).lower()
        if state == "success":
            results = data.get("results", {})
            url = results.get("url") if isinstance(results, dict) else None
            if not url:
                raise RuntimeError("The VTO task succeeded but no rendered image URL was returned.")
            return {"task_id": str(task_id), "image_url": str(url)}
        if state in {"error", "failed", "failure"}:
            raise RuntimeError("YouCam could not render this look. Try a clear, front-facing photo with the full face visible.")
    raise RuntimeError("The virtual look preview timed out. You can retry later.")
