# UI Role Clarity Record 2026-04-08

更新日: 2026-04-08
対象: `C:\tetie\notecode\note\note_writer_app.py`

## Purpose

- UI 上の role / speaker 選択肢が曖昧だと、追従性の高い `gpt-5.4-mini` がその曖昧さをそのまま prompt surface と本文へ持ち込みやすいことを記録する
- `運営側` のような曖昧な立場語を current UI に戻さないため、現行 UI の role 選択肢を固定する
- この記録は naturalness / visible AI feel の再発防止に使い、`AGENTS.md` には詳細を持たせず current package / WORKLOG から参照する

## Historical Finding

- 2026-04-05 backup では company introduction の prompt builder が `speaker = speaker_profile or "運営側"` を採用していた
- 同 backup では `運営側が何を重視してどう支えているか` という wording が company introduction guidance に入っていた
- この形は、会社紹介として自然な主語よりも「役割語そのもの」を本文 surface に押し出しやすく、説明カード調・AI 的なメタ説明を誘発しやすい
- current code では `『運営側』『運営担当として』『広報として見ると』のような役割語を本文に露出させない` guard が追加されている

## Current UI Keep State

### Journey / structure

- canonical UI journey route は 8 分類を keep
- `structure` は UI で選ばせず `auto` 固定

### Semantic role options

- `company_introduction`
  - `自動（おすすめ）`
  - `企業広報として語る`
- `product_introduction`
  - `自動（おすすめ）`
  - `ブランド担当として語る`
  - `導入支援担当として語る`
- `announcement`
  - `自動（おすすめ）`
  - `運営担当として語る`
  - `編集担当として語る`
- `daily_story`
  - `自動（おすすめ）`
  - `現場担当として語る`
  - `編集担当として語る`

### Article-type fallback role options

- `branding`
  - `自動（おすすめ）`
  - `企業広報として語る`
  - `ブランド担当として語る`
  - `導入支援担当として語る`
- `announcement`
  - `自動（おすすめ）`
  - `広報担当として語る`
  - `運営担当として語る`
  - `編集担当として語る`
- `case_study`
  - `自動（おすすめ）`
  - `導入支援担当として語る`
  - `運営担当として語る`
  - `編集担当として語る`

## Interpretation

- `gpt-5.4-mini` は追従性が高いため、UI に曖昧な立場語を置くと、その語を本文の話者・主語・論点の正本として扱いやすい
- その結果、company introduction のような説明系記事では `運営側として` のような不自然な role 語が visible surface に出やすくなる
- したがって、UI 側では「誰として語るか」を semantic ごとに狭く明示し、曖昧な role label を置かないこと自体が品質改善策である

## Rule

- `運営側` のような曖昧 role label を current UI に戻さない
- company introduction では role 語を狭く保ち、`自動（おすすめ）` と `企業広報として語る` を keep する
- UI role 変更を行う場合は、visible quality の変更として current package / WORKLOG に残す
