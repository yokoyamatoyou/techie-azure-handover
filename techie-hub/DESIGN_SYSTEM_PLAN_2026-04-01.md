# TECHIE Design System Plan 2026-04-01

## Purpose

`techie-hub` を TECHIE 全体の入口とし、`コトメイク` `コトミガキ` `コトメガネ` が
別アプリではなく同一 SaaS 群として見える共通UI原則を固定する。

この文書は `全体共通の正本` とし、各サービスの実装計画はサービス配下の docs に分ける。

## Product Positioning

- `techie-hub`
  - 全サービスへの入口
  - 契約プランに応じて見せるサービスを切り替える
- `コトメイク`
  - 文章生成
- `コトミガキ`
  - 診断と改善提案
- `コトメガネ`
  - AI検索での出現確認と周辺語・外部サイト可視化

## Core Principle

認知負荷を全体的に小さく保ち、機能が異なっても「画面の使い方はなんとなく同じ」にする。

狙う状態:

- 初見で迷わない
- 毎回学び直さなくてよい
- 主役情報と詳細情報の差が一目で分かる
- 契約プランに応じた表示制御が自然にできる

## Design Basis

### Human Factors

- Nielsen 10 Heuristics
- Hick's Law
- recognition over recall
- progressive disclosure
- consistency and standards

### Design Tone

- 入口体験は Google 寄り
  - シンプル
  - 余白
  - 選択肢を絞る
  - 最初に見せる情報は少なく
- 作業画面は Microsoft 寄り
  - 情報構造が明確
  - 実務で追いやすい
  - 状態と履歴を把握しやすい

## Shared Layout Rule

### 1. Common H1

全サービスで H1 領域を共通化する。

- 左: 共通ブランドアイコン
- 中央: サービス名
- 下: 一文の価値訴求
- 補助: 簡潔な説明

共通資産:

- icon: `logo_mark.svg`
- favicon: `favicon_v2.png`

### 2. Common Page Skeleton

各サービスの基本レイアウトは次の3段で揃える。

1. `入力 / 条件`
2. `主結果`
3. `詳細 / 運用`

機能が違っても、この順序は崩さない。

### 3. Card Hierarchy

- `card-primary`
  - その画面で一番見てほしい結論
- `card-secondary`
  - 補足判断
- `card-detail`
  - 履歴、設定、比較、保存済み情報

### 4. Navigation Rule

- 共通H1から他サービスへ遷移可能にする
- ただし同一画面で見せる主操作は絞る
- `詳細運用` は折りたたみや別画面に退避する

## Typography Rule

フォント、見出し階層、本文階層は 3 サービスで共通化する。

### shared typography goals

- どのサービスでも読み方が同じ
- 見出し、項目名、補助文の差が一目で分かる
- 毎回学び直さなくてよい

### shared roles

- `display / H1`
  - サービス名と画面の主題
- `section title`
  - `入力する` `結果を見る` `詳細 / 運用` のような大区分
- `item title`
  - カード名、項目名、表の主要ラベル
- `sub item`
  - 補助ラベル、補足見出し、簡潔な説明
- `body`
  - 通常本文
- `caption`
  - 注記、補足、状態説明

### recommendation

- フォントファミリーは全サービスで統一する
- サイズ、太さ、行間のルールも全サービスで統一する
- 差分はサービスごとに持たず、共通 token として管理する

## Service Identification Rule

共通レイアウトを維持したまま、今どのサービスにいるかは弱い差分で伝える。

### keep common

- H1 構造
- フォント
- 文字サイズ体系
- 余白
- カード形状
- ボタン位置
- 情報の並び順

### allow small difference

- 背景のごく薄い色味
- 主強調色
- サービス名の補助ラベル

### background principle

- 背景差分は `識別できる最小限` に抑える
- 色だけに依存しない
- サービス名とH1でも現在地が分かるようにする
- 状態色とブランド差分色を混ぜない

### suggested service tones

- `コトメガネ`
  - ごく薄いウォームクリーム
- `コトミガキ`
  - ごく薄いサンド / ベージュ
- `コトメイク`
  - ごく薄いアイボリー系

## Information Load Rule

- 最初に見せる主要判断は3つまで
- 入力欄は通常利用の最小構成を先に出す
- 高度な設定は初期表示しない
- テーブルは一覧で判断、詳細は下段で読む
- 英語の内部語は原則UIに出さない

## Plan Gating Rule

料金プランによってサービス表示を制御できるようにする。

### visibility modes

- `visible`
  - 通常表示
- `locked`
  - サービス名は見せるが利用不可表示
- `hidden`
  - 完全非表示

### recommendation

- 認知負荷を下げたい通常プランでは `hidden`
- 上位プラン訴求をしたいときだけ `locked`

## Visual Positioning

`90ドル相当` は実価格ではなく、見た目の印象基準として使う。
入口体験は「複雑な分析スイート」ではなく「迷わず使える業務ツール」に寄せる。

この印象で求めるUX:

- すぐ理解できる
- 学習コストが低い
- 何を見ればよいかが明確
- 手動利用でも価値がある
- 定期運用へ自然につながる
- 安っぽく見えない
- 信頼感がある

## Rollout Order

1. `kotomegane` を共通UIの基準実装にする
2. `techie-hub` で共通H1とサービス表示制御の設計を固める
3. `aio2-main` を同じシェルへ寄せる
4. `notecode` を同じシェルへ寄せる

## Next Session Read Order

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\techie-hub\DESIGN_SYSTEM_PLAN_2026-04-01.md`
3. `C:\tetie\kotomegane\AGENTS.md`
4. `C:\tetie\kotomegane\docs\DESIGN_IMPLEMENTATION_PLAN_2026-04-01.md`
5. `C:\tetie\kotomegane\docs\CURRENT_STATE_2026-03-30.md`
