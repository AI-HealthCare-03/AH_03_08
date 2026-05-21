# 라우터 등록은 app.apis.v1 에서만 한다.
from app.apis.v1 import v1_routers

__all__ = ["v1_routers"]
