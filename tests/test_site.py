from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mksite


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.ids = [], set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


class SiteTests(unittest.TestCase):
    def test_generated_guides_are_current(self):
        for source, slug in mksite.PAGES.items():
            self.assertEqual((ROOT / 'pages' / slug / 'index.html').read_text(encoding='utf-8'),
                             mksite.render(ROOT / source, slug), source)

    def test_local_links_and_anchors(self):
        files = [ROOT / 'index.html', ROOT / 'looklab/index.html', *list((ROOT / 'pages').glob('*/index.html'))]
        for file in files:
            text = file.read_text(encoding='utf-8')
            self.assertIn('class="banner"', text)
            for target in Links(text).links:
                parts = urlsplit(target)
                if parts.scheme or parts.netloc:
                    continue
                dest = (file.parent / unquote(parts.path)).resolve() if parts.path else file
                if dest.is_dir():
                    dest /= 'index.html'
                self.assertTrue(dest.is_file(), f'{file}: {target}')
                if parts.fragment and dest.suffix == '.html':
                    self.assertIn(parts.fragment, Links(dest.read_text(encoding='utf-8')).ids, target)


if __name__ == '__main__':
    unittest.main()
