#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブックマークを内容分析して適切に分類するスクリプト
使用頻度が高い勉強関連は細かく分類、低頻度はまとめる
"""

import re
from html.parser import HTMLParser
from datetime import datetime
from collections import defaultdict


class SmartBookmarkCategorizer:
    """
    ブックマークをコンテンツ分析して適切に分類
    """

    def __init__(self):
        self.categories = defaultdict(list)

    def categorize_bookmark(self, url, title):
        """
        URLとタイトルから最適なカテゴリを判定
        """
        url_lower = url.lower()
        title_lower = title.lower()

        # === 勉強関連（細かく分類） ===

        # 英語学習
        english_keywords = ['英検', 'toefl', 'toeic', 'ielts', 'english', '英語', 'vocabulary', 'grammar',
                           'listening', 'speaking', 'writing', 'reading', '英作', '英単語']
        if any(k in title_lower for k in english_keywords):
            if '英検1級' in title or '英検１級' in title:
                return '英語学習/英検1級'
            elif any(k in title_lower for k in ['toefl', 'tpo']):
                return '英語学習/TOEFL'
            elif 'toeic' in title_lower:
                return '英語学習/TOEIC'
            elif '単語' in title or 'vocabulary' in title_lower or 'word' in title_lower:
                return '英語学習/英単語'
            elif '文法' in title or 'grammar' in title_lower:
                return '英語学習/英文法'
            elif 'リスニング' in title or 'listening' in title_lower:
                return '英語学習/リスニング'
            elif 'スピーキング' in title or 'speaking' in title_lower or '会話' in title or '二次試験' in title:
                return '英語学習/スピーキング'
            elif 'ライティング' in title or 'writing' in title_lower or '英作' in title:
                return '英語学習/ライティング'
            else:
                return '英語学習/その他'

        # 大学関連
        if 'letus.ed.tus.ac.jp' in url or 'tus.app.box.com' in url or '27.110.35.148' in url:
            if '物理' in title or 'physics' in title_lower:
                return '大学/物理'
            elif '数学' in title or 'math' in title_lower:
                return '大学/数学'
            elif '化学' in title or 'chemistry' in title_lower:
                return '大学/化学'
            elif '実験' in title or 'experiment' in title_lower:
                return '大学/実験'
            else:
                return '大学/授業・課題'

        # プログラミング（細分化）
        if any(domain in url for domain in ['qiita.com', 'zenn.dev', 'github.com', 'stackoverflow.com']):
            if 'python' in title_lower or 'python' in url_lower:
                return 'プログラミング/Python'
            elif any(k in title_lower for k in ['javascript', 'typescript', 'react', 'vue', 'node']):
                return 'プログラミング/Web開発'
            elif any(k in title_lower for k in ['c++', 'c言語', 'java', 'rust', 'go']):
                return 'プログラミング/その他言語'
            elif any(k in title_lower for k in ['claude', 'chatgpt', 'gpt', 'ai', '機械学習']):
                return 'プログラミング/AI・機械学習'
            elif 'git' in title_lower:
                return 'プログラミング/Git・バージョン管理'
            else:
                return 'プログラミング/その他'

        # 競技プログラミング
        if 'atcoder' in url or '競プロ' in title or 'アルゴリズム' in title:
            return 'プログラミング/競技プログラミング'

        # 数学
        if any(k in title_lower for k in ['数学', '微分', '積分', '線形代数', '統計', 'math']):
            if '線形代数' in title or 'linear algebra' in title_lower:
                return '数学/線形代数'
            elif '微分' in title or '積分' in title or 'calculus' in title_lower:
                return '数学/微積分'
            elif '統計' in title or 'statistics' in title_lower:
                return '数学/統計学'
            else:
                return '数学/その他'

        # 論文・学術
        if 'sciencedirect' in url or 'ncbi.nlm.nih.gov' in url or 'arxiv.org' in url:
            return '学術/論文'

        # 受験・入試
        if any(k in title for k in ['東進', '河合塾', '駿台', '模試', '過去問', '入試']):
            return '受験/過去問・模試'

        # === エンターテイメント（まとめる） ===

        # YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            if any(k in title for k in ['講義', '授業', '解説', 'tutorial', 'lecture']):
                return '動画/教育系YouTube'
            else:
                return '動画/YouTube'

        # 音楽
        if any(domain in url for domain in ['ufret.jp', 'chordwiki', 'lyrics.com', 'genius.com']):
            return 'エンターテイメント/音楽'

        # 映画・ドラマ
        if any(k in title_lower for k in ['映画', 'movie', 'cinema', 'film', 'netflix']):
            return 'エンターテイメント/映画・ドラマ'

        # === ツール ===

        # AI・ChatGPT
        if 'chatgpt.com' in url or 'claude.ai' in url or 'gemini.google.com' in url:
            return 'ツール/AI'

        # Google系
        if any(domain in url for domain in ['docs.google.com', 'drive.google.com', 'sheets.google.com']):
            return 'ツール/Google'

        # Wikipedia
        if 'wikipedia.org' in url:
            return 'リファレンス/Wikipedia'

        # その他の学習サイト
        if 'manabitimes.jp' in url:
            return '学習サイト/まなびタイムズ'

        if 'quizlet.com' in url:
            return 'ツール/暗記・クイズ'

        # === その他の学習リソース ===

        # note.nkmk.me (Python特化)
        if 'note.nkmk.me' in url:
            return 'プログラミング/Python'

        # まなびタイムズ（数学・物理）
        if 'manabitimes.jp' in url:
            if '物理' in title or 'physics' in title_lower:
                return '大学/物理'
            elif '化学' in title or 'chemistry' in title_lower:
                return '大学/化学'
            elif '微分' in title or '積分' in title or '線形代数' in title:
                return '数学/その他'
            else:
                return '学習サイト/まなびタイムズ'

        # === Google検索（内容で分類） ===
        if 'google.com/search' in url:
            # 検索キーワードから推測
            if any(k in title_lower for k in ['英語', 'english', 'vocabulary', 'grammar']):
                return '英語学習/検索'
            elif any(k in title_lower for k in ['数学', 'math', '微分', '積分', '統計']):
                return '数学/検索'
            elif any(k in title_lower for k in ['python', 'javascript', 'programming', 'code']):
                return 'プログラミング/検索'
            elif any(k in title_lower for k in ['物理', 'physics', '化学', 'chemistry']):
                return '大学/検索'
            else:
                return 'リファレンス/Google検索'

        # === その他（まとめる） ===

        # ショッピング
        if 'amazon' in url or '楽天' in url or ('yahoo' in url and 'shopping' in url):
            return 'その他/ショッピング'

        # ブログ・note（内容で分類）
        if 'note.com' in url or 'ameblo.jp' in url or 'hatena' in url:
            # noteの内容を分析
            if any(k in title_lower for k in ['英検', 'toefl', 'toeic', '英語']):
                return '英語学習/参考記事'
            elif any(k in title_lower for k in ['プログラミング', 'python', 'javascript']):
                return 'プログラミング/参考記事'
            elif any(k in title_lower for k in ['数学', '物理', '化学']):
                return '学術/参考記事'
            else:
                return 'その他/ブログ・記事'

        # 知恵袋
        if 'chiebukuro.yahoo.co.jp' in url:
            return 'リファレンス/Q&A'

        # 未分類
        return 'その他/未分類'


def smart_categorize_bookmarks(input_file, output_file):
    """
    ブックマークを賢く分類する
    """
    categorizer = SmartBookmarkCategorizer()

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # ブックマークを抽出
    bookmarks = re.findall(r'<DT><A HREF="([^"]+)"[^>]*>([^<]+)</A>', content, re.DOTALL)

    print(f"📊 {len(bookmarks)}個のブックマークを分析中...")

    # カテゴリごとに分類
    categories = defaultdict(list)
    for url, title in bookmarks:
        category = categorizer.categorize_bookmark(url, title)
        categories[category].append((url, title))

    # カテゴリ別の件数を表示
    print("\n=== カテゴリ別件数 ===")
    for category, items in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{len(items):4d}件 - {category}")

    # HTMLを生成
    html_lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file.',
        '     It will be read and overwritten.',
        '     DO NOT EDIT! -->',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>',
        '    <DT><H3 ADD_DATE="1704067200" LAST_MODIFIED="1735606800" PERSONAL_TOOLBAR_FOLDER="true">ブックマーク バー（整理済み）</H3>',
        '    <DL><p>'
    ]

    # カテゴリをソート（重要度順）
    category_order = [
        '英語学習/', '大学/', 'プログラミング/', '数学/', '学術/',
        '受験/', '動画/', 'ツール/', 'リファレンス/', '学習サイト/',
        'エンターテイメント/', 'その他/'
    ]

    sorted_categories = []
    for prefix in category_order:
        for cat in sorted(categories.keys()):
            if cat.startswith(prefix) and cat not in sorted_categories:
                sorted_categories.append(cat)

    # 大カテゴリごとに整理
    current_main_category = None

    for category in sorted_categories:
        items = categories[category]

        # カテゴリ階層を分解
        parts = category.split('/')

        # 大カテゴリが変わったら閉じる
        if len(parts) >= 2:
            main_cat = parts[0]
            if current_main_category and current_main_category != main_cat:
                html_lines.append('        </DL><p>')
                html_lines.append('    </DL><p>')

            # 新しい大カテゴリの開始
            if current_main_category != main_cat:
                html_lines.append(f'        <DT><H3 ADD_DATE="1704067200">{main_cat}</H3>')
                html_lines.append('        <DL><p>')
                current_main_category = main_cat

            # サブカテゴリ
            sub_cat = parts[1]
            html_lines.append(f'            <DT><H3 ADD_DATE="1704067200">{sub_cat}</H3>')
            html_lines.append('            <DL><p>')

            # ブックマーク
            for url, title in items:
                safe_url = url.replace('"', '&quot;')
                safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(f'                <DT><A HREF="{safe_url}" ADD_DATE="1704067200">{safe_title}</A>')

            html_lines.append('            </DL><p>')

        else:
            # トップレベルカテゴリ
            if current_main_category:
                html_lines.append('        </DL><p>')
                html_lines.append('    </DL><p>')
                current_main_category = None

            html_lines.append(f'        <DT><H3 ADD_DATE="1704067200">{category}</H3>')
            html_lines.append('        <DL><p>')

            for url, title in items:
                safe_url = url.replace('"', '&quot;')
                safe_title = title.replace('<', '&lt;').replace('>', '&gt;')
                html_lines.append(f'            <DT><A HREF="{safe_url}" ADD_DATE="1704067200">{safe_title}</A>')

            html_lines.append('        </DL><p>')

    # 最後のカテゴリを閉じる
    if current_main_category:
        html_lines.append('        </DL><p>')

    html_lines.append('    </DL><p>')
    html_lines.append('</DL><p>')

    # ファイルに書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_lines))

    print(f"\n✅ 整理済みブックマークを生成しました: {output_file}")
    print(f"   カテゴリ数: {len(categories)}")
    print(f"   ブックマーク数: {len(bookmarks)}")


if __name__ == '__main__':
    input_file = 'bookmarks_recent_2024.html'
    output_file = 'bookmarks_organized.html'

    smart_categorize_bookmarks(input_file, output_file)
