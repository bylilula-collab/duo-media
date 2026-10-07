"""Render Duo carousel slides to PNG exactly like the Карусель-машина page.
usage: python3 render_carousel.py <page.html> <data_dir> <fonts_dir> <out_dir> <id> [<id> ...]
data_dir contains results/<id>.json, photos/*.json, settings/profile.json (+ optional settings/main.json)
"""
import sys, json, glob, os, base64
from playwright.sync_api import sync_playwright

page_html, data_dir, fonts_dir, out_dir, *ids = sys.argv[1:]
os.makedirs(out_dir, exist_ok=True)

def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode()

FACES = [('Caveat', 'Caveat*.ttf', '400 700'), ('Golos Text', 'GolosText*.ttf', '400 900'),
         ('Unbounded', 'Unbounded*.ttf', '200 900'), ('Manrope', 'Manrope*.ttf', '200 800')]
font_css = ''
for fam, pat, w in FACES:
    hit = glob.glob(os.path.join(fonts_dir, '**', pat), recursive=True)
    if hit:
        font_css += "@font-face{font-family:'%s';font-weight:%s;src:url(data:font/ttf;base64,%s) format('truetype')}" % (fam, w, b64(hit[0]))

photos = [json.load(open(f)) for f in glob.glob(os.path.join(data_dir, 'photos', '*.json'))]
photos = [{'id': os.path.basename(f)[:-5], **json.load(open(f))} for f in glob.glob(os.path.join(data_dir, 'photos', '*.json'))]
photos.sort(key=lambda p: p.get('createdAt', 0))
prof_path = os.path.join(data_dir, 'settings', 'profile.json')
profile = json.load(open(prof_path)).get('data') if os.path.exists(prof_path) else None
main_path = os.path.join(data_dir, 'settings', 'main.json')
settings = json.load(open(main_path)) if os.path.exists(main_path) else {'handle': '', 'handles': []}

html = open(page_html, encoding='utf8').read()
report = {}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={'width': 1200, 'height': 1400}, device_scale_factor=1)
    pg.route('**/*', lambda r: r.fulfill(status=200, content_type='text/css', body='') if 'fonts.googleapis' in r.request.url
             else (r.abort() if r.request.url.startswith('http') else r.continue_()))
    pg.set_content(html, wait_until='domcontentloaded')
    pg.add_style_tag(content=font_css + "#render{left:0!important;top:0!important;z-index:9999}")
    pg.evaluate("""([ph,prof,st])=>{photos=ph;profileShot=prof;settings={handle:'',handles:[],...st};}""", [photos, profile, settings])
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(400)
    for cid in ids:
        r = json.load(open(os.path.join(data_dir, 'results', cid + '.json')))
        r['id'] = cid
        n = len(r['slides'])
        files = []
        for i in range(n):
            pg.evaluate("""([r,i,n])=>{const h=document.querySelector('#render');h.innerHTML=slideHTML(r.slides[i],i,n,photoFor(r,i),handleFor(r));fitSlide(h.firstElementChild);}""", [r, i, n])
            pg.wait_for_timeout(150)
            el = pg.query_selector('#render > .slide')
            out = os.path.join(out_dir, f'{cid}_{i+1:02d}.png')
            el.screenshot(path=out)
            files.append(out)
        report[cid] = {'files': files, 'caption': r.get('caption', ''), 'title': r['slides'][0]['title']}
    b.close()
print(json.dumps(report, ensure_ascii=False))
