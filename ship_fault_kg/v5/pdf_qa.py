"""Render primary evidence pages for visual source QA, without altering PDFs."""
import pypdfium2 as pdfium
from .preprocess import DATA,OUT

def main():
    out=OUT/'qa';out.mkdir(exist_ok=True)
    for file,page in [('MAN_SL2016_633_piston_rings_scuffing.pdf',2),
                      ('STAMFORD_AGN040_winding_insulation.pdf',7),
                      ('STAMFORD_AGN076_alternator_bearings.pdf',8)]:
        doc=pdfium.PdfDocument(str(DATA/'02_reports'/file))
        image=doc[page-1].render(scale=1.5).to_pil()
        path=out/(file.removesuffix('.pdf')+'_'+str(page)+'.png')
        image.save(path);doc.close();print(path)

if __name__=='__main__':main()
