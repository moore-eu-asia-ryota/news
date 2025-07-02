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
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/115.0.0.0 Safari/537.36'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Referer': BASE_URL
}

session = requests.Session()
session.headers.update(HEADERS)
# Warm up session to get cookies
session.get(BASE_URL)

CZECH_MONTHS = {
    'ledna': '01', 'února': '02', 'března': '03', 'dubna': '04',
    'května': '05', 'června': '06', 'července': '07', 'srpna': '08',
    'září': '09', 'října': '10', 'listopadu': '11', 'prosince': '12'
}

def scrape_listing(page):
    url = f"{BASE_URL}?page={page}"
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Article links in listing are under <h5><a>
    return [requests.compat.urljoin(BASE_URL, a['href'])
            for a in soup.select('h5 a[href]')]

def scrape_article(url):
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Title: try h1, then first h2
    title_tag = soup.find('h1') or soup.find('h2')
    title = title_tag.get_text(strip=True) if title_tag else ''
    # Date: look for <time datetime> or <h4>
    post_date = ''
    time_tag = soup.find('time')
    if time_tag and time_tag.has_attr('datetime'):
        post_date = time_tag['datetime']
    else:
        h4_tag = soup.find('h4')
        if h4_tag:
            parts = h4_tag.get_text(strip=True).split()
            if len(parts) >= 3:
                day, month_cz, year = parts[0], parts[1].lower(), parts[2]
                month = CZECH_MONTHS.get(month_cz, '01')
                post_date = f"{year}-{month}-{day.zfill(2)}"
    # Content: get all visible text inside entry-content or article
    content_div = soup.select_one('div.entry-content') or soup.find('article')
    content = ''
    if content_div:
        raw = content_div.get_text(separator='\n').splitlines()
        lines = [line.strip() for line in raw if line.strip() and line.strip().lower() != 'share']
        content = '\n\n'.join(lines)
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
    seen_urls = set(existing_df['url'])
    new_records = []
    page = 1
    while True:
        urls = scrape_listing(page)
        if not urls:
            break
        print(f"Page {page} found {len(urls)} articles.")
        for url in urls:
            if url in seen_urls:
                continue
            try:
                title, content, post_date = scrape_article(url)
                if title and content:
                    new_records.append({
                        'title': title,
                        'content': content,
                        'post_date': post_date,
                        'url': url
                    })
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            time.sleep(1)
        page += 1
    if new_records:
        updated = pd.concat([existing_df, pd.DataFrame(new_records)], ignore_index=True)
        updated.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_records)} new articles. Total now {len(updated)}.")
    else:
        print("No new articles found.")

if __name__ == '__main__':
    main()
