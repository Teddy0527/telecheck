import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from workflow import run_pipeline
from sheets_client import append_row
from utils.logger import logger
import time
from faster_whisper import WhisperModel

# 環境変数を読み込む
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="SFIDA X テレチェック",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# テーマカラー
PRIMARY_COLOR = "#1E3A8A"
SECONDARY_COLOR = "#4F46E5"
BACKGROUND_COLOR = "#F3F4F6"

# カスタムテーマとスタイル設定
st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.5rem;
        color: {PRIMARY_COLOR};
        margin-bottom: 1rem;
    }}
    .section-header {{
        font-size: 1.8rem;
        color: {PRIMARY_COLOR};
        margin-top: 2rem;
        margin-bottom: 1rem;
    }}
    .results-container {{
        padding: 1.5rem;
        background-color: {BACKGROUND_COLOR};
        border-radius: 0.5rem;
        margin-top: 1rem;
        border-left: 5px solid {SECONDARY_COLOR};
    }}
    .info-text {{
        font-size: 1.2rem;
        line-height: 1.6;
    }}
    .footer {{
        margin-top: 3rem;
        text-align: center;
        color: #6B7280;
        padding: 1rem;
        border-top: 1px solid #E5E7EB;
    }}
    .stButton>button {{
        background-color: {SECONDARY_COLOR};
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }}
    .evaluation-metric {{
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }}
    div[data-testid="stExpander"] {{
        border: 1px solid #E5E7EB;
        border-radius: 0.3rem;
    }}
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

# 最新のStreamlitでファイルアップローダーを拡張
uploaded_file = st.file_uploader(
    "WAV, MP3, M4A形式の音声ファイルをアップロードしてください",
    type=["wav", "mp3", "m4a"],
    accept_multiple_files=False,
    help="最大ファイルサイズ: 200MB"
)

# メイン処理
if uploaded_file is not None:
    # ファイル情報の表示 - より洗練されたビジュアル表示
    file_size_kb = uploaded_file.size / 1024
    file_size_str = f"{file_size_kb:.2f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024:.2f} MB"
    
    file_info_col1, file_info_col2, file_info_col3 = st.columns(3)
    with file_info_col1:
        st.metric("ファイル名", uploaded_file.name)
    with file_info_col2:
        st.metric("ファイルタイプ", uploaded_file.type.split('/')[-1].upper())
    with file_info_col3:
        st.metric("ファイルサイズ", file_size_str)
    
    # 処理を開始するボタン - 改良されたUIでより目立つように
    start_button = st.button("🚀 評価を開始", type="primary", use_container_width=True)
    
    if start_button:
        # 処理状態を追跡するためのステータスコンテナ
        status_container = st.container()
        
        with st.spinner("処理中..."):
            try:
                # ステータスエリアの作成
                with status_container:
                    status = st.status("処理を開始しています...", expanded=True)
                    
                # モデルをロードする
                model = WhisperModel("medium", device="cpu", compute_type="int8")
                # GPUがある場合は device="cuda" も可能
                
                # 音声ファイルを読み込み
                file_bytes = uploaded_file.read()
                
                # Whisper文字起こしのプログレスバー - 動的な表示
                status.update(label="Whisper AIによる文字起こしを実行中...", state="running")
                progress_bar = st.progress(0)
                
                # 処理の進行状況を視覚的に表示
                for i in range(25):
                    time.sleep(0.01)  # 実際の処理速度に合わせて調整
                    progress_bar.progress(i/100)
                
                # ワークフロー実行準備
                status.update(label="評価チェックを準備中...", state="running")
                for i in range(25, 50):
                    time.sleep(0.01)
                    progress_bar.progress(i/100)
                
                # 最終的な処理を実行
                status.update(label="AIによる評価を実行中...", state="running")
                segments, info = model.transcribe(file_bytes, language="ja")
                transcript = " ".join([segment.text for segment in segments])
                result = run_pipeline(file_bytes)
                
                for i in range(50, 75):
                    time.sleep(0.01)
                    progress_bar.progress(i/100)
                
                # Sheetsに結果を保存
                status.update(label="Google Sheetsに結果を保存中...", state="running")
                try:
                    append_row([
                        result.get("テレアポ担当者名", "不明"), 
                        result.get("社名・担当者判定", "不明"), 
                        str(result)
                    ])
                    sheets_success = True
                    st.toast("Google Sheetsに結果を保存しました", icon="✅")
                except Exception as e:
                    sheets_success = False
                    logger.exception("Sheets書き込みエラー: %s", str(e))
                    st.warning(f"Google Sheetsへの書き込みに失敗しました: {e}")
                
                # 完了表示
                for i in range(75, 101):
                    time.sleep(0.01)
                    progress_bar.progress(i/100)
                
                status.update(label="評価が完了しました！", state="complete")
                
                # 結果の表示 - より見やすく構造化
                st.markdown('<h2 class="section-header">評価結果</h2>', unsafe_allow_html=True)
                st.markdown('<div class="results-container">', unsafe_allow_html=True)
                
                # 主要な評価指標を表示
                col1, col2 = st.columns(2)
                
                # 左カラム - 基本情報と総合評価
                with col1:
                    st.subheader("基本情報")
                    st.markdown(f'<div class="evaluation-metric">📋 <b>担当者:</b> {result.get("テレアポ担当者名", "不明")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="evaluation-metric">🎯 <b>総合評価:</b> {result.get("社名・担当者判定", "不明")}</div>', unsafe_allow_html=True)
                    
                    if "報告まとめ" in result and result["報告まとめ"]:
                        st.markdown('<div class="evaluation-metric">📝 <b>改善ポイント:</b></div>', unsafe_allow_html=True)
                        for point in result["報告まとめ"]:
                            st.markdown(f'<div style="margin-left: 1rem;">• {point}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="evaluation-metric">📝 <b>改善ポイント:</b> 特になし</div>', unsafe_allow_html=True)
                
                # 右カラム - カテゴリ別評価
                with col2:
                    st.subheader("主要評価項目")
                    
                    categories = {
                        "社名や担当者名を名乗らない": "🏢",
                        "アプローチで販売店名、ソフト名の先出し": "🎯",
                        "ロングコール": "⏱️",
                        "怒らせた": "👥",
                        "口調や態度が失礼": "🤝"
                    }
                    
                    for category, emoji in categories.items():
                        if category in result:
                            eval_result = result[category]
                            background_color = "#E5F6FD" if eval_result == "問題なし" else "#FEE2E2"
                            text_color = "#0369A1" if eval_result == "問題なし" else "#B91C1C"
                            st.markdown(
                                f'<div style="padding: 0.5rem; background-color: {background_color}; '
                                f'border-radius: 0.3rem; margin-bottom: 0.5rem; color: {text_color};">'
                                f'{emoji} <b>{category}:</b> {eval_result}</div>',
                                unsafe_allow_html=True
                            )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # タブを使用して詳細結果を整理
                tab1, tab2 = st.tabs(["詳細評価結果", "JSON データ"])
                
                with tab1:
                    # カテゴリごとに整理された詳細評価
                    evaluation_categories = [
                        {"title": "自社紹介", "keys": ["社名・担当者判定", "社名や担当者名を名乗らない"], "icon": "🏢"},
                        {"title": "アプローチ", "keys": ["アプローチで販売店名、ソフト名の先出し", "同業他社の悪口等", "2回断られても食い下がる"], "icon": "🎯"},
                        {"title": "通話マナー", "keys": ["ロングコール", "運転中や電車内でも無理やり続ける", "通話対応（無言電話／ガチャ切り）"], "icon": "📞"},
                        {"title": "顧客対応", "keys": ["口調や態度が失礼", "会話が成り立っていない", "怒らせた", "暴言を受けた"], "icon": "👥"},
                        {"title": "コンプライアンス", "keys": ["情報漏洩", "共犯（教唆・幇助）", "嘘・真偽不明"], "icon": "⚖️"}
                    ]
                    
                    for category in evaluation_categories:
                        with st.expander(f"{category['icon']} {category['title']}の詳細"):
                            for key in category["keys"]:
                                if key in result:
                                    st.markdown(f"**{key}:** {result[key]}")
                
                with tab2:
                    # JSON形式で表示
                    st.json(result)
                
                # Google Sheets連携結果
                if sheets_success:
                    st.success("評価結果はGoogle Sheetsに正常に保存されました。", icon="✅")
                
            except Exception as e:
                st.error(f"評価処理中にエラーが発生しました: {e}")
                logger.exception("評価処理エラー: %s", str(e))
                st.error("詳細なエラー情報はログファイルを確認してください。")

# フッター
st.markdown('<div class="footer">SFIDA X テレチェック PoC v1.0.0</div>', unsafe_allow_html=True)

# ローカルWhisperを使用する関数
def whisper_transcribe_local(file_bytes: bytes) -> str:
    """
    ローカルWhisperモデルを使用して音声を文字起こし
    
    Args:
        file_bytes (bytes): 音声ファイルのバイト
        
    Returns:
        str: 文字起こしテキスト
    """
    import tempfile
    from faster_whisper import WhisperModel
    
    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
        temp_file.write(file_bytes)
        temp_file.flush()
        
        # モデルをロード（初回実行時にダウンロードされます）
        model = WhisperModel("medium", device="cpu", compute_type="int8")
        
        # 文字起こし実行（日本語を指定）
        segments, info = model.transcribe(temp_file.name, language="ja")
        transcript = " ".join([segment.text for segment in segments])
        
    return transcript 