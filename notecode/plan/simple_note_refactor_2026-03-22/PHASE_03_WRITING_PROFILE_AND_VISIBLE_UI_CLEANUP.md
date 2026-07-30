# PHASE 03 WRITING PROFILE AND VISIBLE UI CLEANUP

状態: pending  
目的: raw UI 値を compact writing profile に圧縮し、visible UI を最小追加で整理する

## In Scope

- `writing_profile` resolver
- branding subtype/focus の visible control
- free text と pattern select の役割整理
- question flow の再利用方針固定

## Out Of Scope

- prompt 長文化
- UI の大改修
- brand architecture の独立 visible control

## Locked UI Direction

- free text は残す
- pattern select は追加してよい
- branding visible controls:
  - subtype: `company / product / service`
  - focus:
    - `まず知ってもらう`
    - `違いを伝える`
    - `選ぶ基準を作る`
    - `新しい見方を作る`
- question flow は unresolved slot 補完に限定する

## Planned Outputs

- `C:\tetie\notecode\note\simple_note_pipeline\profile_resolver.py`
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`

## Tasks

1. `content_goal / writing_focus / perspective / tone / relationship_mode` を profile に寄せる
2. branding subtype / focus を conditional UI に追加する
3. よくある指示 pattern select を追加する
4. free text のままでも動く fallback を残す
5. question flow を次の unresolved slot に限定する
   - audience
   - core message
   - branding focus
   - 差別化根拠
   - commodity angle
   - category naming

## Self-Test

- functional
  - profile 差分が生成差分に出る
- prompt injection / policy
  - free text を増やしても prompt accretion していない
- anti-bloat
  - visible UI が選択肢過多になっていない
- readability / owner boundary
  - UI shell と profile resolver の責務が分かれている

## Exit Criteria

- raw UI field 直読みが減っている
- branding visible control が最小追加で反映されている
- free text / pattern select / question flow の役割分担が fixed

## Retry Rule

- UI 混線や contract mismatch は 2 回まで修正
- 2 回で解消しなければ blocked にして report
