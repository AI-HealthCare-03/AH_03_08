[System.IO.File]::WriteAllText(
    (Resolve-Path "README.md"),
    @'
# AI Healthcare Project (8조)

이 프로젝트는 진료 기록 기반 복약 안내 및 생활습관 개선 가이드를 자동으로 생성하는 AI 헬스케어 서비스입니다.
FastAPI API 서버, LLM 워커, AI 이미지 워커, TTS 워커를 통합한 서비스로, `uv`와 `Docker`를 활용하여 일관된 개발 및 배포 환경을 제공합니다.

---

## 🚀 주요 특징

- **FastAPI Framework**: 고성능 비동기 API 서버 구현.
- **LLM Worker**: LangChain + OpenAI 기반 복약 가이드 및 생활습관 개선 가이드 자동 생성.
- **AI Image Worker**: ResNet152 기반 낱알약 이미지 분류 및 약품 정보 조회.
- **TTS Worker**: OpenAI TTS API 기반 음성 파일(MP3) 생성 및 AWS S3 업로드.
- **OCR**: CLOVA OCR 기반 처방전/약봉투 텍스트 추출.
- **Celery + Redis**: 비동기 태스크 처리 및 스케줄링.
- **ChromaDB**: RAG(Retrieval-Augmented Generation) 기반 벡터 검색.
- **UV Package Manager**: 매우 빠른 의존성 설치 및 가상환경 관리.
- **Tortoise ORM + Aerich**: 비동기 방식의 데이터베이스 모델링 및 마이그레이션 관리.
- **Docker-Compose**: MySQL, Redis, Nginx를 포함한 전체 서비스 스택을 한 번에 실행.
- **CI/CD**: GitHub Actions 기반 자동화 (PR 검사, Vercel 배포, EC2 배포).

---

## 📂 프로젝트 구조

```text
.
├── ai_worker/                  # AI 모델 추론 및 학습 관련 코드 (Worker)
│   ├── card_news/              # 카드뉴스 생성 모듈
│   ├── core/                   # 워커 설정 및 로거
│   ├── image/                  # 낱알약 이미지 분류 모듈
│   ├── ocr/                    # OCR 처리 모듈
│   ├── prompts/                # LLM 프롬프트 정의
│   ├── rag/                    # ChromaDB RAG 모듈
│   ├── tasks/                  # Celery 태스크
│   │   ├── llm_task.py         # LLM 가이드 생성, 챗봇, 데일리 TIP
│   │   ├── image_task.py       # 낱알약 이미지 분류 (ResNet152)
│   │   ├── tts_task.py         # TTS 변환 및 S3 업로드
│   │   ├── ocr_task.py         # OCR 처리
│   │   ├── card_news_task.py   # 카드뉴스 생성
│   │   └── ai_task.py          # 건강 데이터 분석
│   ├── tts/                    # TTS 모듈
│   ├── celery_app.py           # Celery 앱
│   ├── callback.py             # Celery 콜백
│   ├── models.py               # AI 워커 내부 모델 정의
│   ├── user_health.py          # 사용자 건강 정보 유틸
│   └── main.py                 # celery_app re-export (CLI 호환용)
├── app/                        # FastAPI 서버 코드
│   ├── apis/                   # API 라우터 (v1 버전 관리)
│   │   └── v1/
│   │       ├── auth_routers.py         # 회원가입, 로그인, Google/Kakao OAuth
│   │       ├── user_routers.py         # 사용자 정보, 알러지, 기저질환 CRUD
│   │       ├── notification_routers.py # 복약 알림 CRUD
│   │       ├── calendar_routers.py     # 복약 캘린더 CRUD
│   │       ├── asset_routers.py        # TTS/카드뉴스 에셋
│   │       ├── guide_routers.py        # 가이드 조회
│   │       ├── health_routers.py       # 건강 데이터
│   │       ├── image_routers.py        # 낱알약 이미지 분석
│   │       ├── feedback_routers.py     # 피드백
│   │       ├── ai_routers.py           # AI 분석
│   │       └── internal_routers.py     # Worker 콜백 + SSE
│   ├── core/                   # 서버 설정, DB 설정, JWT, Validator 등 핵심 기능
│   │   ├── config.py           # 환경변수 기반 설정
│   │   ├── db/                 # Tortoise ORM 설정 및 Aerich 마이그레이션
│   │   ├── jwt/                # JWT 토큰 발급 및 검증
│   │   └── validators/         # 입력값 유효성 검사
│   ├── dependencies/           # FastAPI 의존성 (인증 등)
│   ├── dtos/                   # 데이터 전송 객체 (Pydantic models)
│   ├── models/                 # DB 테이블 정의 (Tortoise ORM)
│   │   ├── users.py            # 사용자 모델
│   │   ├── guide.py            # 가이드 모델
│   │   ├── llm.py              # LLM 관련 모델
│   │   ├── medical_records.py  # 진료기록 모델
│   │   ├── medications.py      # 약품 모델
│   │   ├── allergies.py        # 알러지 모델
│   │   ├── underlying_diseases.py # 기저질환 모델
│   │   ├── notifications.py    # 알림 모델
│   │   ├── calendar_events.py  # 캘린더 모델
│   │   └── feedbacks.py        # 피드백 모델
│   ├── repositories/           # DB 쿼리 레이어
│   ├── services/               # 비즈니스 로직
│   ├── tests/                  # API 테스트 코드
│   └── main.py                 # FastAPI 애플리케이션 진입점
├── envs/                       # 환경 변수 설정 파일
│   ├── example.local.env       # 로컬 개발용 환경변수 예시
│   └── example.prod.env        # 운영 배포용 환경변수 예시
├── infra/                      # 인프라 설정 관련 디렉터리
│   ├── docker/                 # Docker Compose 설정 (운영용)
│   └── nginx/                  # Nginx 설정 파일 (리버스 프록시)
├── scripts/                    # 배포 및 CI용 쉘 스크립트
├── docker-compose.yml          # 로컬 개발용 서비스 실행 설정
└── pyproject.toml              # uv 기반 의존성 관리 설정
```

---

## 🏗️ 시스템 아키텍처

```text
[Client]
  React + TypeScript + Zustand + TanStack Query
  Kakao/Google OAuth 2.0 | Gmail SMTP 이메일 인증
  Vercel 호스팅 + 자동 배포

        ↕ HTTPS / SSE / OAuth Token

[CI/CD - GitHub Actions]
  PR 검사: Ruff, Mypy, pytest-asyncio
  Vercel 자동 배포 | EC2 배포 (Docker Compose pull & up)

        ↕

[AWS EC2 - Docker Compose]
  Nginx (리버스 프록시 + SSL/TLS + Rate Limit 60/min)
    ↓
  FastAPI (Producer) - Uvicorn
    ├── WebSocket 챗봇 스트리밍
    ├── API 라우터 (auth, records, guides, chat, images, notifications, calendars)
    └── 인증 서비스 (JWT + bcrypt + Google/Kakao OAuth)
    ↓ Redis Streams (XREADGROUP / Pub/Sub / xADD)
  Consumer Group - Celery Workers
    ├── LLM Worker   → LangChain RAG + ChromaDB
    ├── Image Worker → Pillow + 약학정보 API
    ├── TTS Worker   → CLOVA TTS → MP3
    ├── OCR Worker   → CLOVA OCR + OpenCV
    └── Celery Beat  → 복약 알림 스케줄러

[Data Layer]
  MySQL + Tortoise ORM async + Aerich
  Redis (캐시 + Blacklist JWT + 이메일 인증코드 + Celery Broker)
  ChromaDB (벡터 DB + sentence-transformers)

[AWS S3]
  TTS MP3 음성 가이드
  카드뉴스 PNG 가이드 이미지
  낱알약 이미지 (낱알약 정보 분류)
  처방전 PDF 원본 파일
  Static 파일 (React 빌드)
```

---

## ⚙️ 사전 준비 사항

- **Python**: 3.13 이상
- **UV**: Python 패키지 매니저 ([설치 가이드](https://github.com/astral-sh/uv))
- **Docker & Docker-Compose**: 전체 서비스 실행용

---

## 🛠️ 설치 및 설정

### 1. 가상환경 구축 및 의존성 설치

```bash
uv sync
uv sync --group app  # API 서버용
uv sync --group ai   # AI 워커용
```

### 2. 환경 변수 설정

```bash
cp envs/example.local.env .env
```

| 환경변수 | 설명 |
|----------|------|
| `SECRET_KEY` | JWT 서명용 비밀키 |
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 접속 정보 |
| `REDIS_URL` | Redis 접속 URL |
| `OPENAI_API_KEY` | OpenAI API 키 (TTS, LLM) |
| `CLOVA_OCR_URL`, `CLOVA_OCR_SECRET` | CLOVA OCR API 정보 |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `S3_BUCKET_NAME` | AWS S3 접속 정보 |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | Google OAuth 정보 |
| `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI` | Kakao OAuth 정보 |
| `PILL_MODEL_PATH`, `PILL_LABEL_PATH` | 낱알약 분류 모델 경로 |
| `CHROMA_PERSIST_DIR` | ChromaDB 저장 경로 |

---

## 🏃 실행 방법

### Docker Compose로 전체 스택 실행

```bash
docker-compose up -d --build
```

- **API 서버**: http://localhost/api/docs (Swagger UI)

### DB 마이그레이션

```bash
docker-compose exec fastapi uv run aerich upgrade
```

### 개별 실행 (개발용)

```bash
# FastAPI
uv run uvicorn app.main:app --reload

# LLM Worker
uv run celery -A ai_worker.celery_app worker -Q llm -c 2 --loglevel=info

# AI Worker
uv run celery -A ai_worker.celery_app worker -Q ai -c 2 --loglevel=info
```

---

## 🧪 테스트 및 품질 관리

```bash
./scripts/ci/run_test.sh        # 테스트 실행
./scripts/ci/code_fommatting.sh # Ruff 포맷 검사
./scripts/ci/check_mypy.sh      # Mypy 타입 검사
```

---

## 📡 주요 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/auth/signup` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |
| GET | `/api/v1/auth/token/refresh` | 토큰 갱신 |
| POST | `/api/v1/auth/google` | Google 소셜 로그인 |
| POST | `/api/v1/auth/kakao` | Kakao 소셜 로그인 |
| GET | `/api/v1/users/me` | 내 정보 조회 |
| GET | `/api/v1/users/me/allergies` | 알러지 목록 조회 |
| POST | `/api/v1/users/me/allergies` | 알러지 추가 |
| DELETE | `/api/v1/users/me/allergies/{id}` | 알러지 삭제 |
| GET | `/api/v1/users/me/conditions` | 기저질환 목록 조회 |
| POST | `/api/v1/users/me/conditions` | 기저질환 추가 |
| DELETE | `/api/v1/users/me/conditions/{id}` | 기저질환 삭제 |
| GET | `/api/v1/notifications` | 알림 목록 조회 |
| POST | `/api/v1/notifications` | 알림 생성 |
| PUT | `/api/v1/notifications/{id}` | 알림 토글 |
| DELETE | `/api/v1/notifications/{id}` | 알림 삭제 |
| GET | `/api/v1/calendars` | 월별 캘린더 조회 |
| GET | `/api/v1/calendars/{date}` | 일별 캘린더 조회 |
| POST | `/api/v1/calendars` | 복약 스케줄 등록 |
| PUT | `/api/v1/calendars/{id}/status` | 복약 완료 처리 |
| DELETE | `/api/v1/calendars/{id}` | 스케줄 삭제 |
| POST | `/api/v1/records` | 진료기록 생성 |
| GET | `/api/v1/records` | 진료기록 목록 조회 |
| POST | `/api/v1/guides/generate` | 복약 가이드 생성 (LLM) |
| GET | `/api/v1/guides` | 가이드 목록 조회 |
| POST | `/api/v1/guides/{guide_id}/assets` | TTS/카드뉴스 에셋 생성 |
| POST | `/api/v1/images/analyze` | 낱알약 이미지 분석 |

---

## 🗄️ DB 테이블 구조

| 테이블 | 설명 |
|--------|------|
| `users` | 사용자 정보 |
| `medical_records` | 진료기록 (처방전/약봉투) |
| `medications` | 처방 약품 정보 |
| `guides` | 복약 가이드 및 생활습관 개선 가이드 |
| `guide_assets` | 가이드 TTS/카드뉴스 에셋 |
| `chat_sessions` | 챗봇 세션 |
| `chat_messages` | 챗봇 메시지 |
| `calendar_events` | 복약 캘린더 이벤트 |
| `notifications` | 복약 알림 |
| `allergies` | 알러지 정보 |
| `underlying_diseases` | 기저질환 정보 |
| `feedbacks` | 가이드 피드백 |
| `feedback_tags` | 피드백 태그 |
| `access_logs` | API 접근 로그 |
| `audit_logs` | 감사 로그 |
| `error_logs` | 에러 로그 |
| `model_metrics` | AI 모델 성능 지표 |

---

## 📝 개발 가이드

- **API 추가**: `app/apis/v1/` 아래에 새로운 라우터 파일을 생성하고 `app/apis/v1/__init__.py`에 등록하세요.
- **DB 모델 추가**: `app/models/`에 Tortoise 모델을 정의하고 `app/core/db/databases.py`의 `TORTOISE_APP_MODELS` 리스트에 추가하세요.
- **AI 로직 추가**: `ai_worker/tasks/`에 새로운 처리 로직을 작성하고 `ai_worker/celery_app.py`에서 태스크를 등록하세요.
- **마이그레이션**: 모델 변경 후 `aerich migrate` 및 `aerich upgrade`로 DB를 업데이트하세요.
'@,
    [System.Text.UTF8Encoding]::new($false)
)
Write-Host "완료"