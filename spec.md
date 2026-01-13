# ホワイトリスト式情報収集システム - 実装仕様書

このドキュメントはClaude Codeで使用するプロンプトです。
プロジェクトルートに配置し、実装時に参照してください。

---

## INSTRUCTIONS（役割と行動指針）

あなたは「プラットフォーム非依存のホワイトリスト式情報収集システム」を実装するソフトウェアエンジニアです。

### 行動原則

1. **コード生成に特化**: この対話ではコード生成と実装に集中してください
2. **自律的な判断**: ユーザーからの追加入力は原則期待せず、不明点は合理的に判断して進めてください
3. **実用性重視**: 過度な抽象化を避け、GitHub上で実際に動作するMVP実装を最優先してください
4. **段階的実装**: 探索→計画→コード→検証の順で進めてください

### 技術的判断の基準

以下のデフォルトから逸脱する場合は、READMEに理由を明記してください：

- 言語: Python 3.12
- パッケージ管理: `uv` + `pyproject.toml`
- リンター/フォーマッター: `ruff`
- 実行環境: GitHub Actions `ubuntu-latest` / ローカル Linux・macOS
- フィード形式: RSS 2.0

---

## CONTEXT（プロジェクト背景）

### 解決したい課題

YouTubeやXを直接開かずに、自分が「有用」と判断した発信者の更新情報だけを取得したい。

### システム概要

```
[config.yaml] → [Python処理] → [docs/feed.xml] → [GitHub Pages配信]
                     ↑
              GitHub Actions定期実行
```

### アーキテクチャ前提

| 項目 | 仕様 |
|------|------|
| 実行環境 | GitHub Actions ランナー（ubuntu-latest） |
| 出力先 | `docs/feed.xml` |
| 配信方法 | GitHub Pages（`docs/`ディレクトリ公開） |
| 公開URL | `https://<username>.github.io/<repo>/feed.xml` |
| サーバー | 不要（静的ファイル生成のみ） |
| ローカル実行 | `uv run python -m app.main` |

---

## TASK（実装タスク）

### 必須機能一覧

#### 1. ホワイトリスト管理（config.yaml）

**ファイル構成:**
- `config.yaml`: 実際の設定ファイル（.gitignore対象）
- `config.example.yaml`: サンプル設定（リポジトリにコミット）

**設定スキーマ:**

```yaml
# config.yaml の構造
feed:
  title: "My Whitelisted Feed"
  description: "Selected updates from whitelisted creators"
  link: "https://username.github.io/repo/feed.xml"
  language: "ja"
  max_items: 100  # 統合フィードに含める最大件数

sources:
  - id: "channel_unique_id"        # 必須: 一意な識別子
    type: "youtube_channel"        # 必須: youtube_channel | generic_rss
    display_name: "チャンネル名"    # 必須: 表示名
    enabled: true                  # 必須: 有効/無効
    channel_id: "UC..."            # youtube_channelの場合: チャンネルID
    # または
    rss_url: "https://..."         # generic_rssの場合: RSS URL
```

**対応するソース種別:**
- `youtube_channel`: YouTubeチャンネル（公式RSS利用、APIキー不要）
- `generic_rss`: 任意のRSS/Atomフィード（X→RSS変換サービス含む）

#### 2. ソース取得ロジック

**youtube_channel の処理:**
1. `channel_id`から公式RSS URLを生成: `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`
2. フィードを取得・パース
3. `NormalizedItem`に変換

**generic_rss の処理:**
1. 設定された`rss_url`からフィードを取得
2. `feedparser`でパース
3. `NormalizedItem`に変換

**NormalizedItem 定義:**

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class NormalizedItem:
    source_id: str              # config上のid
    source_display_name: str    # 表示名
    title: str                  # アイテムタイトル
    url: str                    # アイテムURL
    published_at: datetime      # 公開日時（timezone-aware）
    description: str | None     # 説明（存在する場合）
```

**エラーハンドリング要件:**
- 1つのソースが失敗しても他のソースは処理を継続する
- 失敗したソースはログに記録する（ERROR レベル）
- 全ソース失敗時は既存の`feed.xml`を保持する（上書きしない）

#### 3. 統合RSSフィード生成

**処理フロー:**
1. 有効な全ソースから`NormalizedItem`を収集
2. `published_at`降順でソート
3. 設定の`max_items`件に制限
4. RSS 2.0形式で`docs/feed.xml`に出力

**RSS出力要件:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{feed.title}</title>
    <link>{feed.link}</link>
    <description>{feed.description}</description>
    <language>{feed.language}</language>
    <lastBuildDate>{RFC 822形式}</lastBuildDate>
    <item>
      <title>{item.title}</title>
      <link>{item.url}</link>
      <description>{item.description または item.source_display_name}</description>
      <pubDate>{RFC 822形式}</pubDate>
      <guid isPermaLink="true">{item.url}</guid>
      <source url="{source_url}">{item.source_display_name}</source>
    </item>
    <!-- 繰り返し -->
  </channel>
</rss>
```

#### 4. CLIエントリポイント

**実行コマンド:** `uv run python -m app.main`

**処理フロー:**
1. `config.yaml`を読み込む
2. 設定が存在しない場合、エラーメッセージを表示して終了
   ```
   Error: config.yaml not found.
   Please copy config.example.yaml to config.yaml and edit it.
   ```
3. 有効なソースからフィードを取得・正規化
4. 統合RSSを生成し`docs/feed.xml`に書き出す
5. 処理結果サマリーを標準出力

**ログ出力例:**
```
INFO: Loading config from config.yaml
INFO: Processing 5 enabled sources...
INFO: [youtube_channel] channel_a: 15 items fetched
INFO: [generic_rss] blog_b: 10 items fetched
ERROR: [generic_rss] feed_c: Connection timeout
INFO: Processing complete: 25 items from 4 sources (1 failed)
INFO: Writing feed.xml with 25 items...
INFO: Done.
```

#### 5. GitHub Actions ワークフロー

**ファイル:** `.github/workflows/build_rss.yml`

**要件:**

```yaml
name: Build RSS Feed

on:
  schedule:
    - cron: '0 * * * *'  # 毎時0分に実行
  workflow_dispatch:      # 手動トリガー

permissions:
  contents: write         # Push権限

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --frozen

      - name: Build RSS feed
        run: uv run python -m app.main

      - name: Commit and push if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/feed.xml
          git diff --staged --quiet || git commit -m "Update feed.xml"
          git push
```

#### 6. テスト

**テストフレームワーク:** pytest

**必須テストケース:**

1. **正規化ロジックテスト** (`tests/test_normalization.py`)
   - YouTubeフィードアイテム → NormalizedItem
   - 汎用RSSアイテム → NormalizedItem
   - タイムゾーン処理の検証

2. **フィード生成テスト** (`tests/test_feed_builder.py`)
   - 複数NormalizedItemからRSS文字列生成
   - max_items制限の検証
   - ソート順の検証

**テスト実行:** `uv run pytest tests/ -v`

---

## OUTPUT FORMAT（成果物）

### ディレクトリ構成

```
project-root/
├── .github/
│   └── workflows/
│       └── build_rss.yml        # GitHub Actions ワークフロー
├── app/
│   ├── __init__.py
│   ├── config.py                # 設定ファイル読み込み
│   ├── models.py                # NormalizedItem定義
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py              # ソース取得の基底クラス/インターフェース
│   │   ├── youtube.py           # YouTubeチャンネル取得
│   │   └── generic_rss.py       # 汎用RSS取得
│   ├── feed_builder.py          # 統合RSS生成
│   └── main.py                  # CLIエントリポイント
├── docs/
│   └── .gitkeep                 # ディレクトリ保持用（feed.xmlはgitignore対象外）
├── tests/
│   ├── __init__.py
│   ├── test_normalization.py    # 正規化テスト
│   └── test_feed_builder.py     # フィード生成テスト
├── .gitignore
├── .python-version              # Python 3.12指定
├── config.example.yaml          # 設定サンプル
├── pyproject.toml               # プロジェクト設定・依存定義
├── uv.lock                      # 依存ロックファイル
└── README.md                    # セットアップ・使用方法
```

### pyproject.toml 内容

```toml
[project]
name = "rss-feed-aggregator"
version = "0.1.0"
description = "Whitelist-based RSS feed aggregator"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "feedparser>=6.0",
    "requests>=2.31",
    "pyyaml>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### README.md 必須セクション

1. **プロジェクト概要**: ホワイトリスト式RSS統合システムの説明
2. **前提環境**: Python 3.12, uv
3. **ローカルセットアップ手順**:
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
4. **GitHub Actions設定**: ワークフローファイル配置のみで自動有効化
5. **GitHub Pages設定**:
   - Settings → Pages
   - Source: Deploy from a branch
   - Branch: main, Folder: /docs
6. **RSS購読方法**: `https://<username>.github.io/<repo>/feed.xml` をRSSリーダーに登録

### config.example.yaml 内容

```yaml
feed:
  title: "My Whitelisted Feed"
  description: "Selected updates from whitelisted creators"
  link: "https://your-username.github.io/your-repo/feed.xml"
  language: "ja"
  max_items: 100

sources:
  # YouTubeチャンネルの例
  - id: "example_youtube"
    type: "youtube_channel"
    display_name: "Example YouTube Channel"
    enabled: true
    channel_id: "UCxxxxxxxxxxxxxxxxxxxxxxxx"

  # 汎用RSSの例
  - id: "example_blog"
    type: "generic_rss"
    display_name: "Example Blog"
    enabled: true
    rss_url: "https://example.com/feed.xml"

  # 無効化されたソースの例
  - id: "disabled_source"
    type: "generic_rss"
    display_name: "Disabled Source"
    enabled: false
    rss_url: "https://example.org/rss"
```

---

## 実装ワークフロー

以下の順序で実装を進めてください：

### Phase 1: プロジェクト初期化

1. `uv init`でプロジェクト作成
2. `pyproject.toml`を編集し依存関係を追加
3. `uv sync`で依存インストール
4. `.gitignore`作成

### Phase 2: コアモデル実装

1. `app/models.py`: NormalizedItem定義
2. `app/config.py`: YAML設定読み込み

### Phase 3: ソース取得実装

1. `app/sources/base.py`: 基底クラス/プロトコル定義
2. `app/sources/youtube.py`: YouTube取得実装
3. `app/sources/generic_rss.py`: 汎用RSS取得実装

### Phase 4: フィード生成実装

1. `app/feed_builder.py`: RSS 2.0生成ロジック
2. `app/main.py`: CLIエントリポイント

### Phase 5: テスト作成

1. `tests/test_normalization.py`
2. `tests/test_feed_builder.py`
3. `uv run pytest`で全テスト通過を確認

### Phase 6: 設定・ドキュメント

1. `config.example.yaml`作成
2. `README.md`作成
3. `.github/workflows/build_rss.yml`作成
4. `docs/.gitkeep`作成

### Phase 7: 動作確認

1. `cp config.example.yaml config.yaml`
2. `config.yaml`にテスト用ソースを設定
3. `uv run python -m app.main`で`docs/feed.xml`生成を確認
4. 生成されたXMLの妥当性を確認

---

## 検証チェックリスト

実装完了後、以下を確認してください：

- [ ] `uv sync`が正常完了する
- [ ] `uv run ruff check .`がエラーなしで通過する
- [ ] `uv run pytest`が全テスト通過する
- [ ] `uv run python -m app.main`で`docs/feed.xml`が生成される
- [ ] 生成されたXMLが有効なRSS 2.0形式である
- [ ] config.yamlが存在しない場合、適切なエラーメッセージが表示される
- [ ] 1つのソースがエラーでも他のソースは処理される

---

## 今後の拡張案（MVP後）

- Bluesky/Mastodon対応
- キーワードフィルタリング（含む/除外）
- アイテム重複排除（URL正規化ベース）
- OPML インポート/エクスポート
- Slack/Discord通知連携
- フィード更新差分検知
