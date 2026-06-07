import streamlit as st
from PIL import Image
import io
import requests
from openai import OpenAI

# --- ページ設定 ---
st.set_page_config(page_title="アニメスタンプ自動化Webアプリ", layout="wide")

# --- サイドバー：要件定義シート＆設定 ---
with st.sidebar:
    st.header("⚙️ 開発・設定シート")
    # テスト用にAPIキーを入力できるようにします
    api_key = st.text_input("APIキー設定 (OpenAI)", type="password")
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
    """OpenAI API（DALL-E 3）を使ってスタンプ用の画像を生成する関数"""
    if not api_key:
        st.error("🔑 サイドバーにOpenAIのAPIキーを入力してください。")
        return None
        
    try:
        # クライアントの初期化
        client = OpenAI(api_key=api_key)
        
        # クオリティを担保するための絶対ルールをプロンプトに自動結合
        system_rules = (
            "An isolated digital illustration for a LINE sticker/emoji, "
            "perfectly solid white background, flat colors, clean and simple outlines, "
            "no shadows, no gradients, no fur or hair textures on animals. "
            "If it's a cat character, it must NOT have eyebrows or a nose. "
            "If it's a plant/round character, its face/shape must be a perfect circle, not an oval. "
            "The design and character character must be perfectly consistent."
        )
        
        full_prompt = f"{system_rules} Character expressing: {prompt_text}"
        
        with st.spinner("🎨 AIがイラストを生成中... (約10〜20秒かかります)"):
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                n=1,
                size="1024x1024", # DALL-E 3の標準サイズ（後ほど180pxにリサイズ）
                quality="standard"
            )
            
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            image = Image.open(io.BytesIO(img_data))
            
            # LINEの要件に合わせて180x180ピクセルにリサイズ
            image_resized = image.resize((180, 180), Image.Resampling.LANCZOS)
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
# パターンB: 個別指示（こだわり）
# ----------------------------------------
with tab_b:
    st.header("STEP 1: 自動分析 ＆ 詳細指示入力")
    input_text_b = st.text_input("作成したいスタンプのテーマを入力してください", key="input_b")
    
    st.write("💡 動きの個別指示 (1コマずつ設定)")
    
    cols_b = st.columns(6)
    frame_prompts = []
    for i in range(6):
        with cols_b[i]:
            prompt = st.text_area(f"コマ {i+1}", placeholder="例: 「な」がポップアップ\n無表情から笑顔へ", height=100)
            frame_prompts.append(prompt)

    st.markdown("---")
    st.header("STEP 2: 指示に基づいた生成＆書き出し")
    
    if st.button("シート生成実行", key="generate_b"):
        st.success("個別指示に基づいて6コマの画像を生成中です...")
        cols_gen = st.columns(6)
        for i, col in enumerate(cols_gen):
            with col:
                st.markdown(f"<div style='border: 2px solid #4CAF50; padding: 20px; text-align: center; border-radius: 10px; background-color: #f1f8e9;'>生成画像 {i+1}</div>", unsafe_allow_html=True)
                
    if st.button("書き出し (APNG)", key="export_b"):
         st.info("APNGファイルとして書き出します...")

# --- フッター ---
st.markdown("---")
st.caption("Developed with Streamlit & GitHub | Designed for Line Emoji Creators")
