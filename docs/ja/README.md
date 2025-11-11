# GTPlanner: AI駆動のPRD生成ツール

<p align="center">
  <img src="../../assets/banner.png" width="800" alt="GTPlanner Banner"/>
</p>

<p align="center">
  <strong>自然言語の説明を、Vibe codingに最適化された構造化された技術文書に変換する、インテリジェントなAgent PRD生成ツール。</strong>
</p>

<p align="center">
  <a href="#概要">概要</a> •
  <a href="#web-ui-推奨">Web UI</a> •
  <a href="#mcp統合">MCP統合</a> •
  <a href="#クイックスタート">クイックスタート</a> •
  <a href="#設定">設定</a> •
  <a href="#プロジェクト構造">プロジェクト構造</a> •
  <a href="#prefabエコシステム">Prefabエコシステム</a> •
  <a href="#コントリビュート">コントリビュート</a> •
  <a href="#ライセンス">ライセンス</a>
</p>

<p align="center">
  <strong>言語:</strong>
  <a href="../../README.md">English</a> •
  <a href="../zh/README.md">简体中文</a> •
  <a href="README.md">日本語</a>
</p>

---

## 概要—Agentに働いてもらうには？

- まず、タスクを定義します：入力は何か？具体的な手順は何か？出力は何か？成功をどう定義するか？これらは通常SOPと呼ばれます。**SOP化できる作業は、AIで自動化できます。**
- 次に、Agentに適切なツールを提供します。人間はOfficeスイートを使い、Webを閲覧し、ファイルやデータを管理します。Agentに働いてもらうなら、これらのツールも必要です。
- 最後に、Agentが成果物をどのように整理するかを指定します。

Agentのコンテキストでは、これをより適切に表す言葉があります：**コンテキストエンジニアリング**。具体的には、Code Agent（Claude Code/Cursor/Augment/Devin/...）を開始する前に、ドキュメントで明確に定義します：
- design.md：作業内容を定義
- prefab.md：利用可能なツールとその使用方法を定義。これを**Prefab**と呼びます
- starter-kit：開発フレームワークと利用可能な環境を定義（この部分はプロジェクト間でほぼ一貫しています）

これがGTPlannerの目的です—Agentを構築するプロセスを簡素化します。

## GTPlannerを選ぶ理由

GTPlannerは、AIが理解できる標準作業手順書（SOP）であるAgent PRDを簡単に生成し、タスクを迅速に自動化するのを支援します。GTPlannerの設計哲学：
- **決定性**: 明確なSOP（Agent PRD）を通じてAIの曖昧性を排除し、高度に制御可能で予測可能な実行パスと結果を保証します
- **組み合わせ可能性**: SOPを再利用可能な「Prefab」とタスクモジュールに分解し、ブロックのように組み合わせて、より複雑なワークフローを構築します
- **自由度**: 実行プラットフォーム（n8nなど）に縛られず、最小限のAIフレームワークとネイティブPythonコードを使用することで、最大限の柔軟性と自由を保証します

---

## Web UI（推奨）

最高のエクスペリエンスを得るために、Web UIを強くお勧めします。現代の開発者向けに調整された、スムーズなAIプランニングワークフローを提供します。

![GTPlanner Web UI](../../assets/web.gif)

**主な利点：**
- **インテリジェントプランニングアシスタント**: AI支援によるシステムアーキテクチャとプロジェクト計画の迅速な生成
- **インスタントドキュメント生成**: 包括的な技術文書を自動作成
- **Vibe Codingに完璧に適合**: Cursor、Windsurf、GitHub Copilot向けに最適化された出力
- **チームコラボレーション**: 簡単に共有できる複数形式のエクスポート

[ライブデモを試す](https://the-agent-builder.com/)

---

## MCP統合

<details>
<summary>クリックしてMCP統合の説明を展開</summary>

GTPlanner は Model Context Protocol (MCP) をサポートし、AIプログラミングツールで直接使用できます。

<table>
<tr>
<td width="50%">

**Cherry Studioでの使用**
![MCP in Cherry Studio](../../assets/Cherry_Studio_2025-06-24_01-05-49.png)

</td>
<td width="50%">

**Cursorでの使用**
![MCP in Cursor](../../assets/Cursor_2025-06-24_01-12-05.png)

</td>
</tr>
</table>

詳細な設定ガイド → [MCPドキュメント](../../mcp/README_zh.md)

</details>

---

## クイックスタート

### オンライン体験（インストール不要）

[Web UIを試す](https://the-agent-builder.com/) - WYSIWYGプランニングとドキュメント生成

### ローカルセットアップ

#### 前提条件

- **Python ≥ 3.10**（3.11+推奨）
- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv)（推奨）
- **LLM API Key**: OpenAI / Anthropic / Azure OpenAI / セルフホストの互換エンドポイント

#### インストール

```bash
git clone https://github.com/OpenSQZ/GTPlanner.git
cd GTPlanner

# uvで依存関係をインストール
uv sync
```

#### 設定

設定テンプレートをコピーしてAPI Keyを設定：

```bash
cp .env.example .env
# .envファイルを編集し、必要な環境変数を設定
```

**必須設定：**
```bash
LLM_API_KEY="your-api-key-here"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-5"
```

詳細な設定ガイド（一般的なプロバイダー、Langfuseなど） → [設定ドキュメント](../configuration_zh.md)

### CLI使用方法

#### 対話モード

```bash
python gtplanner.py
```

起動後、要件を入力します。例：
```
動画の字幕を自動抽出し、要約とキーポイントを生成できるビデオ分析アシスタントを作成してください。
```

#### 直接実行

```bash
python gtplanner.py "PDF、Word文書の解析とインテリジェントQ&Aをサポートする文書分析アシスタントを設計してください"
```

CLI詳細ドキュメント（セッション管理、パラメータ説明など） → [CLIドキュメント](../../gtplanner/agent/cli/README_zh.md)

### API使用方法

FastAPIサービスを起動：

```bash
uv run fastapi_main.py
# デフォルトで http://0.0.0.0:11211 で実行
```

`http://0.0.0.0:11211/docs` にアクセスしてAPIドキュメントを表示

API詳細ドキュメント（エンドポイント説明、使用例など） → [APIドキュメント](../../gtplanner/agent/api/README_zh.md)

### MCP統合

```bash
cd mcp
uv sync
uv run python mcp_service.py
```

MCP詳細ドキュメント（クライアント設定、利用可能なツールなど） → [MCPドキュメント](../../mcp/README_zh.md)

---

## 設定

GTPlanner は複数の設定方法をサポートしています：

- **環境変数** (.env ファイル): API Key、Base URL、Modelなど
- **設定ファイル** (settings.toml): 言語、トレース、ベクトルサービスなど
- **Langfuseトレース**（オプション）: 実行プロセストレースとパフォーマンス分析

完全な設定ガイド → [設定ドキュメント](../configuration_zh.md)

---

## プロジェクト構造

```
GTPlanner/
├── README.md                  # メインドキュメント
├── gtplanner.py              # CLIエントリーポイント
├── fastapi_main.py           # APIサービスエントリー
├── settings.toml             # 設定ファイル
│
├── gtplanner/                # コアコード
│   ├── agent/               # Agentシステム
│   │   ├── cli/            # → [CLIドキュメント](../../gtplanner/agent/cli/README_zh.md)
│   │   ├── api/            # → [APIドキュメント](../../gtplanner/agent/api/README_zh.md)
│   │   ├── flows/          # 制御フロー
│   │   ├── subflows/       # 専門サブフロー
│   │   └── ...
│   └── utils/              # ユーティリティ
│
├── prefabs/                 # Prefabエコシステム
│   ├── README_zh.md        # → [Prefabドキュメント](../../prefabs/README_zh.md)
│   └── releases/           # リリース管理
│       ├── community-prefabs.json  # Prefabレジストリ
│       └── CONTRIBUTING_zh.md # → [Prefabコントリビューションガイド](../../prefabs/releases/CONTRIBUTING_zh.md)
│
├── mcp/                    # MCPサービス
│   └── README_zh.md       # → [MCPドキュメント](../../mcp/README_zh.md)
│
├── docs/                   # ドキュメント
│   ├── zh/                # 中国語ドキュメント
│   ├── ja/                # 日本語ドキュメント
│   ├── configuration.md   # 設定ガイド
│   └── architecture/      # アーキテクチャドキュメント
│
├── workspace/             # ランタイムディレクトリ
│   ├── logs/             # ログ
│   └── output/           # 出力ドキュメント
│
└── tests/                # テスト
```

システムアーキテクチャドキュメント → [アーキテクチャドキュメント](../architecture/README.md)

---

## Prefabエコシステム

GTPlanner は Prefab エコシステムを通じて機能を拡張します。各Prefabは標準化された再利用可能なAI機能コンポーネントです。

### Prefabとは？

Prefabはすぐに使えるAI機能モジュールで、以下が可能です：
- **発見**: GTPlanner が利用可能なPrefabを自動認識
- **デプロイ**: PRマージ後に自動的にプラットフォームにデプロイ
- **統合**: 標準APIを通じて呼び出し
- **バージョン管理**: セマンティックバージョニング

### PrefabはどのようにGTplannerを強化するか？

`community-prefabs.json` にPrefabを貢献すると：

1. **プランニング機能の拡張**: GTPlanner が新しいソリューションを認識
2. **スマート推奨**: GTPlanner がプラン生成時に適切なPrefabを推奨
3. **自動統合**: プランニングドキュメントにPrefabの使用方法が含まれる

**Prefabの例：**
- **メディア処理**: [ビデオ処理Prefab](../../Video-processing/) - ビデオから音声、字幕抽出
- **データサービス**: [高德天気Prefab](../../Amap-Weather/) - 天気照会
- **ドキュメント処理**: PDF解析、Excel処理
- **AIサービス**: 音声認識、画像認識

### 始め方

**Prefabの使用：**

Prefab Gateway経由で公開されているPrefabを呼び出し：

```bash
# 1. AgentBuilderプラットフォームでAPI Keyを作成
# 2. ゲートウェイ経由でPrefabを呼び出し
curl -X POST "https://gateway.agentbuilder.com/v1/prefabs/{prefab-id}/execute" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"function": "function_name", "parameters": {...}}'
```

**利用可能なPrefabを閲覧：**
```bash
cat prefabs/releases/community-prefabs.json | jq '.'
```

**独自のPrefabを作成：**
```bash
git clone https://github.com/The-Agent-Builder/Prefab-Template.git my-prefab
cd my-prefab
uv sync --dev
# 開発、テスト、公開
```

完全なPrefabドキュメント → [Prefabガイド](../../prefabs/README_zh.md)  
ゲートウェイ呼び出しの詳細 → [Prefab使用ガイド](../../prefabs/README_zh.md#対象ユーザーprefabの使用)

---

## コントリビュート

優れたツールにはコミュニティの知恵とコラボレーションが不可欠です。GTPlanner はあなたの参加を歓迎します！

### Prefabのコントリビュート（最も簡単な貢献方法）

**なぜPrefabを貢献するのか？**

各Prefabは以下を実現します：
- GTPlanner のプランニング能力を拡張
- 他の開発者の問題解決を支援
- 推奨システムに自動的に組み込まれる
- コミュニティの認識を獲得

**どのようにコントリビュートするか？**

1. テンプレートを使用してPrefabを作成 → [Prefab-Template](https://github.com/The-Agent-Builder/Prefab-Template)
2. 機能を開発してテスト
3. GitHub Releaseを公開して `.whl` ファイルをアップロード
4. `prefabs/releases/community-prefabs.json` にPRを提出

**Prefabの影響力：**
- **推奨システムに参加**: `community-prefabs.json` のPrefabはGTPlanner に認識される
- **スマートマッチング**: プランニング時に適切なシナリオに自動推奨
- **自動デプロイ**: PRマージ後、Prefabプラットフォームに自動デプロイ

詳細なコントリビューションガイド → [Prefabコントリビューションドキュメント](../../prefabs/releases/CONTRIBUTING_zh.md)

### コアコードのコントリビュート

評価駆動の開発方式を通じて、GTPlanner のプランニング品質とシステムパフォーマンスを向上させます。

コアコードのコントリビュート → [コントリビューションガイド](CONTRIBUTING.md)

### ケーススタディの共有

経験を共有して、コミュニティがGTPlanner の全ポテンシャルを発見するのを支援：

- **ユースケース**: 実際のプロジェクトでの応用
- **GTPlanner生成のPRD**: プランニング品質の展示
- **チュートリアルとベストプラクティス**: 新規ユーザーの立ち上げを支援

ケースを提出 → `docs/examples/community-cases/` にPRを作成

---

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細は [LICENSE](../../LICENSE.md) をご覧ください。

---

## 謝辞

- [PocketFlow](https://github.com/The-Pocket/PocketFlow) 非同期ワークフローエンジンに基づいて構築
- [Dynaconf](https://www.dynaconf.com/) による設定管理
- MCPプロトコルを通じたAIアシスタントとのシームレスな統合を目指して設計

---

<p align="center">
  <strong>GTPlanner</strong> - AIの力でアイデアを構造化された設計図に変換します。
</p>
