import csv
from datetime import datetime
from deep_translator import GoogleTranslator

header = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>News Articles</title>
  <style>
    body {
      background: #f0f2f5;
      margin: 0;
      padding: 20px;
      font-family: Arial, sans-serif;
      padding-top: 100px;
    }
    .container {
      max-width: 840px;
      margin: auto;
    }
    .controls {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 1000;
      width: 840px;
      display: flex;
      gap: 10px;
      background: #fff;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      flex-wrap: wrap;
    }
    .controls input,
    .controls select {
      flex: 1;
      min-width: 150px;
      padding: 8px 12px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 0.9em;
    }
    .controls button#sortBtn {
      padding: 8px 12px;
      border: 1px solid #ccc;
      border-radius: 4px;
      background: #fff;
      cursor: pointer;
      font-size: 0.9em;
      min-width: 60px;
    }
    #backToTop {
      position: fixed;
      bottom: 40px;
      right: 40px;
      width: 50px;
      height: 50px;
      background: #1ea7fd;
      color: #fff;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      font-size: 24px;
      display: none;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      z-index: 1000;
    }
    .card {
      background: #fff;
      border-radius: 8px;
      padding: 30px;
      margin-bottom: 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      position: relative;
    }
    .card h2 {
      margin: 0 0 8px;
      font-size: 1.3em;
      color: #034d66;
    }
    .card .date {
      color: #999;
      font-size: 0.9em;
      margin-bottom: 10px;
    }
    .card hr {
      border: 0;
      border-top: 2px solid #034d66;
      margin: 12px 0;
      width: 100%;
    }
    .card .summary {
      display: none;
      line-height: 1.6;
      color: #333;
      margin-bottom: 20px;
    }
    .card .summary.translated {
      display: none;
      color: #1ea7fd;
      margin-bottom: 20px;
    }
    .card .source {
      font-size: 0.9em;
      font-weight: bold;
      color: #034d66;
    }
    .card .btn {
      display: inline-block;
      background: #1ea7fd;
      color: #fff;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      text-decoration: none;
      cursor: pointer;
      position: absolute;
      right: 30px;
      bottom: 30px;
    }
    .card .btn.trans {
      right: 160px;
      background: #034d66;
    }
  </style>
  <script>
    var sortAsc = false; // false = descending (newest first)

    function parseDate(str) {
      var p = str.trim().split('.');
      return new Date(p[2], p[1]-1, p[0]).getTime();
    }

    function sortCards(asc) {
      var parent = document.querySelector('.container');
      var cards  = Array.from(document.querySelectorAll('.card'));
      cards.sort(function(a,b){
        var da = parseDate(a.querySelector('.date').innerText);
        var db = parseDate(b.querySelector('.date').innerText);
        return asc ? da - db : db - da;
      });
      cards.forEach(function(c){ parent.appendChild(c); });
    }

    function toggleSort(){
      sortAsc = !sortAsc;
      document.getElementById('sortBtn').innerText = sortAsc ? '▲' : '▼';
      sortCards(sortAsc);
    }

    function toggleSummary(id, btn) {
      var s = document.getElementById(id);
      if (s.style.display === 'block') {
        s.style.display = 'none';
        btn.innerText = 'Read full article';
      } else {
        s.style.display = 'block';
        btn.innerText = 'Hide summary';
      }
    }

    function toggleTranslated(id, btn) {
      var s = document.getElementById(id);
      if (s.style.display === 'block') {
        s.style.display = 'none';
        btn.innerText = 'Show English';
      } else {
        s.style.display = 'block';
        btn.innerText = 'Hide English';
      }
    }

    function filterArticles() {
      var text  = document.getElementById('searchInput').value.toLowerCase();
      var year  = document.getElementById('yearFilter').value;
      var month = document.getElementById('monthFilter').value;
      var src   = document.getElementById('sourceFilter').value;
      document.querySelectorAll('.card').forEach(function(card){
        var t   = card.querySelector('h2').innerText.toLowerCase();
        var sum = card.querySelector('.summary').innerText.toLowerCase();
        var sum_en = card.querySelector('.summary.translated').innerText.toLowerCase();
        var dt  = card.querySelector('.date').innerText.trim().split('.');
        var y   = dt[2], m = dt[1];
        var so  = card.querySelector('.source a').innerText;
        var ok = (t + ' ' + sum + ' ' + sum_en).includes(text)
              && (!year   || y   === year)
              && (!month  || m   === month)
              && (!src    || so  === src);
        card.style.display = ok ? '' : 'none';
      });
    }

    function populateFilters() {
      var years = new Set(), months = new Set(), sources = new Set();
      document.querySelectorAll('.card').forEach(function(c){
        var dt = c.querySelector('.date').innerText.trim().split('.');
        years.add(dt[2]); months.add(dt[1]);
        sources.add(c.querySelector('.source a').innerText);
      });
      Array.from(years).sort().forEach(y =>
        document.getElementById('yearFilter').add(new Option(y, y))
      );
      Array.from(months).sort().forEach(m =>
        document.getElementById('monthFilter').add(new Option(m, m))
      );
      Array.from(sources).sort().forEach(s =>
        document.getElementById('sourceFilter').add(new Option(s, s))
      );
    }

    function handleScroll() {
      var btn = document.getElementById('backToTop');
      btn.style.display = window.pageYOffset > 300 ? 'flex' : 'none';
    }

    window.onload = function(){
      populateFilters();
      sortCards(sortAsc);
      window.addEventListener('scroll', handleScroll);
      document.getElementById('backToTop')
              .addEventListener('click', function(){
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    };
  </script>
</head>
<body>
  <button id="backToTop" title="Back to top">↑</button>
  <div class="container">
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
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return date_str

def make_card(title, title_en, content, content_en, post_date, url, source, idx):
    post_date_fmt = format_date(post_date)
    return f'''
    <div class="card">
      <h2>{title}</h2>
      <h2 style="color:#1ea7fd;font-size:1em;">{title_en}</h2>
      <p class="date">{post_date_fmt}</p>
      <hr/>
      <p class="summary" id="summary{idx}">{content}</p>
      <p class="summary translated" id="summary_en{idx}">{content_en}</p>
      <p class="source">
        Source: <a href="{url}" target="_blank">{source}</a>
      </p>
      <button class="btn"
        onclick="toggleSummary('summary{idx}', this)">
        Read full article
      </button>
      <button class="btn trans"
        onclick="toggleTranslated('summary_en{idx}', this)">
        Show English
      </button>
    </div>
    '''

def translate_text(text):
    if not text.strip():
        return ""
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return text

def main():
    with open('output/articles.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = []
        for idx, row in enumerate(reader):
            title_en = translate_text(row['title'])
            content_en = translate_text(row['content'])
            cards.append(make_card(
                row['title'],
                title_en,
                row['content'],
                content_en,
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
