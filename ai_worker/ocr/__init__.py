from ai_worker.core.config import Config
from ai_worker.ocr.base import OCRProvider
from ai_worker.ocr.clova import ClovaOCRProvider


def get_ocr_provider(config: Config) -> OCRProvider:  # type: ignore[call-arg]
    if config.OCR_PROVIDER == "clova":
        return ClovaOCRProvider(url=config.CLOVA_OCR_URL, secret=config.CLOVA_OCR_SECRET)
    raise ValueError(f"지원하지 않는 OCR 프로바이더: {config.OCR_PROVIDER}")
