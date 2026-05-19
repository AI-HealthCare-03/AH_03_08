# 8조 기술 스택 정의서

> 복약 관리 헬스케어 플랫폼 — 요구사항 정의서 v3 · API 명세서 v2 · 시스템 아키텍처 기반  
> **강의 제공 기술 스택 기준 + 서비스 확장성 고려 반영**

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

- **강의 기준 통일**: FastAPI + Docker + AWS EC2 기준 고수
- **비동기 일관성**: FastAPI의 async 환경에 맞춰 ORM·DB 드라이버 모두 비동기 선택
- **AI 파이프라인 추상화**: LLM Provider를 LangChain으로 래핑 → 교체 시 최소 코드 변경
- **확장성 우선**: 소셜 로그인 provider, OCR 공급사, TTS 공급사 모두 인터페이스 뒤로 숨김
- **운영 가시성**: 비동기 작업 실패율, AI Latency, RAG Fallback 비율을 모니터링 가능하도록 설계

---

## 2. Frontend

### 핵심 스택
- **React** 18+: 컴포넌트 기반 SPA
- **TypeScript** 5+: 정적 타입으로 오류 사전 차단
- **Vite** 5+: 빠른 개발 서버
- **React Router** v6: 클라이언트 사이드 라우팅

### 상태 관리 & 데이터 페칭
- **Zustand**: 전역 클라이언트 상태
- **TanStack Query**: 서버 상태 관리, 비동기 작업 폴링
- **Axios**: HTTP 클라이언트, JWT 자동 갱신

### UI / 스타일
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Shadcn/ui**: 접근성 준수 컴포넌트
- **Zod**: 폼 유효성 검사

### 빌드 & 배포
- **ESLint + Prettier**: 코드 스타일 일관성
- **Vercel**: 프론트엔드 호스팅
- **GitHub Actions**: PR 시 Lint·Type Check 자동 실행

---

## 3. Backend

### 웹 프레임워크
- **FastAPI**: REST API 서버 + WebSocket 서버
- **Uvicorn**: ASGI 서버
- **Nginx**: 리버스 프록시

### 비동기 작업 처리
- **Celery**: OCR·LLM·TTS·Image 비동기 Worker
- **Redis**: 작업 큐 메시지 브로커
- **Celery Beat**: 복약 알림 스케줄러

### 실시간 통신
- **FastAPI WebSocket**: 챗봇 실시간 스트리밍
- **Redis Pub/Sub**: 다중 서버 배포 시 WebSocket 세션 공유

---

## 4. 데이터 레이어

### 주 데이터베이스
- **PostgreSQL**: 주 관계형 DB
- **SQLAlchemy** (async): ORM
- **asyncpg**: PostgreSQL 비동기 드라이버
- **Alembic**: DB 마이그레이션

### 인메모리 캐시 / 브로커
- **Redis**: Celery 작업 큐, JWT Blacklist, 챗봇 컨텍스트, 인증코드, Rate Limit

### 파일 스토리지
- **AWS S3**: 처방전·약봉투 이미지·PDF, TTS mp3, 카드뉴스 이미지

### 벡터 데이터베이스 (RAG용)
- **ChromaDB**: 약학정보원·의료 문서 임베딩 저장 및 유사도 검색

---

## 5. AI / ML 파이프라인

### LLM 오케스트레이션
- **LangChain**: LLM API 래핑, 프롬프트 관리, RAG 체인 구성
- **LangChain Memory**: 챗봇 대화 이력 관리

### 임베딩 & 벡터 검색 (RAG)
- **sentence-transformers**: 문서 → 임베딩 벡터 변환
- **ChromaDB**: 벡터 저장 및 유사도 검색
- **LangChain RAG Chain**: 쿼리 → 벡터 검색 → LLM 컨텍스트 주입

### 이미지 처리
- **OpenCV**: 이미지 전처리
- **Pillow**: 카드뉴스 이미지 생성
- **NumPy**: 이미지 배열 처리

### 외부 AI API
- **CLOVA OCR API**: 처방전·약봉투 텍스트 인식
- **LLM API** (OpenAI 등): 복약 가이드 생성, 챗봇 응답
- **Clova TTS API**: 가이드 요약본 → mp3 변환
- **약학정보원 API**: 낱알 약 이미지 분류

---

## 6. 인증 & 보안

- **python-jose**: JWT 생성·검증
- **passlib + bcrypt**: 비밀번호 해싱
- **python-multipart**: 파일 업로드 처리
- **RBAC 미들웨어**: Admin/User 역할 분리
- **AES-256**: 민감 정보 암호화
- **base62**: 인증코드 인코딩

---

## 7. 외부 서비스 연동

### 인증 / 통신
- **Kakao OAuth**: 카카오 인증
- **Google OAuth**: 구글 인증 + Calendar 연동
- **Twilio**: SMS 인증코드 발송
- **Gmail SMTP**: 이메일 인증코드 발송

### AI / 미디어
- **CLOVA OCR API**: 이미지 분석
- **약학정보원 API**: 낱알 이미지 분류
- **Clova TTS API**: TTS 변환
- **Google Calendar API**: 복약 스케줄 동기화

---

## 8. 인프라 & DevOps

### 컨테이너 구성
- **Docker**: 서비스별 컨테이너화
- **Docker Compose**: 로컬 개발 환경
- **AWS EC2**: 운영 서버
- **AWS S3**: 파일 스토리지

### CI/CD
- **GitHub Actions**: Lint, 타입 검사, 테스트 실행, 자동 배포

---

## 9. 코드 품질 & 테스트

- **Ruff**: Python Lint + 자동 포맷팅
- **Mypy**: 정적 타입 검사
- **pytest-asyncio**: 비동기 테스트
- **Coverage**: 테스트 커버리지 측정
- **ESLint + Prettier**: 프론트엔드 코드 품질

---

## 10. 기술 스택 전체 요약표

### Frontend
| 분류 | 기술 |
|------|------|
| 언어 | TypeScript |
| 프레임워크 | React 18 |
| 빌드 | Vite |
| 상태 관리 | Zustand, TanStack Query |
| HTTP | Axios |
| UI | Tailwind CSS, Shadcn/ui |
| 폼 검증 | Zod |
| 배포 | Vercel |
| CI/CD | GitHub Actions |
| 코드 품질 | ESLint, Prettier |

### Backend
| 분류 | 기술 |
|------|------|
| 언어 | Python 3.11+ |
| 프레임워크 | FastAPI |
| ASGI 서버 | Uvicorn |
| 프록시 | Nginx |
| 비동기 큐 | Celery + Redis |
| 스케줄러 | Celery Beat |
| 실시간 통신 | FastAPI WebSocket |

### 데이터 레이어
| 분류 | 기술 |
|------|------|
| 주 DB | PostgreSQL |
| ORM | SQLAlchemy (async) |
| DB 드라이버 | asyncpg |
| 마이그레이션 | Alembic |
| 캐시·브로커 | Redis |
| 파일 스토리지 | AWS S3 |
| 벡터 DB | ChromaDB |

### AI / ML
| 분류 | 기술 |
|------|------|
| LLM 오케스트레이션 | LangChain |
| 임베딩 | sentence-transformers |
| 이미지 처리 | OpenCV, Pillow |
| 수치 연산 | NumPy, Pandas |

### 인증 & 보안
| 분류 | 기술 |
|------|------|
| JWT | python-jose |
| 비밀번호 | passlib + bcrypt |
| 암호화 | cryptography (AES-256) |
| 파일 업로드 | python-multipart |

### 외부 서비스
| 분류 | 기술 |
|------|------|
| 소셜 로그인 | Kakao OAuth, Google OAuth |
| SMS | Twilio |
| 이메일 | aiosmtplib + Gmail SMTP |
| OCR | CLOVA OCR API |
| TTS | Clova TTS API |
| 이미지 분류 | 약학정보원 API |
| 캘린더 | Google Calendar API |

### 인프라 & DevOps
| 분류 | 기술 |
|------|------|
| 컨테이너 | Docker, Docker Compose |
| 서버 | AWS EC2 |
| 스토리지 | AWS S3 |
| CI/CD | GitHub Actions |

### 코드 품질
| 분류 | 기술 |
|------|------|
| 린터·포매터 | Ruff |
| 타입 검사 | Mypy |
| 테스트 | pytest-asyncio |
| 커버리지 | Coverage |
