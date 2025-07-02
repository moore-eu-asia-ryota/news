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
    Scrape the listing page for article URLs using <h5> headings.
    """
    url = f'{BASE_URL}?page={page}'
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    urls = []
    # Entries are marked by <h5> tags containing an <a> to the article
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
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    # Content paragraphs
    content_div = soup.select_one('div.entry-content')
    paragraphs = content_div.find_all('p') if content_div else []
    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
    # Date from <time> element
    date_tag = soup.find('time')
    post_date = date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else None
    return title, content, post_date


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    page = 1
    articles = []
    while True:
        urls = scrape_listing(page)
        if not urls:
            break
        print(f'Page {page} found {len(urls)} articles.')
        for url in urls:
            try:
                title, content, post_date = scrape_article(url)
                articles.append({
                    'title': title,
                    'content': content,
                    'post_date': post_date,
                    'url': url
                })
                # Polite crawl delay
                time.sleep(1)
            except Exception as e:
                print(f'Error scraping {url}: {e}')
        page += 1

    df = pd.DataFrame(articles)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f'Saved {len(df)} articles to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
