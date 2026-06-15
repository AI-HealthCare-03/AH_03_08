# ai_worker/image/classifier/__init__.py

from ai_worker.image.classifier.model import (
    ColorShapeClassifier,
    load_color_shape_model,
    predict_color_shape,
)

__all__ = [
    "ColorShapeClassifier",
    "load_color_shape_model",
    "predict_color_shape",
]
