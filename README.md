# waiteu.dev

個人開発者ブランド「waiteu」のトップページ。ビルド工程なしの静的HTML1枚（[public/index.html](public/index.html)）。

## 配信

Cloudflare Pages プロジェクト `waiteu-dev`（apex `waiteu.dev` 割当済み）。

**配信対象は `public/` 配下のみ。** リポジトリのルートをデプロイしてはいけない。

- **自動デプロイ**: `master` への push で GitHub Actions（[.github/workflows/deploy.yml](.github/workflows/deploy.yml)）が `wrangler pages deploy public` を実行。
  - 必要な GitHub シークレット: `CLOUDFLARE_API_TOKEN`（Cloudflare の Account → Pages: Edit 権限のトークン）。
- **手動デプロイ**（ローカルから）:
  ```bash
  npx wrangler pages deploy public --project-name waiteu-dev --branch master --commit-dirty=true
  ```

### `.assetsignore` を使わない理由

以前は `wrangler pages deploy .` でルートを丸ごとデプロイし、`.assetsignore` に `README.md` などを並べて除外していた。**これは機能していなかった** — 2026-07-11 時点で `https://waiteu.dev/README.md` が 200 を返しており、除外リストは一度も適用されていなかった。

除外は「公開してはいけないものを数え上げる」作業であり、数え漏れが即座に公開事故になる。代わりに、公開してよいものだけを `public/` に置き、そこをデプロイする。**新しくファイルを足しても、`public/` の外にある限り公開されない。**

### 露出の確認方法（ステータスコードで判断しない）

Cloudflare Pages は**存在しないパスにも 200 で `index.html` を返す**。`https://waiteu.dev/README.md` が 200 でも、それは README が公開されている意味ではない（実際にトップページのHTMLが返っている）。**必ず中身を見て判定すること**:

```bash
curl -s https://waiteu.dev/README.md | head -1   # <!doctype html> なら未公開（フォールバック）
curl -sI https://waiteu.dev/README.md | grep -i content-type   # text/html なら未公開
```

なお `public/` の外にあっても、**GitHubの公開リポジトリでは誰でも読める**。「配信されない」と「非公開」は別物。機微情報は `docs/`（gitignore済み）に置く。

## 構成

```
public/
  index.html          トップページ
  og.png              OGP画像（1200x630）
  _headers            status.json に Cache-Control: no-store
  litus/terms.html    リタス 利用規約
  litus/status.json   リタス 緊急停止スイッチ（→ KILL-SWITCH-RUNBOOK.md）
docs/                 設計ドキュメント・実装計画（gitignore済み・ローカル専用）
```
