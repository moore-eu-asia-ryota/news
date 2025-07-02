#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import openpyxl
from urllib.parse import urljoin
import datetime
import re

BASE_URL       = 'https://www.moore-czech.cz'
LISTING_PATH   = '/tiskove-zpravy'
EXCEL_FILE     = 'News.xlsx'
SOURCE_NAME    = 'Moore Czech s.r.o.'

# Czech month abbreviations → month number
MONTH_MAP = {
    'led': 1, 'úno': 2, 'bře': 3, 'dub': 4,
    'kvě': 5, 'čvn': 6, 'čvc': 7, 'srp': 8,
    'zář': 9, 'říj':10, 'lis':11, 'pro':12
}

def parse_czech_date(d:str) -> datetime.date:
    # e.g. "30 čvn 2025"
    day, mon, year = d.split()
    key = mon[:3].lower()
    return datetime.date(int(year), MONTH_MAP[key], int(day))

def main():
    # load workbook & sheet
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb['Sheet1']

    # find existing URLs
    headers = [c.value for c in ws[1]]
    url_col = headers.index('URL') + 1
    existing = {
        row[url_col-1].value
        for row in ws.iter_rows(min_row=2)
        if row[url_col-1].value
    }

    # fetch listing page
    resp = requests.get(urljoin(BASE_URL, LISTING_PATH))
    soup = BeautifulSoup(resp.content, 'html.parser')
    items = soup.select('.view-content .views-row')

    for item in items:
        a = item.select_one('h5 a')
        if not a: continue
        title = a.get_text(strip=True)
        full_url = urljoin(BASE_URL, a['href'])
        if full_url in existing:
            continue

        # extract post‐date
        text = item.get_text(separator=' ').strip()
        m = re.search(r'(\d{1,2} \S+ \d{4})', text)
        raw_date = m.group(1)
        post_date = parse_czech_date(raw_date).strftime('%d.%m.%Y')

        # fetch detail page & pull full content
        r2 = requests.get(full_url)
        s2 = BeautifulSoup(r2.content, 'html.parser')
        body = s2.select_one('.field--name-field-body')
        if body:
            content = body.get_text('\n', strip=True)
        else:
            paras = s2.select('article p')
            content = '\n\n'.join(p.get_text(strip=True) for p in paras)

        # append to sheet
        ws.append([
            title,
            content,
            '',    # Title ENG blank
            '',    # Summary ENG blank
            post_date,
            full_url,
            SOURCE_NAME
        ])
        print(f'Added: {title}')

    wb.save(EXCEL_FILE)

if __name__ == '__main__':
    main()
