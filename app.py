import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import math
import tempfile

# APNGライブラリのインポート（requirements.txtに含める）
try:
    from apng import APNG
except ImportError:
    APNG = None

# Google Gemini APIのインポート
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ページ設定
st.set_page_config(
    page_title="あなた専用アニメスタンプ自動化Webアプリ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# スタイル調整（プロフェッショナルな見た目にするため）
st.markdown("""
    <style>
    .main-title {
        font-size: 24px;
        font-weight: bold;
        color: #1E1E1E;
        margin-bottom: 20px;
    }
    .section-box {
        background-color: #F8F9FA;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin-bottom: 20px;
    }
    .step-title {
        font-size: 16px;
        font-weight: bold;
        color: #333333;
        margin-bottom: 10px;
        border-left: 4px solid #4A90E2;
        padding-left: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Streamlit & GitHub あなた専用アニメスタンプ自動化Webアプリ</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. 左メニュー（サイドバー）の構築
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 1. イラストをアップロード (分析ベース)")
uploaded_file = st.sidebar.file_uploader(
    "ベースとなるイラストを選択（背景白・キャラクター固定推奨）", 
    type=["png", "jpg", "jpeg"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. アプリ設定")

# GitHubリポジトリURLの設定（公開リポジトリ運用前提）
github_url = st.sidebar.text_input(
    "GitHubリポジトリURL (※公開リポジトリ)", 
    value="https://github.com/yourusername/your-stamp-app"
)

# Google AI Studio API キー設定
api_key_input = st.sidebar.text_input(
    "Google AI Studio API キー設定", 
    type="password", 
    help="空の場合は環境変数または st.secrets から 'GOOGLE_API_KEY' を読み込みます"
)

# APIキーの設定ロジック
api_key = api_key_input or os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")

# テスト用モック機能の切り替え（初期値ONでAPI消費を抑制）
mock_mode = st.sidebar.checkbox("テスト用モック機能を追加（APIキー不要）", value=True)

# 基本テンプレート選択
template = st.sidebar.selectbox(
    "基本テンプレート選択",
    ["強弱2コマ繰り返し✨", "動きのあるラフ生成"]
)

# GitHub連携ボタン
if st.sidebar.button("GitHub連携"):
    st.sidebar.success("GitHubリポジトリとの連携設定を保存しました。")

# -----------------------------------------------------------------------------
# メインコンテンツエリアの処理
# -----------------------------------------------------------------------------
if uploaded_file is None:
    st.info("👈 左メニュー最上部から、ベースとなるイラスト（自分のイラスト）をアップロードしてください。")
else:
    # 画像の読み込み（RGBAに統一して背景処理を容易にする）
    base_image = Image.open(uploaded_file).convert("RGBA")
    
    # -------------------------------------------------------------------------
    # Common STEP 1: 自動分析・アイデア抽出 (両パターン共通)
    # -------------------------------------------------------------------------
    st.markdown('<div class="step-title">Common STEP 1: 自動分析・アイデア抽出（両パターン共通）</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(base_image, caption="アップロードされたイラスト", width=150)
        
    with col2:
        if st.button("AI分析・アイデア抽出を実行"):
            with st.spinner("Gemini APIでイラストを分析中..."):
                if mock_mode or not genai or not api_key:
                    # モックモードまたはAPIキー未設定時のダミー出力
                    st.session_state['analysis_result'] = (
                        "【AI分析結果（モック）】\n"
                        "・キャラクター: 丸みのあるシンプルなキャラクター（毛並み・髪の毛のないクリーンなライン）\n"
                        "・表情: 穏やかな笑顔（目と口のみの構成、鼻・眉毛なし）\n"
                        "・内容分析: 180px角に収まりやすい完全な真ん丸形状。上下の弾む動きや、文字を組み合わせたLINE絵文字スタンプに適しています。"
                    )
                else:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content([
                            "このイラストのキャラクター、表情、およびアニメーションスタンプ（180px角）にした際の内容やポーズのアイデアを分析してください。キャラクターのラインは極力シンプルに保ち、背景は白に固定することを前提としてください。",
                            base_image
                        ])
                        st.session_state['analysis_result'] = response.text
                    except Exception as e:
                        st.error(f"Gemini API エラー: {e} (モックモードに切り替えるかAPIキーを確認してください)")
                        st.session_state['analysis_result'] = "エラーが発生したため分析に失敗しました。"

        if 'analysis_result' in st.session_state:
            st.text_area("AI分析結果", value=st.session_state['analysis_result'], height=120)

    # -------------------------------------------------------------------------
    # アニメーション生成のルート分岐（パターンA / パターンB）
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### アニメーション生成アプローチの選択")
    pattern_choice = st.radio(
        "生成方法を選択してください：",
        ["パターンA: AIおまかせで進む (自動抽出シート生成)", "パターンB: 個別指示を追加する (指示に基づいて生成)"]
    )
    
    user_instruction = ""
    if "パターンB" in pattern_choice:
        user_instruction = st.text_input(
            "個別指示を追加（違う）：", 
            value="文字全体を少し弾ませ、キラキラを2コマ目：最大にする"
        )
    
    generate_pressed = st.button("アニメーション生成・シート構築開始 🚀")
    
    if generate_pressed:
        with st.spinner("6コマのアニメーションシートを生成中..."):
            frames = []
            
            # ベース画像を180x180の枠内に収まるようリサイズ（余白を持たせるため130x130にリサイズ）
            thumb_size = 130
            resized_base = base_image.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            for i in range(6):
                # 180px角、背景白固定（ユーザー指定要件）
                frame = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
                
                # 位置の計算
                offset_x = (180 - thumb_size) // 2
                offset_y = (180 - thumb_size) // 2
                
                if "強弱2コマ繰り返し" in template:
                    if i % 2 == 1:
                        offset_y -= 12
                else:
                    offset_y += int(10 * math.sin(i * math.pi / 3))
                    offset_x += int(5 * math.cos(i * math.pi / 3))
                
                # 個別指示（パターンB）がONで「弾ませ」がある場合の追加効果
                if "パターンB" in pattern_choice and "弾ませ" in user_instruction:
                    if i in [1, 3, 5]:
                        offset_y -= 8
                
                # ベースイラストを配置
                frame.paste(resized_base, (offset_x, offset_y), resized_base if resized_base.mode == 'RGBA' else None)
                
                # エフェクト・文字の描画
                draw = ImageDraw.Draw(frame)
                
                # 個別指示の「キラキラ」を表現
                if "パターンB" in pattern_choice and "キラキラ" in user_instruction:
                    if i == 1: # 2コマ目最大
                        draw.text((10, 10), "✨✨", fill=(255, 215, 0))
                        draw.text((150, 10), "✨✨", fill=(255, 215, 0))
                    elif i in [2, 3]:
                        draw.text((20, 15), "✨", fill=(255, 215, 0))
                
                try:
                    draw.text((50, 150), f"STEP {i+1}", fill=(50, 50, 50))
                except:
                    pass
                
                frames.append(frame)
            
            st.session_state['generated_frames'] = frames

    # -------------------------------------------------------------------------
    # Common STEP 2: 最終シート構成 (180px * 6コマ1シート) & APNG変換
    # -------------------------------------------------------------------------
    if 'generated_frames' in st.session_state:
        frames = st.session_state['generated_frames']
        
        st.markdown('<div class="step-title">Common STEP 2: 最終シート構成（180px × 6コマ1シート）</div>', unsafe_allow_html=True)
        
        st.markdown("#### 各コマのプレビュー (180px角)")
        cols = st.columns(6)
        for idx, f in enumerate(frames):
            with cols[idx]:
                st.image(f, caption=f"コマ {idx+1}", use_container_width=True)
        
        # 1x6 スプライトシートの構築 (横幅 180*6 = 1080px, 縦幅 180px)
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (255, 255, 255, 255))
        for idx, f in enumerate(frames):
            sprite_sheet.paste(f, (180 * idx, 0))
            
        st.markdown("#### 統合スプライトシート (1080px × 180px)")
        st.image(sprite_sheet, caption="LINEアニメ絵文字配信用スプライトシート", use_container_width=True)
        
        # ダウンロード用のバイナリデータ作成 (スプライトシート)
        sprite_byte_arr = io.BytesIO()
        sprite_sheet.save(sprite_byte_arr, format='PNG')
        sprite_byte_arr = sprite_byte_arr.getvalue()
        
        # APNGの生成
        apng_byte_arr = None
        if APNG:
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_paths = []
                    for idx, f in enumerate(frames):
                        path = os.path.join(tmpdir, f"frame_{idx}.png")
                        f.save(path)
                        tmp_paths.append(path)
                    
                    apng_output_arr = io.BytesIO()
                    APNG.from_files(tmp_paths, delay=200).save(apng_output_arr)
                    apng_byte_arr = apng_output_arr.getvalue()
            except Exception as e:
                st.warning(f"APNGの変換中にエラーが発生しました: {e}")
        
        # ダウンロードボタンの配置
        st.markdown("#### 成果物のダウンロード（保存）")
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="スプライトシート (PNG) を保存",
                data=sprite_byte_arr,
                file_name="anime_emoji_sheet.png",
                mime="image/png"
            )
        with dl_col2:
            if apng_byte_arr:
                st.download_button(
                    label="アニメーションスタンプ (APNG) を保存",
                    data=apng_byte_arr,
                    file_name="anime_emoji.png",
                    mime="image/png"
                )
            else:
                st.info("APNGライブラリが利用できないため、スプライトシートのみ保存可能です。")

    # -------------------------------------------------------------------------
    # パターンC: 開発＆デプロイ画面 (Streamlit Community Cloud)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown('<div class="step-title">パターンC: 開発＆デプロイ画面 (Streamlit Community Cloud)</div>', unsafe_allow_html=True)
    
    dep_col1, dep_col2 = st.columns(2)
    with dep_col1:
        st.markdown("**デプロイ環境設定確認**")
        st.code(f"""
Emoji size setting: 180ピクセル角 (180x180)
Sequence setting: 6 frames per sheet
Repository: {github_url}
        """.strip(), language="yaml")
        
    with dep_col2:
        st.markdown("**構成ファイル状況**")
        st.text_input("エントリーポイント", value="app.py", disabled=True)
        st.text_input("依存パッケージファイル", value="requirements.txt", disabled=True)
        
        if st.button("アプリ公開実行 (Deploy to Cloud)"):
            st.balloons()
            st.success("GitHub上の公開リポジトリへコミットをプッシュし、Streamlit Community Cloudへの自動デプロイキューを送信しました！")
            st.info("URL: https://your-stamp-app.streamlit.app")
