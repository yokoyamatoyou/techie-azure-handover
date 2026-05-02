# UI Unification Plan 2026-03-31

## Goal

`C:\tetie\aio2-main`、`C:\tetie\notecode`、`C:\tetie\kotomegane` を、別アプリではなく同一 SaaS 群として見える状態へ寄せる。  
目標は「見た瞬間に同じ会社・同じ製品群だと分かること」であり、単なる似た暖色UIにとどめない。

## Current Diagnosis

### すでに共通している点

- 3製品ともクリーム系背景、暖色アクセント、濃いブラウン系ナビを採用している
- 情報カード中心の NiceGUI 構成で、やさしいトーンは揃っている
- 日本語UIで、非エンジニア向けの読みやすさを意識している

### まだ統一感が弱い点

- フォントが揃っていない
  - `aio2-main`: `Sora`
  - `notecode`: `Work Sans`
  - `kotomegane`: `Space Grotesk`
- アクセント色の役割が揃っていない
  - ブランド色と警告色が混ざる場面がある
  - `自社 / 競合 / 外部` の意味色が製品横断で固定されていない
- カードの主従構造が製品ごとに違う
  - どこが主カードでどこが補助カードかの判断が製品ごとにぶれる
- ナビ、ヒーロー、バッジ、ステップ表示の文法が一致していない

## Shared Design Direction

### 1. ブランドシェルを共通化する

- 上部ナビは `濃いブラウン背景 + 同一高さ + 同一アクティブ色` に統一する
- 画面の最大幅、左右余白、カード角丸、影の強さを3製品で揃える
- ヒーローは「ロゴ / プロダクト名 / 一文価値訴求 / 補助チップ」の4要素を基本構成にする

### 2. タイポグラフィを共通化する

- 見出しとプロダクト名は `Sora`
- 本文、テーブル、フォーム、長文は `Noto Sans JP`
- `Space Grotesk` と `Work Sans` は段階的に外す

理由:  
`Sora` は `aio2-main` ですでに使われていて、SaaS 的な骨格を出しやすい。  
日本語本文は `Noto Sans JP` に寄せたほうが可読性が安定する。

### 3. 色の役割を固定する

ブランド色は「押せる場所」「選ばれている場所」「製品名」に限定する。  
状態色はブランド色と分離する。

#### 共通トークン案

```text
--bg: #FCF5EC
--bg-deep: #F4E5D6
--surface: #FFFDF8
--surface-muted: #F7F0E5
--text: #241813
--text-soft: #5E4D43
--muted: #746458
--brand: #E64424
--brand-deep: #BF4321
--brand-soft: rgba(230, 68, 36, 0.12)
--self: #2F8A57
--self-soft: rgba(47, 138, 87, 0.12)
--competitive: #B67A35
--competitive-soft: rgba(182, 122, 53, 0.14)
--external: #B44A2B
--external-soft: rgba(180, 74, 43, 0.12)
--border: rgba(72, 58, 50, 0.12)
--border-strong: rgba(72, 58, 50, 0.18)
--shadow: 0 10px 28px rgba(42, 31, 26, 0.08)
--shadow-hover: 0 14px 36px rgba(42, 31, 26, 0.12)
--nav-bg: #241813
--nav-text: #D8C6B8
--nav-text-active: #E64424
```

2026-04-01 時点の `kotomegane` では、この命名を基準に `Sora + Noto Sans JP`、`card-primary / card-secondary / card-detail`、`brand / self / competitive / external` を実装側へ反映済み。

#### 意味ルール

- `brand`: CTA、アクティブ状態、製品名、主要リンク
- `self`: 自社優勢、完了、成功、Owned
- `competitive`: 比較対象、注意、保留、並走
- `external`: 外部優勢、未露出、失敗、リスク
- `muted`: 補助文、メモ、説明、非主役情報

### 4. カード階層を共通化する

3種類だけに絞る。

- Primary Card
  - 一番見てほしい結論
  - 白寄り背景
  - 強めの境界線
  - 影あり
- Secondary Card
  - 補足情報
  - 少し muted な背景
  - 境界線は薄め
  - 影は弱め
- Detail Panel
  - 折りたたみ先
  - muted surface
  - 影なし、または inset のみ

2026-04-01 の `kotomegane` 実装では、上記をそれぞれ `card-primary` / `card-secondary` / `card-detail` として置き、他2製品へ移植しやすいクラス名に寄せた。
同日の追加実装で、`saved brief` と `outcome compare` も `card-detail` を基底にし、上段に `summary-eyebrow`、中段に mini stat、下段に軽い比較表を置く文法へ揃えた。

### 5. 共通コンポーネント文法を決める

- CTA ボタンは全製品で同じグラデーション
- ステップチップは `active / done / idle` の3状態だけにする
- バッジは `brand / self / competitive / external / muted` の5種だけにする
- Expansion の見た目を統一する
- テーブル見出し背景と文字色を統一する
- 保存済み下書きの再表示と 2 系列比較は、`detail panel -> eyebrow -> mini-stat -> compact table` の並びで統一する
- 主導線は `workflow rail -> stage header -> 主カード` の 3 段で区切り、`入力する / 設定する / 結果を見る` を日本語で示す

### 6. グラフ文法を共通化する

- 意味を持つ系列は必ず semantic color を使う
  - `自社=緑`
  - `競合=琥珀`
  - `外部=赤茶`
- 意味を持たない識別色は、ブランドトーンから外れすぎない順序色にする
- グラフタイトルと補助文の構成は全製品で揃える

## Product-by-Product Guidance

### kotomegane

- 先にやるべき判断を出すダッシュボードとして、semantic color を最も強く使う
- `自社 / 競合 / 外部` の色分離を基準実装にする
- 今回の修正を3製品共通トークン化のたたき台にする

### aio2-main

- すでにシェル品質が高いので、共通トークン名への寄せを先に行う
- `Sora + Noto Sans JP` の基準実装として扱う
- ヒーロー、チップ、カード角丸、CTA を他2製品の基準にする

### notecode

- 情報量が多いので、共通シェルの上で編集体験だけを個性として残す
- `Work Sans` 依存を弱め、見出しだけでも `Sora` に寄せる
- ステップUI、補助設定、出力カードの階層差を共通仕様へ揃える

## Rollout Order

1. 共通デザイントークンを確定する
2. 3製品のナビ、背景、カード、ボタンを同じトークン名へ置換する
3. フォントを `Sora + Noto Sans JP` に揃える
4. バッジ、ステップ、Expansion、テーブルヘッダの文法を揃える
5. グラフと状態色のルールを揃える
6. 最後に製品固有のワークエリア差分だけを残す

## Acceptance Criteria

- 3画面を並べたとき、3秒以内に同一 SaaS 群だと分かる
- CTA、見出し、ナビ、カード角丸、背景グラデーションが共通に見える
- `成功 / 比較 / リスク` の色意味が3製品で一致する
- 主役カードと補助カードの見分けが製品横断で同じになる
- 各製品の個性は、色ではなくワークフローと情報構造で表現される

## Immediate Next Step

最初の実装対象は `kotomegane` で行った semantic color 分離を、`aio2-main` と `notecode` の `:root` トークンとカード階層へ移植すること。  
その後にフォントとナビ構造を合わせると、最短で「同じプロダクト群」に見える。

2026-04-01 の次アクション:
- `aio2-main`: `Sora + Noto Sans JP`、`--brand / --self / --competitive / --external`、`card-primary / card-secondary / card-detail` の導入
- `notecode`: `Work Sans` 依存を落としつつ、同一 token 名とカード階層へ置換
- 追加で、保存済み draft / compare UI は `card-detail + summary-eyebrow + mini-stat + compact table` の共通文法として持ち込む
