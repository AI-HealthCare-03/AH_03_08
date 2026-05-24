# ai_worker/image/__init__.py

from ai_worker.core.config import Config
from ai_worker.image.lookup import get_drug_info, get_kcode
from ai_worker.image.model import load_model, predict
from ai_worker.image.preprocessor import preprocess_image


class PillClassifier:
    """낱알약 이미지 분류 파이프라인."""

    def __init__(self, model_path: str, label_path: str, data_path: str) -> None:
        self.model = load_model(model_path)
        self.label_path = label_path
        self.data_path = data_path

    def classify(self, image_bytes: bytes) -> tuple[str, dict, float]:
        """
        이미지를 분류하여 K코드, 약품 정보, confidence score를 반환한다.

        Args:
            image_bytes: 사용자가 업로드한 이미지 파일 (bytes)

        Returns:
            tuple[str, dict, float]: (K코드, 약품 정보, confidence score)
        """
        tensor = preprocess_image(image_bytes)
        class_idx, confidence_score = predict(self.model, tensor)
        kcode = get_kcode(class_idx, self.label_path)
        drug_info = get_drug_info(kcode, self.data_path)
        return kcode, drug_info, confidence_score


def get_image_classifier(config: Config) -> PillClassifier:
    """config에서 값을 주입받아 PillClassifier를 반환한다."""
    return PillClassifier(
        model_path=config.PILL_MODEL_PATH,
        label_path=config.PILL_LABEL_PATH,
        data_path=config.PILL_DATA_PATH,
    )