"""Download recent arXiv papers on RLHF/RLAIF using arXiv API."""
import time
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse

from common import ROOT, N_PAPERS

RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# arXiv API query
QUERY = 'all:"RLHF" OR all:"RLAIF" OR all:"reinforcement learning from human feedback" OR all:"reinforcement learning from AI feedback"'
NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_metadata(n: int):
    """Query arXiv API for recent papers (sorted by submittedDate desc)."""
    base = "http://export.arxiv.org/api/query"
    params = {
        "search_query": QUERY,
        "start": 0,
        "max_results": n * 2,  # over-fetch in case some fail
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    print(f"Fetching arXiv metadata ({n*2} results)")
    req = urllib.request.Request(url, headers={"User-Agent": "compiled-kb-vs-rag-experiment/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml = r.read()
    root = ET.fromstring(xml)
    papers = []
    for entry in root.findall("atom:entry", NS):
        aid_full = entry.find("atom:id", NS).text.strip()
        aid = aid_full.rsplit("/", 1)[-1]  # e.g. 2410.12345v1
        aid = re.sub(r"v\d+$", "", aid)
        title = entry.find("atom:title", NS).text.strip().replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        summary = entry.find("atom:summary", NS).text.strip()
        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf" or link.get("type") == "application/pdf":
                pdf_url = link.get("href")
                break
        if pdf_url is None:
            pdf_url = f"https://arxiv.org/pdf/{aid}.pdf"
        papers.append({"id": aid, "title": title, "abstract": summary, "pdf_url": pdf_url})
    return papers


def download_pdf(url: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "compiled-kb-vs-rag-experiment/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 1000:
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  download failed for {url}: {e}")
        return False


def main():
    papers = fetch_metadata(N_PAPERS)
    print(f"Got {len(papers)} candidates, downloading PDFs")
    meta_path = ROOT / "data" / "papers_meta.jsonl"
    downloaded = []
    for p in papers:
        if len(downloaded) >= N_PAPERS:
            break
        dest = RAW / f"{p['id']}.pdf"
        ok = download_pdf(p["pdf_url"], dest)
        if ok:
            downloaded.append(p)
            print(f"  [{len(downloaded)}/{N_PAPERS}] {p['id']} - {p['title'][:70]}")
        time.sleep(3)  # arXiv rate limit
    import json
    with open(meta_path, "w") as f:
        for p in downloaded:
            f.write(json.dumps(p) + "\n")
    print(f"\nDownloaded {len(downloaded)} papers. Metadata -> {meta_path}")


if __name__ == "__main__":
    main()
