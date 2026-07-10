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

## 構成

```
public/
  index.html        トップページ
  litus/terms.html  リタス 利用規約
docs/               設計ドキュメント・実装計画（非公開）
```
