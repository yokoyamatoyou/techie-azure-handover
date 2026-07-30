# autonomous_blog_productization_2026-04-14 VISUAL REVIEW EXECUTION PROMPT

## purpose

- この prompt は `2026-04-14` 時点の code-complete 状態を前提に、別ウインドウで `live acceptance + Codex visual review` だけを実行するためのもの
- 既存 6 phase の実装は完了済みとみなし、default は **コードを書かずに acceptance を進める**
- ただし live 実行中に narrow blocker が出た場合だけ、その blocker owner を最小 diff で修正してよい

## separate-window use

- 別ウインドウ起動後は、このファイルの `prompt` ブロックをそのまま使う
- まず source-of-truth を読み、次に shared checks と live battery を実行し、最後に artifact 視認で verdict を残す
- same failed hypothesis unchanged retry は 3 回まで
- preflight blocked の場合は無理に進めず stop し、blocker と必要条件を report する

## fixed scope

- target package:
  - `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\`
- current keep-state:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- implementation reference:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`
- current code-complete status:
  - `phase06_completed_code_checks_passed`
- live acceptance target cases:
  - source-backed `branding/company_introduction`
  - source-backed `explanatory_article`
  - source-backed `announcement`
  - source-less WEB representative `explanatory_article`

## prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\README.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\TASK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\ROLLBACK.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\VISUAL_REVIEW_EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\README.md
- C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\PROGRESS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の mission:
- code-complete 状態の current mainline に対して、live acceptance battery と Codex visual review を別ウインドウで完走する
- default はコード変更ではなく acceptance 実行
- live preflight が通るなら representative 4 case を short -> promoted long の順で実行する
- artifact を保存し、本文を Codex が視認して `stable pass / unstable pass / unresolved` を判定する
- source-less WEB representative case では `query / url / publisher / exact_date / excerpt` を確認して verdict を付ける

絶対ルール:
- current success path
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  を bypass しない
- `branding/company_introduction` と `announcement` に source-less WEB mode を広げない
- relative date を信用せず exact date で評価する
- preflight blocked のまま live 実行を強行しない
- same failed hypothesis unchanged retry は 3 回まで
- blocker が出たときだけ narrow owner を直す
- blocker 修正後は owner-local tests -> shared checks -> live rerun の順に戻る

開始直後に確認:
1. package docs の read order を確認
2. `C:\tetie\notecode\logs\latest_generation_output.txt`
3. `C:\tetie\notecode\logs\latest_generation_output.json`
4. `C:\tetie\notecode\logs\latest_generation_quality_report.json`
5. `C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\PROGRESS.md` が `phase06_completed_code_checks_passed` であること

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q

artifact root:
- C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\artifacts\visual_review_2026-04-14

short/live battery 実行スクリプト:
```powershell
@'
from pathlib import Path
import json

from note.current_mainline_ui_matrix import UISweepCase, get_short_sweep_cases, run_ui_sweep_cases, build_promoted_long_cases

artifact_root = Path(r"C:\tetie\notecode\plan\autonomous_blog_productization_2026-04-14\artifacts\visual_review_2026-04-14")
artifact_root.mkdir(parents=True, exist_ok=True)

fixed_cases = {case.case_id: case for case in get_short_sweep_cases()}
selected = [
    fixed_cases["ui-short-branding-company-grounded"],
    UISweepCase(
        case_id="ui-short-explanatory-source-backed-acceptance",
        article_type="explanatory_article",
        user_prompt_text="生成AI導入で、利用範囲、運用責任、確認フローをどう切り分けるかを実務担当者向けに整理する",
        audience_profile_input="実務担当者",
        content_goal_key="explain",
        writing_focus_key="analysis",
        tone_profile_key="calm",
        length_mode_key="short",
        speaker_profile_input="解説担当として語る",
        core_message_input="導入前に利用範囲と運用責任の切り分けを判断できるようにする",
        source_values=[
            "https://fixture.techie/acceptance/explanatory/ai-governance-report",
            "https://fixture.techie/acceptance/explanatory/ai-operations-guide",
        ],
        source_documents=[
            {
                "title": "AI導入ガバナンス整理",
                "content": "生成AI導入では、利用目的、入力禁止領域、承認者、日次確認の責任分担を最初に定めるほど運用定着が早い。特に社内利用では、試験導入の段階から対象業務と禁止用途を短く固定し、担当者が判断に迷う分岐を増やしすぎないことが重要である。",
                "locator": "https://fixture.techie/acceptance/explanatory/ai-governance-report",
                "source_type": "url",
            },
            {
                "title": "AI運用フロー解説",
                "content": "実務導入では、利用範囲の定義だけでなく、生成結果の確認者、修正ルール、例外時の連絡先を先に決める必要がある。確認フローを短く固定した組織ほど、試験導入から本運用への移行が滑らかになりやすい。",
                "locator": "https://fixture.techie/acceptance/explanatory/ai-operations-guide",
                "source_type": "url",
            },
        ],
        note="source-backed explanatory acceptance case",
    ),
    fixed_cases["ui-short-announcement-dense-must-cover"],
    fixed_cases["ui-short-web-explanatory-grounded"],
]

short_results = run_ui_sweep_cases(
    selected,
    live=True,
    artifact_dir=artifact_root / "short",
)
(artifact_root / "short_matrix_summary.json").write_text(
    json.dumps(short_results, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

promoted = build_promoted_long_cases(short_results, selected)
promoted_cases = list(promoted.get("promoted_cases") or [])
long_results = {}
if promoted_cases:
    long_results = run_ui_sweep_cases(
        promoted_cases,
        live=True,
        artifact_dir=artifact_root / "long",
    )
    (artifact_root / "long_matrix_summary.json").write_text(
        json.dumps(long_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
else:
    (artifact_root / "long_matrix_summary.json").write_text(
        json.dumps({"promotion_blocked": True, **promoted}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

print("ARTIFACT_ROOT=", artifact_root)
print("SHORT_STATUS=", short_results.get("matrix_status"))
print("SHORT_PREFLIGHT=", (short_results.get("preflight") or {}).get("passed"))
print("PROMOTED_CASE_IDS=", [case.case_id for case in promoted_cases])
'@ | C:\tetie\notecode\.venv\Scripts\python.exe -
```

visual review 読み順:
1. `short_matrix_summary.json`
2. `long_matrix_summary.json`
3. short/long の各 `*.txt`
4. WEB case の `*.json` で `source_trace` と exact date を確認

必須 case:
- source-backed company intro:
  - `ui-short-branding-company-grounded`
- source-backed explanatory:
  - `ui-short-explanatory-source-backed-acceptance`
- source-backed announcement:
  - `ui-short-announcement-dense-must-cover`
- source-less WEB representative:
  - `ui-short-web-explanatory-grounded`

visual verdict rules:
- `stable pass`
  - title / lead が自然で、本文に管理ラベル感がなく、主要段落の運びが安定
  - facts の使い方が自然で、WEB case は exact date と source trace の整合が見える
  - output guard / short gate / long review で重大 blocker がない
- `unstable pass`
  - 概ね成立するが、固さ、反復、段落呼吸、情報配置のどれかに visible wobble が残る
  - ただし unsafe output や trace 欠落はない
- `unresolved`
  - preflight blocked
  - runtime failure
  - output_guard blocked
  - short_gate failure
  - source trace や exact date が崩れる
  - announcement / company intro の safety が視認上も不安定

Codex 視認ポイント:
- company intro:
  - 事業と支え方から入り、沿革先行や brochure 調に崩れていないか
- explanatory:
  - 解説として論点が一本で、 source-backed facts が読み物の流れに入っているか
- announcement:
  - 対象 / 時期 / 確認事項 / 旧設定扱い が混ざらず、安全な案内文か
- WEB representative:
  - dated facts が自然に使われ、`today / recent` の曖昧語へ逃げていないか
  - trace の publisher / exact date / excerpt が artifact と一致するか
- 全 case 共通:
  - title / lead がカード文や管理ラベルに見えないか
  - paragraph breath が均一すぎないか
  - sentence endings が機械反復していないか

blocker handling:
1. preflight blocked なら live run を止める
2. blocker owner を narrow に特定する
3. 同一仮説で最大 3 回まで修正
4. 各修正のたびに owner-local tests -> shared checks -> blocked case rerun
5. 3 回失敗したら rollback して停止し、blocker report を出す

最終 report の必須項目:
- 読んだ source-of-truth
- shared checks の結果
- short/live battery の結果
- promoted long case の結果
- 各 case の artifact path
- 各 case の visual verdict:
  - `stable pass / unstable pass / unresolved`
- WEB case の source trace:
  - query
  - url
  - publisher
  - exact date
  - excerpt
- unresolved risk
- コード変更の有無
- 変更した場合は owner / hypothesis / tests / retry count / rollback要否
```
