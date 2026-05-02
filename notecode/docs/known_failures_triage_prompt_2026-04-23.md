# known failures triage prompt 2026-04-23

この prompt は別ウインドウ開始用。前 window の `explanatory_article` fingerprint bounded repair 差分とは分離して、既知の別件失敗 3 件を triage / 修正する。

## 目的

- まず既知失敗 3 件を個別再現し、原因 owner を分ける。
- 1 failure = 1 narrow hypothesis = 1 owner scope で扱う。
- 修正が 1 file / 1 route に閉じない場合は、実装前に小さい計画を作る。

## 最初に読む

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\WORKLOG.md`
  - `2026-04-23 追記（notecode explanatory fingerprint bounded repair activation）`
  - 既知の別件失敗 / 残リスク
- `C:\tetie\notecode\docs\known_failures_triage_prompt_2026-04-23.md`
- 必要に応じて:
  - `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`

## 現在の前提

- 直前 window で `explanatory_article` / `adaptive` / long single source / uncorrected fingerprint flags の bounded repair activation は実装済み。
- その差分は戻さない。
- current mainline path は維持する:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- guard 閾値を下げない。
- blacklist / cleanup を増やさない。
- prompt 肥大化を避ける。
- completed / frozen planning package は reopen しない。

## 既知失敗

### 1. comparative_review fixture success false

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py::test_st05ab10_ui_short_comparative_axis_lock_fixture_uses_specific_fit_carry_for_caution -q
```

Symptom:

- expected: `result["success"] is True`
- actual: `False`

Priority:

- highest
- 既存 8 記事タイプ維持に関わるため、まずここから見る。

Triage focus:

- `comparative_review` / short / UI fixture / axis lock / caution carry
- output guard block なのか input stop なのか、reason code と diagnostics を先に確認する。
- comparative source contract / axis lock / caution carry のどれが false success を起こしているかを分ける。

### 2. branding experimental prompt stack uncovered source summary

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_experimental_prompt_stack_support_keeps_uncovered_branding_source_summary -q
```

Symptom:

- expected prompt contains:
  - `[summary] 運用見直し方針:`
- actual prompt does not contain that summary.

Priority:

- second
- experimental path だが、source packet / uncovered source summary の欠落なので source grounding 系の品質に近い。

Triage focus:

- `build_experimental_prompt_stack_from_contract`
- support prompt の source summary retention
- grounding item に入っていない source document を support prompt から落としていないか
- ただし本文 runtime の source contract や explanatory fingerprint repair へ波及させない。

### 3. industry_analysis title expectation drift

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt -q
```

Symptom:

- expected title:
  - `市場の前提と論点から考える業界の見方`
- actual title:
  - `市場の前提と構造変化から整理する業界の見方`

Priority:

- third
- 仕様判断が先。actual が prompt echo ではなく許容表現なら test expectation update も候補。prompt echo regression なら title shaping を狭く直す。

Triage focus:

- `format_output`
- industry_analysis title shaping
- prompt echo guard
- `must_cover` の利用が title を過度に topic へ寄せていないか

## 作業計画

### Phase 0: reproduce and classify

- 3 件を個別に再現する。
- 各失敗について、reason code / diagnostics / generated title or prompt snippet を記録する。
- ここで owner file が 1 つに絞れない、または複数 route をまたぐなら、実装前に `C:\tetie\WORKLOG.md` に小計画を書いて止める。

### Phase 1: comparative_review first

- `success=False` の直接原因を特定する。
- guard 閾値を下げず、比較記事固有の source contract / axis lock / caution carry のどれか 1 つに owner を絞る。
- focused test を通す。

### Phase 2: branding experimental prompt stack

- uncovered source summary が support prompt から落ちる原因を直す。
- experimental prompt stack の support prompt retention に限定する。
- focused test を通す。

### Phase 3: industry_analysis title shaping

- actual title が仕様として許容か、prompt echo regression かを判断する。
- 仕様変更なら test expectation の理由を WORKLOG に残す。
- runtime 修正なら title shaping の narrow patch に閉じる。

### Phase 4: regression

最低限:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py::test_st05ab10_ui_short_comparative_axis_lock_fixture_uses_specific_fit_carry_for_caution note\tests\test_simple_note_pipeline.py::test_experimental_prompt_stack_support_keeps_uncovered_branding_source_summary note\tests\test_newalgorithm_phase03_pipeline.py::test_st08b4_industry_analysis_title_and_lead_do_not_echo_prompt -q
```

今回の前 window 差分を壊していない確認:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py::test_explanatory_fingerprint_repair_promotes_uncorrected_flatness_to_patch_scope note\tests\test_simple_note_pipeline.py::test_explanatory_fingerprint_repair_keeps_scope_narrow note\tests\test_simple_note_pipeline.py::test_explanatory_fingerprint_repair_rejects_noop_patch -q
```

shared:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

可能なら:

```powershell
.\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
.\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -q
```

## 成功条件

- 既知失敗 3 件が pass する、または 1 件ずつ原因と stop reason が明確に記録される。
- explanatory fingerprint bounded repair の focused tests が維持される。
- `source_grounding` を弱いまま通す変更をしない。
- 既存 8 記事タイプを壊さない。
- AGENTS / WORKLOG update need を final report に含める。

## 停止条件

- 1 failure の修正が 2 route 以上へ広がる。
- guard 閾値変更や cleanup 増殖でしか通せない。
- current mainline path を変えないと通せない。
- 3 回同一 phase で修正しても通らない。

停止時は、該当 failure、試した仮説、変更ファイル、残る diagnostics、次の最小 owner scope を `C:\tetie\WORKLOG.md` に記録して報告する。
