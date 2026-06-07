import streamlit as st
from PIL import Image
import io
import math

st.set_page_config(page_title="アニメスタンプ作成アプリ", layout="wide")
st.title("アニメスタンプ作成アプリ")

uploaded_file = st.sidebar.file_uploader("ベースイラストをアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    base_image = Image.open(uploaded_file).convert("RGBA")
    st.sidebar.image(base_image, caption="アップロード済み")

    if st.button("生成実行"):
        frames = []
        for i in range(6):
            frame = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
            scale = 1.0 + (math.sin(i * math.pi / 3) * 0.1)
            new_size = (int(180 * scale), int(180 * scale))
            img_resized = base_image.resize(new_size, Image.Resampling.LANCZOS)
            paste_x = (180 - new_size[0]) // 2
            paste_y = (180 - new_size[1]) // 2
            frame.paste(img_resized, (paste_x, paste_y), img_resized)
            frames.append(frame)

        # 統合スプライトシート生成
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (255, 255, 255, 255))
        for idx, f in enumerate(frames):
            sprite_sheet.paste(f, (180 * idx, 0))
        
        st.image(sprite_sheet, caption="生成されたスプライトシート")

        # ダウンロードボタン
        buf = io.BytesIO()
        sprite_sheet.save(buf, format="PNG")
        st.download_button("スプライトシートを保存", data=buf.getvalue(), file_name="anime_sheet.png", mime="image/png")
        
        st.info("APNG形式での生成は、現在ライブラリの依存関係トラブルを防ぐため、スプライトシート形式のみに絞って安定稼働させています。")

else:
    st.info("左メニューから画像をアップロードしてください。")
