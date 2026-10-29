#!/usr/bin/env python3
"""글꼴 조합 비교 — 같은 명세를 assets/fonts.json 의 조합마다 그려 한 페이지에 나란히 놓는다(사용자 확인용).

사용: python3 variants.py spec.json OUT_DIR [render.py 옵션 …]
결과: OUT_DIR/fonts-<조합>.html 과 OUT_DIR/fonts-compare.html. 사용자가 고른 조합을 이후 render.py --fonts 로 고정한다.
"""
import html, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec, out, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
sets = json.load(open(os.path.join(HERE, '..', 'assets', 'fonts.json'), encoding='utf-8'))
cols = ''
for k, v in sets.items():
    f = f'fonts-{k}.html'
    subprocess.run([sys.executable, os.path.join(HERE, 'render.py'), spec, os.path.join(out, f), '--fonts', k, *extra], check=True, stdout=subprocess.DEVNULL)
    cols += f'<figure><figcaption><b>{html.escape(v["label"])}</b><span>render.py --fonts {k}</span></figcaption><div class="frame"><iframe src="{f}" title="{html.escape(v["label"])}" loading="lazy"></iframe></div><a href="{f}" target="_blank" rel="noopener">크게 보기</a></figure>'
page = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>글꼴 비교</title>
<style>
:root {{ --bg: #ECE6DA; --ink: #1C1B1A; --muted: #57534C; --key: #C8401C; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font: 400 15px/1.5 system-ui, sans-serif; }}
main {{ max-width: 1400px; margin: 0 auto; padding: 24px 16px 48px; }}
h1 {{ margin: 0 0 4px; font-size: 22px; }} p {{ margin: 0 0 24px; color: var(--muted); }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; }}
figure {{ margin: 0; display: grid; gap: 8px; }}
figcaption {{ display: grid; gap: 2px; }} figcaption span {{ font: 13px/1.4 ui-monospace, monospace; color: var(--muted); }}
.frame {{ position: relative; width: 100%; aspect-ratio: 210 / 297; overflow: hidden; border-radius: 8px; background: #fff; box-shadow: 0 2px 12px rgba(0,0,0,.12); }}
.frame iframe {{ position: absolute; top: 0; left: 0; width: 820px; height: 1290px; border: 0; transform-origin: 0 0; }}
a {{ color: var(--key); font-weight: 600; }}
</style></head><body><main><h1>글꼴 비교</h1><p>글자 크기 · 색 · 배치는 같고 글꼴 조합만 다름. 하나를 고르면 그 조합으로 고정함.</p><div class="grid">{cols}</div></main>
<script>const fit = () => document.querySelectorAll('.frame').forEach(f => {{ const i = f.querySelector('iframe'), k = f.clientWidth / 820; i.style.transform = `scale(${{k}})`; try {{ const h = i.contentDocument.querySelector('.sheet').getBoundingClientRect().bottom + 16; i.style.height = h + 'px'; f.style.aspectRatio = 'auto'; f.style.height = h * k + 'px'; }} catch (e) {{}} }}); addEventListener('resize', fit); document.querySelectorAll('iframe').forEach(i => i.addEventListener('load', fit)); fit();</script>
</body></html>'''
open(os.path.join(out, 'fonts-compare.html'), 'w', encoding='utf-8').write(page)
print(json.dumps({'compare': os.path.join(out, 'fonts-compare.html'), 'sets': list(sets)}, ensure_ascii=False))
