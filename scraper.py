import requests
from bs4 import BeautifulSoup
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
# Warm up session to get cookies
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
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    # Date extraction
    date_header = soup.find('h4')
    post_date = ''
    if date_header:
        parts = date_header.get_text(strip=True).split()
        if len(parts) >= 3:
            day, month_cz, year = parts[0], parts[1].lower(), parts[2]
            month = CZECH_MONTHS.get(month_cz, '01')
            post_date = f"{year}-{month}-{day.zfill(2)}"
    # Content: collect all <p> tags after date_header
    content_parts = []
    if date_header:
        for p in date_header.find_all_next('p'):
            text = p.get_text(strip=True)
            if text:
                content_parts.append(text)
    content = '\n\n'.join(content_parts)
    return title, content, post_date


def load_existing():
    if os.path.exists(OUTPUT_FILE):
        try:
            return pd.read_csv(OUTPUT_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['title', 'content', 'post_date', 'url'])
    return pd.DataFrame(columns=['title', 'content', 'post_date', 'url'])


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_df = load_existing()
    existing_urls = set(existing_df['url'])
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
                if title:
                    new_records.append({'title': title,
                                        'content': content,
                                        'post_date': post_date,
                                        'url': url})
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
