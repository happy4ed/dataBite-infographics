# 동봉 글꼴 · 라이선스

모두 [SIL Open Font License 1.1](https://openfontlicense.org) 글꼴이다. 원본은 [google/fonts](https://github.com/google/fonts) 의 `ofl/` 에서 그대로 가져왔고, 폴더마다 `OFL.txt` 를 함께 둔다.

| 글꼴 | 폴더 | 저작권 · 예약 이름(RFN) |
|---|---|---|
| Anton | `ofl/anton` | The Anton Project Authors · 없음 |
| Noto Sans KR | `ofl/notosanskr` | Adobe · RFN 'Source' (이름 「Noto Sans KR」 에는 해당 없음) |
| Oswald | `ofl/oswald` | The Oswald Project Authors · 없음 |
| Bebas Neue | `ofl/bebasneue` | Dharma Type · 없음 |
| IBM Plex Sans KR | `ofl/ibmplexsanskr` | IBM Corp. · **RFN 'Plex'** |
| Gothic A1 | `ofl/gothica1` | HanYang I&C · 없음 |

## 지키는 것
- 상업적 사용 · 소프트웨어와 함께 배포 가능. 글꼴만 따로 팔지 않는다. 라이선스 문서를 함께 둔다.
- **고친 글꼴(글자 일부만 잘라 낸 것 포함)은 예약 이름을 쓰지 않는다.** 그래서 `ksx/` 의 IBM Plex Sans KR 축약본과, `render.py` 가 잘라 넣는 IBM Plex 는 이름을 **DataBite Sans B** 로 바꿔 둔다(fonts.json 의 `embed`).
- `ksx/` = 자주 쓰는 한글 2,350자(KS X 1001) + 영문 · 숫자 · 기호만 남긴 woff2. fontTools 가 없는 PC 에서 그대로 내장한다. 다시 만들 때는 `scripts/build_ksx.py`.
