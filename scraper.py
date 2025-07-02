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
# Warm up session to get any cookies
resp_init = session.get(BASE_URL)
resp_init.raise_for_status()

def scrape_listing(page):
    """
    Scrape the listing page for article URLs from <h5> headings.
    """
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
    """
    Scrape individual article page for title, content, and post_date.
    """
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
    content_div = soup.select_one('div.entry-content')
    paragraphs = content_div.find_all('p') if content_div else []
    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
    date_tag = soup.find('time')
    post_date = date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else ''
    return title, content, post_date


def load_existing():
    """
    Load existing CSV if present, else return empty DataFrame.
    """
    if os.path.exists(OUTPUT_FILE):
        return pd.read_csv(OUTPUT_FILE)
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
        new_df = pd.DataFrame(new_records)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        updated_df.to_csv(OUTPUT_FILE, index=False)
        print(f'Added {len(new_records)} new articles. Total now {len(updated_df)}.')
    else:
        print('No new articles found.')

if __name__ == '__main__':
    main()
