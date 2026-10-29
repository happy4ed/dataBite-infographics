#!/usr/bin/env python3
"""Data Bite 인포그래픽 생성기 — 명세(JSON) → 한 장 HTML(그림 · 글꼴 내장).

스타일(글자 크기 · 색 · 간격)은 견본으로 고정. 배치는 명세 순서대로 줄을 쌓고(한 줄 = 두 칸 또는 띠 한 칸),
줄 높이는 브라우저가 내용으로 정한다 → 캔버스 길이가 내용에 따라 저절로 늘고 준다. 맞춤 반복 없음.

사용: python3 render.py spec.json out.html [--illust DIR] [--logo logo.png] [--kicker "TEAM · WEEKLY"] [--footer TEXT]
"""
import argparse, base64, hashlib, html, io, json, math, os, re, subprocess, sys, urllib.parse
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser('~/.cache/databite-infographics')
esc = lambda t: html.escape(str(t), quote=True)

# ── 크기 추정(고정 글자 크기 기준, mm) — 칸 나누기 · 막대 이름 칸 폭에만 씀 ──
BODY_W, GAP, LEAD_W = 190, 5, 64
def tw(t, fs): return sum(fs * (1.0 if ord(ch) > 0x2E80 else .6) for ch in str(t))
def fmt(v, unit):
    v = f'{v:g}' if isinstance(v, (int, float)) else str(v)
    return f'{unit}{v}' if unit in ('$', '₩', '€', '£') else f'{v}{unit or ""}'
def bar_cols(c):
    rows = c['rows'][:6]; u = c.get('unit', '')
    return min(40, max(12, max(tw(r[0], 2.9) for r in rows) * 1.06 + 1)), max(8, max(tw(fmt(r[1], u), 2.9) for r in rows) + 1.5)
def chart_need(c):
    t = c.get('type', 'none')
    if t == 'bars': bl, bv = bar_cols(c); return bl + bv + 34
    if t == 'line': return 90
    if t == 'multi': return 2 * 62 + 7
    if t == 'dumbbell': return 96
    if t in ('waffle', 'stack'): return 70
    return 0
def is_full(it):   # 띠 한 칸이 필요한 항목
    c = it.get('chart') or {}; t = c.get('type', 'none')
    return (t == 'multi' and len(c.get('charts', [])) > 1) or t == 'dumbbell' or chart_need(c) > 100

# ── 차트 ──
def bars(c, avail):
    rows = c['rows'][:6]; mx = c.get('max') or max(r[1] for r in rows) or 1; hi = c.get('highlight'); u = c.get('unit', '')
    bl, bvw = bar_cols(c); stk = avail - bl - bvw - 3.2 < 24   # 막대 칸이 24mm 미만이면 이름을 막대 위로
    return f'<div class="bars{" stk" if stk else ""}" style="--bl:{bl:.1f}mm;--bvw:{bvw:.1f}mm">' + ''.join(
        f'<div class="br{" hi" if k == hi else ""}"><span class="bl">{esc(l)}</span><span class="bt"><i style="width:{min(100, v / mx * 100):.1f}%"></i></span><span class="bv">{esc(fmt(v, u))}</span></div>'
        for k, (l, v) in enumerate(rows)) + '</div>'
def md(x): m = re.match(r'^(\d{1,2})-(\d{1,2})$', str(x)); return f'{int(m.group(1))}/{int(m.group(2))}' if m else str(x)
def line(c):
    x, y = c['x'], c['y']; n = len(y); w, h = 100, 34; base = h - 7; top, lo = max(y), min(y)
    floor = 0 if lo < top * .5 else lo - (top - lo) * .8   # 값이 좁은 범위에서 움직이면 아래를 잘라 변화가 보이게
    mx = (top - floor) * 1.15 or 1
    X = lambda i: 3 + i * (w - 6) / max(1, n - 1); Y = lambda v: base - (v - floor) / mx * (base - 5)
    pts = ' '.join(f'{X(i):.2f},{Y(v):.2f}' for i, v in enumerate(y)); area = f'{X(0):.2f},{base} {pts} {X(n - 1):.2f},{base}'
    k = max(1, math.ceil((n - 1) / 4)); idx = list(range(0, n, k))   # 눈금 = 같은 간격
    marks = ''.join(f'<line x1="{X(i):.2f}" y1="{base}" x2="{X(i):.2f}" y2="{base + (1.4 if i in idx else .7)}" class="tk"/>' for i in range(n))
    anc = lambda i: 'start' if i == 0 else 'end' if i == n - 1 else 'middle'   # 양 끝 눈금 글자가 칸 밖으로 안 나가게
    ticks = ''.join(f'<text x="{X(i) - (1 if i == 0 else -1 if i == n - 1 else 0):.2f}" y="{h - 1.2}" class="t" text-anchor="{anc(i)}">{esc(md(x[i]))}</text>' for i in idx)
    lbl = ''; imax = max(range(n), key=lambda i: y[i])
    kept = []
    for L in sorted(c.get('labels', [])[:2], key=lambda L: L['i'] != imax):   # 최고점 먼저, 가까운 두 번째 글자는 겹치므로 뺌
        if all(abs(X(L['i']) - X(k['i'])) >= 30 for k in kept): kept.append(L)
    for L in kept:
        i = L['i']; right = X(i) > w * .7; anchor, dx = ('end', -1.6) if right else ('start', 1.6)
        val = f'<tspan class="b">{esc(fmt(y[i], c.get("unit", "")))}</tspan> ' if i == imax else ''
        lbl += f'<circle cx="{X(i):.2f}" cy="{Y(y[i]):.2f}" r=".9" class="pk"/><text x="{X(i) + dx:.2f}" y="{Y(y[i]) - (1.6 if i == imax else 2.6):.2f}" class="lb{"" if i == imax else " s"}" text-anchor="{anchor}">{val}{esc(L["text"])}</text>'
    return f'<svg class="cl" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(c.get("unit", ""))} 추이"><line x1="{X(0):.2f}" y1="{base}" x2="{X(n - 1):.2f}" y2="{base}" class="ax"/>{marks}{ticks}<polygon points="{area}" class="ar"/><polyline points="{pts}" class="ln"/>{lbl}</svg>'
def waffle(c):
    parts = c['parts'][:3]; cells = []
    for k, (l, v, *_) in enumerate(parts): cells += [f'p{k}'] * (max(1, round(v)) if v > 0 else 0)
    dots = ''.join(f'<i class="{c_}"></i>' for c_ in (cells + [''] * 100)[:100])
    lg = '<br>'.join(f'<i class="p{k}"></i>{esc(l)} {v:g}%' for k, (l, v, *_) in enumerate(parts))
    return f'<div class="wafw"><div class="waf" role="img" aria-label="100명 중 {esc(", ".join(f"{l} {v:g}%" for l, v, *_ in parts))}">{dots}</div><p class="lg">{lg}</p></div>'
def dumb(c):
    gs = c['groups']; u = c.get('unit', '%'); allv = [v for g in gs for pair in g[1:] for v in pair]
    top = 100 if u == '%' and max(allv) <= 100 else max(allv) * 1.1; P = lambda v: v / top * 100
    out = f'<div class="dumb"><div class="dh"><span></span><span>0</span><span class="m">{top / 2:g}</span><span class="e">{top:g}{esc(u)}</span></div>'
    for name, *pairs in gs:
        segs = vals = ''
        for k, (a, b) in enumerate(pairs[:2]):
            cl = 'a' if k == 0 else 'c'; lo, hi = min(a, b), max(a, b); d = b - a
            segs += f'<b class="ln {cl}" style="left:{P(lo):.1f}%;width:{P(hi) - P(lo):.1f}%"></b><i class="o {cl}" style="left:{P(a):.1f}%"></i><i class="f {cl}" style="left:{P(b):.1f}%"></i>'
            vals += f'<em class="{cl}">{"+" if d >= 0 else ""}{d:.1f}</em> '
        out += f'<div class="dr"><span class="dl">{esc(name)}</span><span class="dtk">{segs}</span><span class="dv">{vals.strip()}</span></div>'
    key = ''.join(f'<span class="{"a" if k == 0 else "c"}">{esc(m)}</span>' for k, m in enumerate(c.get('metrics', [])[:2]))
    return out + f'<div class="dk">{key}<span class="x">○ {esc(c.get("before", "전"))} → ● {esc(c.get("after", "후"))} · {"%p" if u == "%" else esc(u)}</span></div></div>'
def stack(c):
    ps = c['parts'][:5]; tot = sum(v for _, v in ps) or 1; col = ['key', 'bar', 'bar2', 'ink2', 'hair']
    seg = ''.join(f'<i class="p{k}" style="width:{v / tot * 100:.2f}%"></i>' for k, (_, v) in enumerate(ps))
    lab = ''.join(f'<span><i style="background:var(--{col[k]})"></i>{esc(l)} <b>{v:g}{esc(c.get("unit", "%"))}</b></span>' for k, (l, v) in enumerate(ps))
    return f'<div class="stack" role="img" aria-label="구성">{seg}</div><div class="stl">{lab}</div>'
def chart(c, avail):
    t = (c or {}).get('type', 'none')
    if t == 'multi':
        cs = c['charts'][:2]
        if len(cs) == 1: return chart(cs[0], avail)
        return f'<div class="multi" style="--k:{len(cs)}">' + ''.join(f'<div><p class="ct">{esc(x.get("title", ""))}</p>{chart(x, (avail - 7) / 2)}</div>' for x in cs) + '</div>'
    return {'line': line, 'waffle': waffle, 'dumbbell': dumb, 'stack': stack}.get(t, lambda c: '')(c) if t != 'bars' else bars(c, avail)

# ── 그림: 종이색을 흰색으로 맞춰 곱하기 합성 ──
def img64(path, maxpx=800):
    if not path or not os.path.exists(path): return None
    im = Image.open(path).convert('RGB'); im.thumbnail((maxpx, maxpx)); w, h = im.size
    px = [im.getpixel(p) for p in [(4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5), (w // 2, 4), (4, h // 2)]]
    paper = [sorted(c[i] for c in px)[len(px) // 2] for i in range(3)]
    im = Image.merge('RGB', [ch.point(lambda v, P=P: min(255, int(v * 255 / max(P, 1)))) for ch, P in zip(im.split(), paper)])
    b = io.BytesIO(); im.save(b, 'JPEG', quality=82, optimize=True); return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def hero(it):
    h = it.get('hero') or ({'kind': 'num', 'value': it['num'], 'unit': it.get('unit', ''), 'unit_pre': it.get('unit_pre')} if it.get('num') else None)
    if not h: return ''
    if h['kind'] == 'keyword': return f'<div class="kw">{esc(h["text"])}</div>'
    n, u = str(h['value']), h.get('unit', ''); sg = ''
    if n.startswith('+'): sg, n = '<span class="sg">+</span>', n[1:]
    if h.get('unit_pre'): return f'<div class="num"><span class="u pre">{esc(u)}</span>{esc(n)}</div>'
    return f'<div class="num">{sg}{esc(n)}{f"<span class=u>{esc(u)}</span>" if u else ""}</div>'

def block(it, i, kind, colw, illdir):
    c = it.get('chart') or {}; has_chart = c.get('type', 'none') != 'none'
    small = (it.get('illust') or {}).get('kind') in ('icon', 'symbol')
    src = img64(os.path.join(illdir, f"{it['id']}.png")) if illdir else None
    illw = (24 if small else 30) if kind == 'half' else (26 if small else 34)
    img = f'<img class="ill" src="{src}" alt="">' if src else ''
    title = '<br>'.join(esc(t) for t in it['title'].split('\n'))
    chips = ''.join(f'<li>{esc(x)}</li>' for x in (it.get('chips') or [])[:3])
    head = f'<div class="kk"><span class="kn">{esc(it["id"])}</span>{esc(it["kicker"])}</div>{hero(it)}<h2>{title}</h2>' + (f'<ul class="chips">{chips}</ul>' if chips else '')
    style = f'--illw:{illw}mm;--rot:{4 if i % 2 == 0 else -4}deg'
    if kind == 'half':
        return f'<section class="blk half" style="{style}">{img}<div class="lead">{head}</div>' + (f'<div class="viz">{chart(c, colw)}</div>' if has_chart else '') + '</section>'
    if not src: illw = 0; style = f'--illw:0mm;--rot:0deg'
    avail = BODY_W - LEAD_W - 6 - (illw + 6 if src else 0)
    return f'<section class="blk full{"" if has_chart else " nochart"}" style="{style}"><div class="lead">{head}</div>' + (f'<div class="viz">{chart(c, avail)}</div>' if has_chart else '') + img + '</section>'

def layout(items):   # 명세 순서대로: 띠가 필요한 항목은 혼자, 나머지는 두 개씩 한 줄(남는 하나는 띠)
    rows, i = [], 0
    while i < len(items):
        if not is_full(items[i]) and i + 1 < len(items) and not is_full(items[i + 1]): rows.append([i, i + 1]); i += 2
        else: rows.append([i]); i += 1
    return rows

FONTSETS = json.load(open(os.path.join(HERE, '..', 'assets', 'fonts.json'), encoding='utf-8'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
SOURCES = ['https://raw.githubusercontent.com/google/fonts/main/', 'https://cdn.jsdelivr.net/gh/google/fonts@main/']   # 구글 폰트 원본(OFL) — 앞이 막히면 다음

FONTDIR = os.path.join(HERE, '..', 'assets', 'fonts')   # 리포에 동봉한 OFL 원본 · 미리 자른 파일

def fonts_css(page_text, fs):
    """쓰인 글자만 잘라 base64 로 내장한 @font-face. 순서: 1) 리포 동봉 원본을 fontTools 로 자름 → 2) fontTools 가 없으면 동봉한
    「한글 2,350자」 파일을 그대로 → 3) 원본이 없으면 Google Fonts API → 4) 구글 폰트 원본 내려받아 자름. 인터넷 · pip 없이도 1·2 로 끝남."""
    chars = ''.join(sorted(set(page_text + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%$+-.,·()/:○●~→') - set('\n\r\t')))
    os.makedirs(CACHE, exist_ok=True); key = hashlib.sha1((chars + json.dumps(fs, sort_keys=True)).encode()).hexdigest()[:16]; cf = f'{CACHE}/{key}.css'
    if os.path.exists(cf): return open(cf).read()
    css = local_fonts(chars, fs)
    if not css and os.environ.get('DATABITE_FONT_API') != 'off':   # off = API 막힌 환경 시험
        q = f"https://fonts.googleapis.com/css2?family={fs['num']['google']}&family={fs['sans']['google']}&display=block&text=" + urllib.parse.quote(chars)
        css = subprocess.run(['curl', '-sf', '-m', '20', '-A', UA, q], capture_output=True, text=True).stdout
        if css and 'fonts.gstatic.com' in css:
            def embed(m):
                fn = f'{CACHE}/{hashlib.sha1(m.group(1).encode()).hexdigest()[:16]}.woff2'
                if not os.path.exists(fn): subprocess.run(['curl', '-sf', '-m', '30', '-A', UA, '-o', fn, m.group(1)])
                return 'url(data:font/woff2;base64,' + base64.b64encode(open(fn, 'rb').read()).decode() + ')'
            css = re.sub(r'\s*unicode-range:[^;]+;', '', re.sub(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', embed, css))
        else: css = ''
    if not css: css = local_fonts(chars, fs, download=True)
    if css: open(cf, 'w').write(css)
    else: sys.stderr.write('[글꼴] 글꼴을 내장하지 못함 — 시스템 글꼴로 그림\n')
    return css

def local_fonts(chars, fs, download=False):
    try:
        from fontTools import subset as ftsub
        from fontTools.ttLib import TTFont
    except ImportError: ftsub = None
    try: import brotli; flavor, mime = 'woff2', 'font/woff2'   # noqa: F401
    except ImportError: flavor, mime = None, 'font/ttf'
    out = []
    for role in ('num', 'sans'):
        f = fs[role]; name = f.get('embed', f['family'])   # OFL 예약 이름이 있으면 잘라 낸 글꼴은 다른 이름(fonts.json embed)
        for wt, path in f['files'].items():
            src = os.path.join(FONTDIR, path)
            if not os.path.exists(src) and download:
                src = f"{CACHE}/src-{os.path.basename(path).replace('[', '_').replace(']', '_')}"
                for base in ([] if os.path.exists(src) else SOURCES):
                    if subprocess.run(['curl', '-sfL', '-m', '120', '-A', UA, '-o', src, base + urllib.parse.quote(path)]).returncode == 0 and os.path.getsize(src) > 10000: break
                    if os.path.exists(src): os.remove(src)
            if ftsub and os.path.exists(src):
                font = TTFont(src); opt = ftsub.Options(); opt.flavor = flavor; opt.layout_features = ['*']
                sub = ftsub.Subsetter(opt); sub.populate(text=chars); sub.subset(font)
                b = io.BytesIO(); font.flavor = flavor; font.save(b); data, m = b.getvalue(), mime
            elif os.path.exists(os.path.join(FONTDIR, f['ksx'][wt])):   # fontTools 없음 → 미리 자른 2,350자 파일
                data, m = open(os.path.join(FONTDIR, f['ksx'][wt]), 'rb').read(), 'font/woff2'
            else: return ''
            out.append(f"@font-face {{ font-family: '{name}'; font-weight: {wt}; font-display: block; src: url(data:{m};base64,{base64.b64encode(data).decode()}); }}")
    return '\n'.join(out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('out')
    ap.add_argument('--illust', help='그림 폴더(항목 id.png). 기본: 명세 옆 illust/W{week}/')
    ap.add_argument('--logo'); ap.add_argument('--kicker', default='WEEKLY'); ap.add_argument('--footer', default='Proprietary and Confidential')
    ap.add_argument('--fonts', default='anton-noto', choices=list(FONTSETS), help='글꼴 조합(assets/fonts.json) — 사용자가 고른 것으로 고정')
    a = ap.parse_args(); S = json.load(open(a.spec, encoding='utf-8')); items = S['items']
    global FS; FS = FONTSETS[a.fonts]
    illdir = a.illust or os.path.join(os.path.dirname(os.path.abspath(a.spec)), 'illust', f"W{S['week']}")
    rows_html = ''
    for r in layout(items):
        if len(r) == 1: rows_html += f'<div class="row" style="grid-template-columns:1fr">{block(items[r[0]], r[0], "full", BODY_W, illdir)}</div>'; continue
        na, nb = (max(LEAD_W, chart_need(items[k].get('chart') or {})) for k in r)
        fa = min(.58, max(.42, na / (na + nb))); wa = (BODY_W - GAP) * fa; wb = BODY_W - GAP - wa
        rows_html += f'<div class="row" style="grid-template-columns:{fa:.3f}fr {1 - fa:.3f}fr">{block(items[r[0]], r[0], "half", wa, illdir)}{block(items[r[1]], r[1], "half", wb, illdir)}</div>'
    logo = f'<img class="logo" src="data:image/png;base64,{base64.b64encode(open(a.logo, "rb").read()).decode()}" alt="">' if a.logo and os.path.exists(a.logo) else '<span></span>'
    week, period = esc(S['week']), esc(S.get('period', '').replace('–', '~'))
    page = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data Bite {week}주차</title><style>/*FONTS*/
{open(os.path.join(HERE, '..', 'assets', 'style.css'), encoding='utf-8').read()}
:root {{ --numf: "{FS['num'].get('embed', FS['num']['family'])}", "{FS['num']['family']}", sans-serif; --sans: "{FS['sans'].get('embed', FS['sans']['family'])}", "{FS['sans']['family']}", system-ui, sans-serif; --numw: {FS['num']['weight']}; }}</style></head><body>
<article class="sheet" aria-label="Data Bite {week}주차 인포그래픽">
<header class="mast"><div class="m1"><span class="kicker">{esc(a.kicker)}</span><span class="wdb">Data Bite</span></div><div class="m2"><span class="wk">{week}<small>주차</small></span>{logo}<span class="mdate">{period}</span></div></header>
<div class="body">{rows_html}</div>
<footer class="foot">{esc(a.footer)}</footer>
</article>
<script>(() => {{ const s = document.querySelector('.sheet'), st = document.createElement('style'); document.head.appendChild(st);
const fit = () => {{ s.style.zoom = ''; st.textContent = '@page {{ size: 210mm ' + Math.ceil(s.offsetHeight * 25.4 / 96) + 'mm; margin: 0; }}';
s.style.zoom = Math.min(1.75, (document.documentElement.clientWidth - 24) / s.offsetWidth); }};
addEventListener('resize', fit); document.fonts.ready.then(fit); fit(); }})();</script>
</body></html>'''
    text = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', page, flags=re.S))
    page = page.replace('/*FONTS*/', fonts_css(re.sub(r'data:[^"\s]+', '', html.unescape(text)), FS))
    open(a.out, 'w', encoding='utf-8').write(page)
    print(json.dumps({'out': a.out, 'rows': layout(items), 'kb': len(page) // 1024}, ensure_ascii=False))

if __name__ == '__main__': main()
