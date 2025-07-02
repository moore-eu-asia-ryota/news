import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from urllib.parse import urljoin

# ——— Configuration ———
# JetEngine archive for the "Artykuły" category (tax ID 31)
PAGE_URL      = 'https://moorepolska.pl/artykuly/?jsf=jet-engine&tax=category:31&pagenum={page}'
OUTPUT_DIR    = 'output'
OUTPUT_FILE   = os.path.join(OUTPUT_DIR, 'articles.csv')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pl-PL,pl;q=0.9',
    'Referer': 'https://moorepolska.pl/artykuly/'
}

session = requests.Session()
session.headers.update(HEADERS)

# Polish‐month lookup for fallback parsing
PL_MONTHS = {
    'stycznia':'01','lutego':'02','marca':'03','kwietnia':'04',
    'maja':'05','czerwca':'06','lipca':'07','sierpnia':'08',
    'września':'09','października':'10','listopada':'11','grudnia':'12'
}

SOURCE_NAME = 'Moore Polska'


def scrape_listing(page):
    """
    Fetch page {page} of the Artykuły archive and return
    all article URLs by selecting each "Czytaj dalej" link.
    """
    url = PAGE_URL.format(page=page)
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    urls = []
    for a in soup.find_all('a', href=True):
        if a.get_text(strip=True) == 'Czytaj dalej':
            full = urljoin(url, a['href'])
            if full not in urls:
                urls.append(full)
    return urls


def scrape_article(url):
    """
    Given an article URL, extract title, ISO date, and plain-text content.
    """
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Title
    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else ''

    # Date: prefer <time datetime="…">, else fallback to .entry-meta
    post_date = ''
    t = soup.find('time', datetime=True)
    if t:
        post_date = t['datetime'][:10]
    else:
        meta = soup.select_one('.entry-meta, .post-meta')
        if meta:
            parts = meta.get_text(strip=True).split()
            if len(parts) >= 3:
                day, mon_pl, year = parts[0], parts[1].lower(), parts[2]
                mon = PL_MONTHS.get(mon_pl, '01')
                post_date = f"{year}-{mon}-{day.zfill(2)}"

    # Content: grab text from paragraphs, headers, list items
    content_div = soup.select_one('div.entry-content') or soup.find('article')
    lines = []
    if content_div:
        for blk in content_div.find_all(['p','h2','h3','li']):
            txt = blk.get_text(strip=True)
            if txt and txt.lower() != 'share':
                lines.append(txt)
    content = '\n\n'.join(lines)

    return {
        'title': title,
        'content': content,
        'post_date': post_date,
        'url': url,
        'source': SOURCE_NAME
    }


def load_existing():
    cols = ['title','content','post_date','url','source']
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_csv(OUTPUT_FILE)
            for c in cols:
                if c not in df.columns:
                    df[c] = ''
            return df[cols]
        except pd.errors.EmptyDataError:
            pass
    return pd.DataFrame(columns=cols)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing = load_existing()
    seen = set(existing['url'])
    new_recs = []

    page = 1
    while True:
        urls = scrape_listing(page)
        if not urls:
            break
        for u in urls:
            if u in seen:
                continue
            try:
                rec = scrape_article(u)
                if rec['title'] and rec['content']:
                    new_recs.append(rec)
            except Exception as e:
                print(f"Error scraping {u}: {e}")
            time.sleep(1)
        page += 1

    if new_recs:
        df_new = pd.DataFrame(new_recs)
        df_out = pd.concat([existing, df_new], ignore_index=True)
        df_out.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_recs)} new articles (total {len(df_out)}).")
    else:
        print("No new articles found.")


if __name__ == '__main__':
    main()
