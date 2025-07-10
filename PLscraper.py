import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re

BASE_URL = 'https://moorepolska.pl/artykuly/?jsf=jet-engine&tax=category:31&pagenum='
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'PLarticles.csv')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US,en;q=0.8',
    'Connection': 'keep-alive',
}

POLISH_MONTHS = {
    'stycznia': '01', 'lutego': '02', 'marca': '03', 'kwietnia': '04',
    'maja': '05', 'czerwca': '06', 'lipca': '07', 'sierpnia': '08',
    'września': '09', 'października': '10', 'listopada': '11', 'grudnia': '12'
}

SOURCE_NAME = 'Moore Polska'

session = requests.Session()
session.headers.update(HEADERS)

def scrape_listing(page):
    url = f"{BASE_URL}{page}"
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    articles = []
    for div in soup.select('div.jet-listing-grid__item'):
        a = div.find('a', href=True)
        if a:
            articles.append(a['href'])
    return articles

def parse_polish_date(text):
    # Example: "16 stycznia 2025"
    match = re.search(r'(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})', text, re.IGNORECASE)
    if match:
        day, month_pl, year = match.groups()
        month = POLISH_MONTHS.get(month_pl.lower(), '01')
        return f"{year}-{month}-{day.zfill(2)}"
    return ''

def scrape_article(url):
    resp = session.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Title
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else ''
    # Date: look for a date string near the top
    post_date = ''
    for tag in soup.find_all(['time', 'span', 'div']):
        if tag.string and re.search(r'\d{1,2}\s+[a-ząćęłńóśźż]+\s+\d{4}', tag.string, re.IGNORECASE):
            post_date = parse_polish_date(tag.string)
            break
    if not post_date:
        # Fallback: search in the whole text
        text = soup.get_text()
        post_date = parse_polish_date(text)
    # Content: main article content
    content = ''
    main = soup.find('main') or soup
    # Try to find the main content by heading
    content_blocks = []
    found_title = False
    for tag in main.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
        if tag.name == 'h1' and title in tag.get_text():
            found_title = True
            continue
        if found_title:
            # Stop at "Może Cię zainteresować" or similar
            if tag.get_text(strip=True).startswith('Może Cię zainteresować'):
                break
            content_blocks.append(tag.get_text(strip=True))
    content = '\n\n'.join([t for t in content_blocks if t])
    return title, content, post_date

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
    page = 1
    while True:
        urls = scrape_listing(page)
        if not urls:
            break
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
                        'url': url,
                        'source': SOURCE_NAME
                    })
            except Exception as e:
                print(f"Error scraping {url}: {e}")
            time.sleep(1)
        page += 1

    if new_records:
        df_new = pd.DataFrame(new_records)
        updated_df = pd.concat([existing_df, df_new], ignore_index=True)
        updated_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Added {len(new_records)} new articles. Total now {len(updated_df)}.")
    else:
        print("No new articles found.")

if __name__ == '__main__':
    main()
