"""Rasterize real PDF and LibreOffice-rendered PPTX; no mock presentation pages."""
from pathlib import Path
import fitz,json
out=Path(__file__).parent;manifest={}
for kind,path in [('pdf-rows','/tmp/view20-after/report.pdf'),('pdf-metrics','/tmp/view20-metrics/report.pdf'),('pptx-rows','/tmp/view20-slides/report.pdf'),('pptx-metrics','/tmp/view20-metric-slides/report.pdf'),('pptx-full','/tmp/view20-slides/full.pdf')]:
 d=fitz.open(path);paired='full' in kind
 needle='contrast with rest' if paired else 'Numeric column metrics'
 index=next(i for i,p in enumerate(d) if needle in p.get_text())
 for width in [1280,390]:
  p=d[index];pix=p.get_pixmap(matrix=fitz.Matrix(width/p.rect.width,width/p.rect.width));name=f'after-{kind}-{width}.png';pix.save(out/name);manifest[name]={'width':pix.width,'page':index+1,'pages':len(d),'renderer':'ReportLab/PyMuPDF' if kind.startswith('pdf') else 'LibreOffice Impress/PyMuPDF','topic':needle}
 # Capture a paired PDF finding too, independent of the summary page.
 if kind=='pdf-rows':
  index=next(i for i,p in enumerate(d) if 'contrast with rest' in p.get_text())
  for width in [1280,390]:
   p=d[index];pix=p.get_pixmap(matrix=fitz.Matrix(width/p.rect.width,width/p.rect.width));name=f'after-pdf-finding-{width}.png';pix.save(out/name);manifest[name]={'width':pix.width,'page':index+1,'pages':len(d),'renderer':'ReportLab/PyMuPDF','topic':'paired finding'}
(out/'export-checks.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
