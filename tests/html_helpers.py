"""Assertions about reader-visible text, independent of inline typography tags."""
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.scripts=[];self.raw=None
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style'}:self.raw=tag
        if tag=='script':self.scripts.append(dict(attrs))
    def handle_endtag(self,tag):
        if self.raw==tag:self.raw=None
    def handle_data(self,text):
        if not self.raw:self.parts.append(text)

def visible_text(page):
    p=Text();p.feed(page);return ''.join(p.parts)

def assert_navigation_only_script(page):
    p=Text();p.feed(page)
    assert p.scripts==[{'id':'fathom-navigation'}]
    assert 'src="http' not in page and 'href="http' not in page
