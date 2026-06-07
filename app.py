import streamlit as st
from PIL import Image
import io
import math
import imageio

# 基本設定
st.set_page_config(page_title="アニメスタンプ作成アプリ", layout="wide")
st.title("アニメスタンプ作成アプリ")

# 1. イラストアップロード
uploaded_file = st.sidebar.file_uploader("ベースイラストをアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 画像の読み込み (背景白固定)
    base_image = Image.open(uploaded_file).convert("RGBA")
    st.sidebar.image(base_image, caption="アップロード済み")

    if st.button("生成実行"):
        # 6コマのアニメーションを生成
        frames = []
        
        for i in range(6):
            # 180x180の白背景キャンバスを作成
            frame = Image.new("RGBA", (180, 180), (255, 255, 255, 255))

            # アニメーション効果：呼吸するように拡大縮小 (±10%)
            scale = 1.0 + (math.sin(i * math.pi / 3) * 0.1)
            new_size = (int(180 * scale), int(180 * scale))

            # 画像をリサイズ
            img_resized = base_image.resize(new_size, Image.Resampling.LANCZOS)

            # 中央配置
            paste_x = (180 - new_size[0]) // 2
            paste_y = (180 - new_size[1]) // 2
            frame.paste(img_resized, (paste_x, paste_y), img_resized)
            
            # Pillowの画像をRGBAバイトデータに変換して保存用リストへ
            frames.append(frame)

        # --- スプライトシート生成 ---
        sprite_sheet = Image.new("RGBA", (180 * 6, 180), (255, 255, 255, 255))
        for idx, f in enumerate(frames):
            sprite_sheet.paste(f, (180 * idx, 0))
        
        # --- APNGアニメーション生成 (imageioを使用) ---
        apng_buf = io.BytesIO()
        # imageioでAPNGとして保存
        imageio.mimsave(apng_buf, [f for f in frames], format='PNG', duration=0.2, loop=0)

        # プレビュー表示
        st.image(sprite_sheet, caption="生成されたスプライトシート")

        # ダウンロードボタン
        col1, col2 = st.columns(2)
        
        buf_sprite = io.BytesIO()
        sprite_sheet.save(buf_sprite, format="PNG")
        col1.download_button("スプライトシートを保存", data=buf_sprite.getvalue(), file_name="anime_sheet.png", mime="image/png")
        
        col2.download_button("APNGアニメスタンプを保存", data=apng_buf.getvalue(), file_name="anime_stamp.png", mime="image/png")

else:
    st.info("左メニューから画像をアップロードしてください。")
