import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
from datetime import datetime

BASE_URL = 'https://www.moore-bdr.sk/novinky/'
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Referer': BASE_URL
}

session = requests.Session()
session.headers.update(HEADERS)
session.get(BASE_URL)

SOURCE_NAME = 'Moore BDR s.r.o.'

def scrape_listing():
    """Fetches all article URLs and their publication dates from the novinky main page."""
    resp = session.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = []
    for article in soup.find_all('article'):
        h3 = article.find('h3', class_='entry-title')
        a = h3.find('a', href=True) if h3 else None
        time_tag = article.find('time', class_='entry-date')
        url = requests.compat.urljoin(BASE_URL, a['href']) if a else None
        post_date = ''
        if time_tag and time_tag.has_attr('datetime'):
            dt_str = time_tag['datetime']
            try:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                post_date = dt.strftime('%d.%m.%Y')
            except Exception:
                post_date = dt_str
        if url:
            articles.append((url, post_date))
    # Deduplicate while preserving order
    seen = set()
    result = []
    for url, post_date in articles:
        if url not in seen:
            result.append((url, post_date))
            seen.add(url)
    return result

def scrape_article(url):
    """Fetches title and content from an individual article page."""
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    content_div = soup.select_one('div.entry-content')
    content_lines = []
    if content_div:
        for element in content_div.stripped_strings:
            text = element.strip()
            if not text or text.lower() in ('share', 'viac', 'čítať ďalej'):
                continue
            content_lines.append(text)
    content = '\n\n'.join(content_lines)
    return title, content

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
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_df = load_existing()
    seen_urls = set(existing_df['url'])
    new_records = []

    articles = scrape_listing()
    for url, post_date in articles:
        if url in seen_urls:
            continue
        try:
            title, content = scrape_article(url)
            if title and content:
                new_records.append({
                    'title': title,
                    'content': content,
                    'post_date': post_date,
                    'url': url,
                    'source': SOURCE_NAME
                })
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        time.sleep(1)

    if new_records:
        df_new = pd.DataFrame(new_records)
        updated_df = pd.concat([existing_df, df_new], ignore_index=True)
        updated_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_records)} new articles. Total now {len(updated_df)}.")
    else:
        print("No new articles found.")

if __name__ == '__main__':
    main()
