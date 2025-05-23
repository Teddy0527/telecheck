# 📞テレチェック (PoC)

テレアポ通話を **音声ファイル → 文字起こし (Whisper) → LLM によるチェック** というパイプラインで自動評価し、その結果を Google Sheets に書き込む "テレアポ品質監査ツール" です。

## 🚀 機能

- 音声ファイル（WAV/MP3/M4A）のアップロード
- OpenAI Whisper APIによる高精度な文字起こし
- LLMによる複数観点からの評価：
  - 自社紹介の適切さ
  - アプローチ方法の評価
  - 通話時間の適切さ分析
  - 顧客反応の分析
  - 話し方・マナーの評価
- Google Sheetsへの評価結果自動記録
- シンプルで使いやすいWebインターフェース（Streamlit）

## 🏁 クイックスタート（ローカル環境）

1. **リポジトリのクローン**

```bash
git clone <リポジトリURL> telecheck && cd telecheck
```

2. **Python仮想環境の準備と依存関係のインストール**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

3. **環境変数の設定**

```bash
cp .env.sample .env
# .envファイルを編集し、必要なAPIキーなどを設定
```

4. **Google Sheets連携用のサービスアカウント認証情報の配置**

- `service_account.json` ファイルをプロジェクトルートディレクトリに配置

5. **アプリケーションの実行**

```bash
streamlit run app.py
```

## 🐳 Dockerでの実行

```bash
# イメージのビルド
docker build -t sfida-telecheck .

# コンテナの実行
docker run --env-file .env -p 8501:8501 -v $(pwd)/service_account.json:/app/service_account.json sfida-telecheck
```

ブラウザで http://localhost:8501 にアクセスすると、アプリケーションのUIが表示されます。

## 📋 必要な環境変数

`.env`ファイルには以下の環境変数を設定してください：

```
# OpenAI / Whisper
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1

# Google Sheets
GSHEETS_SERVICE_ACCOUNT_JSON_PATH=service_account_teleap.json
SPREADSHEET_NAME=テレアポチェックシート
SHEET_NAME=Difyテスト
```

## サービスアカウントファイルの保存場所

サービスアカウントファイル（`service_account_teleap.json`）は、プロジェクトのルートディレクトリに保存してください。具体的には以下の場所です：

```
.
├── app.py
├── workflow.py
├── sheets_client.py
├── prompts.py
├── utils/
│   └── logger.py
├── service_account_teleap.json  <- ここに保存
└── ...
```

これで、アプリケーションは`service_account_teleap.json`ファイルを使用してGoogle Sheetsに接続するようになります。

## 注意点

1. 環境変数の変更後は、アプリケーションを再起動する必要があります
2. Dockerを使用している場合は、ボリュームマウントのパスが正確に一致していることを確認してください
3. サービスアカウントファイルは機密情報を含むため、Gitリポジトリにコミットしないよう注意してください
