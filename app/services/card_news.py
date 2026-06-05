# app/services/card_news.py

# 표준 라이브러리
import io
import re
import textwrap

# 서드파티 라이브러리
from PIL import Image, ImageDraw, ImageFont

# 카드 이미지 스펙
CARD_WIDTH = 800
CARD_HEIGHT = 1000
BG_COLOR = (245, 247, 250)
ACCENT_COLOR = (26, 115, 232)
ACCENT_LIGHT = (219, 236, 255)
GREEN_COLOR = (46, 125, 50)
GREEN_BG = (234, 246, 238)
TEXT_COLOR = (40, 40, 40)
SUBTEXT_COLOR = (100, 110, 130)
WHITE = (255, 255, 255)
PADDING = 50
FONT_SIZE_TITLE = 38
FONT_SIZE_LABEL = 20
FONT_SIZE_BODY = 26
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


def _extract_first_sentence(text: str) -> str:
    """마크다운 제거 후 첫 문장만 추출."""
    text = re.sub(r'\*\*.*?\*\*\n?', '', text).strip()
    text = re.sub(r'\n+', ' ', text).strip()
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if sentences:
        return sentences[0] + '.'
    return text[:60]


def _wrap_text(text: str, max_chars: int) -> str:
    """한글 줄바꿈 처리."""
    return textwrap.fill(text, width=max(max_chars, 15))


class CardNewsService:
    async def create_card_news_asset(
        self,
        summary_text: str,
        medication_guide: list[dict] | None = None,
        lifestyle_guide: dict | None = None,
    ) -> bytes:
        """
        카드뉴스 이미지 생성 요청을 처리하고 PNG bytes를 반환한다.

        Args:
            summary_text: GUIDES.summary_text (복약+생활 통합 요약)
            medication_guide: 약품별 복약 안내 리스트
            lifestyle_guide: 생활습관 가이드 딕셔너리

        Returns:
            bytes: PNG 이미지 데이터

        Note:
            - 개인정보 보호: 의료 데이터 로그 직접 출력 금지
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

        max_chars = (CARD_WIDTH - PADDING * 2 - 60) // (FONT_SIZE_BODY // 2)

        # ── 상단 헤더 ────────────────────────────────────────────
        _draw_rounded_rect(draw, (PADDING, PADDING, CARD_WIDTH - PADDING, 185), CORNER_RADIUS, ACCENT_COLOR)
        draw.text((PADDING + 30, PADDING + 18), "MediLog", font=label_font, fill=WHITE)
        draw.text((PADDING + 30, PADDING + 48), "건강 가이드", font=title_font, fill=WHITE)

        current_y = 205

        # ── 복약 안내 섹션 ───────────────────────────────────────
        if medication_guide:
            draw.text((PADDING + 30, current_y + 10), "복약 안내", font=label_font, fill=ACCENT_COLOR)
            current_y += 45

            if isinstance(medication_guide, dict):
                raw_text = medication_guide.get("raw", "")
                summary = _extract_first_sentence(raw_text)
                wrapped = _wrap_text(summary, max_chars)
                box_h = 80
                _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, WHITE)
                draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=ACCENT_COLOR)
                draw.text((PADDING + 20, current_y + 22), wrapped, font=body_font, fill=TEXT_COLOR)
                current_y += box_h + 10
            elif isinstance(medication_guide, list):
                for med in medication_guide[:2]:
                    drug_name = med.get("drug_name") or med.get("name", "")
                    instructions = med.get("instructions") or ""
                    if not drug_name:
                        continue
                    text = f"{drug_name}: {_extract_first_sentence(instructions)}" if instructions else drug_name
                    wrapped = _wrap_text(text, max_chars)
                    box_h = 80
                    _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, WHITE)
                    draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=ACCENT_COLOR)
                    draw.text((PADDING + 20, current_y + 22), wrapped, font=body_font, fill=TEXT_COLOR)
                    current_y += box_h + 10

        # ── 생활습관 섹션 ────────────────────────────────────────
        if lifestyle_guide:
            current_y += 20
            draw.text((PADDING + 30, current_y), "생활습관 안내", font=label_font, fill=GREEN_COLOR)
            current_y += 35

            if isinstance(lifestyle_guide, dict):
                raw_text = lifestyle_guide.get("raw", "")
                if raw_text:
                    raw_text = re.sub(r'\*\*.*?\*\*\n?', '', raw_text).strip()
                    sentences = [s.strip() + '.' for s in raw_text.split('.') if s.strip()][:3]
                    for sentence in sentences:
                        wrapped = _wrap_text(sentence, max_chars)
                        box_h = 70
                        _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, GREEN_BG)
                        draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=GREEN_COLOR)
                        draw.text((PADDING + 20, current_y + 18), wrapped, font=body_font, fill=TEXT_COLOR)
                        current_y += box_h + 10

        # ── summary_text fallback ────────────────────────────────
        if not medication_guide and not lifestyle_guide:
            current_y += 10
            _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + 160), CORNER_RADIUS, WHITE)
            draw.text((PADDING + 30, current_y + 20), "오늘의 건강 요약", font=label_font, fill=ACCENT_COLOR)
            draw.line([(PADDING + 30, current_y + 50), (CARD_WIDTH - PADDING - 30, current_y + 50)], fill=(219, 236, 255), width=2)
            wrapped = _wrap_text(_extract_first_sentence(summary_text), max_chars)
            draw.text((PADDING + 30, current_y + 60), wrapped, font=body_font, fill=TEXT_COLOR)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()