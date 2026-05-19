"""
CLOVA OCR API 동작 확인 스크립트

사용법:
    env $(cat envs/.local.env | grep -v '#' | xargs) uv run python scripts/test_clova_ocr.py <이미지_경로>

예시:
    env $(cat envs/.local.env | grep -v '#' | xargs) uv run python scripts/test_clova_ocr.py /tmp/sample.jpg
"""

import asyncio
import base64
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

from ai_worker.core.config import Config  # noqa: E402

_config = Config()  # type: ignore[call-arg]


async def run_ocr(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] 파일 없음: {file_path}")
        sys.exit(1)

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

    print(f"URL   : {_config.CLOVA_OCR_URL}")
    print(f"파일  : {path.name} ({path.stat().st_size / 1024:.1f} KB)")
    print("요청 중...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            _config.CLOVA_OCR_URL,
            headers={
                "X-OCR-SECRET": _config.CLOVA_OCR_SECRET,
                "Content-Type": "application/json",
            },
            json=payload,
        )

    print(f"상태 코드: {response.status_code}")

    if response.status_code != 200:
        print(f"[ERROR] 응답:\n{response.text}")
        sys.exit(1)

    data = response.json()
    texts = []
    for image in data.get("images", []):
        for field in image.get("fields", []):
            if text := field.get("inferText"):
                texts.append(text)

    raw_text = " ".join(texts)
    print(f"\n=== 추출된 텍스트 ({len(raw_text)}자) ===")
    print(raw_text or "(텍스트 없음)")
    print("\n=== 전체 응답 (JSON) ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    asyncio.run(run_ocr(sys.argv[1]))
