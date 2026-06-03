"""가이드 LLM 프롬프트용 사용자 건강정보(알러지·기저질환) 반영 테스트."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ai_worker.user_health import build_user_health, load_user_health

pytestmark = pytest.mark.no_db


def test_build_user_health_empty_when_no_user():
    assert build_user_health(None) == {"allergies": [], "conditions": []}


def test_build_user_health_includes_allergies_and_conditions():
    user = SimpleNamespace(
        gender="FEMALE",
        birth_date=date(1995, 3, 15),
        height_cm=165.0,
        weight_kg=55.0,
    )
    allergy_rows = [SimpleNamespace(allergy_name="페니실린", severity="severe")]
    disease_rows = [SimpleNamespace(underlying_disease_name="고혈압")]

    health = build_user_health(user, allergy_rows, disease_rows)

    assert health["allergies"] == [{"name": "페니실린", "severity": "severe"}]
    assert health["conditions"] == [{"name": "고혈압"}]
    assert health["gender"] == "FEMALE"
    assert health["age"] is not None


def test_build_user_health_defaults_severity_when_missing():
    user = SimpleNamespace(gender="MALE", birth_date=None, height_cm=None, weight_kg=None)
    allergy_rows = [SimpleNamespace(allergy_name="아스피린", severity=None)]

    health = build_user_health(user, allergy_rows, [])

    assert health["allergies"] == [{"name": "아스피린", "severity": "unknown"}]


def test_health_profile_formats_like_guide_prompt():
    """llm_prompts.build_guide_user_prompt 과 동일한 문자열 규칙."""
    health = {
        "allergies": [{"name": "페니실린", "severity": "severe"}],
        "conditions": [{"name": "고혈압"}],
    }
    allergies = ", ".join(f"{a['name']}({a['severity']})" for a in health.get("allergies", [])) or "없음"
    conditions = ", ".join(c["name"] for c in health.get("conditions", [])) or "없음"

    assert allergies == "페니실린(severe)"
    assert conditions == "고혈압"


def test_health_profile_empty_lists_show_none_in_prompt():
    health = {"allergies": [], "conditions": []}
    allergies = ", ".join(f"{a['name']}({a['severity']})" for a in health.get("allergies", [])) or "없음"
    conditions = ", ".join(c["name"] for c in health.get("conditions", [])) or "없음"

    assert allergies == "없음"
    assert conditions == "없음"


@pytest.mark.asyncio
async def test_load_user_health_queries_allergies_and_diseases():
    user = SimpleNamespace(gender="MALE", birth_date=date(1990, 1, 1), height_cm=175, weight_kg=70)
    allergy = SimpleNamespace(allergy_name="우유", severity="mild")
    disease = SimpleNamespace(underlying_disease_name="당뇨")

    with (
        patch("ai_worker.models.Allergy") as mock_allergy,
        patch("ai_worker.models.UnderlyingDisease") as mock_disease,
    ):
        mock_allergy.filter.return_value.all = AsyncMock(return_value=[allergy])
        mock_disease.filter.return_value.all = AsyncMock(return_value=[disease])

        health = await load_user_health(user_id=1, user=user)

    mock_allergy.filter.assert_called_once_with(user_id=1)
    mock_disease.filter.assert_called_once_with(user_id=1)
    assert health["allergies"] == [{"name": "우유", "severity": "mild"}]
    assert health["conditions"] == [{"name": "당뇨"}]
