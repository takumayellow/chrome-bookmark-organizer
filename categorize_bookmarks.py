#!/usr/bin/env python3
"""
ブックマークをカテゴリー別に自動分類
"""

import re
from collections import defaultdict
from urllib.parse import urlparse
import sys

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

def categorize_bookmark(bm):
    """ブックマークをカテゴリー分け"""

    url = bm['url'].lower()
    title = bm['title'].lower()
    parsed = urlparse(url)
    domain = parsed.netloc

    # 動画
    if 'youtube.com' in domain or 'youtu.be' in domain or 'vimeo' in domain or 'nicovideo' in domain:
        return '動画・エンターテイメント'

    # 音楽
    if 'ufret' in domain or 'musescore' in domain or '音楽' in title or 'music' in title or 'chord' in title:
        return '音楽・楽譜'

    # プログラミング・技術
    if any(tech in domain for tech in ['github.com', 'qiita.com', 'zenn.dev', 'stackoverflow', 'atcoder.jp']):
        return 'プログラミング・技術'

    if any(word in title for word in ['python', 'javascript', 'プログラミング', 'コード', 'api', 'github', 'パソコン']):
        return 'プログラミング・技術'

    # ショッピング
    if 'amazon' in domain or 'rakuten' in domain or 'yahoo' in domain and 'shopping' in url:
        return 'ショッピング'

    # ChatGPT/AI
    if 'chatgpt' in domain or 'openai' in domain or 'claude' in domain:
        return 'AI・ChatGPT'

    # 学習・教育（数学・物理・化学など）
    if any(edu in domain for edu in ['manabitimes.jp', 'quizlet.com', 'toshin', 'exam', 'mathlandscape', 'momoyama-usagi']):
        return '学習・受験・教育'

    if any(word in title for word in ['数学', '物理', '化学', '勉強', '受験', 'math', 'physics', 'chemistry', '問題', '解答']):
        return '学習・受験・教育'

    if '27.110.35.148' in domain or 'letus.ed.tus.ac.jp' in domain:
        return '学習・受験・教育'

    # Wikipedia
    if 'wikipedia' in domain:
        return 'Wikipedia・辞書'

    # ニュース・ブログ
    if any(blog in domain for blog in ['note.com', 'ameblo.jp', 'hatenablog', 'blog']):
        return 'ブログ・記事'

    # 論文・アカデミック
    if 'arxiv' in domain or 'scholar' in domain or 'researchgate' in domain:
        return '論文・研究'

    # Google サービス
    if 'google.com' in domain:
        if 'drive' in url:
            return 'Googleドライブ'
        elif 'docs' in url or 'sheets' in url or 'slides' in url:
            return 'Googleドキュメント'
        else:
            return 'Google検索・サービス'

    # デフォルト
    return 'その他'

def save_categorized_bookmarks(categorized_bookmarks, output_file):
    """カテゴリー別に整理されたブックマークを保存"""

    html_header = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''

    html_footer = '''</DL><p>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_header)

        # カテゴリーをソート
        sorted_categories = sorted(categorized_bookmarks.keys())

        for category in sorted_categories:
            bookmarks = categorized_bookmarks[category]

            # カテゴリーフォルダ
            f.write(f'    <DT><H3 ADD_DATE="1703861181" LAST_MODIFIED="1766439577">{category} ({len(bookmarks)})</H3>\n')
            f.write('    <DL><p>\n')

            # ブックマーク
            for bm in bookmarks:
                url = bm['url'].replace('"', '&quot;')
                title = bm['title'].replace('<', '&lt;').replace('>', '&gt;')
                f.write(f'        <DT><A HREF="{url}">{title}</A>\n')

            f.write('    </DL><p>\n')

        f.write(html_footer)

def main():
    input_file = 'bookmarks_cleaned.html'
    output_file = 'bookmarks_categorized.html'

    print("="*70)
    print("ブックマーク自動カテゴリー分類")
    print("="*70)

    # 読み込み
    print(f"\n整理済みブックマークを読み込み中: {input_file}")
    bookmarks = parse_bookmarks_simple(input_file)
    print(f"  読み込み完了: {len(bookmarks)}個")

    # カテゴリー分け
    print(f"\nカテゴリー分類中...")
    categorized = defaultdict(list)

    for bm in bookmarks:
        category = categorize_bookmark(bm)
        categorized[category].append(bm)

    # 統計表示
    print(f"\n【カテゴリー別統計】")
    for category in sorted(categorized.keys()):
        count = len(categorized[category])
        percentage = count / len(bookmarks) * 100
        print(f"  {category:30s} : {count:5d}個 ({percentage:5.1f}%)")

    # 保存
    print(f"\nカテゴリー別ブックマークを保存中: {output_file}")
    save_categorized_bookmarks(categorized, output_file)

    print(f"\n{'='*70}")
    print("完了！")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
