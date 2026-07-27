"""カード用スクリーンショットを生成する（tools/ は public 外＝非配信）。

- LTW: 既存のストア素材 (1280x800) を 680x425 に縮小するだけ
- リタス: 課題(assignments)画面1枚をヘッドレスChromeで撮り、白基調の台紙に
  「見出し＋端末画面」で載せて 16:10 にする（ltw.png と同じ構造にそろえる）

どちらも実データを含まない（学籍番号・氏名・実在の履修情報は写らない）。
出力は 680x425 = カード表示幅 338px の2倍。

■ 設計判断（2026-07-23 に旧デザインから作り直し）
  旧版はブランド緑の台紙にスマホ2枚を横並びにしていたが、縦長の端末を
  16:10 の横長枠に2枚詰めると各画面が小さくなり本文が読めなかった。
  ltw.png が読めるのは「大見出し＋横長スクショ1枚」だから。そこで
  litus 側も同じ「見出し＋スクショ」構造に統一し、白基調テーマで
  home 画面1枚を大きく載せることで legibility と2カードの統一感を得た。
  台紙は白基調（ユーザー指定）＝ltw の淡色地と重さがそろう。
  文字は PIL でなく HTML(CSS + Noto Sans JP)で組み Chrome に焼く
  （サイトと同じフォント/グラデ/影/角丸をそのまま出すため）。
  端末画面もユーザー指定で白テーマ＝home(緑グラデの看板画面)でなく、
  白基調の課題一覧を使う（緑ヘッダー帯＋白いリスト＋色分けした締切バッジ）。
  home/timetable は緑グラデの「看板」領域を持つ意匠なので白地の台紙と
  馴染まない。緑画面を白く塗るのは実アプリと異なる見せ方になるため、
  元から白基調の画面（課題一覧）に差し替える方針。

■ 実行環境（Mac）
  Claude セッションの PATH は素なので Chrome は絶対パスで叩く。
  Noto Sans JP は Google Fonts から取得するので要ネットワーク
  （--virtual-time-budget で取得を待つ）。Pillow は venv 等で用意する。

■ 課題(assignments)画面を選んだ理由
  白基調でありながら情報が詰まっており、リタスの中核価値（課題・締切の
  一元管理）が一目で伝わる。締切の緊急度が色（赤=期限切れ/橙=今日明日/
  緑=提出済み）で表現され、カード縮小時でも状態が読み取れる。
  ※home/timetable も現行プレビューでは描画されるが緑グラデの看板画面
  （過去メモの「home は中央が空・timetable は空グリッド」は古いプレビュー
  時点の話で現行HTMLでは両方描画される）。白テーマ指定により課題画面を採用。

■ プレビューHTML 由来の注意
  litus-design/previews/screens/*.html はダークモード切替トグル
  （.theme-toggle, position:fixed）が右上に乗る。製品UIではないので
  撮影時のみ CSS 注入で display:none にする（元HTMLは編集しない）。
"""
import os
import subprocess

from PIL import Image

# --- 環境パス（Mac） ---
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCREENS = "/Users/waiteu/dev/litus-design/previews/screens"
# shot3 = 「左に見出し＋右にポップアップ1枚」。litus.png と左右の構造が揃い、
# 数字・バッジが大きいので 680x425 まで縮めても読める。
# （shot1 は時間割グリッド 5列×3行＝縮小すると科目名が潰れるため不採用）
LTW_SRC = "/Users/waiteu/dev/lms-task-watcher-develop/store-assets/store-shot3.png"
OUT = "/Users/waiteu/dev/waiteu-dev/public/shots"
TMP = "/Users/waiteu/dev/waiteu-dev/.tmp-shots"

OUT_SIZE = (680, 425)   # 16:10 = カード表示幅の2倍

# home.html を 520x940 で撮ったときの端末フレームの位置（2倍解像度の実測値）。
# 影のにじみを含めず枠ぴったりに切る。プレビュー側の .phone を変えたら測り直す。
PHONE_BOX = (127, 125, 911, 1817)
PHONE_RADIUS_CSS = 20   # --radius-sheet。拡大率に応じて合成側でスケールする

os.makedirs(OUT, exist_ok=True)
os.makedirs(TMP, exist_ok=True)


def shoot(src_path, dst, w, h, extra=None):
    """file:// の HTML を 2倍解像度で PNG に焼く。"""
    subprocess.run(
        [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=2",
            *(extra or []),
            f"--window-size={w},{h}",
            f"--screenshot={dst}",
            "file://" + src_path,
        ],
        check=True,
        capture_output=True,
    )
    return Image.open(dst)


def shoot_screen(name, w, h, hide=None, css=None):
    """プレビュー画面HTMLを撮る。

    hide のセレクタは撮影時のみ非表示にする。css は撮影時だけ差し込む追加CSS
    （トークンの上書きなど）。どちらも litus-design 側の元HTMLは編集しない。
    """
    src_path = os.path.join(SCREENS, name + ".html")
    if hide or css:
        html = open(src_path, encoding="utf-8").read()
        style = "<style>"
        if hide:
            style += ",".join(hide) + "{display:none!important}"
        if css:
            style += css
        style += "</style>\n</head>"
        assert "</head>" in html
        html = html.replace("</head>", style, 1)
        src_path = os.path.join(TMP, name + ".shot.html")
        open(src_path, "w", encoding="utf-8").write(html)
    return shoot(src_path, os.path.join(TMP, name + ".png"), w, h).convert("RGB")


def build_litus(screen=None, out_name="litus.png"):
    # どの画面を載せるかは LITUS_SCREEN で差し替えられる（既定は下の SCREEN）。
    #   home     … .phone(390x844・角丸・影)で端末枠まで描かれる唯一の画面。
    #               緑グラデの「看板」意匠なので画面全体が緑になる。
    #   それ以外 … 白基調（緑ヘッダー帯＋白い本文）。端末枠は無いので
    #               合成側の角丸＋影を枠として使う。
    screen = screen or os.environ.get("LITUS_SCREEN", "home")
    if screen == "home":
        # home は看板グラデ（緑）が画面全体に敷かれる意匠。白基調で見せたいので
        # 撮影時だけ地を白に、ガラス面を「白地でも沈まない淡いカード」に置き換える。
        # ※実アプリのホームはライト/ダークとも緑。これは掲載素材用の見せ方。
        white = (
            ":root{--grad-top:#ffffff;--grad-bottom:#f2f7f5;"
            "--glass-bg:rgba(16,110,84,.055);"
            "--glass-border:rgba(16,110,84,.14);}"
        )
        scr = shoot_screen(screen, 520, 940, hide=[".theme-toggle"], css=white)
        phone = scr.crop(PHONE_BOX)
    else:
        # 幅540 = 右上のラベルが欠けない最小幅。
        # 高さ1240 = 下部のデバッグ操作行(position:fixed)を内容より下へ逃がす。
        scr = shoot_screen(screen, 540, 1240, hide=[".theme-toggle"])
        phone = scr.crop((0, 0, 1080, 1900))
    phone_path = os.path.join(TMP, "phone.png")
    phone.save(phone_path)

    # 合成キャンバス上での端末の表示幅。素の 392px から拡大するほど文字が読める。
    # 角丸は元の --radius-sheet を同じ倍率で拡大しないと枠の形が崩れる。
    PHONE_W = 540
    src_w_css = (PHONE_BOX[2] - PHONE_BOX[0]) / 2
    PHONE_R = round(PHONE_RADIUS_CSS * PHONE_W / src_w_css)

    composer = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:1200px; height:750px; overflow:hidden; }}
  body {{
    font-family:'Noto Sans JP', sans-serif;
    background:
      radial-gradient(120% 90% at 88% 8%, rgba(18,150,110,.16), rgba(18,150,110,0) 55%),
      linear-gradient(158deg, #ffffff 0%, #f5faf7 58%, #e9f5ef 100%);
  }}
  .wrap {{ display:flex; width:100%; height:100%; align-items:center; }}
  .left {{ width:53%; padding:0 28px 0 74px; }}
  .eyebrow {{ display:flex; align-items:center; gap:11px; margin-bottom:26px; }}
  .dot {{ width:11px; height:11px; border-radius:50%; background:#12946e;
          box-shadow:0 0 0 5px rgba(18,148,110,.14); }}
  .eyebrow span {{ font-size:16px; font-weight:700; letter-spacing:.11em; color:#2c7a60; }}
  h1 {{ font-size:47px; font-weight:800; line-height:1.36; color:#12241c; letter-spacing:.005em; }}
  .accent {{ color:#0f8a63; }}
  .sub {{ margin-top:24px; font-size:19px; font-weight:500; line-height:1.95; color:#566b61; }}
  .chips {{ display:flex; gap:10px; margin-top:34px; flex-wrap:wrap; }}
  .chip {{ font-size:14px; font-weight:700; color:#2f7a60; padding:8px 15px;
           border:1.5px solid rgba(18,148,110,.28); border-radius:999px;
           background:rgba(255,255,255,.6); }}
  .right {{ width:47%; height:100%; position:relative; }}
  /* 端末を大きく置き、下端をカンバスの外へ逃がす（bleed）。
     16:10 の横長枠に縦長の端末を「全部」入れると必ず小さくなるので、
     上部だけを大きく見せて可読性を取る。 */
  .phone {{ position:absolute; top:58px; left:-4px; width:{PHONE_W}px;
            border-radius:{PHONE_R}px; overflow:hidden;
            box-shadow:0 40px 80px rgba(14,80,60,.24), 0 6px 18px rgba(14,80,60,.12);
            outline:1px solid rgba(0,0,0,.04); }}
  .phone img {{ display:block; width:100%; }}
</style></head><body>
  <div class="wrap">
    <div class="left">
      <div class="eyebrow"><span class="dot"></span><span>リタス · LITUS</span></div>
      <h1>LETUSもCLASSも、<br><span class="accent">スマホひとつ</span>に。</h1>
      <p class="sub">毎朝ひらくだけ。<br>今日やることが、ひと目でわかる。</p>
      <div class="chips">
        <span class="chip">時間割</span>
        <span class="chip">出席</span>
        <span class="chip">課題</span>
        <span class="chip">掲示</span>
      </div>
    </div>
    <div class="right">
      <div class="phone"><img src="file://{phone_path}"></div>
    </div>
  </div>
</body></html>"""

    composer_path = os.path.join(TMP, "composer.html")
    open(composer_path, "w", encoding="utf-8").write(composer)
    comp = shoot(composer_path, os.path.join(TMP, "composer.png"),
                 1200, 750, extra=["--virtual-time-budget=4000"]).convert("RGB")
    comp.resize(OUT_SIZE, Image.LANCZOS).save(
        os.path.join(OUT, out_name), optimize=True)


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
