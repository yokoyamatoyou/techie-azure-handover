# branding prompt compare 2026-04-08

参照ルールファイル: `C:\tetie\AGENTS.md`, `C:\tetie\notecode\AGENTS.md`

## 目的

- branding / company introduction で、`指示を少し詳しくした prompt` が `一発生成の baseline prompt` より自然さを改善するかを live で確認する
- prompt-only で解決できる範囲と、code-side phase が必要な範囲を切り分ける

## 比較条件

- source は固定
  - `https://fixture.techie/branding/company-profile`
  - `https://fixture.techie/branding/support-policy`
- article_type: `branding`
- ui_journey: `introduce/company`
- audience: `導入前に概要を知りたい読者`
- speaker: `企業広報として語る`

## artifact

- baseline + heavy detail compare:
  - `C:\tetie\notecode\logs\custom_prompt_compare\20260408-193425\summary.json`
- balanced detail compare:
  - `C:\tetie\notecode\logs\custom_prompt_compare\20260408-194023\summary.json`

## prompt variants

### 1. baseline

`医療支援SaaS企業の企業紹介。事業内容、選ばれる理由、現場で大切にしている姿勢を、資料に沿って簡潔に伝える`

### 2. heavy detail

`医療支援SaaS企業の会社紹介記事を書いてください。`

`条件:`

- `note向けの日本語記事`
- `一般読者が読んで、事業内容と会社の姿勢が自然に伝わる文章にする`
- `通常の人が書いたような文の流れにし、改行を適度に入れる`
- `一文ごとの長さを揃えすぎない`
- `同じ文末を連続させすぎない`
- `主語は必要な箇所だけに置き、日本語として自然に省略する`
- `AIがよく使う説明口調やテンプレ表現を抑える`
- `抽象論で膨らませず、資料にある事実を軸に書く`
- `宣伝文句に寄せすぎず、日々の運用姿勢が読める会社紹介にする`
- `見出しは4つ前後`
- `冒頭は、導入前に「何を基準にこの会社を見るべきか」が伝わる入り方にする`
- `本文では、事業内容、選ばれる理由、現場で重視している運用姿勢、最後の短いまとめの順に整理する`
- `ソースにない実績、数値、事例は足さない`

### 3. balanced detail

`医療支援SaaS企業の会社紹介記事を書いてください。導入前に概要を知りたい読者向けに、事業内容と導入初期を支える姿勢が自然に伝わる文章にしてください。資料にある事実を軸に、何をしている会社か、なぜ導入初期支援を重視するのか、問い合わせを運用改善へ戻す進め方、最後に読者がどう理解すればよいか、の順で整理してください。宣伝調に寄せすぎず、現場での支え方が見える会社紹介にしてください。文の長さを揃えすぎず、同じ文末を続けすぎず、見出しごとに適度に改行し、ソースにない実績や数値は足さない。`

## 結果

| variant | rubric | human_visible_ai_reason | output_guard soft | quality soft |
|---|---:|---|---:|---:|
| baseline | 8 | flat_or_repetitive | 5 | 7 |
| heavy detail | 8 | flat_or_repetitive | 4 | 8 |
| balanced detail | 8 | flat_or_repetitive | 2 | 6 |

## 読み取り

- heavy detail は `output_guard soft` を 1 つ下げたが、`quality soft` は 1 つ増えた
- heavy detail では `contract:prompt_context_weak_reflection` が追加され、指示の多さがそのまま効くより、contract 側で取りこぼしている
- balanced detail は `output_guard soft` を `5 -> 2`、`quality soft` を `7 -> 6` まで下げた
- ただし 3 変種とも `human_visible_ai_reason = flat_or_repetitive` は残り、rubric は `8` のまま止まった

## 推奨判断

- 採るなら `balanced detail`
- 避けるなら `heavy detail`
- 理由:
  - style 指示を箇条書きで積みすぎるより、`読者 / 事業内容 / 導入初期支援 / 問い合わせ改善 / 最終理解` を一続きの narrative として指定した方が current mainline では安定した
  - それでも `flat_or_repetitive` は消えないため、prompt-only では頭打ち
  - current package の本線は引き続き `Phase 02 Repair Patch Path And Acceptance For Branding` と `Phase 03 Branding Route Ownership Experiment`

## 採用候補 prompt

```text
医療支援SaaS企業の会社紹介記事を書いてください。導入前に概要を知りたい読者向けに、事業内容と導入初期を支える姿勢が自然に伝わる文章にしてください。資料にある事実を軸に、何をしている会社か、なぜ導入初期支援を重視するのか、問い合わせを運用改善へ戻す進め方、最後に読者がどう理解すればよいか、の順で整理してください。宣伝調に寄せすぎず、現場での支え方が見える会社紹介にしてください。文の長さを揃えすぎず、同じ文末を続けすぎず、見出しごとに適度に改行し、ソースにない実績や数値は足さない。
```
