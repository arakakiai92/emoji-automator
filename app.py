# --- 生成ループ部分の修正コード ---
# 以下の for ループブロックを入れ替えてください

        frames = []
        for i in range(6):
            # 白背景作成
            frame = Image.new("RGBA", (180, 180), (255, 255, 255, 255))
            
            # 【重要】アニメーション効果：呼吸するように拡大縮小 (±10%)
            scale = 1.0 + (math.sin(i * math.pi / 3) * 0.1)
            new_size = (int(180 * scale), int(180 * scale))
            
            # 画像をリサイズ
            img_resized = base_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 中央配置のための座標計算
            paste_x = (180 - new_size[0]) // 2
            paste_y = (180 - new_size[1]) // 2
            
            # 配置
            frame.paste(img_resized, (paste_x, paste_y), img_resized)
            
            frames.append(frame)
