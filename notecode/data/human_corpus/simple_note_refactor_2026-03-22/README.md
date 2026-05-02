# simple_note_refactor_2026-03-22 human corpus

Phase 02 の human corpus / learner foundation package。

## Scope

- human corpus の source rule と split rule を固定する
- first-track の target 120 件を article type 別に追跡する
- bootstrap learner calibration を corpus 本体と分離して置く

## Source Rule

- allowed:
  - rights-cleared internal human-written note/blog/newsletter
  - contractually reusable human-written client/public content
  - editor-reviewed Japanese long-form posts with source owner trace
- excluded:
  - AI生成または AI下書き依存が強い本文
  - 権利確認ができない外部テキスト
  - 機密や個人情報を含む本文
  - プロンプトや system 指示が混ざったログ本文

## Split Rule

- split unit は document 単位
- source owner / series 単位で group split する
- first track は `train 70 / dev 15 / holdout 15`
- article type ごとに stratified する

## Bootstrap Rule

- `learner_calibration_bootstrap.json` は learner callable 化のための bootstrap artifact
- bootstrap rows は target 120 件に算入しない
- corpus 由来データは prompt 制御へ直接流さず、feature extraction と learner inference に限定する
