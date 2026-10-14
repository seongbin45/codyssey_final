# 저장소 상태

절차는 [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md)를 따른다. 이 문서는 한 시점의 사실이다. 세션을 열 때마다 다시 읽고 고친다.

| 항목 | 값 |
|---|---|
| 기록 시각 | 2026-10-14 |
| 최근 세션 | `C:\Users\seong\.grok\sessions\C%3A%5CUsers%5Cseong%5CDesktop%5CProJect%5Ccodyssey_final\01a138a0-a233-7ca1-843c-3de2a5de06b6` |
| 세션 파일 | `chat_history.jsonl`, `events.jsonl`, `updates.jsonl`, `summary.json`, `prompt_context.json`, `resources_state.json`, `system_prompt.txt`, `tool_definitions.json`, `terminal/` |
| 작업 브랜치 | `docs/agent-workflow`. `origin/docs/agent-workflow`와 같다 (앞 0, 뒤 0) |
| 조사 시점 `HEAD` | `2785bc5` — `docs/agent-workflow` |
| `origin` | `https://github.com/seongbin45/codyssey_final` |
| `team` | `https://github.com/01044402345o-beep/codyssey_final.git` |
| 배포 | `https://codyssey-final.onrender.com` (팀 `main` 머지 시 Render 무료 플랜) |

이 읽기의 git 사실: `HEAD` `2785bc5`는 `origin/docs/agent-workflow`와 같다. 작업 트리에는 `mockup/styles.css` 수정과, 추적되지 않은 루트 `.gitignore`가 있다.

`2785bc5`는 병합이다. 첫 부모는 `ad01d4a`(절차 문서), 둘째 부모는 `68ccfcc`이다. 제목은 `Merge fork main into docs/agent-workflow — 충돌은 PR 쪽 내용으로`이다.

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

## 다음 구현 후보

이번 세션은 디자인 가이드 v1(2026-10-08)이 적은 모서리·포커스·탭·안내 상자·비활성 투명도만 목업에 맞춘다. 아래는 그 다음이다.

1. 가이드에 남아 있는 차이. 색 역할 이름과 잠긴 대비 색(이번 작업의 보류), 간격 6/10/11/13의 전부, 문구 다시 쓰기, 데모 크롬의 11px. 넓은 화면 모달 모서리는 아직 24가 아니다. 작은 버튼 모서리 10px는 가이드와 같다.
2. FR-15. 예시 장소에 교통·숙소를 넣어 `categoryOfKind`가 그 계약을 실제로 호출하게 한다. 뉴욕·보스턴 장소 목록이 있거나, `data.js`와 같은 결의 예시 장소를 만들어도 된다는 확인이 필요하다.

## 사용자에게 요청할 파일

트리에 이미 있어서 다시 받지 않는 것: `other/Project261000/design/`의 DC 세 파일, `docs/RESPONSIVE_STRATEGY.md`, `docs/requirements.md`.

다음에 구현하려면 필요한 것:

1. 2026-10-08보다 새로운 디자인 가이드가 있으면 그 파일. 없으면 현재 DC를 기준으로 쓴다.
2. 다크 모드 팀 검수 메모나 화면 캡처. NFR-08이 이 검수를 미완으로 둔다.
3. 실기기에서 깨진 화면이 있으면 그 캡처(기기, 브라우저, 화면 이름).
4. 사용자는 디자인 가이드와 목업의 차이를 먼저 맞추기로 했다. FR-15 장소 목록은 이번 단계에 쓰지 않는다.

## 이번 작업

목적: `other/Project261000/design/디자인 가이드.dc.html`(v1, 2026-10-08)이 적은 모서리, 키보드 포커스, 탭, 안내 상자, 비활성 투명도를 `mockup/styles.css`에 맞춘다. 제품 동작과 잠긴 대비 색은 그대로 둔다.

이 단계의 CSS는 아래 표를 이 문서에 적기 전에 작업 트리에 들어갔다. 그 편집이 파일을 CRLF로 바꿔 `tokens.test.js`가 토큰 블록을 읽지 못했다. LF로 되돌렸다. 포커스 링 투명도는 처음에 0.35와 0.45였고, 가이드의 0.18과 0.25로 고친 뒤에 대조를 맡긴다. 구현한 쪽은 이 단계를 통과로 적지 않는다.

| 단계 | 목적 | 파일 | 완료 조건 | 읽을 것 |
|---|---|---|---|---|
| 1 | 모서리·포커스·탭·안내 상자·비활성 투명도 | `mockup/styles.css` | 아래 체크리스트. `node --test mockup/tokens.test.js` 7개 통과. 파일은 LF | 디자인 가이드 v1, `mockup/styles.css`, `mockup/tokens.test.js`, `docs/RESPONSIVE_STRATEGY.md`의 대비 보류 |
| 2 | 다른 에이전트가 1을 대조한다 | 위 파일과 가이드 | 불일치가 있으면 고친 뒤 같은 조건으로 다시 본다 | 단계 1과 같음 |
| 3 | 검증 결과를 이 문서에 남기고, `styles.css`와 이 문서만 커밋한 뒤 `origin`의 `docs/agent-workflow`에 푸시한다 | git | `.gitignore`는 넣지 않는다. `team`과 `fix/dup-swipe`는 푸시하지 않는다 | 그 시점의 `git status`, `HEAD` |

단계 1 체크리스트:

- `--r`는 18px, `--r-lg`는 24px. 가이드 문장: 목업 12(입력·행) → 14, 16(카드) → 18, 22(히어로) → 24.
- 라이트 `--focus`는 `#0f6b70`, `--focus-ring`은 `rgba(15, 107, 112, .18)`.
- 다크 두 블록의 `--focus`는 `#4fb3b6`, `--focus-ring`은 `rgba(79, 179, 182, .25)`. 두 블록의 내용은 같다.
- `.tabbar button`과 `.pnav button`은 글자 0.75rem, 색 `--text-soft`. 활성 아이콘은 `--accent`. `.pnav button` 모서리는 14px.
- `.notice`는 모서리 14px, 안쪽 여백 12px 14px, 글자 0.9375rem, 줄간격 1.6, 아이콘 18px. `html:not([data-mode=legacy]) .notice`는 `--fs-body`이고, `--fs-small` 묶음에는 없다.
- 모서리 14px: `.input`, `.add-city`, `.summary-strip > div`, `.cand-toggle`, `.srow`, `.sent`, `.toast`, `.split.coll .split-list .chips button`.
- `.hero`와 `.flip-edge` 두 곳의 모서리는 24px. `.kind` 모서리는 6px.
- `.gbtn:disabled, .btn:disabled`와 `.speak-btn:disabled`의 투명도는 .38.
- 제품 입력칸 `:focus-visible`의 `outline-offset`은 2px.

보류. 이번 단계에서 바꾸지 않는다.

- `--bg` `#fbf8f1`, `--surface` `#ffffff`, `--bg-canvas` `#efe9dd`. 가이드는 이 이름에 다른 색을 붙인다. 테스트와 화면 배경은 지금 값을 잠근다.
- 대비로 잠긴 색: `--accent-text`, `--text`, `--text-2`, `--text-3`, `--text-soft`, `--ok`, `--ok-text`, `--bad`, `--bad-text`, `--accent`, `--on-accent`. 다크 팔레트도 `--focus`와 `--focus-ring`만 바꾼다.
- 칩 회색 네 가지를 `--chip` 하나로 합치지 않는다. 글자 크기 `clamp`는 유지한다. `app.js`, `index.html`, 루트 `.gitignore`는 건드리지 않는다.
- 데모 크롬의 11px, 넓은 화면 모달 모서리, 문구 다시 쓰기, FR-15는 다음이다. `.btn.sm` 모서리 10px는 가이드의 작은 버튼과 같아서 둔다.

검증:

- 단계 1 대조. 다른 에이전트가 통과라고 적었다. 체크리스트의 값이 `mockup/styles.css`에 있고, `node --test mockup/tokens.test.js`는 7개 모두 통과했고, 파일은 LF였다. 색 값 변경은 `--focus`와 `--focus-ring`뿐이었다. `app.js`, `index.html`, `.gitignore`는 diff에 없었다. 그때 이 절은 통과로 적혀 있지 않았다. 헤더는 `HEAD` `2785bc5`, `origin/docs/agent-workflow`와 앞 0 뒤 0, 첫 부모 `ad01d4a`, 둘째 부모 `68ccfcc`, 로컬 `main`은 `origin/main`보다 앞 0 뒤 44와 같았다.
- 화면. `http://127.0.0.1:8769`에서 390px로 열었다. 라이트 `--focus` `#0f6b70`, 링 `rgba(15, 107, 112, .18)`, `--r` 18px, `--r-lg` 24px, 본문 배경 `rgb(251, 248, 241)`, `--surface` `#ffffff`. 히어로 24px, 카드 18px, 비활성 탭 12px이고 색은 `--text-soft`, 활성 아이콘은 `--accent`. 입력칸 14px·글자 16px, 포커스 윤곽은 `solid 2px rgb(15, 107, 112)`에 offset 2px. 안내 상자는 모서리 14px, 글자 15px, 줄간격 24px, 아이콘 18px. 종류 칩 6px, 일정 행 14px, 학습 카드 24px, `.flip-edge` 규칙 두 곳 모두 24px, 문장 14px, 비활성 버튼 투명도 0.38. 홈·입력·보고서·일정·학습·문장 모음에서 12px 미만 글자는 0. 다크 배경 `rgb(18, 21, 28)`, `--focus` `#4fb3b6`, 링 `rgba(79, 179, 182, .25)`, `--bg` `#12151c`.
- `e2e/test_shell.py` 126/126. 320·390·768·1280, 라이트·다크, 터치 44px, 입력 16px, 12px 하한을 포함한다. 실기기 화면은 보지 않았다.
