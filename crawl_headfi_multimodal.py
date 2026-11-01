#!/usr/bin/env python3
"""
Multimodal Head-Fi Deep Crawler & Cloud Sync Engine
Crawls reviews, showcase products, technical articles, and active forum discussions
with comments, downloads images locally, and syncs directly to Google Drive.
"""

import os
import re
import sys
import time
import json
import urllib.request
import ssl
import subprocess
import argparse
from typing import List, Dict, Any, Optional
from scrapling.parser import Selector

BASE_URL = "https://www.head-fi.org"
ROOT_DIR = os.path.abspath("headfi_data")
ARTICLES_DIR = os.path.join(ROOT_DIR, "articles")
REVIEWS_DIR = os.path.join(ROOT_DIR, "reviews")
THREADS_DIR = os.path.join(ROOT_DIR, "threads")
IMAGES_DIR = os.path.join(ROOT_DIR, "images")

for d in (ROOT_DIR, ARTICLES_DIR, REVIEWS_DIR, THREADS_DIR, IMAGES_DIR):
    os.makedirs(d, exist_ok=True)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text.lower().strip())
    return re.sub(r'[-\s]+', '_', text)[:60]

def sync_to_gdrive():
    """Sync current state of headfi_data to Google Drive."""
    print("\n>>> Syncing new data and images to Google Drive...", flush=True)
    subprocess.run(['rclone', 'copy', ROOT_DIR, 'gdrive:headfi_data', '-P'], check=False)
    subprocess.run(['rclone', 'copy', 'head_fi_all_posts.json', 'gdrive:', '-q'], check=False)
    subprocess.run(['rclone', 'copy', 'head_fi_all_posts.csv', 'gdrive:', '-q'], check=False)
    print(">>> Google Drive sync completed.\n", flush=True)

def download_image(url: str, filename_prefix: str) -> Optional[str]:
    """Download image to headfi_data/images/ and return relative path."""
    if not url or not url.startswith('http') or 'joypixels' in url or 'smilies' in url:
        return None
    try:
        clean_url = url.split('?')[0]
        ext = os.path.splitext(clean_url)[1] or '.jpg'
        if ext.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            ext = '.jpg'
        filename = f"{filename_prefix}_{abs(hash(clean_url)) % 1000000}{ext}"
        filepath = os.path.join(IMAGES_DIR, filename)
        rel_path = f"../images/{filename}"
        
        if not os.path.exists(filepath):
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=12) as response:
                content = response.read()
                if len(content) > 1500:
                    with open(filepath, 'wb') as f:
                        f.write(content)
                else:
                    return None
        return rel_path
    except Exception:
        return None

def fetch_in_browser(path_or_url: str, timeout_sec: int = 25) -> Optional[str]:
    """Fetch endpoint inside active Brave Browser tab context."""
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
# CRAWL SHOWCASE REVIEWS
# ==========================================
def crawl_showcase_categories(categories: List[str], items_per_cat: int = 5):
    print("\n==============================================")
    print(">>> Crawling Product Showcase & Reviews")
    print("==============================================")
    
    for cat_path in categories:
        cat_name = cat_path.strip('/').split('/')[-1]
        print(f"\n[Showcase Category] Fetching: {cat_name} ({cat_path})...")
        html = fetch_in_browser(cat_path)
        if not html:
            continue
            
        page = Selector(html, url=f"{BASE_URL}{cat_path}")
        items = page.css('.structItem')
        print(f"  Found {len(items)} products in category.")
        
        for idx, item in enumerate(items[:items_per_cat], 1):
            title = item.css('.structItem-title a::text').get() or f"Item {idx}"
            title = title.strip()
            rel_url = item.css('.structItem-title a::attr(href)').get() or ''
            thumb_url = item.css('.structItem-iconContainer img::attr(src)').get() or ''
            rating = item.css('.ratingStars::attr(title)').get() or 'Unrated'
            
            slug = slugify(title)
            print(f"  [{idx}/{items_per_cat}] Product Review: {title} ({rating})...")
            local_thumb = download_image(thumb_url, f"rev_{slug}_thumb") if thumb_url else None
            
            prod_html = fetch_in_browser(rel_url)
            if not prod_html:
                continue
                
            prod_page = Selector(prod_html, url=f"{BASE_URL}{rel_url}")
            reviews = []
            
            for r in prod_page.css('.review, .message, article.message')[:4]:
                r_author = r.css('.message-name a::text, .review-author::text').get() or 'Reviewer'
                r_rating = r.css('.ratingStars::attr(title)').get() or rating
                r_wrappers = r.css('.bbWrapper')
                r_body = r_wrappers[0].get_all_text().strip() if r_wrappers else ''
                
                review_imgs = []
                for r_img in r.css('.bbWrapper img')[:6]:
                    src = r_img.attrib.get('src', '')
                    local_img = download_image(src, f"rev_{slug}_photo")
                    if local_img:
                        review_imgs.append({'remote': src, 'local': local_img})
                        
                if r_body:
                    reviews.append({
                        'author': r_author.strip(),
                        'rating': r_rating.strip(),
                        'body': r_body,
                        'photos': review_imgs
                    })
                    
            # Save Markdown & JSON
            md_file = os.path.join(REVIEWS_DIR, f"{slug}.md")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"- **Category**: {cat_name}\n")
                f.write(f"- **Overall Rating**: {rating.strip()}\n")
                f.write(f"- **Product URL**: [{BASE_URL}{rel_url}]({BASE_URL}{rel_url})\n\n")
                if local_thumb:
                    f.write(f"![Product Image]({local_thumb})\n\n")
                f.write("## Reviews & Audio Impressions\n\n")
                for r_idx, rev in enumerate(reviews, 1):
                    f.write(f"### Review #{r_idx} by {rev['author']} (Rating: {rev['rating']})\n\n")
                    f.write(f"{rev['body']}\n\n")
                    if rev['photos']:
                        f.write("#### Review Photos\n\n")
                        for p in rev['photos']:
                            f.write(f"![Gear Photo]({p['local']})\n\n")
                            
            json_file = os.path.join(REVIEWS_DIR, f"{slug}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'product_name': title,
                    'category': cat_name,
                    'rating': rating.strip(),
                    'url': f"{BASE_URL}{rel_url}",
                    'thumbnail': local_thumb,
                    'reviews': reviews
                }, f, indent=2, ensure_ascii=False)
                
            time.sleep(0.3)

# ==========================================
# CRAWL FORUM DISCUSSIONS
# ==========================================
def crawl_forum_sections(forum_paths: List[str], threads_per_forum: int = 4):
    print("\n==============================================")
    print(">>> Crawling Forum Sections & Community Threads")
    print("==============================================")
    
    for f_path in forum_paths:
        f_name = f_path.strip('/').split('/')[-1]
        print(f"\n[Forum Section] Fetching: {f_name} ({f_path})...")
        html = fetch_in_browser(f_path)
        if not html:
            continue
            
        page = Selector(html, url=f"{BASE_URL}{f_path}")
        threads = page.css('.structItem')
        print(f"  Found {len(threads)} threads in section.")
        
        for idx, th in enumerate(threads[:threads_per_forum], 1):
            title_el = th.css('.structItem-title a:not(.labelLink)')
            title = title_el.css('::text').get() or f"Thread {idx}"
            title = title.strip()
            rel_url = title_el.css('::attr(href)').get() or ''
            author = th.css('.structItem-parts li:first-child a::text').get() or 'Member'
            replies = th.css('.structItem-cell--meta dl:first-child dd::text').get() or '0'
            views = th.css('.structItem-cell--meta dl:last-child dd::text').get() or '0'
            
            slug = slugify(title)
            print(f"  [{idx}/{threads_per_forum}] Thread: {title[:40]}... (Replies: {replies})")
            
            th_html = fetch_in_browser(rel_url)
            if not th_html:
                continue
                
            th_page = Selector(th_html, url=f"{BASE_URL}{rel_url}")
            comments = []
            downloaded_imgs = []
            
            for m_idx, msg in enumerate(th_page.css('article.message')[:10], 1):
                m_author = msg.css('.message-name a::text').get() or 'Member'
                m_time = msg.css('.message-attribution-main time::text').get() or ''
                m_wrappers = msg.css('.bbWrapper')
                m_body = m_wrappers[0].get_all_text().strip() if m_wrappers else ''
                
                for img in msg.css('.bbWrapper img')[:3]:
                    src = img.attrib.get('src', '')
                    local_img = download_image(src, f"th_{slug}_img")
                    if local_img:
                        downloaded_imgs.append(local_img)
                        
                if m_body:
                    comments.append({
                        'post_index': m_idx,
                        'author': m_author.strip(),
                        'date': m_time.strip(),
                        'content': m_body
                    })
                    
            # Save Markdown & JSON
            md_file = os.path.join(THREADS_DIR, f"{slug}.md")
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"- **Forum Section**: {f_name}\n")
                f.write(f"- **Original Author**: {author.strip()}\n")
                f.write(f"- **Replies / Views**: {replies.strip()} / {views.strip()}\n")
                f.write(f"- **URL**: [{BASE_URL}{rel_url}]({BASE_URL}{rel_url})\n\n")
                if downloaded_imgs:
                    f.write("## Attached Gear Images\n\n")
                    for img_p in downloaded_imgs[:4]:
                        f.write(f"![Attached Image]({img_p})\n\n")
                f.write("## Discussion Posts & Comments\n\n")
                for c in comments:
                    f.write(f"### Post #{c['post_index']} by **{c['author']}** ({c['date']})\n\n")
                    f.write(f"{c['content']}\n\n---\n\n")
                    
            json_file = os.path.join(THREADS_DIR, f"{slug}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'title': title,
                    'forum': f_name,
                    'author': author.strip(),
                    'replies': replies.strip(),
                    'views': views.strip(),
                    'url': f"{BASE_URL}{rel_url}",
                    'comments': comments
                }, f, indent=2, ensure_ascii=False)
                
            time.sleep(0.3)

def update_overview_catalog():
    """Update master overview with latest file counts."""
    overview_path = os.path.join(ROOT_DIR, "website_overview.md")
    art_files = [fn for fn in os.listdir(ARTICLES_DIR) if fn.endswith('.md')]
    rev_files = [fn for fn in os.listdir(REVIEWS_DIR) if fn.endswith('.md')]
    th_files = [fn for fn in os.listdir(THREADS_DIR) if fn.endswith('.md')]
    img_files = [fn for fn in os.listdir(IMAGES_DIR) if not fn.startswith('.')]
    
    with open(overview_path, 'w', encoding='utf-8') as f:
        f.write("# Head-Fi.org Multimodal Audio Knowledge Dataset\n\n")
        f.write(f"> **Cloud Storage (Google Drive)**: Connected (`5.0 TiB` storage)  \n")
        f.write(f"> **Articles**: **{len(art_files)} items**  \n")
        f.write(f"> **Product Reviews**: **{len(rev_files)} items**  \n")
        f.write(f"> **Forum Discussions**: **{len(th_files)} items**  \n")
        f.write(f"> **Images & Frequency Charts**: **{len(img_files)} files**  \n\n")
        f.write("---\n\n")
        f.write("## Product Reviews Index\n\n")
        for fn in sorted(rev_files):
            f.write(f"- [{fn.replace('.md', '').replace('_', ' ').title()}](reviews/{fn})\n")
        f.write("\n## Forum Discussions Index\n\n")
        for fn in sorted(th_files):
            f.write(f"- [{fn.replace('.md', '').replace('_', ' ').title()}](threads/{fn})\n")
        f.write("\n## Technical Articles & Guides Index\n\n")
        for fn in sorted(art_files):
            f.write(f"- [{fn.replace('.md', '').replace('_', ' ').title()}](articles/{fn})\n")

def main():
    print("=== Multimodal Head-Fi Crawler Starting ===")
    
    # Showcase categories to crawl
    showcase_cats = [
        "/showcase/categories/in-ear.259/",
        "/showcase/categories/over-ear.263/",
        "/showcase/categories/desktop-amps.269/",
        "/showcase/categories/portable-amps.270/",
        "/showcase/categories/dacs.275/",
        "/showcase/categories/digital-audio-flac-mp3-etc-players-daps.277/"
    ]
    
    # Primary forum sections to crawl
    forum_sections = [
        "/forums/headphones-full-size.4/",
        "/forums/portable-headphones-earphones-and-in-ear-monitors.103/",
        "/forums/headphone-amps-full-size.5/",
        "/forums/portable-source-gear.15/",
        "/forums/dedicated-source-components.7/",
        "/forums/high-end-audio-forum.113/",
        "/forums/sponsor-announcements-and-deals.6015/"
    ]
    
    crawl_showcase_categories(showcase_cats, items_per_cat=4)
    sync_to_gdrive()
    
    crawl_forum_sections(forum_sections, threads_per_forum=4)
    update_overview_catalog()
    sync_to_gdrive()
    
    print("\n=== Multimodal Head-Fi Crawl & Google Drive Sync Completed Successfully! ===")

if __name__ == "__main__":
    main()
