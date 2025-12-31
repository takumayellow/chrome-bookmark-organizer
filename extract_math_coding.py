#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元のディレクトリ構造を保持したまま、数学とコーディング関連のフォルダのみを抽出
重複を削除
"""

import re
from html.parser import HTMLParser
from collections import defaultdict


class MathCodingExtractor(HTMLParser):
    """
    元の構造を保持したまま数学・コーディングのフォルダを抽出
    """

    def __init__(self):
        super().__init__()
        self.tree = {'name': 'root', 'type': 'folder', 'children': []}
        self.folder_stack = [self.tree]
        self.current_dt_level = 0
        self.in_h3 = False
        self.in_a = False
        self.current_text = ''
        self.current_attrs = {}
        self.pending_dt = None
        self.seen_urls = set()  # 重複チェック用
        self.stats = {'total_folders': 0, 'kept_folders': 0, 'total_bookmarks': 0, 'kept_bookmarks': 0, 'duplicates': 0}

    def is_math_or_coding_folder(self, folder_name):
        """
        数学またはコーディング関連のフォルダか判定
        """
        folder_lower = folder_name.lower()

        # 数学関連キーワード
        math_keywords = [
            '数学', 'math', '微分', '積分', '線形代数', 'algebra',
            '統計', 'statistics', 'calculus', '解析', 'analysis',
            'latex', '数式'
        ]

        # コーディング・CS関連キーワード（より広範に）
        coding_keywords = [
            # 一般
            'プログラミング', 'programming', 'python', 'javascript', 'java',
            'c++', 'c言語', 'コード', 'code', 'coding', 'web開発', 'web班',
            # ツール・サービス
            'web', 'react', 'vue', 'node', 'git', 'github', 'gitlab',
            'vscode', 'vim', 'emacs', 'ide', 'copilot', 'cline',
            'slack', 'notion', 'デビン', 'devin',
            # 競プロ
            'atcoder', 'codeforces', 'leetcode', '競プロ', '競技プログラミング',
            'アルゴリズム', 'algorithm', 'データ構造', 'data structure',
            # AI・ML
            'ai', '機械学習', 'ml', 'deep learning', 'chatgpt', 'claude',
            'gpt', 'llm', 'gemini', 'codex', 'glm',
            # 情報系
            '情報', 'computer science', 'cs', '情報工学', 'vr',
            '因果推論', '論文',
            # コミュニティ
            'qiita', 'zenn', 'stackoverflow',
            # モダン技術
            'モダン', 'フレームワーク', 'ライブラリ', '制作班'
        ]

        # 除外キーワード（明らかに関係ないもの）
        exclude_keywords = [
            '英語', 'english', 'toefl', 'toeic', '英検',
            '物理', 'physics', '化学', 'chemistry',
            '音楽', 'music', '映画', 'movie',
            'キューブ', 'cube', 'ルービック',
            'フォトバック', 'photo', '写真'
        ]

        # 除外チェック
        if any(k in folder_lower for k in exclude_keywords):
            return False

        # 数学・コーディングチェック
        if any(k in folder_lower for k in math_keywords + coding_keywords):
            return True

        # 「新しいフォルダ」は中身を見て判定するため一旦保持
        if '新しいフォルダ' in folder_name or folder_name == '':
            return True

        return False

    def is_math_or_coding_bookmark(self, url, title):
        """
        数学またはコーディング関連のブックマークか判定
        """
        url_lower = url.lower()
        title_lower = title.lower()

        # コーディング関連ドメイン
        coding_domains = [
            'qiita.com', 'zenn.dev', 'github.com', 'stackoverflow.com',
            'atcoder.jp', 'note.nkmk.me', 'chatgpt.com', 'claude.ai',
            'leetcode.com', 'hackerrank.com', 'codewars.com'
        ]

        if any(domain in url_lower for domain in coding_domains):
            return True

        # 数学関連ドメイン
        math_domains = [
            'mathlandscape.com', 'manabitimes.jp', 'mathworld.wolfram.com'
        ]

        if any(domain in url_lower for domain in math_domains):
            # まなびタイムズは数学のみ
            if 'manabitimes.jp' in url_lower:
                if any(k in title_lower for k in ['数学', 'math', '微分', '積分', '線形代数', '統計']):
                    return True
                else:
                    return False
            return True

        # タイトル・URLキーワードチェック
        math_coding_keywords = [
            # 数学
            '数学', 'math', '微分', '積分', '線形代数', 'calculus', 'algebra',
            '統計', 'statistics', '確率', 'probability',
            # プログラミング
            'プログラミング', 'programming', 'python', 'javascript', 'java',
            'c++', 'react', 'vue', 'node', 'typescript', 'git',
            'アルゴリズム', 'algorithm', 'data structure', 'データ構造',
            '競プロ', 'atcoder', 'leetcode',
            'ai', '機械学習', 'deep learning', 'neural network',
            'web開発', 'backend', 'frontend', 'api', 'database'
        ]

        if any(k in title_lower or k in url_lower for k in math_coding_keywords):
            return True

        return False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'dt':
            self.pending_dt = {'attrs': attrs_dict}

        elif tag == 'h3':
            self.in_h3 = True
            self.current_text = ''
            self.current_attrs = attrs_dict

        elif tag == 'dl':
            # DLは新しい階層の開始を示す
            pass

        elif tag == 'a':
            self.in_a = True
            self.current_text = ''
            self.current_attrs = attrs_dict

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.in_h3 = False
            folder_name = self.current_text.strip()
            self.stats['total_folders'] += 1

            # 数学・コーディング関連フォルダのみ保持
            if self.is_math_or_coding_folder(folder_name):
                self.stats['kept_folders'] += 1
                new_folder = {
                    'type': 'folder',
                    'name': folder_name,
                    'children': [],
                    'attrs': self.current_attrs
                }
                self.folder_stack[-1]['children'].append(new_folder)
                self.folder_stack.append(new_folder)
            else:
                # このフォルダは無視（NULLフォルダを追加）
                null_folder = {
                    'type': 'null_folder',
                    'name': folder_name,
                    'children': []
                }
                self.folder_stack.append(null_folder)

        elif tag == 'a':
            self.in_a = False
            url = self.current_attrs.get('href', '')
            title = self.current_text.strip()
            self.stats['total_bookmarks'] += 1

            # 親フォルダがNULLフォルダなら無視
            if self.folder_stack[-1].get('type') == 'null_folder':
                return

            # 重複チェック
            if url in self.seen_urls:
                self.stats['duplicates'] += 1
                return

            # 数学・コーディング関連のみ保持
            if self.is_math_or_coding_bookmark(url, title):
                self.seen_urls.add(url)
                self.stats['kept_bookmarks'] += 1
                bookmark = {
                    'type': 'bookmark',
                    'name': title,
                    'url': url,
                    'attrs': self.current_attrs
                }
                self.folder_stack[-1]['children'].append(bookmark)

        elif tag == 'dl':
            # 階層を一つ戻る
            if len(self.folder_stack) > 1:
                # 空のフォルダは削除
                current = self.folder_stack.pop()
                if current.get('type') != 'null_folder' and not current.get('children'):
                    # 親から削除
                    if self.folder_stack:
                        self.folder_stack[-1]['children'] = [
                            c for c in self.folder_stack[-1]['children'] if c != current
                        ]

    def handle_data(self, data):
        if self.in_h3 or self.in_a:
            self.current_text += data


def generate_html(tree):
    """
    ツリー構造からHTMLを生成
    """
    lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file.',
        '     It will be read and overwritten.',
        '     DO NOT EDIT! -->',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>',
        '    <DT><H3 ADD_DATE="1704067200" LAST_MODIFIED="1735606800" PERSONAL_TOOLBAR_FOLDER="true">数学・コーディング専用</H3>',
        '    <DL><p>'
    ]

    def write_node(node, indent='        '):
        result = []

        if node['type'] == 'folder':
            children = node.get('children', [])
            if not children:  # 空フォルダはスキップ
                return result

            attrs = node.get('attrs', {})
            add_date = attrs.get('add_date', '1704067200')
            last_modified = attrs.get('last_modified', '1735606800')

            result.append(f'{indent}<DT><H3 ADD_DATE="{add_date}" LAST_MODIFIED="{last_modified}">{node["name"]}</H3>')
            result.append(f'{indent}<DL><p>')

            for child in children:
                result.extend(write_node(child, indent + '    '))

            result.append(f'{indent}</DL><p>')

        elif node['type'] == 'bookmark':
            attrs = node.get('attrs', {})
            href = attrs.get('href', node.get('url', ''))
            add_date = attrs.get('add_date', '1704067200')

            safe_href = href.replace('"', '&quot;')
            safe_name = node['name'].replace('<', '&lt;').replace('>', '&gt;')

            result.append(f'{indent}<DT><A HREF="{safe_href}" ADD_DATE="{add_date}">{safe_name}</A>')

        return result

    for child in tree.get('children', []):
        lines.extend(write_node(child))

    lines.append('    </DL><p>')
    lines.append('</DL><p>')

    return '\n'.join(lines)


def extract_math_coding(input_file, output_file):
    """
    数学・コーディング関連のフォルダのみを抽出
    """
    print("📖 元のブックマークファイルを読み込んでいます...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("🔍 数学・コーディング関連を抽出中...")
    extractor = MathCodingExtractor()
    extractor.feed(content)

    print("📝 HTMLを生成しています...")
    html_content = generate_html(extractor.tree)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ 数学・コーディング専用ブックマークを生成しました: {output_file}")
    print(f"📊 統計:")
    print(f"   - 元のフォルダ数: {extractor.stats['total_folders']}")
    print(f"   - 保持したフォルダ数: {extractor.stats['kept_folders']}")
    print(f"   - 元のブックマーク数: {extractor.stats['total_bookmarks']}")
    print(f"   - 保持したブックマーク数: {extractor.stats['kept_bookmarks']}")
    print(f"   - 削除した重複: {extractor.stats['duplicates']}")
    print(f"   - 削減率: {100 - (extractor.stats['kept_bookmarks'] * 100 / extractor.stats['total_bookmarks']):.1f}%")


if __name__ == '__main__':
    input_file = 'bookmarks_2025_12_31_cleaned.html'  # 元のクリーニング済みファイル
    output_file = 'bookmarks_study.html'

    extract_math_coding(input_file, output_file)
