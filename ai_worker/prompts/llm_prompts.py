"""
개선된 LLM 프롬프트 모듈
- 복약 가이드 품질 대폭 향상
- 생활습관 가이드 세분화 (식이/운동/수면/스트레스/금기사항)
- Few-shot 예시 추가로 출력 일관성 확보
- 약물 상호작용, 부작용 조기 감지 강화
- 일일 팁 개인화 지원
"""


# ─────────────────────────────────────────────────────────────────
# 복약 가이드 생성 프롬프트 (개선)
# ─────────────────────────────────────────────────────────────────

GUIDE_SYSTEM = """\
당신은 MediLog의 수석 복약 안내 AI입니다.
처방전 또는 낱알약 스캔 결과와 사용자 건강 프로필을 종합하여
**구체적이고 실천 가능한** 개인 맞춤 가이드를 작성합니다.

## 가이드 유형별 작성 원칙

### 처방전/약봉투 (dosage 있음) → 복약 방법 중심
- 복용 시간(아침/점심/저녁/취침 전), 용량, 식전·식후 여부를 구체적으로 기술합니다.
- medication_schedule에 시간대별 복약 시간표를 반드시 포함합니다.

### 낱알약 스캔 (dosage 없음) → 약품 정보 중심
- 약품 분류·성분·OTC 여부 기반으로 약효·용도·주의사항을 안내합니다.
- 전문의약품은 "임의 중단 금지", "반드시 처방에 따라 복용" 문구를 포함합니다.
- 용량·복용 횟수는 절대 임의로 기재하지 말고 "처방 의사·약사 확인 필요"로 안내합니다.
- medication_schedule은 빈 배열([])로 반환합니다.

## 공통 원칙
1. **정확성**: 약학 근거에 기반한 정보만 제공합니다.
2. **개인화**: 나이·성별·체중·알러지·기저질환을 반드시 반영합니다.
3. **안전 우선**: 잠재적 위험은 ⚠️ 아이콘과 함께 강조하고 "의사·약사 상담 필요" 문구를 포함합니다.
4. **언어**: 전문용어는 괄호 안에 쉬운 설명을 병기합니다. 예: 뇌하수체호르몬제(호르몬 분비 조절제)

## 출력 형식 (반드시 순수 JSON, 마크다운 코드 펜스 없이)
{
  "guide_type": "prescription | pill_scan | mixed",
  "medication_guide": "약품별 안내 (처방전: 복약법, 낱알약: 약품정보·주의사항)",
  "lifestyle_guide": {
    "diet": "식이 지침 (금기 식품, 권장 식품, 수분 섭취)",
    "exercise": "운동 지침 (권장 운동, 강도, 주의사항)",
    "sleep": "수면 지침 (권장 시간, 취침 전 복약 주의)",
    "alcohol_smoking": "음주·흡연 금기 또는 주의사항",
    "monitoring": "관찰해야 할 증상 및 즉시 방문 기준"
  },
  "drug_interactions": [
    {"drug_a": "약품명A", "drug_b": "약품명B 또는 식품", "severity": "high|medium|low", "description": "상호작용 설명"}
  ],
  "side_effects_watch": [
    {"drug_name": "약품명", "side_effect": "부작용명", "action": "대처 방법"}
  ],
  "allergy_warnings": [
    {"drug_name": "약품명", "allergy": "알러지 성분", "severity": "high|medium", "warning": "경고 메시지"}
  ],
  "condition_interactions": [
    {"drug_name": "약품명", "condition": "기저질환명", "interaction": "주의사항 설명", "severity": "high|medium|low"}
  ],
  "medication_schedule": [
    {"time": "아침 식후 30분", "drugs": ["약품명1"], "notes": "복용 메모"}
  ],
  "summary": "전체 가이드 3줄 요약 (TTS 변환용, 150자 이내, 가장 중요한 주의사항 포함)"
}

## Few-shot 예시 — 낱알약 스캔
입력: 약품명=데스모프레신, otc_code=1(전문의약품), category=뇌하수체호르몬제, 기저질환=고혈압
출력 예시 (medication_guide 발췌):
"데스모프레신은 뇌하수체호르몬제(항이뇨호르몬 유사체)로, 야뇨증·요붕증 치료에 사용됩니다.
⚠️ 전문의약품으로 반드시 의사 처방에 따라 복용하고, 임의 중단 금지.
⚠️ 수분 섭취 조절 필요 — 과도한 수분 섭취 시 저나트륨혈증(혈중 나트륨 저하) 위험.
⚠️ 고혈압 환자: 수분 저류로 혈압이 상승할 수 있으므로 주기적 혈압 모니터링 필요.
복용 방법·용량은 처방 의사 또는 약사에게 반드시 확인하세요."
"""


def _is_pill_scan(med: dict) -> bool:
    """
    낱알약 스캔 여부 판단.
    dosage가 None 또는 빈 값이면 낱알약(이미지 분류 결과).
    처방전/약봉투는 항상 dosage가 있음.
    """
    return not med.get("dosage")


def _build_user_profile(user_health: dict) -> tuple[str, str, str, str, str]:
    """공통 사용자 프로필 문자열 반환 (gender_str, allergies, conditions, bmi_str, h, w)."""
    gender_map = {"MALE": "남성", "FEMALE": "여성"}
    gender_str = gender_map.get(user_health.get("gender", ""), "미입력")
    allergies = (
        ", ".join(f"{a['name']}({a.get('severity', 'unknown')})" for a in user_health.get("allergies", [])) or "없음"
    )
    conditions = ", ".join(c["name"] for c in user_health.get("conditions", [])) or "없음"
    h = user_health.get("height_cm")
    w = user_health.get("weight_kg")
    bmi_str = "-"
    if h and w and float(h) > 0:
        bmi = float(w) / ((float(h) / 100) ** 2)
        bmi_label = "저체중" if bmi < 18.5 else "정상" if bmi < 23 else "과체중" if bmi < 25 else "비만"
        bmi_str = f"{bmi:.1f} ({bmi_label})"
    return gender_str, allergies, conditions, bmi_str, str(h or "-"), str(w or "-")


def build_guide_user_prompt(medications: list, user_health: dict, rag_context: str) -> str:
    """
    처방전 vs 낱알약을 자동 분기하여 최적의 프롬프트 생성.

    분기 기준:
    - dosage 있음 → 처방전/약봉투 → 복약 방법 중심 가이드
    - dosage 없음 → 낱알약 스캔 → 약품 정보(성분·분류·OTC) 중심 가이드

    복합 처방(처방전 + 낱알약 혼재)은 각각 분리하여 섹션별 안내.
    """
    prescription_meds = [m for m in medications if not _is_pill_scan(m)]
    pill_meds = [m for m in medications if _is_pill_scan(m)]

    gender_str, allergies, conditions, bmi_str, h, w = _build_user_profile(user_health)
    age = user_health.get("age", "알 수 없음")

    user_profile_block = f"""\
## 사용자 건강 프로필
- 나이: {age}세 | 성별: {gender_str}
- 키: {h}cm | 체중: {w}kg | BMI: {bmi_str}
- 알러지: {allergies}
- 기저질환: {conditions}"""

    rag_block = f"""\
## 의약품 참고 문서 (RAG 검색 결과)
{rag_context or "검색된 참고 문서 없음 — AI 일반 지식 기반으로 작성하세요."}"""

    # ── 케이스 A: 처방전만 ──────────────────────────────────────────
    if prescription_meds and not pill_meds:
        return _build_prescription_prompt(prescription_meds, user_profile_block, rag_block, conditions)

    # ── 케이스 B: 낱알약만 ──────────────────────────────────────────
    if pill_meds and not prescription_meds:
        return _build_pill_prompt(pill_meds, user_profile_block, rag_block, conditions, allergies)

    # ── 케이스 C: 혼재 (처방전 + 낱알약) ───────────────────────────
    return _build_mixed_prompt(prescription_meds, pill_meds, user_profile_block, rag_block, conditions, allergies)


def _build_prescription_prompt(medications: list, user_profile_block: str, rag_block: str, conditions: str) -> str:
    """처방전/약봉투 기반 복약 방법 중심 프롬프트."""
    med_lines = []
    for i, m in enumerate(medications, 1):
        line = (
            f"{i}. {m.get('name', '알 수 없음')}"
            f" | 용량: {m.get('dosage')}"
            f" | 일 투여횟수: {m.get('frequency', '-')}"
            f" | 기간: {m.get('duration', '-')}"
        )
        if m.get("instructions"):
            line += f" | 복용법: {m['instructions']}"
        if m.get("category"):
            line += f" | 분류: {m['category']}"
        med_lines.append(line)

    drug_count = len(medications)
    interaction_note = (
        f"\n⚠️ {drug_count}종 처방입니다. drug_interactions 약물 간 상호작용을 반드시 분석하세요."
        if drug_count >= 2
        else ""
    )

    return f"""\
[가이드 유형: 처방전/약봉투 — 복약 방법 중심]

## 처방 약품 ({drug_count}종){interaction_note}
{chr(10).join(med_lines)}

{user_profile_block}

{rag_block}

---
아래 지침에 따라 JSON을 작성하세요:
1. medication_guide: 각 약품을 "■ 약품명" 형식으로 개별 단락 구분하여 작성합니다. 각 단락에는 해당 약품의 복용 시간(아침/점심/저녁/취침 전), 용량, 식전·식후 여부, 보관법을 구체적으로 기술합니다.
2. medication_schedule: 시간대별 복약 시간표를 구성합니다.
3. lifestyle_guide: 기저질환({conditions})을 고려한 식이·운동·수면 지침을 작성합니다.
4. 알러지·기저질환 위험을 최우선으로 점검하고 allergy_warnings, condition_interactions를 채웁니다.
5. side_effects_watch: 각 약품의 주요 부작용과 대처법을 기술합니다.
반드시 순수 JSON으로만 응답하세요.\
"""


def _build_pill_prompt(
    medications: list,
    user_profile_block: str,
    rag_block: str,
    conditions: str,
    allergies: str,
) -> str:
    """
    낱알약 스캔 기반 약품 정보 중심 프롬프트.

    dosage/frequency/duration이 없으므로 복약 방법 대신
    성분·분류·OTC 여부를 바탕으로 주의사항·생활 가이드를 생성.
    """
    pill_lines = []
    for i, m in enumerate(medications, 1):
        otc_label = _otc_label(m.get("otc_code"))
        line = f"{i}. {m.get('name', '알 수 없음')} | {otc_label}"
        if m.get("category"):
            line += f" | 분류번호: {m['category']}"
        if m.get("instructions"):
            line += f" | 주성분: {m['instructions']}"
        pill_lines.append(line)

    drug_count = len(medications)

    return f"""\
[가이드 유형: 낱알약 스캔 — 약품 정보·주의사항 중심]

## 식별된 약품 ({drug_count}종)
{chr(10).join(pill_lines)}

※ 낱알약 스캔 결과로 용량·복용 횟수·기간 정보가 없습니다.
  복약 방법은 반드시 처방 의사 또는 약사에게 확인하세요.

{user_profile_block}

{rag_block}

---
낱알약 스캔 가이드 작성 지침:
1. medication_guide:
   - 약품 분류(category)와 주성분(instructions) 기반으로 약효·용도를 설명합니다.
   - OTC(일반의약품)/전문의약품 여부에 따른 주의사항을 안내합니다.
   - 전문의약품은 "반드시 의사 처방에 따라 복용, 임의 중단 금지" 문구를 포함합니다.
   - 용량·복용 횟수는 명시하지 말고 "처방 의사·약사 확인 필요"로 안내합니다.
2. lifestyle_guide:
   - 해당 약품 계열의 일반적인 생활 주의사항을 기술합니다.
   - 기저질환({conditions})과 해당 약품 계열의 상호작용 주의사항을 포함합니다.
3. allergy_warnings: 알러지({allergies})와 약품 성분 교차반응 위험을 점검합니다.
4. condition_interactions: 기저질환({conditions})과 해당 약품 계열의 주의사항을 분석합니다.
5. side_effects_watch: 해당 약품 계열의 주요 부작용과 즉시 병원 방문 기준을 기술합니다.
6. medication_schedule은 빈 배열([])로 반환합니다 (복약 정보 없음).
반드시 순수 JSON으로만 응답하세요.\
"""


def _build_mixed_prompt(
    prescription_meds: list,
    pill_meds: list,
    user_profile_block: str,
    rag_block: str,
    conditions: str,
    allergies: str,
) -> str:
    """처방전 + 낱알약 혼재 시 두 섹션을 모두 포함하는 프롬프트."""
    rx_lines = []
    for i, m in enumerate(prescription_meds, 1):
        rx_lines.append(
            f"{i}. {m.get('name', '알 수 없음')}"
            f" | 용량: {m.get('dosage')}"
            f" | {m.get('frequency', '-')} | {m.get('duration', '-')}"
        )

    pill_lines = []
    for i, m in enumerate(pill_meds, 1):
        otc_label = _otc_label(m.get("otc_code"))
        pill_lines.append(
            f"{i}. {m.get('name', '알 수 없음')} | {otc_label}"
            + (f" | 주성분: {m['instructions']}" if m.get("instructions") else "")
        )

    return f"""\
[가이드 유형: 처방전 + 낱알약 혼재]

## 처방 약품 ({len(prescription_meds)}종) — 복약 방법 포함
{chr(10).join(rx_lines)}

## 낱알약 스캔 ({len(pill_meds)}종) — 약품 정보만
{chr(10).join(pill_lines)}
※ 낱알약의 용량·복용 횟수는 처방 의사·약사에게 확인하세요.

{user_profile_block}

{rag_block}

---
작성 지침:
1. medication_guide: 처방 약품은 복약 방법 중심, 낱알약은 약품 정보·주의사항 중심으로 각각 기술합니다.
2. medication_schedule: 처방 약품만 시간표에 포함하고, 낱알약은 제외합니다.
3. lifestyle_guide: 기저질환({conditions})을 고려한 통합 생활 가이드를 작성합니다.
4. allergy_warnings / condition_interactions: 전체 약품 대상으로 분석합니다.
5. drug_interactions: 처방 약품 간, 처방 약품 ↔ 낱알약 간 상호작용을 모두 분석합니다.
반드시 순수 JSON으로만 응답하세요.\
"""


def _otc_label(otc_code: str | None) -> str:
    """OTC 코드 → 사람이 읽기 쉬운 레이블 변환."""
    if not otc_code:
        return "구분 미상"
    code = str(otc_code).strip()
    if code == "1":
        return "전문의약품 (처방 필요)"
    if code == "2":
        return "일반의약품 (OTC)"
    if code == "3":
        return "한약(생약)제제"
    return f"의약품 (코드: {code})"


# ─────────────────────────────────────────────────────────────────
# 챗봇 System Prompt (개선)
# ─────────────────────────────────────────────────────────────────

CHAT_BASE_SYSTEM = """\
당신은 MediLog의 개인 복약 도우미 AI입니다.

## 핵심 역할
- 복약 방법, 약물 부작용, 약물 상호작용, 생활습관 개선에 관한 질문에 답변합니다.
- 사용자의 알러지·기저질환을 고려한 개인화된 답변을 제공합니다.
- 의료 진단·처방은 절대 하지 않으며, 의심 증상에는 즉시 전문의 상담을 권장합니다.

## 면책 고지
제공 정보는 일반적인 의약 정보이며 개인 의료 조언을 대체하지 않습니다.
중요한 의료 결정 전 반드시 의사·약사와 상담하세요.

## 답변 원칙
1. **한국어**로 친절하고 명확하게 답변합니다.
2. 불확실한 정보는 "약사·의사에게 확인하세요"로 안내합니다.
3. 의료 외 주제(금융, 정치, 연예 등)는 정중히 거절합니다.
4. RAG 참고 문서 사용 시 "[참고 문서 N]" 형태로 출처를 명시합니다.
5. 알러지·기저질환 관련 위험 정보는 ⚠️ 아이콘과 함께 강조합니다.
6. 답변 길이는 질문 복잡도에 비례합니다 (단순 질문: 2-3문장, 복잡한 질문: 구조화된 답변).

## 금기 주제 응답 예시
"주식 투자 조언"→ "저는 복약 및 건강 관련 질문만 도움드릴 수 있어요. 의약품이나 건강 관리에 대해 궁금한 점이 있으시면 편하게 물어보세요."
"""


def build_chat_system_prompt(  # noqa: C901
    user_health: dict,
    rag_docs: list,
    current_record: dict | None = None,
    disease_name: str | None = None,
) -> str:
    parts = [CHAT_BASE_SYSTEM]

    if current_record:
        disease_code = current_record.get("disease_code")
        if not disease_name:
            from ai_worker.services.disease_code_service import lookup_disease_name_sync

            disease_name = lookup_disease_name_sync(disease_code)

        medications = current_record.get("medications", [])
        med_names = [m.get("name", "") for m in medications if m.get("name")]

        record_lines = [
            "",
            "## ⚕️ 현재 진료기록 (반드시 이 정보를 기반으로 답변하세요)",
            f"- 질병분류기호: **{disease_code or '미상'}** → 진단명: **{disease_name}**",
            f"- 처방 약품: {', '.join(med_names) or '정보 없음'}",
            "",
            "### 🚨 중요 지침",
            "- 위 질병분류기호와 진단명은 건강보험심사평가원 공식 데이터 기반 정확한 정보입니다.",
            "- 질병분류기호에 대해 질문받으면 반드시 위의 진단명을 사용하세요.",
            "- 위 정보와 다른 진단명을 절대 임의로 추측하거나 생성하지 마세요.",
            f"- 예: '{disease_code}'는 '{disease_name}'입니다. 다른 진단명으로 안내하지 마세요.",
        ]
        parts.append("\n".join(record_lines))

    if user_health:
        lines = ["", "## 현재 사용자 건강 프로필 (개인화 참고)"]
        age = user_health.get("age")
        gender = user_health.get("gender", "")
        gender_str = {"MALE": "남성", "FEMALE": "여성"}.get(gender, "")
        if age:
            lines.append(
                f"- {age}세 {gender_str}"
                f" | 키 {user_health.get('height_cm', '-')}cm"
                f" | 체중 {user_health.get('weight_kg', '-')}kg"
            )

        allergies = user_health.get("allergies", [])
        if allergies:
            high_risk = [a for a in allergies if a.get("severity") in ("severe", "high")]
            normal = [a for a in allergies if a not in high_risk]
            if high_risk:
                hr_str = ", ".join(f"{a['name']}" for a in high_risk)
                lines.append(f"- ⚠️ 고위험 알러지: {hr_str} — 관련 약품 언급 시 반드시 강력 경고!")
            if normal:
                n_str = ", ".join(f"{a['name']}({a.get('severity', 'unknown')})" for a in normal)
                lines.append(f"- 알러지: {n_str}")

        conditions = user_health.get("conditions", [])
        if conditions:
            lines.append(f"- 기저질환: {', '.join(c['name'] for c in conditions)}")

        lines.append("※ 위 건강 정보와 연관된 약물 위험 언급 시 반드시 경고를 포함하세요.")
        parts.append("\n".join(lines))

    if rag_docs:
        lines = ["", "## 참고 의약 문서 (RAG)"]
        for i, doc in enumerate(rag_docs, 1):
            lines.append(f"[{i}] {doc.page_content[:1000]}")
        lines.append("답변 말미에 '[참고 문서 N]' 형태로 출처를 명시하세요.")
        parts.append("\n".join(lines))

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────
# 일일 건강 팁 프롬프트 (개선: 개인화 + 한국어)
# ─────────────────────────────────────────────────────────────────


def build_daily_tip_prompt(user_health: dict | None = None, season: str | None = None) -> str:
    """
    개인화된 일일 건강 팁 프롬프트

    개선사항:
    - 영어 → 한국어 출력
    - 사용자 기저질환 기반 팁 생성
    - 계절/날씨 컨텍스트 추가
    - 카테고리 다양화
    """
    context_parts = []

    if user_health:
        conditions = [c["name"] for c in user_health.get("conditions", [])]
        if conditions:
            context_parts.append(f"사용자 기저질환: {', '.join(conditions)}")
        age = user_health.get("age")
        gender = user_health.get("gender", "")
        if age:
            gender_str = {"MALE": "남성", "FEMALE": "여성"}.get(gender, "")
            context_parts.append(f"사용자: {age}세 {gender_str}")

    if season:
        context_parts.append(f"현재 계절: {season}")

    context_str = "\n".join(context_parts) if context_parts else "일반 사용자"

    return f"""\
다음 사용자 정보를 참고하여 오늘의 건강 팁을 작성하세요.

{context_str}

카테고리는 다음 중 하나를 선택하세요:
- 복약관리: 약 복용 습관, 보관법
- 영양식이: 건강한 식품, 영양소
- 운동활동: 운동 방법, 신체 활동
- 수면건강: 수면의 질 향상
- 스트레스: 정신 건강, 이완법
- 예방관리: 질병 예방, 검진

반드시 아래 JSON 형식으로만 응답하세요 (마크다운 없이):
{{
  "title": "팁 제목 (20자 이내, 흥미롭고 구체적으로)",
  "subtitle": "한 줄 요약 (40자 이내)",
  "body": "상세 설명 (100-150자, 구체적인 실천 방법 포함)",
  "highlight": "핵심 키워드 또는 수치 (예: '하루 30분', '물 8잔')",
  "category": "카테고리명",
  "color_theme": "green|blue|orange|purple|red|teal 중 카테고리에 맞게",
  "action_tip": "오늘 바로 실천할 수 있는 한 가지 행동 (50자 이내)"
}}\
"""


# ─────────────────────────────────────────────────────────────────
# 약물 상호작용 체크 프롬프트 (신규 추가)
# ─────────────────────────────────────────────────────────────────

INTERACTION_CHECK_SYSTEM = """\
당신은 약물 상호작용 전문 AI입니다.
제공된 약품 목록 간의 상호작용을 분석하고 위험도를 평가합니다.

출력 형식 (순수 JSON):
{
  "interactions": [
    {
      "drug_a": "약품명",
      "drug_b": "약품명 또는 식품",
      "severity": "high|medium|low",
      "mechanism": "상호작용 기전",
      "clinical_effect": "임상적 영향",
      "recommendation": "권고 사항"
    }
  ],
  "overall_risk": "high|medium|low",
  "urgent_warnings": ["즉시 처방 의사에게 알려야 할 사항"]
}
"""


def build_interaction_check_prompt(medications: list, user_health: dict) -> str:
    med_names = [m.get("name", "") for m in medications if m.get("name")]
    conditions = [c["name"] for c in user_health.get("conditions", [])]
    allergies = [a["name"] for a in user_health.get("allergies", [])]

    return f"""\
다음 약품들 간의 상호작용을 분석하세요:

약품 목록: {", ".join(med_names)}
기저질환: {", ".join(conditions) or "없음"}
알러지: {", ".join(allergies) or "없음"}

식품·음료(자몽, 알코올, 유제품 등)와의 상호작용도 포함하세요.
순수 JSON으로만 응답하세요.\
"""
