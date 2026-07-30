# USER_TRIAL_RUNBOOK

Date: 2026-04-27 JST

## Purpose

この runbook は、current mainline をユーザーが最初に試すための手順です。

最初の試行は最大 3 種類に限定します。

1. `announcement`
2. `comparative_review`
3. `company_introduction`

この runbook では product code、prompt、しきい値、画像生成設定、品質判定、UI 実装は変更しません。

## Start

1. `C:\tetie\techie-hub\start.bat` を実行する。
2. ブラウザで HUB を開く。
   - `http://127.0.0.1:8090/`
3. コトメイクを開く。
   - `http://127.0.0.1:8080/`
4. 画面の反映が古い場合だけ、次を実行してから開き直す。
   - `C:\tetie\techie-hub\start.bat force`

## First Trial Order

### 1. announcement

最初に試す。

Source input should include:

- 変更内容
- 実施日時
- 対象ユーザーまたは対象範囲
- 旧手順や旧仕様の扱い
- 事前準備
- 当日の確認事項
- できれば、主な告知 source 1 件と FAQ / checklist source 1 件

Good source examples:

- 仕様変更のお知らせ
- メンテナンス告知
- 新機能公開のお知らせ
- 価格や提供条件の変更告知。ただし価格は source に明記がある場合だけ

### 2. comparative_review

2 番目に試す。結果は review warning 付きで確認する。

Source input should include:

- 比較する 2-3 候補
- 共通の評価軸
- 候補ごとの差分
- それぞれが向く条件
- 注意点や tradeoff
- 次に確認すべき順番
- 価格、プラン、成果、優位性を書く場合は source に明記があること

Good source examples:

- 2-3 サービスの公式説明
- 自社の選定メモ
- 比較表
- 導入前チェックリスト

### 3. company_introduction

3 番目に試す。`limited user trial OK with review awareness` として扱う。

Source grounding weak reflection は最新 artifact で解消済みです。ただし、自社視点の弱さと repair rejection は残っているため、停止ではなく記録しながら確認します。

Source input should include:

- 現在の事業内容
- 顧客が相談する入口や困りごと
- 支援範囲
- 進め方や対応プロセス
- 相談前に判断できる材料
- 任意で、実績や事例の証拠。ただし source にある範囲だけ

Avoid source made only of:

- 沿革
- 代表挨拶
- 理念
- 抽象的な強み
- 会社の姿勢だけを説明した文章

Review awareness points:

- 自社視点として自然か。
- 第三者紹介調が強すぎないか。
- タイトルが読者を引くか。
- 画像コピーが記事に合うか。
- source 外 claim がないか。

## How To Judge The Result

### Success

成功として扱う条件:

- 記事本文が表示される。
- タイトル、リード、本文、ハッシュタグが確認できる。
- コピーまたは保存に進める。
- source にない価格、実績、保証、比較優位が足されていない。
- 記事本文や画面の通常表示に内部検査用の言葉が出ていない。
- 画像生成が成功しているか、画像だけの警告として扱われている。

### Review Warning

次は記事成功として扱い、手動確認してよい。

- 本文が表示され、確認・修正して使える状態。
- 「要確認」相当の表示があるが、本文は空ではない。
- source が薄い、または確認推奨の警告がある。
- 画像の片方だけが失敗している。
- `review_required_draft`。
- repair warning / `repair_required` / `repair_rejected`。
- voice weakness。
- title weakness。

Review warning のときに確認すること:

- source 外の断定がないか。
- 価格、成果、ランキング、保証、法務判断が勝手に足されていないか。
- 見出しや本文が source の主題から外れていないか。
- `company_introduction` では、自社視点として自然か、第三者紹介調が強すぎないか、タイトルが読者を引くか、画像コピーが記事に合うかを確認する。
- `comparative_review` では、根拠なしに勝者を決めていないか。

### Input Block

入力不足として扱う条件:

- source が不足していると分かる表示が出る。
- 本文が出ず、入力を足す必要がある。
- `product_introduction` または `daily_story` を試して、source 追加が必要だと分かる。

Input block のときは、同じ入力で繰り返さない。source を足すか、今回の first trial から外す。

### Stop And Report

次のどれかが出たら停止して報告する。

- 記事本文が空。
- source にない価格、成果、保証、受賞、顧客名、比較優位が書かれている。
- 法務判断、保証、確実な成果のような断定がある。
- UI/server failure が発生する。
- `blocked_output_redacted=true` が出る。
- 画像生成の失敗で、記事本文まで失敗扱いになる。
- `case_study` で保証やステルス性のある legal warning が出る。
- 次のような内部検査用の言葉が、本文または通常画面に出る。
  - `SYS_*`
  - `source_grounding`
  - `contract_alignment`
  - `must_cover`
  - `PATCH_SCOPE`
  - `SEMANTIC_LEDGER`
  - `SECTION_SHADOW`
  - `persona`
  - `trial`
  - `hidden`
  - `blocked_output_redacted=true`

## Image Check

画像生成は、記事生成が成功した後に自動で始まる。

確認すること:

- 記事プレビューの後に画像パネルが表示される。
- `文字入り画像` と `文字なし画像` の 2 枠を確認する。
- 片方だけ失敗しても、記事本文が使えるなら記事成功は止めない。
- 両方失敗しても、記事本文が成功しているなら画像だけの失敗として記録する。
- 画像失敗が記事失敗へ変わった場合は停止して報告する。

最初の画像確認対象:

1. `announcement`
2. `comparative_review`
3. `company_introduction`

`company_introduction` では、画像コピーが記事の支援範囲や相談入口に合っているか、source 以上の断定になっていないかを確認する。

## Do Not Use These Sources

最初の user trial では使わない。

- source なしの企業紹介
- 沿革、理念、代表挨拶だけの企業紹介
- 価格や成果が source にない比較記事
- ランキングだけを要求する比較記事
- 実績、受賞、顧客名を推測させる source
- 法務判断、保証、医療、金融、投資判断を断定させる source
- 口コミや第三者評価だけで構成された source
- 非公開情報、個人情報、機密情報
- 著作権上そのまま転載できない長文 source
- 今回の対象外 article type の source

## Hold Article Types

今回の first trial では試さない。

- `case_study`
- non-company `branding` values stance

これらは成功 / 失敗の切り分けが first trial には向かないため、別 package または別 smoke で扱う。

## Source Needed Article Types

今回の first trial では主対象にしない。

- `product_introduction`
- `daily_story`

試す場合は、まず source を作り直す。

`product_introduction` needs:

- 何の製品 / サービスか
- 使う場面
- 対象ユーザー
- 機能や支援範囲
- 導入前後の確認点
- 価格や成果を書く場合は source-backed

`daily_story` needs:

- 実際に起きた場面
- 誰が何に困ったか
- 会話や判断のずれ
- その後に変えた行動
- source なしの抽象的な日記にしない

## Artifacts To Save When Reporting

エラー、停止、警告を報告するときは、可能な範囲で次を保存・共有する。

- 試した article type
- 入力した source の種類と件数
- 画面に表示された状態
- 表示された記事本文
- 画像パネルの状態
- 失敗した variant が `文字入り画像` か `文字なし画像` か
- `company_introduction` の voice / title / image-copy / source-claim review notes
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\app.log`
- 画像生成ログがある場合:
  - `C:\tetie\notecode\logs\gpt_image2_blog_image_auto_2026-04-22\`
- 画面のスクリーンショット
- 発生時刻

## Result Record Template

```text
Date:
Tester:
Article type:
Source count:
Source summary:

Result:
- success / review warning / input block / stop

Article:
- title visible:
- lead visible:
- body visible:
- hashtags visible:
- company intro self-perspective natural:
- third-party explanatory tone too strong:
- title attracts reader:
- source outside claim observed:
- legal / guarantee concern:
- internal wording visible:

Image:
- with text: success / warning / failed / not checked
- without text: success / warning / failed / not checked
- image copy fits article:
- image issue blocks article success: yes / no

Artifacts:
- latest_generation_output.txt saved: yes / no
- latest_generation_output.json saved: yes / no
- latest_generation_quality_report.json saved: yes / no
- app.log excerpt saved: yes / no
- screenshot saved: yes / no

Notes:
```
