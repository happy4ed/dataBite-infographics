---
name: databite-infographic
description: Data Bite 주간 덱 HTML 을 확정된 견본 스타일(크림 종이 · 주홍 강조 · Anton 숫자 · Noto Sans KR)의 한 장 인포그래픽 HTML + PNG 로 만든다. Data Bite 전용 — 다른 문서 · 다른 스타일에는 쓰지 않는다. 트리거 - "Data Bite 인포그래픽", "주간 데이터 바이트 한 장으로", "덱 html 로 인포그래픽", databite infographic.
---

# Data Bite 인포그래픽

Data Bite 주간 덱(HTML) 한 개 → 한 장 인포그래픽(HTML 단일 파일 + PNG) 한 개.

**고정된 것(손대지 않는다):** 글자 크기 · 색 · 간격 · 머리 · 바닥 · 차트 모양 · 그림 화풍. `assets/style.css` 가 견본이다.
**주차마다 달라지는 것:** 내용(명세)과 캔버스 길이뿐. 내용이 많으면 아래로 길어지고, 적으면 짧아진다(폭은 A4 210mm 고정).
**에이전트가 판단하는 것:** 요약(명세 작성)과 그 검수뿐. 배치 · 크기 조정 · 맞춤 반복은 하지 않는다.

## 순서

```bash
SK=<이 스킬 폴더>
python3 $SK/scripts/extract.py deck.html > slides.txt          # 1. 장표 텍스트
# 2. slides.txt + references/SCHEMA.md 만 읽고 spec.json 작성 (에이전트)
python3 $SK/scripts/check_spec.py spec.json slides.txt          # 3. 검수 — 오류 0 될 때까지 명세만 고침
python3 $SK/scripts/illjobs.py spec.json illust/W<주차> > jobs.json   # 4. 그림(선택, 아래 「그림」)
python3 $SK/scripts/render.py spec.json out/DataBite_W<주차>.html --illust illust/W<주차> [--logo logo.png] [--kicker "TEAM · WEEKLY"]
node    $SK/scripts/export.mjs out/DataBite_W<주차>.html           # 5. PNG(3배) + 넘침 점검
```

여러 주차는 4단계까지 주차별로 하고, 5단계는 `export.mjs a.html b.html ...` 한 번에(브라우저 1회).

## 1~3. 요약과 검수 — 이 스킬에서 에이전트가 하는 일의 전부

- 읽을 것은 `slides.txt` 와 `references/SCHEMA.md` 둘뿐. 덱 HTML 원문을 통째로 읽지 않는다(토큰 낭비).
- 항목의 핵심 = 원본 장표 타이틀 내용. `source_title` 에 요약 장 항목 제목을 글자 그대로 적고, `title` 은 그 뜻을 그대로 짧게.
- 크게 쓰는 자리(`hero`)는 타이틀을 직접 받치는 근거 숫자가 있을 때만 숫자, 없거나 약하면 핵심 키워드. 표본 수 · 날짜 · 가격처럼 타이틀 주장을 받치지 않는 숫자는 크게 쓰지 않는다.
- `check_spec.py` 가 숫자 원본 대조 · 문구 규칙을 자동으로 본다. 끝에 나오는 **대조표**(원본 타이틀 ↔ 제목 ↔ 크게)를 읽고 뜻이 바뀐 항목만 고친다. 이것이 검수의 전부다.

## 4. 그림 (선택)

- `gpt-image` 스킬(ChatGPT 구독 · Codex CLI)로 `illjobs.py` 가 만든 작업 파일을 한 번에 돌린다:
  `node <gpt-image 스킬>/scripts/gpt_image.mjs batch --manifest jobs.json --concurrency 4`
- **ChatGPT 이미지 생성이 한도 초과 · 로그인 문제 · 설치 안 됨 · 오류로 안 되면, 그림 생성을 그만두고 그림 없이 인포그래픽을 끝까지 완성한다.** 재시도 · 다른 이미지 생성기 · API 로 우회하지 않는다. `render.py` 는 그림 파일이 없는 항목을 그림 없이 그린다(일부만 성공해도 그대로 진행).
- 작업 파일(jobs.json)은 명령을 실행하는 현재 폴더 안에 둔다(gpt-image 가 작업 폴더 밖 파일을 거부).
- 이미 만든 그림은 `illust/W<주차>/<id>.png` 에 두면 다시 만들지 않는다.

## 5. 결과 확인

- `export.mjs` 출력의 `length`(캔버스 길이) · `issues`(칸 밖 넘침 · 막대 이름 두 줄)를 본다. issues 가 있으면 **명세를 고친다**(이름 줄이기 · 행 줄이기). CSS 나 글자 크기는 바꾸지 않는다.
- PNG 한 장을 열어 한 번 훑어본다. 그 이상의 반복 검사는 하지 않는다.

## 배치 규칙(render.py 가 자동으로 함 · 참고용)

명세 순서대로 줄을 쌓는다. 두 항목이 한 줄(폭은 차트 필요량 비율, 42~58%), 띠가 필요한 항목(차트 2개 · 전후 비교 · 넓은 차트)과 짝이 없는 항목은 한 줄 전체(글 | 차트 | 그림). 줄 높이는 브라우저가 내용으로 정하므로 캔버스 길이가 저절로 맞는다. 인쇄 크기(@page)도 페이지가 열릴 때 그 길이로 잡힌다.

## 준비물

- Python 3 + Pillow, Node 18+ + `playwright`(`npm i` — 이 폴더의 package.json), 인터넷(글꼴 첫 내려받기 · 이후 `~/.cache/databite-infographics` 캐시).
- 로고는 리포에 넣지 않는다. 쓰려면 `--logo` 로 경로를 준다.
