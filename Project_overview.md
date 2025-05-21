# 📁 Project: sfida-telecheck (PoC)

## 🏁 Quick Start – Cursor 開発者向け指示

1. **このリポジトリを Clone**

   ```bash
   gh repo clone sfida-x/telecheck && cd telecheck
   ```
2. **Python 仮想環境を準備 → 依存インストール**

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **環境変数をセット**

   * `.env.sample` をコピーして `.env` を作成し、API キーを入力。
   * `service_account.json` をプロジェクト直下に配置（Sheets 用）。
4. **Cursor でワークスペースを開く**

   * 推奨設定が自動で読み込まれるので、`app.py` を Run するとブラウザ UI が立ち上がります。
5. **Vibe Coding 活用例**

   * ファイル新規作成: `vibe: create app.py skeleton for streamlit uploader`
   * リファクタ: `vibe: refactor this function using logger and error handling`
   * ドキュメント生成: `vibe: generate markdown explaining run_pipeline()`
6. **Docker で一発検証**

   ```bash
   docker build -t telecheck .
   docker run --env-file .env -p 8501:8501 -v $(pwd)/service_account.json:/app/service_account.json telecheck
   ```
7. **コミット指針**

   * Conventional Commits (`feat:`, `fix:`, `docs:` …)。
   * Black で整形 & pylint clean を CI 条件に設定予定。

---

## Overview

SFIDA X のテレアポ通話を **音声ファイル → 文字起こし (Whisper) → LLM によるチェック** というパイプラインで自動評価し、その結果を Google Sheets に書き込む "テレアポ品質監査ツール" です。ブラウザ UI（Streamlit）から音声をドラッグ & ドロップするだけで、社内担当者・クライアント双方がワンクリックで検査を実行できます。PoC では以下 3 点が成立すれば成功と定義します。

1. **UX**: 1 クリック Docker 起動 → ファイルをアップ → 数十秒で結果表示
2. **再現性**: `.env` と `service_account.json` さえ用意すれば誰でも同一環境を再構築可能
3. **拡張性**: コアロジックと I/O（UI / Sheets）が疎結合で、後続フェーズのバッチ処理や SSO 導入に備えた構成

> **Goal**: 1‑click Docker run 👉 Browser UI 👉 Upload audio 👉 Whisper STT 👉 LLM check 👉 Google Sheets write‑back

---

## 1. Directory / File Tree

```
.
├── README.md                # How to run / env setup / architecture diagram
├── .gitignore               # Python, venv, logs, .env, __pycache__ …
├── .env.sample              # Template for required env vars
├── requirements.txt         # Pinned Python deps
├── prompts.py               # SYSTEM_PROMPTS = { … }  ← ★ 追加
├── app.py                   # Streamlit entry‑point (UI layer)
├── workflow.py              # STT + LLM logic (pure functions)
├── sheets_client.py         # Google Sheets wrapper (I/O boundary)
├── utils/
│   └── logger.py            # Standardised logging config
├── Dockerfile               # Multi‑stage build → final minimal image
├── .dockerignore            # exclude venv, cache, docs …
└── tests/                   # (optional) pytest suites
    ├── __init__.py
    └── test_workflow.py
```

> **Minimal PoC** では `app.py` / `workflow.py` / `sheets_client.py` の3モジュールだけで動作。その他は開発・配布補助。

---

## 2. Environment Variables (`.env.sample`)

```dotenv
# OpenAI / Whisper
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1              # API model name

# Google Sheets
GSHEETS_SERVICE_ACCOUNT_JSON_PATH=service_account.json
SPREADSHEET_NAME=テレアポチェックシート
SHEET_NAME=Difyテスト
```

---

## 3. `requirements.txt`

```txt
streamlit==1.34.0
openai==1.25.1
gspread==6.0.2
google-auth==2.29.0
python-dotenv==1.0.1
pandas==2.2.2
```

---

## 4. Module Responsibilities & Skeleton Code

### 4.1 `utils/logger.py`

```python
import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telecheck")
```

### 4.2 `sheets_client.py`

```python
import os, json, gspread, google.auth
from utils.logger import logger

SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_NAME       = os.getenv("SHEET_NAME")

_default_ws = None  # lazy‑loaded worksheet cache

def _authorize():
    creds_path = os.getenv("GSHEETS_SERVICE_ACCOUNT_JSON_PATH")
    if not creds_path:
        raise RuntimeError("GSHEETS_SERVICE_ACCOUNT_JSON_PATH not set")
    with open(creds_path, "r", encoding="utf-8") as f:
        creds_dict = json.load(f)
    creds = google.oauth2.service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def get_ws():
    global _default_ws
    if _default_ws:
        return _default_ws
    gc = _authorize()
    _default_ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    return _default_ws

def append_row(values: list[str]):
    ws = get_ws()
    ws.append_row(values, value_input_option="USER_ENTERED")
    logger.info("Appended row: %s", values)
```

### 4.3 `prompts.py`

```python
"""Single source of truth for all LLM system prompts."""
# 個別プロンプトは非常に長いためここでは省略
# 実際のファイルでは各キーに対し巨大な文字列を格納してください。

SYSTEM_PROMPTS: dict[str, str] = {
    "replace": "...",
    "speaker": "...",
    "company_check": "...",
    "approach_check": "...",
    "longcall": "...",
    "customer_react": "...",
    "manner": "...",
    "to_json": "...",
}
```

### 4.4 `workflow.py`

```python
"""Pure functions: transcription + LLM QA → dict result"""
import os, json, textwrap, openai
from utils.logger import logger
from prompts import SYSTEM_PROMPTS  # ★ 追加

openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "whisper-1")

# ---------- helpers ----------

def whisper_transcribe(file_bytes: bytes) -> str:
    """Call Whisper API and return full transcript string"""
    resp = openai.audio.transcriptions.create(
        model=WHISPER_MODEL,
        file=("audio.wav", file_bytes, "audio/wav")
    )
    return resp.text


def _chat(system_prompt, user_prompt, *, expect_json=False, temperature=0.0):
    params = dict(
        model=OPENAI_MODEL,
        messages=[{"role":"system", "content": system_prompt},
                  {"role":"user",   "content": user_prompt}],
        temperature=temperature,
    )
    if expect_json:
        params["response_format"] = {"type": "json_object"}
    return openai.chat.completions.create(**params).choices[0].message.content.strip()

# ---------- node wrappers ----------
# Colab と同一の node_replace, node_speaker_separation, ... を SYSTEM_PROMPTS に合わせて実装

# ---------- public entrypoint ----------

def run_pipeline(file_bytes: bytes) -> dict:
    txt = whisper_transcribe(file_bytes)
    logger.info("Whisper done (%d chars)", len(txt))
    result_json = run_workflow(txt)  # 既存ロジックそのまま
    return result_json
```

### 4.4 `app.py` (Streamlit)

```python
import streamlit as st, pandas as pd, os
from workflow import run_pipeline
from sheets_client import append_row
from utils.logger import logger

st.set_page_config(page_title="SFIDA Tele‑Check", page_icon="📞")

st.title("📞 SFIDA Tele‑Check (PoC)")
file = st.file_uploader("音声ファイルをアップロード", type=["wav", "mp3", "m4a"])

if file is not None:
    with st.spinner("Whisper 文字起こし中…"):
        try:
            result = run_pipeline(file.read())
        except Exception as e:
            st.error(f"処理失敗: {e}")
            logger.exception("pipeline error")
            st.stop()
    st.success("解析完了！結果を表示します")
    st.json(result, expanded=False)

    # シート書き込み
    with st.spinner("Sheets へ書き込み中…"):
        try:
            append_row([result.get("担当者"), result.get("評価"), str(result)])
            st.toast("Sheets 更新完了", icon="✅")
        except Exception as e:
            st.warning(f"Sheets 書き込み失敗: {e}")
```

### 4.5 `Dockerfile`

```dockerfile
# ----- Builder stage -----
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# ----- Final stage -----
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . /app
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

---

## 5. README.md (抜粋)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.sample .env  # keys を入力
streamlit run app.py
```

### Quick Start (Docker)

```bash
# 初回のみ
docker build -t sfida-telecheck:latest .
# 実行
docker run --env-file .env -p 8501:8501 -v $(pwd)/service_account.json:/app/service_account.json sfida-telecheck:latest
```

---

## 6. Cursor + Vibe Coding 開発フロー Tips
Cursor の "Vibe" AI 機能を活かすと、ペアプログラミングのようにコード生成・リファクタ・ドキュメント作成を高速化できます。以下ワークフロー例を推奨します。

| フェーズ | Vibe へのプロンプト例 | 期待アウトプット |
|---------|----------------------|-----------------|
| **Skeleton 作成** | `vibe: create a streamlit skeleton with file uploader and placeholder columns.` | `app.py` 雛形 + UI コメント |
| **LLM ノード実装** | 選択範囲で <br>`vibe: convert this pseudo code into a python function using SYSTEM_PROMPTS['company_check']` | 完全な `node_company_check` 実装 |
| **テスト生成** | `vibe: write pytest for run_pipeline with dummy audio bytes` | `tests/test_workflow.py` 自動生成 |
| **環境追加** | `vibe: add watchdog to requirements and create watchdog_cli.py that monitors ./input_audio` | 新規ファイル & 依存追記 |
| **ドキュメント補完** | `vibe: explain what this Dockerfile does step by step in markdown` | README 追記用テキスト |

🔑 **コツ**: Vibe のチャット欄へは *「目的 + 制約 + 期待形式」* を明示すると高品質な出力になります。

### 推奨 Editor 設定 (`.vscode/settings.json`)
```json
{
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll": true
  },
  "python.formatting.provider": "black",
  "python.linting.pylintEnabled": true
}
```

これをコミットしておけば、チーム全員が同じフォーマット＆Lint を共有できます。

---

##
