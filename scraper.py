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
    url = f'{BASE_URL}?page={page}'
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    entries = soup.select('article.press-release')
    results = []
    for entry in entries:
        link_tag = entry.find('a', href=True)
        if not link_tag:
            continue
        link = link_tag['href']
        full_url = requests.compat.urljoin(BASE_URL, link)
        date_tag = entry.find('time')
        post_date = date_tag['datetime'] if date_tag else None
        results.append({'url': full_url, 'post_date': post_date})
    return results


def scrape_article(url):
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    content_div = soup.select_one('div.entry-content')
    paragraphs = content_div.find_all('p') if content_div else []
    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs)
    date_tag = soup.find('time')
    post_date = date_tag['datetime'] if date_tag else None
    return title, content, post_date


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    page = 1
    articles = []
    while True:
        listings = scrape_listing(page)
        if not listings:
            break
        for item in listings:
            title, content, post_date = scrape_article(item['url'])
            articles.append({
                'title': title,
                'content': content,
                'post_date': post_date,
                'url': item['url']
            })
            # Polite crawling
            time.sleep(1)
        print(f'Page {page} scraped, {len(listings)} articles.')
        page += 1

    df = pd.DataFrame(articles)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f'Saved {len(df)} articles to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
