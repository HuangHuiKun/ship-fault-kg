"""Check every curated page/anchor against the downloaded original PDF."""
import json
from build import Builder, ALL_CASES, CASE_ASSETS, clean


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
    print(json.dumps({'checked': checked, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
