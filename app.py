import streamlit as st
from PIL import Image
import io
import requests
from google import genai
from google.genai import types

# --- ページ設定 ---
st.set_page_config(page_title="アニメスタンプ自動化Webアプリ", layout="wide")

# --- サイドバー：要件定義シート＆設定 ---
with st.sidebar:
    st.header("⚙️ 開発・設定シート")
    # Google APIキーを入力できるように変更しました
    api_key = st.text_input("APIキー設定 (Google Gemini API)", type="password")
    github_url = st.text_input("GitHubリポジトリURL", value="arakakiaiai92/emoji-automator")
    
    st.markdown("---")
    st.subheader("🎨 キャラ・出力定義 (完全版)")
    st.checkbox("背景は「白」で固定", value=True, disabled=True)
    st.checkbox("キャラクターデザインを固定", value=True, disabled=True)
    st.checkbox("シンプルな線 (毛並み等の自動追加NG)", value=True, disabled=True)
    
    st.markdown("---")
    st.subheader("🌐 マーケティング設定")
    market_lang = st.radio("ターゲット言語", ["日本語", "繁体字 (台湾市場向け)"])

    st.markdown("---")
    st.subheader("出力フォーマット")
    st.code("サイズ: 180×180 px\n構成: 6コマ 1シート\n形式: APNG")

# --- 画像生成用の共通関数 ---
def generate_stamp_image(prompt_text, api_key):
    """GoogleのImagenモデルを使ってスタンプ用の画像を生成する関数"""
    if not api_key:
        st.error("🔑 サイドバーにGoogleのAPIキーを入力してください。")
        return None
        
    try:
        # クライアントの初期化
        client = genai.Client(api_key=api_key)
        
        # クオリティを担保するための絶対ルールをプロンプトに自動結合
        # スタンプの品質を安定させるための厳格な制約です
        system_rules = (
            "An isolated digital illustration for a LINE sticker/emoji, "
            "perfectly solid white background, flat colors, clean and simple outlines, "
            "no shadows, no gradients, strictly no fur or hair textures. "
            "If it's a cat character, it must absolutely NOT have eyebrows or a nose. "
            "If it's a Platycerium ridleyi (plant) or a round character, its face/shape must be a perfect circle, never an oval. "
            "The design must be perfectly consistent."
        )
        
        full_prompt = f"{system_rules} Character expressing: {prompt_text}"
        
        with st.spinner("🎨 Google AIがイラストを生成中... (約10〜20秒かかります)"):
            result = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            
            # 生成された画像をPillowオブジェクトとして取得
            img = result.generated_images[0].image
            
            # LINEの要件に合わせて180x180ピクセルにリサイズ
            image_resized = img.resize((180, 180), Image.Resampling.LANCZOS)
            return image_resized
            
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
        return None

# --- メインコンテンツ ---
st.title("あなた専用 アニメスタンプ自動化アプリ")
st.write("自動抽出（おまかせ）と個別指示（こだわり）を使い分けて、ブラウザからアニメ絵文字を自動生成します。")

tab_a, tab_b = st.tabs(["✨ パターンA: 自動抽出 (おまかせ)", "🛠️ パターンB: 個別指示 (こだわり)"])

# ----------------------------------------
# パターンA: 自動抽出（おまかせ）
# ----------------------------------------
with tab_a:
    st.header("STEP 1: 自動分析・アイデア抽出")
    input_text_a = st.text_input("スタンプにしたい文字や感情を入力してください（例：了解、なるほど）", key="input_a")
    
    if st.button("AIにおまかせで進む", key="btn_a_step1"):
        if input_text_a:
            st.success(f"✅ AI分析結果: 文字「{input_text_a}」、強弱2コマ繰り返しのアニメーションを提案します。")
            
            # テストとして、1コマ目の画像を実際に生成してみる
            st.markdown("### 📸 テスト生成結果 (1コマ目)")
            generated_img = generate_stamp_image(input_text_a, api_key)
            
            if generated_img:
                st.image(generated_img, caption=f"生成されたスタンプ (180x180px)", width=180)
                st.success("🎉 画像の生成と180pxへのリサイズに成功しました！")
        else:
            st.warning("文字を入力してください。")

    st.markdown("---")
    st.header("STEP 2: コマ送りラフ生成＆コマ並べ")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    columns = [col1, col2, col3, col4, col5, col6]
    for i, col in enumerate(columns):
        with col:
            st.markdown(f"<div style='border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 10px;'>コマ {i+1}<br>180x180</div>", unsafe_allow_html=True)
    
    st.write("")
    if st.button("シート生成＆書き出し (APNG)", key="export_a"):
        st.info("APNGファイルへの変換ロジックを実行し、ダウンロードの準備をしています...")

# ----------------------------------------
# パターンB: 個別指示（こだわり）- 更新版
# ----------------------------------------
with tab_b:
    st.header("STEP 1: 基準となるキャラクター画像のアップロード")
    # 【追加項目】ファイルアップローダー
    uploaded_file = st.file_uploader("お手元のキャラクター画像（1コマ目、または三面図など）を選択してください", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # アップロードされた画像を表示
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた基準画像", width=180)
        st.success("基準画像の読み込みが完了しました。これをベースに指示を入力してください。")
        
    st.markdown("---")
    st.header("STEP 2: 自動分析 ＆ 詳細指示入力")
    input_text_b = st.text_input("作成したいスタンプのテーマを入力してください", key="input_b")
    
    st.write("💡 動きの個別指示 (1コマずつ設定)")
    
    cols_b = st.columns(6)
    frame_prompts = []
    for i in range(6):
        with cols_b[i]:
            # コマごとの指示を入力
            prompt = st.text_area(f"コマ {i+1}", placeholder="例: 「な」がポップアップ\n無表情から笑顔へ", height=100)
            frame_prompts.append(prompt)

    st.markdown("---")
    st.header("STEP 3: 指示に基づいた生成＆書き出し")
    
    if st.button("シート生成実行", key="generate_b"):
        # まだ画像連携ロジック（I2I）は未実装ですが、UIの確認として
        if uploaded_file is None:
            st.error("❌ STEP 1 で基準画像をアップロードしてください。")
        else:
            st.success("アップロードされた画像を分析し、個別指示に基づいて6コマの画像を生成します（実装中...）")
            # プレースホルダー表示
            cols_gen = st.columns(6)
            for i, col in enumerate(cols_gen):
                with col:
                    st.markdown(f"<div style='border: 2px solid #4CAF50; padding: 20px; text-align: center; border-radius: 10px; background-color: #f1f8e9;'>生成画像 {i+1}</div>", unsafe_allow_html=True)
                
    if st.button("書き出し (APNG)", key="export_b"):
         st.info("APNGファイルとして書き出します...")

# --- フッター ---
st.markdown("---")
st.caption("Developed with Streamlit & GitHub | Designed for Line Emoji Creators")
