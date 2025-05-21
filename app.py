import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from workflow import run_pipeline
from sheets_client import append_row
from utils.logger import logger

# 環境変数を読み込む
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="SFIDA X テレチェック",
    page_icon="📞",
    layout="wide"
)

# スタイル設定
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
    }
    .section-header {
        font-size: 1.8rem;
        color: #1E3A8A;
        margin-top: 2rem;
    }
    .results-container {
        padding: 1.5rem;
        background-color: #F3F4F6;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .info-text {
        font-size: 1.2rem;
    }
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #6B7280;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown('<h1 class="main-header">📞 SFIDA X テレチェック (PoC)</h1>', unsafe_allow_html=True)

# 説明テキスト
st.markdown("""
<p class="info-text">
テレアポ通話の録音ファイルをアップロードして、AIによる自動評価を実行します。
評価結果はGoogleスプレッドシートに自動的に記録されます。
</p>
""", unsafe_allow_html=True)

# ファイルアップローダー
st.markdown('<h2 class="section-header">音声ファイルのアップロード</h2>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("WAV, MP3, M4A形式の音声ファイルをアップロードしてください", type=["wav", "mp3", "m4a"])

# メイン処理
if uploaded_file is not None:
    # ファイル情報の表示
    file_details = {
        "ファイル名": uploaded_file.name,
        "ファイルタイプ": uploaded_file.type,
        "ファイルサイズ": f"{uploaded_file.size / 1024:.2f} KB"
    }
    
    st.write("アップロードされたファイル:")
    st.json(file_details)
    
    # 処理を開始するボタン
    if st.button("評価を開始", type="primary"):
        with st.spinner("音声を処理中..."):
            try:
                # 音声ファイルを読み込み
                file_bytes = uploaded_file.read()
                
                # Whisper文字起こしのプログレスバー
                progress_text = "Whisper AIによる文字起こしを実行中..."
                progress_bar = st.progress(0)
                st.text(progress_text)
                progress_bar.progress(25)
                
                # ワークフローを実行
                st.text("評価チェックを実行中...")
                progress_bar.progress(50)
                
                # 最終的な処理を実行
                result = run_pipeline(file_bytes)
                progress_bar.progress(75)
                
                # Sheetsに結果を保存
                try:
                    append_row([
                        result.get("担当者", "不明"), 
                        result.get("評価", "不明"), 
                        str(result)
                    ])
                    sheets_success = True
                    st.toast("Google Sheetsに結果を保存しました", icon="✅")
                except Exception as e:
                    sheets_success = False
                    logger.exception("Sheets書き込みエラー: %s", str(e))
                    st.warning(f"Google Sheetsへの書き込みに失敗しました: {e}")
                
                progress_bar.progress(100)
                
                # 結果の表示
                st.markdown('<h2 class="section-header">評価結果</h2>', unsafe_allow_html=True)
                st.markdown('<div class="results-container">', unsafe_allow_html=True)
                
                # 主要な評価指標を表示
                col1, col2 = st.columns(2)
                
                # 左カラム - 基本情報と総合評価
                with col1:
                    st.subheader("基本情報")
                    st.write(f"📋 担当者: {result.get('担当者', '不明')}")
                    st.write(f"🎯 総合評価: {result.get('評価', '不明')}")
                    st.write(f"📝 改善ポイント: {result.get('改善ポイント', '特になし')}")
                
                # 右カラム - カテゴリ別評価
                with col2:
                    st.subheader("カテゴリ別評価")
                    
                    categories = {
                        "自社紹介": "🏢",
                        "アプローチ": "🎯",
                        "通話時間": "⏱️",
                        "顧客反応": "👥",
                        "マナー": "🤝"
                    }
                    
                    for category, emoji in categories.items():
                        if category in result:
                            if isinstance(result[category], dict) and "総合評価" in result[category]:
                                eval_result = result[category]["総合評価"]
                                st.write(f"{emoji} {category}: {eval_result}")
                            else:
                                st.write(f"{emoji} {category}: データなし")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 詳細な結果をJSON形式で表示
                with st.expander("詳細な評価結果を表示"):
                    st.json(result)
                
                # Google Sheets連携結果
                if sheets_success:
                    st.success("評価結果はGoogle Sheetsに正常に保存されました。")
                
            except Exception as e:
                st.error(f"評価処理中にエラーが発生しました: {e}")
                logger.exception("評価処理エラー: %s", str(e))

# フッター
st.markdown('<div class="footer">SFIDA X テレチェック PoC v0.1.0</div>', unsafe_allow_html=True) 