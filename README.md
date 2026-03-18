# YouTube2Blog CLI

YouTube URL을 입력하면 영상 내용을 기반으로 한국어 블로그 글(Markdown)을 생성하는 CLI입니다.

## Features

- 단일 YouTube URL 처리
- 자막 우선 추출 (`youtube-transcript-api`)
- 자막 미존재 시 STT 폴백 (`yt-dlp` + OpenAI Audio Transcription)
- 블로그 본문에 `[출처: mm:ss]` 형태 인라인 근거 표기
- 문서 하단 `출처` 섹션에 URL + 타임스탬프 목록 제공

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
```

`.env`에 `OPENAI_API_KEY`를 설정하세요.

## Usage

```bash
python -m youtube2blog "https://www.youtube.com/watch?v=VIDEO_ID" --out ./posts --lang ko
```

성공 시 `posts/{slug}.md` 파일이 생성됩니다.

## Test

```bash
pytest -q
```

## Notes

- 저작권/플랫폼 정책을 준수하기 위해 요약/해설 중심으로 생성하도록 프롬프트를 제한합니다.
- STT 폴백은 네트워크, 파일 다운로드, 모델 호출 환경에 의존합니다.

---

## Plant Care CLI

식물 관리 전용 CLI도 포함되어 있습니다.

### 실행 예시

```bash
python -m plantcare add-plant --name "우리집 몬스테라" --species "몬스테라" --water-interval 5 --pesticide-interval 30
python -m plantcare list-plants
python -m plantcare care --plant-id 1
python -m plantcare log-water --plant-id 1 --date 2026-03-18 --note "충분히 물줌"
python -m plantcare log-pesticide --plant-id 1 --note "응애 예방 약제"
python -m plantcare history --plant-id 1 --type all
python -m plantcare dashboard
```

기본 DB 파일은 `./plantcare.db`이며 `--db`로 경로를 바꿀 수 있습니다.

### Web UI

웹 화면으로도 식물 등록/가이드 조회/물주기 기록/해충약 기록/대시보드 조회가 가능합니다.
또한 월간 캘린더와 D-1/지연 알림을 제공합니다.
식물 등록 시 이미지를 업로드하면 목록/상세에서 확인할 수 있습니다.

```bash
python -m plantcare.web_server --db ./plantcare.db --host 127.0.0.1 --port 5000
```

브라우저에서 `http://127.0.0.1:5000` 접속

- `Dashboard`: D-1/지연 알림 + 다음 일정
- `Calendar`: 월별 물주기/해충약 예정 항목
- `View Plants`: 조회 전용 목록/상세
- `Add Plant`: 등록 전용 화면
- `Delete Plant`: 삭제 전용 목록/확인 화면
