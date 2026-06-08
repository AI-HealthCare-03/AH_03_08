# app/services/card_news.py

# 표준 라이브러리
import io
import re

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
WHITE = (255, 255, 255)
PADDING = 50
FONT_SIZE_TITLE = 38
FONT_SIZE_LABEL = 20
FONT_SIZE_BODY = 22
CORNER_RADIUS = 30

# 텍스트 시작 x, 최대 너비 (픽셀)
TEXT_X = PADDING + 20
TEXT_MAX_WIDTH = CARD_WIDTH - PADDING - TEXT_X - 20  # 660px


def _draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple) -> None:
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + radius * 2, y0 + radius * 2], fill=fill)
    draw.ellipse([x1 - radius * 2, y0, x1, y0 + radius * 2], fill=fill)
    draw.ellipse([x0, y1 - radius * 2, x0 + radius * 2, y1], fill=fill)
    draw.ellipse([x1 - radius * 2, y1 - radius * 2, x1, y1], fill=fill)


def _extract_first_sentence(text: str) -> str:
    text = re.sub(r"\*\*.*?\*\*\n?", "", text).strip()
    text = re.sub(r"\n+", " ", text).strip()
    # "1. xxx. 2. yyy." 형식 번호 목록 → 첫 항목만 추출
    parts = re.split(r"(?<!\d)\d+\.\s+", text)
    parts = [p.strip().rstrip(".") for p in parts if p.strip()]
    if parts:
        return parts[0] + "."
    return text[:60]


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width_px: int) -> str:
    """실제 픽셀 너비 기준 줄바꿈."""
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if font.getlength(candidate) <= max_width_px:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def _box_height(wrapped: str, base: int = 80) -> int:
    line_count = wrapped.count("\n") + 1
    return max(base, 36 + line_count * (FONT_SIZE_BODY + 4))


def _draw_medication_section(
    draw: ImageDraw.ImageDraw,
    medication_guide: list | dict,
    current_y: int,
    label_font: ImageFont.FreeTypeFont,
    body_font: ImageFont.FreeTypeFont,
    medications: list[dict],
) -> int:
    draw.text((PADDING + 30, current_y + 10), "복약 안내", font=label_font, fill=ACCENT_COLOR)
    current_y += 45

    if medications:
        for med in medications[:3]:
            drug_name = med.get("name", "")
            if not drug_name:
                continue
            frequency = med.get("frequency")
            freq_str = f"하루 {int(str(frequency))}회" if frequency is not None else ""
            detail = freq_str

            # 낱알약(frequency 없음)이면 medication_guide raw 내용 표시
            if not frequency and isinstance(medication_guide, dict):
                raw = medication_guide.get("raw", "")
                detail = _extract_first_sentence(raw) if raw else ""

            detail_wrapped = _wrap_text(detail, body_font, TEXT_MAX_WIDTH) if detail else ""
            line_count = detail_wrapped.count("\n") + 1 if detail_wrapped else 0
            box_h = max(70, 14 + FONT_SIZE_LABEL + 6 + line_count * (FONT_SIZE_BODY + 4) + 12)
            _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, WHITE)
            draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=ACCENT_COLOR)
            draw.text((TEXT_X, current_y + 12), drug_name, font=label_font, fill=ACCENT_COLOR)
            if detail_wrapped:
                draw.text(
                    (TEXT_X, current_y + 12 + FONT_SIZE_LABEL + 6), detail_wrapped, font=body_font, fill=TEXT_COLOR
                )
            current_y += box_h + 10
    elif isinstance(medication_guide, dict):
        raw_text = medication_guide.get("raw", "")
        summary = _extract_first_sentence(raw_text)
        wrapped = _wrap_text(summary, body_font, TEXT_MAX_WIDTH)
        box_h = _box_height(wrapped)
        _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, WHITE)
        draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=ACCENT_COLOR)
        draw.text((TEXT_X, current_y + 22), wrapped, font=body_font, fill=TEXT_COLOR)
        current_y += box_h + 10

    return current_y


def _draw_lifestyle_section(
    draw: ImageDraw.ImageDraw,
    lifestyle_guide: dict,
    current_y: int,
    label_font: ImageFont.FreeTypeFont,
    body_font: ImageFont.FreeTypeFont,
) -> int:
    current_y += 20
    draw.text((PADDING + 30, current_y), "생활습관 안내", font=label_font, fill=GREEN_COLOR)
    current_y += 35

    key_labels = {
        "diet": "식단",
        "sleep": "수면",
        "exercise": "운동",
        "monitoring": "관찰",
        "alcohol_smoking": "음주·흡연",
    }

    if lifestyle_guide.get("raw"):
        raw_text = re.sub(r"\*\*.*?\*\*\n?", "", lifestyle_guide["raw"]).strip()
        items = [(None, s.strip() + ".") for s in raw_text.split(".") if s.strip()][:3]
    else:
        items = [(key_labels.get(k), v) for k, v in lifestyle_guide.items() if isinstance(v, str) and v.strip()][:3]

    if not items:
        return current_y

    for label, sentence in items:
        sentence = sentence[:80]
        wrapped = _wrap_text(sentence, body_font, TEXT_MAX_WIDTH)
        box_h = _box_height(wrapped, base=70)
        if label:
            box_h += FONT_SIZE_LABEL + 4
        _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, GREEN_BG)
        draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=GREEN_COLOR)
        text_y = current_y + 12
        if label:
            draw.text((TEXT_X, text_y), label, font=label_font, fill=GREEN_COLOR)
            text_y += FONT_SIZE_LABEL + 4
        draw.text((TEXT_X, text_y), wrapped, font=body_font, fill=TEXT_COLOR)
        current_y += box_h + 10

    return current_y


class CardNewsService:
    async def create_card_news_asset(
        self,
        summary_text: str,
        medication_guide: list[dict] | None = None,
        lifestyle_guide: dict | None = None,
        medications: list[dict] | None = None,
    ) -> bytes:
        """
        카드뉴스 이미지 생성 요청을 처리하고 PNG bytes를 반환한다.

        Returns:
            bytes: PNG 이미지 데이터
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

        # ── 상단 헤더 ────────────────────────────────────────────
        _draw_rounded_rect(draw, (PADDING, PADDING, CARD_WIDTH - PADDING, 185), CORNER_RADIUS, ACCENT_COLOR)
        draw.text((PADDING + 30, PADDING + 18), "MediLog", font=label_font, fill=WHITE)
        draw.text((PADDING + 30, PADDING + 48), "건강 가이드", font=title_font, fill=WHITE)

        current_y = 205

        # ── 복약 안내 섹션 ───────────────────────────────────────
        if medication_guide or medications:
            current_y = _draw_medication_section(
                draw, medication_guide or {}, current_y, label_font, body_font, medications or []
            )

        # ── 생활습관 섹션 ────────────────────────────────────────
        if lifestyle_guide:
            current_y = _draw_lifestyle_section(draw, lifestyle_guide, current_y, label_font, body_font)

        # ── summary_text fallback ────────────────────────────────
        if not medication_guide and not lifestyle_guide:
            current_y += 10
            _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + 160), CORNER_RADIUS, WHITE)
            draw.text((PADDING + 30, current_y + 20), "오늘의 건강 요약", font=label_font, fill=ACCENT_COLOR)
            draw.line(
                [(PADDING + 30, current_y + 50), (CARD_WIDTH - PADDING - 30, current_y + 50)],
                fill=ACCENT_LIGHT,
                width=2,
            )
            wrapped = _wrap_text(_extract_first_sentence(summary_text), body_font, TEXT_MAX_WIDTH)
            draw.text((PADDING + 30, current_y + 60), wrapped, font=body_font, fill=TEXT_COLOR)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()