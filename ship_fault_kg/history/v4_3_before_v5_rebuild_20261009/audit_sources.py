"""Check every curated page/anchor against the downloaded original PDF."""
import json
from build import Builder, ALL_CASES, CASE_ASSETS, clean
from fault_profiles import PROFILES


def main():
    builder = Builder()
    errors = []
    checked = 0
    for case in ALL_CASES:
        anchors = [(case['summary_page'], case['summary_anchor'])]
        assets = CASE_ASSETS.get(case['id'], (None, case.get('assets', [])))[1]
        anchors += [(asset[3], asset[4]) for asset in assets]
        anchors += [(fact[3], fact[4]) for fact in case['facts']]
        pages = builder.pdf_pages(case['source'])
        for page, anchor in anchors:
            checked += 1
            if clean(anchor).casefold() not in pages[page - 1].casefold():
                errors.append({'case': case['id'], 'page': page, 'anchor': anchor})
    for profile in PROFILES:
        for _, _, _, filename, page, anchor, _ in profile['facts']:
            checked += 1
            pages = builder.pdf_pages(filename)
            if not (1 <= page <= len(pages)) or clean(anchor).casefold() not in pages[page-1].casefold():
                errors.append({'knowledge_id': profile['id'], 'source': filename, 'page': page, 'anchor': anchor})
    result = {'checked': checked, 'reference_units': len(PROFILES), 'errors': errors,
              'limitation':'Exact page/anchor checks do not replace expert validation of translated engineering claims.'}
    from pathlib import Path
    (Path(__file__).resolve().parent / 'output' / 'source_anchor_audit_v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
