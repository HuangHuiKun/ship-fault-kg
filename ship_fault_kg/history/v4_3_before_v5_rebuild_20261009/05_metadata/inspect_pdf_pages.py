"""Inspect downloaded PDFs with page numbers and keyword snippets.

Usage: python inspect_pdf_pages.py PDF [KEYWORD ...]
"""

from pathlib import Path
import sys

from pypdf import PdfReader


def main() -> None:
    path = Path(sys.argv[1])
    args = sys.argv[2:]
    selected_pages = None
    if args and args[0] == "--pages":
        selected_pages = {int(x) for x in args[1].split(",")}
        args = args[2:]
    keywords = [x.casefold() for x in args]
    reader = PdfReader(path)
    print(f"FILE {path.name} PAGES {len(reader.pages)}")
    for page_number, page in enumerate(reader.pages, 1):
        if selected_pages is not None and page_number not in selected_pages:
            continue
        text = " ".join((page.extract_text() or "").split())
        if not keywords:
            print(f"PAGE {page_number}: {text[:12000]}")
            continue
        lower = text.casefold()
        for keyword in keywords:
            start = lower.find(keyword)
            if start >= 0:
                print(f"PAGE {page_number} KEY {keyword}: {text[max(0,start-180):start+420]}")


if __name__ == "__main__":
    main()
