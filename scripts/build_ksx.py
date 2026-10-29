#!/usr/bin/env python3
"""(관리용) assets/fonts 원본에서 「자주 쓰는 한글 2,350자 + 영문 · 숫자 · 기호」만 남긴 woff2 를 만든다 → assets/fonts/ksx/.
fontTools 가 없는 PC 에서 render.py 가 이 파일을 그대로 내장한다. OFL 예약 이름이 있는 글꼴(fonts.json 의 embed)은 이름을 바꿔 저장.
사용: pip install fonttools brotli && python3 build_ksx.py
"""
import json, os
from fontTools import subset
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, '..', 'assets')
hangul = ''.join(bytes([a, b]).decode('euc-kr') for a in range(0xB0, 0xC9) for b in range(0xA1, 0xFF))   # KS X 1001 완성형 2,350자
chars = hangul + ''.join(chr(c) for c in range(0x20, 0x7F)) + '·○●→←↑↓~%$₩€£+−×÷=≈≤≥「」『』()[]{}<>※▾▴▸✓…—–‘’“”!?#&*@_|/\\:;,.\'"°'
def rename(font, new):
    ps = new.replace(' ', '')
    for rec in font['name'].names:
        if rec.nameID in (1, 3, 4, 6, 16, 18, 21):
            s = rec.toUnicode(); old = font['name'].getDebugName(16) or font['name'].getDebugName(1)
            rec.string = (s.replace(old, new) if old in s else new) if rec.nameID != 6 else ps + '-' + (font['name'].getDebugName(2) or 'Regular').replace(' ', '')
sets = json.load(open(os.path.join(A, 'fonts.json'), encoding='utf-8')); done = set()
for v in sets.values():
    for r in ('num', 'sans'):
        f = v[r]
        for wt, path in f['files'].items():
            out = os.path.join(A, 'fonts', f['ksx'][wt])
            if out in done: continue
            done.add(out); os.makedirs(os.path.dirname(out), exist_ok=True)
            font = TTFont(os.path.join(A, 'fonts', path)); o = subset.Options(); o.flavor = 'woff2'; o.layout_features = ['*']; o.name_IDs = ['*']
            s = subset.Subsetter(o); s.populate(text=chars); s.subset(font)
            if f.get('embed'): rename(font, f['embed'])
            font.flavor = 'woff2'; font.save(out); print(f"{os.path.getsize(out) // 1024:5d}K {f['ksx'][wt]}")
