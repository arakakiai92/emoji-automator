import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json

# APIキーはハードコードせず、st.secretsから読み込む運用を徹底
# Streamlit Cloudの「Secrets」設定で GOOGLE_API_KEY を登録してください
try:
    import google.generativeai as genai
    API_KEY = st.secrets.get("GOOGLE_API_KEY")
    if API_KEY:
        genai.configure(api_key=API_KEY)
except ImportError:
    genai = None

st.set_page_config(page_title="アニメスタンプ作成アプリ", layout="wide")

st.title("アニメスタンプ作成アプリ")

# 1. イラストアップロード
uploaded_file = st.sidebar.file_uploader("ベースイラストをアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 完全に白背景（255, 255, 255, 255）でリサイズなし・位置固定で処理
    base_image = Image.open(uploaded_file).convert("RGBA")
    
    # 180x180の白背景キャンバスを作成
    canvas_size = (180, 180)
    
    # プレビュー表示
    st.sidebar.image(base_image, caption="アップロード済み")
    
    if st.button("生成実行"):
        frames = []
        for i in range(6):
            # 白背景作成
            frame = Image.new("RGBA", canvas_size, (255, 255, 255, 255))
            
            # 画像を中央に配置（サイズ変更なし）
            frame.paste(base_image, (0, 0), base_image)
            
            # 必要ならここにキラキラなどのエフェクトを追加
            frames.append(frame)
            
        # 統合スプライトシート作成 (1080x180)
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (255, 255, 255, 255))
        for idx, f in enumerate(frames):
            sprite_sheet.paste(f, (180 * idx, 0))
            
        st.image(sprite_sheet, caption="生成されたスプライトシート")
        
        # ダウンロード処理
        buf = io.BytesIO()
        sprite_sheet.save(buf, format="PNG")
        st.download_button("スプライトシートを保存", data=buf.getvalue(), file_name="output.png", mime="image/png")
else:
    st.info("左メニューから画像をアップロードしてください。")
