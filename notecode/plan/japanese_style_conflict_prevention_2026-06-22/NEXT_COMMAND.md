# Next Command: external_japanese_style_reference_inventory

Paste the following into a separate work window.

```text
C:\Users\横山裕明\Documents\実行環境準備完了\tetie の notecode で、proposal / non-current package:

C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\plan\japanese_style_conflict_prevention_2026-06-22\

の次owner `external_japanese_style_reference_inventory` を実施してください。

参照ルール:
1. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\AGENTS.md
2. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\AGENTS.md
3. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\AGENTS.md
4. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\CURRENT_ALGORITHM.md
5. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\PIPELINE_SPEC.md
6. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\CONFIG_AND_PERSONA_POLICY.md
7. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\JAPANESE_STYLE_POLICY.md
8. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\JAPANESE_STYLOMETRY_POLICY.md
9. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\0506\docs\AI_CODING_RULES.md
10. C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\plan\japanese_style_conflict_prevention_2026-06-22\README.md

外部参照:
- https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d

目的:
- Gistを現行アルゴリズムやprompt本文にしない。
- Gist由来の規範を、採用候補 / 不採用 / 現行と重複 / 衝突リスク に棚卸しする。
- `body_length_floor_chars`、depth-budget contract、source-grounding、genre naturalness、prompt compactness と衝突しない形だけを候補に残す。

作成する成果物:
- C:\Users\横山裕明\Documents\実行環境準備完了\tetie\notecode\plan\japanese_style_conflict_prevention_2026-06-22\INVENTORY.md

INVENTORY.md に必ず入れる:
- Status: proposal / non-current
- Current owner preserved: draft_writer_depth_budget_contract_smoke_failure_diagnosis
- External reference boundary
- Current source-of-truth boundary
- Overlap table
- Gap table
- Non-adopted table
- Collision-risk table
- Candidate home table: draft writer / style editor / structural editor / japanese quality checker / targeted rewriter
- Recommended next owner

禁止:
- product code を変更しない。
- prompt template を変更しない。
- AGENTS.md / WORKLOG.md を変更しない。
- API validation を実行しない。
- Route A fallback、writer-only fallback、old repair loop、raw full source_documents pass を戻さない。
- QA threshold / repair acceptance を緩めない。
- Gist全文を転載しない。
- broad prompt tuning を提案しない。

完了報告形式:
decision: inventory_completed | blocked_by_doc_conflict
artifact:
current_owner_preserved: true/false
product_code_changed: false
api_used: false
route_a_fallback_used: false
writer_only_fallback_used: false
raw_full_source_documents_passed: false
threshold_relaxed: false
repair_acceptance_relaxed: false
prompt_bloat: none | found
module_bloat: none | found
recommended_next_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

