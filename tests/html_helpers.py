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
    assert p.scripts==[{'id':'fathom-navigation'},{'id':'fathom-transpose'}]
    assert 'src="http' not in page and 'href="http' not in page


def assert_finding_preserved(finding,page):
    """Check source-order facts in the actual finding, allowing nested presentation."""
    import re
    class Article(HTMLParser):
        def __init__(self):super().__init__();self.active=False;self.parts=[]
        def handle_starttag(self,tag,attrs):
            if tag=='article' and dict(attrs).get('id')==finding['id']:self.active=True
            if self.active and tag in {'div','p','ul','li','details','summary'}:self.parts.append(' ')
        def handle_endtag(self,tag):
            if tag=='article':self.active=False
            if self.active and tag in {'li','p','div','dd','dt','ul','summary'}:self.parts.append(' ')
        def handle_data(self,text):
            if self.active:self.parts.append(text)
    a=Article();a.feed(page);actual=''.join(a.parts);assert actual,finding['id']
    if finding.get('rule')=='target_group_contrast' and finding['kind']=='observation':
        from fathom.presentation import formatted
        group=finding['evidence'][0]['value'];assert 'group:' in actual and 'rest:' in actual
        for contrast in group['contrasts']:
            share=contrast['measure'].startswith('rate:') or contrast['measure']=='missing share'
            assert formatted(contrast['group'],share) in actual and formatted(contrast['rest'],share) in actual
        assert 'marked' in actual
    else:
        tokens=lambda s:[t.casefold() for t in re.findall(r'\w+(?:[.−-]\w+)*|[≥<>=%]',s) if t.casefold()!='and']
        available=iter(tokens(actual))
        for token in tokens(finding['message']):assert any(t==token for t in available),(finding['id'],token,actual[:300])
