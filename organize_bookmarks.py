#!/usr/bin/env python3
"""
Chromeブックマーク整理スクリプト
重複、無効なリンク、不要なブックマークを削除して整理済みHTMLを生成
"""

import re
from collections import defaultdict, Counter
from html.parser import HTMLParser
from urllib.parse import urlparse
import sys

class BookmarkParser(HTMLParser):
    """ブックマークHTMLをパースするクラス"""

    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.folder_stack = []
        self.current_bookmark = None
        self.pending_folder = None
        self.in_h3 = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h3':
            # フォルダ開始
            self.in_h3 = True
            self.pending_folder = {
                'name': '',
                'attrs': attrs_dict
            }

        elif tag == 'a':
            # ブックマーク
            self.current_bookmark = {
                'url': attrs_dict.get('href', ''),
                'add_date': attrs_dict.get('add_date', ''),
                'icon': attrs_dict.get('icon', ''),
                'folder_path': '/'.join(self.folder_stack),
                'title': '',
                'attrs': attrs_dict
            }

        elif tag == 'dl':
            # 新しいフォルダ階層開始
            if self.pending_folder:
                self.folder_stack.append(self.pending_folder['name'])
                self.pending_folder = None

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_h3 = False

        elif tag == 'dl':
            # フォルダ階層終了
            if self.folder_stack:
                self.folder_stack.pop()

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        if self.in_h3 and self.pending_folder:
            # フォルダ名
            self.pending_folder['name'] = data

        elif self.current_bookmark is not None:
            # ブックマークタイトル
            self.current_bookmark['title'] = data
            self.bookmarks.append(self.current_bookmark)
            self.current_bookmark = None

def is_valid_url(url):
    """URLが有効かチェック"""
    if not url or not url.strip():
        return False, 'empty'

    url = url.strip()

    if url.startswith('chrome://') or url.startswith('chrome-extension://'):
        return False, 'chrome_url'
    if url.startswith('javascript:'):
        return False, 'javascript'
    if url.startswith('file://'):
        return False, 'file'
    if 'localhost' in url or '127.0.0.1' in url:
        return False, 'localhost'
    if not url.startswith('http'):
        return False, 'invalid_protocol'

    return True, 'valid'

def analyze_bookmarks(bookmarks):
    """ブックマークを詳細分析"""

    print(f"\n{'='*70}")
    print(f"総ブックマーク数: {len(bookmarks):,}")
    print(f"{'='*70}\n")

    # 統計情報
    domains = Counter()
    protocols = Counter()
    folder_counts = Counter()
    invalid_reasons = Counter()

    valid_count = 0
    invalid_bookmarks = []

    for bm in bookmarks:
        url = bm['url']
        folder = bm['folder_path'] or '(ルート)'
        folder_counts[folder] += 1

        # URL検証
        is_valid, reason = is_valid_url(url)
        if is_valid:
            valid_count += 1
            try:
                parsed = urlparse(url)
                domains[parsed.netloc] += 1
                protocols[parsed.scheme] += 1
            except:
                pass
        else:
            invalid_reasons[reason] += 1
            invalid_bookmarks.append(bm)

    # ドメイン別集計
    print("\n【トップ30ドメイン】")
    for i, (domain, count) in enumerate(domains.most_common(30), 1):
        print(f"  {i:2d}. {count:5,}個 : {domain}")

    # プロトコル別
    print("\n【プロトコル別】")
    for proto, count in protocols.most_common():
        print(f"  {proto:15s} : {count:5,}個")

    # フォルダ別
    print("\n【トップ30フォルダ】")
    sorted_folders = sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (folder, count) in enumerate(sorted_folders[:30], 1):
        folder_display = folder[:60] + '...' if len(folder) > 60 else folder
        print(f"  {i:2d}. {count:5,}個 : {folder_display}")

    # 無効URL統計
    print(f"\n【無効URL統計】")
    print(f"  有効: {valid_count:5,}個")
    for reason, count in sorted(invalid_reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason:20s} : {count:5,}個")
    print(f"  {'='*40}")
    print(f"  無効合計: {len(invalid_bookmarks):5,}個")

    return {
        'domains': domains,
        'protocols': protocols,
        'folder_counts': folder_counts,
        'invalid_bookmarks': invalid_bookmarks,
        'invalid_reasons': invalid_reasons
    }

def find_duplicates(bookmarks):
    """重複URLを検出"""

    url_to_bookmarks = defaultdict(list)
    for bm in bookmarks:
        url_to_bookmarks[bm['url']].append(bm)

    duplicates = {url: bms for url, bms in url_to_bookmarks.items() if len(bms) > 1}
    total_duplicate_count = sum(len(bms) for bms in duplicates.values())

    print(f"\n{'='*70}")
    print(f"重複URL: {len(duplicates):,}種類 (合計 {total_duplicate_count:,}個のブックマーク)")
    print(f"{'='*70}\n")

    if duplicates:
        print("【重複数トップ20】")
        sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
        for i, (url, bms) in enumerate(sorted_dups[:20], 1):
            url_display = url[:70] + '...' if len(url) > 70 else url
            print(f"  {i:2d}. {len(bms):3d}回 : {url_display}")

    return duplicates

def clean_bookmarks(bookmarks, duplicates):
    """ブックマークを整理（重複削除、無効URL削除）"""

    cleaned = []
    removed_count = {
        'duplicate': 0,
        'invalid': 0
    }

    # 重複は最初の1つだけ残す
    seen_urls = set()

    for bm in bookmarks:
        url = bm['url']

        # 重複チェック
        if url in seen_urls:
            removed_count['duplicate'] += 1
            continue

        # URL有効性チェック
        is_valid, reason = is_valid_url(url)
        if not is_valid:
            removed_count['invalid'] += 1
            continue

        seen_urls.add(url)
        cleaned.append(bm)

    print(f"\n{'='*70}")
    print(f"クリーニング結果")
    print(f"{'='*70}")
    print(f"  元のブックマーク数: {len(bookmarks):6,}個")
    print(f"  重複削除:         {removed_count['duplicate']:6,}個")
    print(f"  無効URL削除:      {removed_count['invalid']:6,}個")
    print(f"  {'='*50}")
    print(f"  整理後:           {len(cleaned):6,}個")
    print(f"  削減率:           {(1 - len(cleaned)/len(bookmarks))*100:6.2f}%")
    print(f"{'='*70}\n")

    return cleaned

def generate_cleaned_html(original_html_path, cleaned_bookmarks):
    """整理済みHTMLを生成"""

    # URLセットを作成（高速検索用）
    valid_urls = {bm['url'] for bm in cleaned_bookmarks}

    # 元のHTMLを読み込み
    with open(original_html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 新しいHTMLを生成
    output_lines = []
    skip_next_line = False

    for i, line in enumerate(lines):
        if skip_next_line:
            skip_next_line = False
            continue

        # ブックマーク行かチェック
        if '<A HREF=' in line or '<A href=' in line:
            # URLを抽出
            href_match = re.search(r'HREF="([^"]*)"', line, re.IGNORECASE)
            if href_match:
                url = href_match.group(1)
                # 有効なURLのみ残す
                if url in valid_urls:
                    output_lines.append(line)
                # else: この行はスキップ（削除）
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)

    # ファイルに書き出し
    output_path = original_html_path.replace('.html', '_cleaned.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    print(f"整理済みブックマークを保存: {output_path}\n")
    return output_path

def save_analysis_report(bookmarks, analysis, duplicates, output_path='bookmark_analysis_report.txt'):
    """詳細な分析レポートを保存"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("Chromeブックマーク分析レポート\n")
        f.write("="*70 + "\n\n")

        f.write(f"総ブックマーク数: {len(bookmarks):,}個\n\n")

        # 無効URL詳細
        f.write("-"*70 + "\n")
        f.write("無効URL統計\n")
        f.write("-"*70 + "\n")
        for reason, count in sorted(analysis['invalid_reasons'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {reason:20s} : {count:5,}個\n")
        f.write(f"\n  合計: {len(analysis['invalid_bookmarks']):,}個\n\n")

        # 重複URL詳細
        f.write("-"*70 + "\n")
        f.write("重複URL統計\n")
        f.write("-"*70 + "\n")
        f.write(f"重複URL種類: {len(duplicates):,}\n")
        f.write(f"重複ブックマーク数: {sum(len(bms) for bms in duplicates.values()):,}個\n\n")

        # トップドメイン
        f.write("-"*70 + "\n")
        f.write("トップ50ドメイン\n")
        f.write("-"*70 + "\n")
        for i, (domain, count) in enumerate(analysis['domains'].most_common(50), 1):
            f.write(f"  {i:3d}. {count:5,}個 : {domain}\n")

        # フォルダ別
        f.write("\n" + "-"*70 + "\n")
        f.write("フォルダ別ブックマーク数\n")
        f.write("-"*70 + "\n")
        sorted_folders = sorted(analysis['folder_counts'].items(), key=lambda x: x[1], reverse=True)
        for i, (folder, count) in enumerate(sorted_folders, 1):
            f.write(f"  {i:3d}. {count:5,}個 : {folder}\n")

    print(f"詳細レポートを保存: {output_path}\n")

def main():
    input_file = 'bookmarks_2025_12_31.html'

    print("\n" + "="*70)
    print("Chromeブックマーク整理スクリプト")
    print("="*70 + "\n")

    # ステップ1: HTMLパース
    print(f"[1/5] ブックマークファイル読み込み中... ({input_file})")
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = BookmarkParser()
    parser.feed(html_content)
    bookmarks = parser.bookmarks
    print(f"      完了: {len(bookmarks):,}個のブックマークを検出\n")

    # ステップ2: 分析
    print("[2/5] ブックマーク分析中...")
    analysis = analyze_bookmarks(bookmarks)

    # ステップ3: 重複検出
    print("\n[3/5] 重複検出中...")
    duplicates = find_duplicates(bookmarks)

    # ステップ4: クリーニング
    print("\n[4/5] ブックマーククリーニング中...")
    cleaned_bookmarks = clean_bookmarks(bookmarks, duplicates)

    # ステップ5: 整理済みHTML生成
    print("[5/5] 整理済みHTMLファイル生成中...")
    output_path = generate_cleaned_html(input_file, cleaned_bookmarks)

    # レポート保存
    save_analysis_report(bookmarks, analysis, duplicates)

    print("="*70)
    print("処理完了！")
    print("="*70)
    print(f"\n整理済みファイル: {output_path}")
    print(f"元のファイル:     {input_file}")
    print(f"\n削減: {len(bookmarks) - len(cleaned_bookmarks):,}個のブックマークを削除")
    print(f"削減率: {(1 - len(cleaned_bookmarks)/len(bookmarks))*100:.2f}%\n")

if __name__ == '__main__':
    main()
