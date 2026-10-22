"""Render approximate EU5-style previews of generated events for design review.

These are mockups for reading text and layout, not engine screenshots:
fonts, frames and sizes only approximate the native event window.
Usage: python tools/preview_events.py --out DIR ga_gathering.36 ga_gathering.37 ...
"""
import argparse
import base64
import html
import io
import json
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageOps
from verify_055 import parse

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mod'
NAMES = {c['tag']: c['name'] for c in json.loads((ROOT / 'data/island.json').read_text(encoding='utf-8-sig'))['countries']}
# Sample cast for saved scopes: Cindermaw asks, Brackmaw answers.
SAMPLE = {'ga_sp_requester': 'CDM', 'ga_sp_provider': 'QBR', 'ga_sp_broken_partner': 'QBR',
          'ga_cp_requester': 'CDM', 'ga_cp_provider': 'QBR', 'ga_hb_requester': 'CDM', 'ga_hb_provider': 'QBR'}
COLORS = {'Y': '#f3c75a', 'G': '#7fd46a', 'R': '#e8664f'}


def localization():
    text = {}
    for path in (MOD / 'main_menu/localization/english').glob('*.yml'):
        for key, value in re.findall(r'^ ([\w.]+): "(.*)"$', path.read_text(encoding='utf-8-sig'), re.M):
            text[key] = value.replace('\\"', '"')
    return text


def rich(value):
    value = re.sub(r"\[SCOPE\.sCountry\('(\w+)'\)\.GetName\]", lambda m: NAMES[SAMPLE.get(m.group(1), 'CDM')], value)
    value = html.escape(value).replace('\\n', '\n')
    def fmt(m):
        tag, body = m.group(1), m.group(2)
        if tag == 'bold': return f'<b>{body}</b>'
        return f'<span style="color:{COLORS.get(tag, "#fff")}">{body}</span>'
    value = re.sub(r'#(\w+) (.*?)#!', fmt, value, flags=re.S)
    return value.replace('\n', '<br>')


def painting(event_image):
    name = Path(event_image).stem
    with Image.open(ROOT / 'art/events/sources' / (name + '.png')) as source:
        img = ImageOps.fit(source.convert('RGB'), (1080, 440), method=Image.Resampling.LANCZOS)
    buffer = io.BytesIO(); img.save(buffer, 'JPEG', quality=88)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()


def page(event_id, body, text):
    fields = {k: v for k, _, v in body if k != 'option'}
    options = []
    for row in [v for k, _, v in body if k == 'option']:
        option = {k: v for k, _, v in row}
        tip = option.get('custom_tooltip') if isinstance(option.get('custom_tooltip'), str) else None
        options.append((text[option['name']], text.get(tip) if tip else None))
    buttons = ''.join(
        f'<div class="option"><div class="label">{rich(name)}</div>'
        + (f'<div class="tip">{rich(tip)}</div>' if tip else '') + '</div>' for name, tip in options)
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
body {{ margin:0; background:#1a1612; font-family:"Liberation Serif","DejaVu Serif",serif; }}
.window {{ width:560px; margin:20px; background:linear-gradient(#3b3227,#2a231b); border:3px solid #8a7146;
  box-shadow:0 0 0 2px #1c1711, 0 12px 30px rgba(0,0,0,.6); color:#e9dfc8; }}
.title {{ text-align:center; font-size:24px; letter-spacing:.5px; padding:12px 16px 10px; color:#f1e2bb;
  background:linear-gradient(#5a4a33,#3d3223); border-bottom:2px solid #8a7146; text-shadow:0 2px 2px #000; }}
.art {{ display:block; width:100%; border-bottom:2px solid #8a7146; }}
.desc {{ padding:14px 22px 6px; font-size:16px; line-height:1.42; }}
.options {{ padding:8px 22px 20px; }}
.option {{ margin-top:8px; }}
.label {{ background:linear-gradient(#6b5a3d,#4d3f2a); border:1px solid #a88c5a; border-radius:3px; padding:9px 12px;
  font-size:16px; color:#fff3d6; text-align:center; }}
.tip {{ margin:4px 10px 0; padding:8px 10px; background:#14110d; border:1px solid #5c4b31; font-size:13.5px; line-height:1.35; color:#d9ceb6; }}
.tag {{ text-align:right; font-size:11px; color:#8a7a60; padding:0 10px 6px; font-family:monospace; }}
</style></head><body><div class="window">
<div class="title">{rich(text[fields['title']])}</div>
<img class="art" src="{painting(fields['image'])}">
<div class="desc">{rich(text[fields['desc']])}</div>
<div class="options">{buttons}</div>
<div class="tag">{event_id} · preview mockup, option tooltips shown below each button</div>
</div></body></html>'''


SHOOT = r'''
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  for (const [src, dst] of JSON.parse(process.argv[1])) {
    await page.goto('file://' + src);
    await (await page.$('.window')).screenshot({ path: dst });
  }
  await browser.close();
})();
'''


def render(out, ids):
    out.mkdir(parents=True, exist_ok=True)
    text = localization()
    events = {k: v for k, _, v in parse((MOD / 'in_game/events/goblins_gathering.txt').read_text(encoding='utf-8-sig')) if k != 'namespace'}
    jobs = []
    for event_id in ids:
        source = out / (event_id + '.html')
        source.write_text(page(event_id, events[event_id], text), encoding='utf-8')
        jobs.append([str(source), str(out / (event_id + '.png'))])
    subprocess.run(['node', '-e', SHOOT, json.dumps(jobs)], check=True)
    for source, _ in jobs: Path(source).unlink()
    return [dst for _, dst in jobs]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('ids', nargs='+')
    args = parser.parse_args()
    print('\n'.join(render(args.out, args.ids)))
