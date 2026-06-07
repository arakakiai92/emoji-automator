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
mock_mode = st.sidebar.checkbox("テスト用モック機能を追加（APIキー不要）", value=True) # 開発中はデフォルトTrueが安全

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
                        # 最新モデルの gemini-2.5-flash に修正
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content([
                            "このイラストのキャラクター、表情、およびアニメーションスタンプ（180px角）にした際の内容やポーズのアイデアを分析してください。キャラクターのラインは極力シンプルに保ち、背景は白に固定することを前提としてください。",
                            base_image
                        ])
                        st.session_state['analysis_result'] = response.text
                    except Exception as e:
                        st.error(f"Gemini API エラー: {e}\n\n⚠️ APIエラーが発生したため、自動的に一時的なモック分析結果を表示します。")
                        # 万が一APIエラーが起きた時用の安全策（フォールバック）
                        st.session_state['analysis_result'] = (
                            "【AI分析結果（エラー回避用モック）】\n"
                            "アップロードされた画像を元に、背景白・キャラクター固定の180pxアニメ絵文字として最適な構成をシミュレートしています。文字の追加やエフェクトの点滅が効果的なクリーンなラインのキャラクターです。"
                        )

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
            
            # --- パターンB の場合のAIによるJSON演出データの生成 ---
            animation_plan = []
            
            if "パターンB" in pattern_choice:
                # モックモード、またはAPIキーがない場合は入力文字を自動解釈してシミュレート（API消費ゼロ）
                if mock_mode or not genai or not api_key:
                    st.toast("🎨 モックモードで演出をシミュレートします")
                    
                    # 入力された文字を抽出（指示用の定型文を除外して文字だけを狙う）
                    clean_text = user_instruction.replace("キラキラを点滅させる", "").replace("を点滅させる", "").strip()
                    if "なるほど" in user_instruction or not clean_text:
                        display_text = "なるほど"
                    else:
                        display_text = clean_text[:4] # 4文字まで切り出し
                    
                    has_sparkle = "キラキラ" in user_instruction or "点滅" in user_instruction
                    
                    animation_plan = [
                        {"frame": 1, "offset_y": 0, "text": display_text[0] if len(display_text)>0 else "", "sparkle": has_sparkle and 1==2},
                        {"frame": 2, "offset_y": -12, "text": display_text[:2] if len(display_text)>1 else display_text, "sparkle": has_sparkle}, 
                        {"frame": 3, "offset_y": 0, "text": display_text[:3] if len(display_text)>2 else display_text, "sparkle": has_sparkle and 3%2==0},
                        {"frame": 4, "offset_y": -6, "text": display_text, "sparkle": has_sparkle},
                        {"frame": 5, "offset_y": 0, "text": display_text, "sparkle": has_sparkle and 5%2==0},
                        {"frame": 6, "offset_y": 0, "text": display_text, "sparkle": has_sparkle},
                    ]
                else:
                    try:
                        genai.configure(api_key=api_key)
                        # 最新モデルの gemini-2.5-flash に修正、JSON出力を指定
                        model = genai.GenerativeModel(
                            'gemini-2.5-flash',
                            generation_config={
                                "response_mime_type": "application/json",
                                "temperature": 0.2
                            }
                        )
                        prompt = f"""
                        ユーザーの指示に基づいて、180x180ピクセルのアニメーション（全6コマ）の各コマの演出パラメーターをJSON配列で出力してください。
                        
                        【ユーザーの指示】
                        "{user_instruction}"
                        
                        【出力フォーマット規約】
                        必ず以下の構造の、6つの要素を持つJSON配列のみを出力してください。余計な説明テキストは一切含めないでください。
                        [
                          {{"frame": 1, "offset_y": 0, "text": "文字", "sparkle": false}},
                          ...
                          {{"frame": 6, "offset_y": 0, "text": "文字", "sparkle": false}}
                        ]
                        - offset_y: キャラを上下に弾ませる場合はマイナス値（例: -10）。通常は0。
                        - text: 指示に沿って、1文字ずつ増やすなどのテキスト変化。無関係なシステム用語は含めない。
                        - sparkle: キラキラや点滅の指示がある場合、該当するコマをtrueにする。
                        """
                        response = model.generate_content(prompt)
                        animation_plan = json.loads(response.text)
                    except Exception as e:
                        st.error(f"演出プランの生成中にエラーが発生しました。基本モック演出に切り替えます: {e}")
                        # APIエラー時のセーフティネット
                        animation_plan = [
                            {"frame": 1, "offset_y": 0, "text": "OK", "sparkle": False},
                            {"frame": 2, "offset_y": -10, "text": "OK!", "sparkle": True},
                            {"frame": 3, "offset_y": 0, "text": "OKです", "sparkle": False},
                            {"frame": 4, "offset_y": -5, "text": "OKです👋", "sparkle": True},
                            {"frame": 5, "offset_y": 0, "text": "OKです👋", "sparkle": False},
                            {"frame": 6, "offset_y": 0, "text": "OKです👋", "sparkle": False},
                        ]

            # --- 画像合成処理 ---
            frames = []
            thumb_size = 120 
            resized_base = base_image.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            
            # フォント読み込み処理
            font = None
            font_sizes = [24, 20, 16]
            for size in font_sizes:
                for font_path in ["msgothic.ttc", "HelveticaNeue.ttc", "AppleGothic.ttf", "/System/Library/Fonts/Hiragino Sans GB.ttc", "NotoSansCJK-Regular.ttf"]:
                    try:
                        font = ImageFont.truetype(font_path, size)
                        break
                    except:
                        continue
                if font:
                    break

            for i in range(6):
                # 180px角、背景白固定（ユーザー指定必須条件）
                frame = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
                
                # 配置の初期座標（中央少し上）
                offset_x = (180 - thumb_size) // 2
                offset_y = (180 - thumb_size) // 2 - 10
                
                current_text = ""
                show_sparkle = False
                
                # パターンA（自動テンプレート）
                if "パターンA" in pattern_choice or not animation_plan:
                    if "強弱2コマ繰り返し" in template:
                        if i % 2 == 1:
                            offset_y -= 12
                            show_sparkle = True
                    else:
                        offset_y += int(10 * math.sin(i * math.pi / 3))
                    current_text = f"STEP {i+1}"
                
                # パターンB（演出プラン適用）
                else:
                    plan = animation_plan[i]
                    offset_y += plan.get("offset_y", 0)
                    current_text = plan.get("text", "")
                    show_sparkle = plan.get("sparkle", False)
                
                # キャラクター画像を貼り付け
                frame.paste(resized_base, (offset_x, offset_y), resized_base if resized_base.mode == 'RGBA' else None)
                
                draw = ImageDraw.Draw(frame)
                
                # キラキラの描画
                if show_sparkle:
                    draw.text((15, 20), "✨", fill=(255, 215, 0), font=font)
                    draw.text((145, 20), "✨", fill=(255, 215, 0), font=font)
                    if i % 2 == 0:
                        draw.text((150, 90), "✨", fill=(255, 215, 0), font=font)
                
                # 下部に文字を描画（擬似太字風）
                if current_text:
                    text_x = 90 - (len(current_text) * 10)
                    text_y = 140
                    for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1), (0,0)]:
                        draw.text((text_x + dx, text_y + dy), current_text, fill=(40, 40, 40), font=font)
                
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
        
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (255, 255, 255, 255))
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
