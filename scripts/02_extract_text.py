"""Extract plaintext from the downloaded arXiv PDFs using PyMuPDF."""
import json
import re
from pathlib import Path

import fitz  # pymupdf

from common import ROOT

RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "raw_text"
OUT.mkdir(parents=True, exist_ok=True)


def extract(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    doc.close()
    txt = "\n".join(parts)
    # normalize whitespace (keep paragraph breaks)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def main():
    meta_path = ROOT / "data" / "papers_meta.jsonl"
    meta = [json.loads(l) for l in open(meta_path)]
    ok = 0
    skipped = []
    for p in meta:
        pdf = RAW / f"{p['id']}.pdf"
        dest = OUT / f"{p['id']}.txt"
        if dest.exists():
            ok += 1
            continue
        if not pdf.exists():
            skipped.append(p["id"])
            continue
        try:
            text = extract(pdf)
            if len(text) < 2000:
                print(f"  [skip] {p['id']}: extracted only {len(text)} chars")
                skipped.append(p["id"])
                continue
            dest.write_text(text)
            ok += 1
        except Exception as e:
            print(f"  [err] {p['id']}: {e}")
            skipped.append(p["id"])
    print(f"\nExtracted {ok} / {len(meta)} (skipped {len(skipped)})")

    # If any paper was skipped, drop it from meta so downstream stages stay consistent.
    if skipped:
        kept = [p for p in meta if p["id"] not in skipped]
        with open(meta_path, "w") as f:
            for p in kept:
                f.write(json.dumps(p) + "\n")
        print(f"Updated meta to {len(kept)} papers")


if __name__ == "__main__":
    main()
