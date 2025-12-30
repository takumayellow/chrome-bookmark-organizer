#!/usr/bin/env python3
"""
Chromeブックマーク整理スクリプト
- 重複削除
- 無効URL削除
- カテゴリー整理
"""

import re
from collections import defaultdict, Counter
from urllib.parse import urlparse
import sys

def parse_bookmarks_simple(filepath):
    """シンプルなブックマークパーサー"""
    bookmarks = []

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # ブックマークを正規表現で抽出
    pattern = r'<DT><A HREF="([^"]*)"[^>]*>([^<]*)</A>'
    matches = re.findall(pattern, content)

    for url, title in matches:
        bookmarks.append({
            'url': url,
            'title': title.strip()
        })

    return bookmarks

def analyze_bookmarks(bookmarks):
    """ブックマーク分析"""

    print(f"\n{'='*70}")
    print(f"総ブックマーク数: {len(bookmarks)}")
    print(f"{'='*70}\n")

    # ドメイン別集計
    domains = Counter()
    protocols = Counter()
    suspicious_count = {
        'chrome': 0,
        'javascript': 0,
        'file': 0,
        'localhost': 0,
        'empty': 0,
        'invalid': 0
    }

    for bm in bookmarks:
        url = bm['url']

        # 怪しいURLチェック
        if not url or url.strip() == '':
            suspicious_count['empty'] += 1
            continue

        if url.startswith('chrome://') or url.startswith('chrome-extension://'):
            suspicious_count['chrome'] += 1
            continue

        if url.startswith('javascript:'):
            suspicious_count['javascript'] += 1
            continue

        if url.startswith('file://'):
            suspicious_count['file'] += 1
            continue

        if 'localhost' in url or '127.0.0.1' in url:
            suspicious_count['localhost'] += 1
            continue

        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            protocol = parsed.scheme

            if domain:
                domains[domain] += 1
            if protocol:
                protocols[protocol] += 1
            else:
                suspicious_count['invalid'] += 1
        except:
            suspicious_count['invalid'] += 1

    # トップドメイン表示
    print("\n【トップ30ドメイン】")
    for domain, count in domains.most_common(30):
        print(f"  {count:5d} : {domain}")

    # プロトコル別
    print("\n【プロトコル別】")
    for proto, count in protocols.most_common():
        print(f"  {proto:15s} : {count:5d}")

    # 怪しいURL
    total_suspicious = sum(suspicious_count.values())
    print(f"\n【削除候補（怪しいブックマーク）】")
    for category, count in suspicious_count.items():
        if count > 0:
            print(f"  {category:15s} : {count:5d}個")
    print(f"\n  合計削除候補: {total_suspicious}個")

    # 重複検出
    url_count = Counter(bm['url'] for bm in bookmarks)
    duplicates = {url: count for url, count in url_count.items() if count > 1}

    duplicate_total = sum(duplicates.values()) - len(duplicates)

    print(f"\n【重複URL】")
    print(f"  重複しているユニークURL数: {len(duplicates)}")
    print(f"  削除可能な重複数: {duplicate_total}個")

    if duplicates:
        print(f"\n  トップ20重複URL:")
        for url, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:20]:
            url_display = url[:65] if len(url) > 65 else url
            print(f"    {count:3d}回 : {url_display}")

    return domains, suspicious_count, duplicates

def clean_bookmarks(bookmarks, remove_duplicates=True, remove_suspicious=True):
    """ブックマークをクリーニング"""

    print(f"\n{'='*70}")
    print("ブックマーククリーニング開始...")
    print(f"{'='*70}\n")

    seen_urls = set()
    cleaned = []
    removed_count = {
        'duplicate': 0,
        'chrome': 0,
        'javascript': 0,
        'file': 0,
        'localhost': 0,
        'empty': 0,
        'invalid': 0
    }

    for bm in bookmarks:
        url = bm['url']

        # 空URLチェック
        if not url or url.strip() == '':
            if remove_suspicious:
                removed_count['empty'] += 1
                continue

        # 重複チェック
        if remove_duplicates:
            if url in seen_urls:
                removed_count['duplicate'] += 1
                continue
            seen_urls.add(url)

        # 怪しいURLチェック
        if remove_suspicious:
            if url.startswith('chrome://') or url.startswith('chrome-extension://'):
                removed_count['chrome'] += 1
                continue

            if url.startswith('javascript:'):
                removed_count['javascript'] += 1
                continue

            if url.startswith('file://'):
                removed_count['file'] += 1
                continue

            if 'localhost' in url or '127.0.0.1' in url:
                removed_count['localhost'] += 1
                continue

        # 有効なブックマーク
        cleaned.append(bm)

    # 結果表示
    print("【削除内訳】")
    for category, count in removed_count.items():
        if count > 0:
            print(f"  {category:15s} : {count:5d}個")

    total_removed = sum(removed_count.values())
    print(f"\n  合計削除数: {total_removed}個")
    print(f"  残存ブックマーク数: {len(cleaned)}個")
    print(f"  削減率: {total_removed / len(bookmarks) * 100:.1f}%")

    return cleaned, removed_count

def save_cleaned_bookmarks(bookmarks, output_file):
    """クリーニングされたブックマークを保存"""

    html_header = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1703861181" LAST_MODIFIED="1766439577" PERSONAL_TOOLBAR_FOLDER="true">整理済みブックマーク</H3>
    <DL><p>
'''

    html_footer = '''    </DL><p>
</DL><p>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_header)

        for bm in bookmarks:
            url = bm['url'].replace('"', '&quot;')
            title = bm['title'].replace('<', '&lt;').replace('>', '&gt;')
            f.write(f'        <DT><A HREF="{url}">{title}</A>\n')

        f.write(html_footer)

    print(f"\n整理済みブックマークを保存: {output_file}")

def main():
    input_file = 'bookmarks_2025_12_31.html'
    output_file = 'bookmarks_cleaned.html'
    report_file = 'bookmark_cleaning_report.txt'

    print("="*70)
    print("Chromeブックマーク整理スクリプト")
    print("="*70)

    # パース
    print(f"\n[1/4] ブックマークファイルを読み込み中: {input_file}")
    bookmarks = parse_bookmarks_simple(input_file)

    # 分析
    print(f"\n[2/4] ブックマークを分析中...")
    domains, suspicious, duplicates = analyze_bookmarks(bookmarks)

    # クリーニング
    print(f"\n[3/4] ブックマークをクリーニング中...")
    cleaned_bookmarks, removed = clean_bookmarks(
        bookmarks,
        remove_duplicates=True,
        remove_suspicious=True
    )

    # 保存
    print(f"\n[4/4] 整理済みブックマークを保存中...")
    save_cleaned_bookmarks(cleaned_bookmarks, output_file)

    # レポート保存
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"ブックマーク整理レポート\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"元のブックマーク数: {len(bookmarks)}\n")
        f.write(f"整理後のブックマーク数: {len(cleaned_bookmarks)}\n")
        f.write(f"削除数: {sum(removed.values())}\n")
        f.write(f"削減率: {sum(removed.values()) / len(bookmarks) * 100:.1f}%\n\n")
        f.write(f"削除内訳:\n")
        for category, count in removed.items():
            f.write(f"  {category}: {count}個\n")

    print(f"\nレポートを保存: {report_file}")
    print(f"\n{'='*70}")
    print("完了！")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
