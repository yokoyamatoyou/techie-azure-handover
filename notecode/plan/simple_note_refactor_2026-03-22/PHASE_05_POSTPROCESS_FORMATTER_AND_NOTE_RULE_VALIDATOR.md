# PHASE 05 POSTPROCESS FORMATTER AND NOTE RULE VALIDATOR

状態: pending  
目的: note 向け整形と rule check を deterministic layer に寄せる

## In Scope

- tagged output parse
- note formatter
- `## 目次` rule validator
- deterministic local edit

## Out Of Scope

- native note TOC 連携
- full rewrite pass

## Planned Outputs

- `C:\tetie\notecode\note\simple_note_pipeline\postprocess.py`
- formatter / validator tests

## Tasks

1. parser を抽出する
2. formatter を抽出する
3. `## 目次` validator を追加する
4. deterministic local edit を先行適用にする
5. note rule check を必須化する

## Mandatory Rule Check

- `## 目次` は条件を満たすときだけ出す
- TOC 項目と `##` 見出しが一致する
- `BODY` に title や hashtags を混ぜない
- 箇条書きや番号付きリストが暴れていない
- paragraph break が note 貼り付けで崩れにくい

## Self-Test

- functional
  - parse / normalize / validator が通る
- prompt injection / policy
  - formatter が prompt 由来 text を危険に増幅しない
- anti-bloat
  - note rule を prompt に戻していない
- readability / owner boundary
  - parse / format / validate / local edit の役割が分かれている

## Exit Criteria

- `## 目次` rule check が必須
- validator fail 時の動作が説明できる
- full rewrite path が存在しない

## Retry Rule

- validator false positive / false negative は 2 回まで修正
- 2 回で安定しなければ blocked にして report
