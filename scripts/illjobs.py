#!/usr/bin/env python3
"""명세의 illust.subject → gpt-image 배치 작업 파일(모든 그림이 같은 스타일 문장을 공유). 이미 있는 그림은 건너뜀.

사용: python3 illjobs.py spec.json OUT_DIR > jobs.json
그다음: node <gpt-image 스킬>/scripts/gpt_image.mjs batch --manifest jobs.json --concurrency 4
"""
import json, os, sys

STYLE = ("Editorial magazine illustration, hand-drawn with a black felt-tip pen and fine liner outlines, then painted with thick oil paint brushstrokes showing visible impasto texture, "
         "on a plain warm cream paper background. Limited palette: deep ink black, warm vermilion orange, cobalt blue, muted greys. Subject: {s}. "
         "Loose confident linework with a slight wobble, generous empty paper around the subject, not photorealistic. No readable text, no logos, no brand marks.")
spec, out = json.load(open(sys.argv[1], encoding='utf-8')), sys.argv[2]; os.makedirs(out, exist_ok=True)
jobs = [{'id': it['id'], 'out': os.path.join(out, f"{it['id']}.png"), 'prompt': STYLE.format(s=it['illust']['subject'].rstrip('.'))}
        for it in spec['items'] if it.get('illust', {}).get('subject') and not os.path.exists(os.path.join(out, f"{it['id']}.png"))]
print(json.dumps({'jobs': jobs}, ensure_ascii=False, indent=1))
