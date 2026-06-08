# app/services/card_news.py

import io
import re

from PIL import Image, ImageDraw, ImageFont

CARD_WIDTH = 800
CARD_HEIGHT = 1100
BG_COLOR = (245, 247, 250)
HEADER_COLOR = (15, 110, 86)  # #0F6E56

# 복약 안내 - 파란색
MED_COLOR = (55, 138, 221)  # #378ADD
MED_LIGHT = (230, 241, 251)  # #E6F1FB
MED_DARK = (12, 68, 124)  # #0C447C
MED_LABEL = (24, 95, 165)  # #185FA5

# 생활습관 - 초록색
GREEN_COLOR = (15, 110, 86)  # #0F6E56
GREEN_BG = (225, 245, 238)  # #E1F5EE
GREEN_DARK = (8, 80, 65)  # #085041

TEXT_COLOR = (40, 40, 40)
TEXT_MUTED = (100, 100, 100)
WHITE = (255, 255, 255)
PADDING = 50
FONT_SIZE_TITLE = 42
FONT_SIZE_LABEL = 22
FONT_SIZE_BODY = 20
FONT_SIZE_SMALL = 17
CORNER_RADIUS = 30

TEXT_X = PADDING + 20
TEXT_MAX_WIDTH = CARD_WIDTH - PADDING - TEXT_X - 20


def _draw_rounded_rect(draw, xy, radius, fill):
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
    parts = re.split(r"(?<!\d)\d+\.\s+", text)
    parts = [p.strip().rstrip(".") for p in parts if p.strip()]
    if parts:
        return parts[0] + "."
    return text[:60]


def _wrap_text(text: str, font, max_width_px: int) -> str:
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
    draw, medication_guide, current_y, label_font, body_font, small_font, medications, summary_text=""
):
    draw.text((PADDING + 30, current_y + 10), "복약 안내", font=label_font, fill=MED_LABEL)
    current_y += 48

    if medications:
        for med in medications[:3]:
            drug_name = med.get("name", "")
            if not drug_name:
                continue
            frequency = med.get("frequency")
            freq_str = f"하루 {int(str(frequency))}회" if frequency is not None else ""
            detail = freq_str

            if not frequency:
                detail = summary_text[:80] if summary_text else ""

            detail_wrapped = _wrap_text(detail, body_font, TEXT_MAX_WIDTH) if detail else ""
            line_count = detail_wrapped.count("\n") + 1 if detail_wrapped else 0
            box_h = max(80, 16 + FONT_SIZE_LABEL + 8 + line_count * (FONT_SIZE_BODY + 4) + 16)

            _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, MED_LIGHT)
            draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=MED_COLOR)
            draw.text((TEXT_X, current_y + 14), drug_name, font=label_font, fill=MED_DARK)
            if detail_wrapped:
                draw.text(
                    (TEXT_X, current_y + 14 + FONT_SIZE_LABEL + 8), detail_wrapped, font=body_font, fill=TEXT_COLOR
                )
            current_y += box_h + 10

    elif isinstance(medication_guide, dict):
        raw_text = medication_guide.get("raw", "")
        summary = _extract_first_sentence(raw_text)
        wrapped = _wrap_text(summary, body_font, TEXT_MAX_WIDTH)
        box_h = _box_height(wrapped)
        _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, MED_LIGHT)
        draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=MED_COLOR)
        draw.text((TEXT_X, current_y + 22), wrapped, font=body_font, fill=TEXT_COLOR)
        current_y += box_h + 10

    return current_y


def _draw_lifestyle_section(draw, lifestyle_guide, current_y, label_font, body_font, small_font):
    current_y += 20
    draw.text((PADDING + 30, current_y), "생활습관 안내", font=label_font, fill=GREEN_COLOR)
    current_y += 48

    key_labels = {
        "diet": "식단",
        "exercise": "운동",
        "sleep": "수면",
        "monitoring": "관찰",
        "alcohol_smoking": "음주·흡연",
    }

    if lifestyle_guide.get("raw"):
        raw_text = re.sub(r"\*\*.*?\*\*\n?", "", lifestyle_guide["raw"]).strip()
        items = [(None, s.strip() + ".") for s in raw_text.split(".") if s.strip()][:4]
    else:
        items = [(key_labels.get(k, k), v) for k, v in lifestyle_guide.items() if isinstance(v, str) and v.strip()][:4]

    if not items:
        return current_y

    for label, sentence in items:
        sentence = sentence[:90]
        wrapped = _wrap_text(sentence, body_font, TEXT_MAX_WIDTH)
        line_count = wrapped.count("\n") + 1
        box_h = max(70, 16 + (FONT_SIZE_LABEL + 6 if label else 0) + line_count * (FONT_SIZE_BODY + 4) + 16)

        _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + box_h), 16, GREEN_BG)
        draw.rectangle([PADDING, current_y, PADDING + 6, current_y + box_h], fill=GREEN_COLOR)
        text_y = current_y + 14
        if label:
            draw.text((TEXT_X, text_y), label, font=label_font, fill=GREEN_COLOR)
            text_y += FONT_SIZE_LABEL + 6
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
        img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), color=BG_COLOR)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", FONT_SIZE_TITLE)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", FONT_SIZE_LABEL)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", FONT_SIZE_BODY)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", FONT_SIZE_SMALL)
        except OSError:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # ── 헤더 (약품명 서브타이틀 없음) ───────────────────────
        _draw_rounded_rect(draw, (PADDING, PADDING, CARD_WIDTH - PADDING, 190), CORNER_RADIUS, HEADER_COLOR)
        draw.text((PADDING + 30, PADDING + 18), "MediLog", font=small_font, fill=(200, 235, 225))
        draw.text((PADDING + 30, PADDING + 44), "건강 가이드", font=title_font, fill=WHITE)

        current_y = 210

        # ── 복약 안내 (파란색) ───────────────────────────────────
        if medication_guide or medications:
            current_y = _draw_medication_section(
                draw,
                medication_guide or {},
                current_y,
                label_font,
                body_font,
                small_font,
                medications or [],
                summary_text,
            )

        # ── 생활습관 (초록색) ────────────────────────────────────
        if lifestyle_guide:
            current_y = _draw_lifestyle_section(draw, lifestyle_guide, current_y, label_font, body_font, small_font)

        # ── fallback ─────────────────────────────────────────────
        if not medication_guide and not lifestyle_guide:
            current_y += 10
            _draw_rounded_rect(draw, (PADDING, current_y, CARD_WIDTH - PADDING, current_y + 160), CORNER_RADIUS, WHITE)
            draw.text((PADDING + 30, current_y + 20), "오늘의 건강 요약", font=label_font, fill=MED_COLOR)
            draw.line(
                [(PADDING + 30, current_y + 50), (CARD_WIDTH - PADDING - 30, current_y + 50)], fill=MED_LIGHT, width=2
            )
            wrapped = _wrap_text(_extract_first_sentence(summary_text), body_font, TEXT_MAX_WIDTH)
            draw.text((PADDING + 30, current_y + 60), wrapped, font=body_font, fill=TEXT_COLOR)

        # ── 하단 면책 문구 ───────────────────────────────────────
        footer_y = CARD_HEIGHT - 60
        draw.line([(PADDING, footer_y), (CARD_WIDTH - PADDING, footer_y)], fill=(200, 210, 205), width=1)
        draw.text(
            (PADDING + 30, footer_y + 14),
            "정확한 복약 방법은 의사·약사에게 확인하세요",
            font=small_font,
            fill=TEXT_MUTED,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
