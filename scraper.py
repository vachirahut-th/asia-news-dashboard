import feedparser
import json
import os
import urllib.request
from datetime import datetime
from dateutil import parser as date_parser

# แหล่งข้อมูล: ผสมผสานระหว่างหน่วยงานเศรษฐกิจระดับทางการ (Central Banks/Stats) 
# และสำนักข่าวเทคโนโลยี/เศรษฐกิจระดับภูมิภาค
FEEDS = [
    # --- หน่วยงานทางการ / สถิติและนโยบายเศรษฐกิจ (Official Economy & Stats) ---
    {
        "source": "Bank of Japan (BOJ)",
        "category": "Official Stats/Policy",
        "region": "East Asia",
        "url": "https://www.boj.or.jp/en/rss/whatsnew.xml"
    },
    {
        "source": "Ministry of Finance (Japan)",
        "category": "Official Stats/Policy",
        "region": "East Asia",
        "url": "https://www.mof.go.jp/english/press_release.xml"
    },
    {
        "source": "Asian Development Bank (ADB)",
        "category": "Official Stats/Policy",
        "region": "Asia-Pacific",
        "url": "https://www.adb.org/rss/news.xml"
    },
    {
        "source": "Bank of Thailand (BOT)",
        "category": "Official Stats/Policy",
        "region": "Southeast Asia",
        "url": "https://www.bot.or.th/en/news-and-media/news.rss"
    },

    # --- สื่อเศรษฐกิจและการเงินชั้นนำ (Macro & Regional Economy) ---
    {
        "source": "SCMP - Economy",
        "category": "Economy",
        "region": "China/East Asia",
        "url": "https://www.scmp.com/rss/92/feed"
    },
    {
        "source": "The Straits Times (Business)",
        "category": "Economy",
        "region": "Southeast Asia",
        "url": "https://www.straitstimes.com/news/business/rss.xml"
    },
    {
        "source": "CNA (Business & Economy)",
        "category": "Economy",
        "region": "Asia-Pacific",
        "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936"
    },
    {
        "source": "Nikkei Asia",
        "category": "Economy",
        "region": "East Asia",
        "url": "https://asia.nikkei.com/rss/feed/nar"
    },

    # --- สื่อเทคโนโลยีและนวัตกรรม (Technology & Innovation) ---
    {
        "source": "e27 (Tech & Startups)",
        "category": "Technology",
        "region": "Southeast Asia",
        "url": "https://e27.co/feed/"
    },
    {
        "source": "Digitimes (Semiconductor/Tech)",
        "category": "Technology",
        "region": "East Asia",
        "url": "https://www.digitimes.com/rss/daily.xml"
    },
    {
        "source": "KrASIA (Tech & Digital Economy)",
        "category": "Technology",
        "region": "Asia-Pacific",
        "url": "https://kr-asia.com/feed"
    }
]

DATA_FILE = "data/news.json"

def fetch_feed_data(url):
    """ส่ง Request พร้อม Custom User-Agent ป้องกันไม่ให้สำนักข่าวบล็อก"""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

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
        print(f"Fetching: {feed_info['source']}...")
        xml_content = fetch_feed_data(feed_info["url"])
        if not xml_content:
            continue

        parsed = feedparser.parse(xml_content)
        
        # จำกัดไม่เกิน 8 ข่าวต่อสำนักข่าว เพื่อเฉลี่ยสัดส่วนไม่ให้สำนักข่าวใดครอบงำแดชบอร์ด
        count = 0
        for entry in parsed.entries:
            if count >= 8:
                break

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
            count += 1

    # รวมข่าวเดิมและใหม่ แล้วเรียงตามวันที่ล่าสุด
    all_news = new_entries + existing_news
    all_news.sort(key=lambda x: x["published_at"], reverse=True)
    all_news = all_news[:600]

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Fetch completed! Added {len(new_entries)} articles. Total in DB: {len(all_news)}")

if __name__ == "__main__":
    main()
