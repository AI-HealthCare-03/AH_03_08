import base64
import time
import uuid
from pathlib import Path

import httpx

from ai_worker.ocr.base import OCRProvider


class ClovaOCRProvider(OCRProvider):
    def __init__(self, url: str, secret: str) -> None:
        self._url = url
        self._secret = secret

    async def extract_text(self, file_path: str) -> str:
        path = Path(file_path)
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = path.suffix.lstrip(".").lower()
        if ext == "jpg":
            ext = "jpeg"

        payload = {
            "images": [{"format": ext, "name": path.name, "data": image_data}],
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "version": "V2",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self._url,
                headers={
                    "X-OCR-SECRET": self._secret,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        texts = [
            field.get("inferText", "")
            for image in data.get("images", [])
            for field in image.get("fields", [])
            if field.get("inferText")
        ]
        return " ".join(texts)

    async def extract_text_from_bytes(self, image_bytes: bytes, ext: str = "jpeg") -> list[str]:
        if ext == "jpg":
            ext = "jpeg"

        image_data = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "images": [{"format": ext, "name": "pill.jpg", "data": image_data}],
            "requestId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "version": "V2",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._url,
                    headers={
                        "X-OCR-SECRET": self._secret,
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()

            data = response.json()
            return [
                field.get("inferText", "")
                for image in data.get("images", [])
                for field in image.get("fields", [])
                if field.get("inferText")
            ]
        except Exception:
            return []