"""Duo carousel, 'realistic scene' style (AI photo + condensed caps, gold accent).
usage: python3 render_real.py <carousel.json> <scenes_dir> <fonts_dir> <out_dir>
carousel.json: {"id":..., "slides":[...as in Карусель-машина...],
                "scenes": {"0":"cover.jpg","2":"mid.jpg"},   # slide index -> scene file (full-bleed photo)
                "bg":"cover.jpg",                             # blurred background for text slides
                "crop": {"0":120}}                            # optional top offset (px at 1080 width)
"""
import sys, json, os, glob, base64, re, html as H
from playwright.sync_api import sync_playwright

spec_p, scenes_dir, fonts_dir, out_dir = sys.argv[1:5]
os.makedirs(out_dir, exist_ok=True)
spec = json.load(open(spec_p))
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
osw = glob.glob(os.path.join(fonts_dir, '**', 'Oswald*.ttf'), recursive=True)[0]
gol = glob.glob(os.path.join(fonts_dir, '**', 'GolosText*.ttf'), recursive=True)[0]
img = {}
def src(name):
    if name not in img:
        img[name] = 'data:image/jpeg;base64,' + b64(os.path.join(scenes_dir, name))
    return img[name]

def gold(t):
    t = H.escape(t or '')
    return re.sub(r'\*(.+?)\*', r'<b>\1</b>', t).replace('\n','<br>')

CSS = f"""
@font-face{{font-family:O;src:url(data:font/ttf;base64,{b64(osw)});font-weight:200 700}}
@font-face{{font-family:G;src:url(data:font/ttf;base64,{b64(gol)});font-weight:400 900}}
body{{margin:0}} *{{box-sizing:border-box}}
.s{{width:1080px;height:1350px;position:relative;overflow:hidden;background:#0d0b0a;color:#fff}}
.ph{{position:absolute;left:0;width:1080px}}
.bg{{position:absolute;inset:-60px;background-size:cover;background-position:center;filter:blur(30px) brightness(.32) saturate(.9)}}
.gt{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.92) 0%,rgba(0,0,0,.7) 34%,rgba(0,0,0,0) 54%,rgba(0,0,0,0) 76%,rgba(0,0,0,.65) 100%)}}
.c{{position:absolute;left:80px;right:80px;top:84px}}
.k{{font:600 30px/1.3 G;letter-spacing:.06em;text-transform:uppercase;border-left:6px solid #e9b872;padding-left:22px;color:#f1e6d6;margin-bottom:36px}}
h1{{font:700 var(--fs,112px)/1.02 O;text-transform:uppercase;margin:0;letter-spacing:-.005em}}
h1 b,.big b{{color:#e9b872;font-weight:700}}
.p{{font:400 46px/1.42 G;color:rgba(255,255,255,.9);margin-top:40px}}
ul{{list-style:none;padding:0;margin:44px 0 0}}
li{{font:500 44px/1.35 G;padding:22px 0 22px 64px;position:relative;border-top:1px solid rgba(255,255,255,.14)}}
li:before{{content:'';position:absolute;left:0;top:44px;width:36px;height:5px;background:#e9b872}}
.cmp{{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:48px}}
.col{{border-radius:22px;padding:34px 30px;background:rgba(255,255,255,.07)}}
.col h3{{font:700 46px O;text-transform:uppercase;margin:0 0 18px}}
.col.g h3{{color:#e9b872}} .col.r h3{{color:#ff8a7a}}
.col div{{font:500 38px/1.32 G;padding:12px 0;border-top:1px solid rgba(255,255,255,.12)}}
.cta{{margin-top:56px;display:inline-block;background:#e9b872;color:#16110b;font:700 58px/1 O;text-transform:uppercase;padding:30px 40px;border-radius:18px}}
.f{{position:absolute;left:80px;right:80px;bottom:56px;display:flex;justify-content:space-between;font:500 28px G;color:rgba(255,255,255,.8)}}
.c.mid{{top:0;bottom:130px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start}}
.bot{{position:absolute;left:80px;right:80px;bottom:130px}}
"""

def slide(s, i, n):
    sc = spec.get('scenes', {}).get(str(i))
    kicker = ''
    if s.get('num'):
        kicker = f"{int(s['num']):02d}"
    if i == 0:
        kicker = spec.get('kicker', 'Владелец экскурсий на Пхукете')
    if s['type'] == 'cta':
        kicker = 'Напишите мне'
    body = ''
    if s.get('items') and s['type'] == 'compare':
        good = [x[1:].strip() for x in s['items'] if x.startswith('+')]
        bad = [x[1:].strip() for x in s['items'] if x.startswith('-')]
        body = (f"<div class=cmp><div class='col g'><h3>{H.escape(s.get('goodLabel') or 'Норма')}</h3>"
                + ''.join(f'<div>{H.escape(x)}</div>' for x in good)
                + f"</div><div class='col r'><h3>{H.escape(s.get('badLabel') or 'Тревожно')}</h3>"
                + ''.join(f'<div>{H.escape(x)}</div>' for x in bad) + '</div></div>')
    elif s.get('items'):
        body = '<ul>' + ''.join(f'<li>{H.escape(x)}</li>' for x in s['items']) + '</ul>'
    if s.get('text') and i != 0:
        body = f"<div class=p>{H.escape(s['text'])}</div>" + body
    if s['type'] == 'cta':
        body += "<div class=cta>«ОСТРОВ» в директ</div>"
    fs = s.get('fs') or (124 if i == 0 else 108)
    title = s.get('realTitle') or s['title']
    head = f"<div class=k>{H.escape(kicker)}</div>" if kicker else ''
    if sc:
        top = spec.get('crop', {}).get(str(i), 120)
        back = f"<img class=ph style='top:-{top}px' src='{src(sc)}'><div class=gt></div>"
        txt = f"<div class=c>{head}<h1 style='--fs:{fs}px'>{gold(title)}</h1></div>"
        if body and i != 0:
            txt += f"<div class=bot style='background:rgba(0,0,0,.55);padding:30px 34px;border-radius:22px;left:56px;right:56px'>{body.replace('class=p','class=p style=margin:0')}</div>"
        elif i == 0 and s.get('text'):
            pass
    else:
        back = f"<div class=bg style=\"background-image:url('{src(spec['bg'])}')\"></div>"
        txt = f"<div class='c mid'>{head}<h1 style='--fs:{fs}px'>{gold(title)}</h1>{body}</div>"
    foot = f"<div class=f><span>@duo.phuket</span><span>{'листайте →' if i == 0 else f'{i+1}/{n}'}</span></div>"
    return f"<div class=s>{back}{txt}{foot}</div>"

files = []
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={'width': 1080, 'height': 1350})
    n = len(spec['slides'])
    for i, s in enumerate(spec['slides']):
        pg.set_content(f"<html><head><style>{CSS}</style></head><body>{slide(s, i, n)}</body></html>")
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
        # shrink title if content overflows
        pg.evaluate("""()=>{const s=document.querySelector('.s'),h=document.querySelector('h1');let f=parseFloat(getComputedStyle(h).fontSize);
          const c=document.querySelector('.c');const lim=document.querySelector('.bot')?document.querySelector('.bot').offsetTop-30:1350-130;
          while(((c.classList.contains('mid')&&c.scrollHeight>c.clientHeight+8)||c.offsetTop+c.offsetHeight>lim)&&f>56){f-=4;h.style.setProperty('--fs',f+'px');}}""")
        out = os.path.join(out_dir, f"{i+1:02d}.png")
        pg.screenshot(path=out); files.append(out)
    br.close()
print(json.dumps(files))
