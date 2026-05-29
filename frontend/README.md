# 메디로그 프론트엔드

건강 기록 기반 맞춤 관리 가이드 서비스, **메디로그**의 프론트엔드입니다.

## 기술 스택

| 분류 | 기술 |
|------|------|
| 프레임워크 | React 18 + TypeScript + Vite |
| 스타일링 | Tailwind CSS v4 + shadcn/ui |
| 상태 관리 | Zustand (클라이언트), TanStack Query (서버) |
| 라우팅 | React Router v6 |
| 폼 | react-hook-form + Zod |
| 알림 | Sonner |
| 아키텍처 | FSD (Feature-Sliced Design) |

## 폴더 구조

```
src/
├── app/            # 앱 진입점, 전역 Provider, 라우터
├── pages/          # 페이지 컴포넌트
├── widgets/        # 레이아웃 단위 복합 컴포넌트 (사이드바, 헤더 등)
├── features/       # 기능 단위 컴포넌트 (업로드, 인증 등)
├── entities/       # 도메인 모델 및 API (user, medical-record, guide)
└── shared/         # 공통 UI, 유틸리티, API 클라이언트
    ├── api/
    ├── lib/
    ├── types/
    └── ui/
```

## 시작하기

```bash
# 의존성 설치
npm install

# 환경변수 설정
cp .env.example .env
# .env의 VITE_API_BASE_URL을 백엔드 주소로 수정

# 개발 서버 실행
npm run dev
```

## 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `VITE_API_BASE_URL` | 백엔드 API 기본 URL | `http://localhost:8000/api/v1` |

## 주요 명령어

```bash
npm run dev       # 개발 서버 실행
npm run build     # 프로덕션 빌드
npm run preview   # 빌드 결과 미리보기
npm run lint      # ESLint 검사

#도커에서 실행
cd frontend
docker run --rm -it -v ${PWD}:/app -w /app -p 5173:5173 node:20 sh -c "npm install && npm run dev -- --host"
```

## 인증 방식

- `access_token`: localStorage 저장 (Zustand persist)
- `refresh_token`: httpOnly 쿠키 (서버 관리)
- 401 응답 시 `/auth/token/refresh` 호출 후 자동 재시도
