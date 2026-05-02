# GPT-5.4 移行検討：コスト・性能とシンプル化の方向性

最終更新: 2026-03-07  
対象: `C:\tetie\notecode`（コトメイク）  
参照: OpenAI Pricing, GPT-5.4 Prompt Guidance, AGENTS.md §5

## 1. GPT-5.4 のコスト（2026年3月時点）

### 公式価格（Standard Tier, コンテキスト < 272K tokens）

| 項目 | 単価（1M tokens あたり） |
|------|---------------------------|
| **Input** | $2.50 |
| **Cached input** | $0.25（90% 割引） |
| **Output** | $15.00 |

- コンテキストが 272K を超えると Input 2倍・Output 1.5倍。
- コンテキスト窓: 最大約 1M tokens（GPT-5.2 の 400K から拡大）。
- GPT-5.2 比で Input +43%、Output +7% の値上げ（TokenCost 等の比較記事による）。

### 現行モデル（GPT-4.1-mini）との比較

| モデル | Input（1M tokens） | Output（1M tokens） | 1ドルあたり Output |
|--------|--------------------|---------------------|---------------------|
| **GPT-5.4** | $2.50 | $15.00 | 約 66,667 tokens |
| **GPT-4.1-mini** | $0.40 | $1.60 | 約 625,000 tokens |

- **Output は GPT-5.4 の方が約 9.4 倍高い**（トークン単価ベース）。
- Input は約 6.25 倍高い。
- 同じトークン数で比較すると、全面 GPT-5.4 化はコスト増が大きい。

---

## 2. GPT-5.4 の性能・公式の言及

- **トークン効率**: GPT-5.2 より「少ないトークンで問題を解く」設計（Tool search で 47% 削減の事例あり）。
- **指示・文体の維持**: "Strong personality and tone adherence, with less drift over long answers"（長文でもトーンが崩れにくい）。
- **出力の制御**: "Instruction adherence in modular, skill-based prompts when **the contract is explicit**"（出力契約をはっきり書くと従いやすい）。
- **推論レベル**: `reasoning_effort`: low / medium / high で速度と複雑さを切り替え可能。

### プロンプト設計の公式ガイド（要約）

- **まずは最小プロンプト**: "Start with the smallest prompt that passes your evaluations and only add complexity when fixing measured failure modes."
- **明示的な出力契約**: 出力形式・セクション・長さをはっきり書く。
- **簡潔で構造化**: "Prefer concise, information-dense writing." / "Apply length limits only to the section they are intended for."
- **冗長な説明より契約**: 長い説明を足すより、output contract を明確にする方が効く。

→ **「性能がかなり違うので、プロンプトと後段をシンプルにできる」という仮説が公式の説明と整合する。**

---

## 3. コストを抑えつつシンプル化する方向性

### A. モデル使い分け（ハイブリッド）

- **負荷の大きいタスクだけ GPT-5.4**: 談話計画（discourse plan）、セクション本文生成。
- **軽いタスクは現行のまま**: タイトル・リード・ハッシュタグ・ペルソナ/オーディエンス補完などは GPT-4.1-mini のまま。
- `config.json` の `task_models` でタスク別にモデルを指定可能（現状は未使用）。例:
  - `section` / `outline` 系 → `gpt-5.4`（または API 上の正式名）
  - `title` / `lead` / `hashtags` / `persona` / `audience` → 従来モデル

これで「高い出力トークン」をセクション生成に限定し、呼び出し回数の多い軽いタスクは安いモデルのままにできる。

### B. プロンプトのシンプル化（GPT-5.4 の強みを活かす）

- **Tier B / ルールの重複削減**: 同じ制約が複数箇所（Tier B、core_guide、セクション【ルール】）に入っている場合は、**output_contract に集約**し、1か所で明示する形に寄せる。
- **短い肯定形の維持**: すでに zero_base_v2 で「短い肯定形」を方針にしているため、GPT-5.4 向けにも「禁止列挙より、やること・出力形式・長さ」を短く書くスタイルを続ける。
- **長大なプロンプトの見直し**: 評価で通る最小の長さにし、失敗モードが計測されたときだけブロックを足す（公式ガイドに沿う）。

→ プロンプトが短くなれば **Input トークン削減** になり、GPT-5.4 の高単価を少しでも相殺できる。

### C. 後段処理・品質パイプラインの整理

- **人間らしさ・トーンの維持**: GPT-5.4 は「トーンドリフトが少ない」とされているため、**Human Resonance / quality_pipeline の phase の一部を shadow または off にできる可能性**がある。
- **段階的な検証**: まず `quality_pipeline.mode: shadow` で GPT-5.4 のみの出力を計測し、`flat_zone_count` / `semantic_issue_count` / 主観評価が悪化しなければ、enforce の適用範囲を減らす（例: phase01/02 は shadow のまま、phase05/06 だけ enforce）。
- **minimal postprocess の維持**: ALGORITHM の方針どおり、後処理は「メタ除去・整形・最小限の文法補修」に留め、重い LLM 多重補正は足さない。

→ **「モデルが賢いので、後段のルールを減らす」** ことで、コードと設定のシンプル化と、実行時コスト・レイテンシの削減の両方を狙える。

### D. reasoning_effort の選択（GPT-5.4 公式仕様）

[Using GPT-5.4](https://developers.openai.com/api/docs/guides/latest-model/) によると:

- **`temperature` / `top_p` / `logprobs` は、reasoning effort が `none` のときのみサポート**される。`low` 以上を指定したリクエストにこれらを含めると API がエラーを返す。
- GPT-5.2 以降のデフォルトは `reasoning.effort: "none"`。推論を増やしたい場合は `low` → `medium` → `high` → `xhigh` と上げる。
- `none` のときは「プロンプトで考えさせる」ことが推奨されている（例: 答える前にステップを書かせる）。

**notecode での使い分け:**

| タスク | reasoning_effort | 理由 |
|--------|-------------------|------|
| **セクション本文・リード・記事本体** | **`none`** | temperature (0.8–1.1) で人間らしい揺らぎを出すため。`none` でないと temperature を送れない。 |
| **アウトライン解析・契約解決・検証・法務チェック** | **`low`**（任意） | 揺らぎは不要で、少し推論が欲しい場合。このときは temperature を送らないよう `task_type` 別に制御する必要あり。 |

→ **結論: 5.4 にするなら、本文生成は `none`、それ以外は `none` のままでもよいし、`low` を試すなら task_models と同様に `reasoning_effort` をタスク別に渡す実装にする。** 現状は config で 1 つの `reasoning_effort` のみなので、まずは **全体を `none` で GPT-5.4 に切り替え**（temperature が効く）、必要なら後で「推論が必要なタスクだけ low」を検討するのが安全。

---

## 4. 移行時の確認項目（チェックリスト）

- [ ] **API モデル名**: 実際のエンドポイント名（例: `gpt-5.4` / `gpt-5.4-pro`）を OpenAI ドキュメントで確認し、`config.json` の `model_name` / `task_models` に反映する。
- [ ] **temperature / top_p**: GPT-5 系は `disable_temperature_model_prefixes` / `disable_top_p_model_prefixes` に `gpt-5` が含まれているため、GPT-5.4 でも送信制御が働く。必要なら `gpt-5.4` を明示的に追加する。
- [ ] **reasoning_effort / verbosity**: `llm_client.py` はすでに `reasoning_effort` と `verbosity` を渡せる。GPT-5.4 用に `verbosity` で簡潔出力を指定すると、Output トークン削減に繋がる可能性がある（公式の verbosity_controls に沿う）。
- [ ] **コスト監視**: `core/token_tracker.py` や PoC の CSV 出力で、モデル別・タスク別のトークン数とコストを記録し、GPT-4.1-mini 単体との差分を把握する。
- [ ] **品質の維持**: `latest_generation_output.json` / `generation_audit_log.jsonl` / `latest_generation_quality_report.json` で、契約整合・semantic_dedupe・品質指標が悪化していないか確認する。

**カテゴリ別パラメータ（GPT-5.4 相談結果）**: 解説／ストーリー／ブランド／お知らせごとの temperature・verbosity・presence_penalty の取り込み案は `docs/gpt54_consultation_category_params.md` にまとめた。

---

## 5. 参照リンク（検索日 2026-03-07）

- **Using GPT-5.4（reasoning / temperature 互換の正本）**: https://developers.openai.com/api/docs/guides/latest-model/
- OpenAI Pricing: https://openai.com/api/pricing/
- GPT-5.4 Model (API): https://developers.openai.com/api/docs/models/gpt-5.4
- Prompt guidance for GPT-5.4: https://developers.openai.com/api/docs/guides/prompt-guidance/
- Introducing GPT-5.4: https://openai.com/index/introducing-gpt-5-4/
- TokenCost GPT-5.4: https://tokencost.ankitaglawe.com/blog/openai-gpt-5-4-pricing-benchmarks-review
- GPT-4.1 vs GPT-5 (price comparison): https://pricepertoken.com/compare/openai-gpt-4-1-vs-openai-gpt-5

---

## 6. まとめ

| 観点 | 要点 |
|------|------|
| **コスト** | GPT-5.4 は GPT-4.1-mini より Output 約 9 倍・Input 約 6 倍高い。全面切り替えはコスト増が大きい。 |
| **性能** | トークン効率・指示遵守・トーン維持が強く、「明示的な出力契約」でより少ないプロンプトで制御しやすい。 |
| **シンプル化** | (1) プロンプトの短縮と output_contract 集約、(2) 後段の品質 phase の一部 shadow/off 化、(3) タスク別モデル使い分けで、コストを抑えつつシンプルにできる余地がある。 |
| **次のステップ** | API モデル名の確定 → `task_models` で section/outline のみ GPT-5.4 を試す → コスト・品質を計測 → プロンプト削減と quality_pipeline の縮小を検討。 |

AGENTS/WORKLOG 更新の要否: 本ドキュメントは notecode 内の検討メモ。パラメータやモデルを実際に変更した時点で `generation_parameter_tuning_log.md`（現物がなければ作成）や WORKLOG に変更を記録する。
