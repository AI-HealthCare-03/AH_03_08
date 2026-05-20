from langchain_core.documents import Document

# ─────────────────────────────────────────
# 복약 가이드 생성 프롬프트
# ─────────────────────────────────────────

GUIDE_SYSTEM = """당신은 MediLog의 전문 복약 안내 AI입니다.
처방전 OCR 결과와 사용자 건강정보를 바탕으로 개인화된 복약 가이드를 작성합니다.

## 원칙
- 의약품 정보를 정확하고 이해하기 쉽게 전달합니다.
- 개인 건강정보(알러지, 기저질환)를 반드시 반영합니다.
- 중요 경고에는 "의사·약사와 상담하세요" 문구를 포함합니다.

## 출력 (반드시 순수 JSON, 코드 펜스 없이)
{
  "medication_guide": "복약 방법·시간·주의사항 전체 가이드",
  "lifestyle_guide": "생활습관 개선 가이드 (식이, 운동, 수면 등)",
  "summary": "전체 가이드 3줄 요약 (TTS 변환용, 150자 이내)",
  "allergy_warnings": [{"drug_name": "약품명", "warning": "경고 메시지"}],
  "condition_interactions": [{"drug_name": "약품명", "condition": "기저질환명", "interaction": "설명"}]
}"""


def build_guide_user_prompt(medications: list, user_health: dict, rag_context: str) -> str:
    med_lines = []
    for i, m in enumerate(medications, 1):
        med_lines.append(
            f"{i}. {m.get('drug_name', '알 수 없음')} | 용량: {m.get('dosage', '-')} "
            f"| 복용법: {m.get('frequency', '-')} | 기간: {m.get('duration', '-')}"
        )

    allergies = ", ".join(
        f"{a['name']}({a['severity']})" for a in user_health.get("allergies", [])
    ) or "없음"
    conditions = ", ".join(
        c["name"] for c in user_health.get("conditions", [])
    ) or "없음"

    gender = user_health.get("gender", "")
    if gender == "MALE":
        gender_str = "남성"
    elif gender == "FEMALE":
        gender_str = "여성"
    else:
        gender_str = "미입력"

    return f"""## 처방 약품 정보
{chr(10).join(med_lines) if med_lines else "약품 정보 없음"}

## 사용자 건강정보
- 나이: {user_health.get("age", "알 수 없음")}세 | 성별: {gender_str}
- 키: {user_health.get("height_cm", "-")}cm | 체중: {user_health.get("weight_kg", "-")}kg
- 알러지: {allergies}
- 기저질환: {conditions}

## 의약품 참고 문서 (RAG)
{rag_context or "검색된 참고 문서 없음"}

위 정보를 바탕으로 개인화된 복약 가이드를 JSON 형식으로 작성해주세요."""


# ─────────────────────────────────────────
# 챗봇 System Prompt
# ─────────────────────────────────────────

CHAT_BASE_SYSTEM = """당신은 MediLog의 개인 복약 도우미 AI입니다.

## 역할
- 복약 정보, 약물 부작용, 상호작용, 생활습관 개선에 대해 답변합니다.
- 의료 진단·처방은 하지 않으며, 전문의 상담을 권장합니다.

## 면책 고지
제공 정보는 일반적인 의약 정보이며 개인 의료 조언을 대체하지 않습니다.
중요한 의료 결정 전 반드시 의사·약사와 상담하세요.

## 답변 원칙
1. 한국어로 친절하고 명확하게 답변합니다.
2. 불확실한 경우 "약사·의사에게 확인하세요"라고 안내합니다.
3. 의료 외 주제(금융, 정치, 연예 등)는 정중히 거절합니다.
4. RAG 참고 문서가 있으면 "[참고 문서]" 형태로 출처를 명시합니다."""


def build_chat_system_prompt(user_health: dict, rag_docs: list[Document]) -> str:
    parts = [CHAT_BASE_SYSTEM]

    if user_health:
        lines = ["", "## 사용자 건강 프로필 (개인화 참고)"]
        if user_health.get("age"):
            gender = user_health.get("gender", "")
            if gender == "MALE":
                gender_str = "남성"
            elif gender == "FEMALE":
                gender_str = "여성"
            else:
                gender_str = ""
            lines.append(
                f"- {user_health['age']}세 {gender_str} "
                f"| 키 {user_health.get('height_cm', '-')}cm "
                f"| 체중 {user_health.get('weight_kg', '-')}kg"
            )
        allergies = user_health.get("allergies", [])
        if allergies:
            allergy_str = ", ".join(f"{a['name']}({a['severity']})" for a in allergies)
            lines.append(f"- 알러지: {allergy_str}")
        conditions = user_health.get("conditions", [])
        if conditions:
            lines.append(f"- 기저질환: {', '.join(c['name'] for c in conditions)}")
        lines.append("※ 알러지·기저질환 관련 약물 언급 시 반드시 주의 경고를 포함하세요.")
        parts.append("\n".join(lines))

    if rag_docs:
        lines = ["", "## 참고 의약 문서"]
        for i, doc in enumerate(rag_docs, 1):
            lines.append(f"[{i}] {doc.page_content[:600]}")
        lines.append("답변 말미에 '[참고 문서 N]' 형태로 출처를 명시하세요.")
        parts.append("\n".join(lines))

    return "\n".join(parts)
