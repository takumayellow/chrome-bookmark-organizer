#!/usr/bin/env python3
"""
Chromeブックマーク分析・整理スクリプト
"""

import re
from collections import defaultdict, Counter
from html.parser import HTMLParser
from urllib.parse import urlparse
import sys

class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.folders = []
        self.current_folder = []
        self.in_dt = False
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'dt':
            self.in_dt = True

        elif tag == 'h3':
            # フォルダ
            folder_name = ''
            self.current_folder.append(folder_name)

        elif tag == 'a':
            # ブックマーク
            href = attrs_dict.get('href', '')
            add_date = attrs_dict.get('add_date', '')
            icon = attrs_dict.get('icon', '')

            self.current_link = {
                'url': href,
                'add_date': add_date,
                'icon': icon,
                'folder': '/'.join(self.current_folder),
                'title': ''
            }

    def handle_endtag(self, tag):
        if tag == 'dt':
            self.in_dt = False
            if self.current_link:
                self.bookmarks.append(self.current_link)
                self.current_link = None

        elif tag == 'dl':
            # フォルダ終了
            if self.current_folder:
                self.current_folder.pop()

    def handle_data(self, data):
        data = data.strip()
        if data:
            if self.current_link is not None:
                self.current_link['title'] = data
            elif self.in_dt and self.current_folder:
                self.current_folder[-1] = data

def analyze_bookmarks(bookmarks):
    """ブックマークを分析"""

    print(f"\n{'='*60}")
    print(f"総ブックマーク数: {len(bookmarks)}")
    print(f"{'='*60}\n")

    # ドメイン別集計
    domains = Counter()
    protocols = Counter()
    folder_counts = Counter()

    for bm in bookmarks:
        url = bm['url']
        folder = bm['folder']

        folder_counts[folder if folder else '(ルート)'] += 1

        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            protocol = parsed.scheme

            if domain:
                domains[domain] += 1
            protocols[protocol] += 1
        except:
            pass

    # トップドメイン表示
    print("\n【トップ20ドメイン】")
    for domain, count in domains.most_common(20):
        print(f"  {count:4d} : {domain}")

    # プロトコル別
    print("\n【プロトコル別】")
    for proto, count in protocols.most_common():
        print(f"  {proto:10s} : {count}")

    # フォルダ別
    print("\n【トップ20フォルダ】")
    for folder, count in sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        folder_display = folder[:50] if len(folder) > 50 else folder
        print(f"  {count:4d} : {folder_display}")

    return domains, protocols, folder_counts

def find_duplicates(bookmarks):
    """重複ブックマークを検出"""

    url_count = Counter(bm['url'] for bm in bookmarks)
    duplicates = {url: count for url, count in url_count.items() if count > 1}

    print(f"\n{'='*60}")
    print(f"重複URL数: {len(duplicates)} ({sum(duplicates.values())} ブックマーク)")
    print(f"{'='*60}\n")

    if duplicates:
        print("【重複トップ20】")
        for url, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:20]:
            url_display = url[:60] if len(url) > 60 else url
            print(f"  {count:3d}回 : {url_display}")

    return duplicates

def find_suspicious(bookmarks):
    """怪しいブックマークを検出"""

    suspicious = {
        'chrome_urls': [],
        'localhost': [],
        'file': [],
        'javascript': [],
        'empty': [],
        'invalid': []
    }

    for bm in bookmarks:
        url = bm['url']

        if not url or url.strip() == '':
            suspicious['empty'].append(bm)
        elif url.startswith('chrome://') or url.startswith('chrome-extension://'):
            suspicious['chrome_urls'].append(bm)
        elif url.startswith('javascript:'):
            suspicious['javascript'].append(bm)
        elif url.startswith('file://'):
            suspicious['file'].append(bm)
        elif 'localhost' in url or '127.0.0.1' in url:
            suspicious['localhost'].append(bm)
        elif not url.startswith('http'):
            suspicious['invalid'].append(bm)

    print(f"\n{'='*60}")
    print("【削除候補（怪しいブックマーク）】")
    print(f"{'='*60}\n")

    total_suspicious = 0
    for category, items in suspicious.items():
        if items:
            print(f"  {category:15s} : {len(items):4d}個")
            total_suspicious += len(items)

    print(f"\n  合計削除候補: {total_suspicious}個\n")

    return suspicious

def main():
    print("Chromeブックマーク分析開始...")

    # HTMLファイル読み込み
    with open('bookmarks_2025_12_31.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # パース
    parser = BookmarkParser()
    parser.feed(html_content)

    bookmarks = parser.bookmarks

    # 分析実行
    domains, protocols, folder_counts = analyze_bookmarks(bookmarks)
    duplicates = find_duplicates(bookmarks)
    suspicious = find_suspicious(bookmarks)

    # 統計情報保存
    with open('bookmark_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(f"総ブックマーク数: {len(bookmarks)}\n")
        f.write(f"重複URL数: {len(duplicates)}\n")
        f.write(f"削除候補数: {sum(len(v) for v in suspicious.values())}\n")

    print(f"\n{'='*60}")
    print("分析完了！")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
