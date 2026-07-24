# waiteu.dev

個人開発者ブランド「waiteu」のトップページ。ビルド工程なしの静的HTML1枚（[public/index.html](public/index.html)）。

## 配信

Cloudflare Pages。**配信対象は `public/` 配下のみ**で、`master` への push で
GitHub Actions（[.github/workflows/deploy.yml](.github/workflows/deploy.yml)）が自動デプロイする。

## 構成

```
public/
  index.html          トップページ
  og.png              OGP画像（1200x630）
  _headers            status.json に Cache-Control: no-store
  litus/terms.html    リタス 利用規約
  litus/status.json   リタス 緊急停止スイッチ
tools/make-shots.py   カード画像の生成スクリプト
```
