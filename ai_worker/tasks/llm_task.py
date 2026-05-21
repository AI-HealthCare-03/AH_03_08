import os

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_guide_with_llm(medical_record_data: dict, user_info: dict) -> dict:
    system_prompt = """당신은 전문 의료 상담 AI입니다.
환자의 진료기록과 처방 정보를 바탕으로 복약 안내와 생활습관 개선 가이드를 제공합니다.
반드시 의학적으로 정확한 정보만 제공하고, 불확실한 경우 전문의 상담을 권고하세요.
주의: 이 정보는 참고용이며 실제 의료 조언을 대체하지 않습니다."""

    user_prompt = f"""다음 진료기록을 바탕으로 복약 안내와 생활습관 개선 가이드를 작성해주세요.

진료기록: {medical_record_data}
환자 정보: {user_info}

형식:
1. 복약 안내: 각 약품의 복용법, 주의사항
2. 생활습관 개선: 식이요법, 운동, 수면 등"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.3,
    )

    result = response.choices[0].message.content
    return {"medication_guide": result, "lifestyle_guide": result, "llm_model": "gpt-4o-mini", "llm_temperature": 0.3}
