import os
from openai import AsyncOpenAI

# OpenAI 클라이언트 초기화
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_guide_with_llm(medical_record_data: dict, user_info: dict) -> dict:
    """
    진료기록 데이터를 받아서 LLM으로 가이드 생성
    """
    # 프롬프트 구성
    system_prompt = """당신은 전문 의료 상담 AI입니다.
환자의 진료기록과 처방 정보를 바탕으로 복약 안내와 생활습관 개선 가이드를 제공합니다.
반드시 의학적으로 정확한 정보만 제공하고, 불확실한 경우 전문의 상담을 권고하세요."""

    user_prompt = f"""
다음 진료기록을 바탕으로 복약 안내와 생활습관 개선 가이드를 작성해주세요.

진료기록:
{medical_record_data}

환자 정보:
{user_info}

다음 형식으로 작성해주세요:
1. 복약 안내: 각 약품의 복용법, 주의사항
2. 생활습관 개선: 식이요법, 운동, 수면 등
"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3  # 코치님 피드백: 0 말고 최적값 조정
    )

    result = response.choices[0].message.content

    return {
        "medication_guide": result,
        "lifestyle_guide": result,
        "llm_model": "gpt-4o-mini",
        "llm_temperature": 0.3
    }