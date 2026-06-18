# 기술 스택 정의서 — MediLog (8조)

> 실제 구현 및 배포 기준으로 작성 (설계 문서와 다른 부분 반영)

---

## 목차

1. [기술 스택 선정 원칙](#1-기술-스택-선정-원칙)
2. [Frontend](#2-frontend)
3. [Backend](#3-backend)
4. [데이터 레이어](#4-데이터-레이어)
5. [AI / ML 파이프라인](#5-ai--ml-파이프라인)
6. [인증 & 보안](#6-인증--보안)
7. [외부 서비스 연동](#7-외부-서비스-연동)
8. [인프라 & DevOps](#8-인프라--devops)
9. [코드 품질 & 테스트](#9-코드-품질--테스트)
10. [기술 스택 전체 요약표](#10-기술-스택-전체-요약표)

---

## 1. 기술 스택 선정 원칙

- **비동기 일관성**: FastAPI의 async 환경에 맞춰 ORM·DB 드라이버 모두 비동기 선택
- **AI 파이프라인 추상화**: OCRProvider 인터페이스 추상화로 공급사 교체 가능한 구조
- **확장성 우선**: 소셜 로그인 provider, OCR 공급사 모두 인터페이스 뒤로 숨김
- **운영 가시성**: AI Latency, 성공률, 피드백 평점을 DB에 저장하여 관리자 대시보드에서 모니터링

---

## 2. Frontend

### 핵심 스택
- **React 18**: 컴포넌트 기반 SPA
- **TypeScript 5**: 정적 타입으로 오류 사전 차단
- **Vite 5**: 빠른 개발 서버 및 빌드
- **React Router v6**: 클라이언트 사이드 라우팅

### 상태 관리 & 데이터 페칭
- **Zustand**: 전역 클라이언트 상태 (인증 정보 등)
- **TanStack Query**: 서버 상태 관리, OCR 완료 폴링
- **Axios**: HTTP 클라이언트, JWT 자동 갱신 인터셉터

### UI / 스타일
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Shadcn/ui**: 접근성 준수 컴포넌트
- **Zod**: 폼 유효성 검사

### 기타
- **Web Speech API**: 브라우저 내장 음성 합성 (가이드 음성 읽기)
- **Vercel**: 프론트엔드 호스팅 및 자동 배포

---

## 3. Backend

### 웹 프레임워크
- **FastAPI**: REST API 서버 + WebSocket 서버
- **Uvicorn**: ASGI 서버
- **Nginx**: 리버스 프록시, Rate Limit, 보안 강화
- **uv**: Python 패키지 매니저 (pip 대비 빠른 의존성 설치)

### 비동기 작업 처리
- **Celery**: OCR·LLM·Image 비동기 Worker (큐 분리: `llm`, `image`)
- **Redis**: Celery 메시지 브로커 + 결과 백엔드
- **Celery Beat**: 복약 알림 스케줄러 (매 분 실행)

### 실시간 통신
- **FastAPI WebSocket**: 챗봇 토큰 스트리밍
- **SSE (Server-Sent Events)**: 비동기 태스크 완료 알림

---

## 4. 데이터 레이어

### 주 데이터베이스
- **MySQL 8.0**: 주 관계형 DB (utf8mb4)
- **Tortoise ORM**: 비동기 ORM
- **Aerich**: Tortoise ORM 전용 마이그레이션 도구

### 인메모리 캐시 / 브로커
- **Redis**: Celery 브로커, JWT Blacklist, 이메일 인증코드, 일별 건강팁 캐시 (24h TTL)

### 파일 스토리지
- **AWS S3**: 처방전·약봉투 이미지·PDF 저장 (프라이빗 버킷 + Presigned URL)

### 벡터 데이터베이스
- **ChromaDB**: 약학 문서 임베딩 저장 및 유사도 검색 (RAG)

---

## 5. AI / ML 파이프라인

### LLM 오케스트레이션
- **LangChain**: LLM API 래핑, 프롬프트 관리, RAG 체인 구성
- **OpenAI GPT-4o**: 복약 가이드 생성, 챗봇 응답 (temperature=0)

### OCR 파이프라인
- **CLOVA OCR API**: 처방전·약봉투 원문 텍스트 추출
- **OpenAI LLM**: OCR 원문 → 구조화 파싱 (약품명·용법·KCD 코드 등)
- **KCD 코드 정규화**: 공백·O/0·l/1 혼동 후처리 교정

### 질병분류기호 변환
- **로컬 KCD 사전**: 200개+ KCD 코드 → 한국어 진단명 변환 (fallback)
- **HIRA API**: 건강보험심사평가원 질병정보 API (배포 환경)

### 낱알약 이미지 분류
- **ResNet152**: 낱알약 색상·모양 분류 모델
- **CLOVA OCR**: 약물 표면 텍스트 추출 (OCR + 모델 결합으로 정확도 향상)
- **약학정보원 API**: 약품 상세 정보 조회

### 임베딩 & 벡터 검색
- **sentence-transformers**: 문서 → 임베딩 벡터 변환
- **ChromaDB**: 벡터 저장 및 유사도 검색

### 이미지 처리
- **Pillow**: 카드뉴스 이미지 생성

---

## 6. 인증 & 보안

- **JWT (python-jose)**: Access Token + Refresh Token (httpOnly 쿠키)
- **passlib + bcrypt**: 비밀번호 해싱
- **Redis Blacklist**: 로그아웃 시 Access Token 무효화
- **MIME 타입 검증**: 업로드 파일 서버사이드 형식 제한
- **Nginx Rate Limit**: 로그인 엔드포인트 브루트포스 방어
- **SSE 소유자 검증**: 타 사용자 스트림 구독 차단
- **Nginx 내부 URL 차단**: `/api/v1/internal/*` 외부 접근 차단
- **RBAC**: Admin/User 역할 분리

---

## 7. 외부 서비스 연동

| 서비스 | 용도 | 구현 여부 |
|--------|------|----------|
| Google OAuth 2.0 | 소셜 로그인 | ✅ |
| Kakao OAuth 2.0 | 소셜 로그인 | ✅ |
| Gmail SMTP | 이메일 인증코드 발송 | ✅ |
| CLOVA OCR API | 처방전·약봉투 텍스트 추출 | ✅ |
| OpenAI API | LLM 가이드 생성·챗봇 | ✅ |
| 약학정보원 API | 낱알약 약품 정보 조회 | ✅ |
| HIRA API | KCD 질병분류기호 → 진단명 | ✅ (배포 환경) |
| AWS S3 | 이미지·파일 스토리지 | ✅ |

---

## 8. 인프라 & DevOps

### 컨테이너 구성 (Docker Compose)
| 컨테이너 | 역할 |
|---------|------|
| `fastapi` | API 서버 |
| `llm-worker` | LLM·TTS Celery 워커 |
| `ai-worker` | 이미지 분류 Celery 워커 |
| `celery-beat` | 복약 알림 스케줄러 |
| `nginx` | 리버스 프록시 |
| `mysql` | 데이터베이스 |
| `redis` | 캐시·브로커 |
| `frontend` | React 개발 서버 |

### 배포
- **AWS EC2**: 운영 서버 (Ubuntu)
- **Vercel**: 프론트엔드 호스팅
- **GitHub Actions**: PR 검사(Ruff·Mypy·pytest) + EC2/Vercel 자동 배포

---

## 9. 코드 품질 & 테스트

- **Ruff**: Python Lint + 자동 포맷팅
- **Mypy**: 정적 타입 검사
- **pytest-asyncio**: 비동기 API 테스트 (67 passed, 1 skipped)
- **ESLint**: 프론트엔드 코드 품질

---

## 10. 기술 스택 전체 요약표

### Frontend
| 분류 | 기술 |
|------|------|
| 언어 | TypeScript 5 |
| 프레임워크 | React 18 |
| 빌드 | Vite 5 |
| 상태 관리 | Zustand, TanStack Query |
| HTTP | Axios |
| UI | Tailwind CSS, Shadcn/ui |
| 폼 검증 | Zod |
| 음성 합성 | Web Speech API (브라우저 내장) |
| 배포 | Vercel |

### Backend
| 분류 | 기술 |
|------|------|
| 언어 | Python 3.13 |
| 프레임워크 | FastAPI |
| ASGI 서버 | Uvicorn |
| 프록시 | Nginx |
| 패키지 관리 | uv |
| 비동기 큐 | Celery + Redis |
| 스케줄러 | Celery Beat |
| 실시간 통신 | WebSocket, SSE |

### 데이터 레이어
| 분류 | 기술 |
|------|------|
| 주 DB | MySQL 8.0 |
| ORM | Tortoise ORM (async) |
| 마이그레이션 | Aerich |
| 캐시·브로커 | Redis |
| 파일 스토리지 | AWS S3 |
| 벡터 DB | ChromaDB |

### AI / ML
| 분류 | 기술 |
|------|------|
| LLM | OpenAI GPT-4o |
| LLM 오케스트레이션 | LangChain |
| OCR | CLOVA OCR API |
| 이미지 분류 | ResNet152 |
| 임베딩 | sentence-transformers |
| 이미지 처리 | Pillow |

### 인증 & 보안
| 분류 | 기술 |
|------|------|
| JWT | python-jose |
| 비밀번호 | passlib + bcrypt |
| 파일 검증 | MIME 타입 서버사이드 검증 |
| 브루트포스 방어 | Nginx Rate Limit |

### 인프라 & DevOps
| 분류 | 기술 |
|------|------|
| 컨테이너 | Docker, Docker Compose |
| 서버 | AWS EC2 (Ubuntu) |
| 스토리지 | AWS S3 |
| 프론트 배포 | Vercel |
| CI/CD | GitHub Actions |

### 코드 품질
| 분류 | 기술 |
|------|------|
| 린터·포매터 | Ruff |
| 타입 검사 | Mypy |
| 테스트 | pytest-asyncio |
