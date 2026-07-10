# waiteu.dev トップページ再設計 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** waiteu.dev のトップページを、カード全体が各サービスのランディングへのリンクとして機能する、6ブロックの縦スクロール1枚に作り直す。

**Architecture:** 成果物は `index.html` 単一ファイル。CSS は `<style>`、JS は `<script>` にインライン。ビルド工程は導入しない。既存のCSS変数（配色）とフォント指定はそのまま流用し、レイアウトのみ再設計する。スクロール時の表示アニメーションだけ `IntersectionObserver` を使い、JS が無効でもコンテンツが見えるよう `html.js` クラスでガードする。

**Tech Stack:** 素のHTML / CSS / JavaScript。Google Fonts（Noto Sans JP）。配信は Cloudflare Pages（`master` push → GitHub Actions → `wrangler pages deploy`）。

## Global Constraints

仕様 `docs/superpowers/specs/2026-07-10-waiteu-dev-redesign-design.md` の全体制約。**全タスクの要件に暗黙に含まれる。**

- ビルド工程を導入しない。`index.html` を配置するだけで動くこと
- 外部依存は Google Fonts のみ。CSSフレームワーク・JSライブラリを追加しない
- 配色は変更しない。ライト `--bg: #f7f4ef` / `--fg: #2b2723` / `--accent: #d9724c`、ダーク `--bg: #221e1a` / `--fg: #f2ede6` / `--accent: #e8875f`
- フォントは Noto Sans JP。現行の `<link>` をそのまま使う
- 入れ子の `<a>` を作らない
- 文言は仕様の「文言（確定稿）」から**一字一句変えない**。特に以下は理由があって現在の形になっている。善意で「揃える」と壊れる:
  - 「永久に無料」と書かない。「黙って始めることはしない」は短文のまま維持する
  - 「使いづらいものを、気合いで使い続けるしかないのはおかしい」の矛先は LETUS と CLASS であって学生ではない
  - About の献辞は「すべての理科大生へ」と限定し、Contact の呼びかけは誰も限定しない。この非対称は意図的
  - Contact に「困りごと**からしか**決まらない」と書かない（Roadmap と自己矛盾する）
- リンク先: リタス `https://lms.waiteu.dev/app`、拡張 `https://lms.waiteu.dev/`。Chrome Web Store への直リンクは置かない

---

## File Structure

| ファイル | 責務 |
|---|---|
| `index.html` | ページ全体（構造・スタイル・スクリプト）。**変更** |
| `.assetsignore` | Cloudflare Pages の配信対象から除外するパス。**変更**（`docs` と `.claude` を追加） |
| `.claude/launch.json` | ローカル検証用の静的サーバ定義。**新規** |

`index.html` は約400行になるが、分割しない。ビルド工程がないため分割すると配信ファイルが増え、非目標に反する。現行も単一ファイルであり、既存パターンを踏襲する。

---

### Task 1: 配信除外とローカル検証環境

`docs/` を配信対象から外す。現行の `.assetsignore` は `.github` / `.git` / `.assetsignore` / `README.md` のみを除外しており、このままだと設計ドキュメントと本計画が `https://waiteu.dev/docs/superpowers/...` として公開される（`litus/terms.html` が配信されているのと同じ仕組み）。あわせて、後続タスクの検証に使う静的サーバを定義し、その `.claude/` も除外する。

**Files:**
- Modify: `.assetsignore`
- Create: `.claude/launch.json`

**Interfaces:**
- Consumes: なし
- Produces: `preview_start` で起動できるサーバ名 `waiteu-dev`（ポート 4173）。Task 2〜5 の検証で使う

- [ ] **Step 1: `.assetsignore` に `docs` と `.claude` を追加**

`.assetsignore` の全文を以下にする。

```
.github
.git
.assetsignore
README.md
docs
.claude
```

- [ ] **Step 2: `.claude/launch.json` を作成**

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "waiteu-dev",
      "runtimeExecutable": "npx",
      "runtimeArgs": ["--yes", "serve", "--listen", "4173", "."],
      "port": 4173
    }
  ]
}
```

- [ ] **Step 3: 除外が効くことを確認**

Run: `npx --yes wrangler pages deploy . --project-name waiteu-dev --dry-run 2>&1 | head -20`

Expected: アップロード対象のファイル数が表示され、`docs/` 配下のファイルが含まれない。`--dry-run` が未対応のバージョンでエラーになる場合は、代わりに `.assetsignore` の内容を目視確認して次へ進む（Cloudflare Pages は `.assetsignore` の各行をパスのプレフィックスとして扱う）。

- [ ] **Step 4: コミット**

```bash
git add .assetsignore .claude/launch.json
git commit -m "Exclude docs from Pages deploy, add local preview server"
```

---

### Task 2: HTML構造と文言

`index.html` の `<body>` を、Hero / About / Products / Roadmap / Contact / Footer の6ブロックに置き換える。この時点ではスタイルは旧CSSのままなので**表示は崩れる**。それでよい。Task 3 でCSSを入れ替える。

構造だけを先に確定させるのは、文言とリンク先とマークアップの正しさ（入れ子 `<a>` がない、見出しレベルが飛ばない）を、見た目に惑わされずに確認するためである。

**Files:**
- Modify: `index.html`（`<body>` 内すべて。`<head>` と `<style>` は次タスクまで触らない）

**Interfaces:**
- Consumes: Task 1 の `preview_start` サーバ名 `waiteu-dev`
- Produces: 以下のクラス名。Task 3 のCSSと Task 4 のJSがこれに依存する
  - ブロック: `.page` `.hero` `.section` `.footer`
  - 見出し: `.eyebrow` `.rule` `.lede`
  - 本文: `.prose` `.stances` `.dedication`
  - 製品: `.cards` `.card` `.card-topbar` `.card-body` `.card-meta` `.card-kind` `.card-title` `.card-desc` `.cta`
  - 状態: `.pill` `.pill-live` `.pill-soon` `.pill-wip`
  - 行程: `.timeline` `.phase` `.phase-head` `.phase-no` `.phase-title` `.phase-desc`
  - 連絡先: `.links` `.link-item` `.badge` `.link-label`
  - 出現制御: `.reveal`（Task 4 が `.is-visible` を付与する）

- [ ] **Step 1: `<body>` を差し替える**

`index.html` の `<body>` 開始タグから `</body>` 直前までを、以下で置き換える。

```html
<body>
  <main class="page">

    <header class="hero">
      <div class="wordmark">waiteu</div>
      <hr class="rule">
      <p class="lede">東京理科大生。学生のためのツールを、個人でつくっています。</p>
    </header>

    <section class="section reveal" aria-labelledby="about-heading">
      <h2 class="eyebrow" id="about-heading">ABOUT</h2>

      <div class="prose">
        <p>課題の提出期限を、一度落としかけたことがある。</p>
        <p>LETUSを開いて履修科目をひとつずつ辿り、締切を目で拾う。必要な情報がLETUSとCLASSに分かれて置かれている。使いづらいものを、気合いで使い続けるしかないのはおかしい。</p>
        <p>だから自分で作ることにした。まずブラウザ拡張を、次にスマートフォンアプリを。</p>
      </div>

      <ul class="stances">
        <li><strong>無料で始める。</strong>学生からお金を取るために作っていないが、安全に、止めずに提供し続けるにはお金がかかる。その負担が無視できなくなったときは、有料化して支援をお願いすることがある。黙って始めることはしない。</li>
        <li><strong>パスワードは読み取らない。</strong>ログイン情報に触れない設計にしている。</li>
        <li><strong>動かし続けることを優先する。</strong>機能を足すより壊れないことを選ぶ。学期の途中で止まらないことが、いちばんの機能だと思っている。</li>
      </ul>

      <p class="dedication">日々を生き抜く、すべての理科大生へ。</p>
    </section>

    <section class="section reveal" aria-labelledby="products-heading">
      <h2 class="eyebrow" id="products-heading">PRODUCTS</h2>

      <div class="cards">
        <a class="card" href="https://lms.waiteu.dev/app">
          <span class="card-topbar" aria-hidden="true"></span>
          <span class="card-body">
            <span class="card-meta">
              <span class="card-kind">モバイルアプリ</span>
              <span class="pill pill-soon">事前登録受付中</span>
            </span>
            <span class="card-title">リタス（Litus）</span>
            <span class="card-desc">LETUSもCLASSも、スマホひとつに。時間割・出席・課題をまとめる。</span>
            <span class="cta">事前登録ページへ<span aria-hidden="true">→</span></span>
          </span>
        </a>

        <a class="card" href="https://lms.waiteu.dev/">
          <span class="card-topbar" aria-hidden="true"></span>
          <span class="card-body">
            <span class="card-meta">
              <span class="card-kind">Chrome拡張</span>
              <span class="pill pill-live">公開中</span>
            </span>
            <span class="card-title">LETUS課題ウォッチャー</span>
            <span class="card-desc">LETUSの課題期限を自動で集めて、締切前に通知する。</span>
            <span class="cta">紹介ページへ<span aria-hidden="true">→</span></span>
          </span>
        </a>
      </div>
    </section>

    <section class="section reveal" aria-labelledby="roadmap-heading">
      <h2 class="eyebrow" id="roadmap-heading">ROADMAP</h2>

      <ol class="timeline">
        <li class="phase">
          <div class="phase-head">
            <span class="phase-no">フェーズ1</span>
            <span class="pill pill-live">公開中</span>
          </div>
          <h3 class="phase-title">LETUS課題ウォッチャー</h3>
          <p class="phase-desc">課題の自動収集と締切通知</p>
        </li>
        <li class="phase">
          <div class="phase-head">
            <span class="phase-no">フェーズ2</span>
            <span class="pill pill-wip">進行中</span>
          </div>
          <h3 class="phase-title">CLASS連携</h3>
          <p class="phase-desc">時間割と出席を、課題と同じ場所に</p>
        </li>
        <li class="phase">
          <div class="phase-head">
            <span class="phase-no">フェーズ3</span>
            <span class="pill pill-soon">準備中</span>
          </div>
          <h3 class="phase-title">リタス</h3>
          <p class="phase-desc">すべてをスマートフォンへ</p>
        </li>
      </ol>
    </section>

    <section class="section reveal" aria-labelledby="contact-heading">
      <h2 class="eyebrow" id="contact-heading">CONTACT</h2>

      <p class="prose">うまくいかないことがあれば、教えてください。使っている人の困りごとが、いちばん確かな手がかりです。</p>

      <nav class="links" aria-label="外部リンク">
        <a class="link-item" href="https://github.com/waiteu-git" target="_blank" rel="noopener">
          <span class="badge">GH</span>
          <span class="link-label">GitHub</span>
        </a>
        <a class="link-item" href="https://x.com/yning_y2" target="_blank" rel="noopener">
          <span class="badge">X</span>
          <span class="link-label">X</span>
        </a>
        <a class="link-item" href="mailto:y2studyabout@gmail.com">
          <span class="badge">@</span>
          <span class="link-label">メール</span>
        </a>
      </nav>
    </section>

    <footer class="footer">© waiteu</footer>

  </main>
</body>
```

**カード内が `<span>` だらけなのは意図的である。** `<a>` の内側に `<h2>` や `<p>` を置くと、`<a>` は phrasing content しか持てないためHTMLとして不正になる。見た目の階層はCSSで作り、意味の階層は `.card-title` を `<span>` のまま扱う。カード全体が1つのリンクであることが、支援技術にとっても正しい構造になる。

- [ ] **Step 2: 入れ子リンクがないことを確認**

Run: `grep -c '<a ' index.html`

Expected: `5`（カード2 + 外部リンク3）。

続けて、`<a class="card">` の内側に `<a` が現れないことを目視で確認する。カード内は `<span>` のみであること。

- [ ] **Step 3: リンク先を確認**

Run: `grep -o 'href="https://lms.waiteu.dev[^"]*"' index.html`

Expected:
```
href="https://lms.waiteu.dev/app"
href="https://lms.waiteu.dev/"
```

- [ ] **Step 4: Chrome Web Store への直リンクが消えたことを確認**

Run: `grep -c 'chromewebstore' index.html`

Expected: `0`（`grep -c` は該当なしで終了コード1を返すが、出力される数値が `0` であればよい）。

- [ ] **Step 5: 6ブロックが揃っていることを確認**

Run: `preview_start` でサーバ `waiteu-dev` を起動し、`preview_snapshot` を撮る。

Expected: アクセシビリティツリーに `ABOUT` / `PRODUCTS` / `ROADMAP` / `CONTACT` の見出しと、wordmark `waiteu`、フッター `© waiteu` が現れる。カードは2つのリンクとして現れ、それぞれのリンク名に「リタス（Litus）」「LETUS課題ウォッチャー」が含まれる。

この時点で**レイアウトは崩れている**。旧CSSに新しいクラスの定義がないため。次のタスクで直す。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "Restructure top page into six blocks, make cards whole-card links"
```

---

### Task 3: CSS再設計

`<style>` の中身を入れ替える。配色変数とフォント指定は現行から引き継ぐ。レイアウトを中央寄せ1画面完結から、左寄せ単一カラムの縦スクロールへ変える。

**Files:**
- Modify: `index.html`（`<style>` 内すべて）

**Interfaces:**
- Consumes: Task 2 が定義したクラス名
- Produces: `.reveal` の初期状態（`html.js` のときのみ不可視）と `.reveal.is-visible`（可視）。Task 4 の JS がこの2つに依存する

- [ ] **Step 1: `<style>` の中身を差し替える**

`<style>` の開始タグ直後から `</style>` 直前までを、以下で置き換える。

```css
  :root {
    --accent: #d9724c;
    --bg: #f7f4ef;
    --fg: #2b2723;
    --muted: rgba(43, 39, 35, .6);
    --muted-strong: rgba(43, 39, 35, .5);
    --card: #f2ede4;
    --card-links: #e9e2d6;
    --footer: rgba(43, 39, 35, .45);
    --line: rgba(43, 39, 35, .14);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --accent: #e8875f;
      --bg: #221e1a;
      --fg: #f2ede6;
      --muted: rgba(242, 237, 230, .62);
      --muted-strong: rgba(242, 237, 230, .52);
      --card: #2c2621;
      --card-links: #352e27;
      --footer: rgba(242, 237, 230, .45);
      --line: rgba(242, 237, 230, .16);
    }
  }

  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    background: var(--bg);
    color: var(--fg);
    font-family: "Noto Sans JP", sans-serif;
    line-height: 1.8;
  }

  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
    border-radius: 4px;
  }

  .page {
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    padding: 72px 24px 56px;
    display: flex;
    flex-direction: column;
    gap: 72px;
  }

  /* --- 出現アニメーション（JS有効時のみ隠す） --- */
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  html.js .reveal {
    opacity: 0;
    transform: translateY(14px);
    transition: opacity .6s ease, transform .6s ease;
  }
  html.js .reveal.is-visible {
    opacity: 1;
    transform: none;
  }

  /* --- Hero --- */
  .hero { animation: fadeInUp .5s ease both; }
  .wordmark {
    font-weight: 800;
    font-size: 40px;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }
  .rule {
    width: 36px;
    height: 2px;
    background: var(--accent);
    margin: 16px 0;
    border: none;
  }
  .lede {
    margin: 0;
    font-size: 15px;
    line-height: 1.8;
    color: var(--muted);
  }

  /* --- セクション共通 --- */
  .section {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  .eyebrow {
    margin: 0;
    font-size: 11px;
    letter-spacing: .12em;
    font-weight: 700;
    color: var(--muted-strong);
  }

  .prose { margin: 0; }
  .prose p {
    margin: 0 0 18px;
    font-size: 15px;
    line-height: 1.9;
  }
  .prose p:last-child { margin-bottom: 0; }

  /* --- スタンス --- */
  .stances {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .stances li {
    font-size: 14.5px;
    line-height: 1.9;
    color: var(--muted);
    padding-left: 16px;
    border-left: 2px solid var(--line);
  }
  .stances strong {
    display: block;
    color: var(--fg);
    font-weight: 700;
  }

  /* --- 献辞 --- */
  .dedication {
    margin: 12px 0 0;
    padding-top: 28px;
    border-top: 2px solid var(--accent);
    border-image: none;
    text-align: center;
    font-size: 17px;
    font-weight: 700;
    line-height: 1.8;
  }
  @supports (width: min(1px, 2px)) {
    .dedication {
      border-top: none;
      position: relative;
    }
    .dedication::before {
      content: "";
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 36px;
      height: 2px;
      background: var(--accent);
    }
  }

  /* --- 状態pill --- */
  .pill {
    display: inline-block;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .04em;
    line-height: 1;
    padding: 5px 8px;
    border-radius: 999px;
    border: 1px solid var(--line);
    color: var(--muted-strong);
    white-space: nowrap;
  }
  .pill-live {
    color: var(--accent);
    border-color: var(--accent);
  }

  /* --- カード --- */
  .cards {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .card {
    display: block;
    background: var(--card);
    border-radius: 12px;
    overflow: hidden;
    text-decoration: none;
    color: inherit;
    transition: transform .18s ease, box-shadow .18s ease;
  }
  .card-topbar {
    display: block;
    height: 4px;
    background: var(--accent);
    transition: height .18s ease;
  }
  .card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, .10);
  }
  .card:hover .card-topbar { height: 7px; }
  .card-body {
    display: block;
    padding: 22px 22px 24px;
  }
  .card-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }
  .card-kind {
    font-size: 10.5px;
    letter-spacing: .08em;
    font-weight: 700;
    color: var(--muted-strong);
  }
  .card-title {
    display: block;
    font-size: 19px;
    font-weight: 700;
    line-height: 1.5;
    color: var(--fg);
  }
  .card-desc {
    display: block;
    margin: 8px 0 16px;
    font-size: 13.5px;
    line-height: 1.75;
    color: var(--muted);
  }
  .cta {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--accent);
    font-weight: 700;
    font-size: 14px;
  }
  .card:hover .cta { text-decoration: underline; }

  /* --- ロードマップ --- */
  .timeline {
    list-style: none;
    margin: 0;
    padding: 0 0 0 26px;
    border-left: 2px solid var(--line);
    display: flex;
    flex-direction: column;
    gap: 32px;
  }
  .phase { position: relative; }
  .phase::before {
    content: "";
    position: absolute;
    left: -33px;
    top: 6px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--bg);
    border: 2px solid var(--accent);
  }
  .phase-head {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .phase-no {
    font-size: 10.5px;
    letter-spacing: .08em;
    font-weight: 700;
    color: var(--muted-strong);
  }
  .phase-title {
    margin: 8px 0 0;
    font-size: 17px;
    font-weight: 700;
    line-height: 1.5;
  }
  .phase-desc {
    margin: 4px 0 0;
    font-size: 13.5px;
    line-height: 1.75;
    color: var(--muted);
  }

  /* --- Contact --- */
  .links {
    background: var(--card-links);
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    flex-wrap: wrap;
    gap: 22px;
  }
  .link-item {
    display: flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    color: inherit;
  }
  .link-item:hover { opacity: .72; }
  .badge {
    width: 30px;
    height: 30px;
    border-radius: 6px;
    background: var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
    font: 700 12px ui-monospace, Menlo, monospace;
    color: var(--fg);
    flex: none;
  }
  .link-label {
    font-size: 12.5px;
    color: var(--fg);
    font-weight: 500;
  }

  .footer {
    font-size: 11.5px;
    color: var(--footer);
  }

  /* --- 広い画面 --- */
  @media (min-width: 760px) {
    .page {
      max-width: 760px;
      padding: 112px 32px 80px;
      gap: 96px;
    }
    .wordmark { font-size: 60px; }
    .rule { width: 44px; margin: 20px 0; }
    .lede { font-size: 17px; }

    .section { gap: 28px; }
    .eyebrow { font-size: 11.5px; }
    .prose p { font-size: 16px; }
    .stances li { font-size: 15px; padding-left: 20px; }
    .dedication { font-size: 20px; padding-top: 32px; }

    .cards {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .card-body { padding: 28px 26px 30px; }
    .card-title { font-size: 21px; }
    .card-desc { font-size: 14px; }

    .links { padding: 16px 24px; gap: 32px; }
    .badge { width: 34px; height: 34px; }
    .link-label { font-size: 13.5px; }

    .footer { font-size: 12.5px; }
  }

  /* --- モーション抑制 --- */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: .001ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: .001ms !important;
      scroll-behavior: auto !important;
    }
    html.js .reveal {
      opacity: 1;
      transform: none;
    }
  }
```

`.dedication` の `@supports` ブロックは、罫を文字幅いっぱいではなく中央の36pxだけに引くためのもの。`border-top` はフォールバックとして残してある。

- [ ] **Step 2: レイアウトを目視確認**

Run: `preview_start` でサーバ `waiteu-dev` を起動（起動済みならリロード）、`preview_screenshot`。

Expected: 上から wordmark、ABOUT（3段落＋スタンス3件＋中央寄せの献辞）、PRODUCTS（カード2枚）、ROADMAP（縦線とドット3つ）、CONTACT（リンク3つ）、フッターが順に並ぶ。この時点では `.reveal` に `.is-visible` が付かないが、`html.js` クラスも付いていないため**すべて見えている**こと。

- [ ] **Step 3: カードのホバーとフォーカスを確認**

Run: `preview_inspect` でセレクタ `.card` を指定し、`['background-color', 'border-radius', 'display']` を取得。

Expected: `display: block`、`border-radius: 12px`、背景がライトモードで `rgb(242, 237, 228)`（`#f2ede4`）。

- [ ] **Step 4: モバイル幅で横スクロールが出ないことを確認**

Run: `preview_resize` で `preset: "mobile"`（375x812）にし、`preview_eval` で
```js
document.documentElement.scrollWidth <= window.innerWidth
```

Expected: `true`

- [ ] **Step 5: ダークモードを確認**

Run: `preview_resize` で `colorScheme: "dark"` にし、`preview_inspect` で `body` の `['background-color', 'color']` を取得。

Expected: `background-color: rgb(34, 30, 26)`（`#221e1a`）、`color: rgb(242, 237, 230)`（`#f2ede6`）。続けて `preview_screenshot` を撮り、文字が背景に沈んでいないことを目視で確認する。確認後 `colorScheme: "light"` に戻す。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "Redesign layout as single-column scrolling page"
```

---

### Task 4: スクロール表示とモーション抑制

`.reveal` を持つセクションを、画面に入ったタイミングで表示する。JS が無効・失敗した場合にコンテンツが永久に不可視になってはならないため、**JS 自身が `html.js` クラスを付けてから隠す**という順序にする。CSS 側は Task 3 で既に `html.js .reveal` としてガード済み。

**Files:**
- Modify: `index.html`（`</body>` 直前に `<script>` を追加）

**Interfaces:**
- Consumes: Task 3 の `html.js .reveal` / `html.js .reveal.is-visible`
- Produces: なし（最終タスク）

- [ ] **Step 1: `</body>` の直前に `<script>` を追加**

```html
  <script>
    (function () {
      var root = document.documentElement;
      if (!('IntersectionObserver' in window)) return;
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

      root.classList.add('js');

      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -10% 0px' });

      document.querySelectorAll('.reveal').forEach(function (el) {
        observer.observe(el);
      });
    })();
  </script>
```

**`root.classList.add('js')` が2つの早期 return より後にあることが要点である。** `IntersectionObserver` が無い環境、あるいはモーション抑制が有効な環境では `html.js` が付かないので、CSS の `html.js .reveal { opacity: 0 }` が一度も適用されない。「隠す責任を持つ者だけが、見せる責任も持つ」という形にしてある。

- [ ] **Step 2: スクロールで表示されることを確認**

Run: `preview_start`（起動済みならリロード）のうえ `preview_eval` で
```js
(function () {
  var below = document.querySelectorAll('.reveal:not(.is-visible)').length;
  window.scrollTo(0, document.body.scrollHeight);
  return { hasJsClass: document.documentElement.classList.contains('js'), hiddenBeforeScroll: below };
})()
```

Expected: `hasJsClass: true`、`hiddenBeforeScroll` が 1 以上（ファーストビュー外のセクションが隠れている）。

続けて 1 秒ほど置いてから `preview_eval` で
```js
document.querySelectorAll('.reveal:not(.is-visible)').length
```

Expected: `0`（最下部までスクロールした結果、全セクションが可視になっている）。

- [ ] **Step 3: モーション抑制時にコンテンツが見えることを確認**

`prefers-reduced-motion` はブラウザ設定であり `preview_resize` では切り替えられない。代わりに `preview_eval` で CSS の効き方を直接確かめる。

Run:
```js
(function () {
  var el = document.querySelector('.reveal');
  var cs = getComputedStyle(el);
  return { opacity: cs.opacity, transform: cs.transform };
})()
```

Expected: 最下部までスクロール済みの状態で `opacity: "1"`。

加えて、**JS を無効化した状態を模擬する**。`preview_eval` で
```js
(function () {
  document.documentElement.classList.remove('js');
  var el = document.querySelector('.reveal');
  return getComputedStyle(el).opacity;
})()
```

Expected: `"1"`。`html.js` が無ければ `.reveal` は隠れない、という設計が効いていることの確認。確認後はリロードして状態を戻す。

- [ ] **Step 4: キーボード操作を確認**

Run: `preview_eval` で
```js
(function () {
  var card = document.querySelector('.card');
  card.focus();
  var cs = getComputedStyle(card, ':focus-visible');
  return { tag: card.tagName, href: card.getAttribute('href'), focused: document.activeElement === card };
})()
```

Expected: `tag: "A"`、`href: "https://lms.waiteu.dev/app"`、`focused: true`。

`<a href>` はネイティブにフォーカス可能・Enter で遷移するため、`tabindex` や `keydown` ハンドラは追加しない。

- [ ] **Step 5: コンソールエラーがないことを確認**

Run: `preview_console_logs` で `level: "error"`。

Expected: エラーなし。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "Reveal sections on scroll, respect prefers-reduced-motion"
```

---

### Task 5: 受け入れ条件の通し確認

仕様の受け入れ条件を、実装が終わった状態で頭から順に観測する。ここで初めて「全部そろっているか」を見る。個々のタスクで確認済みの項目も、**再度観測する**（途中のタスクが後のタスクで壊れていないことの確認）。

**Files:**
- Modify: なし（不合格項目が出た場合のみ `index.html`）

**Interfaces:**
- Consumes: Task 1〜4 のすべて
- Produces: なし

- [ ] **Step 1: 静的な確認**

Run:
```bash
grep -c '<a ' index.html
grep -o 'href="https://lms.waiteu.dev[^"]*"' index.html
grep -c 'chromewebstore' index.html
grep -c 'prefers-reduced-motion' index.html
grep -c '^docs$' .assetsignore
```

Expected: 順に `5`、`href="https://lms.waiteu.dev/app"` と `href="https://lms.waiteu.dev/"`、`0`、`1`、`1`。

- [ ] **Step 2: 文言が仕様と一字一句一致することを確認**

`docs/superpowers/specs/2026-07-10-waiteu-dev-redesign-design.md` の「文言（確定稿）」と `index.html` のテキストを突き合わせる。特に以下を確認する。

- 「黙って始めることはしない。」が存在する。「永久に無料」が存在しない
- 「使いづらいものを、気合いで使い続けるしかないのはおかしい。」が存在する
- 「日々を生き抜く、すべての理科大生へ。」が存在する
- 「いちばん確かな手がかりです。」が存在する。「からしか」が存在しない

Run: `grep -c 'からしか\|永久に無料' index.html`

Expected: `0`

- [ ] **Step 3: ブラウザで通し確認**

`preview_start` → `preview_snapshot` で以下を確認する。

- Hero / ABOUT / PRODUCTS / ROADMAP / CONTACT / フッターの6ブロックが上から順に存在する
- カード2枚がリンクとして現れ、リンク先が `lms.waiteu.dev/app` と `lms.waiteu.dev/`
- 入れ子リンクが存在しない

`preview_resize` で mobile（375px）→ `preview_eval` で `document.documentElement.scrollWidth <= window.innerWidth` が `true`。

`preview_resize` で `colorScheme: "dark"` → `preview_screenshot` で読める。`light` に戻す。

`preview_console_logs`（`level: "error"`）でエラーなし。

- [ ] **Step 4: 仕様の受け入れ条件にチェックを入れる**

`docs/superpowers/specs/2026-07-10-waiteu-dev-redesign-design.md` の受け入れ条件9項目のうち、観測できたものに `- [x]` を入れる。**観測していない項目にチェックを入れてはならない。**

- [ ] **Step 5: コミット**

```bash
git add docs/superpowers/specs/2026-07-10-waiteu-dev-redesign-design.md
git commit -m "Check off acceptance criteria for top page redesign"
```

- [ ] **Step 6: デプロイはユーザーに確認する**

`master` への push が Cloudflare Pages への本番デプロイを引き起こす（`.github/workflows/deploy.yml`）。**push する前にユーザーの承認を得る。** 承認が得られたら:

```bash
git push origin master
```

push 後、`https://waiteu.dev/` を開いて表示を確認し、あわせて `https://waiteu.dev/docs/superpowers/plans/2026-07-10-waiteu-dev-redesign.md` が **404 になる**ことを確認する（Task 1 の除外が本番で効いていることの検証）。

---

## Self-Review

**1. Spec coverage**

| 仕様の要求 | 実装タスク |
|---|---|
| カード全体がリンク | Task 2 Step 1 |
| リンク先 `/app` と `/` | Task 2 Step 1・Step 3 |
| Chrome Web Store 直リンク廃止 | Task 2 Step 4 |
| 6ブロックの情報設計 | Task 2 Step 1 |
| 文言（確定稿） | Task 2 Step 1、Task 5 Step 2 |
| 配色・フォント維持 | Task 3 Step 1（`:root` を現行から引き継ぎ） |
| 左寄せ単一カラム | Task 3 Step 1（`.page { max-width: 680px }`） |
| `.eyebrow` / `.rule` の流用 | Task 3 Step 1 |
| カードの hover / focus-visible / pill | Task 3 Step 1 |
| 献辞の中央寄せ・上に罫 | Task 3 Step 1（`.dedication`） |
| 縦タイムライン | Task 3 Step 1（`.timeline` / `.phase::before`） |
| Contact のセクション昇格 | Task 2 Step 1、Task 3 Step 1 |
| `IntersectionObserver` によるスクロール表示 | Task 4 Step 1 |
| `prefers-reduced-motion` 対応 | Task 3 Step 1、Task 4 Step 1・Step 3 |
| ビルド工程を増やさない | 全タスク（`.claude/launch.json` は配信対象外） |
| `docs/` を配信対象から除外 | Task 1 |

未カバーの仕様項目なし。

**2. Placeholder scan**

「TBD」「後で実装」「適切にエラー処理」等の記述なし。すべてのコードステップに実際のコードが入っている。

**3. Type consistency**

Task 2 が定義するクラス名と、Task 3 のCSSセレクタ、Task 4 のJSセレクタ（`.reveal` / `is-visible` / `js`）が一致していることを確認済み。`.card-kind` は Task 2・Task 3 の双方で `.card-kind`（旧 `.eyebrow` からの改名。カードの種別ラベルとセクション見出しは役割が異なるため別クラスにした）。
