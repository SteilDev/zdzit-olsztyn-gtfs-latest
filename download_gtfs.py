import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import certifi

URL = "https://zdzit.olsztyn.eu/gtfs/"
date_pattern = re.compile(r"(\d{4}_\d{2}_\d{2})")

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y_%m_%d")

def extract_date_range(text: str):
    matches = date_pattern.findall(text)
    if not matches:
        return None, None
    if len(matches) == 1:
        return parse_date(matches[0]), parse_date(matches[0])
    return parse_date(matches[0]), parse_date(matches[1])

def safe_get(url: str):
    try:
        return requests.get(url, verify=certifi.where(), timeout=30)
    except requests.exceptions.SSLError:
        return requests.get(url, verify=False, timeout=30)

def get_latest_gtfs_info(page_url: str):
    resp = safe_get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    gtfs_files = []
    for a in soup.select("a[href$='.zip']"):
        href = a["href"]
        text = a.get_text(strip=True)
        start, end = extract_date_range(text)
        if start and end:
            gtfs_files.append({"url": href, "text": text, "start": start, "end": end})

    if gtfs_files:
        # choose by latest end date
        gtfs_files.sort(key=lambda x: x["end"], reverse=True)
        return gtfs_files[0]
    else:
        # fallback: just take the last .zip link
        all_links = [a["href"] for a in soup.select("a[href$='.zip']")]
        if not all_links:
            raise RuntimeError("No GTFS .zip links found at all")
        last_href = all_links[-1]
        return {"url": last_href, "text": last_href, "start": None, "end": None}

def download_file(url: str, dest: str):
    with safe_get(url) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    latest = get_latest_gtfs_info(URL)
    download_file(latest["url"], "gtfs_zdzit_olsztyn_latest.zip")

if __name__ == "__main__":
    main()

