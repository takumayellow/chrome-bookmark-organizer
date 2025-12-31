#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学・英語・コーディングに特化したブックマークを作成
元のフォルダ構造を保持しつつ、不要なものを削除
"""

import re
from html.parser import HTMLParser
from datetime import datetime


class StudyBookmarkFilter(HTMLParser):
    """
    勉強用ブックマークのみをフィルタリング
    """

    def __init__(self):
        super().__init__()
        self.tree = {'name': 'root', 'type': 'folder', 'children': [], 'is_bookmark_bar': False}
        self.current_path = [self.tree]
        self.pending_folder = None
        self.in_h3 = False
        self.in_a = False
        self.current_text = ''
        self.current_attrs = {}
        self.stats = {
            'total': 0,
            'kept': 0,
            'removed_old': 0,
            'removed_category': 0
        }

    def should_keep_bookmark(self, url, title, add_date):
        """
        ブックマークを保持すべきか判定
        """
        self.stats['total'] += 1

        url_lower = url.lower()
        title_lower = title.lower()

        # 2023年以前（Unix timestamp: 1704067200未満）は削除
        try:
            if add_date and int(add_date) < 1672531200:  # 2023-01-01
                self.stats['removed_old'] += 1
                return False
        except:
            pass

        # 削除対象キーワード
        remove_keywords = [
            '政治', '選挙', '政党', '国会', '議員',
            '社会問題', 'ニュース', '芸能',
            'レシピ', '料理', 'ファッション', 'コスメ',
            '旅行', '観光', 'ホテル',
            'ゲーム', 'アニメ', '漫画', 'マンガ',
            '映画', 'ドラマ', 'netflix',
            'ショッピング', '買い物', 'amazon',
            '音楽', 'youtube' # YouTubeは教育系以外削除
        ]

        # YouTubeは教育系のみ保持
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            education_keywords = ['講義', '授業', '解説', 'tutorial', 'lecture', '数学', '英語', 'プログラミング']
            if not any(k in title_lower for k in education_keywords):
                self.stats['removed_category'] += 1
                return False

        # 削除対象チェック
        if any(k in title_lower for k in remove_keywords):
            if 'youtube' not in url_lower:  # YouTubeは上で判定済み
                self.stats['removed_category'] += 1
                return False

        # 保持対象キーワード
        keep_keywords = [
            # 数学
            '数学', 'math', '微分', '積分', '線形代数', '統計', 'calculus', 'algebra',
            # 英語
            '英語', 'english', '英検', 'toefl', 'toeic', 'vocabulary', 'grammar',
            # プログラミング・CS
            'プログラミング', 'programming', 'python', 'javascript', 'java', 'c++',
            'react', 'vue', 'node', 'git', 'github', 'qiita', 'zenn',
            'アルゴリズム', 'algorithm', 'atcoder', '競プロ',
            'ai', '機械学習', 'deep learning', 'chatgpt', 'claude',
            # 大学
            '物理', 'physics', '化学', 'chemistry', '実験', 'letus', '授業'
        ]

        # ドメインベースの判定
        study_domains = [
            'qiita.com', 'zenn.dev', 'github.com', 'stackoverflow.com',
            'atcoder.jp', 'letus.ed.tus.ac.jp', 'tus.app.box.com',
            'note.nkmk.me', 'manabitimes.jp', 'quizlet.com',
            'chatgpt.com', 'claude.ai'
        ]

        if any(domain in url_lower for domain in study_domains):
            self.stats['kept'] += 1
            return True

        # キーワードベースの判定
        if any(k in title_lower or k in url_lower for k in keep_keywords):
            self.stats['kept'] += 1
            return True

        # その他は削除
        self.stats['removed_category'] += 1
        return False

    def should_keep_folder(self, folder_name):
        """
        フォルダを保持すべきか判定（名前ベース）
        """
        folder_lower = folder_name.lower()

        # 削除対象フォルダ
        remove_folders = [
            'エンターテイメント', '音楽', '映画', 'ドラマ',
            'ショッピング', '買い物',
            '政治', '社会', 'ニュース',
            '生活', 'レシピ', '料理',
            '旅行', '観光'
        ]

        if any(k in folder_lower for k in remove_folders):
            return False

        return True

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
                'attrs': attrs_dict,
                'is_bookmark_bar': attrs_dict.get('personal_toolbar_folder') == 'true'
            }

        elif tag == 'dl':
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
            url = self.current_attrs.get('href', '')
            add_date = self.current_attrs.get('add_date', '')
            title = self.current_text.strip()

            # ブックマークバーの場合は厳選
            if self.current_path and len(self.current_path) > 1:
                parent = self.current_path[-1]
                if parent.get('is_bookmark_bar'):
                    # ブックマークバーに必須のサイトのみ保持
                    essential_domains = [
                        'atcoder.jp', 'letus.ed.tus.ac.jp', 'mail.google.com',
                        'gmail.com', 'quizlet.com', 'chatgpt.com', 'github.com'
                    ]
                    if not any(domain in url.lower() for domain in essential_domains):
                        return

            if self.should_keep_bookmark(url, title, add_date):
                bookmark = {
                    'type': 'bookmark',
                    'name': title,
                    'url': url,
                    'attrs': self.current_attrs,
                    'level': len(self.current_path) - 1
                }
                self.current_path[-1]['children'].append(bookmark)

        elif tag == 'dl':
            if len(self.current_path) > 1:
                self.current_path.pop()

    def handle_data(self, data):
        if self.in_h3 or self.in_a:
            self.current_text += data


def categorize_unnamed_folder(folder):
    """
    「新しいフォルダ」などの未分類フォルダを内容で分類
    """
    if folder['name'] not in ['新しいフォルダ', '仮置き', '名前のないフォルダ', '']:
        return folder['name']

    children = folder.get('children', [])
    bookmarks = [c for c in children if c['type'] == 'bookmark']

    if not bookmarks:
        return folder['name']

    # URLから推測
    urls = [b['url'].lower() for b in bookmarks]
    titles = [b['name'].lower() for b in bookmarks]

    # プログラミング
    if any('qiita.com' in url or 'github.com' in url or 'zenn.dev' in url for url in urls):
        if any('python' in t for t in titles):
            return 'Python'
        elif any('javascript' in t or 'react' in t for t in titles):
            return 'Web開発'
        else:
            return 'プログラミング'

    # 数学
    if any(k in ' '.join(titles) for k in ['数学', '微分', '積分', '線形代数']):
        return '数学'

    # 英語
    if any(k in ' '.join(titles) for k in ['英語', 'english', 'toefl', '英検']):
        return '英語'

    # AtCoder
    if any('atcoder' in url for url in urls):
        return '競技プログラミング'

    return folder['name']


def generate_filtered_html(tree):
    """
    フィルタリングされたHTMLを生成
    """
    lines = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file.',
        '     It will be read and overwritten.',
        '     DO NOT EDIT! -->',
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        '<TITLE>Bookmarks</TITLE>',
        '<H1>Bookmarks</H1>',
        '<DL><p>'
    ]

    def write_folder(folder, indent='    '):
        result = []

        # 空フォルダはスキップ
        children = folder.get('children', [])
        if not children:
            return result

        # フォルダ名を分類
        folder_name = categorize_unnamed_folder(folder) if folder.get('name') else 'root'

        if folder_name != 'root':
            attrs = folder.get('attrs', {})
            add_date = attrs.get('add_date', '1704067200')
            last_modified = attrs.get('last_modified', '1735606800')
            toolbar = ' PERSONAL_TOOLBAR_FOLDER="true"' if folder.get('is_bookmark_bar') else ''

            result.append(f'{indent}<DT><H3 ADD_DATE="{add_date}" LAST_MODIFIED="{last_modified}"{toolbar}>{folder_name}</H3>')
            result.append(f'{indent}<DL><p>')

        # 子要素を処理
        for child in children:
            if child['type'] == 'folder':
                # フォルダ名で除外判定
                if not filter_obj.should_keep_folder(child.get('name', '')):
                    continue
                result.extend(write_folder(child, indent + '    '))
            elif child['type'] == 'bookmark':
                attrs = child.get('attrs', {})
                href = attrs.get('href', child.get('url', ''))
                add_date = attrs.get('add_date', '1704067200')

                safe_href = href.replace('"', '&quot;')
                safe_name = child['name'].replace('<', '&lt;').replace('>', '&gt;')

                result.append(f'{indent}    <DT><A HREF="{safe_href}" ADD_DATE="{add_date}">{safe_name}</A>')

        if folder_name != 'root':
            result.append(f'{indent}</DL><p>')

        return result

    for child in tree.get('children', []):
        lines.extend(write_folder(child))

    lines.append('</DL><p>')
    return '\n'.join(lines)


def filter_study_bookmarks(input_file, output_file):
    """
    勉強用ブックマークのみを抽出
    """
    global filter_obj

    print("📖 ブックマークファイルを読み込んでいます...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("🔍 フィルタリング中...")
    filter_obj = StudyBookmarkFilter()
    filter_obj.feed(content)

    print("📝 HTMLを生成しています...")
    html_content = generate_filtered_html(filter_obj.tree)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ 勉強用ブックマークを生成しました: {output_file}")
    print(f"📊 統計:")
    print(f"   - 総ブックマーク数: {filter_obj.stats['total']}")
    print(f"   - 保持: {filter_obj.stats['kept']}")
    print(f"   - 削除（古い）: {filter_obj.stats['removed_old']}")
    print(f"   - 削除（カテゴリ）: {filter_obj.stats['removed_category']}")
    print(f"   - 削減率: {100 - (filter_obj.stats['kept'] * 100 / filter_obj.stats['total']):.1f}%")


if __name__ == '__main__':
    input_file = 'bookmarks_recent_2024.html'
    output_file = 'bookmarks_study.html'

    filter_study_bookmarks(input_file, output_file)
