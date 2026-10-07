"""Render selected downloaded PDF pages for visual source QA only."""
from pathlib import Path
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'ship_fault_kg'/'output'/'source_review'
OUT.mkdir(exist_ok=True)
for filename,page in [('MAN_SL2016_633_piston_rings_scuffing.pdf',2),
                      ('STAMFORD_AGN039_marine_shaft_generators.pdf',2),
                      ('Frontiers_2021_marine_converter_oscillations.pdf',6)]:
    with pdfium.PdfDocument(ROOT/'ship_fault_kg_data'/'02_reports'/filename) as doc:
        output=OUT/(Path(filename).stem+f'_page{page}.png')
        doc[page-1].render(scale=1.25).to_pil().save(output)
        print(output)
