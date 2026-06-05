# 표준 라이브러리
import io
import logging
import textwrap

# 서드파티 라이브러리
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

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


class CardNewsGenerator:
    """Pillow 기반 카드뉴스 이미지 생성."""

    def generate(self, summary_text: str) -> bytes:
        """summary_text로 카드뉴스 PNG 이미지를 생성한다.

        Args:
            summary_text: 가이드 요약 텍스트 (GUIDES.summary_text)

        Returns:
            bytes: PNG 이미지 데이터

        Note:
            - 개인정보 보호: 텍스트 내용 직접 로그 출력 금지, 길이만 기록
        """
        logger.info(f"카드뉴스 생성 시작 - 텍스트 길이: {len(summary_text)}자")

        img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE_TITLE)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONT_SIZE_BODY)
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        # 타이틀
        title = "MediLog 복약 가이드"
        draw.text((PADDING, PADDING), title, font=title_font, fill=TITLE_COLOR)

        # 구분선
        line_y = PADDING + FONT_SIZE_TITLE + 20
        draw.line([(PADDING, line_y), (CARD_WIDTH - PADDING, line_y)], fill=TITLE_COLOR, width=2)

        # 본문 텍스트 (자동 줄바꿈)
        max_chars = (CARD_WIDTH - PADDING * 2) // (FONT_SIZE_BODY // 2)
        wrapped = textwrap.fill(summary_text, width=max_chars)
        draw.text((PADDING, line_y + 30), wrapped, font=body_font, fill=TEXT_COLOR, spacing=LINE_SPACING)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        logger.info("카드뉴스 생성 완료")
        return buf.getvalue()
