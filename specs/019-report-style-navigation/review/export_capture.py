"""Rasterize actual PDF and actual LibreOffice-rendered PPTX, never mock slides."""
from pathlib import Path
import fitz,json
out=Path(__file__).parent;manifest={}
for fmt,path in [('pdf',Path('/tmp/style-after/report.pdf')),('pptx',Path('/tmp/style-slides/report.pdf'))]:
 d=fitz.open(path)
 targets=[('head',0)]
 if fmt=='pdf':
  i=next((i for i,p in enumerate(d) if 'Findings' in p.get_text()),0);targets.append(('findings',i))
 else:
  i=next((i for i,p in enumerate(d) if 'Target ranking' in p.get_text()),0);targets.append(('ranking',i))
 for name,i in targets:
  for width in [1280,390]:
   p=d[i];pix=p.get_pixmap(matrix=fitz.Matrix(width/p.rect.width,width/p.rect.width));filename=f'after-{fmt}-{name}-{width}.png';pix.save(out/filename);manifest[filename]={'page':i+1,'pages':len(d),'width':pix.width,'renderer':'ReportLab/PyMuPDF' if fmt=='pdf' else 'LibreOffice Impress/PyMuPDF'}
(out/'export-checks.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
