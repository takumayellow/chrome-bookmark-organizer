#!/usr/bin/env python3
"""
ブックマークをWebビュー用に変換
"""

import re
from collections import defaultdict
from urllib.parse import urlparse
import json

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

    # 学習・教育
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

    return 'その他'

def generate_web_view(categorized_bookmarks, output_file):
    """Webビュー用HTMLを生成"""

    html_header = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>整理済みブックマーク - Chrome Bookmark Organizer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            color: #666;
            margin-top: 5px;
        }

        .content {
            padding: 40px;
        }

        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #667eea;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .search-box:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }

        .category {
            margin-bottom: 40px;
        }

        .category-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }

        .category-header:hover {
            transform: translateX(5px);
        }

        .category-title {
            font-size: 1.5em;
            font-weight: bold;
        }

        .category-count {
            background: rgba(255,255,255,0.3);
            padding: 5px 15px;
            border-radius: 20px;
        }

        .bookmarks {
            margin-top: 10px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            display: none;
        }

        .bookmarks.active {
            display: block;
        }

        .bookmark {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
        }

        .bookmark:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .bookmark a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            display: block;
            margin-bottom: 5px;
        }

        .bookmark a:hover {
            color: #764ba2;
        }

        .bookmark-url {
            color: #999;
            font-size: 0.9em;
            word-break: break-all;
        }

        footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
        }

        .expand-all {
            margin-bottom: 20px;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }

        .expand-all:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔖 整理済みブックマーク</h1>
            <p class="subtitle">Chrome Bookmark Organizer - カテゴリー別表示</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">8,438</div>
                <div class="stat-label">元のブックマーク数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">6,529</div>
                <div class="stat-label">整理後のブックマーク数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">-22.6%</div>
                <div class="stat-label">削減率</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">13</div>
                <div class="stat-label">カテゴリー数</div>
            </div>
        </div>

        <div class="content">
            <input type="text" class="search-box" id="search" placeholder="🔍 ブックマークを検索..." onkeyup="searchBookmarks()">
            <button class="expand-all" onclick="toggleAll()">すべて展開/折りたたみ</button>
            <div id="categories">
'''

    html_footer = '''
            </div>
        </div>

        <footer>
            <p>Chrome Bookmark Organizer - 自動整理ツール</p>
            <p style="margin-top: 10px; font-size: 0.9em;">元: 8,438個 → 整理後: 6,529個（-22.6%削減）</p>
        </footer>
    </div>

    <script>
        function toggleCategory(element) {
            const bookmarks = element.nextElementSibling;
            bookmarks.classList.toggle('active');
        }

        function toggleAll() {
            document.querySelectorAll('.bookmarks').forEach(b => {
                b.classList.toggle('active');
            });
        }

        function searchBookmarks() {
            const searchText = document.getElementById('search').value.toLowerCase();
            let foundAny = false;

            document.querySelectorAll('.category').forEach(category => {
                const bookmarks = category.querySelectorAll('.bookmark');
                let foundInCategory = false;

                bookmarks.forEach(bookmark => {
                    const text = bookmark.textContent.toLowerCase();
                    if (text.includes(searchText)) {
                        bookmark.style.display = 'block';
                        foundInCategory = true;
                        foundAny = true;
                    } else {
                        bookmark.style.display = 'none';
                    }
                });

                if (searchText && foundInCategory) {
                    category.querySelector('.bookmarks').classList.add('active');
                } else if (!searchText) {
                    category.querySelector('.bookmarks').classList.remove('active');
                }

                category.style.display = (!searchText || foundInCategory) ? 'block' : 'none';
            });
        }
    </script>
</body>
</html>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_header)

        # カテゴリーをソート
        sorted_categories = sorted(categorized_bookmarks.items(), key=lambda x: len(x[1]), reverse=True)

        for category, bookmarks in sorted_categories:
            f.write(f'''
                <div class="category">
                    <div class="category-header" onclick="toggleCategory(this)">
                        <span class="category-title">{category}</span>
                        <span class="category-count">{len(bookmarks)}個</span>
                    </div>
                    <div class="bookmarks">
''')

            for bm in bookmarks[:100]:  # 各カテゴリー最初の100件のみ表示
                url = bm['url'].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                title = bm['title'].replace('<', '&lt;').replace('>', '&gt;')

                f.write(f'''
                        <div class="bookmark">
                            <a href="{url}" target="_blank">{title if title else '(タイトルなし)'}</a>
                            <div class="bookmark-url">{url}</div>
                        </div>
''')

            if len(bookmarks) > 100:
                f.write(f'''
                        <div style="text-align: center; padding: 20px; color: #999;">
                            ... さらに {len(bookmarks) - 100}個のブックマーク
                        </div>
''')

            f.write('''
                    </div>
                </div>
''')

        f.write(html_footer)

def main():
    print("Web表示用HTMLを生成中...")

    # ブックマークを読み込み
    bookmarks = parse_bookmarks_simple('bookmarks_cleaned.html')
    print(f"  {len(bookmarks)}個のブックマークを読み込みました")

    # カテゴリー分類
    categorized = defaultdict(list)
    for bm in bookmarks:
        category = categorize_bookmark(bm)
        categorized[category].append(bm)

    # Web表示用HTMLを生成
    generate_web_view(categorized, 'bookmarks_web.html')
    print(f"  bookmarks_web.html を生成しました")

    print("\n完了！")

if __name__ == '__main__':
    main()
