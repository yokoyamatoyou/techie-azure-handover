# GPT-5.4mini で「AIっぽさ」を抜く実験設計

GPT-5.4mini の「AIっぽい会社案内文体」は、**プロンプトの不足ではなく、ポストトレーニング由来の構造的アトラクタ**である。Stanford の AxBench (ICML 2025) は、SAE/ReFT などの内部介入よりも**プロンプト設計のほうが文体ステアリングに強い**ことを示しており、API 縛りでも勝ち筋がある。本レポートは、ユーザーが既に失敗させた 5 方式と**機構レベルで異なる**実験案を、2025–2026 年の研究証拠とともに 6 案提示する。最重視はパイプライン提案で、原因診断・評価指標・モデル設定はそれを支える土台として整理した。結論を先に言えば、**(a) `reasoning_effort=minimal`、(b) Generate-then-Structure 反転、(c) 多軸スタイルリランカーによる Best-of-N、(d) シーン起点生成**の 4 つを最初に走らせるのが、根拠強度と実装容易性のバランスで最良である。

---

## 1. 原因診断:なぜ会社案内・教科書調になるのか

「AIっぽさ」は単一原因ではなく、**少なくとも 5 つのメカニズムが加算的に効く過剰決定された現象**である。だから「自然に書いて」と足すだけでは消えない。優先順位をつけて整理する。

### 1.1 ポストトレーニングによるモード崩壊(最有力・確立)

RLHF と SFT は出力分布を「安全で網羅的で構造化された」狭いモードに集約する。Kirk らの基礎研究(2023)以降、Zhang ら *Verbalized Sampling*(arXiv 2510.01171, 2025)、*LLM Output Homogenization is Task Dependent*(2509.21267, 2025)、Sourati らの *Trends in Cognitive Sciences* 論文(2026)が、**創作・ブログ系タスクで特に多様性損失が大きい**ことを実証している。Selective Layer Restoration(2602.06665, 2026)はこの崩壊が特定層に局在することを示しており、機構的に裏付けが強い。**確立**。

### 1.2 報酬モデルのフォーマット・冗長バイアス(確立)

Zhang ら *From Lists to Emojis*(ACL 2025)は、reward model が**箇条書き・太字・絵文字・見出し・「網羅的」回答に強いバイアス**を持ち、**学習データの 1% 未満の汚染でもバイアスが転写される**ことを示した。RM-Bench では SOTA reward model の Hard Acc が 46.6%(ランダム未満)に落ちる。これがユーザーの観察する「歴史/信頼/選ばれる理由/価格」見出し化と総括調の直接的源泉である。**確立**。

### 1.3 推論モデル特有の「構造化成果物」バイアス(早期証拠が強い)

GPT-5/5.2/5.5 のプロンプトガイドは自社で「default to comprehensive, well-structured answer」「deliberate scaffolding」と明記している。*When Thinking Fails*(2505.11423, May 2025)は 15 モデル横断で **CoT が指示追従を一貫して劣化させ、特にスタイル制約に弱い**ことを示した。R²-Write(2026)、*Language Models that Think, Chat Better*(2509.20357)は、推論モデルが open-ended writing で 10–25 ポイント劣化することを定量化している。**つまり「考えてから書く」モードに入った瞬間、ブログではなくレポート構造が生成される**。サム・アルトマン自身が「GPT-5.2 の writing は失敗した」と公に認めており、5.4 系も改善途上。**早期証拠だが多角的に再現**。

### 1.4 In-context レジスタ漏洩(早期証拠)

会社サイト素材を渡した瞬間、モデルは **「実績/選ばれる理由/お客様第一/創業◯年」**といった企業 PR レジスタを ICL で模倣し続ける。Patel ら STYLL(2505.00679, 2025)、*Catch Me If You Can*(2509.14543, 2025)が、**LLM はソース側の register に強く同期する一方で、everyday author の implicit style 模倣には失敗する**ことを示している。ユーザーの失敗 #2(near-raw)が改善せず brochure に張り付くのはこれが理由。

### 1.5 日本語コーパスの企業文書偏重(強い間接証拠/仮説部分あり)

Swallow パイプライン(Okazaki 2024, Llama 3.3 Swallow 2025)が公開している事実:Common Crawl 日本語のうち最終的に残るのは **0.27%**、Educational Classifier で **上位 10%** のみ採用、Gemma-2 で QA 形式に再生成。これは構造的に「企業サイト・IR・公文書・Wikipedia 的レジスタ」を残し、note や個人ブログを捨てる方向のフィルタである。GPT-5 のコーパス組成は非公開だが、産業界の標準パイプラインが同質である以上、**日本語の「個人エッセイ事前分布」が英語より相対的に薄い**ことはほぼ確実視できる。**Swallow は確立、GPT-5 への外挿は仮説**。

### 1.6 シンプトムから機構へのマッピング

| 症状 | 主因 | 副因 |
|---|---|---|
| ですます単調 | 日本語コーパス偏重(1.5) + モード崩壊(1.1) | 説明モード事前分布(1.3) |
| 抽象語・カタカナ語多用 | 企業日本語偏重(1.5) + ソース漏洩(1.4) | 推論モデル冗長バイアス |
| 総括調・教科書調 | 推論プランナーテンプレ(1.3) | RM 網羅性バイアス(1.2) |
| 主語明示しすぎ | 形式日本語レジスタ(1.5) | モード崩壊(1.1) |
| 段落呼吸欠如・低 burstiness | モード崩壊(1.1) | プランナーテンプレ(1.3) |
| 「歴史/信頼/価格」ドリフト | RM「網羅的」バイアス(1.2) + プランナーテンプレ(1.3) | ソース漏洩(1.4) |

**重要な含意**:症状は過剰決定なので、単一介入(プロンプトに語彙を足す、ban list を増やす)では消えない。**少なくとも 2 つの異なる機構を同時に外す介入セット**が必要。

---

## 2. source grounding と自然文体を両立する設計原則

ここから設計案の前提となる原則を 4 つ立てる。これらは、ユーザーの 5 失敗が「同じ機構を別言いで踏み続けていた」ことから逆算した。

**原則 A:構造を「事前」ではなく「事後」に取り出す。** 失敗 #5(article-function plan)がブローシャー化したのは、プランニング自体が RM が好むテンプレートを呼び出すから。OpenReview 2025 の *Does Forcing Structured Output Degrade LLM Creativity?* は **Generate-then-Structure ワークフローで創造性が 17–26% 回復**することを実証している。プランは捨て、自由作文を先に書かせ、メタデータ(タイトル・h2・タグ)は別コールで抽出する。

**原則 B:文体は「描写」ではなく「実演」する。** GPT-5.5 ガイドが明言する通り、5.x 系は「prompts を literal に解釈する」。「自然に」「note風に」と書けば、モデルは "natural-sounding AI prose" を literal に生成する。*Catch Me If You Can*(2509.14543)が示した通り、few-shot でも実装上の限界はあるが、describe より show のほうが常に強い。

**原則 C:編集ループを廃し、サンプリング+選抜に移す。** 失敗 #4(editor pass)も *Talk Isn't Always Cheap*(ICML 2025, 2509.05396)、*Stay Focused*(2502.19559, gpt-5-mini 評価)も同じ知見:**マルチエージェント編集ループは linguistic quality を犠牲にして reasoning を上げる**。編集ではなく N 個生成して選ぶ。

**原則 D:推論モードを切る。** 推論深度が高いほどプランナーテンプレが呼ばれ、ブローシャー構造が再構築される。`reasoning_effort=minimal`(GPT-5)/ `none`(GPT-5.1+)が出発点。Heilig(2025)は逆方向の証拠も示しており(高 effort で文学判断が悪化)、推論を強める方向は捨てるべき。

---

## 3. 次に試すべき実験アルゴリズム案(最重要)

以下 6 案は、すべて**ユーザーの失敗 5 方式と機構レベルで異なる**ことを確認している。優先度順。

### 案 1:Generate-then-Structure 反転(構造の事後抽出)

**何をするか**:writer は **schema・JSON・見出し計画を一切持たず**、ソースと voice 例だけで自由作文を吐く(`response_format` も指定しない)。完成したプロースに対して**第 2 のコール**でタイトル・h2・タグを抽出する。プランは事後派生物。

**既存失敗との違い**:失敗 #5 は plan-then-write、失敗 #1 はソース shaping。本案は逆方向で、**書き手にいかなる構造も先に与えない**。失敗 #4(editor pass)とも違う:プロースは生成後に編集されず、抽出のみされる。

**根拠**:OpenReview 2025 *Does Forcing Structured Output Degrade LLM Creativity?* が Generate-then-Structure ワークフローで 17–26% 創造性回復を実証(**確立**)。Tam ら *Let Me Speak Freely?*(2408.02442)、*The Format Tax*(2604.03616, 2026)が **prompt 上で schema を「描写」するだけでも degrade する**ことを示しており、本案の厳格さ(schema を一切見せない)が必須であることを支持する。

**API 実装可能性**:GPT-5.4mini で**完全に可能**。2 コールのみ、追加コスト微小。

**最初の owner scope**:writer 用の system prompt から JSON / schema / 「以下の構成で書いてください」型の指示を全削除し、メタデータ抽出は別コールに分離する。3 日で実装可能。

**失敗判定基準**:30 サンプルでブラインド評価し、**ブローシャー的見出し(歴史・信頼・選ばれる理由・価格)が 25% 以上の本文に出現**したら reject。または **段落長分散がベースラインを上回らなければ** reject。

---

### 案 2:`reasoning_effort=minimal` + 多軸スタイルリランカーによる Best-of-N

**何をするか**:GPT-5.4mini を `reasoning_effort=minimal`、`verbosity=medium` で **N=8–16 並列**生成(seed と微小プロンプト摂動でのみ多様化)。**編集は一切せず**、各候補を 6 軸の確定的スコアで採点して 1 つ選ぶ。スコア軸は:(a) 文末エントロピー、(b) 文長分散・burstiness、(c) 漢語率(jReadability 公式)、(d) GPT-ism n-gram penalty、(e) ソース grounding(NLI / 埋め込み)、(f) note 参照コーパスへの埋め込み距離(Ruri-v3-310m)。残り N-1 は破棄。

**既存失敗との違い**:失敗 #4 は編集、本案は**選抜のみ**。失敗 #5 は単一サンプルの計画依存、本案は**多サンプルの分布依存**。reranker 自体が確定的スコアなので、LLM 編集の副作用(本文短縮・見出し崩し)が原理的に発生しない。

**根拠**:Suzgun ら *Prompt-and-Rerank*(2205.11503)が TST における selection-only アプローチの有効性を確立。Meta DivPO(2501.18101, 2025)は **rarity ベース選抜が多様性を 45–75% 取り戻す**ことを示す(訓練ベースだが概念は推論時に転用可能)。Stanford *AxBench*(2501.17148, ICML 2025 spotlight)は活性化ステアリング系を全否定し「**ただしくプロンプトを工夫し選抜するほうが強い**」と結論。文末エントロピーの根拠は Zaitsu ら PLOS ONE 2025(99.8% で人間/LLM 弁別)の language-specific 特徴量。

**API 実装可能性**:**完全に可能**。並列推論 + オフライン採点。GPT-5.4mini の単価ではコストも許容範囲。

**最初の owner scope**:採点関数 v0 をまず文末エントロピー(M4)+ 文長分散(M12)+ GPT-ism 定型句カウント(M16)の 3 軸だけで作る。MeCab/Sudachi のみで実装可能、半日。

**失敗判定基準**:選抜後の top-1 が、ランダム選抜 baseline と比較して**ブラインド人手評価で有意に勝てない**(p>0.1, n=30)場合 reject。または **N=16 でも top-1 が依然として全候補で文末エントロピー < 1.5** なら採点軸ではなく**生成側の温存問題**として再設計。

---

### 案 3:シーン起点生成(Scene-anchored, 機能プランの代替)

**何をするか**:失敗 #5 の article-function plan(歴史・信頼・選ばれる理由)を、**3–5 個の具体的シーン/瞬間/逸話**(顧客との実際のやり取り、開発者の火曜朝の苛立ち、創業時の特定の決断)へ置き換える。各段落は 1 シーンに紐づき、ソース事実はシーン内に grounding される。**抽象的「機能」ではなく具体的「場面」を計画単位とする**。

**既存失敗との違い**:失敗 #5 はトピック/機能ベースのプラン、本案は narrative event ベース。これは **RM が好む「網羅的解説」テンプレートを呼ばない**。失敗 #3(self-perspective)は人称を変えただけで構造が会社プロフィールのまま残ったが、本案は構造単位そのものをミクロ叙述に置換する。

**根拠**:*Beyond Outlining: Heterogeneous Recursive Planning*(2503.08275, Mar 2025)は flat outline がテンプレート化するため動的分解を推奨。Long-form narrative literature(WritingPath, NAACL Industry 2025)は scene/event ベース計画が trope-y にならないことを示唆。**早期証拠だが理論的には強い**。

**API 実装可能性**:完全に可能。プランを「scene + ソース事実紐付け」に書き換えるだけ。

**最初の owner scope**:既存の plan-then-write パイプラインの「機能 JSON」を「3–5 個のシーン箇条書き(各 50 字)」に差し替え、書き手にはシーンと紐付くソース facts をペアで渡す。

**失敗判定基準**:生成本文が依然として **「〜について解説します」「〜は重要です」「以上のように」**型の総括述語で 5 段落以上を占めたら reject。または scene が抽象化されて結局 generic profile に戻ったら reject。

---

### 案 4:対比型 In-Context Learning(明示的 negative example)

**何をするか**:プロンプトに **(a) 目標 voice の note 例 1 本、(b) 「これは BAD: 会社案内ブローシャー」とラベル付けした反例 1 本、(c) ソース素材**を並べ、「**BAD 例と表面的に最大限異なる文体で、ソースに grounding しながら書け**」と指示。生成後、BAD 例とのコサイン類似度が高い候補は rejection sampling で破棄。

**既存失敗との違い**:失敗 #5 は「何を書くか」に向かう計画、本案は「何を書かないか」から逃げる prompt。失敗 #4 は editor 役を立てたが、本案は generation 時点で対比を組み込む(後処理ではない)。

**根拠**:CICL(*Customizing LM Responses with Contrastive ICL*, 2401.17390)が positive+negative few-shot の有効性を示す(早期証拠)。Sanchez ら *Stay on Topic with Classifier-Free Guidance*(2306.17806, ICLR 2024)は negative prompt が text 領域でも効くことを実証(API では logit 操作不可だが、prompt-only で近似)。SynDec(2505.12821, 2025)も類似の思想。**早期証拠**。

**API 実装可能性**:完全に可能。注意点として GPT-5.x は instruction を literal に取るので、BAD 例にラベルを明示する必要がある(「以下は望ましくない例です」)。

**最初の owner scope**:既存の few-shot プロンプトに BAD 例 1 本(明らかな会社案内文)+ ラベルを追加する単独実験。1 日で AB 比較可能。

**失敗判定基準**:対比の効果が **ブローシャー定型句出現率を 30% 以上削減できなければ** reject。または BAD 例のフレーズを直接コピーする regression が起きたら reject。

---

### 案 5:Voice-first / Fact-second 二段生成

**何をするか**:**Stage 1**:題材の 1 文要約だけを与え、ソース素材を**渡さず**、note 例の voice で 100–150 字の voice sample を書かせる。Stage 2:**生成された voice sample + 全ソース**を渡し、「この voice をそのまま継続しつつ、これらの事実を織り込め」と指示。Voice が content より先に固定される。

**既存失敗との違い**:失敗 #2 は near-raw source が voice より先に入るためブローシャーレジスタが ICL される。本案は**逆順:voice を先に lock してから事実を入れる**。失敗 #3(self-perspective)は人称指示だが、本案はモデル自身が生成した voice を anchor にする(self-generated demonstration)。

**根拠**:1.4 節の register leakage 知見の裏返し。ICL が register に強く同期するなら、**最初に晒すコンテキストの register を変えれば**生成全体が同期する。直接の論文検証は限定的(speculative-to-early)。Persona drift 文献(Li 2402.10962, 2024;Stable Personas 2601.22812, 2026)は voice の途中減衰を警告するため、**Stage 2 の冒頭で voice sample を再注入する**運用が必要。

**API 実装可能性**:完全に可能。2 コールのみ。

**最初の owner scope**:既存パイプラインの先頭に Voice Sample 生成ステージを 1 つ挟むだけ。

**失敗判定基準**:Stage 2 で voice sample の文末分布・漢語率が **30% 以上ドリフト**してブローシャー寄りに戻ったら reject。または voice sample 自体が AI っぽければ Stage 1 のプロンプト設計に戻る。

---

### 案 6:文末分布パラメトリック強制 + Rejection Sampling

**何をするか**:目標分布(例:です/ます 35%、体言止め 15%、〜のだ系 15%、〜と思う/気がする 系 10%、その他 25%)を事前に決め、生成後に MeCab/Sudachi で実分布を計測。**目標と KL > 閾値なら破棄して再サンプル**(編集はしない)。N 回まで再サンプルしてだめなら諦める。

**既存失敗との違い**:失敗 #4 は局所編集、本案は**分布ターゲット rejection sampling**。編集ループに入らないので本文短縮や見出し崩しの副作用がない。

**根拠**:Speculative だが、Zaitsu ら(PLOS ONE 2025)の Japanese stylometry が **語尾(文末)を人間が最も強く識別する特徴**として挙げている(survey 回答 n=18 で最頻)。Burstiness 文献(GPTZero, Pangram 2025)とも整合。**仮説段階だが症状直撃**。

**API 実装可能性**:完全に可能。形態素解析 + N サンプリング。

**最初の owner scope**:文末分布計測関数を MeCab で実装(半日)、案 2 の reranker の 1 軸として組み込む形で先行検証してから rejection 化。

**失敗判定基準**:目標分布に到達してもブラインド評価で「自然さ」が改善しなかった場合(=文末は症状であって原因ではない)、reject して案 2/3 に戻る。

---

### 採用順序の推奨(根拠強度順)

| 順 | 案 | 根拠強度 | 実装工数 | 期待改善 |
|---|---|---|---|---|
| 1 | 案 1(Generate-then-Structure) | 確立 | 小 | 大 |
| 2 | パラメータ刷新(`reasoning_effort=minimal`) | 強い間接 | 極小 | 中–大 |
| 3 | 案 2(Best-of-N + 多軸 reranker) | 構成要素は確立 | 中 | 大 |
| 4 | 案 3(Scene-anchored) | 早期証拠 | 小 | 中 |
| 5 | 案 4(Contrastive ICL) | 早期証拠 | 極小 | 中 |
| 6 | 案 5(Voice-first) | 仮説 | 小 | 中 |
| 7 | 案 6(文末 rejection) | 仮説 | 中 | 小–中 |

**合わせ技推奨**:案 1 + パラメータ刷新 + 案 3 を**まずベースラインとして同時に投入**(機構が独立)、その上に案 2 の reranker を被せる。これで 3 つの異なるメカニズムを同時にオフできる。

---

## 4. 日本語スタイロメトリ評価指標

実験を進めるには、ブローシャー化の**症状を定量化する**指標群が要る。以下 7 つの懸念ごとに、計算可能な指標と日本語 NLP 2024–2026 の根拠を示す。すべて **MeCab/Sudachi/GiNZA** で実装可能。

### 4.1 主語省略の自然さ

**M1 ProDrop Rate**:GiNZA/KNP で各述語のガ格項が同一文内に明示されているかを判定。`ProDropRate = #zero_ga / #predicates`。ネイティブエッセイは **50–70%** が省略、AI ブローシャーは 60–80% が明示(逆転)。**確立**(NAIST Text Corpus / Konno EMNLP 2021)。

**M2 項省略判断**:Kubota ら ANLP 2025(Tohoku/Riken)の判断フレームワークが、reader perspective での 5 質問形式で 93% アノテーション一致を達成。**実験的だがフレームワーク公開済み**。

### 4.2 文末分布

**M4 文末形エントロピー**:UniDic で文末 1–3 形態素を抽出、10 クラス(です/ます/だ/である/体言止め/〜のだ/〜だろう/疑問/命令/その他)に分類し Shannon entropy。ネイティブブログ **H ≈ 1.8–2.4 nats**、AI 単調系 H ≈ 0.7–1.2。Zaitsu PLOS ONE 2025 の人間判定根拠でも語尾は最強の特徴。**実験的だが計算は単純**。

**M5 ですます連続最大ラン長 / 体言止め率(M6)**:5 文以上の連続ですますは AI 兆候。体言止め率はネイティブ note で 5–15%、AI で 0–2%。

### 4.3 接続語の頻度・種類

**M7-M8 接続詞密度・HHI**:GiNZA POS=`CCONJ`/`SCONJ` + 文頭接続詞ルール。AI は「また/さらに/そのため/これにより/つまり」に集中。Herfindahl HHI でトップ 3 接続詞が **70% 以上**を占めれば AI 兆候。

### 4.4 抽象語密度

**M9 漢語率**:UniDic の語種(goshu)タグから直接算出。jReadability 公式で係数 −0.126(2 番目に大きい難度寄与)。新聞社説 35–45%、note エッセイ 18–28%、AI 解説 40%+。**確立**(jReadability、柴崎 readability lab)。

**M10 動詞率 / M11 和語動詞率**:サ変動詞(実施する/向上する)率が高いほどブローシャー。和語動詞(やる/上げる/いく)率がネイティブで 2–4 倍。

### 4.5 段落呼吸

**M12 文長分散・burstiness**:Goh-Barabási の `B = (σ−μ)/(σ+μ)`。AI は B<−0.3、ネイティブは +0.1–+0.4。**確立**(GPTZero, Pangram Multilingual v2 が日本語にも対応)。

**M14 Fast-DetectGPT / Binoculars 日本語版**:scorer に PLaMo-1B、observer に llm-jp-3-1.8B を組み合わせて curvature を算出。**閾値要キャリブレーション**だが実装可能。

### 4.6 AIっぽさ

**M15 Zaitsu 3 特徴量**(PLOS ONE 2025、最重要):機能語 unigram + POS bigram + CaboCha 句パターン + JS divergence + Random Forest。**99.8% で人間/7 LLM を弁別**。データ公開済み。**確立**。これを評価指標化すれば、ブローシャー判定の確定的スコアが手に入る。

**M16 GPT-ism 定型句カウンタ**:`〜と言えるでしょう / 〜が重要です / まとめると / 〜について解説します / これにより / 〜と考えられます / いかがでしたか / ではないでしょうか / 〜ことができます`。EQ-Bench Slop Score の日本語版を自前で作る運用。**業界経験則(実験的)**。

**M18 pfgen-bench**(Preferred Networks):n-gram ベース流暢性、確定的、judge LLM 不要。**確立**だがブログでなく QA 設計のため補助指標扱い。

**M19 PFN Comparative LLM-as-Judge**(2026 年 2 月、Preferred Networks Tech Blog):**reasoning judge(GPT-5.1-Thinking 等)で参照テキストとペアワイズ比較**するプロトコル。non-reasoning judge は日本語不自然さを過小評価することが報告されている。

### 4.7 noteブログらしさ

**M20 埋め込み距離(Ruri-v3-310m / GLuCoSE-base-ja-v2)**:500–2000 本のネイティブ note エッセイで centroid μ・共分散 Σ を作り、生成テキストとの cos / Mahalanobis 距離。**実験的だがツーリングは確立**(JMTEB v2、Ruri SOTA)。

**M21 MATTR / MTLD**:Sudachi mode A 固定で測定(モードで結果が大きく変わる点は flag)。AI は MATTR が一貫して低い。

### 4.8 評価指標運用の注意

**Judge LLM の自己選好問題**:GPT-4/5 を judge にすると AI 文体を選好する(Heilig 2025、PFN 2026)。**reasoning judge またはペアワイズ比較プロンプト**を必ず使う。最終判定はネイティブ人手評価のみが信頼できる。

**Zaitsu の 99.8% は 660 字公的コメント**なので、note 長文ブログでは再キャリブレーション要。機能語 unigram は分布が変わる可能性、句パターン特徴は転移しやすい。

**指標の組合せ運用**:Shaib ら ACL/IJCNLP 2025 demo は「単一指標は信頼できない、suite で運用せよ」と勧告。**最低限 M4 + M9 + M12 + M15 + M20 の 5 軸スコアカード**を毎実験で出すのが推奨。

---

## 5. GPT-5.4mini API 設定推奨

GPT-5.4mini は推論モデル系列(2026 年 3 月 17 日リリース)で、**`temperature` / `top_p` / `presence_penalty` / `frequency_penalty` / `logprobs` / `logit_bias` / `n` を一切受け付けない**。HTTP 400 を返す。これは伝統的な単調回避テクニックがすべて使えないことを意味する。少ない knob を以下のように使う。

| パラメータ | 推奨初期値 | 比較すべき値 | 根拠 |
|---|---|---|---|
| `reasoning_effort` | `minimal` または `none` | `low` / `medium` | 高 effort で構造化バイアス増(Heilig 2025、When Thinking Fails 2025、OpenAI 5.5 ガイド明文) |
| `verbosity` | `medium` | `low`(短くなりすぎ注意)/ `high`(冗長 padding 増) | OpenAI ドキュメント、Shumer 2025 |
| API 種別 | **Responses API** | Chat Completions | OpenAI 公式が GPT-5 系に Responses API を強く推奨 |
| `seed` | 固定(再現性) | — | Beta、best-effort |
| `previous_response_id` | セクション間でチェーン | — | persona 安定化(Persona drift 対策) |
| 比較アーム | **`gpt-5-chat-latest`(非推論、temperature サポート)** を必ず併走 | — | 非推論モデルはブローシャー化が弱い可能性 |

**プロンプト設計指針**(OpenAI 自社ドキュメント+Heilig+Shumer から導出):

(1) **「自然な」「人間らしい」「note風に」を直接書かない**。GPT-5.x は literal に解釈し、"natural-sounding AI prose" を生成する。代わりに具体的な傾向(文末分布、漢語率の上限、特定の禁則表現)で記述する。

(2) **Persona ブロックは task instructions と分離**。OpenAI の 2026 年 1 月 *Prompt Personalities* cookbook の通り、persona は「どう響くか」だけ書き、「何をすべきか」と混ぜない。

(3) **few-shot demonstration が最大レバー**。Catch Me If You Can の限界を踏まえても、describe より show のほうが常に強い。**目標 voice の note 記事 1–2 本を全文埋め込む**。

(4) **schema を prompt で「描写」しない**。Format Tax(2604.03616, 2026)が示す通り、schema を prompt に書くだけで degrade する。構造が必要な場合は Structured Outputs API を別コールで使う。

(5) **アクノウレッジメント抑制**(GPT-5.1 ガイド推奨):「got it」「了解しました」「以下に記述します」型の前置きを禁止する instruction を入れる。

---

## 6. 結論と novel insight

ユーザーが 5 方式で失敗してきたのは、**それらが同じ機構(モデルにより多くの構造を与える)を別言いで踏み続けていたから**である。本研究の最大の含意は、解決方向がその逆——**与える構造を減らし、生成後に選抜する**——であることが、2025–2026 年の post-training 多様性研究、format bias 研究、structured output creativity 研究によって独立に支持されている点である。

特筆すべき非自明な発見が 4 つある。第一に、**Stanford AxBench が SAE/活性化ステアリングを実質否定し、プロンプト+選抜が最強と結論した**こと。これは「クローズド API では何もできない」という思い込みを破る。第二に、**サム・アルトマンが GPT-5.2 の writing 失敗を公式に認めており、5.4 系も coding 改善優先で writing は副次的**だった事実(Smith Stephen 2026)。これは GPT-5.4mini で「AIっぽさ」が抜けないことが**ユーザー側の設計問題ではなくモデル側の既知の構造的問題**であることを示す。第三に、**`reasoning_effort=minimal` への変更だけで挙動が大きく変わる可能性があり、しかも一行修正**で済む(ユーザーがまだ試していない可能性が高い、最も低工数で最も期待値の高い介入)。第四に、**Zaitsu ら PLOS ONE 2025 が日本語特化の AI 検出を 99.8% で成立させた**ため、ブローシャー化の症状を**確定的スコア**として直接最適化対象にできる時代に入った——「AIっぽい」がもはや主観ではない。

最初の 2 週間で走らせるべき実験は 3 本に絞れる:**(α)** 既存 Route A をそのままに `reasoning_effort=minimal` だけ変えた arm、**(β)** 案 1(Generate-then-Structure)+ 案 3(Scene-anchored)を組み合わせた新パイプライン、**(γ)** 案 2 の Best-of-N + 5 軸 reranker(M4/M9/M12/M15/M20)を β に被せた arm。評価は Zaitsu RF スコア + ネイティブ盲検評価(n=30)で、α が中、β が大、γ が β+α を上回るというのが本レポートの予測である。もし γ でも改善が頭打ちなら、原因は post-training 構造により深く食い込んでおり、**`gpt-5-chat-latest`(非推論)併走** または **小型日本語 OSS モデルとの asymmetric draft/verify**(案外、本レポートで言及した Pipeline 2 系統)に進むのが筋となる。

---

## 7. 主要参考文献(2025–2026 中心)

**ポストトレーニングの多様性損失と原因診断**
- Zhang et al., *Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity*, arXiv:2510.01171, 2025
- *Not All Layers Need Tuning: Selective Layer Restoration Recovers Diversity*, arXiv:2602.06665, 2026
- Sourati, Ziabari, Dehghani, *The Homogenizing Effect of LLMs*, Trends in Cognitive Sciences, 2026 (arXiv:2508.01491)
- *LLM Output Homogenization is Task Dependent*, arXiv:2509.21267, 2025
- Zhang et al., *From Lists to Emojis: How Format Bias Affects Model Alignment*, ACL 2025
- *Bias Fitting to Mitigate Length Bias of Reward Model*, arXiv:2505.12843, 2025
- *Reward Models are Metrics in a Trench Coat*, arXiv:2510.03231, 2025

**推論・構造化出力の副作用**
- Li et al., *When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following*, arXiv:2505.11423, 2025
- *R²-Write: Reflection and Revision for Open-Ended Writing*, arXiv:2604.03004, 2026
- *Language Models that Think, Chat Better*, arXiv:2509.20357, 2025
- *Does Forcing Structured Output Degrade LLM Creativity?*, OpenReview vYkz5tzzjV, 2025
- Tam et al., *Let Me Speak Freely?*, arXiv:2408.02442, 2024
- *The Format Tax*, arXiv:2604.03616, 2026
- *Reverse-Engineered Reasoning for Open-Ended Generation*, arXiv:2509.06160, 2025

**スタイル制御・選抜**
- Wu et al., *AxBench: Steering LLMs? Even Simple Baselines Outperform SAEs*, arXiv:2501.17148, ICML 2025 Spotlight
- Suzgun, Melas-Kyriazi, Jurafsky, *Prompt-and-Rerank*, arXiv:2205.11503
- Lanchantin et al., *Diverse Preference Optimization*, arXiv:2501.18101, 2025
- *Modifying LLM Post-Training for Diverse Creative Generation (DDPO/DORPO)*, arXiv:2503.17126, 2025
- Sun et al., *SynDec: Synthesize-then-Decode for Arbitrary Style Transfer*, arXiv:2505.12821, 2025
- *Customizing LM Responses with Contrastive ICL (CICL)*, arXiv:2401.17390
- Wang et al., *Catch Me If You Can? LLMs Still Struggle to Imitate Implicit Writing Styles*, arXiv:2509.14543, 2025
- Patel et al., *Steering LLMs with Register Analysis (STYLL)*, arXiv:2505.00679, 2025

**マルチエージェント・編集ループ失敗**
- *Talk Isn't Always Cheap: Failure Modes in Multi-Agent Debate*, ICML 2025, arXiv:2509.05396
- *Stay Focused: Problem Drift in Multi-Agent Debate*, arXiv:2502.19559, 2025

**Persona drift / 長文計画**
- Li et al., *Measuring and Controlling Persona Drift in LM Dialogs*, arXiv:2402.10962
- *Stable Personas: Dual-Assessment of Temporal Stability*, arXiv:2601.22812, 2026
- *Beyond Outlining: Heterogeneous Recursive Planning*, arXiv:2503.08275, 2025

**日本語コーパスと事前学習**
- Okazaki et al., *Building a Large Japanese Web Corpus for LLMs*, arXiv:2404.17733, COLM 2024
- Fujii et al., *Continual Pre-Training for Japanese*, arXiv:2404.17790, COLM 2024
- Llama 3.3 Swallow project pages, swallow-llm.github.io, 2025

**日本語スタイロメトリ・評価**
- Zaitsu, Jin, Ishihara, Tsuge, Inaba, *Japanese stylometric AI detection*, PLOS ONE, October 2025
- Kubota, Ishizuki, Matsubayashi, *項省略判断*, ANLP 2025 Q6-8
- Mikami, *日本語の自然さを測る評価手法の検証*, Preferred Networks Tech Blog, 2026.02.20
- pfgen-bench, github.com/pfnet-research/pfgen-bench, 2024
- Tsukagoshi & Sasano, *Ruri Japanese Embeddings*, arXiv:2409.07737, 2024
- JMTEB v2, sbintuitions, LREC 2026
- Hans et al., *Binoculars*, arXiv:2401.12070, ICML 2024
- Bao et al., *Fast-DetectGPT*, arXiv:2310.05130
- jReadability, jreadability.net (Lee Jaeho lab)
- Shaib et al., *Standardizing the Measurement of Text Diversity*, ACL/IJCNLP 2025 demo

**サイコファンシー・指示追従とのトレードオフ**
- Sharma et al., *Towards Understanding Sycophancy*, arXiv:2310.13548
- *SycEval*, arXiv:2502.08177, 2025
- *Interaction Context Often Increases Sycophancy*, arXiv:2509.12517, CHI 2026
- *Dancing in Chains: IF/Faithfulness Tradeoff*, arXiv:2407.21417
- *On the Paradoxical Interference between IF and Task Solving*, arXiv:2601.22047, 2026

**OpenAI 公式ドキュメント**
- GPT-5 launch: openai.com/index/introducing-gpt-5-for-developers/, 2025-08-07
- GPT-5 prompting guide: cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide
- GPT-5.1 prompting guide: cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide
- GPT-5.4 mini launch: openai.com/index/introducing-gpt-5-4-mini-and-nano/, 2026-03-17
- Prompt Personalities cookbook: developers.openai.com/cookbook/examples/gpt-5/prompt_personalities, 2026-01
- Latest model guide (GPT-5.5): developers.openai.com/api/docs/guides/latest-model

**第三者レビュー(GPT-5 系列の文体傾向)**
- Heilig, *GPT-5 is a Terrible Storyteller*, christoph-heilig.de, 2025-08
- Shumer, *GPT-5.2 review*, shumer.dev/gpt52review
- Smith Stephen, *ChatGPT 5.4 review*, smithstephen.com, 2026-03
- Novelcrafter, *Is GPT-5 any good for writing fiction*, 2025
- *Sam Altman admits GPT-5.2 writing regression*, Search Engine Journal, 2026