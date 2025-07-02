#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import openpyxl
from openpyxl.utils import range_boundaries
from urllib.parse import urljoin
import datetime
import re

BASE_URL     = 'https://www.moore-czech.cz'
LISTING_PATH = '/tiskove-zpravy'
EXCEL_FILE   = 'News.xlsx'
TABLE_NAME   = 'News'
SOURCE_NAME  = 'Moore Czech s.r.o.'

# pretend to be a real browser
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    )
}

# Map Czech month abbreviations → month number
MONTH_MAP = {
    'led': 1, 'úno': 2, 'bře': 3, 'dub': 4,
    'kvě': 5, 'čvn': 6, 'čvc': 7, 'srp': 8,
    'zář': 9, 'říj':10, 'lis':11, 'pro':12
}

def parse_czech_date(d: str) -> datetime.date:
    # e.g. "30 čvn 2025"
    day, mon, year = d.split()
    key = mon[:3].lower()
    return datetime.date(int(year), MONTH_MAP[key], int(day))

def main():
    # 1) Load workbook & identify your table by name
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb['Sheet1']
    table = ws.tables[TABLE_NAME]
    min_col, min_row, max_col, max_row = range_boundaries(table.ref)

    # 2) Read headers
    headers = [
        ws.cell(row=min_row, column=col).value.strip()
        for col in range(min_col, max_col + 1)
    ]
    if 'URL' not in headers:
        raise RuntimeError(f"'URL' column not found: {headers}")
    url_idx = headers.index('URL')
    url_col = min_col + url_idx

    # 3) Collect existing URLs
    existing = {
        ws.cell(row=row, column=url_col).value
        for row in range(min_row+1, ws.max_row+1)
        if ws.cell(row=row, column=url_col).value
    }

    # 4) Fetch listing page with browser‐like headers
    resp = requests.get(urljoin(BASE_URL, LISTING_PATH), headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    items = soup.select('.view-content .views-row')

    # 5) Scrape each entry
    for item in items:
        a = item.select_one('h5 a')
        if not a:
            continue
        title = a.get_text(strip=True)
        full_url = urljoin(BASE_URL, a['href'])
        if full_url in existing:
            continue

        # extract date
        raw = item.get_text(separator=' ')
        m = re.search(r'(\d{1,2} \S+ \d{4})', raw)
        if not m:
            continue
        post_date = parse_czech_date(m.group(1)).strftime('%d.%m.%Y')

        # fetch detail page with headers
        r2 = requests.get(full_url, headers=HEADERS)
        r2.raise_for_status()
        s2 = BeautifulSoup(r2.content, 'html.parser')

        body = s2.select_one('.field--name-field-body')
        if body:
            content = body.get_text('\n', strip=True)
        else:
            paras = s2.select('article p')
            content = '\n\n'.join(p.get_text(strip=True) for p in paras)

        # append new row
        ws.append([
            title,         # Title Original
            content,       # Content Original
            '',            # Title ENG
            '',            # Summary ENG
            post_date,     # PostDate
            full_url,      # URL
            SOURCE_NAME    # Source
        ])
        print(f'Added: {title}')

    # 6) Save
    wb.save(EXCEL_FILE)

if __name__ == '__main__':
    main()
