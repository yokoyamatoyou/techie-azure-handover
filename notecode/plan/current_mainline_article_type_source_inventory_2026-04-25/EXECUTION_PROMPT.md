# current_mainline_article_type_source_inventory_2026-04-25 EXECUTION_PROMPT

Use this prompt for the next normal-mode UI validation window.

```text
C:\tetie\notecode の current mainline UI validation を通常モードで開始してください。

前提:
- product code / prompt / threshold / repair / UI は変更しない。
- 生成前に source inventory の判定を採用する。
- 使用OK source のみ UI品質試験に投入する。
- thin / NG source は smoke 目的以外では使わない。
- case_study は httpbingo/base64 artifact ではなく clean source に差し替えてから実行する。
- daily_story はユーザー提供の日次メモがない場合、synthetic daily fixture と明記して実行する。
- Web candidate URL は取得候補であり、fixture や runtime source へ勝手に書き込まない。

優先実行:
1. company_introduction: Kyoto 4 URLs
2. announcement: existing spec-change fixture
3. explanatory_article: existing misread-metric fixture
4. branding: values/stance fixture
5. product_introduction, case_study, comparative_review, industry_analysis: source差し替え後に実行
6. daily_story: user memo または synthetic daily fixture として実行

禁止:
- 失敗を見て即実装修正しない。
- repair count / threshold / prompt accretion で対症療法しない。
- source不足による短さを runtime 品質劣化として断定しない。
- mojibake / encoded title を含む source を clean case_study source として扱わない。

参照:
- C:\tetie\notecode\plan\current_mainline_article_type_source_inventory_2026-04-25\README.md
- C:\tetie\notecode\plan\current_mainline_article_type_source_inventory_2026-04-25\PROGRESS.md
- C:\tetie\notecode\logs\multi_type_current_mainline_validation_20260425-013935\
- C:\tetie\notecode\logs\source_compression_length_adequacy_20260425-093131\
- C:\tetie\notecode\logs\current_mainline_source_grounding_metric_correction_ui_validation_20260425-214032\
```
