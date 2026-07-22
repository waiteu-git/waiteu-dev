"""カード用スクリーンショットを生成する。

- LTW: 既存のストア素材 (1280x800) を 680x425 に縮小するだけ
- リタス: 端末画面2枚をヘッドレスChromeで撮り、ブランド色の台紙に載せて 16:10 にする

どちらも実データを含まない（学籍番号・氏名・実在の履修情報は写らない）。
出力は 680x425 = カード表示幅 338px の2倍。
"""
import os
import subprocess

from PIL import Image, ImageDraw

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCREENS = r"C:\dev\litus-design\previews\screens"
LTW_SRC = r"C:\dev\lms-task-watcher-develop\store-assets\store-shot1.png"
OUT = r"C:\dev\waiteu-dev\public\shots"
TMP = r"C:\dev\waiteu-dev\.tmp-shots"

OUT_SIZE = (680, 425)          # 16:10
CANVAS = (1360, 850)           # 出力の2倍で作ってから縮小する
LITUS_GREEN = (12, 130, 96)    # #0c8260 リタスLPの基調色
PHONE_H = 730                  # 台紙上の端末の高さ
GAP = 64
RADIUS = 28

os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)


def shoot(name, w, h):
    """プレビューHTMLをPNGに焼く。2倍解像度で撮る（戻り値は物理px = CSS px x2）。"""
    dst = os.path.join(TMP, name + ".png")
    src = os.path.join(SCREENS, name + ".html").replace("\\", "/")
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--window-size={w},{h}",
            f"--screenshot={dst}",
            f"file:///{src}",
        ],
        check=True,
        capture_output=True,
    )
    return Image.open(dst).convert("RGB")


def rounded(im, radius):
    """角を丸める（アルファ付きで返す）。"""
    im = im.convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1],
                                           radius=radius, fill=255)
    im.putalpha(mask)
    return im


def build_litus():
    """課題一覧（枠なし・実データ風）＋掲示詳細（端末幅）の2枚を並べる。

    home.html と timetable.html は不採用:
    - timetable.html はグリッドが描画されず実質空（ヘッダーとボタンのみ）
    - home.html は中央が大きく空いていて地味（掲示詳細の方が内容が詰まっている）

    どちらのHTMLも「ちょうど390px幅」で撮ると本文の右端が数文字分欠ける
    レイアウト不具合があるため（assignments.html は右上の同期ラベルが
    ダーク切替ボタンとぶつかる/隠れる、bulletin-detail.html は
    `.screen{max-width:390px}` の中身自体が右にはみ出して切れる）、
    余裕を持たせた幅で撮ってから対象領域だけ切り出す。
    assignments.html 下部のデバッグ用状態切替行（通常/全提出/未同期/エラー）は
    position:fixed でビューポート下端に張り付くため、十分な高さで撮って
    本文の末尾で切り捨てることで除外する。
    """
    # 課題一覧: 幅可変レイアウト。480px幅で撮ると右上の同期ラベルが欠けない。
    # 本文は y=1821(物理px)で終わり、その先は下部デバッグ行までただの余白。
    assignments = shoot("assignments", 480, 1200).crop((0, 0, 960, 1840))

    # 掲示詳細: 390pxちょうどで撮ると本文が右端で切れる（既知の描画不具合）。
    # 600px幅で撮り、画面本体(x=210..990)だけを切り出す。
    bulletin = shoot("bulletin-detail", 600, 1600).crop((210, 0, 990, 1955))

    phones = [assignments, bulletin]
    scaled = []
    for p in phones:
        w = round(p.size[0] * PHONE_H / p.size[1])
        scaled.append(rounded(p.resize((w, PHONE_H), Image.LANCZOS), RADIUS))

    total = sum(p.size[0] for p in scaled) + GAP * (len(scaled) - 1)
    canvas = Image.new("RGB", CANVAS, LITUS_GREEN)
    x = (CANVAS[0] - total) // 2
    y = (CANVAS[1] - PHONE_H) // 2
    for p in scaled:
        canvas.paste(p, (x, y), p)
        x += p.size[0] + GAP
    canvas.resize(OUT_SIZE, Image.LANCZOS).save(
        os.path.join(OUT, "litus.png"), optimize=True)


def build_ltw():
    im = Image.open(LTW_SRC).convert("RGB")
    im.resize(OUT_SIZE, Image.LANCZOS).save(
        os.path.join(OUT, "ltw.png"), optimize=True)


if __name__ == "__main__":
    build_ltw()
    build_litus()
    for f in ("ltw.png", "litus.png"):
        p = os.path.join(OUT, f)
        print(f, Image.open(p).size, os.path.getsize(p), "bytes")
