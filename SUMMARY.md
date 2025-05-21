# SFIDA X テレチェック プロジェクト構築まとめ

## 概要

このプロジェクトは、SFIDA X のテレアポ通話を自動評価するツールです。音声ファイルをアップロードすると、以下のパイプラインで処理されます：

1. 音声ファイルをWhisper APIで文字起こし
2. 文字起こしされたテキストをLLMで複数の観点から評価
3. 評価結果をGoogle Sheetsに記録

## プロジェクト構成

```
.
├── app.py                  # Streamlit UI
├── workflow.py             # 文字起こし・評価ロジック
├── sheets_client.py        # Google Sheets連携
├── prompts.py              # LLMプロンプト定義
├── utils/
│   ├── __init__.py
│   └── logger.py           # ロギング設定
├── tests/
│   ├── __init__.py
│   └── test_workflow.py    # ワークフローのテスト
├── requirements.txt        # 依存パッケージ
├── .env.sample             # 環境変数サンプル
├── Dockerfile              # Dockerビルド設定
├── .dockerignore           # Dockerビルド除外設定
├── .vscode/
│   └── settings.json       # VSCode設定
└── README.md               # プロジェクト説明
```

## 主要コンポーネント

1. **Streamlit UI (app.py)**
   - 音声ファイルのアップロード
   - 処理進捗の表示
   - 評価結果の可視化

2. **ワークフローロジック (workflow.py)**
   - Whisper APIによる文字起こし
   - LLMを使用した評価処理
   - 評価結果の統合

3. **Google Sheets連携 (sheets_client.py)**
   - サービスアカウントを使用した認証
   - 評価結果の保存

4. **プロンプト管理 (prompts.py)**
   - 各評価項目に対するLLMプロンプトの定義

## デプロイ方法

### ローカル開発環境

```bash
# リポジトリのクローン
git clone <リポジトリURL> telecheck && cd telecheck

# Python仮想環境の準備と依存関係のインストール
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 環境変数の設定
cp .env.sample .env
# .envファイルを編集

# アプリケーションの実行
streamlit run app.py
```

### Docker環境

```bash
# イメージのビルド
docker build -t sfida-telecheck .

# コンテナの実行
docker run --env-file .env -p 8501:8501 -v $(pwd)/service_account.json:/app/service_account.json sfida-telecheck
```

## 次のステップ

1. **機能拡張**
   - バッチ処理モードの追加
   - より詳細な分析オプション

2. **UI改善**
   - ダッシュボード機能の強化
   - 過去の評価結果の閲覧機能

3. **統合・自動化**
   - CI/CDパイプラインの構築
   - 自動テストの拡充 