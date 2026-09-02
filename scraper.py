import feedparser
import json
import os
from datetime import datetime
from dateutil import parser as date_parser

FEEDS = [
    {
        "source": "Tech in Asia",
        "category": "Technology",
        "region": "Southeast Asia",
        "url": "https://www.techinasia.com/feed"
    },
    {
        "source": "Nikkei Asia - Tech",
        "category": "Technology",
        "region": "East Asia",
        "url": "https://asia.nikkei.com/rss/feed/nar"
    },
    {
        "source": "e27",
        "category": "Technology",
        "region": "Southeast Asia",
        "url": "https://e27.co/feed/"
    },
    {
        "source": "SCMP - Economy",
        "category": "Economy",
        "region": "China/East Asia",
        "url": "https://www.scmp.com/rss/92/feed"
    }
]

DATA_FILE = "data/news.json"

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def main():
    existing_news = load_existing_data()
    seen_links = {item["link"] for item in existing_news}
    new_entries = []

    for feed_info in FEEDS:
        print(f"Fetching: {feed_info['source']}")
        parsed = feedparser.parse(feed_info["url"])
        
        for entry in parsed.entries[:15]:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()
            
            if not link or not title or link in seen_links:
                continue

            published = entry.get("published") or entry.get("updated")
            try:
                dt = date_parser.parse(published) if published else datetime.utcnow()
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

            new_entries.append({
                "title": title,
                "link": link,
                "source": feed_info["source"],
                "category": feed_info["category"],
                "region": feed_info["region"],
                "published_at": date_str
            })
            seen_links.add(link)

    all_news = new_entries + existing_news
    all_news.sort(key=lambda x: x["published_at"], reverse=True)
    all_news = all_news[:500]

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Updated successfully! Total articles: {len(all_news)}")

if __name__ == "__main__":
    main()
