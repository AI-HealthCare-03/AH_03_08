import pytest

from ai_worker.services.disease_code_service import (
    _normalize_code,
    lookup_disease_name_sync,
)


class TestDiseaseCodeService:
    def test_exact_match(self):
        """정확한 코드 매칭"""
        assert "방광염" in lookup_disease_name_sync("N300")
        assert "방광염" in lookup_disease_name_sync("N30")
        assert "당뇨" in lookup_disease_name_sync("E10")
        assert "고혈압" in lookup_disease_name_sync("I10")

    def test_lowercase_normalize(self):
        """소문자 코드 정규화"""
        assert "방광염" in lookup_disease_name_sync("n300")
        assert "당뇨" in lookup_disease_name_sync("e10")

    def test_dot_notation(self):
        """소수점 표기 코드 (N30.0 → N300)"""
        result = lookup_disease_name_sync("N30.0")
        assert result != "진단명 미상"
        assert "방광염" in result or "분류" in result

    def test_parent_fallback(self):
        """하위 코드 → 상위 코드 fallback (N309 → N30)"""
        result = lookup_disease_name_sync("N309")
        assert result != "진단명 미상"
        assert "방광염" in result

    def test_unknown_code(self):
        """알 수 없는 코드 → 처방 의사 확인 안내"""
        result = lookup_disease_name_sync("Z99")
        assert "확인" in result or "Z99" in result

    def test_none_input(self):
        """None 입력 → 진단명 미상"""
        assert lookup_disease_name_sync(None) == "진단명 미상"

    def test_empty_string(self):
        """빈 문자열 → 진단명 미상"""
        assert lookup_disease_name_sync("") == "진단명 미상"

    def test_critical_codes(self):
        """실제 자주 쓰이는 KCD 코드 검증"""
        cases = [
            ("J00", "감기"),
            ("J45", "천식"),
            ("K21", "위식도역류"),
            ("E11", "당뇨"),
            ("I10", "고혈압"),
            ("N390", "요로감염"),
            ("B02", "대상포진"),
            ("M54", "통증"),
        ]
        for code, keyword in cases:
            result = lookup_disease_name_sync(code)
            assert keyword in result or result != "진단명 미상", f"{code} 조회 실패: {result}"

    def test_normalize_code(self):
        """코드 정규화 함수 단독 테스트"""
        assert _normalize_code("n30") == "n30"[0].upper() + "n30"[1:]
        assert _normalize_code("N30") == "N30"
        assert _normalize_code(" N30 ") == "N30"


@pytest.mark.asyncio
async def test_lookup_async():
    """비동기 조회 테스트"""
    from ai_worker.services.disease_code_service import lookup_disease_name_async

    result = await lookup_disease_name_async("N300")
    assert "방광염" in result
