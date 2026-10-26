"""YouCam Skin Analysis v2.1 client using File API upload + task polling.

Endpoint paths and task fields follow the official Perfect Corp developer docs.
The API host is configurable because account/region routing can vary.
"""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import requests

DEFAULT_BASE_URL = "https://yce-api-01.makeupar.com"
DEFAULT_ACTIONS = [
    "acne", "age_spot", "dark_circle_v2", "eye_bag", "firmness", "moisture",
    "oiliness", "pore", "radiance", "redness", "skin_type", "texture", "wrinkle",
]


class YouCamError(RuntimeError):
    def __init__(self, message: str, category: str = "unknown"):
        super().__init__(message)
        self.category = category


def _json(response: requests.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise YouCamError("YouCam returned an unreadable response. Please retry shortly.", "bad_response") from exc
    if not isinstance(body, dict):
        raise YouCamError("YouCam returned an unexpected response format.", "bad_response")
    return body


def _friendly_http_error(response: requests.Response, body: dict[str, Any] | None = None) -> YouCamError:
    body = body or {}
    nested = body.get("data") if isinstance(body.get("data"), dict) else {}
    text = str(body.get("message") or body.get("error") or body.get("detail") or body.get("error_code") or nested.get("message") or nested.get("error") or nested.get("error_code") or "").lower()
    code = response.status_code
    if code in (401, 403):
        return YouCamError("YouCam rejected the API key or account permissions. Check the key and account region.", "auth")
    if code == 402 or "unit" in text or "credit" in text or "quota" in text:
        return YouCamError("Your YouCam API units may be exhausted. Check the API Console balance before retrying.", "quota")
    if code == 429:
        return YouCamError("YouCam is rate-limiting requests. Wait a little before trying again.", "rate_limit")
    if code in (400, 422):
        if any(term in text for term in ("face", "no_face", "face_detect")):
            return YouCamError("We couldn't detect a usable face. Face the camera directly, remove glasses if possible, and try a clear photo in even light.", "no_face")
        if any(term in text for term in ("blur", "light", "quality", "image")):
            return YouCamError("The photo may not meet image-quality requirements. Face a window, avoid filters, remove glasses if possible, and upload a sharp, front-facing photo.", "image_quality")
        return YouCamError("YouCam couldn't process this photo or request. Try a clear JPG/PNG with one face, facing forward, in even lighting.", "invalid_request")
    if code >= 500:
        return YouCamError("YouCam is temporarily unavailable. Please wait and try again.", "provider_error")
    return YouCamError(f"YouCam returned HTTP {code}. Check the API Console and try again.", "http_error")


def _extract_task_id(body: dict[str, Any]) -> str:
    data = body.get("data", {})
    task_id = data.get("task_id") if isinstance(data, dict) else None
    if not task_id:
        task_id = body.get("task_id")
    if not task_id:
        raise YouCamError("YouCam did not return a task ID. Check the API response and account configuration.", "bad_response")
    return str(task_id)


def _task_state(body: dict[str, Any]) -> str:
    data = body.get("data", {})
    candidates = [
        body.get("task_status"), body.get("taskStatus"), body.get("state"),
        data.get("task_status") if isinstance(data, dict) else None,
        data.get("taskStatus") if isinstance(data, dict) else None,
        data.get("state") if isinstance(data, dict) else None,
        data.get("status") if isinstance(data, dict) else None,
    ]
    for value in candidates:
        if isinstance(value, str) and value.lower() in {"running", "queued", "pending", "success", "succeeded", "error", "failed", "failure"}:
            return value.lower()
    return "unknown"


def _find_result_payload(body: dict[str, Any]) -> dict[str, Any]:
    """Find JSON result payload without inventing field names or values."""
    data = body.get("data")
    if isinstance(data, dict):
        for key in ("result", "results", "task_result", "result_json", "output"):
            value = data.get(key)
            if isinstance(value, dict):
                return value
        # Some JSON-format responses put metrics directly inside data.
        if any(k in data for k in DEFAULT_ACTIONS) or any(k in data for k in ("score_info", "skin_analysis", "scores")):
            return data
    for key in ("result", "results", "task_result", "output"):
        value = body.get(key)
        if isinstance(value, dict):
            return value
    return body


def analyze_skin(
    api_key: str,
    image_bytes: bytes,
    filename: str,
    content_type: str,
    base_url: str = DEFAULT_BASE_URL,
    actions: list[str] | None = None,
    timeout_seconds: int = 120,
    poll_interval_seconds: float = 3.0,
) -> dict[str, Any]:
    """Upload image, create v2.1 task, poll until terminal state, and return result JSON."""
    if not api_key.strip():
        raise YouCamError("Add YOUCAM_API_KEY in your environment settings.", "not_configured")
    base = base_url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.netloc:
        raise YouCamError("The YouCam API base URL must be a valid HTTPS URL.", "configuration")
    headers = {"Authorization": f"Bearer {api_key.strip()}"}
    if content_type in {"image/jpeg", "image/jpg"}:
        mime = "image/jpg"  # YouCam File API examples use image/jpg for JPEG uploads.
    elif content_type == "image/png":
        mime = "image/png"
    else:
        mime = "image/jpg"
    session = requests.Session()

    # 1. Request an upload URL and file_id from File API.
    file_resp = session.post(
        f"{base}/s2s/v2.0/file",
        headers={**headers, "Content-Type": "application/json"},
        json={"files": [{"content_type": mime, "file_name": filename, "file_size": len(image_bytes)}]},
        timeout=(10, 30),
    )
    if file_resp.status_code >= 400:
        try:
            err_body = _json(file_resp)
        except YouCamError:
            err_body = {}
        raise _friendly_http_error(file_resp, err_body)
    file_body = _json(file_resp)
    files = file_body.get("data", {}).get("files", [])
    if not files or not isinstance(files[0], dict):
        raise YouCamError("YouCam did not provide an upload URL. Check File API access and account region.", "bad_response")
    file_item = files[0]
    file_id = file_item.get("file_id")
    requests_list = file_item.get("requests", [])
    upload_request = requests_list[0] if requests_list and isinstance(requests_list[0], dict) else {}
    upload_url = upload_request.get("url")
    if not file_id or not upload_url:
        raise YouCamError("YouCam's File API response is missing file_id or upload URL.", "bad_response")

    # 2. Upload bytes to the signed URL. Do not send the API key to object storage.
    upload_headers = dict(upload_request.get("headers", {}))
    upload_headers.setdefault("Content-Type", mime)
    method = str(upload_request.get("method", "PUT")).upper()
    upload_resp = session.request(method, upload_url, headers=upload_headers, data=image_bytes, timeout=(10, 45))
    if upload_resp.status_code >= 400:
        raise YouCamError("The image upload did not complete. Please retry with a smaller JPG or PNG.", "upload_failed")

    # 3. Start asynchronous Skin Analysis v2.1 task (SD features only; HD/SD cannot be mixed).
    task_body = {
        "src_file_id": file_id,
        "dst_actions": actions or DEFAULT_ACTIONS,
        "format": "json",
        "pf_camera_kit": False,
    }
    task_resp = session.post(
        f"{base}/s2s/v2.1/task/skin-analysis",
        headers={**headers, "Content-Type": "application/json"},
        json=task_body,
        timeout=(10, 30),
    )
    if task_resp.status_code >= 400:
        try:
            err_body = _json(task_resp)
        except YouCamError:
            err_body = {}
        raise _friendly_http_error(task_resp, err_body)
    task_id = _extract_task_id(_json(task_resp))

    # 4. Poll until terminal state or timeout. The API docs recommend polling about every 10 sec;
    # shorter interval here keeps hackathon demo feedback responsive while remaining configurable.
    deadline = time.monotonic() + timeout_seconds
    last_body: dict[str, Any] = {}
    while time.monotonic() < deadline:
        time.sleep(min(poll_interval_seconds, max(0.1, deadline - time.monotonic())))
        status_resp = session.get(
            f"{base}/s2s/v2.1/task/skin-analysis/{task_id}",
            headers=headers,
            timeout=(10, 30),
        )
        if status_resp.status_code >= 400:
            try:
                err_body = _json(status_resp)
            except YouCamError:
                err_body = {}
            raise _friendly_http_error(status_resp, err_body)
        last_body = _json(status_resp)
        state = _task_state(last_body)
        if state in {"success", "succeeded"}:
            result = _find_result_payload(last_body)
            return {"task_id": task_id, "task_status": state, "result": result, "raw_response": last_body}
        if state in {"error", "failed", "failure"}:
            nested = last_body.get("data", {}) if isinstance(last_body.get("data"), dict) else {}
            message = str(last_body.get("message") or nested.get("message") or nested.get("error_code") or nested.get("error", ""))
            raise YouCamError(
                "YouCam could not analyze this photo. Try facing a window, looking straight at the camera, removing glasses if possible, and using a sharp photo."
                + (f" Provider detail: {message[:180]}" if message else ""),
                "analysis_failed",
            )
    raise YouCamError("Skin analysis took too long. Your photo may still be processing; wait briefly and try again.", "timeout")
