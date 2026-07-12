"""
kireinote YouTube 動画生成スクリプト v2
-----------------------------------------
対象記事: beauty-appliance-replacement.md
動画: 美容家電の買い替え時・5つのサイン (約15秒 / 1920x1080)
レイアウト: Option A (左右分割) + タイトルスライドのみ全画面画像

使い方:
    python generate_video_v2.py

出力:
    C:\\Users\\miker\\Downloads\\kireinote-beauty-appliance-15sec.mp4

必要なもの:
    - Python 3.x
    - Pillow (pip install pillow)
    - ffmpeg (winget でインストール済み)

Pexels 画像クレジット (CC0 / 商用利用可・帰属表示不要):
    hair_iron.jpg        - https://www.pexels.com/photo/3738341/
    warning_sparks.jpg   - https://www.pexels.com/photo/9665375/ (cottonbro studio)  ※v3差し替え
    calendar.jpg          - https://www.pexels.com/photo/273153/ (unknown)  ※v4差し替え（砂時計→カレンダー）
    hero.jpg, signs.jpg, disposal.jpg - 既存素材 (Pexels CC0)
"""

import os
import subprocess
import shutil
import tempfile
import glob
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1920, 1080
FPS = 30
SLIDE_DURATION = 2.5   # 秒
FADE_DURATION = 0.4    # クロスフェード秒数

BG_COLOR = "#FFF5F7"            # 薄いピンク背景（テキスト側）
TITLE_COLOR = "#c97a8c"         # kireinote ブランドカラー（メインピンク）
SIGN_COLOR = "#8b3a4d"          # 濃いピンク（番号・見出し）
SUB_COLOR = "#c97a8c"           # サブテキスト
ACCENT_LINE = "#f0b8c8"         # 装飾ライン
WHITE = (255, 255, 255)

OUTPUT_PATH = r"C:\Users\miker\Downloads\kireinote-beauty-appliance-15sec.mp4"

# 画像ディレクトリ
IMAGE_DIR = r"C:\Users\miker\kireinote\public\images\posts\beauty-appliance-replacement"

# フォント候補（上から順に試す）
FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\meiryob.ttc",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\BIZ-UDGothicB.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]
FONT_CANDIDATES_REGULAR = [
    r"C:\Windows\Fonts\meiryo.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\BIZ-UDGothicR.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
]

# ---------------------------------------------------------------------------
# スライド定義
# ---------------------------------------------------------------------------

SLIDES = [
    {
        "type": "title",
        "line1": "美容家電の買い替え時",
        "line2": "5つのサイン",
        "image": "hero.jpg",        # 全画面背景（タイトルのみ特別扱い）
    },
    {
        "type": "sign",
        "number": "1",
        "text": "風量・温度・パワーが",
        "text2": "買った頃より明らかに落ちている",
        "image": "signs.jpg",       # シルバードライヤー（ピンク背景）
    },
    {
        "type": "sign",
        "number": "2",
        "text": "使い終わるまでの時間が",
        "text2": "長くなっている",
        "image": "hair_iron.jpg",   # ヘアアイロン使用シーン
    },
    {
        "type": "sign",
        "number": "3",
        "text": "異音・焦げ臭さ・煙",
        "text2": "",
        "image": "warning_sparks.jpg",  # 火花・危険信号
    },
    {
        "type": "sign",
        "number": "4",
        "text": "コード・接続部の劣化",
        "text2": "",
        "image": "hero.jpg",        # コードが絡まった美容ツール集
    },
    {
        "type": "sign",
        "number": "5",
        "text": "メーカー推奨の",
        "text2": "使用年数を超えている",
        "image": "calendar.jpg",  # カレンダー（時間経過・年数）v4差し替え
    },
]


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    print(f"  警告: 日本語フォントが見つかりませんでした (size={size})")
    return ImageFont.load_default()


def draw_text_centered_in_area(draw, text, y, font, fill, x_left, x_right):
    """指定範囲内でテキストを水平中央に描画"""
    if not text:
        return
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    area_w = x_right - x_left
    x = x_left + (area_w - w) // 2
    draw.text((x, y), text, font=font, fill=fill)


def load_and_crop_image(img_path, target_w, target_h):
    """
    画像を読み込んでターゲットサイズにクロップ（中央）
    アスペクト比を維持しながらリサイズ後に中央クロップ
    """
    src = Image.open(img_path).convert("RGB")
    src_w, src_h = src.size

    # スケールを計算（ターゲットを完全に覆う最小サイズ）
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    src = src.resize((new_w, new_h), Image.LANCZOS)

    # 中央クロップ
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    src = src.crop((left, top, left + target_w, top + target_h))
    return src


def add_rounded_corners(img, radius=12):
    """画像に角丸マスクを適用（RGBAで返す）"""
    img = img.convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


# ---------------------------------------------------------------------------
# タイトルスライド（全画面画像 + 半透明ピンクオーバーレイ）
# ---------------------------------------------------------------------------

def make_title_slide(img_path):
    """
    タイトルは画像を全画面背景にして中央下部にテキストを重ねる。
    下部にグラデーション風の半透明ピンクバーを敷く。
    """
    base = load_and_crop_image(img_path, WIDTH, HEIGHT)

    # 半透明の暗いオーバーレイ（全体を少し暗くして文字を読みやすく）
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 80))
    base = base.convert("RGBA")
    base = Image.alpha_composite(base, overlay)

    # 下部バー（半透明ピンク）
    bar_h = 320
    bar = Image.new("RGBA", (WIDTH, bar_h), (251, 229, 234, 210))
    base.paste(bar, (0, HEIGHT - bar_h), bar)

    draw = ImageDraw.Draw(base)

    # kireinote ロゴテキスト（上部）
    font_logo = load_font(FONT_CANDIDATES_REGULAR, 38)
    logo_text = "kireinote"
    bbox = draw.textbbox((0, 0), logo_text, font=font_logo)
    lw = bbox[2] - bbox[0]
    draw.text(((WIDTH - lw) // 2, 60), logo_text, font=font_logo, fill=(255, 255, 255, 220))

    # メインタイトル line1（下部バー内）
    font_title1 = load_font(FONT_CANDIDATES_BOLD, 88)
    draw_text_centered_in_area(
        draw, "美容家電の買い替え時",
        HEIGHT - bar_h + 28,
        font_title1,
        hex_to_rgb(TITLE_COLOR) + (255,),
        0, WIDTH
    )

    # 区切りライン
    cx = WIDTH // 2
    draw.rectangle([cx - 140, HEIGHT - bar_h + 128, cx + 140, HEIGHT - bar_h + 134],
                   fill=hex_to_rgb(ACCENT_LINE) + (255,))

    # メインタイトル line2
    font_title2 = load_font(FONT_CANDIDATES_BOLD, 104)
    draw_text_centered_in_area(
        draw, "5つのサイン",
        HEIGHT - bar_h + 148,
        font_title2,
        hex_to_rgb(SIGN_COLOR) + (255,),
        0, WIDTH
    )

    return base.convert("RGB")


# ---------------------------------------------------------------------------
# サインスライド（Option A: 左右分割）
# ---------------------------------------------------------------------------

def make_sign_slide_split(number, text, text2, img_path):
    """
    左半分: 画像（角丸あり）
    右半分: 薄ピンク背景 + テキスト
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # --- 左パネル: 画像 ---
    IMG_MARGIN = 40          # 画像の外マージン
    IMG_W = WIDTH // 2 - IMG_MARGIN * 2 + 20   # 少し広め
    IMG_H = HEIGHT - IMG_MARGIN * 2

    photo = load_and_crop_image(img_path, IMG_W, IMG_H)
    photo_rounded = add_rounded_corners(photo, radius=16)

    # RGBA画像をRGBキャンバスに貼り付け（アルファチャンネルを使う）
    img.paste(photo_rounded, (IMG_MARGIN, IMG_MARGIN), photo_rounded.split()[3])

    # --- 右パネル: テキストエリア ---
    TEXT_X_LEFT = WIDTH // 2 + 20
    TEXT_X_RIGHT = WIDTH - 60

    # 上部装飾ライン（右パネル上端）
    draw.rectangle([TEXT_X_LEFT, 0, WIDTH, 10], fill=hex_to_rgb(ACCENT_LINE))
    draw.rectangle([TEXT_X_LEFT, HEIGHT - 10, WIDTH, HEIGHT], fill=hex_to_rgb(ACCENT_LINE))

    # 「サイン」ラベル
    font_label = load_font(FONT_CANDIDATES_REGULAR, 34)
    draw_text_centered_in_area(draw, "サイン", 180, font_label, hex_to_rgb(SUB_COLOR), TEXT_X_LEFT, TEXT_X_RIGHT)

    # 番号バッジ（大きめサークル）
    badge_cx = (TEXT_X_LEFT + TEXT_X_RIGHT) // 2
    badge_cy = 320
    badge_r = 76
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r,
         badge_cx + badge_r, badge_cy + badge_r],
        fill=hex_to_rgb(TITLE_COLOR)
    )
    font_num = load_font(FONT_CANDIDATES_BOLD, 80)
    nb = draw.textbbox((0, 0), number, font=font_num)
    nw = nb[2] - nb[0]
    nh = nb[3] - nb[1]
    draw.text(
        (badge_cx - nw // 2, badge_cy - nh // 2 - 4),
        number, font=font_num, fill=WHITE
    )

    # 区切りライン
    draw.rectangle(
        [badge_cx - 100, badge_cy + badge_r + 20,
         badge_cx + 100, badge_cy + badge_r + 26],
        fill=hex_to_rgb(ACCENT_LINE)
    )

    # 本文テキスト
    font_body = load_font(FONT_CANDIDATES_BOLD, 58)
    body_y_start = badge_cy + badge_r + 52

    if text2:
        # 2行ある場合は少し上に寄せる
        draw_text_centered_in_area(draw, text, body_y_start, font_body, hex_to_rgb(SIGN_COLOR), TEXT_X_LEFT, TEXT_X_RIGHT)
        draw_text_centered_in_area(draw, text2, body_y_start + 80, font_body, hex_to_rgb(SIGN_COLOR), TEXT_X_LEFT, TEXT_X_RIGHT)
    else:
        # 1行の場合は縦中央寄り
        draw_text_centered_in_area(draw, text, body_y_start + 20, font_body, hex_to_rgb(SIGN_COLOR), TEXT_X_LEFT, TEXT_X_RIGHT)

    # 下部装飾ドット
    dot_y = HEIGHT - 80
    dot_base_x = (TEXT_X_LEFT + TEXT_X_RIGHT) // 2 - 87
    for i in range(6):
        dx = dot_base_x + i * 35
        draw.ellipse([dx, dot_y, dx + 14, dot_y + 14], fill=hex_to_rgb(ACCENT_LINE))

    return img


# ---------------------------------------------------------------------------
# ffmpeg 検索
# ---------------------------------------------------------------------------

def find_ffmpeg():
    candidates = [
        "ffmpeg",
        r"C:\Users\miker\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    for c in candidates:
        try:
            result = subprocess.run([c, "-version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # winget インストール先を glob で探す
    patterns = [
        r"C:\Users\miker\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg*\bin\ffmpeg.exe",
    ]
    for pat in patterns:
        found = glob.glob(pat, recursive=True)
        if found:
            return found[0]

    return None


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("kireinote 動画生成スクリプト v2 (Pexels画像入り)")
    print("=" * 60)

    # 一時ディレクトリに PNG を出力
    tmp_dir = tempfile.mkdtemp(prefix="kireinote_slides_v2_")
    print(f"\n[1/4] PNGスライドを生成中...")
    print(f"      一時フォルダ: {tmp_dir}")

    png_paths = []
    for i, slide in enumerate(SLIDES):
        img_path = os.path.join(IMAGE_DIR, slide["image"])
        if not os.path.exists(img_path):
            print(f"  エラー: 画像が見つかりません -> {img_path}")
            return

        if slide["type"] == "title":
            img = make_title_slide(img_path)
        else:
            img = make_sign_slide_split(
                slide["number"],
                slide["text"],
                slide.get("text2", ""),
                img_path,
            )

        path = os.path.join(tmp_dir, f"slide_{i:02d}.png")
        img.save(path, "PNG")
        png_paths.append(path)
        label = slide.get("line1", slide.get("text", ""))[:20]
        print(f"  slide_{i:02d}.png [{label}...] -> OK")

    # ffmpeg 検索
    print("\n[2/4] 各スライドをMP4クリップに変換中...")
    ffmpeg_cmd = find_ffmpeg()
    if ffmpeg_cmd is None:
        print("\nエラー: ffmpegが見つかりません。")
        print("PowerShellを新しく開いて再実行してください。")
        return
    print(f"  ffmpeg: {ffmpeg_cmd}")

    frames_per_slide = int(FPS * SLIDE_DURATION)
    clip_paths = []

    for i, png_path in enumerate(png_paths):
        clip_path = os.path.join(tmp_dir, f"clip_{i:02d}.mp4")
        cmd = [
            ffmpeg_cmd, "-y",
            "-loop", "1",
            "-i", png_path,
            "-t", str(SLIDE_DURATION),
            "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            clip_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  エラー (clip_{i:02d}): {result.stderr[-500:]}")
            return
        clip_paths.append(clip_path)
        print(f"  clip_{i:02d}.mp4 -> OK")

    # xfade フィルターでクロスフェード結合
    print("\n[3/4] クロスフェードで結合中...")

    n = len(clip_paths)
    effective = SLIDE_DURATION - FADE_DURATION

    inputs = []
    for cp in clip_paths:
        inputs += ["-i", cp]

    filter_parts = []
    last_label = "[0:v]"
    for i in range(1, n):
        offset = round(effective * i, 3)
        out_label = f"[v{i}]" if i < n - 1 else "[vout]"
        filter_parts.append(
            f"{last_label}[{i}:v]xfade=transition=fade:"
            f"duration={FADE_DURATION}:offset={offset}{out_label}"
        )
        last_label = out_label

    filter_graph = "; ".join(filter_parts)

    cmd = (
        [ffmpeg_cmd, "-y"]
        + inputs
        + [
            "-filter_complex", filter_graph,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            OUTPUT_PATH,
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  フィルター結合失敗: {result.stderr[-800:]}")
        print("  フォールバック: シンプル連結に切り替えます...")
        concat_list_path = os.path.join(tmp_dir, "concat.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")
        cmd2 = [
            ffmpeg_cmd, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            OUTPUT_PATH,
        ]
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        if result2.returncode != 0:
            print(f"  エラー: {result2.stderr[-500:]}")
            return
        print("  連結完了 (トランジションなし)")
    else:
        print("  クロスフェード結合完了")

    # 確認
    print("\n[4/4] ファイル確認中...")
    if os.path.exists(OUTPUT_PATH):
        size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024

        ffprobe_cmd = ffmpeg_cmd.replace("ffmpeg", "ffprobe")
        probe = subprocess.run(
            [ffprobe_cmd, "-v", "quiet",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             OUTPUT_PATH],
            capture_output=True, text=True
        )
        duration_str = ""
        if probe.returncode == 0 and probe.stdout.strip():
            duration = float(probe.stdout.strip())
            duration_str = f"  再生時間: {duration:.1f}秒"

        print(f"\n完成！")
        print(f"  ファイル: {OUTPUT_PATH}")
        print(f"  サイズ:   {size_mb:.1f} MB")
        if duration_str:
            print(duration_str)
    else:
        print("  エラー: 出力ファイルが見つかりません")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n一時ファイルを削除しました")
    print("=" * 60)
    print("次のステップ: Downloadsフォルダの MP4 を YouTube にアップロード")
    print("=" * 60)


if __name__ == "__main__":
    main()
