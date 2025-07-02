import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from urllib.parse import urljoin

# ——— Configuration ———
BASE_LISTING  = 'https://moorepolska.pl/artykuly/'
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
    'Connection': 'keep-alive',
    'Referer': BASE_LISTING
}

# Warm up session to pick up cookies, etc.
session = requests.Session()
session.headers.update(HEADERS)
session.get(BASE_LISTING)

# For fallback Polish‐month parsing (if <time> isn’t present)
PL_MONTHS = {
    'stycznia':'01','lutego':'02','marca':'03','kwietnia':'04',
    'maja':'05','czerwca':'06','lipca':'07','sierpnia':'08',
    'września':'09','października':'10','listopada':'11','grudnia':'12'
}

SOURCE_NAME = 'Moore Polska'


def scrape_listing():
    """
    Hit /artykuly/ once, pull every <h3><a href="…">…</a></h3>,
    return a deduped list of full URLs.
    """
    resp = session.get(BASE_LISTING)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    urls = []
    seen = set()
    for h3 in soup.find_all('h3'):
        a = h3.find('a', href=True)
        if not a:
            continue
        full = urljoin(BASE_LISTING, a['href'])
        if full not in seen:
            seen.add(full)
            urls.append(full)

    return urls


def scrape_article(url):
    """
    Given one article URL, fetch title, date, and content.
    """
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # — Title
    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else ''

    # — Date: prefer <time datetime="YYYY-MM-DD…"> fallback to .entry-meta text
    post_date = ''
    t = soup.find('time', attrs={'datetime': True})
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

    # — Content: grab all <p>, <h2>, <h3>, <li> under .entry-content
    cont = soup.select_one('div.entry-content')
    lines = []
    if cont:
        for blk in cont.find_all(['p','h2','h3','li']):
            txt = blk.get_text(strip=True)
            if txt and txt.lower() != 'share':
                lines.append(txt)
    content = '\n\n'.join(lines)

    return {
        'title':   title,
        'content': content,
        'post_date': post_date,
        'url':     url,
        'source':  SOURCE_NAME
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
    seen_urls = set(existing['url'].tolist())

    new_records = []
    for url in scrape_listing():
        if url in seen_urls:
            continue
        try:
            rec = scrape_article(url)
            if rec['title'] and rec['content']:
                new_records.append(rec)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        time.sleep(1)

    if new_records:
        df_new = pd.DataFrame(new_records)
        out = pd.concat([existing, df_new], ignore_index=True)
        out.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_records)} articles (total {len(out)}).")
    else:
        print("No new articles found.")


if __name__ == '__main__':
    main()
