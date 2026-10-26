"""Lightweight photo preflight checks; provider analysis remains authoritative for face detection."""
from io import BytesIO
from PIL import Image, ImageStat, UnidentifiedImageError


def inspect_image(image_bytes: bytes) -> dict:
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return {"ok": False, "message": "This file doesn't look like a valid image. Please upload a JPG or PNG."}
    width, height = image.size
    if min(width, height) < 256:
        return {"ok": False, "message": "This photo is too small. Upload a sharper image at least 256 pixels on each side."}
    if max(width, height) > 6000:
        return {"ok": False, "message": "This photo is unusually large. Please resize it and try again."}
    stats = ImageStat.Stat(image.convert("L"))
    mean = stats.mean[0]
    variance = stats.var[0]
    hints = []
    if mean < 42:
        hints.append("The photo looks very dark. Face a window or use soft, even lighting.")
    elif mean > 225:
        hints.append("The photo looks very bright. Avoid direct sunlight or strong backlighting.")
    if variance < 120:
        hints.append("The photo may be blurry or low-contrast. Clean the camera lens and retake a sharp photo.")
    if width / height > 1.5 or height / width > 1.8:
        hints.append("Use a closer, portrait-oriented photo with your face centered and facing forward.")
    return {"ok": not hints, "message": " ".join(hints), "width": width, "height": height, "brightness_mean": round(mean, 1), "contrast_variance": round(variance, 1)}
