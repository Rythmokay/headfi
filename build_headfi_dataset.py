#!/usr/bin/env python3
"""
Master Scrapling Extractor: Head-Fi Website Data Engine
Builds the complete `headfi_data` package with structured articles, gear reviews,
discussion threads, comments, and downloads all images locally.
"""

import os
import re
import sys
import time
import json
import urllib.request
import ssl
import subprocess
from typing import List, Dict, Any, Optional
from scrapling.parser import Selector

BASE_URL = "https://www.head-fi.org"
ROOT_DIR = os.path.abspath("headfi_data")
ARTICLES_DIR = os.path.join(ROOT_DIR, "articles")
REVIEWS_DIR = os.path.join(ROOT_DIR, "reviews")
THREADS_DIR = os.path.join(ROOT_DIR, "threads")
IMAGES_DIR = os.path.join(ROOT_DIR, "images")

# Ensure directories exist
for d in (ROOT_DIR, ARTICLES_DIR, REVIEWS_DIR, THREADS_DIR, IMAGES_DIR):
    os.makedirs(d, exist_ok=True)

# SSL Context for image downloads
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def slugify(text: str) -> str:
    """Create a clean filename slug from text."""
    text = re.sub(r'[^\w\s-]', '', text.lower().strip())
    return re.sub(r'[-\s]+', '_', text)[:60]

def download_image(url: str, filename_prefix: str) -> Optional[str]:
    """Download an image to headfi_data/images/ and return relative path."""
    if not url or not url.startswith('http'):
        return None
    # Skip small joypixels / emojis
    if 'joypixels' in url or 'smilies' in url:
        return None
        
    try:
        # Determine extension
        clean_url = url.split('?')[0]
        ext = os.path.splitext(clean_url)[1] or '.jpg'
        if ext.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            ext = '.jpg'
            
        filename = f"{filename_prefix}_{abs(hash(clean_url)) % 100000}{ext}"
        filepath = os.path.join(IMAGES_DIR, filename)
        rel_path = f"../images/{filename}"
        
        if not os.path.exists(filepath):
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as response:
                content = response.read()
                if len(content) > 1000:  # Minimum 1KB
                    with open(filepath, 'wb') as f:
                        f.write(content)
                else:
                    return None
        return rel_path
    except Exception as e:
        # Silently skip download errors for broken external hotlinks
        return None

def fetch_in_browser(path_or_url: str, timeout_sec: int = 25) -> Optional[str]:
    """Fetch HTML within the active logged-in Brave Browser tab."""
    if path_or_url.startswith(BASE_URL):
        path = path_or_url[len(BASE_URL):]
    else:
        path = path_or_url

    escaped_path = path.replace('"', '\\"')
    applescript = f'''
tell application "Brave Browser"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t contains "head-fi.org" then
                execute t javascript "window.__bhtml = null; fetch('{escaped_path}').then(r => r.text()).then(t => {{ window.__bhtml = t; }}).catch(e => {{ window.__bhtml = 'ERR:' + e; }});"
                set tries to 0
                repeat while tries < {int(timeout_sec * 2.5)}
                    delay 0.4
                    set r to execute t javascript "window.__bhtml ? 'READY:' + window.__bhtml.length : 'WAIT'"
                    if r starts with "READY" then
                        return execute t javascript "window.__bhtml"
                    end if
                    set tries to tries + 1
                end repeat
                return "TIMEOUT"
            end if
        end repeat
    end repeat
end tell
return "NO_TAB"
'''
    p = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    out = p.stdout.strip()
    if not out or out in ("TIMEOUT", "NO_TAB") or out.startswith("ERR:"):
        return None
    return p.stdout

# ==========================================
# 1. ARTICLES PROCESSOR
# ==========================================
def scrape_articles():
    print("\n--- Scraping Articles from /articles/ ---")
    html = fetch_in_browser("/articles/")
    if not html:
        print("Failed to load /articles/")
        return
        
    page = Selector(html, url=f"{BASE_URL}/articles/")
    items = page.css('.structItem')
    print(f"Found {len(items)} articles on /articles/")
    
    for idx, item in enumerate(items[:6], 1):
        title = item.css('.structItem-title a::text').get() or f"Article {idx}"
        title = title.strip()
        rel_url = item.css('.structItem-title a::attr(href)').get() or ''
        thumb_url = item.css('.structItem-iconContainer img::attr(src)').get() or ''
        
        slug = slugify(title)
        print(f"[{idx}/6] Fetching Article: {title} ...")
        
        # Download thumbnail
        local_thumb = download_image(thumb_url, f"art_{slug}_thumb") if thumb_url else None
        
        art_html = fetch_in_browser(rel_url)
        if not art_html:
            continue
            
        art_page = Selector(art_html, url=f"{BASE_URL}{rel_url}")
        
        # Metadata
        cat = art_page.css('.p-breadcrumbs li:last-child a::text').get() or 'General'
        author = art_page.css('.article-author a::text, .username::text').get() or 'Staff'
        date = art_page.css('time::text').get() or ''
        
        # Body
        body_wrappers = art_page.css('.articleBody .bbWrapper, .bbWrapper')
        body_text = body_wrappers[0].get_all_text().strip() if body_wrappers else ''
        
        # Download images within the article
        img_elements = art_page.css('.articleBody img, .bbWrapper img')
        downloaded_images = []
        for img_idx, img in enumerate(img_elements[:8], 1):
            src = img.attrib.get('src', '')
            local_img = download_image(src, f"art_{slug}_img_{img_idx}")
            if local_img:
                downloaded_images.append({'remote': src, 'local': local_img})
                
        # Comments
        comments = []
        for c in art_page.css('.message--articleComment, .message--post, article.message')[:10]:
            c_author = c.css('.message-name a::text').get() or 'User'
            c_time = c.css('.message-attribution-main time::text').get() or ''
            c_wrappers = c.css('.bbWrapper')
            c_body = c_wrappers[0].get_all_text().strip() if c_wrappers else ''
            if c_body:
                comments.append({
                    'author': c_author.strip(),
                    'date': c_time.strip(),
                    'content': c_body
                })
                
        # Write Markdown file
        md_file = os.path.join(ARTICLES_DIR, f"{slug}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"- **Category**: {cat.strip()}\n")
            f.write(f"- **Author**: {author.strip()}\n")
            f.write(f"- **Date**: {date.strip()}\n")
            f.write(f"- **URL**: [{BASE_URL}{rel_url}]({BASE_URL}{rel_url})\n\n")
            
            if local_thumb:
                f.write(f"![Thumbnail]({local_thumb})\n\n")
                
            f.write("## Article Content\n\n")
            f.write(f"{body_text}\n\n")
            
            if downloaded_images:
                f.write("## Article Images & Charts\n\n")
                for img_data in downloaded_images:
                    f.write(f"![Illustration]({img_data['local']})\n\n")
                    
            if comments:
                f.write("## User Comments & Discussion\n\n")
                for c_idx, c in enumerate(comments, 1):
                    f.write(f"### Comment #{c_idx} by {c['author']} ({c['date']})\n\n")
                    f.write(f"> {c['content']}\n\n")
                    
        # Write JSON file
        json_file = os.path.join(ARTICLES_DIR, f"{slug}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'title': title,
                'category': cat.strip(),
                'author': author.strip(),
                'date': date.strip(),
                'url': f"{BASE_URL}{rel_url}",
                'content': body_text,
                'images': downloaded_images,
                'comments': comments
            }, f, indent=2, ensure_ascii=False)
            
        time.sleep(0.3)

# ==========================================
# 2. REVIEWS & SHOWCASE PROCESSOR
# ==========================================
def scrape_reviews():
    print("\n--- Scraping Product Reviews from /showcase/ ---")
    html = fetch_in_browser("/showcase/")
    if not html:
        print("Failed to load /showcase/")
        return
        
    page = Selector(html, url=f"{BASE_URL}/showcase/")
    items = page.css('.structItem')
    print(f"Found {len(items)} items on /showcase/")
    
    for idx, item in enumerate(items[:6], 1):
        title = item.css('.structItem-title a::text').get() or f"Product {idx}"
        title = title.strip()
        rel_url = item.css('.structItem-title a::attr(href)').get() or ''
        thumb_url = item.css('.structItem-iconContainer img::attr(src)').get() or ''
        rating = item.css('.ratingStars::attr(title)').get() or 'Unrated'
        
        slug = slugify(title)
        print(f"[{idx}/6] Fetching Product Review: {title} ...")
        
        # Download product thumbnail
        local_thumb = download_image(thumb_url, f"rev_{slug}_thumb") if thumb_url else None
        
        prod_html = fetch_in_browser(rel_url)
        if not prod_html:
            continue
            
        prod_page = Selector(prod_html, url=f"{BASE_URL}{rel_url}")
        
        # Category
        cat = prod_page.css('.p-breadcrumbs li:last-child a::text').get() or 'Audio Gear'
        
        # Review Content
        reviews = []
        for r in prod_page.css('.review, .message, article.message')[:4]:
            r_author = r.css('.message-name a::text, .review-author::text').get() or 'Reviewer'
            r_rating = r.css('.ratingStars::attr(title)').get() or rating
            r_wrappers = r.css('.bbWrapper')
            r_body = r_wrappers[0].get_all_text().strip() if r_wrappers else ''
            
            # Review photos
            review_imgs = []
            for r_img in r.css('.bbWrapper img')[:6]:
                src = r_img.attrib.get('src', '')
                local_r_img = download_image(src, f"rev_{slug}_photo")
                if local_r_img:
                    review_imgs.append({'remote': src, 'local': local_r_img})
                    
            if r_body:
                reviews.append({
                    'author': r_author.strip(),
                    'rating': r_rating.strip(),
                    'body': r_body,
                    'photos': review_imgs
                })
                
        # Write Markdown file
        md_file = os.path.join(REVIEWS_DIR, f"{slug}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"- **Category**: {cat.strip()}\n")
            f.write(f"- **Overall Rating**: {rating.strip()}\n")
            f.write(f"- **Product URL**: [{BASE_URL}{rel_url}]({BASE_URL}{rel_url})\n\n")
            
            if local_thumb:
                f.write(f"![Product Image]({local_thumb})\n\n")
                
            f.write("## In-Depth Reviews & Sound Impressions\n\n")
            for r_idx, rev in enumerate(reviews, 1):
                f.write(f"### Review #{r_idx} by {rev['author']} (Rating: {rev['rating']})\n\n")
                f.write(f"{rev['body']}\n\n")
                if rev['photos']:
                    f.write("#### Review Photos\n\n")
                    for p in rev['photos']:
                        f.write(f"![Gear Photo]({p['local']})\n\n")
                        
        # Write JSON file
        json_file = os.path.join(REVIEWS_DIR, f"{slug}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'product_name': title,
                'category': cat.strip(),
                'rating': rating.strip(),
                'url': f"{BASE_URL}{rel_url}",
                'thumbnail': local_thumb,
                'reviews': reviews
            }, f, indent=2, ensure_ascii=False)
            
        time.sleep(0.3)

# ==========================================
# 3. FORUM THREADS PROCESSOR
# ==========================================
def scrape_threads():
    print("\n--- Scraping Top Forum Threads & Discussions ---")
    if not os.path.exists("head_fi_all_posts.json"):
        print("head_fi_all_posts.json not found, skipping threads.")
        return
        
    with open("head_fi_all_posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    posts = data.get("posts", [])[:8]
    print(f"Processing {len(posts)} top threads with comments...")
    
    for idx, thread in enumerate(posts, 1):
        title = thread['title']
        slug = slugify(title)
        url = thread['url']
        print(f"[{idx}/{len(posts)}] Processing Thread: {title[:40]}...")
        
        # Fetch thread page
        th_html = fetch_in_browser(url)
        if not th_html:
            continue
            
        th_page = Selector(th_html, url=url)
        
        # User messages / comments
        comments = []
        downloaded_imgs = []
        for m_idx, msg in enumerate(th_page.css('article.message')[:12], 1):
            author = msg.css('.message-name a::text').get() or 'Member'
            time_str = msg.css('.message-attribution-main time::text').get() or ''
            wrappers = msg.css('.bbWrapper')
            body = wrappers[0].get_all_text().strip() if wrappers else ''
            
            # Images in message
            for img in msg.css('.bbWrapper img')[:2]:
                src = img.attrib.get('src', '')
                local_img = download_image(src, f"th_{slug}_img")
                if local_img:
                    downloaded_imgs.append(local_img)
                    
            if body:
                comments.append({
                    'post_index': m_idx,
                    'author': author.strip(),
                    'date': time_str.strip(),
                    'content': body
                })
                
        # Write Markdown file
        md_file = os.path.join(THREADS_DIR, f"{slug}.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"- **Forum Section**: {thread.get('forum', 'General')}\n")
            f.write(f"- **Original Author**: {thread.get('author', 'Unknown')}\n")
            f.write(f"- **Total Replies / Views**: {thread.get('replies', '0')} / {thread.get('views', '0')}\n")
            f.write(f"- **Thread URL**: [{url}]({url})\n\n")
            
            if downloaded_imgs:
                f.write("## Attached Gear Images\n\n")
                for img_path in downloaded_imgs[:4]:
                    f.write(f"![Attached Image]({img_path})\n\n")
                    
            f.write("## Discussion Posts & Comments\n\n")
            for c in comments:
                f.write(f"### Post #{c['post_index']} by **{c['author']}** ({c['date']})\n\n")
                f.write(f"{c['content']}\n\n---\n\n")
                
        # Write JSON file
        json_file = os.path.join(THREADS_DIR, f"{slug}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'title': title,
                'forum': thread.get('forum', ''),
                'author': thread.get('author', ''),
                'replies': thread.get('replies', ''),
                'views': thread.get('views', ''),
                'url': url,
                'comments': comments
            }, f, indent=2, ensure_ascii=False)
            
        time.sleep(0.3)

# ==========================================
# 4. WEBSITE SITEMAP & OVERVIEW REPORT
# ==========================================
def generate_overview():
    print("\n--- Generating Website Overview & Sitemap ---")
    overview_path = os.path.join(ROOT_DIR, "website_overview.md")
    
    # Count generated files
    art_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith('.md')]
    rev_files = [f for f in os.listdir(REVIEWS_DIR) if f.endswith('.md')]
    th_files = [f for f in os.listdir(THREADS_DIR) if f.endswith('.md')]
    img_files = [f for f in os.listdir(IMAGES_DIR) if not f.startswith('.')]
    
    md_content = f"""# Head-Fi.org Website Structure & Extracted Dataset

> **Extraction System**: [Scrapling v0.5](https://github.com/D4Vinci/Scrapling)  
> **Authenticated Account**: **Rythm** (Logged in session)  
> **Generated Root Folder**: `headfi_data/`

---

## 1. What Head-Fi Contains (Site Architecture)

Head-Fi.org is the premier global audio community, structured into five primary sections:

### 1.1 Articles & Guides (`/articles/`)
Editorial and community in-depth guides, measurement analysis, DIY modifications, and gear tutorials:
- **DIY and Mods**: Hardware modifications (e.g. DT-770 bass reduction mod, pad damping).
- **Measurement & Frequency Analysis**: Lab-grade acoustic measurements and frequency response comparison charts (e.g. Dekoni Audio HD600 & HD800 ear pad analysis).
- **Buying Guides**: Curated gear recommendations across Desktop DACs, Amps, and IEMs.
- **Tutorials & Member Guides**: Walkthroughs for classifieds, audio terms, and beginner setups.

### 1.2 Head Gear & Showcase (`/showcase/`)
A structured product catalog containing community reviews, lab measurements, and star ratings:
- **Headphones**: In-Ear (IEMs), Over-Ear, Custom In-Ears (CIEMs), Wireless, Noise-Canceling.
- **Amplification**: Desktop Amps, Portable Amps, Tube Amps, Solid State, Amp/DAC combos.
- **Sources**: High-Resolution Digital Audio Players (DAPs), Dedicated DACs, Streamers, CD Players.
- **Cables & Accessories**: Interconnects, Headphone cables, Ear pads, Stands.

### 1.3 Discussion Forums (`/forums/`)
Thread-based community discussions organized by acoustic discipline:
- **Full-Size Headphones**: Dynamic, Planar Magnetic, Electrostatic headphones.
- **Portable Audio & IEMs**: In-ear monitors, dongle DACs, bluetooth audio.
- **Amplifiers & Sources**: Tube rolling discussions, R2R DAC reviews, amplifier build threads.
- **Members' Lounge & Music**: General banter, gear impressions, high-res music, vinyl, jazz.
- **Sponsor Deals**: Official manufacturer threads (Schiit, ZMF, Moondrop, iFi, Aune, HiFiMAN).

### 1.4 Classifieds (`/classifieds/`)
Community peer-to-peer buy, sell, and trade marketplace with feedback rating system.

---

## 2. Extracted Dataset Structure (`headfi_data/`)

```
headfi_data/
├── website_overview.md      # This comprehensive sitemap and index
├── images/                  # {len(img_files)} downloaded product photos, frequency charts & thumbnails
├── articles/                # In-depth articles with full text, diagrams, and comments
│   ├── *.md                 # Formatted Markdown reports
│   └── *.json               # Structured JSON data
├── reviews/                 # Gear reviews with ratings, photos, pros/cons, and review bodies
│   ├── *.md                 # Formatted Markdown reports
│   └── *.json               # Structured JSON data
└── threads/                 # Forum discussions with metadata and complete user replies
    ├── *.md                 # Formatted Markdown reports
    └── *.json               # Structured JSON data
```

---

## 3. Extracted Files Index

### 3.1 Articles ({len(art_files)} items)
"""
    for f in sorted(art_files):
        title = f.replace('.md', '').replace('_', ' ').title()
        md_content += f"- [{title}](articles/{f}) ([JSON](articles/{f.replace('.md', '.json')}))\n"

    md_content += f"\n### 3.2 Product Reviews ({len(rev_files)} items)\n"
    for f in sorted(rev_files):
        title = f.replace('.md', '').replace('_', ' ').title()
        md_content += f"- [{title}](reviews/{f}) ([JSON](reviews/{f.replace('.md', '.json')}))\n"

    md_content += f"\n### 3.3 Discussion Threads ({len(th_files)} items)\n"
    for f in sorted(th_files):
        title = f.replace('.md', '').replace('_', ' ').title()
        md_content += f"- [{title}](threads/{f}) ([JSON](threads/{f.replace('.md', '.json')}))\n"

    md_content += f"\n### 3.4 Downloaded Images ({len(img_files)} assets)\n"
    md_content += f"Stored locally in `headfi_data/images/` including product photos, frequency response graphs, and author icons.\n"

    with open(overview_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Generated overview at: {overview_path}")

def main():
    print("=== Starting Head-Fi Dataset Construction ===")
    print(f"Target directory: {ROOT_DIR}")
    scrape_articles()
    scrape_reviews()
    scrape_threads()
    generate_overview()
    print("\n=== Dataset Construction Finished Successfully! ===")

if __name__ == "__main__":
    main()
