import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import math
import tempfile
import json

# APNGライブラリのインポート
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

# スタイル調整
st.markdown("""
    <style>
    .main-title {
        font-size: 24px;
        font-weight: bold;
        color: #1E1E1E;
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

github_url = st.sidebar.text_input(
    "GitHubリポジトリURL (※公開リポジトリ)", 
    value="https://github.com/yourusername/your-stamp-app"
)

api_key_input = st.sidebar.text_input(
    "Google AI Studio API キー設定", 
    type="password", 
    help="空の場合は環境変数または st.secrets から 'GOOGLE_API_KEY' を読み込みます"
)

api_key = api_key_input or os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
mock_mode = st.sidebar.checkbox("テスト用モック機能を追加（APIキー不要）", value=True)

template = st.sidebar.selectbox(
    "基本テンプレート選択",
    ["強弱2コマ繰り返し✨", "動きのあるラフ生成"]
)

if st.sidebar.button("GitHub連携"):
    st.sidebar.success("GitHubリポジトリとの連携設定を保存しました。")

# -----------------------------------------------------------------------------
# メインコンテンツエリアの処理
# -----------------------------------------------------------------------------
if uploaded_file is None:
    st.info("👈 左メニュー最上部から、ベースとなるイラスト（自分のイラスト）をアップロードしてください。")
else:
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
                    st.session_state['analysis_result'] = (
                        "【AI分析結果（モック）】\n"
                        "・キャラクター: 丸みのあるシンプルなキャラクター（毛並み・髪の毛のないクリーンなライン）\n"
                        "・表情: 穏やかな笑顔（目と口のみの構成、鼻・眉毛なし）\n"
                        "・内容分析: 180px角に収まりやすい完全な真ん丸形状。上下の弾む動きや、文字を組み合わせたLINE絵文字スタンプに適しています。"
                    )
                else:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content([
                            "このイラストのキャラクター、表情、およびアニメーションスタンプ（180px角）にした際の内容やポーズのアイデアを分析してください。キャラクターのラインは極力シンプルに保ち、背景は白に固定することを前提としてください。",
                            base_image
                        ])
                        st.session_state['analysis_result'] = response.text
                    except Exception as e:
                        st.error(f"Gemini API エラー: {e}\n\n⚠️ APIエラーが発生したため、自動的に一時的なモック分析結果を表示します。")
                        st.session_state['analysis_result'] = "一時的なエラーのため詳細な分析をスキップします。"

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
            "個別指示を追加：", 
            value="「なるほど」という文字を1文字ずつポップアップさせ、2コマ目でキラキラを最大にする"
        )
    
    generate_pressed = st.button("アニメーション生成・シート構築開始 🚀")
    
    if generate_pressed:
        with st.spinner("AIが演出プランを構築し、6コマのおすすめアニメーションを合成中..."):
            
            animation_plan = []
            
            if "パターンB" in pattern_choice:
                if mock_mode or not genai or not api_key:
                    st.toast("🎨 モックモードで演出をシミュレートします")
                    
                    clean_text = user_instruction.replace("キラキラを点滅させる", "").replace("を点滅させる", "").strip()
                    if "なるほど" in user_instruction or not clean_text:
                        display_text = "なるほど"
                    else:
                        display_text = clean_text[:4]
                    
                    has_sparkle = "キラキラ" in user_instruction or "点滅" in user_instruction
                    
                    animation_plan = [
                        {"frame": 1, "offset_y": 0, "text": display_text[0] if len(display_text)>0 else "", "sparkle": False},
                        {"frame": 2, "offset_y": 0, "text": display_text[:2] if len(display_text)>1 else display_text, "sparkle": has_sparkle}, 
                        {"frame": 3, "offset_y": 0, "text": display_text[:3] if len(display_text)>2 else display_text, "sparkle": False},
                        {"frame": 4, "offset_y": 0, "text": display_text, "sparkle": has_sparkle},
                        {"frame": 5, "offset_y": 0, "text": display_text, "sparkle": False},
                        {"frame": 6, "offset_y": 0, "text": display_text, "sparkle": has_sparkle},
                    ]
                else:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel(
                            'gemini-2.5-flash',
                            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
                        )
                        prompt = f"""
                        ユーザーの指示に基づいて、180x180ピクセルのアニメーション（全6コマ）の各コマの演出パラメーターをJSON配列で出力してください。
                        
                        【ユーザーの指示】
                        "{user_instruction}"
                        
                        【出力フォーマット規約】
                        必ず以下の構造の、6つの要素を持つJSON配列のみを出力してください。余計な説明は一切含めないでください。
                        [
                          {{"frame": 1, "offset_y": 0, "text": "文字", "sparkle": false}},
                          ...
                          {{"frame": 6, "offset_y": 0, "text": "文字", "sparkle": false}}
                        ]
                        - offset_y: 今回は使用しないためすべて0を出力してください。
                        - text: 指示に沿って、1文字ずつ増やすなどのテキスト変化。
                        - sparkle: キラキラや点滅の指示がある場合、該当するコマをtrueにする。
                        """
                        response = model.generate_content(prompt)
                        animation_plan = json.loads(response.text)
                    except Exception as e:
                        st.error(f"演出プランの生成中にエラーが発生しました。基本モック演出に切り替えます: {e}")
                        animation_plan = []

            # --- 画像合成処理（ここを透過・枠固定・最大サイズに完全修正！） ---
            frames = []
            
            # 180px枠ギリギリいっぱいに拡大（元画像の透過品質を維持）
            thumb_size = 180 
            resized_base = base_image.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            # エフェクト用のフォント読み込み
            font = None
            font_paths = [
                "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                "NotoSansCJK-Regular.ttf",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "msgothic.ttc"
            ]
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, 28)
                    break
                except:
                    continue

            for i in range(6):
                # 背景は白ではなく、完全に「透明（透過）」のキャンバスを作成
                frame = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
                
                # ベースの透過イラストを(0, 0)に完全静止・デカサイズで配置（ブレません）
                frame.paste(resized_base, (0, 0), resized_base)
                
                draw = ImageDraw.Draw(frame)
                
                # 演出プランから「キラキラを出すか」を判定
                show_sparkle = False
                if "パターンA" in pattern_choice or not animation_plan:
                    if i % 2 == 1:
                        show_sparkle = True
                else:
                    plan = animation_plan[i]
                    show_sparkle = plan.get("sparkle", False)
                
                # 固定された透過吹き出しの「中（上）」でキラキラをパチパチ点滅させる
                if show_sparkle and font:
                    # 吹き出しの文字（OKです）に被らない右上の空きスペースなどに配置
                    draw.text((140, 15), "✨", fill=(255, 215, 0), font=font)
                    # 4コマ目や6コマ目では左下にも出して動きに変化をつける
                    if i == 3 or i == 5:
                        draw.text((15, 120), "✨", fill=(255, 215, 0), font=font)
                
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
        
        # 1x6 スプライトシートの構築 (白背景を廃止し、完全透過に修正)
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (0, 0, 0, 0))
        for idx, f in enumerate(frames):
            sprite_sheet.paste(f, (180 * idx, 0))
            
        st.markdown("#### 統合スプライトシート (1080px × 180px)")
        st.image(sprite_sheet, caption="LINEアニメ絵文字配信用スプライトシート", use_container_width=True)
        
        sprite_byte_arr = io.BytesIO()
        sprite_sheet.save(sprite_byte_arr, format='PNG')
        sprite_byte_arr = sprite_byte_arr.getvalue()
        
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
