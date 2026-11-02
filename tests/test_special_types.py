import csv
import io
import socket

import pytest

from fathom.renderers import render_html


def text(names,rows):
    out=io.StringIO();w=csv.writer(out);w.writerow(names);w.writerows(rows);return out.getvalue()


@pytest.mark.parametrize('name,typ,bad,good',[
    ('phone','phone','000-000-0000','+1 (202) 555-0101'),
    ('phone','phone','call-me','+1 (202) 555-0101'),
    ('email','email','test@test.com','alpha@example.org'),
    ('website','url','https:///broken','https://example.org/path'),
    ('latitude','latitude','91','45'),('longitude','longitude','-181','-75'),
])
def test_special_violation_clean_and_inference(make_profile,name,typ,bad,good):
    dirty=make_profile(text([name],[[bad],[good],[good]])).document
    clean=make_profile(text([name],[[good],[good],[good]])).document
    col=dirty['columns'][0];assert col['effective_type']==typ
    assert col['inference']['confidence'] and col['inference']['alternatives']
    assert any(f.get('generator')=='rule:special-v1' for f in dirty['findings'])
    assert not any(f.get('generator')=='rule:special-v1' and f['kind']=='action' for f in clean['findings'])
    assert col['special']['policy']


def test_syntax_counts_domains_and_override(make_profile):
    d=make_profile(text(['email','url','lat'],[
        ['alpha@example.org','https://example.org:443/a','90'],
        ['bad@@example.org','http://example.org/x','-90'],
        ['test@test.com','http://bad host','91'],
    ])).document
    assert d['columns'][0]['special']['valid']==2 and d['columns'][0]['special']['invalid']==1
    assert d['columns'][0]['special']['test_values']==1
    assert d['columns'][1]['special']['domains']==[{'value':'example.org','count':2}]
    assert d['columns'][2]['special']['invalid']==1
    overridden=make_profile('phone\n000-000-0000\n',{'columns':{'phone':{'type':'string'}}}).document['columns'][0]
    assert overridden['inference']['type']=='phone' and overridden['effective_type']=='string'
    assert 'special' not in overridden


def test_no_network_or_sensitive_classification(make_profile,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('network lookup attempted')
    monkeypatch.setattr(socket,'getaddrinfo',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)
    d=make_profile('email\nalpha@example.org\nbeta@example.org\ngamma@example.org\n').document
    assert d['columns'][0]['special']['valid']==3
    assert 'quality_score' not in d and 'pii' not in d and 'phi' not in d


def test_values_only_recognition_and_coordinate_boundaries(make_profile):
    d=make_profile('contact\na@example.org\nb@example.org\nc@example.org\n').document
    assert d['columns'][0]['inference']['type']=='email'
    p=make_profile('x\n-180\n0\n180\n',{'columns':{'x':{'type':'longitude'}}}).document
    assert p['columns'][0]['special']['invalid']==0
    dates=make_profile('x\n2026-01-01\n2026-02-01\n2026-03-01\n').document
    assert dates['columns'][0]['effective_type']=='temporal'


def test_builder_acceptance_tables():
    from pathlib import Path
    from fathom.connectors import CSVConnector
    from fathom.profiler import profile
    root=Path(__file__).parent/'fixtures'/'special'
    d=profile(CSVConnector(root/'planted.csv').load()).document
    by={c['name']:c['special'] for c in d['columns'] if 'special' in c}
    assert {k:v['invalid'] for k,v in by.items()}=={'phone':1,'email':1,'website':2,'latitude':1,'longitude':1}
    assert by['phone']['placeholders']==by['email']['test_values']==1
    from fathom.renderers import render_html,render_markdown
    for view in (render_html,render_markdown):
        text=view(profile(CSVConnector(root/'planted.csv').load()))
        assert 'repeated-digit placeholder' in text and 'test-like address' in text and 'local syntax/range policy' in text
    clean=profile(CSVConnector(root/'clean.csv').load()).document
    assert not any(f['kind']=='action' and f['generator']=='rule:special-v1' for f in clean['findings'])
