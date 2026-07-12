"""
kireinote YouTube 動画生成スクリプト
-------------------------------------
対象記事: beauty-appliance-replacement.md
動画: 美容家電の買い替え時・5つのサイン (15秒 / 1920x1080)

使い方:
    python generate_video.py

出力:
    C:\\Users\\miker\\Downloads\\kireinote-beauty-appliance-15sec.mp4

必要なもの:
    - Python 3.x
    - Pillow (pip install pillow)
    - ffmpeg (winget でインストール済み)
"""

import os
import subprocess
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 1920, 1080
FPS = 30
SLIDE_DURATION = 2.5   # 秒
FADE_DURATION = 0.4    # クロスフェード秒数 (ffmpegで処理)

BG_COLOR = "#FFF5F7"            # 薄いピンク背景
TITLE_COLOR = "#c97a8c"         # kireinote ブランドカラー（メインピンク）
SIGN_COLOR = "#8b3a4d"          # 濃いピンク（サイン本文）
SUB_COLOR = "#c97a8c"           # サブテキスト
ACCENT_LINE = "#f0b8c8"         # 装飾ライン

OUTPUT_PATH = r"C:\Users\miker\Downloads\kireinote-beauty-appliance-15sec.mp4"

# フォント候補（上から順に試す）
FONT_CANDIDATES_BOLD = [
    r"C:\Windows\Fonts\meiryob.ttc",    # Meiryo Bold
    r"C:\Windows\Fonts\YuGothB.ttc",   # Yu Gothic Bold
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
    },
    {
        "type": "sign",
        "number": "1",
        "text": "風量・温度・パワーが",
        "text2": "買った頃より明らかに落ちている",
    },
    {
        "type": "sign",
        "number": "2",
        "text": "使い終わるまでの時間が",
        "text2": "長くなっている",
    },
    {
        "type": "sign",
        "number": "3",
        "text": "異音・焦げ臭さ・煙",
        "text2": "",
    },
    {
        "type": "sign",
        "number": "4",
        "text": "コード・接続部の劣化",
        "text2": "",
    },
    {
        "type": "sign",
        "number": "5",
        "text": "メーカー推奨の",
        "text2": "使用年数を超えている",
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
    # フォールバック: デフォルトフォント（日本語は化けるが落ちない）
    print(f"  警告: 日本語フォントが見つかりませんでした (size={size})")
    return ImageFont.load_default()


def draw_text_centered(draw, text, y, font, fill, img_width):
    """テキストを水平中央に描画する"""
    if not text:
        return
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (img_width - w) // 2
    draw.text((x, y), text, font=font, fill=fill)


# ---------------------------------------------------------------------------
# スライド描画
# ---------------------------------------------------------------------------

def make_title_slide():
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # 上部装飾ライン
    draw.rectangle([0, 0, WIDTH, 12], fill=hex_to_rgb(ACCENT_LINE))
    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=hex_to_rgb(ACCENT_LINE))

    # サブテキスト（小さい）
    font_sub = load_font(FONT_CANDIDATES_REGULAR, 36)
    draw_text_centered(draw, "kireinote", 120, font_sub, hex_to_rgb(SUB_COLOR), WIDTH)

    # メインタイトル line1
    font_big = load_font(FONT_CANDIDATES_BOLD, 90)
    draw_text_centered(draw, "美容家電の買い替え時", 330, font_big, hex_to_rgb(TITLE_COLOR), WIDTH)

    # 中央装飾ライン
    cx = WIDTH // 2
    draw.rectangle([cx - 120, 460, cx + 120, 466], fill=hex_to_rgb(ACCENT_LINE))

    # メインタイトル line2
    font_big2 = load_font(FONT_CANDIDATES_BOLD, 100)
    draw_text_centered(draw, "5つのサイン", 500, font_big2, hex_to_rgb(SIGN_COLOR), WIDTH)

    return img


def make_sign_slide(number, text, text2=""):
    img = Image.new("RGB", (WIDTH, HEIGHT), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # 上部装飾ライン
    draw.rectangle([0, 0, WIDTH, 12], fill=hex_to_rgb(ACCENT_LINE))
    draw.rectangle([0, HEIGHT - 12, WIDTH, HEIGHT], fill=hex_to_rgb(ACCENT_LINE))

    # 番号サークル（左寄り上部）
    font_num = load_font(FONT_CANDIDATES_BOLD, 72)
    circle_x, circle_y, circle_r = 200, 200, 80
    draw.ellipse(
        [circle_x - circle_r, circle_y - circle_r,
         circle_x + circle_r, circle_y + circle_r],
        fill=hex_to_rgb(TITLE_COLOR)
    )
    num_bbox = draw.textbbox((0, 0), number, font=font_num)
    nw = num_bbox[2] - num_bbox[0]
    nh = num_bbox[3] - num_bbox[1]
    draw.text(
        (circle_x - nw // 2, circle_y - nh // 2 - 4),
        number, font=font_num, fill=(255, 255, 255)
    )

    # "サイン" ラベル
    font_label = load_font(FONT_CANDIDATES_REGULAR, 32)
    draw_text_centered(draw, "サイン", 330, font_label, hex_to_rgb(SUB_COLOR), WIDTH)

    # 本文 (line1)
    font_body = load_font(FONT_CANDIDATES_BOLD, 64)
    if text2:
        draw_text_centered(draw, text, 410, font_body, hex_to_rgb(SIGN_COLOR), WIDTH)
        draw_text_centered(draw, text2, 500, font_body, hex_to_rgb(SIGN_COLOR), WIDTH)
    else:
        draw_text_centered(draw, text, 455, font_body, hex_to_rgb(SIGN_COLOR), WIDTH)

    # 装飾ドット
    for i in range(6):
        dx = WIDTH // 2 - 87 + i * 35
        draw.ellipse([dx, 650, dx + 14, 664], fill=hex_to_rgb(ACCENT_LINE))

    return img


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("kireinote 動画生成スクリプト")
    print("=" * 60)

    # 一時ディレクトリに PNG を出力
    tmp_dir = tempfile.mkdtemp(prefix="kireinote_slides_")
    print(f"\n[1/4] PNGスライドを生成中... ({tmp_dir})")

    png_paths = []
    for i, slide in enumerate(SLIDES):
        if slide["type"] == "title":
            img = make_title_slide()
        else:
            img = make_sign_slide(
                slide["number"],
                slide["text"],
                slide.get("text2", ""),
            )
        path = os.path.join(tmp_dir, f"slide_{i:02d}.png")
        img.save(path, "PNG")
        png_paths.append(path)
        print(f"  slide_{i:02d}.png -> OK")

    # ffmpegで各スライドを静止動画（mp4）に変換してからクロスフェードで結合
    print("\n[2/4] 各スライドをMP4クリップに変換中...")

    clip_paths = []
    # ffmpegのパスを確認（winget でインストールするとシステムPATHに追加されるが
    # 現シェルではまだ有効でない場合がある）
    ffmpeg_candidates = [
        "ffmpeg",
        r"C:\Users\miker\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]
    ffmpeg_cmd = None
    for c in ffmpeg_candidates:
        try:
            result = subprocess.run(
                [c, "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                ffmpeg_cmd = c
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if ffmpeg_cmd is None:
        # winget でインストールされた場所を検索
        import glob
        patterns = [
            r"C:\Users\miker\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg*\bin\ffmpeg.exe",
        ]
        for pat in patterns:
            found = glob.glob(pat, recursive=True)
            if found:
                ffmpeg_cmd = found[0]
                break

    if ffmpeg_cmd is None:
        print("\nエラー: ffmpegが見つかりません。")
        print("PowerShellを新しく開いて再実行してください。")
        print("(winget インストール直後はシェル再起動が必要)")
        return

    print(f"  ffmpeg: {ffmpeg_cmd}")

    frames_per_slide = int(FPS * SLIDE_DURATION)

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
    # xfadeフィルターグラフを構築
    # 各クリップの実効長 = SLIDE_DURATION - FADE_DURATION (最後以外)
    effective = SLIDE_DURATION - FADE_DURATION

    # 入力リスト
    inputs = []
    for cp in clip_paths:
        inputs += ["-i", cp]

    # フィルターグラフ
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
        # フォールバック: concat (トランジションなし)
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
        print(f"\n完成！")
        print(f"  ファイル: {OUTPUT_PATH}")
        print(f"  サイズ:   {size_mb:.1f} MB")

        # ffprobeで再生時間確認
        ffprobe_cmd = ffmpeg_cmd.replace("ffmpeg", "ffprobe")
        probe = subprocess.run(
            [ffprobe_cmd, "-v", "quiet",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1",
             OUTPUT_PATH],
            capture_output=True, text=True
        )
        if probe.returncode == 0:
            duration = float(probe.stdout.strip())
            print(f"  再生時間: {duration:.1f}秒")
    else:
        print("  エラー: 出力ファイルが見つかりません")

    # 一時ファイルを削除
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n一時ファイルを削除しました")
    print("=" * 60)
    print("次のステップ: Downloadsフォルダの MP4 を YouTube にアップロード")
    print("=" * 60)


if __name__ == "__main__":
    main()
