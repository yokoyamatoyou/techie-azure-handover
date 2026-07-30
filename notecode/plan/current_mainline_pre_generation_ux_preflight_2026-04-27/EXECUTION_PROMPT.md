# EXECUTION_PROMPT

Use this only for the Phase 1 implementation window. Phase 2 / Phase 3 must remain separate work.

```text
C:\tetie\notecode の current mainline launch UX blocker Phase 1 だけを実装する。
最初に prompt_builder.py が hash 4F29076F... の failed naturalness prompt surface 状態なら、82DC095B... baseline へ rollback する。company_intro_source_contract*.py の launch-blocker accepted 変更は保持する。
その後、journey UI の確認ボタンと生成ボタンを分離する。確認ボタンは URL取得・入力状態・記事条件確認だけを行い、run_generation を呼ばない。生成は明示ボタン「この内容で生成を開始」だけで起動する。run_generation は未確認/stale signature を自動 confirm せず停止する。
Phase 2 source preflight と Phase 3 repair trigger は実装しない。
prompt_builder.py へ禁止語・few-shot・追加 prompt を積まない。repair回数、threshold、target_chars、length_mode、pipeline behavior は変えない。
確認は URL 4件保持、確認クリックで Generation started なし、生成クリックだけ Generation started あり、8080 listener 維持まで行う。
```

## Implemented Notes

- Exact `82DC095B...` file artifact was not found in this workspace, so the failed prompt surface was manually rolled back according to WORKLOG.
- Phase 1 UI separation has been implemented in this package.
- Phase 2 source preflight and Phase 3 repair trigger remain pending.
