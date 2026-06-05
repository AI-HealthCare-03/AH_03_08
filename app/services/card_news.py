# app/services/card_news.py

# 표준 라이브러리
import io
import textwrap

# 서드파티 라이브러리
from PIL import Image, ImageDraw, ImageFont

# 카드 이미지 스펙
CARD_WIDTH = 800
CARD_HEIGHT = 800
BG_COLOR = (255, 255, 255)
TITLE_COLOR = (34, 139, 230)
TEXT_COLOR = (50, 50, 50)
PADDING = 60
FONT_SIZE_TITLE = 36
FONT_SIZE_BODY = 28
LINE_SPACING = 10


class CardNewsService:
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
        img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE_TITLE)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONT_SIZE_BODY)
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        title = "MediLog 복약 가이드"
        draw.text((PADDING, PADDING), title, font=title_font, fill=TITLE_COLOR)

        line_y = PADDING + FONT_SIZE_TITLE + 20
        draw.line([(PADDING, line_y), (CARD_WIDTH - PADDING, line_y)], fill=TITLE_COLOR, width=2)

        max_chars = (CARD_WIDTH - PADDING * 2) // (FONT_SIZE_BODY // 2)
        wrapped = textwrap.fill(summary_text, width=max_chars)
        draw.text((PADDING, line_y + 30), wrapped, font=body_font, fill=TEXT_COLOR, spacing=LINE_SPACING)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()