import os
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

# ─── CONFIG ─────────────────────────────────────────────────────────────

# template for each page of the "Artykuły" listing
LISTING_URL_TPL = (
    'https://moorepolska.pl/artykuly/'
    '?jsf=jet-engine&tax=category:31&pagenum={page}'
)

OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')
SOURCE_NAME = 'Moore Polska'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.headers.update(HEADERS)

# ─── PAGINATED LISTING SCRAPE ───────────────────────────────────────────

def scrape_listing():
    """
    Loop through pages 1, 2, ... until a page has no articles.
    Returns a de-duplicated list of article URLs.
    """
    page = 1
    urls = []
    while True:
        url = LISTING_URL_TPL.format(page=page)
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        items = soup.select('div.jet-listing-grid__item')
        if not items:
            break

        for item in items:
            a = item.find('a', href=True)
            if a:
                full = urljoin(url, a['href'])
                urls.append(full)

        page += 1
        time.sleep(0.5)  # be polite

    # preserve ordering, drop dupes
    return list(dict.fromkeys(urls))


# ─── SINGLE-ARTICLE SCRAPE ──────────────────────────────────────────────

def scrape_article(url):
    """
    Fetch title, publication date and the full text of one article.
    - Title: prefers <h1> text; if that <h1> wraps an <a>, grabs the <a> text.
    - Date: the visible text in <time>
    - Content: concatenates all headings + paragraphs in the body.
    """
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # ── TITLE ──
    title = ''
    h1 = soup.select_one('.elementor-widget-theme-post-title .elementor-heading-title')
    if h1:
        a = h1.find('a')
        title = a.get_text(strip=True) if a else h1.get_text(strip=True)
    else:
        # fallback to first <h1> or even <title> tag
        raw_h1 = soup.find('h1')
        if raw_h1:
            a = raw_h1.find('a')
            title = a.get_text(strip=True) if a else raw_h1.get_text(strip=True)
        else:
            # ultimate fallback
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ''

    # ── DATE ──
    date_el = soup.select_one('.elementor-widget-post-info time')
    post_date = date_el.get_text(strip=True) if date_el else ''

    # ── CONTENT ──
    parts = []
    # grab text-editor (paragraphs) and heading widgets in document order
    for sel in (
        '.elementor-widget-text-editor .elementor-widget-container',
        '.elementor-widget-heading .elementor-heading-title'
    ):
        for node in soup.select(sel):
            text = node.get_text(strip=True)
            if not text:
                continue
            # skip boilerplate
            low = text.lower()
            if low.startswith('zapraszamy') or low.startswith('może cię'):
                continue
            parts.append(text)

    content = '\n\n'.join(parts)
    return title, content, post_date


# ─── STATE LOAD / SAVE ───────────────────────────────────────────────────

def load_existing():
    cols = ['title', 'content', 'post_date', 'url', 'source']
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
    new_records = []

    for article_url in scrape_listing():
        if article_url in seen:
            continue
        try:
            title, content, date = scrape_article(article_url)
            if title and content:
                new_records.append({
                    'title': title,
                    'content': content,
                    'post_date': date,
                    'url': article_url,
                    'source': SOURCE_NAME
                })
        except Exception as e:
            print(f"Failed {article_url}: {e}")
        time.sleep(1)

    if new_records:
        df_new = pd.DataFrame(new_records)
        out = pd.concat([existing, df_new], ignore_index=True)
        out.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_records)} articles (total {len(out)})")
    else:
        print("No new articles found.")

if __name__ == '__main__':
    main()
