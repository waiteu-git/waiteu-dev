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


def shoot(name, w, h, hide=None):
    """プレビューHTMLをPNGに焼く。2倍解像度で撮る（戻り値は物理px = CSS px x2）。

    hide: 撮影時のみ非表示にするCSSセレクタのリスト。プレビューページ専用の
    操作UI（ダークモード切替トグル等）は製品スクリーンショットに写ってはいけないが、
    元のHTML（litus-design側の共有プレビュー）は編集しない。TMP に
    `<style>{sel}{display:none!important}</style>` を注入したコピーを作り、
    それを撮る。トグルは position:fixed で通常フローから外れているため、
    非表示にしても他要素のレイアウトは変わらない。
    """
    src_path = os.path.join(SCREENS, name + ".html")
    if hide:
        html = open(src_path, encoding="utf-8").read()
        style = "<style>" + ",".join(hide) + "{display:none!important}</style>\n</head>"
        assert "</head>" in html
        html = html.replace("</head>", style, 1)
        src_path = os.path.join(TMP, name + ".shot.html")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(html)
    dst = os.path.join(TMP, name + ".png")
    src = src_path.replace("\\", "/")
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
    レイアウト不具合があるため（bulletin-detail.html は
    `.screen{max-width:390px}` の中身自体が右にはみ出して切れる）、
    余裕を持たせた幅で撮ってから対象領域だけ切り出す。
    assignments.html 下部のデバッグ用状態切替行（通常/全提出/未同期/エラー）は
    position:fixed でビューポート下端に張り付くため、十分な高さで撮って
    本文の末尾で切り捨てることで除外する。

    どちらの画面にもプレビューページ専用のダークモード切替トグル
    （`.theme-toggle`、position:fixed;top/right固定）が右上に乗っている。
    このトグルは製品UIではないため常に非表示にして撮る。
    トグルもラベルも「ビューポート右端からの固定オフセット」で位置決めされて
    いるため、撮影幅を変えても両者の重なりは解消しない（試して確認済み）。
    bulletin-detail.html はたまたま横クロップの範囲外に収まっていたが、
    assignments.html は本文が画面幅いっぱいまで使うレイアウトのため横
    クロップでは避けられない。よって shoot() 側で CSS 注入により非表示にする。
    """
    # 課題一覧: 幅可変レイアウト。480px幅で撮ると右上の同期ラベルが
    # flexの折返しで欠けることはない（ただし同期ラベルとトグルの重なりは
    # 幅に関係なく起きるため hide=[".theme-toggle"] で別途対処）。
    # 本文は y=1821(物理px)で終わり、その先は下部デバッグ行までただの余白。
    assignments = shoot("assignments", 480, 1200, hide=[".theme-toggle"]) \
        .crop((0, 0, 960, 1840))

    # 掲示詳細: 390pxちょうどで撮ると本文が右端で切れる（既知の描画不具合）。
    # 600px幅で撮り、画面本体(x=210..990)だけを切り出す。
    bulletin = shoot("bulletin-detail", 600, 1600, hide=[".theme-toggle"]) \
        .crop((210, 0, 990, 1955))

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
