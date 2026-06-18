# MediLog — AI 기반 복약 관리 헬스케어 플랫폼

**서비스 URL**: https://medilog.kro.kr

처방전·약봉투를 업로드하면 OCR로 의약품 정보를 자동 추출하고, LLM이 맞춤형 복약 가이드를 생성합니다.  
처방전 컨텍스트를 이해하는 실시간 챗봇, 복약 캘린더·알림, 낱알약 이미지 인식까지 통합한 의료 정보 관리 서비스입니다.

---

## 핵심 기능

| 기능 | 설명 |
|------|------|
| **OCR 의료정보 인식** | CLOVA OCR + OpenAI 파싱으로 처방전·약봉투에서 약품명·용법·KCD 질병분류기호 자동 추출 |
| **LLM 복약 가이드 생성** | RAG + few-shot 프롬프트로 복약 방법·생활습관·약물 상호작용·알레르기 경고 가이드 생성 |
| **실시간 챗봇** | WebSocket 스트리밍 + 처방전 컨텍스트 주입으로 처방 내용 기반 Q&A |
| **복약 캘린더·알림** | 처방 기간 내 복약 일정 자동 생성, Celery Beat 기반 복약 알림 스케줄러 |
| **낱알약 이미지 분류** | ResNet152 기반 이미지 분류 + 약학정보원 API 연동 |
| **관리자 대시보드** | 사용자·피드백 관리, 프롬프트 버전 관리, AI 성능 지표 모니터링 |

---

## 시스템 아키텍처

```
[Frontend — Vercel]
  React 18 + TypeScript + Vite
  Zustand (클라이언트 상태) + TanStack Query (서버 상태·폴링)
  Tailwind CSS + Shadcn/ui

        ↕ HTTPS / WebSocket

[AWS EC2 — Docker Compose]

  Nginx
  ├── Rate Limit (60 req/min), 악성 UA 차단, 민감 파일 444 반환
  └── /api/v1/internal/* 외부 접근 차단 (Worker 콜백 보호)
         ↓
  FastAPI (Uvicorn)
  ├── REST API — auth, records, guides, medications, calendar, notifications
  ├── WebSocket — 챗봇 실시간 스트리밍
  ├── SSE — 비동기 태스크 완료 알림
  └── JWT + bcrypt + Google/Kakao OAuth 2.0
         ↓ Redis Pub/Sub (Celery 브로커)
  Celery Workers
  ├── LLM Worker  — LangChain RAG + ChromaDB + OpenAI → 복약 가이드 생성
  ├── AI Worker   — ResNet152 낱알약 이미지 분류
  ├── OCR Worker  — CLOVA OCR + OpenAI 파싱 → KCD 코드 정규화
  └── Celery Beat — 복약 알림 스케줄러 (매 분 실행)

[Data Layer]
  MySQL 8.0 + Tortoise ORM (async) + Aerich 마이그레이션
  Redis — Celery 브로커, JWT Blacklist, 이메일 인증코드, 캐시
  ChromaDB — 약학 문서 벡터 임베딩 (RAG)
  AWS S3 — 처방전 이미지·PDF (Presigned URL로 보안 접근)

[CI/CD — GitHub Actions]
  PR: Ruff lint, Mypy 타입 검사, pytest-asyncio (67 passed)
  main 병합 → EC2 Docker Compose 자동 배포
  develop 병합 → Vercel 프론트엔드 자동 배포
```

---

## 기술적 특징

### OCR + LLM 파이프라인
- 업로드 즉시 202 반환 후 **Celery 비동기 처리** — 사용자는 SSE 폴링으로 완료 감지
- CLOVA OCR 원문 → OpenAI 구조화 파싱 → KCD 코드 후처리 정규화(O/0·l/1 혼동 교정)
- `OCRProvider` 인터페이스 추상화로 OCR 공급사 교체 가능한 구조

### 챗봇
- 처방전에서 추출한 **KCD 질병분류기호·처방 약물**을 시스템 프롬프트에 자동 주입
- 세션 단위 대화 히스토리 DB 저장 → 재진입 시 컨텍스트 복원
- 의료 범위 외 질문 거절 처리 및 경고성 답변 `[경고]` 마커 구분
- temperature=0으로 응답 일관성 확보

### 보안
- nginx 단에서 로그인 엔드포인트 **브루트포스 방어** (Rate Limit)
- Worker 콜백 URL `/api/v1/internal/*` 외부 접근 차단
- SSE 스트림 소유자 검증 — 타 사용자 스트림 구독 불가
- S3 Presigned URL — 버킷 직접 노출 없이 이미지 접근
- RefreshToken httpOnly 쿠키 + Access Token 블랙리스트(Redis)

### Clean Architecture (챗봇 도메인)
```
domain/      — 엔티티, 추상 인터페이스 (외부 의존성 없음)
application/ — 유스케이스 (세션·메시지 처리)
infra/       — Tortoise ORM 레포지토리, LLM 클라이언트 구현체
presentation/— FastAPI 라우터
```

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| **Frontend** | React 18, TypeScript, Vite, Zustand, TanStack Query, Tailwind CSS, Shadcn/ui |
| **Backend** | FastAPI, Uvicorn, Tortoise ORM, Aerich, Pydantic v2 |
| **AI/ML** | OpenAI API, LangChain, CLOVA OCR, ChromaDB, sentence-transformers, ResNet152 |
| **비동기 처리** | Celery, Redis, Celery Beat |
| **데이터베이스** | MySQL 8.0, Redis |
| **인프라** | AWS EC2, AWS S3, Docker Compose, Nginx, Vercel |
| **인증** | JWT, bcrypt, Google OAuth 2.0, Kakao OAuth 2.0 |
| **CI/CD** | GitHub Actions (Ruff, Mypy, pytest-asyncio, 자동 배포) |
| **패키지 관리** | uv |

---

## 프로젝트 구조

```
.
├── app/                        # FastAPI 서버
│   ├── apis/v1/                # REST API 라우터 (auth, records, guides, chat 등)
│   ├── models/                 # Tortoise ORM 모델 (19개 테이블)
│   ├── repositories/           # DB 쿼리 레이어
│   ├── services/               # 비즈니스 로직
│   ├── dtos/                   # Pydantic 요청·응답 스키마
│   ├── core/                   # 설정, DB, JWT, 미들웨어
│   └── tests/                  # pytest-asyncio 테스트 (67 passed)
├── ai_worker/                  # Celery 워커
│   ├── tasks/
│   │   ├── llm_task.py         # 복약 가이드 생성, 챗봇, 알림
│   │   ├── ocr_task.py         # OCR 처리
│   │   └── image_task.py       # 낱알약 이미지 분류
│   ├── prompts/                # LLM 프롬프트 정의
│   ├── rag/                    # ChromaDB RAG 모듈
│   └── celery_app.py           # Celery + Beat 스케줄러
├── frontend/                   # React 클라이언트
│   └── src/pages/              # landing, home, medical-record, guide, chatbot,
│                               # calendar, notification, my-page, admin
├── infra/
│   ├── nginx/                  # Nginx 설정 (보안 강화)
│   └── docker/                 # 운영 Docker Compose
├── docs/
│   ├── ERD.md                  # Mermaid ERD
│   ├── TECH_STACK.md           # 기술 스택 정의서
│   └── evaluation/             # AI 모델 평가 스크립트 및 결과
├── scripts/                    # CI 및 배포 스크립트
├── docker-compose.yml          # 로컬 개발용 전체 스택
└── pyproject.toml              # uv 의존성 관리
```

---

## 실행 방법

### 사전 요구사항

- Python 3.13+, uv, Docker & Docker Compose

### 환경 변수 설정

```bash
cp envs/example.local.env .env
```

주요 환경 변수:

| 변수 | 설명 |
|------|------|
| `SECRET_KEY` | JWT 서명 키 |
| `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL 접속 정보 |
| `REDIS_URL` | Redis URL |
| `OPENAI_API_KEY` | OpenAI API 키 (LLM, TTS) |
| `CLOVA_OCR_URL`, `CLOVA_OCR_SECRET` | CLOVA OCR API |
| `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `S3_BUCKET_NAME` | AWS S3 |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET` | Kakao OAuth |

### Docker Compose로 전체 스택 실행

```bash
docker-compose up -d --build
```

- API 서버: `http://localhost:8000/api/docs` (로컬 환경에서만 접근 가능)
- 프론트엔드: `http://localhost:5173`

### DB 마이그레이션

```bash
docker-compose exec fastapi uv run aerich upgrade
```

### 의존성만 설치 (개발용)

```bash
uv sync --group app   # API 서버
uv sync --group ai    # AI 워커
```

---

## 테스트

```bash
# 전체 테스트 실행
docker-compose exec fastapi uv run pytest app/tests/ -q

# 코드 품질 검사
./scripts/ci/run_test.sh
./scripts/ci/code_fommatting.sh   # Ruff
./scripts/ci/check_mypy.sh        # Mypy
```

| 상태 | 수 | 범위 |
|------|----|------|
| ✅ passed | 67 | auth, user, record, chat, tts, image, notification, calendar |
| ⏭️ skipped | 1 | Kakao OAuth mock |
| ❌ failed | 0 | |

---

## API 주요 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/v1/auth/signup` | 이메일 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |
| POST | `/api/v1/auth/google` | Google OAuth |
| POST | `/api/v1/auth/kakao` | Kakao OAuth |
| POST | `/api/v1/records` | 처방전·약봉투 업로드 (OCR 비동기 처리) |
| GET | `/api/v1/records` | 업로드 기록 목록 |
| POST | `/api/v1/guides/generate` | 복약 가이드 생성 (LLM 비동기) |
| GET | `/api/v1/guides` | 가이드 목록 |
| WS | `/api/v1/chats/ws/{session_id}` | 챗봇 WebSocket 스트리밍 |
| GET | `/api/v1/chats/{session_id}/messages` | 대화 히스토리 조회 |
| GET | `/api/v1/calendars` | 월별 복약 캘린더 |
| PUT | `/api/v1/calendars/{id}/status` | 복약 완료 처리 |
| GET | `/api/v1/notifications` | 복약 알림 목록 |
| GET | `/api/v1/images/{record_id}` | 낱알약 분석 결과 조회 |
| POST | `/api/v1/images/pill-match` | 식별코드 기반 약품 매칭 |
| POST | `/api/v1/guides/feedbacks` | 가이드 피드백 등록 |
| GET | `/api/v1/health/medications/drug-search` | 공공데이터 약품 검색 |
