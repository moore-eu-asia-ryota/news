import csv
from datetime import datetime

header = """<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\" />
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
  <script type=\"text/javascript\">\n    var sortAsc = false;\n    function parseDate(str) { var p = str.trim().split('.'); return new Date(p[2], p[1]-1, p[0]).getTime(); }\n    function sortCards(asc) { var parent = document.querySelector('.container'); var cards  = Array.from(document.querySelectorAll('.card')); cards.sort(function(a,b){ var da = parseDate(a.querySelector('.date').innerText); var db = parseDate(b.querySelector('.date').innerText); return asc ? da - db : db - da; }); cards.forEach(function(c){ parent.appendChild(c); }); }\n    function toggleSort(){ sortAsc = !sortAsc; document.getElementById('sortBtn').innerText = sortAsc ? '▲' : '▼'; sortCards(sortAsc); }\n    function toggleFullContent(idx, btn) {\n      var full = document.getElementById('full' + idx);\n      var preview = document.getElementById('summary' + idx);\n      if (full.style.display === 'block') {\n        full.style.display = 'none';\n        preview.style.display = 'block';\n        btn.innerText = 'Read full article';\n      } else {\n        full.style.display = 'block';\n        preview.style.display = 'none';\n        btn.innerText = 'Hide full article';\n      }\n    }\n    function filterArticles() { var text  = document.getElementById('searchInput').value.toLowerCase(); var year  = document.getElementById('yearFilter').value; var month = document.getElementById('monthFilter').value; var src   = document.getElementById('sourceFilter').value; document.querySelectorAll('.card').forEach(function(card){ var t   = card.querySelector('h2').innerText.toLowerCase(); var sum = card.querySelector('.summary').innerText.toLowerCase(); var full = card.querySelector('.full-content').innerText.toLowerCase(); var dt  = card.querySelector('.date').innerText.trim().split('.'); var y   = dt[2], m = dt[1]; var so  = card.querySelector('.source a').innerText; var ok = (t + ' ' + sum + ' ' + full).includes(text) && (!year   || y   === year) && (!month  || m   === month) && (!src    || so  === src); card.style.display = ok ? '' : 'none'; }); }\n    function populateFilters() { var years = new Set(), months = new Set(), sources = new Set(); document.querySelectorAll('.card').forEach(function(c){ var dt = c.querySelector('.date').innerText.trim().split('.'); years.add(dt[2]); months.add(dt[1]); sources.add(c.querySelector('.source a').innerText); }); Array.from(years).sort().forEach(y => document.getElementById('yearFilter').add(new Option(y, y))); Array.from(months).sort().forEach(m => document.getElementById('monthFilter').add(new Option(m, m))); Array.from(sources).sort().forEach(s => document.getElementById('sourceFilter').add(new Option(s, s))); }\n    function handleScroll() { var btn = document.getElementById('backToTop'); btn.style.display = window.pageYOffset > 300 ? 'flex' : 'none'; }\n    window.onload = function(){ populateFilters(); sortCards(sortAsc); window.addEventListener('scroll', handleScroll); document.getElementById('backToTop').addEventListener('click', function(){ window.scrollTo({ top: 0, behavior: 'smooth' }); }); };\n  </script>
</head>
<body>
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

def add_line_breaks(text):
    # Replace double newlines or single newlines with <br> for HTML
    if not text:
        return ''
    # Replace two or more newlines with <br><br>, single newline with <br>
    import re
    text = re.sub(r'\r?\n\r?\n+', '<br><br>', text)
    text = re.sub(r'\r?\n', '<br>', text)
    return text

def make_card(title, content, post_date, url, source, idx):
    post_date_fmt = format_date(post_date)
    preview = content[:200]
    content_html = add_line_breaks(content)
    preview_html = add_line_breaks(preview)
    return f'''
    <div class="card">
      <h2>{title}</h2>
      <p class="date">{post_date_fmt}</p>
      <hr/>
      <p class="summary" id="summary{idx}">{preview_html}</p>
      <p class="full-content" id="full{idx}" style="display:none;">{content_html}</p>
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
    with open('output/final.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cards = []
        for idx, row in enumerate(reader):
            title = row.get('title_eng', '')
            content = row.get('content_eng', '')
            cards.append(make_card(
                title,
                content,
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
