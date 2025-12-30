# GitHubリポジトリ作成手順

## 方法1: GitHub Web UIで作成（推奨）

### 1. GitHubでリポジトリを作成

1. https://github.com/new にアクセス
2. 以下の情報を入力：
   - **Repository name**: `chrome-bookmark-organizer`
   - **Description**: `Chromeブックマーク自動整理ツール - 重複削除・カテゴリー分類`
   - **Public** または **Private** を選択
   - **Add a README file** のチェックは **外す**（既にREADME.mdがあるため）
   - **Add .gitignore** は **None**（既に.gitignoreがあるため）
   - **Choose a license** は **MIT** または **None**

3. **Create repository** をクリック

### 2. ローカルリポジトリをプッシュ

ターミナルで以下のコマンドを実行：

```bash
cd /workspaces/Downloads/bookmark_organaizing

# GitHubユーザー名を設定（YOUR_USERNAMEを実際のユーザー名に置き換え）
git remote add origin https://github.com/YOUR_USERNAME/chrome-bookmark-organizer.git

# プッシュ
git push -u origin main
```

---

## 方法2: GitHub CLIで作成（GitHub CLI がインストールされている場合）

```bash
cd /workspaces/Downloads/bookmark_organaizing

# パブリックリポジトリとして作成
gh repo create chrome-bookmark-organizer --public --source=. --push

# または、プライベートリポジトリとして作成
gh repo create chrome-bookmark-organizer --private --source=. --push
```

---

## 作成後の確認

リポジトリが作成されたら、以下のURLでアクセスできます：

```
https://github.com/YOUR_USERNAME/chrome-bookmark-organizer
```

---

## リポジトリの説明文例

GitHubのリポジトリ説明欄（About）には以下を設定すると良いでしょう：

**Description:**
```
🔖 Chromeブックマーク自動整理ツール | 重複削除・無効URL除去・13カテゴリー自動分類 | 8,438個→6,529個に削減成功
```

**Topics (タグ):**
```
chrome, bookmarks, organizer, python, automation, bookmark-manager, duplicate-removal
```

---

## 現在のGit状態

```bash
# 現在のブランチを確認
git branch

# コミット履歴を確認
git log --oneline

# リモート設定を確認
git remote -v
```

---

## トラブルシューティング

### 認証エラーが出る場合

GitHubの Personal Access Token (PAT) を使用してください：

1. https://github.com/settings/tokens にアクセス
2. **Generate new token (classic)** をクリック
3. **repo** にチェックを入れる
4. トークンを生成してコピー
5. プッシュ時にパスワードの代わりにトークンを使用

### または SSH を使用

```bash
# SSH リモートに変更
git remote set-url origin git@github.com:YOUR_USERNAME/chrome-bookmark-organizer.git
```

---

## 次のステップ

リポジトリを作成したら：

1. ✅ README.md が適切に表示されているか確認
2. ✅ ファイルがすべてアップロードされているか確認
3. ✅ About セクションに説明とタグを追加
4. ✅ GitHub Releases でバージョン管理（オプション）

---

**リポジトリが作成できたら、このファイル（GITHUB_SETUP.md）は削除してもOKです。**
