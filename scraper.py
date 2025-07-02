```python
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import pandas as pd
import os
import time

BASE_URL = 'https://www.moore-czech.cz/tiskove-zpravy'
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')

# Browser-like headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Referer': BASE_URL
}

session = requests.Session()
session.headers.update(HEADERS)
# Warm up session to get any cookies
resp_init = session.get(BASE_URL)
resp_init.raise_for_status()

CZECH_MONTHS = {
    'ledna': '01', 'února': '02', 'března': '03', 'dubna': '04',
    'května': '05', 'června': '06', 'července': '07', 'srpna': '08',
    'září': '09', 'října': '10', 'listopadu': '11', 'prosince': '12'
}

def scrape_listing(page):
    url = f'{BASE_URL}?page={page}'
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    urls = []
    for heading in soup.find_all('h5'):
        a = heading.find('a', href=True)
        if a:
            full_url = requests.compat.urljoin(BASE_URL, a['href'])
            urls.append(full_url)
    return urls


def scrape_article(url):
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    date_header = soup.find('h4')
    date_text = date_header.get_text(strip=True) if date_header else ''
    post_date = ''
    if date_text:
        parts = date_text.split()
        if len(parts) >= 3:
            day, month_cz, year = parts[0], parts[1], parts[2]
            month = CZECH_MONTHS.get(month_cz.lower(), '01')
            post_date = f"{year}-{month}-{day.zfill(2)}"
    content_parts = []
    if date_header:
        for sib in date_header.next_siblings:
            if isinstance(sib, Tag) and sib.name and sib.name.startswith('h'):
                break
            if isinstance(sib, Tag) and sib.name == 'p':
                txt = sib.get_text(strip=True)
                if txt:
                    content_parts.append(txt)
            if isinstance(sib, NavigableString):
                txt = sib.strip()
                if txt:
                    content_parts.append(txt)
    content = '\n\n'.join(content_parts)
    return title, content, post_date


def load_existing():
    """
    Load existing CSV if present, handling empty files gracefully.
    """
    if os.path.exists(OUTPUT_FILE):
        try:
            return pd.read_csv(OUTPUT_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['title', 'content', 'post_date', 'url'])
    else:
        return pd.DataFrame(columns=['title', 'content', 'post_date', 'url'])


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_df = load_existing()
    existing_urls = set(existing_df['url'].tolist())
    new_records = []
    page = 1
    while True:
        urls = scrape_listing(page)
        if not urls:
            break
        print(f'Page {page} found {len(urls)} articles.')
        for url in urls:
            if url in existing_urls:
                continue
            try:
                title, content, post_date = scrape_article(url)
                new_records.append({
                    'title': title,
                    'content': content,
                    'post_date': post_date,
                    'url': url
                })
                time.sleep(1)
            except Exception as e:
                print(f'Error scraping {url}: {e}')
        page += 1

    if new_records:
        updated_df = pd.concat([existing_df, pd.DataFrame(new_records)], ignore_index=True)
        updated_df.to_csv(OUTPUT_FILE, index=False)
        print(f'Added {len(new_records)} new articles. Total now {len(updated_df)}.')
    else:
        print('No new articles found.')

if __name__ == '__main__':
    main()
