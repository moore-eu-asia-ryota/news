import os
import time
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

# ─── CONFIG ─────────────────────────────────────────────────────────────

# start on the first page of the "Artykuły" listing
BASE_URL = 'https://moorepolska.pl/artykuly/?jsf=jet-engine&tax=category:31&pagenum=1'
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')
SOURCE_NAME = 'Moore Polska'

# browser-like headers
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': BASE_URL
}

session = requests.Session()
session.headers.update(HEADERS)
session.get(BASE_URL)  # warm up cookies

# ─── LISTING PAGE ────────────────────────────────────────────────────────

def scrape_listing():
    """Fetch all article URLs from the Artykuły listing page."""
    resp = session.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    urls = []
    # each card is a .jet-listing-grid__item
    for item in soup.select('div.jet-listing-grid__item'):
        a = item.find('a', href=True)
        if not a:
            continue
        link = urljoin(BASE_URL, a['href'])
        urls.append(link)

    # preserve order + dedupe
    return list(dict.fromkeys(urls))

# ─── ARTICLE PAGE ────────────────────────────────────────────────────────

def scrape_article(url):
    """Extract title, publication date and full text from a single article."""
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # --- title ---
    title_tag = soup.select_one('.elementor-widget-theme-post-title .elementor-heading-title')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # --- date ---
    date_tag = soup.select_one('.elementor-widget-post-info time')
    post_date = date_tag.get_text(strip=True) if date_tag else ''

    # --- content: pull all headings + text blocks in order ---
    content_parts = []
    # we target both text-editor (paragraphs) and heading widgets
    for widget in soup.select(
        '.elementor-widget-text-editor .elementor-widget-container, '
        '.elementor-widget-heading .elementor-heading-title'
    ):
        text = widget.get_text(strip=True)
        # skip empty or boilerplate
        if not text or text.lower().startswith(('zapraszamy','może cię')):
            continue
        content_parts.append(text)

    content = '\n\n'.join(content_parts)
    return title, content, post_date

# ─── STATE HANDLING ──────────────────────────────────────────────────────

def load_existing():
    cols = ['title', 'content', 'post_date', 'url', 'source']
    if os.path.exists(OUTPUT_FILE):
        try:
            df = pd.read_csv(OUTPUT_FILE)
            for c in cols:
                if c not in df:
                    df[c] = ''
            return df[cols]
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

# ─── MAIN ────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing = load_existing()
    seen = set(existing['url'])
    new_entries = []

    for url in scrape_listing():
        if url in seen:
            continue
        try:
            title, content, post_date = scrape_article(url)
            if title and content:
                new_entries.append({
                    'title': title,
                    'content': content,
                    'post_date': post_date,
                    'url': url,
                    'source': SOURCE_NAME
                })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        time.sleep(1)

    if new_entries:
        df_new = pd.DataFrame(new_entries)
        df_out = pd.concat([existing, df_new], ignore_index=True)
        df_out.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_entries)} new articles. Total now {len(df_out)}.")
    else:
        print("No new articles found.")

if __name__ == '__main__':
    main()
