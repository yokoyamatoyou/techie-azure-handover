# stepwise three article gate 2026-04-08

参照ルールファイル: `C:\tetie\AGENTS.md`, `C:\tetie\notecode\AGENTS.md`

## 目的

- `1 step = 1 owner-local change` ごとに、live 生成の visible quality を gate する
- current mainline の変更を、一般的な prompt baseline より AI 感が少ないかで判定する
- 3 記事を Codex が目視確認し、blog としての一貫性が崩れた step を次 phase へ進めない

## fixed gate rule

- 各 step 完了ごとに `3 cases × 2 prompt modes` を live 生成する
- prompt mode は以下の 2 つ
  - `generic`
  - `step-optimized`
- 進行条件
  - `step-optimized` が `generic` より target case で AI 感が少ない
  - `step-optimized` が target case で blog としての一貫性を保つ
  - guard case で current success path regression を起こさない
- 進行停止条件
  - target case のいずれかで `generic` より悪化
  - visible な broken output
  - article type fit / grounding / structure のどれかが崩れる

## fixed cases

- target 1
  - `ui-short-branding-company-grounded`
- target 2
  - `ui-short-branding-trust`
- guard
  - `ui-short-case-study-explain`

## prompt modes

### generic

- `ui-short-branding-company-grounded`
  - `医療支援SaaS企業の企業紹介。事業内容、選ばれる理由、現場で大切にしている姿勢を、資料に沿って簡潔に伝える`
- `ui-short-branding-trust`
  - `小規模SaaSの導入初期で、機能の多さより運用の迷いを減らす価値を伝えるブランド記事`
- `ui-short-case-study-explain`
  - `オンボーディング初回設定の案内導線を見直した事例。成功談に寄せすぎず、最初にどこで迷ったか、どう直したか、どの条件で再現できるかを含める`

### step-optimized

- `ui-short-branding-company-grounded`
  - `医療支援SaaS企業の会社紹介記事を書いてください。導入前に概要を知りたい読者向けに、事業内容と導入初期を支える姿勢が自然に伝わる文章にしてください。資料にある事実を軸に、何をしている会社か、なぜ導入初期支援を重視するのか、問い合わせを運用改善へ戻す進め方、最後に読者がどう理解すればよいか、の順で整理してください。宣伝調に寄せすぎず、現場での支え方が見える会社紹介にしてください。文の長さを揃えすぎず、同じ文末を続けすぎず、見出しごとに適度に改行し、ソースにない実績や数値は足さない。`
- `ui-short-branding-trust`
  - `導入初期のブランド記事を書いてください。機能の多さを売り込むより、運用の迷いを減らす価値が自然に伝わる文章にしてください。導入前の担当者が読み、何を支える会社なのか、どの場面で安心感が出るのか、なぜ初期設計が効くのか、最後にどう捉えればよいかの順に整理してください。断定や宣伝調を強めすぎず、文末と段落の運びを揃えすぎず、資料にない実績は足さない。`
- `ui-short-case-study-explain`
  - `オンボーディング導線を見直した事例記事を書いてください。成功談として盛らず、最初にどこで迷いが起きていたか、何をどう直したか、どの条件なら再現しやすいかが自然に読める文章にしてください。説明の順番を無理に整えすぎず、資料にある事実を軸に、改善の前後が見える事例記事にしてください。`

## visible review checklist

- AI 感
  - 文末の連続が目立たないか
  - 抽象名詞の言い換えループになっていないか
  - `整理できます / 理解しやすいです / 〜と見えます` のようなメタ解説口調が増えていないか
- blog 一貫性
  - 冒頭から結びまで同じ対象を語っているか
  - 見出しごとに役割が分かれ、後半が言い換えの連打になっていないか
  - source-grounded な説明が保たれているか
- regression guard
  - empty title/body なし
  - output_guard blocked なし
  - quality hard fail なし

## artifact naming

- root
  - `C:\tetie\notecode\logs\stepwise_three_article_gate\`
- per step
  - `{timestamp}-{step_name}\generic\summary.json`
  - `{timestamp}-{step_name}\optimized\summary.json`

## advancement decision

- `step-optimized` が target 2 本で `generic` より明確に良い
- guard 1 本で visible regression がない
- 上記を満たしたときだけ次の owner-local step へ進む
