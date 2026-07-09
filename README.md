# waiteu.dev

個人開発者ブランド「waiteu」のトップページ。ビルド工程なしの静的HTML1枚（[index.html](index.html)）。

## 配信

Cloudflare Pages プロジェクト `waiteu-dev`（apex `waiteu.dev` 割当済み）。

- **自動デプロイ**: `master` への push で GitHub Actions（[.github/workflows/deploy.yml](.github/workflows/deploy.yml)）が `wrangler pages deploy` を実行。
  - 必要な GitHub シークレット: `CLOUDFLARE_API_TOKEN`（Cloudflare の Account → Pages: Edit 権限のトークン）。
- **手動デプロイ**（ローカルから）:
  ```bash
  npx wrangler pages deploy . --project-name waiteu-dev --branch master --commit-dirty=true
  ```

配信対象は `index.html` のみ（[.assetsignore](.assetsignore) で workflow / README / git メタを除外）。
