#!/usr/bin/env python3
"""명세 검수 — 요약이 원본을 제대로 옮겼는지만 본다(배치 · 글자 크기는 고정이라 검사 안 함).

1. 숫자 추적: hero · 칩 · 차트의 모든 숫자가 원본 텍스트에 있는지
2. 문구 규칙: 제목 2줄 · 줄당 24자 · 긴 대시 금지 · hero 숫자 반복 금지 · 키워드 2~10자 · 키커 22자 · 칩 3개/8자 · 막대 6행
3. 대조표: 원본 타이틀 ↔ 제목 ↔ hero 를 나란히 출력 → 사람/에이전트가 뜻이 같은지 마지막으로 읽어 본다

사용: python3 check_spec.py spec.json slides.txt   (오류가 있으면 종료 코드 1)
"""
import json, re, sys

S = json.load(open(sys.argv[1], encoding='utf-8')); src = open(sys.argv[2], encoding='utf-8').read()
norm = lambda t: re.sub(r'(?<=\d),(?=\d{3})', '', str(t))
SRC = norm(src); errs, rows = [], []

def num_ok(v):
    s = norm(v).lstrip('+')
    if not re.search(r'\d', s): return True
    for n in re.findall(r'\d+(?:\.\d+)?', s):
        alts = {n, n.rstrip('0').rstrip('.') if '.' in n else n, n + '.0'}
        if not any(re.search(r'(?<![\d.])' + re.escape(a) + r'(?![\d])', SRC) for a in alts): return False
    return True

def chart_nums(c):
    t = (c or {}).get('type', 'none')
    if t == 'multi': return [v for x in c.get('charts', []) for v in chart_nums(x)]
    if t == 'bars': return [r[1] for r in c.get('rows', [])]
    if t == 'line': return list(c.get('y', []))
    if t in ('waffle', 'stack'): return [p[1] for p in c.get('parts', [])]
    if t == 'dumbbell': return [v for g in c.get('groups', []) for pair in g[1:] for v in pair]
    return []

items = S.get('items', [])
if not 1 <= len(items) <= 9: errs.append(f'항목 수 {len(items)} (1~9)')
for it in items:
    i = it.get('id', '?'); title = it.get('title', ''); lines = title.split('\n')
    h = it.get('hero') or ({'kind': 'num', 'value': it['num'], 'unit': it.get('unit', '')} if it.get('num') else None)
    if not it.get('source_title'): errs.append(f'{i} source_title 없음(원본 타이틀을 그대로 적어야 대조 가능)')
    if len(lines) > 2: errs.append(f'{i} 제목 {len(lines)}줄(2줄까지)')
    for l in lines:
        if len(l) > 24: errs.append(f'{i} 제목 한 줄 {len(l)}자(24자까지): {l}')
    if re.search('[—–]', title + it.get('kicker', '')): errs.append(f'{i} 긴 대시 사용')
    if len(it.get('kicker', '')) > 22: errs.append(f'{i} 키커 {len(it["kicker"])}자(22자까지)')
    chips = it.get('chips') or []
    if len(chips) > 3 or any(len(c) > 8 for c in chips): errs.append(f'{i} 칩 3개 · 각 8자까지')
    for c in chips:
        if not num_ok(c): errs.append(f'{i} 칩 숫자가 원본에 없음: {c}')
    if h:
        if h['kind'] == 'num':
            if not num_ok(h['value']): errs.append(f'{i} hero 숫자가 원본에 없음: {h["value"]}')
            if norm(h['value']).lstrip('+') in norm(title): errs.append(f'{i} hero 숫자를 제목에서 반복')
        elif not 2 <= len(h.get('text', '')) <= 10: errs.append(f'{i} 키워드 {len(h.get("text", ""))}자(2~10자)')
    il = it.get('illust') or {}
    if il.get('kind') in ('device', 'app', 'icon') and not (il.get('ref') or {}).get('notes'):
        errs.append(f"{i} 그림 레퍼런스 없음 — 실제 기기 · 앱을 검색해 illust.ref.notes(모양 특징 영어 1~2문장) · ref.source(출처 URL)를 채울 것")
    c = it.get('chart') or {}
    for sub in (c.get('charts', []) if c.get('type') == 'multi' else [c]):
        if sub.get('type') == 'bars' and len(sub.get('rows', [])) > 6: errs.append(f'{i} 막대 {len(sub["rows"])}행(6행까지)')
    bad = [v for v in chart_nums(c) if not num_ok(v)]
    if bad: errs.append(f'{i} 차트 숫자가 원본에 없음: {bad[:5]}')
    hero_txt = '' if not h else (h.get('text') if h['kind'] == 'keyword' else f"{h.get('value')}{h.get('unit', '')}")
    rows.append(f"{i} | 원본: {it.get('source_title', '-')}\n   | 제목: {title.replace(chr(10), ' / ')}\n   | 크게: {hero_txt or '(없음)'} · 차트: {c.get('type', 'none')}")

print('── 대조표: 제목이 원본 타이틀의 뜻을 그대로 살렸는지, 크게 쓴 것이 그 뜻을 받치는지 읽어 볼 것 ──')
print('\n'.join(rows))
print(f'── 규칙 · 숫자 오류 {len(errs)}건 ──'); print('\n'.join(errs) or '없음')
sys.exit(1 if errs else 0)
