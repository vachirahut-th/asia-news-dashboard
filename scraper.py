import json
import os
from datetime import datetime
from urllib.parse import urljoin
import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

DATA_FILE = "data/news.json"
SOURCES_FILE = "sources.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def load_sources():
    if os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def parse_rss_feed(feed_info, seen_links):
    """ดึงข้อมูลจาก RSS / XML"""
    entries = []
    try:
        res = requests.get(feed_info["url"], headers=HEADERS, timeout=15)
        parsed = feedparser.parse(res.content)
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

            entries.append({
                "title": title,
                "link": link,
                "source": feed_info["source"],
                "category": feed_info["category"],
                "region": feed_info["region"],
                "published_at": date_str
            })
            seen_links.add(link)
            count += 1
    except Exception as e:
        print(f"Error parsing RSS {feed_info['source']}: {e}")
    return entries

def parse_html_page(feed_info, seen_links):
    """ดึงข้อมูลจากหน้าเว็บ HTML ทั่วไปที่ไม่ใช่ RSS โดยค้นหาหัวข้อและลิงก์อัตโนมัติ"""
    entries = []
    try:
        res = requests.get(feed_info["url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # ค้นหา article หรือกล่องข่าวทั่วไป
        candidates = soup.find_all(["article", "li", "div"], limit=50)
        count = 0
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        for item in candidates:
            if count >= 8:
                break
            
            # หาแท็ก <a> ที่มีข้อความยาวพอจะเป็นหัวข้อข่าว (เกิน 25 ตัวอักษร)
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            # ข้ามเมนูหรือข้อความสั้นๆ
            if len(title) < 25:
                # ลองดูแท็ก h1, h2, h3 ภายในกล่อง
                heading = item.find(["h1", "h2", "h3", "h4"])
                if heading:
                    title = heading.get_text(strip=True)

            if len(title) < 25:
                continue

            link = urljoin(feed_info["url"], link_tag["href"])
            if link in seen_links:
                continue

            entries.append({
                "title": title,
                "link": link,
                "source": feed_info["source"],
                "category": feed_info["category"],
                "region": feed_info["region"],
                "published_at": now_str
            })
            seen_links.add(link)
            count += 1
    except Exception as e:
        print(f"Error parsing HTML {feed_info['source']}: {e}")
    return entries

def main():
    sources = load_sources()
    existing_news = load_existing_data()
    seen_links = {item["link"] for item in existing_news}
    new_entries = []

    for src in sources:
        print(f"Fetching: {src['source']} ({src.get('type', 'rss').upper()})...")
        if src.get("type") == "html":
            items = parse_html_page(src, seen_links)
        else:
            items = parse_rss_feed(src, seen_links)
        new_entries.extend(items)

    all_news = new_entries + existing_news
    all_news.sort(key=lambda x: x["published_at"], reverse=True)
    all_news = all_news[:600]

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)

    print(f"Fetch completed! Added {len(new_entries)} articles. Total in DB: {len(all_news)}")

if __name__ == "__main__":
    main()
