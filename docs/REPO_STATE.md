# 저장소 상태

절차는 [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md)를 따른다. 이 문서는 한 시점의 사실이다. 세션을 열 때마다 다시 읽고 고친다.

| 항목 | 값 |
|---|---|
| 기록 시각 | 2026-10-14 |
| 최근 세션 | `C:\Users\seong\.grok\sessions\C%3A%5CUsers%5Cseong%5CDesktop%5CProJect%5Ccodyssey_final\01a138a0-a233-7ca1-843c-3de2a5de06b6` |
| 세션 파일 | `chat_history.jsonl`, `events.jsonl`, `updates.jsonl`, `summary.json`, `prompt_context.json`, `resources_state.json`, `system_prompt.txt`, `tool_definitions.json`, `terminal/` |
| 작업 브랜치 | `docs/agent-workflow`. `origin/docs/agent-workflow`와 같다 (앞 0, 뒤 0) |
| 조사 시점 `HEAD` | `a1fa890` — `docs/agent-workflow` |
| `origin` | `https://github.com/seongbin45/codyssey_final` |
| `team` | `https://github.com/01044402345o-beep/codyssey_final.git` |
| 배포 | `https://codyssey-final.onrender.com` (팀 `main` 머지 시 Render 무료 플랜) |

이 읽기의 git 사실: `HEAD` `a1fa890`는 `origin/docs/agent-workflow`와 같다. 부모는 `2785bc5`. 제목은 `style(mockup): 디자인 가이드의 모서리·포커스·탭·안내 상자를 맞춘다`. 작업 트리는 `docs/ASSIGNMENT.md`(새 파일), `docs/REPO_STATE.md`, `docs/rubric.md`와 추적되지 않은 루트 `.gitignore`이다. `mockup/` 수정은 없다.

`2785bc5`는 병합이다. 첫 부모는 `ad01d4a`, 둘째 부모는 `68ccfcc`이다. 디자인 가이드를 맞춘 커밋은 `a1fa890`에서 멈춘다.

로컬 `main`은 `origin/main`보다 44커밋 뒤이고, 앞은 0이다. 평가·배포 기준은 팀 저장소 `main`이다.

추적되지 않은 루트 `.gitignore`는 Next.js 템플릿이다. 이 제품은 바닐라 JS와 FastAPI라 그 파일은 커밋하지 않는다.

## 구조

```
.                         현재 제품
├── README.md             제품 설명 (현행)
├── prd.md                초기 기획 (Firebase, 이력)
├── 기술스택.md            초기 기술 구조 (이력)
├── 시나리오.md            시나리오 초안 (이력)
├── 시나리오완료.MD        기능·규칙 상세 (이력)
├── render.yaml           Render 배포
├── agent_contract/       카테고리 계약. restaurant, transport, lodging
├── backend/              FastAPI. /health, /generate, /speak-check
├── mockup/               화면. index.html, app.js, ai.js, data.js, styles.css
├── e2e/                  Playwright 시나리오
├── docs/                 현행 요구사항, 반응형, 배포, 연구, 측정, 사용자 테스트
└── other/                아이디어·자료. 런타임에 서빙하지 않음
    └── Project261000/
        ├── codyssey_final/   루트보다 오래된 사본 (lodging.json 없음)
        ├── design/           디자인 가이드.dc.html (2026-10-08), 반응형 전략.dc.html, 반응형 전략 v2.dc.html
        ├── output/           발표 HTML·슬라이드
        ├── resorce/          기획 PDF, 진단, 체크리스트 (폴더명 철자 그대로)
        └── transcribe_app/   다른 프로그램. 이 제품의 범위 밖
```

제품은 여행지와 일정을 넣으면 갈 장소에서 쓸 영어 문장을 만들고, 말해 보고, 어려웠던 상황을 브라우저에 기억하는 학습 서비스다. 화면과 API는 같은 주소에서 서빙한다. AI가 하는 일은 문장 생성(`/generate`), 말하기 채점(`/speak-check`), 어려웠던 상황의 다음 생성 반영이다. 장소 목록은 예시 데이터다.

## `.`에서 열려 있는 일

기준 문서: `docs/requirements.md` (2026-10-09, 커밋 `f78b23b` 시점 표기). 아래는 그 문서가 완료로 두지 않은 항목이다.

| ID | 상태 | 코드에서 확인한 내용 |
|---|---|---|
| FR-03 장소 보고서 | 예시 | `mockup/data.js` `PLACE_POOLS`. 뉴욕·보스턴은 관광지·맛집만 있음 |
| FR-04 방문 순서 | 예시 | 코드 배치 |
| FR-15 교통·숙소 생성 | 부분 | 계약 3종은 `agent_contract/categories/`에 있다. `mockup/ai.js` `categoryOfKind`는 식당·카페→restaurant, 공항·역·택시→transport, 호텔·호스텔·게스트하우스·에어비앤비→lodging. `genReport`(`mockup/app.js`)는 장소를 `attraction`과 `restaurant`로만 만든다. `attraction`은 계약 밖이라 생성 요청은 식당만 나간다 |
| FR-16 로그인·서버 저장 | 예정 | 데모 사용자와 브라우저 저장 |
| NFR-08 화면 | 부분 | 반응형·다크·넓은 화면 배치는 구현 기록이 `docs/RESPONSIVE_STRATEGY.md`에 있다. 남은 것: 실기기(iOS Safari·iPad), 다크 모드 팀 디자인 검수, 브라우저 뒤로가기와 날짜 선택 |
| 장소 보강 파이프라인 | 제안 | `docs/ENRICHMENT_PIPELINE.md`는 미구현 |

`README.md`의 알려진 한계는 이 표의 FR-15와 같다. 예시 장소는 관광지·맛집뿐이고, 생성 요청은 식당만 나간다.

## `./other`에서 가져올 수 있는 것

| 자료 | 쓰는 조건 |
|---|---|
| `design/디자인 가이드.dc.html` | 2026-10-08 가이드 v1. 색·글자·부품. 출처로 `mockup/styles.css`를 들고, 목업과 다른 값을 표에 적는다 |
| `design/반응형 전략 v2.dc.html`, `반응형 전략.dc.html` | 초안. `docs/RESPONSIVE_STRATEGY.md`가 바닐라 CSS 기준으로 다시 적었고, React·Vite·Tailwind 전제는 따르지 않는다 |
| `output/` | 발표 구성. 제품 동작을 바꾸려면 `docs/requirements.md`와 코드를 먼저 본다 |
| `resorce/` | 과제 원문, 상세기획서, 2026-10-04 진단(스코프 과대, 기술 요소 미달). 진단이 제안한 말하기·기억은 현재 제품에 들어가 있다 |
| `codyssey_final/` | 오래된 사본. 루트에 없는 기능을 여기서 현재인 것처럼 가져오지 않는다 |
| `transcribe_app/` | 범위 밖 |

## 동결

2026-10-14에 사용자가 정한 것이다.

- 디자인 가이드 적용은 `a1fa890`에서 멈춘다.
- `team`에는 푸시하지 않는다. 팀 저장소로는 나중에 PR을 연다.
- `mockup/`은 2차 테스트가 끝나는 2026-10-22까지 동결이다.
- 그때까지 저장소에서 할 일은 과제 원문 요건 확인이다. 2차 테스트에서 나온 버그만 고친다.

## 다음 구현 후보

2026-10-22 전에는 아래를 구현하지 않는다.

1. 디자인 가이드에 남아 있는 차이.
2. FR-15. 예시 장소에 교통·숙소를 넣는 일.
3. 2차 테스트 버그가 아닌 기능 추가.

## 사용자에게 요청할 파일

과제 원문은 받았다. 사용자가 적은 `C:\User\seong\Downloads\과제원문.html`은 없다. 같은 바이트는 `C:\Users\seong\Downloads\과제원문.html`과 작업 트리 `other/Project261000/resorce/과제원문.html`이다. sha256 `85b7eec5898e687b31528492e0522b97f730b8c7d1206d7808917500ae271fc7`. `git ls-files other`는 0건이다. 작업 트리 `.gitignore`가 `/other/`를 무시하고, 그 `.gitignore`는 커밋하지 않는다.

아직 저장소에 없는 것:

1. 팀 6인에 대한 운영진 예외 승인. `docs/rubric.md`가 확인을 요구하고, 추적된 문서에는 승인이 없다.
2. 2026-10-22 2차 테스트의 과업 성공률·설문. `docs/user-test/results.md`의 그 칸은 비어 있다.

## 이번 작업

목적: 과제 원문(2026-10-07 저장, 프로젝트 143001)의 필수 문장을 `docs/ASSIGNMENT.md`에 고정하고, `docs/rubric.md`의 인용과 저장소 문서가 그 문장과 어디가 같은지 적는다. `mockup/`은 수정하지 않는다. `team`에는 푸시하지 않는다.

| 단계 | 목적 | 파일 | 완료 조건 | 읽을 것 |
|---|---|---|---|---|
| 1 | 원문 필수 문장과 저장소 대응을 적는다 | `docs/ASSIGNMENT.md`, `docs/rubric.md`의 원문 출처 주석, 이 문서 | 아래 체크리스트 | 과제원문.html, `docs/rubric.md`, `README.md`, `docs/requirements.md`, `docs/user-test/results.md` |
| 2 | 다른 에이전트가 1을 대조한다 | 위 파일과 원문 | 불일치가 있으면 고친 뒤 같은 조건으로 다시 본다 | 단계 1과 같음 |
| 3 | 검증 결과를 이 문서에 남기고, 그 문서들만 커밋한 뒤 `origin`의 `docs/agent-workflow`에 푸시한다 | git | `.gitignore`와 `mockup/`과 `other/`는 넣지 않는다. `team`은 푸시하지 않는다 | 그 시점의 `git status`, `HEAD` |

단계 1 체크리스트:

- 원문 URL, 저장 시각, sha256, 두 경로가 같다는 사실, git에 없다는 사실이 있다.
- 필수 문장을 원문 절 번호와 함께 인용한다. 4절 주제·기술 요소 5종·팀 인원, 6절 필수 요건·AI 윤리, 2절 배포 문장.
- `docs/rubric.md` R1~R5 인용을 그 문장과 비교해, 같은 것과 글자가 다른 것을 구분한다.
- 각 필수 항목이 어느 저장소 문서에 어떻게 적혀 있는지 파일 경로를 붙인다.
- README 2절 이름이 6명이고, 예외 승인 문서는 없다는 내용이 있다.
- README 9절은 실사용자 테스트가 예정이라고 하고, `docs/user-test/results.md`에는 P1~P5가 있다는 차이를 적는다.
- Long-term Memory 원문 정의와 브라우저 저장 한계를 둘 다 적는다. 충족 여부를 이 문서가 확정하지 않는다.
- 동결 네 줄이 이 문서에 있다.
- `mockup/` diff가 없다.

검증:

- 단계 1 첫 대조: 불일치. 두 HTML의 sha256, URL, 저장 시각, R1·R4·R5 글자, R3의 빠진 "서비스", README 여섯 이름, 9절의 "예정", `results.md`의 P1~P5, 동결, `HEAD` `a1fa890`은 맞았다. 2절 기능 요구 명세서와 팀 문장, 4절 수행 문장이 원문보다 줄여 적혀 있었다.
- 그 문장을 원문 그대로 고친 뒤 같은 단계 재대조: 다른 에이전트가 통과라고 적었다. 2절 표의 문장 37개가 원문 본문에 연속된 글자로 있다. `mockup/` 변경은 없다.
