# AI Healthcare Project (8조)

이 프로젝트는 진료 기록 기반 복약 안내 및 생활습관 개선 가이드를 자동으로 생성하는 AI 헬스케어 서비스입니다.
FastAPI API 서버, LLM 워커, AI 이미지 워커, TTS 워커를 통합한 서비스로, `uv`와 `Docker`를 활용하여 일관된 개발 및 배포 환경을 제공합니다.

---

## 🚀 주요 특징

- **FastAPI Framework**: 고성능 비동기 API 서버 구현.
- **LLM Worker**: LangChain + Anthropic/OpenAI 기반 복약 가이드 및 생활습관 개선 가이드 자동 생성.
- **AI Image Worker**: ResNet152 기반 낱알약 이미지 분류 및 약품 정보 조회.
- **TTS Worker**: OpenAI TTS API 기반 음성 파일(MP3) 생성 및 AWS S3 업로드.
- **OCR**: CLOVA OCR 기반 처방전/약봉투 텍스트 추출.
- **Celery + Redis**: 비동기 태스크 처리 및 스케줄링.
- **ChromaDB**: RAG(Retrieval-Augmented Generation) 기반 벡터 검색.
- **UV Package Manager**: 매우 빠른 의존성 설치 및 가상환경 관리.
- **Tortoise ORM**: 비동기 방식의 데이터베이스 모델링 및 쿼리 관리.
- **Docker-Compose**: MySQL, Redis, Nginx를 포함한 전체 서비스 스택을 한 번에 실행.
- **CI/CD**: GitHub Actions 기반 자동화 (PR 검사, Vercel 배포, EC2 배포).

---

## 📂 프로젝트 구조

```text
.
├── ai_worker/                  # AI 모델 추론 및 학습 관련 코드 (Worker)
│   ├── core/                   # 워커 설정 및 로거
│   ├── prompts/                # LLM 프롬프트 정의
│   ├── task/                   # Celery 태스크 (팀 규칙: task 단수, tasks 폴더 사용 안 함)
│   │   ├── llm_tasks.py        # LLM 가이드 생성, 챗봇, 데일리 TIP
│   │   ├── image_task.py       # 낱알약 이미지 분류 (ResNet152)
│   │   ├── tts_task.py         # TTS 변환 및 S3 업로드
│   │   ├── ocr_task.py         # OCR 처리
│   │   └── ai_tasks.py         # 건강 데이터 분석
│   ├── celery_app.py           # Celery 앱 (워커 기동: -A ai_worker.celery_app)
│   ├── models.py               # AI 워커 내부 모델 정의
│   └── main.py                 # celery_app re-export (CLI 호환용)
├── app/                        # FastAPI 서버 코드
│   ├── apis/                   # API 라우터 (v1 버전 관리)
│   │   └── v1/
│   │       ├── auth_routers.py     # 회원가입, 로그인, 토큰 갱신
│   │       ├── user_routers.py     # 사용자 정보 조회/수정
│   │       ├── llm_routers.py      # 진료기록, 가이드, 채팅 API
│   │       ├── image_routers.py    # 낱알약 이미지 분석 API
│   │       └── ocr_routers.py      # OCR 처방전 업로드 API
│   ├── core/                   # 서버 설정, DB 설정, JWT, Validator 등 핵심 기능
│   │   ├── config.py           # 환경변수 기반 설정
│   │   ├── db/                 # Tortoise ORM 설정 및 마이그레이션
│   │   ├── jwt/                # JWT 토큰 발급 및 검증
│   │   └── validators/         # 입력값 유효성 검사
│   ├── dtos/                   # 데이터 전송 객체 (Pydantic models)
│   ├── models/                 # DB 테이블 정의 (Tortoise ORM)
│   │   ├── users.py            # 사용자 모델
│   │   ├── llm.py              # 진료기록, 가이드, 채팅 모델
│   │   ├── medical_records.py  # 진료기록 모델
│   │   ├── guides.py           # 가이드 모델
│   │   └── ...                 # 기타 모델
│   ├── repositories/           # DB 쿼리 레이어
│   ├── services/               # 비즈니스 로직
│   ├── tests/                  # API 테스트 코드
│   │   ├── auth_apis/          # 인증 API 테스트
│   │   ├── user_apis/          # 사용자 API 테스트
│   │   ├── chat_apis/          # 채팅 API 테스트
│   │   ├── record_apis/        # 진료기록 API 테스트
│   │   ├── image_apis/         # 이미지 API 테스트
│   │   ├── tts_apis/           # TTS API 테스트
│   │   └── conftest.py         # 테스트 픽스처
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
    ├── API 라우터 (auth, records, guides, chat, images)
    └── 인증 서비스 (JWT + bcrypt + RBAC)
    ↓ Redis Streams (XREADGROUP / Pub/Sub / xADD)
  Consumer Group - Celery Workers
    ├── LLM Worker   → LangChain RAG + ChromaDB
    ├── Image Worker → Pillow + 약학정보 API
    ├── TTS Worker   → CLOVA TTS → MP3
    ├── OCR Worker   → CLOVA OCR + OpenCV
    └── Celery Beat  → 복약 알림 스케줄러

[Data Layer]
  MySQL (PostgreSQL) + SQLAlchemy async + Alembic
  Redis (캐시 + Blacklist JWT + 이메일 인증코드 + Celery Broker)
  ChromaDB (벡터 DB + sentence-transformers)
  Google Calendar (복약 스케줄 동기화)

[AWS S3]
  TTS MP3 음성 가이드
  카드뉴스 PNG 가이드 이미지
  날알 이미지 (낱알약 정보 분류)
  처방전 PDF 원본 파일
  Static 파일 (React 빌드)
```

---

## ⚙️ 사전 준비 사항

- **Python**: 3.13 이상 (로컬 개발 환경용)
- **UV**: Python 패키지 매니저 ([설치 가이드](https://github.com/astral-sh/uv))
- **Docker & Docker-Compose**: 전체 서비스 실행용

---

## 🛠️ 설치 및 설정

### 1. 가상환경 구축 및 의존성 설치

`uv`를 사용하여 프로젝트에 필요한 패키지를 설치합니다.

```bash
# 의존성 설치 (가상환경 자동 생성)
uv sync

# 특정 그룹의 의존성만 설치하려는 경우
uv sync --group app  # API 서버용
uv sync --group ai   # AI 워커용
```

### 2. 환경 변수 설정

`envs/` 디렉토리에 있는 예시 파일을 복사하여 `.env` 파일을 생성합니다.

- 로컬용
    ```bash
    cp envs/example.local.env .env
    ```
- 배포용
    ```bash
    cp envs/example.prod.env .env
    ```

생성된 `.env` 파일 내의 주요 환경변수를 설정하세요:

| 환경변수 | 설명 |
|----------|------|
| `SECRET_KEY` | JWT 서명용 비밀키 |
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 접속 정보 |
| `REDIS_URL` | Redis 접속 URL |
| `OPENAI_API_KEY` | OpenAI API 키 (TTS, LLM) |
| `CLOVA_OCR_URL`, `CLOVA_OCR_SECRET` | CLOVA OCR API 정보 |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `S3_BUCKET_NAME` | AWS S3 접속 정보 |
| `PILL_MODEL_PATH`, `PILL_LABEL_PATH`, `PILL_DATA_PATH` | 낱알약 분류 모델 경로 |
| `CHROMA_PERSIST_DIR` | ChromaDB 저장 경로 |

---

## 🏃 실행 방법

### 1. 로컬 및 개발 환경

#### Docker Compose로 전체 스택 실행

모든 서비스(FastAPI, LLM Worker, AI Worker, Celery Beat, MySQL, Redis, Nginx)를 한 번에 실행합니다.

```bash
docker-compose up -d --build
```

실행 후 다음 주소로 접속 가능합니다:
- **API 서버**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs) (Swagger UI)
- **Nginx**: 80 포트를 통해 API 서버로 요청을 전달합니다.

#### DB 마이그레이션

```bash
docker-compose exec fastapi uv run aerich upgrade
```

#### 로컬에서 개별 실행 (개발용)

**FastAPI 서버 실행:**
```bash
uv run uvicorn app.main:app --reload
# or
docker compose up -d --build fastapi
```

**LLM Worker 실행:**
```bash
uv run celery -A ai_worker.celery_app worker -Q llm -c 2 --loglevel=info
# or
docker compose up -d --build llm-worker
```

**AI Worker 실행:**
```bash
uv run celery -A ai_worker.celery_app worker -Q ai -c 2 --loglevel=info
# or
docker compose up -d --build ai-worker
```

### 2. EC2 배포 환경 (Production)

제공된 쉘 스크립트를 사용하여 AWS EC2 환경에 이미지를 빌드, 푸시 및 배포할 수 있습니다.

#### 사전 준비
- EC2 인스턴스 (Ubuntu 권장)
- SSH 키 페어 (`~/.ssh/` 경로에 위치)
- 도커 허브(Docker Hub) 계정 및 Personal Access Token
- 배포용 환경 변수 설정 (`envs/.prod.env`)
- 도메인 구매 (Gabia, GoDaddy, AWS Route53 등)

#### 자동 배포 스크립트 실행

```bash
chmod +x scripts/deployment.sh
./scripts/deployment.sh
```

스크립트 실행 시 다음 정보를 입력해야 합니다:
1. 도커 허브 계정 정보 (Username, PAT)
2. 이미지를 업로드할 레포지토리 이름
3. 배포할 서비스 선택 (FastAPI, AI-Worker) 및 버전(Tag)
4. SSH 키 파일명 및 EC2 IP 주소
5. HTTPS 사용 여부 (사용 시 도메인 추가 입력)

#### SSL(HTTPS) 설정 (Certbot)

도메인을 연결하고 HTTPS를 적용하려면 `scripts/certbot.sh`를 사용합니다.

```bash
chmod +x scripts/certbot.sh
./scripts/certbot.sh
```

1. 도메인 주소 및 이메일 입력
2. SSH 키 파일명 및 EC2 IP 주소 입력
3. Let's Encrypt를 통한 인증서 발급 및 Nginx 설정 자동 갱신 적용

---

## 🧪 테스트 및 품질 관리

제공된 스크립트를 사용하여 코드의 품질을 검증할 수 있습니다.

```bash
# 테스트 실행
./scripts/ci/run_test.sh

# 코드 포맷팅 확인 (Ruff)
./scripts/ci/code_fommatting.sh

# 정적 타입 검사 (Mypy)
./scripts/ci/check_mypy.sh
```

---

## 📡 주요 API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/auth/signup` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |
| GET | `/api/v1/auth/token/refresh` | 토큰 갱신 |
| GET | `/api/v1/users/me` | 내 정보 조회 |
| PATCH | `/api/v1/users/me` | 내 정보 수정 |
| POST | `/api/v1/records` | 진료기록 생성 |
| GET | `/api/v1/records` | 진료기록 목록 조회 |
| GET | `/api/v1/records/{record_id}` | 진료기록 상세 조회 |
| POST | `/api/v1/guides/generate` | 복약 가이드 생성 (LLM) |
| GET | `/api/v1/guides` | 가이드 목록 조회 |
| GET | `/api/v1/guides/{guide_id}` | 가이드 상세 조회 |
| POST | `/api/v1/guides/{guide_id}/assets` | TTS/카드뉴스 에셋 생성 |
| GET | `/api/v1/chat/sessions` | 채팅 세션 목록 조회 |
| POST | `/api/v1/chat/sessions` | 채팅 세션 생성 |
| POST | `/api/v1/chat/sessions/{session_id}/messages` | 메시지 전송 |
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
- **AI 로직 추가**: `ai_worker/task/`에 새로운 처리 로직을 작성하고 `ai_worker/celery_app.py`에서 태스크를 등록하세요.
- **마이그레이션**: 모델 변경 후 `aerich migrate` 및 `aerich upgrade`로 DB를 업데이트하세요.
