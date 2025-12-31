#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブックマークの階層構造を正確に再現するビューア作成スクリプト
元のフォルダ構造を保持したまま、ツリー形式で表示します。
"""

import re
from html.parser import HTMLParser
from datetime import datetime


class HierarchicalBookmarkParser(HTMLParser):
    """
    ブックマークの階層構造を正確に解析するパーサー
    """

    def __init__(self):
        super().__init__()
        self.tree = {'name': 'root', 'type': 'folder', 'children': [], 'level': -1}
        self.current_path = [self.tree]
        self.pending_folder = None
        self.in_h3 = False
        self.in_a = False
        self.current_text = ''
        self.current_attrs = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h3':
            self.in_h3 = True
            self.current_text = ''
            self.current_attrs = attrs_dict
            self.pending_folder = {
                'type': 'folder',
                'children': [],
                'level': len(self.current_path) - 1,
                'attrs': attrs_dict
            }

        elif tag == 'dl':
            # 新しい階層の開始
            if self.pending_folder:
                self.current_path[-1]['children'].append(self.pending_folder)
                self.current_path.append(self.pending_folder)
                self.pending_folder = None

        elif tag == 'a':
            self.in_a = True
            self.current_text = ''
            self.current_attrs = attrs_dict

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_h3 = False
            if self.pending_folder:
                self.pending_folder['name'] = self.current_text.strip()

        elif tag == 'a':
            self.in_a = False
            bookmark = {
                'type': 'bookmark',
                'name': self.current_text.strip(),
                'url': self.current_attrs.get('href', ''),
                'level': len(self.current_path) - 1
            }
            self.current_path[-1]['children'].append(bookmark)

        elif tag == 'dl':
            # 階層を一つ戻る
            if len(self.current_path) > 1:
                self.current_path.pop()

    def handle_data(self, data):
        if self.in_h3 or self.in_a:
            self.current_text += data


def analyze_folder_names(tree):
    """
    「新しいフォルダ」「仮置き」などを分析して適切な名前を提案
    """
    def analyze_children(folder):
        if folder['type'] != 'folder':
            return

        # 子要素を分析
        bookmarks = [c for c in folder.get('children', []) if c['type'] == 'bookmark']

        # フォルダ名が不適切な場合、内容から推測
        if folder.get('name') in ['新しいフォルダ', '仮置き', '名前のないフォルダ', '']:
            suggested_name = suggest_folder_name(bookmarks)
            if suggested_name:
                folder['suggested_name'] = suggested_name

        # 再帰的に子フォルダも処理
        for child in folder.get('children', []):
            if child['type'] == 'folder':
                analyze_children(child)

    analyze_children(tree)


def suggest_folder_name(bookmarks):
    """
    ブックマークの内容からフォルダ名を推測
    """
    if not bookmarks:
        return None

    # URLのドメインやタイトルから共通要素を抽出
    urls = [b['url'] for b in bookmarks if b.get('url')]
    names = [b['name'] for b in bookmarks]

    # ドメインの頻度を調べる
    domains = {}
    for url in urls:
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            domains[domain] = domains.get(domain, 0) + 1

    # 最も多いドメインからカテゴリ推測
    if domains:
        top_domain = max(domains.items(), key=lambda x: x[1])[0]

        # ドメインからカテゴリを推測
        if 'github' in top_domain:
            return 'GitHub関連'
        elif 'youtube' in top_domain or 'youtu.be' in top_domain:
            return 'YouTube'
        elif 'qiita' in top_domain:
            return 'Qiita記事'
        elif 'zenn' in top_domain:
            return 'Zenn記事'
        elif 'twitter' in top_domain or 'x.com' in top_domain:
            return 'Twitter/X'
        elif 'note' in top_domain:
            return 'note'
        elif 'amazon' in top_domain:
            return 'Amazon'
        elif any(word in top_domain for word in ['google', 'docs', 'drive', 'sheet']):
            return 'Google関連'

    # タイトルから共通キーワードを探す
    keywords = {}
    for name in names[:5]:  # 最初の5件から分析
        words = re.findall(r'[ぁ-んァ-ヶー一-龯a-zA-Z]+', name)
        for word in words:
            if len(word) > 1:
                keywords[word] = keywords.get(word, 0) + 1

    if keywords:
        top_keyword = max(keywords.items(), key=lambda x: x[1])[0]
        if keywords[top_keyword] >= 2:  # 2回以上出現
            return f'{top_keyword}関連'

    return None


def generate_html_tree_hierarchical(node, level=0):
    """
    正しい階層構造でHTMLツリーを生成
    """
    html = []

    if node['type'] == 'folder':
        folder_name = node.get('suggested_name', node.get('name', 'フォルダ'))
        original_name = node.get('name', '')

        if original_name in ['新しいフォルダ', '仮置き', '名前のないフォルダ', '']:
            display_name = f"{folder_name} <span style='color:#999;font-size:0.8em;'>(元: {original_name})</span>"
        else:
            display_name = folder_name

        children = node.get('children', [])
        bookmark_count = count_items(children)

        if children:  # 空フォルダは表示しない
            folder_id = f"folder_{abs(hash(folder_name + str(level)))}"

            html.append(f'<div class="folder level-{level}">')
            html.append(f'  <div class="folder-header" onclick="toggleFolder(\'{folder_id}\')">')
            html.append(f'    <span class="folder-icon">📁</span>')
            html.append(f'    <span class="folder-name">{display_name}</span>')
            html.append(f'    <span class="bookmark-count">({bookmark_count} items)</span>')
            html.append(f'  </div>')
            html.append(f'  <div class="folder-content" id="{folder_id}">')

            # 子要素を再帰的に生成
            for child in children:
                html.append(generate_html_tree_hierarchical(child, level + 1))

            html.append(f'  </div>')
            html.append(f'</div>')

    elif node['type'] == 'bookmark':
        safe_url = node['url'].replace('"', '&quot;')
        safe_name = node['name'].replace('<', '&lt;').replace('>', '&gt;')

        html.append(f'<div class="bookmark level-{level}">')
        html.append(f'  <span class="bookmark-icon">🔖</span>')
        html.append(f'  <a href="{safe_url}" target="_blank" class="bookmark-link">{safe_name}</a>')
        html.append(f'</div>')

    return '\n'.join(html)


def count_items(children):
    """
    フォルダ内のアイテム数をカウント（再帰的）
    """
    count = 0
    for child in children:
        if child['type'] == 'bookmark':
            count += 1
        elif child['type'] == 'folder':
            count += count_items(child.get('children', []))
    return count


def count_all_bookmarks(tree):
    """
    全ブックマーク数をカウント
    """
    count = 0
    if tree['type'] == 'bookmark':
        return 1
    for child in tree.get('children', []):
        count += count_all_bookmarks(child)
    return count


def count_all_folders(tree):
    """
    全フォルダ数をカウント
    """
    count = 0
    if tree['type'] == 'folder':
        count = 1
    for child in tree.get('children', []):
        count += count_all_folders(child)
    return count


def create_hierarchical_viewer(input_file, output_file):
    """
    階層構造を保持したブックマークビューアを生成
    """
    print("📖 ブックマークファイルを読み込んでいます...")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("🔍 階層構造を解析しています...")
    parser = HierarchicalBookmarkParser()
    parser.feed(content)

    tree = parser.tree

    print("🏷️  フォルダ名を分析しています...")
    analyze_folder_names(tree)

    print("📝 HTMLを生成しています...")
    tree_html = ''
    for child in tree.get('children', []):
        tree_html += generate_html_tree_hierarchical(child)

    total_bookmarks = count_all_bookmarks(tree)
    total_folders = count_all_folders(tree) - 1  # root除く

    # 完全なHTMLページを生成
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ブックマーク階層構造ビューア</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            font-size: 1.1em;
        }}

        .stat-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .content {{
            padding: 30px;
            max-height: 75vh;
            overflow-y: auto;
        }}

        .folder {{
            margin: 8px 0;
            margin-left: 20px;
            border-left: 2px solid #e9ecef;
            padding-left: 10px;
        }}

        .folder.level-0 {{
            margin-left: 0;
            border-left: none;
            padding-left: 0;
        }}

        .folder-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 4px solid #667eea;
            margin-bottom: 5px;
        }}

        .folder-header:hover {{
            background: #e9ecef;
            transform: translateX(3px);
        }}

        .folder-icon {{
            font-size: 1.2em;
            min-width: 24px;
        }}

        .folder-name {{
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }}

        .bookmark-count {{
            color: #6c757d;
            font-size: 0.85em;
            font-weight: normal;
        }}

        .folder-content {{
            display: block;
            margin-top: 5px;
        }}

        .folder-content.collapsed {{
            display: none;
        }}

        .bookmark {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            margin: 4px 0;
            margin-left: 20px;
            background: #ffffff;
            border-radius: 6px;
            border: 1px solid #e9ecef;
            transition: all 0.2s ease;
        }}

        .bookmark:hover {{
            background: #f1f3f5;
            border-color: #667eea;
            transform: translateX(3px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }}

        .bookmark-icon {{
            font-size: 1em;
            min-width: 20px;
        }}

        .bookmark-link {{
            color: #495057;
            text-decoration: none;
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .bookmark-link:hover {{
            color: #667eea;
        }}

        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 15px;
            justify-content: center;
        }}

        button {{
            padding: 10px 25px;
            border: none;
            border-radius: 6px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }}

        button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}

        .search-box {{
            padding: 20px 30px;
            background: #fff;
            border-bottom: 1px solid #dee2e6;
        }}

        .search-input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            transition: all 0.3s ease;
        }}

        .search-input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}

        ::-webkit-scrollbar {{
            width: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}

        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 ブックマーク階層構造ビューア</h1>
            <div class="stats">
                <div class="stat-item">
                    <span>📁 フォルダ数:</span>
                    <strong>{total_folders}</strong>
                </div>
                <div class="stat-item">
                    <span>🔖 ブックマーク数:</span>
                    <strong>{total_bookmarks}</strong>
                </div>
                <div class="stat-item">
                    <span>📅 生成日:</span>
                    <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong>
                </div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" class="search-input" id="searchInput" placeholder="🔍 ブックマークを検索..." onkeyup="searchBookmarks()">
        </div>

        <div class="controls">
            <button onclick="expandAll()">すべて展開</button>
            <button onclick="collapseAll()">すべて折りたたむ</button>
        </div>

        <div class="content" id="bookmarkTree">
{tree_html}
        </div>
    </div>

    <script>
        function toggleFolder(folderId) {{
            const folder = document.getElementById(folderId);
            folder.classList.toggle('collapsed');
        }}

        function expandAll() {{
            document.querySelectorAll('.folder-content').forEach(folder => {{
                folder.classList.remove('collapsed');
            }});
        }}

        function collapseAll() {{
            document.querySelectorAll('.folder-content').forEach(folder => {{
                folder.classList.add('collapsed');
            }});
        }}

        function searchBookmarks() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const bookmarks = document.querySelectorAll('.bookmark');
            const folders = document.querySelectorAll('.folder');

            if (searchTerm === '') {{
                bookmarks.forEach(b => b.style.display = 'flex');
                folders.forEach(f => f.style.display = 'block');
                expandAll();
                return;
            }}

            // 全て非表示にする
            bookmarks.forEach(b => b.style.display = 'none');
            folders.forEach(f => f.style.display = 'none');

            // マッチするブックマークとその親フォルダを表示
            bookmarks.forEach(bookmark => {{
                const text = bookmark.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    bookmark.style.display = 'flex';

                    // 親フォルダを全て表示
                    let parent = bookmark.parentElement;
                    while (parent && parent.classList) {{
                        if (parent.classList.contains('folder')) {{
                            parent.style.display = 'block';
                        }}
                        if (parent.classList.contains('folder-content')) {{
                            parent.classList.remove('collapsed');
                            parent.style.display = 'block';
                        }}
                        parent = parent.parentElement;
                    }}
                }}
            }});
        }}

        // 初期状態: 第1階層のみ展開
        window.onload = function() {{
            collapseAll();
            // 第1階層のフォルダのみ展開
            document.querySelectorAll('.folder.level-0 > .folder-content').forEach(folder => {{
                folder.classList.remove('collapsed');
            }});
        }};
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"\n✅ ブックマークビューアを生成しました: {output_file}")
    print(f"📊 統計:")
    print(f"   - フォルダ数: {total_folders}")
    print(f"   - ブックマーク数: {total_bookmarks}")


if __name__ == '__main__':
    input_file = 'bookmarks_recent_2024.html'
    output_file = 'index.html'

    create_hierarchical_viewer(input_file, output_file)
