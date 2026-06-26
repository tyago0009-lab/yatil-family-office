"""
Busca notícias imobiliárias dos principais portais brasileiros.
Executado pelo GitHub Action a cada 6h.
"""
import json, re, datetime, sys

try:
    import feedparser
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "feedparser", "-q"])
    import feedparser

FEEDS = [
    ("VivaReal Blog",      "https://www.vivareal.com.br/blog/feed/"),
    ("ZAP Imóveis Blog",   "https://www.zapimoveis.com.br/blog/feed/"),
    ("CBIC",               "https://cbic.org.br/feed/"),
    ("ABRAINC",            "https://www.abrainc.org.br/feed/"),
    ("Secovi-SP",          "https://www.secovi.com.br/noticias/rss"),
    ("FipeZAP",            "https://www.fipezap.zapimoveis.com.br/feed/"),
    ("Google News",        "https://news.google.com/rss/search?q=mercado+imobili%C3%A1rio+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"),
    ("InfoMoney Imóveis",  "https://www.infomoney.com.br/rss/"),
    ("G1 Economia",        "https://g1.globo.com/rss/g1/economia/"),
    ("Valor Econômico",    "https://valor.globo.com/rss/imoveis/"),
    ("Exame",              "https://exame.com/rss.xml"),
]

def strip_html(text):
    text = re.sub(r'<[^>]+>', ' ', text or '')
    text = re.sub(r'&[a-z#0-9]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

news = []
for source, url in FEEDS:
    try:
        d = feedparser.parse(url)
        count = 0
        for e in d.entries[:6]:
            title = strip_html(e.get("title", "")).strip()
            if not title:
                continue
            pub = e.get("published_parsed") or e.get("updated_parsed")
            try:
                date_str = datetime.datetime(*pub[:6]).isoformat() if pub else datetime.datetime.now().isoformat()
            except Exception:
                date_str = datetime.datetime.now().isoformat()
            summary = strip_html(e.get("summary", "") or e.get("description", ""))[:300]
            link = e.get("link", "#")
            # Filter for real estate relevance (for generic feeds)
            keywords = ["imóvel","imobiliário","construtora","incorporadora","apartamento","aluguel",
                       "financiamento","habitação","construção","lançamento","FGTS","Selic","juros"]
            is_relevant = any(k.lower() in title.lower() or k.lower() in summary.lower() for k in keywords)
            if source in ("Google News", "VivaReal Blog", "ZAP Imóveis Blog", "CBIC", "ABRAINC",
                          "Secovi-SP", "FipeZAP", "Valor Econômico") or is_relevant:
                news.append({
                    "source": source,
                    "title": title,
                    "link": link,
                    "date": date_str,
                    "summary": summary
                })
                count += 1
        print(f"✓ {source}: {count} notícias")
    except Exception as ex:
        print(f"✗ {source}: {ex}")

# Sort by date, most recent first
news.sort(key=lambda x: x.get("date", ""), reverse=True)

# Deduplicate by title similarity
seen = set()
unique = []
for item in news:
    key = item["title"][:60].lower()
    if key not in seen:
        seen.add(key)
        unique.append(item)

unique = unique[:30]  # up to 30 cards

output = {
    "updated": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    "count": len(unique),
    "items": unique
}

with open("news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {len(unique)} notícias salvas em news.json")
