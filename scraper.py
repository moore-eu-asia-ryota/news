import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

BASE_URL = 'https://www.moore-czech.cz/tiskove-zpravy'
OUTPUT_DIR = 'output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'articles.csv')

def scrape_listing(page):
    url = f'{BASE_URL}?page={page}'
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    entries = soup.select('article.press-release')
    results = []
    for entry in entries:
        link_tag = entry.find('a', href=True)
        link = link_tag['href']
        full_url = requests.compat.urljoin(BASE_URL, link)
        date_tag = entry.find('time')
        post_date = date_tag['datetime'] if date_tag else None
        results.append({'url': full_url, 'post_date': post_date})
    return results

def scrape_article(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.find('h1').get_text(strip=True)
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
        print(f'Page {page} scraped, {len(listings)} articles.')
        page += 1

    df = pd.DataFrame(articles)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f'Saved {len(df)} articles to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
