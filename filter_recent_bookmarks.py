#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最近1年間のブックマークを抽出するスクリプト
2024年以降（Unix timestamp: 1704067200以降）のブックマークのみを抽出
"""

import re
from datetime import datetime
from html.parser import HTMLParser


class RecentBookmarkFilter(HTMLParser):
    """
    最近のブックマークのみを抽出するパーサー
    """

    def __init__(self, cutoff_timestamp):
        super().__init__()
        self.cutoff_timestamp = cutoff_timestamp
        self.output = []
        self.current_folder_stack = []
        self.current_folder_dates = []
        self.in_bookmark_bar = False
        self.folder_has_recent = {}
        self.recent_count = 0
        self.total_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h3':
            # フォルダの開始
            add_date = attrs_dict.get('add_date', '0')
            last_modified = attrs_dict.get('last_modified', '0')

            # フォルダ情報をスタックに追加
            self.current_folder_dates.append((add_date, last_modified))

        elif tag == 'a':
            # ブックマーク
            self.total_count += 1
            add_date = int(attrs_dict.get('add_date', '0'))

            # 2024年以降かチェック
            if add_date >= self.cutoff_timestamp:
                self.recent_count += 1
                # このブックマークを含む全ての親フォルダをマーク
                for i in range(len(self.current_folder_stack)):
                    self.folder_has_recent[tuple(self.current_folder_stack[:i+1])] = True

    def handle_endtag(self, tag):
        if tag == 'dl' and self.current_folder_dates:
            self.current_folder_dates.pop()


def filter_bookmarks_by_date(input_file, output_file, cutoff_year=2024):
    """
    指定された年以降のブックマークのみを抽出
    """
    # カットオフ日時（2024-01-01 00:00:00 UTC）のUnixタイムスタンプ
    cutoff_timestamp = int(datetime(cutoff_year, 1, 1).timestamp())

    print(f"📅 {cutoff_year}年以降のブックマークを抽出します")
    print(f"   カットオフタイムスタンプ: {cutoff_timestamp}")

    # まず、ファイルを読み込んで最近のブックマークを含むフォルダを特定
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # HTMLを解析して最近のブックマークのみを抽出
    lines = content.split('\n')
    output_lines = []

    folder_stack = []
    keep_current_folder = False
    in_dl = 0
    skip_mode = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # ヘッダー部分はそのまま保持
        if i < 10 or '<H1>' in line or '<!DOCTYPE' in line or '<META' in line or '<TITLE>' in line:
            output_lines.append(line)
            i += 1
            continue

        # H3タグ（フォルダ）の処理
        if '<H3' in line and 'ADD_DATE' in line:
            # ADD_DATEを抽出
            match = re.search(r'ADD_DATE="(\d+)"', line)
            if match:
                add_date = int(match.group(1))

                # 次の行でDLが始まるか確認
                next_i = i + 1
                while next_i < len(lines) and lines[next_i].strip() == '':
                    next_i += 1

                # フォルダ内のブックマークをチェック
                folder_has_recent = check_folder_has_recent(lines, next_i, cutoff_timestamp)

                if folder_has_recent or add_date >= cutoff_timestamp:
                    output_lines.append(line)
                    folder_stack.append(True)
                else:
                    # このフォルダはスキップ
                    folder_stack.append(False)
                    skip_mode = True
            else:
                output_lines.append(line)

        # Aタグ（ブックマーク）の処理
        elif '<A ' in line and 'HREF' in line:
            if folder_stack and not folder_stack[-1]:
                # スキップ対象のフォルダ内
                pass
            else:
                # ADD_DATEを抽出
                match = re.search(r'ADD_DATE="(\d+)"', line)
                if match:
                    add_date = int(match.group(1))
                    if add_date >= cutoff_timestamp:
                        # DTタグから該当行までを追加
                        if i > 0 and '<DT>' in lines[i-1]:
                            output_lines.append(lines[i-1])
                        output_lines.append(line)
                # ADD_DATEがない場合は保持
                else:
                    if i > 0 and '<DT>' in lines[i-1]:
                        output_lines.append(lines[i-1])
                    output_lines.append(line)

        # DLタグの処理
        elif '<DL>' in line:
            if not folder_stack or folder_stack[-1]:
                output_lines.append(line)
            in_dl += 1

        elif '</DL>' in line:
            in_dl -= 1
            if not folder_stack or folder_stack[-1]:
                output_lines.append(line)
            if folder_stack:
                folder_stack.pop()
                if folder_stack and not folder_stack[-1]:
                    skip_mode = True
                else:
                    skip_mode = False

        # その他のタグ
        elif '<DT>' not in line:
            if not skip_mode:
                output_lines.append(line)

        i += 1

    # より簡単なアプローチ：正規表現で直接フィルタリング
    print("\n🔍 簡易フィルタリングを実行します...")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # ブックマーク（Aタグ）を抽出して日付でフィルタ
    bookmark_pattern = r'<DT><A[^>]*ADD_DATE="(\d+)"[^>]*>.*?</A>'

    filtered_content = []
    header_end = content.find('<DL><p>')

    if header_end > 0:
        filtered_content.append(content[:header_end + 7])

    recent_bookmarks = []
    total_bookmarks = 0

    for match in re.finditer(bookmark_pattern, content, re.DOTALL):
        total_bookmarks += 1
        add_date = int(match.group(1))
        if add_date >= cutoff_timestamp:
            recent_bookmarks.append(match.group(0))

    # 最近のブックマークをフォルダ構造で整理
    filtered_html = reconstruct_bookmarks(content, cutoff_timestamp)

    # ファイルに書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(filtered_html)

    print(f"\n✅ フィルタリング完了！")
    print(f"   入力ファイル: {input_file}")
    print(f"   出力ファイル: {output_file}")
    print(f"   総ブックマーク数: {total_bookmarks}")
    print(f"   {cutoff_year}年以降: {len(recent_bookmarks)} 個")
    print(f"   削減率: {100 - (len(recent_bookmarks) * 100 / total_bookmarks):.1f}%")


def check_folder_has_recent(lines, start_idx, cutoff_timestamp):
    """
    フォルダ内に最近のブックマークがあるかチェック
    """
    depth = 0
    for i in range(start_idx, len(lines)):
        line = lines[i]

        if '<DL>' in line:
            depth += 1
        elif '</DL>' in line:
            depth -= 1
            if depth < 0:
                return False
        elif '<A ' in line and 'ADD_DATE' in line:
            match = re.search(r'ADD_DATE="(\d+)"', line)
            if match and int(match.group(1)) >= cutoff_timestamp:
                return True

    return False


def reconstruct_bookmarks(html_content, cutoff_timestamp):
    """
    HTMLを解析して最近のブックマークのみで再構築
    """
    lines = html_content.split('\n')
    output = []

    # ヘッダー部分
    for i, line in enumerate(lines):
        if '<DL><p>' in line:
            output.append(line)
            break
        output.append(line)

    # ブックマークバーを探す
    bookmark_bar_started = False
    current_folder = None
    folder_stack = []
    folder_bookmarks = {}

    for i, line in enumerate(lines):
        # ブックマークバーの開始
        if 'PERSONAL_TOOLBAR_FOLDER="true"' in line:
            bookmark_bar_started = True
            # フォルダ名を抽出
            match = re.search(r'>([^<]+)</H3>', line)
            if match:
                current_folder = match.group(1)
                folder_bookmarks[current_folder] = []

        # サブフォルダの処理
        elif '<H3' in line and bookmark_bar_started:
            match = re.search(r'>([^<]+)</H3>', line)
            if match:
                folder_name = match.group(1)
                folder_stack.append(folder_name)
                full_path = ' > '.join(folder_stack)
                folder_bookmarks[full_path] = []
                current_folder = full_path

        # ブックマークの処理
        elif '<A ' in line and 'HREF' in line:
            match = re.search(r'ADD_DATE="(\d+)"', line)
            if match:
                add_date = int(match.group(1))
                if add_date >= cutoff_timestamp:
                    # DTタグも含める
                    if i > 0 and '<DT>' in lines[i-1]:
                        bookmark_line = lines[i-1] + '\n' + line
                    else:
                        bookmark_line = '        <DT>' + line

                    if current_folder and current_folder in folder_bookmarks:
                        folder_bookmarks[current_folder].append(bookmark_line)

        # フォルダの終了
        elif '</DL>' in line and folder_stack:
            folder_stack.pop()
            if folder_stack:
                current_folder = ' > '.join(folder_stack)
            else:
                current_folder = None

    # 最近のブックマークがあるフォルダのみで再構築
    output.append('    <DT><H3 ADD_DATE="1704067200" LAST_MODIFIED="1735606800" PERSONAL_TOOLBAR_FOLDER="true">ブックマーク バー（2024年以降）</H3>')
    output.append('    <DL><p>')

    for folder_path, bookmarks in sorted(folder_bookmarks.items()):
        if bookmarks:
            # フォルダ構造を再現
            parts = folder_path.split(' > ')
            indent = '    ' + '    ' * len(parts)

            output.append(f'{indent}<DT><H3 ADD_DATE="1704067200">{parts[-1]}</H3>')
            output.append(f'{indent}<DL><p>')

            for bookmark in bookmarks:
                output.append(f'{indent}    {bookmark}')

            output.append(f'{indent}</DL><p>')

    output.append('    </DL><p>')

    return '\n'.join(output)


if __name__ == '__main__':
    input_file = 'bookmarks_2025_12_31_cleaned.html'
    output_file = 'bookmarks_recent_2024.html'

    filter_bookmarks_by_date(input_file, output_file, cutoff_year=2024)
