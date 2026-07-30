# Route A Legacy Opt-out Deprecation Notice

作成日: 2026-05-12
対象: `C:\tetie\notecode`

## User Notice

Route 0506 は、現在の UI 本文生成 default route です。

`NOTECODE_UI_BODY_ROUTE=route_a` は、deprecated legacy opt-out としてだけ残します。通常利用・新規検証・SaaS 運用の既定値には使わず、Route A の挙動そのものを確認する narrow rollback / forensics / compatibility check のときだけ明示的に使います。

Route 0506 が blocked / error / source 不足で止まった場合も、Route A へ自動 fallback しません。その場合は Route 0506 の fail-closed 結果を維持し、該当する Route 0506 owner で原因を切り分けます。

## Operator Notice

Default behavior:

```text
blank NOTECODE_UI_BODY_ROUTE -> route_0506_structured_blog_ui_v1
NOTECODE_UI_BODY_ROUTE=route_a -> deprecated legacy Route A opt-out
Route 0506 blocked/error -> blocked state, no Route A fallback
```

運用 guidance:

- Route 0506 を UI 本文生成の main route として扱う。
- 通常 launcher、`.env`、SaaS 運用 default に `NOTECODE_UI_BODY_ROUTE=route_a` を入れない。
- Route A は、作業 window が Route A forensics / rollback owner を明示した場合だけ使う。
- current owner が明示許可しない限り、Route A 再生成、Route A fallback 追加、Route A 比較を行わない。
- category 05/07 の source contract block は Route 0506 の source-readiness 問題であり、Route A へ黙って切り替える理由にしない。

## Current Runtime Boundary

Runtime behavior is unchanged by this notice.

- Route A deletion: false
- Route A opt-out behavior changed: false
- Route A fallback added: false
- Route A regenerated: false
- Route 0506 generation logic changed: false

## Next Removal Work

この notice は削除開始ではありません。削除や deeper deprecation implementation は、runtime / docs / tests / env examples / rollback expectations を棚卸しする別 owner で扱います。
