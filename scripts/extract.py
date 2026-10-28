#!/usr/bin/env python3
"""Data Bite 덱 HTML → 장표별 텍스트(명세 작성 · 검수용). 태그 · 스크립트 · 스타일 제거, 장표 경계는 === SLIDE NN === 로 표시.

사용: python3 extract.py deck.html > slides.txt
덱 HTML 은 남이 만든 파일일 수 있으니 실행하지 않고 텍스트만 읽는다(정규식 처리, 외부 요청 없음).
"""
import html, re, sys

src = open(sys.argv[1], encoding='utf-8', errors='replace').read()
src = re.sub(r'<(script|style|svg|noscript)\b.*?</\1>', ' ', src, flags=re.S | re.I)
src = re.sub(r'<!--.*?-->', ' ', src, flags=re.S)
# 장표 경계: class 에 slide 가 들어간 요소 또는 <section>
parts = re.split(r'<(?:section|div)\b[^>]*class="[^"]*\bslide\b[^"]*"[^>]*>|<section\b[^>]*>', src, flags=re.I)
out = []
for k, p in enumerate(parts[1:] if len(parts) > 1 else parts, 1):
    t = re.sub(r'<br\s*/?>|</(p|div|li|h\d|tr|td|th)>', '\n', p, flags=re.I)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    lines = [re.sub(r'[ \t ]+', ' ', l).strip() for l in t.split('\n')]
    lines = [l for l in lines if l]
    if lines: out.append(f'=== SLIDE {k:02d} ===\n' + '\n'.join(lines))
print('\n\n'.join(out))
