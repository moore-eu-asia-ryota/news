import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time

# Base blog listing, first page has no /page/ suffix
BASE_LISTING = 'https://moorepolska.pl/blog/'
PAGE_URL = 'https://moorepolska.pl/blog/page/{page}/'
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')

# Browser-like headers
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

session = requests.Session()
session.headers.update(HEADERS)
session.get(BASE_LISTING)  # warm up

# Polish month names → two-digit month
PL_MONTHS = {
    'stycznia':'01', 'lutego':'02', 'marca':'03', 'kwietnia':'04',
    'maja':'05', 'czerwca':'06', 'lipca':'07', 'sierpnia':'08',
    'września':'09', 'października':'10', 'listopada':'11', 'grudnia':'12'
}

SOURCE_NAME = 'Moore Polska'

def scrape_listing(page):
    url = BASE_LISTING if page == 1 else PAGE_URL.format(page=page)
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Each post block has a link in <h2 class="entry-title"><a href="...">
    links = soup.select('h2.entry-title a[href]')
    return [a['href'] for a in links]

def scrape_article(url):
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Extract tags
    tags = [a.get_text(strip=True) for a in soup.select('.tags-links a[rel="tag"]')]
    if 'Artykuły' not in tags:
        return None

    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # Date: try <time datetime="...">, else polish month in header
    post_date = ''
    t = soup.find('time', attrs={'datetime': True})
    if t:
        post_date = t['datetime'][:10]
    else:
        # e.g. "13 marca 2025"
        meta = soup.select_one('.entry-meta')
        if meta:
            parts = meta.get_text(strip=True).split()
            if len(parts) >= 3:
                day, month_pl, year = parts[0], parts[1].lower(), parts[2]
                month = PL_MONTHS.get(month_pl, '01')
                post_date = f"{year}-{month}-{day.zfill(2)}"

    # Content
    content_div = soup.select_one('div.entry-content')
    content_lines = []
    if content_div:
        for block in content_div.find_all(['p','h2','h3','li']):
            text = block.get_text(strip=True)
            if text and text.lower() != 'share':
                content_lines.append(text)
    content = '\n\n'.join(content_lines)

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
                if c not in df: df[c] = ''
            return df[cols]
        except pd.errors.EmptyDataError:
            pass
    return pd.DataFrame(columns=cols)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing = load_existing()
    seen = set(existing['url'])
    new = []
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
                if rec:
                    new.append(rec)
            except Exception as e:
                print(f"Error scraping {u}: {e}")
            time.sleep(1)
        page += 1

    if new:
        df = pd.DataFrame(new)
        out = pd.concat([existing, df], ignore_index=True)
        out.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new)} new articles (total {len(out)}).")
    else:
        print("No new 'Artykuły' found.")

if __name__ == '__main__':
    main()
