import csv
from datetime import datetime

header = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>News Articles</title>
  <style>
    /* ...existing CSS from your template... */
  </style>
  <script>
    // ...existing JS from your template...
  </script>
</head>
<body>
  <!-- Back to top button -->
  <button id="backToTop" title="Back to top">↑</button>
  <div class="container">
    <!-- Fixed Search & Filters & Sort -->
    <div class="controls">
      <input id="searchInput"
             type="text"
             placeholder="Search articles..."
             onkeyup="filterArticles()" />
      <select id="yearFilter" onchange="filterArticles()">
        <option value="">All years</option>
      </select>
      <select id="monthFilter" onchange="filterArticles()">
        <option value="">All months</option>
      </select>
      <select id="sourceFilter" onchange="filterArticles()">
        <option value="">All sources</option>
      </select>
      <button id="sortBtn" onclick="toggleSort()">▼</button>
    </div>
"""

footer = """
  </div>
</body>
</html>
"""

def format_date(date_str):
    # Try to parse date in ISO or other formats, output as DD.MM.YYYY
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        # fallback: just return as is
        return date_str

def make_card(title, content, post_date, url, source, idx):
    post_date_fmt = format_date(post_date)
    return f'''
    <div class="card">
      <h2>{title}</h2>
      <p class="date">{post_date_fmt}</p>
      <hr/>
      <p class="summary" id="summary{idx}">{content}</p>
      <p class="source">
        Source: <a href="{url}" target="_blank">{source}</a>
      </p>
      <button class="btn"
        onclick="toggleSummary('summary{idx}', this)">
        Read full article
      </button>
    </div>
    '''

def main():
    with open('output/articles.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = []
        for idx, row in enumerate(reader):
            cards.append(make_card(
                row['title'],
                row['content'],
                row['post_date'],
                row['url'],
                row['source'],
                idx
            ))
    with open('output/articles.html', 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(cards))
        f.write(footer)

if __name__ == "__main__":
    main()
