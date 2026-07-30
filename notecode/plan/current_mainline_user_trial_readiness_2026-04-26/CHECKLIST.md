# CHECKLIST

Date: 2026-04-27 JST

## Before Trial

- [ ] `C:\tetie\techie-hub\start.bat` で起動した
- [ ] HUB `http://127.0.0.1:8090/` を開いた
- [ ] コトメイク `http://127.0.0.1:8080/` を開いた
- [ ] first trial は最大 3 種類に限定する
- [ ] full-flow rerun や追加検証を目的にしない

## Trial Targets

- [ ] 1. `announcement`
- [ ] 2. `comparative_review`
- [ ] 3. `company_introduction`
- [ ] `company_introduction` は review awareness として扱う

## Source Check

### announcement

- [ ] 変更内容がある
- [ ] 実施日時がある
- [ ] 対象者または対象範囲がある
- [ ] 旧手順の扱いがある
- [ ] 事前準備がある
- [ ] 当日の確認事項がある

### comparative_review

- [ ] 2-3 候補がある
- [ ] 共通評価軸がある
- [ ] 候補ごとの差分がある
- [ ] 向く条件がある
- [ ] 注意点や tradeoff がある
- [ ] 次の確認順がある
- [ ] 価格 / プラン / 成果 / 優位性は source にある場合だけ使う

### company_introduction

- [ ] 現在の事業内容がある
- [ ] 顧客の入口や困りごとがある
- [ ] 支援範囲がある
- [ ] 進め方や対応プロセスがある
- [ ] 相談前の判断材料がある
- [ ] 沿革 / 代表挨拶 / 理念だけの source ではない

## Result Check

- [ ] 記事本文が表示された
- [ ] タイトル、リード、本文、ハッシュタグが確認できた
- [ ] source 外の価格、成果、保証、受賞、顧客名、比較優位がない
- [ ] 法務判断や保証の断定がない
- [ ] 通常画面や本文に内部検査用の言葉が出ていない
- [ ] `company_introduction` は自社視点として自然か確認した
- [ ] `company_introduction` は第三者紹介調が強すぎないか確認した
- [ ] `company_introduction` はタイトルが読者を引くか確認した
- [ ] `company_introduction` は画像コピーが記事に合うか確認した
- [ ] `company_introduction` は source 外 claim がないか確認した

## Record-Only Conditions

出ても停止せず、結果に記録する。

- [ ] `review_required_draft`
- [ ] repair warning / `repair_required` / `repair_rejected`
- [ ] voice weakness
- [ ] title weakness

## Image Check

- [ ] 記事成功後に画像パネルが表示された
- [ ] `文字入り画像` を確認した
- [ ] `文字なし画像` を確認した
- [ ] 片方 variant の失敗だけで記事成功が止まっていない
- [ ] 画像失敗が記事失敗へ変わっていない

## Stop Conditions

出たら停止して報告する。

- [ ] 記事本文が空
- [ ] source 外 claim がある
- [ ] 法務判断、保証、確実な成果の断定がある
- [ ] UI/server failure がある
- [ ] 画像失敗が記事成功を止めた
- [ ] `case_study` の保証 / legal warning が出た
- [ ] `SYS_*`
- [ ] `source_grounding`
- [ ] `contract_alignment`
- [ ] `must_cover`
- [ ] `PATCH_SCOPE`
- [ ] `SEMANTIC_LEDGER`
- [ ] `SECTION_SHADOW`
- [ ] `persona`
- [ ] `trial`
- [ ] `hidden`
- [ ] `blocked_output_redacted=true`

## Do Not Use In First Trial

- [ ] `case_study`
- [ ] non-company `branding` values stance
- [ ] `product_introduction` without stronger source
- [ ] `daily_story` without stronger source
- [ ] source なしの企業紹介
- [ ] 沿革 / 理念 / 代表挨拶だけの企業紹介
- [ ] source にない価格や成果を求める比較記事
- [ ] 機密情報、個人情報、非公開情報

## Report Artifacts

- [ ] article type
- [ ] source summary
- [ ] screen state
- [ ] visible article body
- [ ] image panel state
- [ ] company_intro voice review
- [ ] company_intro title review
- [ ] company_intro image-copy review
- [ ] source-claim review
- [ ] `C:\tetie\notecode\logs\latest_generation_output.txt`
- [ ] `C:\tetie\notecode\logs\latest_generation_output.json`
- [ ] `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- [ ] `C:\tetie\notecode\logs\app.log`
- [ ] screenshot
