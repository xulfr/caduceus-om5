#!/usr/bin/env python3
"""Render checked-in guides: pip install -r requirements-dev.txt; python tools/mksite.py."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
import markdown

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    'docs/INSTALL.md': 'install', 'docs/USING.md': 'using', 'docs/FAQ.md': 'faq',
    'docs/SAFETY.md': 'safety', 'docs/FIRST_FLASH.md': 'first-flash',
    'docs/FORMATS.md': 'formats', 'docs/WHITE_BALANCE.md': 'white-balance', 'docs/OM5_PREALPHA.md': 'om5-prealpha',
    'ROADMAP.md': 'roadmap', 'CHANGELOG.md': 'changelog',
}
REPO = 'https://github.com/xulfr/caduceus-om5'
BANNER = ('<div class="banner"><strong>Experimental firmware.</strong> Alpha9 has not been run on a camera; alpha8 booted on one OM-5 Mark II. Earlier builds caused boot loops. '
          '<a href="../safety/">Read the safety notes.</a></div>')
BANNERS = {'om5-prealpha': '<div class="banner"><strong>Pre-alpha for the original OM-5: never run on any camera.</strong> '
           'Recovery from a failure is unknown. For testers who accept that risk. '
           '<a href="../safety/">Read the safety notes.</a></div>'}


def link(target, source):
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not parts.path:
        return target
    rel = (source.parent / parts.path).resolve().relative_to(ROOT).as_posix()
    path = '../' + PAGES[rel] + '/' if rel in PAGES else REPO + '/blob/main/' + rel
    return urlunsplit(('', '', path, parts.query, parts.fragment))


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;600;700'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')
CALLOUTS = {'NOTE': ('note', 'Note'), 'TIP': ('tip', 'Tip'), 'WARNING': ('warning', 'Warning'),
            'IMPORTANT': ('warning', 'Important'), 'CAUTION': ('warning', 'Caution')}


def callout(m):
    kind = re.match(r'<blockquote>\s*<p>\s*\[!(\w+)\]\s*', m[0])
    if not kind or kind[1].upper() not in CALLOUTS:
        return m[0]
    cls, label = CALLOUTS[kind[1].upper()]
    return f'<blockquote class="callout {cls}">\n<p class="ct">{label}</p>\n<p>' + m[0][kind.end():].removeprefix('<blockquote>')


def layout(body):
    """Title and intro, a table of contents, then one card per h2 section (as Caduceus for OM-3's guide pages)."""
    body = re.sub(r'<blockquote>.*?</blockquote>', callout, body, flags=re.S)
    body = re.sub(r'(<table>.*?</table>)', r'<div class="tablewrap">\1</div>', body, flags=re.S)
    parts = re.split(r'(?=<h2[ >])', body)
    lead, sections = parts[0], parts[1:]
    out = [f'<div class="lead">\n{lead.strip()}\n</div>']
    heads = [re.match(r'<h2(?: id="([^"]*)")?>(.*?)</h2>', sec, re.S) for sec in sections]
    if len(sections) > 2:
        links = ''.join(f'<a href="#{h[1]}">{re.sub(r"<[^>]+>", "", h[2])}</a>' for h in heads if h and h[1])
        out.append(f'<nav class="toc" aria-label="On this page">{links}</nav>')
    out += [f'<section class="card">\n{sec.strip()}\n</section>' for sec in sections]
    return '\n'.join(out)


def render(source, slug):
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    text = source.read_text(encoding='utf-8')
    body = md.convert(text)
    body = re.sub(r'href="([^"]+)"', lambda m: 'href="' + escape(link(m[1], source), quote=True) + '"', body)
    title = re.search(r'^# (.+)$', text, re.M)[1]
    nav = [('Tour', '../../'), ('Install', '../install/'), ('Using it', '../using/'), ('LookLab', '../../looklab/'),
           ('FAQ', '../faq/'), ('Safety', '../safety/'), ('Roadmap', '../roadmap/'), ('Changelog', '../changelog/'),
           ('GitHub ↗', REPO)]
    links = ''.join(f'\n  <a class="tab" href="{url}"' + (' aria-current="page"' if url == f'../{slug}/' else '')
                    + f'>{label}</a>' for label, url in nav)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · Caduceus for OM-5</title>
{FONTS}
<link rel="stylesheet" href="../site/doc.css"></head><body>
<a class="skip" href="#content">Skip to content</a>
<nav class="topnav" aria-label="Main"><div class="in">
  <a class="brand" href="../../">Caduceus for OM-5</a>{links}
</div></nav>
{BANNERS.get(slug, BANNER)}
<main class="wrap" id="content">
{layout(body)}
<footer>By xulfr and the Caduceus contributors · Apache-2.0 · <a href="{REPO}/blob/main/{source.relative_to(ROOT).as_posix()}">Page source</a> · Built on <a href="https://github.com/fishcu/oly_fw_analysis">fishcu’s firmware research</a>, <a href="https://github.com/cakelesscoder/caduceus-ep7">Caduceus for E-P7</a> by cakelesscoder and <a href="https://github.com/androidfanman/caduceus-om3">Caduceus for OM-3</a> by androidfanman · <a href="../../#credits">Credits</a></footer>
</main>
</body></html>
'''


def main():
    for name, slug in PAGES.items():
        source = ROOT / name
        if not source.exists():
            print(f'Pending source: {name}')
            continue
        out = ROOT / 'pages' / slug / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(source, slug), encoding='utf-8', newline='\n')
        print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
