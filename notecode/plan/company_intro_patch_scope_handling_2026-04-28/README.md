# company_intro_patch_scope_handling_2026-04-28 README

## Objective

`company_introduction` repair で original draft の `LEAD` や見出し名に route drift phrase が入った場合だけ、patch path が悪い導線語を保持し続ける問題を docs-only で設計整理する。

対象 symptom は、`相談の入口` / `相談前` などが original draft / raw source-derived material から入り、repair prompt の patch scope と `pipeline.py` 側 acceptance が `LEAD` / heading stability を要求するため、repair candidate が route drift phrase を温存するケースである。

## Background

- 直前診断 artifact:
  - `C:\tetie\notecode\logs\company_intro_repair_prompt_assembly_20260428-112438\`
- 診断分類:
  - `B + D mixed`
  - `D`: original draft / raw source-derived material に route drift phrase が既に入っていた
  - `B`: repair prompt surface と patch-scope acceptance が `LEAD` / heading name を保持するため、route drift phrase が sticky になる
  - not `C`: public `company_introduction_source_contract` material は clean
  - not `E`: repair candidate は clean ではなく、`repair_acceptance.py` を触る根拠はない
- current algorithm:
  - `single-pass + optional single repair 1回`
  - repair は局所修復であり、別記事 rewrite ではない
  - output は常に `[TITLE] / [LEAD] / [BODY] / [HASHTAGS]` を含む全文 tagged article
  - `SEMANTIC_LEDGER` / `SECTION_SHADOW` / `PATCH_SCOPE` の anchor を維持する

## Why Docs-Only

この問題は prompt wording だけで閉じない。`prompt_builder.py` の patch-scope prompt は `LEAD` / heading name preservation を明示し、`pipeline.py` 側も patch path active 時に同じ surface stability を acceptance boundary にしている。

そのため、prompt だけを変えると candidate が変わっても acceptance で落ちる可能性があり、acceptance だけを変えると prompt が bad surface を保持し続ける。product code に入る前に、どの条件で lead / heading 変更を許すかを owner-local に固定する必要がある。

## Current Blocker

現行 patch scope では、次の理由で lead / heading の route drift を直せない。

- `prompt_builder.py` の company-intro surface patch lines が `TITLE / LEAD / HASHTAGS` と heading names を一字一句保持するよう要求する
- `pipeline.py` の `_repair_preserves_flagged_scope()` と `_repair_preserves_local_patch_scope()` が repaired draft の `lead` と heading list の変更を reject する
- flagged spans は section body / fingerprint flatness 側に寄りやすく、bad phrase が `LEAD` または heading name にあると repair target の外側として扱われる
- route drift phrase の除去だけを目的に source-backed information まで落とすと、会社紹介としての現在事業 / 製品サービス / 対応範囲が痩せる

## Non-Goals

- product code 変更
- UI server 起動
- generation rerun
- pytest 実行
- repair 回数追加
- fingerprint / quality / source grounding threshold 緩和
- source外 claim 許容
- `相談の入口` の単語禁止だけでの対症療法
- body 全体 rewrite
- `repair_acceptance.py` 先行変更
- `prompt_builder.py` への長文 accretion
- `pipeline.py` への大きな条件分岐 accretion
- article-type fixed routing table 追加

## Owner Boundary

次 implementation owner は 1 つに固定する。

- owner:
  - `company_intro patch-scope helper`
- product code scope candidate:
  - new helper: `C:\tetie\notecode\note\simple_note_pipeline\company_intro_patch_scope.py`
  - minimal hook: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - minimal prompt surface replacement only if needed: `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - tests: `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- owner rule:
  - `pipeline.py` に直接条件を積まない
  - helper が detection / allowed surface / acceptance precondition を持つ
  - `pipeline.py` は existing patch hook から helper 判定を呼ぶだけにする
  - `prompt_builder.py` は helper と同じ条件で既存の keep wording を narrow replacement するだけにし、長文 block を足さない
  - `repair_acceptance.py` は clean candidate が出てから検討する

## Success Criteria

- `company_introduction` かつ route drift phrase が lead / affected heading にある場合だけ、patch scope を lead / affected heading へ最小拡張できる設計になっている
- 拡張対象は lead と affected heading のみで、body 全体 rewrite にしない
- accept 条件が明示されている
  - source grounding が悪化しない
  - output guard / internal leakage が green
  - body が空でない
  - hard source contract を破らない
  - current business / product-service / support scope が残る
  - source-backed な問い合わせ窓口への短い自然な言及は許す
  - 会社紹介の主軸を相談導線へ戻す candidate は reject
- reject 条件が明示されている
  - route phrase を消すために source-backed business material を落とす
  - lead / heading 変更が unflagged section へ波及する
  - heading を相談導線・導入手順・問い合わせ誘導中心に改名する
  - source外 claim / unsupported result / price / customer / award / superiority を足す
  - internal/runtime terms を visible output / UI に出す
  - fingerprint / grounding / source contract / quality thresholds を緩めないと通らない

