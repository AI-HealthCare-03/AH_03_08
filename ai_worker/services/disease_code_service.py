import logging
import os
import xml.etree.ElementTree as ET
 
import httpx
 
logger = logging.getLogger(__name__)
 
_BASE_URL = "https://apis.data.go.kr/B551182/diseaseInfoService1/getDissNameCodeList1"
_SERVICE_KEY = os.getenv("HIRA_API_KEY", "")

_FALLBACK_MAP: dict[str, str] = {
 
    # ── 비뇨기계 (N) ─────────────────────────────────────────────
    "N10":  "급성 세뇨관-간질성 신염 (급성 신우신염)",
    "N11":  "만성 세뇨관-간질성 신염",
    "N12":  "세뇨관-간질성 신염 (급성·만성 불명)",
    "N20":  "신장 및 요관 결석",
    "N200": "신장 결석",
    "N201": "요관 결석",
    "N30":  "방광염",
    "N300": "급성 방광염",
    "N301": "간질성 방광염 (만성)",
    "N308": "기타 방광염",
    "N309": "상세불명의 방광염",
    "N34":  "요도염 및 요도증후군",
    "N39":  "비뇨기계의 기타 장애",
    "N390": "요로감염 (상세불명 부위)",
    "N40":  "전립선 비대증",
    "N41":  "전립선의 염증성 질환",
    "N410": "급성 전립선염",
    "N411": "만성 전립선염",
    "N45":  "고환염 및 부고환염",
    "N73":  "기타 여성 골반 염증성 질환",
    "N76":  "질 및 외음부의 기타 염증",
    "N760": "급성 질염",
    "N761": "아급성 및 만성 질염",
 
    # ── 호흡기계 (J) ─────────────────────────────────────────────
    "J00":  "급성 비인두염 (감기)",
    "J01":  "급성 부비동염",
    "J010": "급성 상악동염",
    "J011": "급성 전두동염",
    "J02":  "급성 인두염",
    "J020": "연쇄상구균성 인두염",
    "J03":  "급성 편도염",
    "J04":  "급성 후두염 및 기관염",
    "J06":  "다발성 및 상세불명 부위의 급성 상기도감염",
    "J069": "상세불명의 급성 상기도감염",
    "J10":  "인플루엔자 (바이러스 확인)",
    "J11":  "인플루엔자 (바이러스 미확인)",
    "J18":  "상세불명 병원체에 의한 폐렴",
    "J180": "기관지폐렴",
    "J181": "대엽성 폐렴",
    "J20":  "급성 기관지염",
    "J21":  "급성 세기관지염",
    "J22":  "상세불명의 급성 하기도감염",
    "J30":  "혈관운동성 및 알레르기성 비염",
    "J301": "꽃가루에 의한 알레르기성 비염",
    "J302": "기타 계절성 알레르기성 비염",
    "J303": "기타 알레르기성 비염",
    "J304": "상세불명의 알레르기성 비염",
    "J32":  "만성 부비동염",
    "J35":  "편도 및 아데노이드의 만성 질환",
    "J350": "만성 편도염",
    "J351": "편도 비대",
    "J40":  "기관지염 (급성·만성 불명)",
    "J41":  "단순성 및 점액화농성 만성 기관지염",
    "J42":  "상세불명의 만성 기관지염",
    "J43":  "폐기종",
    "J44":  "기타 만성 폐쇄성 폐질환 (COPD)",
    "J45":  "천식",
    "J450": "주로 알레르기성 천식",
    "J451": "비알레르기성 천식",
    "J459": "상세불명의 천식",
 
    # ── 소화기계 (K) ─────────────────────────────────────────────
    "K00":  "치아 발육 및 맹출 장애",
    "K02":  "치아 우식증",
    "K05":  "치은염 및 치주 질환",
    "K08":  "치아 및 지지 구조물의 기타 장애",
    "K21":  "위식도역류병 (GERD)",
    "K210": "식도염을 동반한 위식도역류병",
    "K219": "식도염이 없는 위식도역류병",
    "K25":  "위궤양",
    "K26":  "십이지장궤양",
    "K27":  "소화성 궤양 (부위 불명)",
    "K29":  "위염 및 십이지장염",
    "K290": "급성 출혈성 위염",
    "K291": "기타 급성 위염",
    "K295": "만성 표재성 위염",
    "K296": "만성 위축성 위염",
    "K297": "상세불명의 만성 위염",
    "K30":  "기능성 소화불량",
    "K35":  "급성 충수염",
    "K40":  "서혜부 탈장",
    "K50":  "크론병 (국한성 장염)",
    "K51":  "궤양성 대장염",
    "K57":  "장의 게실 질환",
    "K58":  "과민성 대장 증후군 (IBS)",
    "K580": "설사를 동반한 과민성 대장 증후군",
    "K589": "상세불명의 과민성 대장 증후군",
    "K59":  "기타 기능성 장 장애",
    "K590": "변비",
    "K70":  "알코올성 간 질환",
    "K73":  "만성 간염",
    "K74":  "간의 섬유증 및 경화증",
    "K75":  "간의 기타 염증성 질환",
    "K76":  "간의 기타 질환",
    "K80":  "담석증",
    "K81":  "담낭염",
    "K85":  "급성 췌장염",
    "K86":  "췌장의 기타 질환",
    "K92":  "소화기계의 기타 질환",
 
    # ── 내분비·영양·대사 (E) ─────────────────────────────────────
    "E03":  "기타 갑상선기능저하증",
    "E039": "상세불명의 갑상선기능저하증",
    "E04":  "비독성 갑상선종",
    "E05":  "갑상선중독증 (갑상선기능항진증)",
    "E059": "상세불명의 갑상선중독증",
    "E10":  "제1형 당뇨병",
    "E100": "케톤산혈증을 동반한 제1형 당뇨병",
    "E109": "합병증이 없는 제1형 당뇨병",
    "E11":  "제2형 당뇨병",
    "E110": "케톤산혈증을 동반한 제2형 당뇨병",
    "E115": "말초순환 합병증을 동반한 제2형 당뇨병",
    "E119": "합병증이 없는 제2형 당뇨병",
    "E14":  "상세불명의 당뇨병",
    "E55":  "비타민D 결핍증",
    "E559": "상세불명의 비타민D 결핍증",
    "E58":  "식이성 칼슘 결핍증",
    "E61":  "기타 영양소 결핍증",
    "E66":  "비만증",
    "E660": "과다한 열량 섭취로 인한 비만증",
    "E669": "상세불명의 비만증",
    "E78":  "지질단백질 대사장애 및 기타 지질혈증",
    "E780": "순수 고콜레스테롤혈증",
    "E781": "순수 고중성지방혈증",
    "E785": "상세불명의 고지혈증",
    "E79":  "퓨린 및 피리미딘 대사장애 (통풍 관련)",
 
    # ── 순환기계 (I) ─────────────────────────────────────────────
    "I10":  "본태성(원발성) 고혈압",
    "I11":  "고혈압성 심장병",
    "I13":  "고혈압성 심장 및 신장 질환",
    "I20":  "협심증",
    "I200": "불안정 협심증",
    "I209": "상세불명의 협심증",
    "I21":  "급성 심근경색증",
    "I25":  "만성 허혈심장병",
    "I259": "상세불명의 만성 허혈심장병",
    "I48":  "심방세동 및 조동",
    "I50":  "심부전",
    "I63":  "뇌경색증",
    "I64":  "뇌졸중 (출혈·경색 불명)",
    "I70":  "죽상경화증",
    "I83":  "하지의 정맥류",
 
    # ── 근골격계 (M) ─────────────────────────────────────────────
    "M05":  "혈청반응 양성 류마티스 관절염",
    "M06":  "기타 류마티스 관절염",
    "M10":  "통풍",
    "M100": "특발성 통풍",
    "M15":  "다발성 관절증",
    "M16":  "고관절증 (엉덩이 관절염)",
    "M17":  "슬관절증 (무릎 관절염)",
    "M19":  "기타 관절증",
    "M40":  "척추 후만증 및 전만증",
    "M47":  "척추증",
    "M48":  "기타 척추병증",
    "M50":  "경추간판 장애",
    "M51":  "기타 추간판 장애",
    "M510": "요추 및 기타 추간판 장애 (척수병증 동반)",
    "M511": "요추 및 기타 추간판 장애 (신경근병증 동반)",
    "M54":  "등통증",
    "M540": "목통증",
    "M542": "경추통",
    "M544": "요통",
    "M545": "하요통",
    "M75":  "어깨 병변",
    "M750": "유착성 피막염 (오십견)",
    "M79":  "기타 연조직 장애",
    "M800": "골다공증성 척추골절",
    "M810": "폐경후 골다공증",
 
    # ── 정신·신경 (F, G) ─────────────────────────────────────────
    "F10":  "알코올 사용에 의한 정신 및 행동 장애",
    "F17":  "담배 사용에 의한 정신 및 행동 장애",
    "F20":  "조현병 (정신분열병)",
    "F32":  "우울 에피소드",
    "F320": "경도 우울 에피소드",
    "F321": "중등도 우울 에피소드",
    "F322": "정신병적 증상이 없는 중증 우울 에피소드",
    "F329": "상세불명의 우울 에피소드",
    "F33":  "재발성 우울 장애",
    "F40":  "공포불안 장애",
    "F41":  "기타 불안 장애",
    "F410": "공황 장애",
    "F411": "범불안 장애",
    "F419": "상세불명의 불안 장애",
    "F43":  "심한 스트레스에 대한 반응 및 적응 장애",
    "F51":  "비기질성 수면 장애",
    "F90":  "과잉운동 장애 (ADHD)",
    "G20":  "파킨슨병",
    "G35":  "다발성 경화증",
    "G40":  "간질",
    "G43":  "편두통",
    "G430": "전조가 없는 편두통",
    "G431": "전조가 있는 편두통",
    "G439": "상세불명의 편두통",
    "G44":  "기타 두통 증후군",
    "G45":  "일과성 뇌허혈 발작 (TIA)",
    "G47":  "수면 장애",
    "G470": "불면증",
    "G473": "수면무호흡증",
    "G50":  "삼차신경 장애",
    "G54":  "신경근 및 신경총 장애",
    "G62":  "기타 다발신경병증",
 
    # ── 눈 및 귀 (H) ─────────────────────────────────────────────
    "H10":  "결막염",
    "H100": "점액화농성 결막염",
    "H101": "급성 위축성 결막염",
    "H109": "상세불명의 결막염",
    "H25":  "노년성 백내장",
    "H26":  "기타 백내장",
    "H35":  "기타 망막 장애",
    "H40":  "녹내장",
    "H52":  "굴절 및 조절 장애",
    "H524": "노안",
    "H60":  "외이도염",
    "H65":  "비화농성 중이염",
    "H66":  "화농성 및 상세불명의 중이염",
    "H660": "급성 화농성 중이염",
    "H81":  "전정 기능 장애 (어지럼증)",
    "H819": "상세불명의 전정 기능 장애",
 
    # ── 피부 (L) ──────────────────────────────────────────────────
    "L01":  "농가진",
    "L02":  "피부 농양·종기·옹",
    "L03":  "봉와직염",
    "L20":  "아토피성 피부염",
    "L200": "베사니에 가려움증",
    "L209": "상세불명의 아토피성 피부염",
    "L23":  "알레르기성 접촉 피부염",
    "L24":  "자극성 접촉 피부염",
    "L25":  "상세불명의 접촉 피부염",
    "L29":  "가려움증",
    "L30":  "기타 피부염",
    "L40":  "건선",
    "L50":  "두드러기",
    "L509": "상세불명의 두드러기",
    "L60":  "손발톱 장애",
    "L70":  "여드름",
    "L700": "심상성 여드름",
 
    # ── 감염 (A, B) ──────────────────────────────────────────────
    "A00":  "콜레라",
    "A01":  "장티푸스 및 파라티푸스",
    "A02":  "기타 살모넬라 감염",
    "A04":  "기타 세균성 장 감염",
    "A09":  "기타 및 상세불명의 위장염 및 대장염",
    "A15":  "호흡기 결핵",
    "A16":  "호흡기 결핵 (세균 확인 안됨)",
    "A36":  "디프테리아",
    "A37":  "백일해",
    "A46":  "단독 (erysipelas)",
    "A49":  "상세불명 부위의 세균 감염",
    "A53":  "기타 및 상세불명의 매독",
    "A54":  "임균성 감염",
    "A56":  "기타 성적으로 전파된 클라미디아 질환",
    "A60":  "항문생식기 포진바이러스 감염",
    "A63":  "기타 주로 성적으로 전파되는 질환",
    "B00":  "단순 포진바이러스 감염",
    "B01":  "수두",
    "B02":  "대상포진",
    "B020": "대상포진성 뇌염",
    "B022": "대상포진성 삼차신경병증",
    "B029": "합병증이 없는 대상포진",
    "B05":  "홍역",
    "B06":  "풍진",
    "B07":  "바이러스 사마귀",
    "B15":  "급성 A형 간염",
    "B16":  "급성 B형 간염",
    "B17":  "기타 급성 바이러스성 간염",
    "B18":  "만성 바이러스성 간염",
    "B180": "만성 B형 간염 (델타인자 동반)",
    "B181": "만성 B형 간염 (델타인자 없음)",
    "B182": "만성 C형 간염",
    "B19":  "상세불명의 바이러스성 간염",
    "B34":  "상세불명 부위의 바이러스 감염",
    "B35":  "피부사상균증 (무좀 계열)",
    "B37":  "칸디다증",
    "B86":  "옴",
 
    # ── 신생물 (C, D) ────────────────────────────────────────────
    "C00":  "입술의 악성 신생물",
    "C15":  "식도의 악성 신생물",
    "C16":  "위의 악성 신생물",
    "C18":  "결장의 악성 신생물",
    "C20":  "직장의 악성 신생물",
    "C22":  "간 및 간내 담관의 악성 신생물",
    "C25":  "췌장의 악성 신생물",
    "C34":  "기관지 및 폐의 악성 신생물",
    "C50":  "유방의 악성 신생물",
    "C53":  "자궁경부의 악성 신생물",
    "C54":  "자궁체부의 악성 신생물",
    "C56":  "난소의 악성 신생물",
    "C61":  "전립선의 악성 신생물",
    "C64":  "신장의 악성 신생물",
    "C67":  "방광의 악성 신생물",
    "C73":  "갑상선의 악성 신생물",
    "D25":  "자궁의 평활근종 (자궁근종)",
 
    # ── 여성생식기 (N6x, N9x) ────────────────────────────────────
    "N60":  "유방의 양성 유방형성이상",
    "N63":  "상세불명의 유방 덩이",
    "N80":  "자궁내막증",
    "N83":  "난소, 난관 및 광인대의 비염증성 장애",
    "N91":  "무월경, 희소월경 및 희소배란",
    "N92":  "월경과다, 빈발월경 및 불규칙 월경",
    "N94":  "여성 생식기관 및 월경주기와 관련된 통증",
    "N95":  "폐경기 및 기타 여성 갱년기 장애",
    "N950": "폐경후 출혈",
    "N951": "폐경기 및 여성 갱년기 상태",
 
    # ── 임신·출산 (O) ─────────────────────────────────────────────
    "O10":  "기존에 있던 고혈압이 임신에 합병",
    "O20":  "임신 초기의 출혈",
    "O26":  "기타 상태의 임신 합병증",
    "O34":  "알려진 또는 의심되는 태아 위치이상",
    "O80":  "자연 두정위 분만",
 
    # ── 소아·선천성 (P, Q) ───────────────────────────────────────
    "P07":  "임신기간 단축 및 저출생 체중 관련 장애",
    "P22":  "신생아의 호흡 곤란",
    "Q21":  "심장 중격의 선천성 기형",
 
    # ── 손상·중독 (S, T) ─────────────────────────────────────────
    "S00":  "머리의 표재성 손상",
    "S09":  "머리의 기타 및 상세불명의 손상",
    "S20":  "흉부의 표재성 손상",
    "S30":  "복부, 허리 및 골반의 표재성 손상",
    "S40":  "어깨 및 위팔의 표재성 손상",
    "S60":  "손목 및 손의 표재성 손상",
    "S80":  "무릎 및 아래다리의 표재성 손상",
    "S90":  "발목 및 발의 표재성 손상",
    "T14":  "신체 부위 불명의 손상",
    "T36":  "전신 항생제에 의한 중독",
    "T39":  "비아편 진통제, 해열제 및 항류마티스제에 의한 중독",
    "T78":  "달리 분류되지 않은 유해 효과",
    "T780": "음식에 대한 아나필락시스",
    "T782": "상세불명의 아나필락시스",
    "T784": "상세불명의 알레르기 반응",
 
    # ── 증상·징후 (R) ────────────────────────────────────────────
    "R00":  "심박수 이상 (두근거림 등)",
    "R05":  "기침",
    "R06":  "호흡 이상",
    "R07":  "목 및 가슴 통증",
    "R10":  "복통 및 골반통",
    "R11":  "오심 및 구토",
    "R12":  "가슴쓰림",
    "R13":  "연하 곤란",
    "R14":  "고창 및 관련 상태",
    "R19":  "소화기계 및 복부의 기타 증상 및 징후",
    "R50":  "기타 및 상세불명의 발열",
    "R51":  "두통",
    "R52":  "통증 (달리 분류되지 않은)",
    "R53":  "피로감 및 권태감",
    "R55":  "실신 및 허탈",
    "R68":  "기타 일반 증상 및 징후",
 
    # ── 눈·귀 외 감각기 (H 추가) ─────────────────────────────────
    "H91":  "기타 난청",
    "H910": "소음성 난청",
    "H919": "상세불명의 난청",
    "H92":  "이통 및 귀 분비",
    "H93":  "귀의 기타 장애",
}
 
# 런타임 캐시
_runtime_cache: dict[str, str] = {}
 
# ─────────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────────
 
_BASE_URL = "https://apis.data.go.kr/B551182/diseaseInfoService1/getDissNameCodeList1"
_SERVICE_KEY = os.getenv("HIRA_API_KEY", "")   # .env 에 HIRA_API_KEY 추가 필요
 
# 로컬 fallback 사전 (API 호출 실패 시 사용)
_FALLBACK_MAP: dict[str, str] = {
    "N30": "방광염",
    "N300": "급성 방광염",
    "N301": "간질성 방광염",
    "N308": "기타 방광염",
    "N309": "상세불명의 방광염",
    "N390": "요로감염",
    "N10": "급성 신우신염",
    "N20": "신장결석",
    "J00": "급성 비인두염(감기)",
    "J06": "급성 상기도감염",
    "J18": "폐렴",
    "J20": "급성 기관지염",
    "J45": "천식",
    "K21": "위식도역류병",
    "K25": "위궤양",
    "K29": "위염 및 십이지장염",
    "E10": "제1형 당뇨병",
    "E11": "제2형 당뇨병",
    "E78": "고지혈증",
    "I10": "본태성 고혈압",
    "I25": "만성 허혈심장병",
    "M54": "등통증",
    "F32": "우울 에피소드",
    "F41": "불안장애",
    "G43": "편두통",
    "L20": "아토피성 피부염",
    "A09": "감염성 위장염",
}
 
# 런타임 캐시 (프로세스 내 메모리, API 재호출 방지)
_runtime_cache: dict[str, str] = {}
 
 
# ─────────────────────────────────────────────────────────────────
# 핵심 함수
# ─────────────────────────────────────────────────────────────────
 
async def lookup_disease_name_async(code: str | None) -> str:
    """
    질병분류기호 → 한국어 진단명 비동기 조회
 
    우선순위:
    1. 런타임 캐시
    2. HIRA API (HIRA_API_KEY 설정 시 — AWS 배포 후 사용)
    3. 로컬 KCD 사전 (fallback)
    4. 미상 반환
    """
    if not code:
        return "진단명 미상"
 
    normalized = _normalize_code(code)
 
    if normalized in _runtime_cache:
        return _runtime_cache[normalized]
 
    # HIRA API (키 있을 때만)
    if _SERVICE_KEY:
        name = await _fetch_from_api(normalized)
        if name:
            _runtime_cache[normalized] = name
            return name
 
    # 로컬 사전 fallback
    result = _lookup_local(normalized)
    _runtime_cache[normalized] = result
    return result
 
 
def lookup_disease_name_sync(code: str | None) -> str:
    """동기 버전 — Celery 워커 직접 호출용 (로컬 사전만 사용)"""
    if not code:
        return "진단명 미상"
    normalized = _normalize_code(code)
    if normalized in _runtime_cache:
        return _runtime_cache[normalized]
    return _lookup_local(normalized)
 
 
def _lookup_local(normalized: str) -> str:
    """로컬 KCD 사전 조회 (소수점 제거, 상위 코드 fallback 포함)"""
    # 정확히 일치
    if normalized in _FALLBACK_MAP:
        return _FALLBACK_MAP[normalized]
 
    # 소수점 제거 (N30.0 → N300)
    no_dot = normalized.replace(".", "")
    if no_dot in _FALLBACK_MAP:
        return _FALLBACK_MAP[no_dot]
 
    # 소수점 포함 변환 (N300 → N30.0)
    if len(no_dot) >= 4:
        with_dot = no_dot[:3] + "." + no_dot[3:]
        if with_dot in _FALLBACK_MAP:
            return _FALLBACK_MAP[with_dot]
 
    # 상위 코드 fallback (N309 → N30 → N3)
    for length in range(len(normalized) - 1, 2, -1):
        parent = normalized[:length]
        if parent in _FALLBACK_MAP:
            return _FALLBACK_MAP[parent] + " (세부 분류)"
 
    return f"코드 {normalized} — 처방 의사에게 확인 필요"
 
 
def lookup_disease_name_sync(code: str | None) -> str:
    """
    동기 버전 — Celery 워커에서 asyncio.run() 없이 직접 호출 가능
    (캐시 또는 fallback만 사용, API 호출 없음)
    """
    if not code:
        return "진단명 미상"
 
    normalized = _normalize_code(code)
 
    if normalized in _runtime_cache:
        return _runtime_cache[normalized]
 
    no_dot = normalized.replace(".", "")
    for key in [normalized, no_dot, normalized[:3]]:
        if key in _FALLBACK_MAP:
            return _FALLBACK_MAP[key]
 
    return f"코드 {normalized} — 처방 의사에게 확인 필요"
 
 
# ─────────────────────────────────────────────────────────────────
# API 호출 (비동기)
# ─────────────────────────────────────────────────────────────────
 
async def _fetch_from_api(code: str) -> str | None:
    """
    건강보험심사평가원 API 호출하여 진단명 반환
 
    엔드포인트: GET /getDissNameCodeList1
    파라미터:
      - serviceKey: 공공데이터포털 인증키
      - diseaseCode: 질병 분류기호 (예: N300)
      - numOfRows: 1
      - pageNo: 1
    응답: XML
    """
    params = {
        "serviceKey": _SERVICE_KEY,
        "diseaseCode": code,
        "numOfRows": "5",
        "pageNo": "1",
    }
 
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(_BASE_URL, params=params)
 
        if resp.status_code != 200:
            logger.warning(f"[HIRA API] HTTP {resp.status_code} for code={code}")
            return None
 
        return _parse_xml_response(resp.text, code)
 
    except httpx.TimeoutException:
        logger.warning(f"[HIRA API] 타임아웃 code={code}")
        return None
    except Exception as exc:
        logger.warning(f"[HIRA API] 호출 실패 code={code}: {exc}")
        return None
 
 
def _parse_xml_response(xml_text: str, code: str) -> str | None:
    """
    API XML 응답 파싱 → 진단명 추출
 
    응답 구조:
    <response>
      <body>
        <items>
          <item>
            <diseaseCode>N300</diseaseCode>
            <diseaseName>급성 방광염</diseaseName>
            <diseaseEngName>Acute cystitis</diseaseEngName>
            ...
          </item>
        </items>
        <totalCount>1</totalCount>
      </body>
    </response>
    """
    try:
        root = ET.fromstring(xml_text)
 
        # 에러 코드 확인
        result_code = root.findtext(".//resultCode", "")
        if result_code and result_code != "00":
            result_msg = root.findtext(".//resultMsg", "")
            logger.warning(f"[HIRA API] 오류 응답 code={code}: {result_code} {result_msg}")
            return None
 
        items = root.findall(".//item")
        if not items:
            logger.info(f"[HIRA API] 결과 없음 code={code}")
            return None
 
        # 첫 번째 항목에서 진단명 추출
        for item in items:
            item_code = (item.findtext("diseaseCode") or "").strip()
            disease_name = (item.findtext("diseaseName") or "").strip()
 
            if disease_name:
                logger.info(f"[HIRA API] 조회 성공 {code} → {disease_name}")
                return disease_name
 
        return None
 
    except ET.ParseError as exc:
        logger.error(f"[HIRA API] XML 파싱 실패: {exc}")
        return None
 
 
# ─────────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────────
 
def _normalize_code(code: str) -> str:
    """
    코드 정규화:
    - 공백 제거
    - 첫 글자 대문자
    - 소수점은 유지 (N30.0 → N30.0)
    """
    return code.strip()[0].upper() + code.strip()[1:] if code.strip() else code
 
 
async def prefetch_disease_codes(codes: list[str]) -> dict[str, str]:
    """
    여러 코드를 한 번에 조회하여 캐시에 저장
    OCR 완료 시점에 미리 호출하면 챗봇 응답 속도 향상
 
    Args:
        codes: 질병분류기호 목록
 
    Returns:
        {code: disease_name} 딕셔너리
    """
    results = {}
    for code in codes:
        name = await lookup_disease_name_async(code)
        results[code] = name
    return results
 
#  # ─────────────────────────────────────────────────────────────────
# # HIRA API (AWS 배포 후 사용)
# # ─────────────────────────────────────────────────────────────────
 
# async def _fetch_from_api(code: str) -> str | None:
#     params = {
#         "serviceKey": _SERVICE_KEY,
#         "diseaseCode": code,
#         "numOfRows": "5",
#         "pageNo": "1",
#     }
#     try:
#         async with httpx.AsyncClient(timeout=5.0) as client:
#             resp = await client.get(_BASE_URL, params=params)
#         if resp.status_code != 200:
#             return None
#         return _parse_xml_response(resp.text)
#     except Exception as exc:
#         logger.warning(f"[HIRA API] 호출 실패 code={code}: {exc}")
#         return None
 
 
# def _parse_xml_response(xml_text: str) -> str | None:
#     try:
#         root = ET.fromstring(xml_text)
#         for item in root.findall(".//item"):
#             name = (item.findtext("diseaseName") or "").strip()
#             if name:
#                 return name
#         return None
#     except ET.ParseError:
#         return None
 
 
# def _normalize_code(code: str) -> str:
#     s = code.strip()
#     if not s:
#         return code
#     return s[0].upper() + s[1:]

