# RSS Feed Aggregator

YouTubeやXを直接開かずに、自分が「有用」と判断した発信者の更新情報だけを取得するホワイトリスト式RSS統合システムです。

## 概要

- `config.yaml`で指定したソース（YouTubeチャンネル、汎用RSS）からフィードを取得
- 全ソースのアイテムを統合し、日付順にソートしたRSS 2.0形式で出力
- GitHub Actionsで定期実行し、GitHub Pagesで配信

## 前提環境

- Python 3.12
- [uv](https://github.com/astral-sh/uv) (パッケージマネージャー)

## ローカルセットアップ

```bash
# uvインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存インストール
uv sync

# 設定ファイル作成
cp config.example.yaml config.yaml
# config.yamlを編集

# RSS生成実行
uv run python -m app.main

# docs/feed.xml が生成される
```

## GitHub Actions設定

`.github/workflows/build_rss.yml`がリポジトリに含まれているため、GitHubにプッシュするだけで自動的に有効化されます。

- 毎時0分に自動実行
- 手動実行も可能（Actions → Build RSS Feed → Run workflow）

## GitHub Pages設定

1. リポジトリの Settings → Pages を開く
2. Source: Deploy from a branch を選択
3. Branch: main, Folder: /docs を選択
4. Save をクリック

## RSS購読

GitHub Pages設定後、以下のURLをRSSリーダーに登録：

```
https://<username>.github.io/<repo>/feed.xml
```

## 設定ファイル (config.yaml)

```yaml
feed:
  title: "My Whitelisted Feed"
  description: "Selected updates from whitelisted creators"
  link: "https://your-username.github.io/your-repo/feed.xml"
  language: "ja"
  max_items: 100

sources:
  # YouTubeチャンネル
  - id: "channel_id"
    type: "youtube_channel"
    display_name: "チャンネル名"
    enabled: true
    channel_id: "UC..."

  # 汎用RSS
  - id: "blog_id"
    type: "generic_rss"
    display_name: "ブログ名"
    enabled: true
    rss_url: "https://example.com/feed.xml"
```

### 対応ソース種別

| タイプ | 説明 |
|--------|------|
| `youtube_channel` | YouTubeチャンネル（公式RSS、APIキー不要） |
| `generic_rss` | 任意のRSS/Atomフィード |

## 開発

```bash
# テスト実行
uv run pytest tests/ -v

# リンター実行
uv run ruff check .

# フォーマット
uv run ruff format .
```
