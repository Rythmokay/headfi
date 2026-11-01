#!/usr/bin/env python3
"""
Scrapling-based extractor for Head-Fi 'What's New / Posts'
Uses Scrapling's Selector parser to extract thread metadata, post activity, and user session info.
"""

import os
import sys
import json
import csv
import subprocess
from scrapling.parser import Selector

def fetch_html_from_browser():
    """Extract HTML directly from the active Brave Browser tab using AppleScript."""
    applescript = '''
    tell application "Brave Browser"
        repeat with w in windows
            repeat with t in tabs of w
                if URL of t starts with "https://www.head-fi.org" then
                    return execute t javascript "document.documentElement.outerHTML"
                end if
            end repeat
        end repeat
    end tell
    '''
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, check=True)
    return result.stdout

def main():
    target_url = "https://www.head-fi.org/whats-new/posts/7934587/"
    
    # Try reading from temporary cache or live browser
    html = None
    if os.path.exists("/tmp/headfi_page.html"):
        with open("/tmp/headfi_page.html", "r", encoding="utf-8") as f:
            html = f.read()
    else:
        print("Extracting live page from Brave Browser...")
        html = fetch_html_from_browser()
        with open("/tmp/headfi_page.html", "w", encoding="utf-8") as f:
            f.write(html)
            
    # Parse with Scrapling Selector
    page = Selector(html, url=target_url)
    
    # Session / User details
    logged_in_user = page.css('.p-navgroup-link--user .p-navgroup-linkText::text').get()
    
    # Post items extraction
    posts = []
    for item in page.css('.structItem'):
        labels = item.css('.labelLink::text').getall()
        prefix = ' '.join([l.strip() for l in labels if l.strip()])
        
        title_el = item.css('.structItem-title a:not(.labelLink)')
        title = title_el.css('::text').get() or ''
        rel_url = title_el.css('::attr(href)').get() or ''
        full_url = f"https://www.head-fi.org{rel_url}" if rel_url.startswith('/') else rel_url
        
        parts = item.css('.structItem-minor .structItem-parts li')
        author = parts[0].css('::text').get().strip() if len(parts) > 0 and parts[0].css('::text').get() else ''
        created_date = parts[1].css('time::text').get() or parts[1].css('::text').get() if len(parts) > 1 else ''
        forum = parts[2].css('::text').get().strip() if len(parts) > 2 and parts[2].css('::text').get() else ''
        
        replies = item.css('.structItem-cell--meta dl:first-child dd::text').get() or '0'
        views = item.css('.structItem-cell--meta dl:last-child dd::text').get() or '0'
        
        latest_user = item.css('.structItem-cell--latest .structItem-minor a::text').get() or ''
        latest_time = item.css('.structItem-cell--latest time::text').get() or item.css('.structItem-cell--latest time::attr(datetime)').get() or ''
        
        posts.append({
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
        
    output_data = {
        'url': target_url,
        'logged_in_user': logged_in_user.strip() if logged_in_user else None,
        'total_extracted': len(posts),
        'posts': posts
    }
    
    # Save to JSON
    json_path = "head_fi_posts.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    # Save to CSV
    csv_path = "head_fi_posts.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            'title', 'prefix', 'forum', 'author', 'created_date', 
            'replies', 'views', 'latest_reply_by', 'latest_reply_time', 'url'
        ])
        writer.writeheader()
        writer.writerows(posts)
        
    print(f"Extraction successful!")
    print(f"Logged-in user: {logged_in_user}")
    print(f"Extracted {len(posts)} posts/threads.")
    print(f"Saved to {json_path} and {csv_path}")

if __name__ == "__main__":
    main()
