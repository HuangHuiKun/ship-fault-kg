"""Download primary-source PDFs for the fault-centred revision, without overwriting old sources."""
import csv
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.error import URLError
from urllib.request import Request, urlopen
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'ship_fault_kg_data'
OUT = ROOT / 'ship_fault_kg' / 'output'
SOURCES = [
    ('MAN_SL2016_633_piston_rings_scuffing.pdf', 'MAN SL2016-633 hard-coated piston rings and liner scuffing', 'https://www.man-es.com/docs/default-source/service-letters/sl2016-633.pdf', 'MAN SL2016-633', 'manufacturer_guidance'),
    ('MAN_SL2019_685_ring_coating_wear.pdf', 'MAN SL2019-685 condition-based overhaul of cermet piston rings', 'https://www.man-es.com/docs/default-source/service-letters/sl2019-685.pdf', 'MAN SL2019-685', 'manufacturer_guidance'),
    ('MAN_SL2023_737_cylinder_lubrication.pdf', 'MAN SL2023-737 cylinder lubrication update', 'https://www.man-es.com/docs/default-source/service-letters/sl2023-737.pdf', 'MAN SL2023-737', 'manufacturer_guidance'),
    ('MAN_SL2013_569_bearing_wear_monitoring.pdf', 'MAN SL2013-569 bearing wear monitoring and bearing seizure', 'https://www.man-es.com/docs/default-source/service-letters/sl2013-569.pdf', 'MAN SL2013-569', 'manufacturer_guidance'),
    ('MAN_SL2017_654_torsional_damper.pdf', 'MAN SL2017-654 crankshaft torsional vibration damper', 'https://www.man-es.com/docs/default-source/service-letters/sl2017-654.pdf', 'MAN SL2017-654', 'manufacturer_guidance'),
    ('MAN_SL2016_623_cooling_water.pdf', 'MAN SL2016-623 cooling water treatment and periodical testing', 'https://www.man-es.com/docs/default-source/service-letters/sl2016-623.pdf', 'MAN SL2016-623', 'manufacturer_guidance'),
    ('MAN_main_engine_auxiliary_efficiency.pdf', 'MAN efficiency improvements main engine auxiliary systems', 'https://www.man-es.com/docs/default-source/document-sync/efficiency-improvements-main-engine-auxiliary-systems-eng.pdf', 'MAN auxiliary systems', 'manufacturer_guidance'),
    ('STAMFORD_AGN040_winding_insulation.pdf', 'STAMFORD AGN040 winding insulation system', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-040_E-Winding-Insulation-System.pdf', 'AGN040', 'manufacturer_guidance'),
    ('STAMFORD_AGN033_bearing_currents.pdf', 'STAMFORD AGN033 shaft bearing currents', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-033_C-Shaft-Bearing-Currents.pdf', 'AGN033', 'manufacturer_guidance'),
    ('STAMFORD_AGN039_marine_shaft_generators.pdf', 'STAMFORD AGN039 marine shaft generators', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-039_C-Marine-Shaft-Generators.pdf', 'AGN039', 'manufacturer_guidance'),
    ('STAMFORD_AGN235_torsional_analysis.pdf', 'STAMFORD AGN235 generating set torsional vibration analysis', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-235_A-Generating-Set-Assembly-Torsional-Vibration-Analysis.pdf', 'AGN235', 'manufacturer_guidance'),
    ('STAMFORD_AGN232_coupling_arrangements.pdf', 'STAMFORD AGN232 generating set coupling arrangements', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-232_B-Generating-Set-Assembly-Coupling-Arrangements.pdf', 'AGN232', 'manufacturer_guidance'),
    ('STAMFORD_AGN035_fault_protection.pdf', 'STAMFORD AGN035 overload fault protection and transient coupling torque', 'https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/AGN-035_B-Overload-and-Fault-Protection.pdf', 'AGN035', 'manufacturer_guidance'),
    ('STAMFORD_AGN076_alternator_bearings.pdf', 'STAMFORD AGN076 alternator bearings', 'https://www.stamford-avk.com/sites/stamfordavk/files/2024-04/AGN076_C.pdf', 'AGN076', 'manufacturer_guidance'),
    ('Frontiers_2021_marine_converter_oscillations.pdf', 'Comparative Case Study on Oscillatory Behavior in Power Systems of Marine Vessels With High Power Converters', 'https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2020.529756/pdf', '10.3389/fenrg.2020.529756', 'research_paper'),
    ('MAIB_2017_20_Hebrides_CPP_coupling.pdf', 'MAIB Hebrides CPP actuator coupling failure', 'https://assets.publishing.service.gov.uk/media/59b7ab1c40f0b61231e71a54/MAIBInvReport20_2017.pdf', 'MAIB 20/2017', 'field_report'),
]

def download(item):
    filename, title, url, ident, origin = item
    path = DATA / '02_reports' / filename
    if not path.exists():
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (local academic source archive)'})
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read()
        except URLError as error:
            # Windows curl uses the OS certificate store; never disable TLS verification.
            if 'CERTIFICATE_VERIFY_FAILED' not in str(error):
                raise
            payload = subprocess.check_output(['curl.exe', '--fail', '--location', '--silent',
                                               '--show-error', '--max-time', '60', url])
        if not payload.startswith(b'%PDF'):
            raise ValueError(f'Not a PDF: {filename}')
        path.write_bytes(payload)
    reader = PdfReader(path)
    pages = [' '.join((p.extract_text() or '').split()) for p in reader.pages]
    if not any(len(p) > 100 for p in pages):
        raise ValueError(f'No searchable text: {filename}')
    license_note = ('CC BY; credit original authors and DOI' if origin == 'research_paper' else
                    'OGL v3.0 except third-party material' if origin == 'field_report' else
                    'Copyright manufacturer; local internal research; no public redistribution of full PDF')
    row = dict(category='reference_pdf', local_item='02_reports/' + filename, title=title,
               source_url=url, doi_or_id=ident, license_or_reuse=license_note,
               primary_use=origin, validation=f'PDF parsed; {len(pages)} physical pages')
    return row, {'file': filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'bytes': path.stat().st_size, 'pages': pages, 'origin': origin, 'url': url}

def main():
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(download, SOURCES))
    manifest = DATA / '05_metadata' / 'source_manifest_v3.csv'
    with manifest.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0][0]))
        writer.writeheader()
        writer.writerows(row for row, _ in results)
    (OUT / 'new_source_pages_v3.json').write_text(json.dumps([x for _, x in results], ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{'file':x['file'], 'pages':len(x['pages']), 'bytes':x['bytes']} for _,x in results], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
