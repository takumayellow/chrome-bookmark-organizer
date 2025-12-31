#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブックマーク階層構造ビューア作成スクリプト
Chrome/Firefox形式のHTMLブックマークを読み込んで、
階層構造を視覚的に表示するWebページを生成します。
"""

import re
from html.parser import HTMLParser
from datetime import datetime


class BookmarkParser(HTMLParser):
    """
    HTMLブックマークをパースするクラス
    """

    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.current_folder = []
        self.folder_stack = []
        self.in_dl = 0
        self.in_h3 = False
        self.in_a = False
        self.current_text = ''
        self.current_url = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'dl':
            self.in_dl += 1
            if self.in_dl > 1:
                # 新しいフォルダの開始
                if self.current_folder:
                    self.folder_stack.append(list(self.current_folder))

        elif tag == 'h3':
            self.in_h3 = True
            self.current_text = ''

        elif tag == 'a':
            self.in_a = True
            self.current_text = ''
            for attr, value in attrs:
                if attr == 'href':
                    self.current_url = value

    def handle_endtag(self, tag):
        if tag == 'dl':
            self.in_dl -= 1
            if self.folder_stack:
                self.current_folder = self.folder_stack.pop()

        elif tag == 'h3':
            self.in_h3 = False
            if self.current_text:
                self.current_folder.append(self.current_text.strip())

        elif tag == 'a':
            self.in_a = False
            if self.current_text and self.current_url:
                folder_path = ' > '.join(self.current_folder) if self.current_folder else 'ルート'
                self.bookmarks.append({
                    'folder': folder_path,
                    'name': self.current_text.strip(),
                    'url': self.current_url,
                    'level': len(self.current_folder)
                })

    def handle_data(self, data):
        if self.in_h3 or self.in_a:
            self.current_text += data


def parse_bookmarks(html_content):
    """
    ブックマークHTMLをパースして階層構造を抽出
    """
    parser = BookmarkParser()
    parser.feed(html_content)
    return parser.bookmarks


def build_folder_tree(bookmarks):
    """
    ブックマークからフォルダツリーを構築
    """
    folders = {}

    for bookmark in bookmarks:
        folder_path = bookmark['folder']
        if folder_path not in folders:
            folders[folder_path] = []
        folders[folder_path].append(bookmark)

    return folders


def generate_html_viewer(bookmarks, folders):
    """
    HTMLビューアを生成
    """
    total_bookmarks = len(bookmarks)
    total_folders = len(folders)

    # フォルダをソート
    sorted_folders = sorted(folders.keys())

    # HTML本体を生成
    folder_html = []
    for folder_path in sorted_folders:
        folder_items = folders[folder_path]
        folder_id = f"folder_{abs(hash(folder_path))}"
        level = folder_path.count(' > ')

        folder_html.append(f'<div class="folder level-{level}">')
        folder_html.append(f'  <div class="folder-header" onclick="toggleFolder(\'{folder_id}\')">')
        folder_html.append(f'    <span class="folder-icon">📁</span>')
        folder_html.append(f'    <span class="folder-name">{folder_path}</span>')
        folder_html.append(f'    <span class="bookmark-count">({len(folder_items)} items)</span>')
        folder_html.append(f'  </div>')
        folder_html.append(f'  <div class="folder-content" id="{folder_id}">')

        for item in folder_items:
            safe_url = item['url'].replace('"', '&quot;')
            safe_name = item['name'].replace('<', '&lt;').replace('>', '&gt;')
            folder_html.append(f'    <div class="bookmark">')
            folder_html.append(f'      <span class="bookmark-icon">🔖</span>')
            folder_html.append(f'      <a href="{safe_url}" target="_blank" class="bookmark-link">{safe_name}</a>')
            folder_html.append(f'    </div>')

        folder_html.append(f'  </div>')
        folder_html.append(f'</div>')

    tree_html = '\n'.join(folder_html)

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
            max-width: 1200px;
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
            max-height: 70vh;
            overflow-y: auto;
        }}

        .folder {{
            margin: 10px 0;
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
        }}

        .folder-header:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}

        .folder-icon {{
            font-size: 1.3em;
        }}

        .folder-name {{
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }}

        .bookmark-count {{
            color: #6c757d;
            font-size: 0.9em;
            font-weight: normal;
        }}

        .folder-content {{
            margin-left: 20px;
            margin-top: 5px;
            border-left: 2px dashed #dee2e6;
            padding-left: 15px;
            display: block;
        }}

        .folder-content.collapsed {{
            display: none;
        }}

        .bookmark {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            margin: 5px 0;
            background: #ffffff;
            border-radius: 6px;
            border: 1px solid #e9ecef;
            transition: all 0.2s ease;
        }}

        .bookmark:hover {{
            background: #f1f3f5;
            border-color: #667eea;
            transform: translateX(3px);
        }}

        .bookmark-icon {{
            font-size: 1.1em;
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
                return;
            }}

            bookmarks.forEach(bookmark => {{
                const text = bookmark.textContent.toLowerCase();
                if (text.includes(searchTerm)) {{
                    bookmark.style.display = 'flex';
                    // 親フォルダも表示
                    let parent = bookmark.closest('.folder-content');
                    while (parent) {{
                        parent.style.display = 'block';
                        parent.classList.remove('collapsed');
                        parent = parent.parentElement.closest('.folder-content');
                    }}
                }} else {{
                    bookmark.style.display = 'none';
                }}
            }});
        }}

        // 初期状態: すべて折りたたむ
        window.onload = function() {{
            collapseAll();
        }};
    </script>
</body>
</html>
"""

    return html_template


def create_viewer_html(bookmark_file, output_file):
    """
    ブックマークビューアHTMLを生成
    """
    # ブックマークHTMLを読み込み
    with open(bookmark_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # パース
    bookmarks = parse_bookmarks(content)
    folders = build_folder_tree(bookmarks)

    # HTML生成
    html_content = generate_html_viewer(bookmarks, folders)

    # ファイルに書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ ブックマークビューアを生成しました: {output_file}")
    print(f"📊 統計:")
    print(f"   - フォルダ数: {len(folders)}")
    print(f"   - ブックマーク数: {len(bookmarks)}")


if __name__ == '__main__':
    input_file = 'bookmarks_2025_12_31_cleaned.html'
    output_file = 'index.html'

    create_viewer_html(input_file, output_file)
