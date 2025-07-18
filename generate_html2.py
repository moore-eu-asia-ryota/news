import csv
from datetime import datetime
from transformers import pipeline

# Load summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

header = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>News Articles</title>
  <style>
    body { background: #f0f2f5; margin: 0; padding: 20px; font-family: Arial, sans-serif; padding-top: 140px; }
    .container { max-width: 840px; margin: auto; }
    .controls { position: fixed; top: 60px; left: 50%; transform: translateX(-50%); z-index: 1000; width: 840px; display: flex; gap: 10px; background: #fff; padding: 12px 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex-wrap: wrap; }
    .controls input, .controls select { flex: 1; min-width: 150px; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9em; }
    .controls button#sortBtn { padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.9em; min-width: 60px; }
    #backToTop { position: fixed; bottom: 40px; right: 40px; width: 50px; height: 50px; background: #1ea7fd; color: #fff; border: none; border-radius: 50%; cursor: pointer; font-size: 24px; display: none; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.2); z-index: 1000; }
    .card { background: #fff; border-radius: 8px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); position: relative; }
    .card h2 { margin: 0 0 8px; font-size: 1.3em; color: #034d66; }
    .card .date { color: #999; font-size: 0.9em; margin-bottom: 10px; }
    .card hr { border: 0; border-top: 2px solid #034d66; margin: 12px 0; width: 100%; }
    .card .summary { line-height: 1.6; color: #333; margin-bottom: 20px; }
    .card .full-content { display: none; line-height: 1.6; color: #333; margin-bottom: 20px; }
    .card .source { font-size: 0.9em; font-weight: bold; color: #034d66; }
    .card .btn { display: inline-block; background: #1ea7fd; color: #fff; padding: 10px 20px; border: none; border-radius: 4px; text-decoration: none; cursor: pointer; position: absolute; right: 30px; bottom: 30px; }
  </style>
  <script type="text/javascript">
    var sortAsc = false;
    function parseDate(str) { var p = str.trim().split('.'); return new Date(p[2], p[1]-1, p[0]).getTime(); }
    function sortCards(asc) { var parent = document.querySelector('.container'); var cards  = Array.from(document.querySelectorAll('.card')); cards.sort(function(a,b){ var da = parseDate(a.querySelector('.date').innerText); var db = parseDate(b.querySelector('.date').innerText); return asc ? da - db : db - da; }); cards.forEach(function(c){ parent.appendChild(c); }); }
    function toggleSort(){ sortAsc = !sortAsc; document.getElementById('sortBtn').innerText = sortAsc ? '▲' : '▼'; sortCards(sortAsc); }
    function toggleFullContent(idx, btn) {
      var full = document.getElementById('full' + idx);
      var preview = document.getElementById('summary' + idx);
      if (full.style.display === 'block') {
        full.style.display = 'none';
        preview.style.display = 'block';
        btn.innerText = 'Read full article';
      } else {
        full.style.display = 'block';
        preview.style.display = 'none';
        btn.innerText = 'Hide full article';
      }
    }
    function filterArticles() { var text  = document.getElementById('searchInput').value.toLowerCase(); var year  = document.getElementById('yearFilter').value; var month = document.getElementById('monthFilter').value; var src   = document.getElementById('sourceFilter').value; document.querySelectorAll('.card').forEach(function(card){ var t   = card.querySelector('h2').innerText.toLowerCase(); var sum = card.querySelector('.summary').innerText.toLowerCase(); var full = card.querySelector('.full-content').innerText.toLowerCase(); var dt  = card.querySelector('.date').innerText.trim().split('.'); var y   = dt[2], m = dt[1]; var so  = card.querySelector('.source a').innerText; var ok = (t + ' ' + sum + ' ' + full).includes(text) && (!year   || y   === year) && (!month  || m   === month) && (!src    || so  === src); card.style.display = ok ? '' : 'none'; }); }
    function populateFilters() { var years = new Set(), months = new Set(), sources = new Set(); document.querySelectorAll('.card').forEach(function(c){ var dt = c.querySelector('.date').innerText.trim().split('.'); years.add(dt[2]); months.add(dt[1]); sources.add(c.querySelector('.source a').innerText); }); Array.from(years).sort().forEach(y => document.getElementById('yearFilter').add(new Option(y, y))); Array.from(months).sort().forEach(m => document.getElementById('monthFilter').add(new Option(m, m))); Array.from(sources).sort().forEach(s => document.getElementById('sourceFilter').add(new Option(s, s))); }
    function handleScroll() { var btn = document.getElementById('backToTop'); btn.style.display = window.pageYOffset > 300 ? 'flex' : 'none'; }
    window.onload = function(){ populateFilters(); sortCards(sortAsc); window.addEventListener('scroll', handleScroll); document.getElementById('backToTop').addEventListener('click', function(){ window.scrollTo({ top: 0, behavior: 'smooth' }); }); };
  </script>
  <script type="text/javascript">
    function googleTranslateElementInit() {
      new google.translate.TranslateElement({
        pageLanguage: 'auto',
        includedLanguages: 'en,ko,ja,zh,fr,de,es,ru',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE
      }, 'google_translate_element');
    }
  </script>
  <script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
</head>
<body>
  <div id="google_translate_element" style="position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:2000;"></div>
  <button id="backToTop" title="Back to top">↑</button>
  <div class="container">
    <div class="controls">
      <input id="searchInput" type="text" placeholder="Search articles..." onkeyup="filterArticles()" />
      <select id="yearFilter" onchange="filterArticles()"><option value="">All years</option></select>
      <select id="monthFilter" onchange="filterArticles()"><option value="">All months</option></select>
      <select id="sourceFilter" onchange="filterArticles()"><option value="">All sources</option></select>
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

def summarize_text(text, max_words=200):
    if not text or len(text.strip()) < 50:
        return " ".join(text.split()[:max_words])
    try:
        summary = summarizer(text, max_length=200, min_length=100, do_sample=False)[0]['summary_text']
        words = summary.split()
        return " ".join(words[:max_words])
    except Exception:
        return " ".join(text.split()[:max_words])

def make_card(title, summary, post_date, url, source, idx):
    post_date_fmt = format_date(post_date)
    preview = summary[:200]
    return f'''
    <div class="card">
      <h2>{title}</h2>
      <p class="date">{post_date_fmt}</p>
      <hr/>
      <p class="summary" id="summary{idx}">{preview}</p>
      <p class="full-content" id="full{idx}" style="display:none;">{summary}</p>
      <p class="source">
        Source: <a href="{url}" target="_blank">{source}</a>
      </p>
      <button class="btn"
        onclick="toggleFullContent({idx}, this)">
        Read full article
      </button>
    </div>
    '''

def main():
    with open('output/articles.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = []
        for idx, row in enumerate(reader):
            summary = summarize_text(row['content'], max_words=200)
            cards.append(make_card(
                row['title'],
                summary,
                row['post_date'],
                row['url'],
                row['source'],
                idx
            ))
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(cards))
        f.write(footer)

if __name__ == "__main__":
    main()
