#!/usr/bin/env python3
"""
最終レポート生成
"""

import re
import os
from collections import Counter
from urllib.parse import urlparse

def parse_bookmarks_simple(filepath):
    """シンプルなブックマークパーサー"""
    bookmarks = []

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    pattern = r'<DT><A HREF="([^"]*)"[^>]*>([^<]*)</A>'
    matches = re.findall(pattern, content)

    for url, title in matches:
        bookmarks.append({
            'url': url,
            'title': title.strip()
        })

    return bookmarks

def get_file_size_mb(filepath):
    """ファイルサイズ（MB）を取得"""
    return os.path.getsize(filepath) / (1024 * 1024)

def main():
    print("="*80)
    print("ブックマーク整理 最終レポート")
    print("="*80)
    print()

    # ファイル情報
    original_file = 'bookmarks_2025_12_31.html'
    cleaned_file = 'bookmarks_cleaned.html'
    categorized_file = 'bookmarks_categorized.html'

    # オリジナル
    original_bookmarks = parse_bookmarks_simple(original_file)
    original_size = get_file_size_mb(original_file)

    # クリーニング済み
    cleaned_bookmarks = parse_bookmarks_simple(cleaned_file)
    cleaned_size = get_file_size_mb(cleaned_file)

    # カテゴリー分類済み
    categorized_bookmarks = parse_bookmarks_simple(categorized_file)
    categorized_size = get_file_size_mb(categorized_file)

    # 統計
    removed_count = len(original_bookmarks) - len(cleaned_bookmarks)
    removal_rate = (removed_count / len(original_bookmarks)) * 100
    size_reduction = ((original_size - categorized_size) / original_size) * 100

    print("【整理結果サマリー】")
    print(f"  元のブックマーク数       : {len(original_bookmarks):,}個")
    print(f"  整理後のブックマーク数   : {len(cleaned_bookmarks):,}個")
    print(f"  削除したブックマーク数   : {removed_count:,}個")
    print(f"  削減率                   : {removal_rate:.1f}%")
    print()
    print(f"  元のファイルサイズ       : {original_size:.1f} MB")
    print(f"  整理後のファイルサイズ   : {categorized_size:.1f} MB")
    print(f"  ファイルサイズ削減率     : {size_reduction:.1f}%")
    print()

    print("【削除されたブックマークの内訳】")
    print(f"  - 重複URL: 約1,790個")
    print(f"  - chrome://系URL: 12個")
    print(f"  - file://系URL: 101個")
    print(f"  - localhost系URL: 6個")
    print()

    # ドメイン統計（整理後）
    domains = Counter()
    for bm in cleaned_bookmarks:
        try:
            parsed = urlparse(bm['url'])
            if parsed.netloc:
                domains[parsed.netloc] += 1
        except:
            pass

    print("【整理後のトップ15ドメイン】")
    for i, (domain, count) in enumerate(domains.most_common(15), 1):
        percentage = (count / len(cleaned_bookmarks)) * 100
        print(f"  {i:2d}. {domain:40s} : {count:4d}個 ({percentage:4.1f}%)")
    print()

    print("【生成されたファイル】")
    print(f"  1. {cleaned_file}")
    print(f"     - 重複・無効URLを削除した整理済みブックマーク")
    print(f"     - {len(cleaned_bookmarks):,}個のブックマーク")
    print()
    print(f"  2. {categorized_file}")
    print(f"     - カテゴリー別に自動分類されたブックマーク")
    print(f"     - 13のカテゴリーに分類")
    print(f"     - 最も見やすく、おすすめ！")
    print()

    print("【使い方】")
    print("  1. Chromeを開く")
    print("  2. ブックマークマネージャー（Ctrl+Shift+O）を開く")
    print("  3. 右上のメニュー（︙）から「ブックマークをインポート」を選択")
    print(f"  4. 「{categorized_file}」を選択してインポート")
    print()

    print("【注意事項】")
    print("  - インポート前に現在のブックマークをエクスポートしてバックアップ推奨")
    print("  - カテゴリー分類は自動なので、必要に応じて手動で調整してください")
    print()

    # レポートファイルに保存
    report_file = 'FINAL_REPORT.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ブックマーク整理 最終レポート\n")
        f.write("="*80 + "\n\n")

        f.write("【整理結果サマリー】\n")
        f.write(f"  元のブックマーク数       : {len(original_bookmarks):,}個\n")
        f.write(f"  整理後のブックマーク数   : {len(cleaned_bookmarks):,}個\n")
        f.write(f"  削除したブックマーク数   : {removed_count:,}個\n")
        f.write(f"  削減率                   : {removal_rate:.1f}%\n\n")

        f.write(f"  元のファイルサイズ       : {original_size:.1f} MB\n")
        f.write(f"  整理後のファイルサイズ   : {categorized_size:.1f} MB\n")
        f.write(f"  ファイルサイズ削減率     : {size_reduction:.1f}%\n\n")

        f.write("【削除されたブックマークの内訳】\n")
        f.write("  - 重複URL: 約1,790個\n")
        f.write("  - chrome://系URL: 12個\n")
        f.write("  - file://系URL: 101個\n")
        f.write("  - localhost系URL: 6個\n\n")

        f.write("【整理後のトップ15ドメイン】\n")
        for i, (domain, count) in enumerate(domains.most_common(15), 1):
            percentage = (count / len(cleaned_bookmarks)) * 100
            f.write(f"  {i:2d}. {domain:40s} : {count:4d}個 ({percentage:4.1f}%)\n")
        f.write("\n")

        f.write("【生成されたファイル】\n")
        f.write(f"  1. {cleaned_file}\n")
        f.write("     - 重複・無効URLを削除した整理済みブックマーク\n")
        f.write(f"     - {len(cleaned_bookmarks):,}個のブックマーク\n\n")

        f.write(f"  2. {categorized_file}\n")
        f.write("     - カテゴリー別に自動分類されたブックマーク\n")
        f.write("     - 13のカテゴリーに分類\n")
        f.write("     - 最も見やすく、おすすめ！\n\n")

        f.write("【使い方】\n")
        f.write("  1. Chromeを開く\n")
        f.write("  2. ブックマークマネージャー（Ctrl+Shift+O）を開く\n")
        f.write("  3. 右上のメニュー（︙）から「ブックマークをインポート」を選択\n")
        f.write(f"  4. 「{categorized_file}」を選択してインポート\n\n")

        f.write("【注意事項】\n")
        f.write("  - インポート前に現在のブックマークをエクスポートしてバックアップ推奨\n")
        f.write("  - カテゴリー分類は自動なので、必要に応じて手動で調整してください\n")

    print(f"レポートを保存: {report_file}")
    print()
    print("="*80)
    print("整理完了！")
    print("="*80)

if __name__ == '__main__':
    main()
