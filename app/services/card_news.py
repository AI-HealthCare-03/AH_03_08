# app/services/card_news.py

# 표준 라이브러리
import io
import textwrap

# 서드파티 라이브러리
from PIL import Image, ImageDraw, ImageFont

# 카드 이미지 스펙
CARD_WIDTH = 800
CARD_HEIGHT = 900
BG_COLOR = (245, 247, 250)
ACCENT_COLOR = (34, 139, 230)
ACCENT_LIGHT = (219, 236, 255)
TEXT_COLOR = (40, 40, 40)
SUBTEXT_COLOR = (100, 110, 130)
WHITE = (255, 255, 255)
PADDING = 50
FONT_SIZE_TITLE = 38
FONT_SIZE_LABEL = 20
FONT_SIZE_BODY = 24
CORNER_RADIUS = 30


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple) -> None:
    """모서리가 둥근 사각형을 그린다."""
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius * 2, y0 + radius * 2], fill=fill)
    draw.ellipse([x1 - radius * 2, y0, x1, y0 + radius * 2], fill=fill)
    draw.ellipse([x0, y1 - radius * 2, x0 + radius * 2, y1], fill=fill)
    draw.ellipse([x1 - radius * 2, y1 - radius * 2, x1, y1], fill=fill)


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
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", FONT_SIZE_TITLE)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", FONT_SIZE_LABEL)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", FONT_SIZE_BODY)
        except OSError:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        # ── 상단 헤더 카드 ──────────────────────────────────────
        _draw_rounded_rect(draw, (PADDING, PADDING, CARD_WIDTH - PADDING, 180), CORNER_RADIUS, ACCENT_COLOR)

        # 헤더 텍스트
        draw.text((PADDING + 30, PADDING + 20), "MediLog", font=label_font, fill=WHITE)
        draw.text((PADDING + 30, PADDING + 50), "건강 가이드", font=title_font, fill=WHITE)

        # ── 본문 카드 ───────────────────────────────────────────
        card_y = 210
        _draw_rounded_rect(draw, (PADDING, card_y, CARD_WIDTH - PADDING, CARD_HEIGHT - PADDING), CORNER_RADIUS, WHITE)

        # 본문 레이블
        draw.text((PADDING + 30, card_y + 30), "오늘의 건강 요약", font=label_font, fill=ACCENT_COLOR)

        # 구분선
        line_y = card_y + 65
        draw.line([(PADDING + 30, line_y), (CARD_WIDTH - PADDING - 30, line_y)], fill=ACCENT_LIGHT, width=2)

        # 본문 텍스트 (한글 줄바꿈)
        max_chars = (CARD_WIDTH - PADDING * 2 - 60) // FONT_SIZE_BODY
        wrapped_lines = []
        for sentence in summary_text.split("."):
            sentence = sentence.strip()
            if not sentence:
                continue
            wrapped = textwrap.fill(sentence + ".", width=max(max_chars, 15))
            wrapped_lines.append(wrapped)

        body_text = "\n".join(wrapped_lines)
        draw.text(
            (PADDING + 30, line_y + 20),
            body_text,
            font=body_font,
            fill=TEXT_COLOR,
            spacing=12,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()