#!/usr/bin/env python3
"""
Comprehensive Scrapling Crawler for Head-Fi "What's New / Posts"
Walks through all pagination pages (1 to 10+), extracting threads, reviews, metadata,
and supports deep comment extraction using Scrapling's Selector parser.
"""

import os
import sys
import time
import json
import csv
import subprocess
import argparse
from typing import List, Dict, Any, Optional
from scrapling.parser import Selector

BASE_URL = "https://www.head-fi.org"
WHATS_NEW_PATH = "/whats-new/posts/7934587/"

def fetch_url_via_browser(path_or_url: str, timeout_sec: int = 25) -> Optional[str]:
    """
    Fetch an endpoint inside the authenticated Brave Browser tab context.
    Inherits all active cookies, Cloudflare clearance, and user session.
    """
    # Clean URL path if absolute
    if path_or_url.startswith(BASE_URL):
        fetch_path = path_or_url[len(BASE_URL):]
    else:
        fetch_path = path_or_url

    escaped_path = fetch_path.replace('"', '\\"')
    applescript = f'''
tell application "Brave Browser"
    repeat with w in windows
        repeat with t in tabs of w
            if URL of t starts with "https://www.head-fi.org" then
                execute t javascript "window.__fetchedHtml = null; fetch('{escaped_path}').then(r => r.text()).then(t => {{ window.__fetchedHtml = t; }}).catch(e => {{ window.__fetchedHtml = 'ERROR: ' + e; }});"
                set tries to 0
                repeat while tries < {int(timeout_sec * 2.5)}
                    delay 0.4
                    set res to execute t javascript "window.__fetchedHtml ? 'READY:' + window.__fetchedHtml.length : 'WAITING'"
                    if res starts with "READY" then
                        return execute t javascript "window.__fetchedHtml"
                    end if
                    set tries to tries + 1
                end repeat
                return "TIMEOUT"
            end if
        end repeat
    end repeat
end tell
return "NO_HEADFI_TAB"
'''
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    out = result.stdout.strip()
    if not out or out in ("TIMEOUT", "NO_HEADFI_TAB") or out.startswith("ERROR:"):
        print(f"Warning: Fetch failed for {fetch_path}: {out[:100]}", file=sys.stderr)
        return None
    return result.stdout

def parse_posts_page(html: str, page_num: int, page_url: str) -> List[Dict[str, Any]]:
    """Parse a single What's New pagination page using Scrapling."""
    page = Selector(html, url=page_url)
    items = page.css('.structItem')
    posts = []
    
    for item in items:
        # Badges / Prefixes (e.g., 'Review', 'Discussion')
        labels = item.css('.labelLink::text').getall()
        prefix = ' '.join([l.strip() for l in labels if l.strip()])
        
        # Thread Title & Relative Link
        title_el = item.css('.structItem-title a:not(.labelLink)')
        title = title_el.css('::text').get() or ''
        rel_url = title_el.css('::attr(href)').get() or ''
        full_url = f"{BASE_URL}{rel_url}" if rel_url.startswith('/') else rel_url
        
        # Minor parts (Author, Created Date, Forum Category)
        parts = item.css('.structItem-minor .structItem-parts li')
        author = parts[0].css('::text').get().strip() if len(parts) > 0 and parts[0].css('::text').get() else ''
        created_date = parts[1].css('time::text').get() or parts[1].css('::text').get() if len(parts) > 1 else ''
        forum = parts[2].css('::text').get().strip() if len(parts) > 2 and parts[2].css('::text').get() else ''
        
        # Metrics
        replies = item.css('.structItem-cell--meta dl:first-child dd::text').get() or '0'
        views = item.css('.structItem-cell--meta dl:last-child dd::text').get() or '0'
        
        # Latest Post info
        latest_user = item.css('.structItem-cell--latest .structItem-minor a::text').get() or ''
        latest_time = item.css('.structItem-cell--latest time::text').get() or item.css('.structItem-cell--latest time::attr(datetime)').get() or ''
        
        posts.append({
            'page_num': page_num,
            'title': title.strip(),
            'prefix': prefix,
            'forum': forum,
            'author': author,
            'created_date': created_date.strip() if created_date else '',
            'replies': replies.strip(),
            'views': views.strip(),
            'latest_reply_by': latest_user.strip(),
            'latest_reply_time': latest_time.strip(),
            'url': full_url
        })
        
    return posts

def fetch_thread_comments(thread_url: str, max_comments: int = 10) -> List[Dict[str, Any]]:
    """Fetch and parse comments from an individual thread using Scrapling."""
    html = fetch_url_via_browser(thread_url)
    if not html:
        return []
        
    page = Selector(html, url=thread_url)
    messages = page.css('article.message')
    comments = []
    
    for msg in messages[:max_comments]:
        user = msg.css('.message-name a::text').get() or ''
        time_el = msg.css('.message-attribution-main time')
        date_str = time_el.css('::text').get() or time_el.css('::attr(datetime)').get() or ''
        post_num = msg.css('.message-attribution-opposite a::text').get() or ''
        wrappers = msg.css('.bbWrapper')
        body = wrappers[0].get_all_text() if wrappers else ''
        
        comments.append({
            'post_number': post_num.strip(),
            'author': user.strip(),
            'date': date_str.strip() if date_str else '',
            'content': body.strip()
        })
        
    return comments

def main():
    parser = argparse.ArgumentParser(description="Scrape all pages of Head-Fi What's New posts using Scrapling.")
    parser.add_argument('--max-pages', type=int, default=10, help='Maximum number of pagination pages to scrape (default: 10)')
    parser.add_argument('--include-comments-for-top', type=int, default=15, help='Deep-scrape comments for top N threads (default: 15)')
    parser.add_argument('--comments-per-thread', type=int, default=15, help='Max comments to fetch per thread (default: 15)')
    args = parser.parse_args()
    
    print(f"=== Starting Head-Fi Scrapling Crawl ===")
    print(f"Target: What's New feed ({args.max_pages} pages)")
    print(f"Base URL: {BASE_URL}{WHATS_NEW_PATH}")
    
    all_posts = []
    
    for page_num in range(1, args.max_pages + 1):
        if page_num == 1:
            page_path = WHATS_NEW_PATH
        else:
            page_path = f"{WHATS_NEW_PATH}page-{page_num}"
            
        page_url = f"{BASE_URL}{page_path}"
        print(f"\n[Page {page_num}/{args.max_pages}] Fetching: {page_path} ...", end="", flush=True)
        
        html = fetch_url_via_browser(page_path)
        if not html:
            print(" Failed to retrieve.")
            break
            
        posts = parse_posts_page(html, page_num, page_url)
        print(f" Extracted {len(posts)} threads.")
        all_posts.extend(posts)
        
        # Check if there is next page indicator
        page_sel = Selector(html)
        next_btn = page_sel.css('.pageNav-jump--next')
        if not next_btn and page_num > 1:
            print("Reached last available page.")
            break
            
        time.sleep(0.4)  # Polite delay
        
    print(f"\nTotal threads extracted across {page_num} pages: {len(all_posts)}")
    
    # Optional comment deep extraction for top threads
    if args.include_comments_for_top > 0:
        top_n = min(args.include_comments_for_top, len(all_posts))
        print(f"\nFetching top comments ({args.comments_per_thread} per thread) for {top_n} threads...")
        for i in range(top_n):
            thread = all_posts[i]
            print(f"  [{i+1}/{top_n}] Fetching comments for: {thread['title'][:40]}...")
            thread['comments'] = fetch_thread_comments(thread['url'], max_comments=args.comments_per_thread)
            time.sleep(0.4)
            
    # Save to JSON
    json_path = "head_fi_all_posts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_count": len(all_posts),
            "pages_crawled": page_num,
            "posts": all_posts
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved full JSON to: {json_path}")
    
    # Save to CSV
    csv_path = "head_fi_all_posts.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            'page_num', 'title', 'prefix', 'forum', 'author', 
            'created_date', 'replies', 'views', 'latest_reply_by', 'latest_reply_time', 'url'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_posts)
    print(f"Saved CSV to: {csv_path}")

if __name__ == "__main__":
    main()
