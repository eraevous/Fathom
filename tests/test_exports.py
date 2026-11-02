import builtins
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from fathom.exports import export_bundle


def test_optional_absence_preserves_core_status(make_profile,monkeypatch):
    original=builtins.__import__
    def no_extras(name,*args,**kwargs):
        if name.startswith(('reportlab','pptx')):raise ImportError('synthetic absent extra')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',no_extras)
    files,status=export_bundle(make_profile('x\n1\n2\n'),['pdf','pptx'])
    assert files=={} and all(x['status']=='unavailable' for x in status['formats'].values())


def test_pdf_content_and_determinism(make_profile):
    pytest.importorskip('reportlab')
    p=make_profile('title,amount\nAlpha,100\nAlpha,0\nBeta,200\nGamma,300\nDelta,400\n')
    one,status=export_bundle(p,['pdf']);two,_=export_bundle(p,['pdf'])
    pdf=one['report.pdf'];assert pdf==two['report.pdf'] and pdf.startswith(b'%PDF-')
    assert b'First rows' in pdf and b'Last rows' in pdf and b'Random rows' in pdf
    assert b'Dataset summary' in pdf
    assert status['formats']['pdf']['status']=='written'
    from fathom.profiler import compare
    files,_=export_bundle(compare(p,p),['pdf'])
    assert b'Contexts' in files['report.pdf'] and b'Measured deltas' in files['report.pdf']


def test_pptx_content_charts_and_determinism(make_profile):
    pptx=pytest.importorskip('pptx')
    p=make_profile('amount,category\n100,A\n200,B\n300,A\n400,B\n')
    one,status=export_bundle(p,['pptx']);two,_=export_bundle(p,['pptx'])
    data=one['report.pptx'];assert data==two['report.pptx']
    deck=pptx.Presentation(io.BytesIO(data));assert len(deck.slides)>=5
    assert any('Dataset summary' in slide.shapes.title.text for slide in deck.slides if slide.shapes.title)
    assert any(shape.has_chart for slide in deck.slides for shape in slide.shapes)
    with zipfile.ZipFile(io.BytesIO(data)) as z:assert all(x.date_time==(1980,1,1,0,0,0) for x in z.infolist())
    from fathom.profiler import compare
    files,_=export_bundle(compare(p,p),['pptx'])
    deck=pptx.Presentation(io.BytesIO(files['report.pptx']))
    assert any(s.shapes.title.text.startswith('Measured deltas') for s in deck.slides)
    assert not any('{' in shape.text for s in deck.slides for shape in s.shapes if shape.has_text_frame)


def test_cli_export_fresh_process_bytes(make_profile,tmp_path):
    pytest.importorskip('reportlab');pytest.importorskip('pptx')
    p=tmp_path/'saved.json';p.write_text(make_profile('x\n1\n2\n3\n').to_json())
    env={**os.environ,'PYTHONPATH':str(Path(__file__).parents[1]/'src')}
    for name in ('one','two'):
        run=subprocess.run([sys.executable,'-m','fathom','export',str(p),'--out',str(tmp_path/name)],capture_output=True,text=True,env=env)
        assert run.returncode==0,run.stderr
    for name in ('report.pdf','report.pptx','report.html','report.md','export-status.json'):
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes()


def test_formats_are_independent_and_unicode_is_disclosed(make_profile,monkeypatch):
    pytest.importorskip('pptx');pytest.importorskip('reportlab')
    original=builtins.__import__
    def no_pdf(name,*args,**kwargs):
        if name.startswith('reportlab'):raise ImportError('synthetic absent extra')
        return original(name,*args,**kwargs)
    p=make_profile('item\n合成\n😀\n')
    with monkeypatch.context() as m:
        m.setattr(builtins,'__import__',no_pdf)
        files,status=export_bundle(p,['pdf','pptx'])
        assert set(files)=={'report.pptx'} and status['formats']['pdf']['status']=='unavailable'
    files,status=export_bundle(p,['pdf'])
    assert status['formats']['pdf']['unsupported_glyph_replacements']>0


def test_export_invalid_input_writes_nothing(tmp_path):
    bad=tmp_path/'bad.json';bad.write_text('{}')
    from fathom.cli import main
    out=tmp_path/'absent'
    assert main(['export',str(bad),'--out',str(out)])==2
    assert not out.exists()
