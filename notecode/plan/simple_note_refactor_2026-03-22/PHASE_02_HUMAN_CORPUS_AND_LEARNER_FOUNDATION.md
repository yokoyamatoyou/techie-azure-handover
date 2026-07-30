# PHASE 02 HUMAN CORPUS AND LEARNER FOUNDATION

状態: pending  
目的: AIっぽさ判定を human corpus と learner の両輪にする

## In Scope

- human corpus の source rule 固定
- corpus manifest の作成
- feature extraction の初期版
- learner 初期版の導入

## Out Of Scope

- visible UI 変更
- full semantic guard
- LightGBM への拡張

## Locked Inputs

- learner 初期モデル: `RandomForest`
- first-track corpus target:
  - `announcement`: 30
  - `branding`: 40
  - `daily_story`: 20
  - `explanatory_article`: 30

## Planned Outputs

- `C:\tetie\notecode\data\human_corpus\simple_note_refactor_2026-03-22\README.md`
- `C:\tetie\notecode\data\human_corpus\simple_note_refactor_2026-03-22\manifest.json`
- `C:\tetie\notecode\note\simple_note_pipeline\style_learner.py`
- learner calibration artifact

## Tasks

1. corpus source / split rule を決める
2. article type 別 manifest を作る
3. first feature set を実装する
4. learner inference API を作る
5. `AIIndex` へ learner 出力を接続する準備をする

## Self-Test

- functional
  - manifest と learner inference が再現可能
- prompt injection / policy
  - corpus 由来データを prompt 制御へ直接流していない
- anti-bloat
  - learner 周りが runtime mainline にベタ書きされていない
- readability / owner boundary
  - corpus logic と runtime generation logic が分離されている

## Exit Criteria

- corpus source rule が fixed
- learner inference が callable
- target 120 件の充足状況が PROGRESS で読める

## Retry Rule

- manifest / learner が壊れたら 2 回まで修正
- 2 回で安定しなければ blocked にして report
