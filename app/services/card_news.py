# app/services/card_news.py

# 로컬 모듈
from ai_worker.card_news import get_card_news_generator
from ai_worker.core.config import Config


class CardNewsService:
    def __init__(self):
        self.generator = get_card_news_generator(Config())

    async def create_card_news_asset(
        self,
        summary_text: str,
    ) -> bytes:
        """
        카드뉴스 이미지 생성 요청을 처리하고 PNG bytes를 반환한다.

        Args:
            summary_text: GUIDES.summary_text (복약+생활 통합 요약)

        Returns:
            bytes: PNG 이미지 데이터

        Note:
            - 개인정보 보호: 의료 데이터(summary_text) 로그 직접 출력 금지
        """
        return self.generator.generate(summary_text)