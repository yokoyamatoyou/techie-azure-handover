# **テキストの不気味の谷：大規模言語モデルと人間による著作物の言語的乖離に関する包括的分析報告書**

## **エグゼクティブサマリー**

大規模言語モデル（LLM）の急速な普及は、テキスト生成の風景を根本から変革し、文法的にも意味的にも高度に洗練された談話を生成可能な非人間的エージェントを社会に導入することとなった。しかし、その流暢さにもかかわらず、OpenAIのGPTシリーズやMetaのLlamaなどのLLMが生成するテキストは、人間の書き手が作成するものとは決定的に異なるという経験的証拠が蓄積されている。本報告書は、機械生成テキストに特有の「AI訛り」とも呼ぶべき微細だが広範な人工的違和感の根本原因を、計算言語学、心理言語学、および情報理論の観点から詳細に解明することを目的とする。

本分析は、計算言語学、認知科学、および機械学習の最新の研究成果を統合し、人間とAIの言語的乖離を引き起こす主要な要因を3つの次元で特定した。（1）**語彙的多様性の異常（Lexical Diversity Anomalies）**：AIモデルは、人間には不可能なほどに統計的に平滑化された語彙選択と、文脈に応じた不自然な反復回避傾向を示す。（2）**統語的および修辞的硬直性（Syntactic and Rhetorical Rigidity）**：指示チューニング（Instruction Tuning）とRLHF（人間からのフィードバックによる強化学習）の結果、AIは動詞中心で冗長性を含む人間のコミュニケーションとは対照的な、名詞中心で情報密度の高い「堆積した文体（Sedimented Style）」を固持する。（3）**心理言語学的非対称性（Psycholinguistic Dissonance）**：人間特有の認知負荷（Cognitive Load）やワーキングメモリの制約が欠如しているため、AIのテキストには人間らしい思考のリズム、言い淀み、そして「バースト性（Burstiness）」が欠落している。

さらに、本報告書では、テキストベースのコミュニケーションにおける「不気味の谷（Uncanny Valley）」現象について深く掘り下げる。特に、技術的に進歩した最新モデルが、その過剰な最適化ゆえに、かえって人間らしさから遠ざかるというパラドックスを明らかにする。最後に、これらの分析に基づき、プロンプトエンジニアリングの高度な技法から、Min-Pサンプリングのようなデコーディングパラメータの調整に至るまで、AI出力をより「人間らしく」再構築するための科学的根拠に基づいた戦略を提示する。

## ---

**1\. 序論：チューリングテストを超えて**

### **1.1 背景と問題の所在**

人工知能研究の黎明期より、機械が人間と見分けがつかないほどのテキストを生成できるか否かという問い、すなわち「チューリングテスト」は、AIの知能を測る金字塔であった。しかし、2020年代に入り、GPT-4をはじめとする大規模言語モデルの登場によって、この問いの質は劇的に変化した。もはや機械は、単に文法的に正しい文章を書くだけでなく、詩を創作し、複雑な論文を要約し、人間のような対話を行う能力を獲得している。しかし、それと同時に、読者はAIが生成したテキストに対して、得体の知れない違和感や「冷たさ」、あるいは「人間味の欠如」を直感的に感知するようになった 1。

この違和感は、単なる品質の問題ではない。むしろ、AIの生成するテキストがあまりにも「完璧」であり、確率論的に「平均的」であるがゆえに生じる現象である。人間が文章を書く際、そこには疲労、感情、記憶の曖昧さ、そして特定の他者への伝達意図が介在する。これらはテキストに微細な「ノイズ」として現れるが、このノイズこそが人間性の証明となる。対して、確率的最適化に基づくLLMの出力は、この人間的ノイズが欠落しているか、あるいは不自然に模倣されているため、読み手に認知的な不協和音をもたらすのである 2。

### **1.2 報告書の目的と構成**

本報告書は、AI生成テキストがなぜ「AIっぽい」と感じられるのか、その言語学的・認知科学的メカニズムを解明し、その知見を基に、より人間らしい自然なテキスト生成を実現するための具体的な手法を提案することを目的とする。

報告書の構成は以下の通りである。第2章では、最新の計算言語学的研究に基づき、AIと人間の語彙的多様性（Lexical Diversity）の決定的な違いを6つの次元から分析する。第3章では、文体と修辞の観点から、AI特有の「堆積した文体」と情報密度の問題を探求する。第4章では、心理言語学的アプローチを用い、認知負荷の欠如がいかにして不自然な流暢さを生み出すかを論じる。第5章では、日本語特有の言語構造（敬語、文末表現、文脈依存性）におけるAIの不自然さに焦点を当てる。第6章では、これらの知見を統合し、「人間化（Humanization）」のための具体的な技術戦略（プロンプト設計、パラメータ調整）を詳述する。最後に第7章で、AIと人間の共創における未来の展望を述べる。

## ---

**2\. LLMにおける語彙的多様性のパラドックス**

AI生成テキストと人間が執筆したテキストを区別する最も堅牢な指標の一つが、語彙的多様性（Lexical Diversity: LD）である。LDとは、テキスト内で使用される語彙の範囲や変化の豊かさを指す。直感的には、「より賢い」モデルほど、人間の語彙使用パターンをより忠実に模倣すると考えられがちである。しかし、最新の実証研究は、技術的に進歩したモデルほど、人間とは異なる独自の「超多様性（Hyper-diversity）」あるいは構造的に異質な語彙プロファイルを形成していることを示唆している 4。

### **2.1 語彙的多様性の多次元的分析**

Kendro, Maloney, and Jarvis (2025) による画期的な研究は、ChatGPTの各バージョン（3.5, 4, o4-mini, 4.5）と、多様な背景（教育レベル、第一言語/第二言語）を持つ240名の人間の参加者が作成したテキストを比較分析したものである。この研究の特筆すべき点は、語彙的多様性を単一の指標（Type-Token Ratioなど）で捉えるのではなく、以下の6つの独立した次元に分解して評価したことにある 4。この多次元的アプローチにより、AIと人間の差異の微細な構造が明らかになった。

#### **2.1.1 Volume（テキスト量）**

Volumeは、生成されたテキストの総トークン数を指す。

* **分析結果**: AIモデル、特にGPT-4.0は、人間と同一のプロンプト（TOEFLのエッセイ課題）を与えられた際、人間よりも有意に長いテキストを生成する傾向がある。人間は認知的・時間的制約の中で効率的に意図を伝達しようとするため、必要十分な長さで完結させる傾向が強い。一方、AIは確率的に「続く可能性のある」内容を吐き出し続ける傾向があり、これが冗長さを生み出す一因となっている 4。  
* **意味合い**: テキストが長くなるほど、通常は同じ単語が繰り返される確率が高まり、見かけ上の語彙多様性は低下するはずである。しかし、後述するようにAIは長文であっても高い多様性を維持するという、人間には困難な特性を示す。

#### **2.1.2 Abundance（語彙の豊富さ）**

Abundanceは、テキスト内に含まれるユニークな単語（異なり語数）の総数を指す。

* **分析結果**: AIは人間と比較して、圧倒的に多くのユニークな単語を使用する。これは部分的にはVolume（テキスト量）の多さに起因するが、それを補正してもなお、AIは同義語や類義語を頻繁に切り替えて使用する傾向がある 4。  
* **人間との対比**: 人間は、特定のトピックについて語る際、重要なキーワードを一貫して使用する傾向がある（例：「学習」という言葉を定義したら、それを「勉強」や「習得」と言い換えずに「学習」として使い続ける）。AIはこの一貫性を「繰り返し」として統計的に回避しようとするため、不自然なほどの語彙の散らばりが生じる。

#### **2.1.3 Variety-Repetition（多様性と反復のバランス）**

これは、従来のTTR（Type-Token Ratio）やMATTR（Moving Average TTR）などで測定される、ユニークな単語と繰り返される単語の比率である。

* **分析結果**: AI生成テキストは、人間よりも有意に高いVariety-Repetitionスコアを示す。つまり、AIは同じ単語の繰り返しを極端に避ける 4。  
* **言語学的洞察**: 人間のコミュニケーションにおいて、「反復（Repetition）」はバグではなく機能である。反復は、情報の定着、リズムの形成、そして談話の結束性（Cohesion）を高めるために不可欠な要素である。AIが示す「反復の欠如」は、一見すると語彙が豊富で洗練されているように見えるが、読み手にとっては「焦点が定まらない」「教科書的で無味乾燥」という印象を与える原因となる 6。

#### **2.1.4 Evenness（均等性）**

Evennessは、テキスト内での単語の出現頻度分布の均一性を測る指標である。

* **分析結果**: AIの単語分布は数学的に滑らかであり、確率曲線に厳密に従う傾向がある。一方、人間のテキストは「塊（lumpy）」がある分布を示す。人間は、その場の思いつきや、短期記憶内で活性化している特定の単語（Availability Heuristic）に引きずられるため、特定の単語が局所的に集中して使用される 4。  
* **不気味さの源泉**: この過度な「均等性」は、AIテキストに「人工的な整然さ」を与える。自然界や人間の行動にはムラがあるが、AIの出力にはそのムラが欠如しているため、直感的な違和感を生むのである。

#### **2.1.5 Dispersion（分散）**

Dispersionは、同じ単語が繰り返される際の間隔（距離）を測定する。

* **分析結果**: AIは高いDispersion（再出現までの間隔が長い）を示す。人間は、トピックを維持するために、近い距離でキーワードを連呼する（低いDispersion）傾向がある 4。  
* **認知プロセスとの関連**: 人間はワーキングメモリの制約上、直前に使用した単語を再利用する方が認知コストが低い。AIにはこの制約がないため、文脈ウィンドウ全体を参照しながら、意図的に離れた位置で単語を使用したり、別の単語に置き換えたりすることが可能である。これが、AIテキストが「記憶力が良すぎる」ように感じられる一因である。

#### **2.1.6 Disparity（意味的相違度）**

Disparityは、使用される単語間の意味的な距離や違いの度合いを測る。

* **分析結果**: 興味深いことに、この次元においてのみ、一部のAIモデル（GPT-3.5やGPT-4.5）が人間のグループと類似したスコアを示した 4。  
* **解釈**: これは、AIが選ぶ単語の「意味的な散らばり具合」自体は人間に近いことを示唆している。しかし、その頻度（Evenness）や配置（Dispersion）が人間とかけ離れているため、全体としては異質に感じられるのである。

### **2.2 進化するほど人間から遠ざかる「逆説」**

Kendroらの研究における最も衝撃的な発見は、\*\*「新しいモデルほど、人間らしくなくなっている」\*\*という事実である 4。

* **GPT-4.5の特異性**: 特に最新のGPT-4.5は、GPT-4.0よりも生成するトークン数が少ない（Volumeが小さい）にもかかわらず、極めて高い語彙的多様性を示した。通常、短いテキストでは語彙の重複が避けられないはずだが、GPT-4.5は限られた字数の中に驚異的な密度の異なり語を詰め込んでいる。これは、RLHF（人間からのフィードバックによる強化学習）によって「簡潔さ」と「情報量」が過剰に最適化された結果、人間が自然に行う冗長性や非効率性が排除されたためと考えられる 4。  
* **人間の一貫性**: 対照的に、人間の書き手は、高校卒から博士号取得者、母語話者から第二言語学習者に至るまで、語彙的多様性のプロファイルにおいて驚くほど一貫していた 4。これは、語彙の多様性が教育レベルによって変わる知識の問題ではなく、人間の脳が言語を処理する際の生物学的・認知的な制約（ハードウェアの仕様）に根ざしていることを示唆している。AIはこの制約を持たないため、進化すればするほど、人間の生物学的限界を超越した「エイリアン」のような言語生成へと突き進んでいるのである。

### **2.3 語彙の豊かさと「モデルの崩壊」**

AIの語彙選択に関する別の懸念として、「モデルの崩壊（Model Collapse）」や「言語の均質化（Homogenization）」がある。Reviriegoら（2024）の研究では、初期のモデルは人間よりも語彙が貧弱であったが、GPT-4以降は人間を凌駕する多様性を持つようになったとされる 5。しかし、この「豊かさ」は統計的な確率分布（Zipf則）に忠実すぎるがゆえの豊かさである。

さらに、AIが生成したテキストがインターネット上に溢れ、それをまたAIが学習するというフィードバックループが発生することで、言語の「レジスター（使用域）の平準化（Register Leveling）」が進行している 8。AIは「平均的に正しく、無難な」表現を好むため、方言、俗語、独特な言い回し、そして滅多に使われないレアな単語（ロングテール）が淘汰され、人間の言語表現そのものがAIのスタイルへと均質化されていくリスクが指摘されている 8。

## ---

**3\. 「堆積した文体」：文法的・修辞的硬直性の解剖**

AIテキストが「AIっぽい」と感じられる要因は、単語の選び方だけでなく、文の構造や修辞的なスタイルにも深く根ざしている。この特徴的なスタイルは、研究者たちによって「堆積した文体（Sedimented Style）」と形容されている 9。これは、地層のように重層的で変化に乏しく、情報密度が異常に高い文体を指す。

### **3.1 指示チューニング（Instruction Tuning）がもたらす弊害**

ベースモデル（事前学習のみのモデル）は、インターネット上の多様なテキスト（掲示板の書き込みから小説まで）を学習しているため、本来は極めて多様な文体を模倣する能力を持っている。しかし、製品化のために行われる**指示チューニング（Instruction Tuning）とRLHF**が、この多様性を押し殺していることがPNAS（米国科学アカデミー紀要）の2025年の研究で明らかになった 9。

開発者はAIに対して「役に立つ」「安全な」「正確な」回答をするように調整を行う。この過程で、AIは「中立的で、権威があり、効率的な」トーンを正解として学習する。その結果、ユーザーが「カジュアルに話して」とプロンプトで指示しても、モデルはこの「安全な」文体から完全には脱却できず、名詞中心の硬い文構造を維持してしまう 10。この現象は、AIが文体的な柔軟性を失い、どのような文脈でも一種の「擬似アカデミック」なスタイルに収束してしまうことを意味する。

### **3.2 AI特有の文法的マーカー**

Biberの多次元分析フレームワークを用いた比較研究により、AIテキストには人間と比較して統計的に有意に過剰使用される文法構造があることが特定されている 9。

#### **3.2.1 名詞化（Nominalization）の多用**

AIモデルは、動詞や形容詞で表現できる内容を名詞化して表現する傾向が、人間の**1.5倍から2倍**強い 9。

* **例**:  
  * 人間：「このシステムを導入すれば、作業が速くなります。」（動詞中心）  
  * AI：「このシステムの**導入**は、作業の**迅速化**をもたらします。」（名詞中心）  
* **効果**: 名詞化は情報の密度を高めるが、文章から「動き」や「物語性」を奪う。結果として、静的でレポートのような、いわゆる「お役所言葉」に近い印象を与える。これがAIテキストの「冷たさ」の正体の一つである。

#### **3.2.2 現在分詞構文（Present Participial Clauses）の乱用**

AIは、文の主節に従属する形で現在分詞（〜ing）を用いた節を挿入する頻度が、人間の**2倍から5倍**に達する 9。

* **例**: "Brian, *leaning on his agility*, dances around the ring, *evading Show's heavy blows*." 11  
* **分析**: このような構造は文法的には正しいが、情報の階層を複雑にし、認知的な処理負荷を高める。人間は通常、このような重層的な文を連続して書くことは避け、短い文に分割したり、接続詞を使ったりしてリズムを作る。AIがこの構造を好むのは、一つの文に多くの情報を効率的に詰め込むことができるためである（情報圧縮へのバイアス）。

#### **3.2.3 受動態の回避と明示的な文法マーカー**

一方で、GPT-4oなどは人間と比較して、動作主を示さない受動態（Agentless Passive Voice）の使用頻度が半分程度である 11。AIは主語を明確にすることを好む（あるいはそう訓練されている）ため、受動態でぼかすよりも、名詞化した無生物主語を用いて能動態で書くことを選ぶ傾向がある。また、補文標識の "that"（例: "The study concluded *that*..."）なども、人間は省略することが多いが、AIは省略せずに明示的に記述する傾向がある 12。これはAIが「曖昧さ」を嫌い、文法的な完全性を優先していることを示している。

### **3.3 「Delve」現象：AIスタイルワードの爆発的増加**

文法構造だけでなく、特定の単語（スタイルワード）の使用頻度における異常なスパイクも、AIテキストの顕著な特徴である。2023年以降、学術論文やウェブ記事において、特定の単語の使用率が垂直的に上昇していることが確認されている 8。

* **代表的なAI単語（The "Dirty Dozen"）**:  
  * **Delve (into)**: 「掘り下げる」。PubMedなどのデータベースで、2023年以降に使用頻度が激増した。AIが「詳細に説明する」という文脈で好んで選択する単語である 13。  
  * **Tapestry**: 「タペストリー（織物）、複雑な構造」。"A rich tapestry of culture" のように、複雑さを比喩的に表現する際に多用される。人間よりも約150倍多く使用されている 11。  
  * **Underscore**: 「強調する」。"This underscores the importance of..." はAIの定型句である。  
  * **Realm**: 「領域」。"In the realm of digital marketing..." のような導入句で頻出する。  
  * **Camaraderie, Vibrant, Intricate, Pivotal, Crucial**: これらの単語も、AIが文脈を滑らかに接続するための「フィラー（埋め草）」として過剰に使用する 14。

これらの単語は、統計的に「安全」であり、どのような文脈でもそれっぽく聞こえるため、モデルが局所最適解として選択しやすいと考えられる。しかし、人間にとっては、これらの単語の頻出は「AIが書いた」という強力なシグナル（Shibboleth）となってしまっている。

## ---

**4\. 心理言語学的非対称性：なぜAIは「間違っている」と感じるのか**

文体論的特徴が「何が違うか」を定量化するのに対し、心理言語学は「なぜその違いが人間に違和感を与えるのか」という知覚のメカニズムを説明する。AIテキストの不気味さは、AIが「思考の結果」だけを模倣し、「思考のプロセス」を経ていないことに起因する。

### **4.1 認知負荷理論と「エラーの欠如」**

人間の執筆行為は、常に認知的な制約との戦いである。\*\*認知負荷理論（Cognitive Load Theory: CLT）\*\*によれば、人間のワーキングメモリには限界がある。複雑なアイデアを言語化する際、人間は「内容の計画（Discourse Planning）」と「文の構築（Sentence Generation）」の間でリソースを配分しなければならない。この負荷が高まると、人間は以下のような「不完全さ」を露呈する 16。

* **統語的単純化**: 難しい概念を説明する際、文構造を単純にして認知コストを下げる。  
* **言い淀みと修正**: 文の途中で表現を変えたり、前の文との接続が曖昧になったりする。  
* **品質の揺らぎ**: 素晴らしい洞察を含む文の直後に、平凡な文が続くような「ムラ」が生じる。

対して、AIにはこのような認知負荷が存在しない。AIは常に一定の計算リソースを使用し、テキストの冒頭から結末まで、文法的に完璧で、かつ高い統語的複雑性を維持し続けることができる 16。この\*\*「疲れを知らない流暢さ（Unrelenting Fluency）」\*\*こそが、人間に違和感を与える。人間は無意識のうちに、他者のテキストの中に「思考の苦労」や「認知的な息継ぎ」を探している。それらが完全に欠落したテキストは、重みがなく、地に足がついていない（ungrounded）と感じられるのである。

### **4.2 均一情報密度（UID）仮説の違反**

情報理論における\*\*均一情報密度（Uniform Information Density: UID）\*\*仮説は、人間はコミュニケーションにおいて、情報の伝達速度（密度）を一定に保とうと無意識に最適化しているとするものである 12。

* **人間の戦略**: 難しい内容（情報量が多い）を話すときは、冗長な言葉（フィラーや言い換え）を挟んでペースを落とす。逆に、予測可能な内容（情報量が少ない）は、言葉を省略してスピードを上げる。  
* **AIの逸脱**: AIは、文脈ウィンドウ全体を同時に参照できるため、人間が必要とするような「冗長性によるペースダウン」を行わない傾向がある。その結果、情報の密度が常に高い状態で維持されたり、物語の展開において伏線を張って緊張感を高めるような「溜め」を作らずに、急速にプロットを展開させてしまったりする 17。  
* **影響**: 読み手にとって、UIDに違反したテキストは「息苦しい」あるいは「情緒がない」と感じられる。必要な冗長性（ムダ）がないため、情報の消化不良を起こしやすいのである。

### **4.3 テキストにおける「不気味の谷」現象**

ロボット工学における「不気味の谷（Uncanny Valley）」現象は、テキストベースのAIにも強く当てはまることが最新の研究で確認されている 2。

* **感情の急降下**: チャットボットや生成テキストが「人間に非常に近いが、完全ではない」領域に達したとき、ユーザーの親近感は急激に低下し、嫌悪感や恐怖感に変わる。これを「不気味の谷」と呼ぶ。  
* **テキストにおけるトリガー**: 人間らしい共感や感情表現を模倣しようとするが、文脈にそぐわない完璧すぎる応答や、微妙にずれた感情的ニュアンスが含まれると、この谷に落ちる。Oparaらの研究では、人間らしく振る舞うようにプロンプトエンジニアリングされたボット（Uncanny-Valley Bot）が、明らかに機械的なボットよりも「知性」や「好感度」の評価で低くなることが示されている 2。  
* **「中間のリアリズム」の失敗**: 完全に機械的であれば道具として受け入れられ、完全に人間であれば共感される。しかし、GPT-4レベルの「人間まであと一歩」のテキストは、その微細なズレ（過剰な丁寧さ、感情の欠落、定型的な反応）が強調され、最も不気味に感じられる領域にあると言える 2。

## ---

**5\. 日本語特有の「AIっぽさ」：ロボットは敬語を話す**

ここまでの議論は主に英語圏の研究に基づいているが、日本語という言語構造においては、AIの不自然さはさらに独特な形で顕現する。日本語は、敬語システム、文脈依存性（空気を読む）、主語の省略などを特徴としており、これらがAIの確率モデルと相性が悪い場合がある。

### **5.1 「です・ます」の呪縛とリズムの欠如**

日本語のAIテキストがロボットのように感じられる最大の要因の一つは、文末表現の単調さである。

* **AIの傾向**: AIは「〜です」「〜ます」という丁寧語を、すべての文末で律儀に使用する傾向が極めて強い。  
* **人間のリズム**: 人間の書き手は、同じ丁寧語の文章であっても、「〜でしょう」「〜ですね」「〜（体言止め）」「〜か？」などのバリエーションを混ぜたり、文の長さを変えたりして、リズム（余韻）を作る。  
* **違和感**: 全ての文が「〜です。」「〜ます。」で完結するテキストは、スタッカートのように断続的で、まるで小学校の教科書や機械のマニュアルを読んでいるような印象を与える 18。

### **5.2 テンプレート構造とMarkdownの侵入**

ウェブ上のデータを学習したAIは、特にSEO記事やブログの構造を過学習している傾向がある。

* **「結論から言うと」**: AIは論理的な整合性を優先するため、「まず結論から申し上げますと（Ketsuron kara iu to）」や「重要なのは〜です」といったフレーズを多用する。これはビジネスメールや実用文では有用だが、エッセイや創作文で使われると一気に情緒が損なわれる 18。  
* **Markdownの視覚的ノイズ**: プロンプトで指定しなくても、AIは文章中に箇条書き（・や1.）や太字を挿入したがる。人間は、感情的な文章や手紙の中で突然箇条書きを始めることは稀である。この視覚的な構造化は「効率性」の象徴であり、人間的な「語り」とは対極にある。

### **5.3 意味の浅さと「過剰な説明」**

日本語はハイコンテクスト文化であり、多くの情報を「言わずに察する」ことが良しとされる。しかし、AIは文脈を共有していないため、すべてを言語化して説明しようとする（Explicitation）。

* **主語の補完**: 日本語では自明な主語（私、あなた）は省略されるが、AIはこれを補完して「私は〜と思います。あなたは〜ですか？」と出力しがちである。これが翻訳調の不自然さを生む。  
* **抽象語の多用**: 具体的な描写（Show）よりも、抽象的な感情語（Tell）を多用する。「不安だった」とは言うが、「胃がキリキリした」とは言わない。感覚的な深みがなく、表層的な意味の羅列になりやすい 18。

## ---

**6\. 数理的決定論：パープレキシティとバースト性**

AIと人間のテキストの違いを数学的に定量化する上で、最も重要な指標が\*\*パープレキシティ（Perplexity）**と**バースト性（Burstiness）\*\*である。これらの概念は、なぜAIが上記のような特徴を持つのかを根本から説明する。

### **6.1 パープレキシティ：予測可能性の指標**

パープレキシティは、言語モデルが次の単語をどれだけ「驚かずに」予測できるかを示す指標である。数値が低いほど、予測しやすく、ありふれた文章であることを意味する。

* **AIの目的**: LLMの学習目的は、パープレキシティを最小化すること（正解の単語を当てること）である。したがって、生成されるテキストは必然的に「最も確率の高い（驚きの少ない）経路」を辿ろうとする。  
* **人間の現実**: 人間の文章は、パープレキシティが本来的に高い。人間は突然話題を変えたり、独創的な比喩を使ったり、文法的に破格な表現を用いたりする。  
* **結果**: AIテキストは「滑らか」で「読みやすい」が、それは「驚きがない」ことの裏返しである。それはBGMのようなもので、不快ではないが、心に刺さるフック（Perplexityのスパイク）が存在しない 19。

### **6.2 バースト性：思考のリズム**

バースト性は、文の長さや構造の変動（ばらつき）を指す。

* **人間のバースト**: 人間は「バースト（爆発）」的に書く。複雑な論理を展開する長い文の後に、結論を述べる短い文を置く。「昨日は雨だった。本当にひどい雨で、傘も役に立たず、靴の中までぐしょ濡れになって最悪の気分だった。」のように、静と動が混在する。これは人間の呼吸や思考のパルスを反映している 21。  
* **AIの平坦さ**: AIのテキストはバースト性が低い。平均的な長さ、平均的な複雑さの文を淡々と積み重ねる。標準偏差が小さく、リズムが一定であるため、読者は単調さを感じて飽きてしまう（Fatigue） 20。

## ---

**7\. 「人間化」へのアプローチ：乖離を埋める技術戦略**

AIの「癖」の原因が特定された今、それを逆手に取ることで、AI生成テキストをより人間らしく（あるいは、より魅力的に）するための具体的な戦略を立案できる。これには、プロンプトエンジニアリングによる介入と、モデルの推論パラメータの調整という二つのアプローチがある。

### **7.1 高度なプロンプトエンジニアリング**

最も手軽かつ効果的な方法は、プロンプトを通じてAIのデフォルトの振る舞い（確率的な安全策）を強制的に解除することである。

#### **7.1.1 構造と語彙の制約（Negative Constraints）**

「人間らしく書いて」という抽象的な指示は機能しない。具体的になにを「しない」かを指示する必要がある。

* **NGワードリスト**: 「以下の単語を使用禁止にする: delve, tapestry, realm, underscore, 導入（introduction）, 結論（conclusion）」 22。  
* **構造の破壊**: 「『導入・本文・結論』の構成を禁止する。いきなり核心から書き始めること。箇条書きの使用を禁止する。」  
* **日本語特有の指示**: 「文末を『〜です』『〜ます』だけで終わらせないこと。体言止め、疑問形、独り言のような文を3回以上混ぜること。」「『結論から言うと』というフレーズを使わないこと。」 18

#### **7.1.2 認知シミュレーションとペルソナ**

AIに「人間のような認知負荷」をシミュレートさせる。

* **思考のプロセスの模倣**: 「あなたは疲れているが、どうしても伝えたいことがある情熱的なエンジニアとして書いてください。推敲された文章ではなく、思考がそのまま漏れ出したような、少し荒い文体で書いてください。」  
* **バースト性の強制**: 「短文（10文字以内）と長文（80文字以上）を交互に織り交ぜて、リズムに極端な強弱をつけること。」 24

### **7.2 サンプリングパラメータの最適化**

APIを利用する場合、デコーディングパラメータを調整することで、AIの統計的な決定論を崩すことができる。

#### **7.2.1 Min-Pサンプリング：次世代の多様性制御**

従来のTop-P（Nucleus）サンプリングに代わる、より人間らしい出力を可能にする手法として**Min-Pサンプリング**が注目されている 25。

* **仕組み**: Top-Pは累積確率が閾値（例: 0.9）になるまで候補を採用するが、Min-Pは「最も確率の高い単語の確率（![][image1]）」を基準にし、その ![][image2]（例: 0.05倍）以上の確率を持つ単語だけを候補に残す（動的切り捨て）。  
* **効果**: モデルが自信を持っているとき（$P\_{max}$が高いとき）は候補を絞り込んで一貫性を保ち、自信がないとき（$P\_{max}$が低いとき）は候補を広げて創造性を発揮する。これにより、文脈に応じた適切な「遊び」が生まれ、Top-Pよりも人間らしい語彙選択が可能になる 25。

#### **7.2.2 温度（Temperature）とペナルティ**

* **高温度（Temperature \> 1.0）**: 創造性を高めるために温度を上げるが、Min-Pと組み合わせることで論理破綻を防ぎつつ、"Delve"のような定型語の選択確率を下げることができる。  
* **Frequency/Presence Penalty**: これらのペナルティをわずかに上げる（0.1-0.3）ことで、同じ単語の反復を防ぎ、AI特有の「くどさ」を軽減できるが、上げすぎると不自然な言い換えが発生するため注意が必要である 27。

### **7.3 ポストエディティングとツール**

* **人間による介入**: 最も確実な方法は、AIが生成したテキストに人間が「ノイズ」を加えることである。接続詞を削除する、文を途中で切る、個人的なエピソードを挿入する、あえて主語を抜くといった編集は、AIには模倣しにくい「生きた痕跡」を与える。  
* **Humanizerツールの利用**: 既存のAI検出回避ツールは、類義語の置換や構文の並べ替えを行うが、意味の明瞭さを損なう場合があるため、補助的な利用に留めるべきである 28。

## ---

**8\. 結論：ハイブリッド・ライティングの未来**

AIが生成するテキストが「人間らしくない」のは、技術的な失敗ではなく、その設計思想（確率的最適化、安全性、効率性）の必然的な帰結である。開発者たちは、誤情報を減らし、不快な発言を防ぐためにモデルを調整してきたが、その副作用として「人間味」というノイズまでもが除去されてしまったのである。

Kendroらの研究が示したように、モデルが進化すればするほど、その語彙プロファイルは人間から離れていく可能性がある 4。これは、AIが人間を目指しているのではなく、「超人間的な効率的伝達者」へと進化していることを意味する。したがって、「不気味の谷」は今後さらに広がるかもしれない。

我々人間に求められるのは、AIに「人間になれ」と強いることではなく、AIが生成した「堆積した情報ブロック」を、人間的なリズムと文脈で彫刻し直すスキルである。AIの出力は最終製品ではなく、あくまで「素材」である。バースト性を意識し、Min-Pのような高度な制御を用い、そして何より人間の意図（Intent）を強く介在させることでのみ、デジタルなテキストに魂を吹き込むことが可能となる。真に人間らしいテキストとは、確率の波に逆らって選ばれた、予測不可能な言葉の中にこそ宿るのである。

---

**Reference Materials:** 1 plus supplementary search data.

#### **引用文献**

1. (PDF) Do LLMs produce texts with "human-like" lexical diversity? \- ResearchGate, 2月 10, 2026にアクセス、 [https://www.researchgate.net/publication/394263012\_Do\_LLMs\_produce\_texts\_with\_human-like\_lexical\_diversity](https://www.researchgate.net/publication/394263012_Do_LLMs_produce_texts_with_human-like_lexical_diversity)  
2. The Uncanny Valley: An Empirical Study on Human ... \- DSpace@MIT, 2月 10, 2026にアクセス、 [https://dspace.mit.edu/bitstream/handle/1721.1/159096/kishnani-deepalik-sm-sdm-2025-thesis.pdf](https://dspace.mit.edu/bitstream/handle/1721.1/159096/kishnani-deepalik-sm-sdm-2025-thesis.pdf)  
3. Chikamatsu, Mori, and the uncanny valley \- PMC, 2月 10, 2026にアクセス、 [https://pmc.ncbi.nlm.nih.gov/articles/PMC11800272/](https://pmc.ncbi.nlm.nih.gov/articles/PMC11800272/)  
4. 2508.00086v2.pdf  
5. Playing with words: Comparing the vocabulary and lexical diversity of ChatGPT and humans, 2月 10, 2026にアクセス、 [https://www.researchgate.net/publication/385756888\_Playing\_with\_words\_Comparing\_the\_vocabulary\_and\_lexical\_diversity\_of\_ChatGPT\_and\_humans](https://www.researchgate.net/publication/385756888_Playing_with_words_Comparing_the_vocabulary_and_lexical_diversity_of_ChatGPT_and_humans)  
6. 2月 10, 2026にアクセス、 [https://bykovbrett.net/blog/techniques-to-make-ai-generated-text-sound-more-human\#:\~:text=Break%20up%20long%20sentences%20or,instantly%20liven%20up%20a%20paragraph.](https://bykovbrett.net/blog/techniques-to-make-ai-generated-text-sound-more-human#:~:text=Break%20up%20long%20sentences%20or,instantly%20liven%20up%20a%20paragraph.)  
7. \[2308.07462\] Playing with words: Comparing the vocabulary and lexical diversity of ChatGPT and humans \- arXiv, 2月 10, 2026にアクセス、 [https://arxiv.org/abs/2308.07462](https://arxiv.org/abs/2308.07462)  
8. Testing English News Articles for Lexical ... \- ACL Anthology, 2月 10, 2026にアクセス、 [https://aclanthology.org/2025.acl-srw.95.pdf](https://aclanthology.org/2025.acl-srw.95.pdf)  
9. Do LLMs write like humans? Variation in grammatical and rhetorical styles \- PNAS, 2月 10, 2026にアクセス、 [https://www.pnas.org/doi/10.1073/pnas.2422455122](https://www.pnas.org/doi/10.1073/pnas.2422455122)  
10. Do LLMs write like humans? Variation in grammatical and rhetorical styles \- arXiv, 2月 10, 2026にアクセス、 [https://arxiv.org/html/2410.16107v1](https://arxiv.org/html/2410.16107v1)  
11. Is It Human, or Is It AI? \- Dietrich College of Humanities and Social ..., 2月 10, 2026にアクセス、 [https://www.cmu.edu/dietrich/news/news-stories/2025/february/large-language-models-writing-text.html](https://www.cmu.edu/dietrich/news/news-stories/2025/february/large-language-models-writing-text.html)  
12. Redundancy and reduction: Speakers manage syntactic information ..., 2月 10, 2026にアクセス、 [https://pmc.ncbi.nlm.nih.gov/articles/PMC2896231/](https://pmc.ncbi.nlm.nih.gov/articles/PMC2896231/)  
13. Delving into PubMed Records: Some Terms in Medical Writing Have Drastically Changed after the Arrival of ChatGPT \*Corresponding \- medRxiv, 2月 10, 2026にアクセス、 [https://www.medrxiv.org/content/10.1101/2024.05.14.24307373v1.full.pdf](https://www.medrxiv.org/content/10.1101/2024.05.14.24307373v1.full.pdf)  
14. The most overused ChatGPT words \- Plus AI, 2月 10, 2026にアクセス、 [https://plusai.com/blog/the-most-overused-chatgpt-words](https://plusai.com/blog/the-most-overused-chatgpt-words)  
15. Words and Phrases that Make it Obvious You Used ChatGPT | by Margaret Efron \- Medium, 2月 10, 2026にアクセス、 [https://medium.com/learning-data/words-and-phrases-that-make-it-obvious-you-used-chatgpt-2ba374033ac6](https://medium.com/learning-data/words-and-phrases-that-make-it-obvious-you-used-chatgpt-2ba374033ac6)  
16. Distinguishing AI-Generated and Human-Written Text Through ..., 2月 10, 2026にアクセス、 [https://arxiv.org/abs/2505.01800](https://arxiv.org/abs/2505.01800)  
17. Echoes in AI: Quantifying lack of plot diversity in LLM outputs \- PNAS, 2月 10, 2026にアクセス、 [https://www.pnas.org/doi/10.1073/pnas.2504966122](https://www.pnas.org/doi/10.1073/pnas.2504966122)  
18. 人間らしくて少しラフなnote記事生成プロンプト（改訂版）2025/11 ..., 2月 10, 2026にアクセス、 [https://note.com/chi\_vc\_/n/n1698b2f55b1c](https://note.com/chi_vc_/n/n1698b2f55b1c)  
19. 2月 10, 2026にアクセス、 [https://www.unic.ac.cy/ai-lc/2023/04/11/perplexity-and-burstiness-in-ai-and-human-writing-two-important-concepts/\#:\~:text=In%20some%20ways%2C%20burstiness%20is,what%20perplexity%20is%20to%20words.\&text=AI%20is%20more%20robotic%3A%20uniform,encourages%20them%20to%20keep%20reading.](https://www.unic.ac.cy/ai-lc/2023/04/11/perplexity-and-burstiness-in-ai-and-human-writing-two-important-concepts/#:~:text=In%20some%20ways%2C%20burstiness%20is,what%20perplexity%20is%20to%20words.&text=AI%20is%20more%20robotic%3A%20uniform,encourages%20them%20to%20keep%20reading.)  
20. Comparisons of Quality, Correctness, and Similarity Between ChatGPT-Generated and Human-Written Abstracts for Basic Research: Cross-Sectional Study \- PMC, 2月 10, 2026にアクセス、 [https://pmc.ncbi.nlm.nih.gov/articles/PMC10760418/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10760418/)  
21. Perplexity and Burstiness in Writing \- Originality.ai, 2月 10, 2026にアクセス、 [https://originality.ai/blog/perplexity-and-burstiness-in-writing](https://originality.ai/blog/perplexity-and-burstiness-in-writing)  
22. A list of words that AI over-uses \- Embryo, 2月 10, 2026にアクセス、 [https://embryo.com/blog/list-words-ai-overuses/](https://embryo.com/blog/list-words-ai-overuses/)  
23. Write human-like responses to bypass AI detection. Prompt Included. \- Reddit, 2月 10, 2026にアクセス、 [https://www.reddit.com/r/ChatGPTPromptGenius/comments/1gwxdw4/write\_humanlike\_responses\_to\_bypass\_ai\_detection/](https://www.reddit.com/r/ChatGPTPromptGenius/comments/1gwxdw4/write_humanlike_responses_to_bypass_ai_detection/)  
24. A Prompt That Makes Your Writing Sound 100% Human (Maybe 80%) \- Reddit, 2月 10, 2026にアクセス、 [https://www.reddit.com/r/ChatGPTPromptGenius/comments/1lpe99y/a\_prompt\_that\_makes\_your\_writing\_sound\_100\_human/](https://www.reddit.com/r/ChatGPTPromptGenius/comments/1lpe99y/a_prompt_that_makes_your_writing_sound_100_human/)  
25. TURNING UP THE HEAT: MIN-p SAMPLING FOR ... \- OpenReview, 2月 10, 2026にアクセス、 [https://openreview.net/pdf?id=FBkpCyujtS](https://openreview.net/pdf?id=FBkpCyujtS)  
26. 2月 10, 2026にアクセス、 [https://arxiv.org/html/2407.01082v8\#:\~:text=Our%20results%20show%20that%20min,%2C%20particularly%20at%20high%2Dtemperatures.](https://arxiv.org/html/2407.01082v8#:~:text=Our%20results%20show%20that%20min,%2C%20particularly%20at%20high%2Dtemperatures.)  
27. LLM Parameters Explained: A Practical Guide with Examples for OpenAI API in Python, 2月 10, 2026にアクセス、 [https://learnprompting.org/blog/llm-parameters](https://learnprompting.org/blog/llm-parameters)  
28. How to Humanize AI Content Like a Pro in 2026 (What Actually Works) \- Medium, 2月 10, 2026にアクセス、 [https://medium.com/illumination/how-to-humanize-ai-content-like-a-pro-in-2025-what-actually-works-bc51eab02edc](https://medium.com/illumination/how-to-humanize-ai-content-like-a-pro-in-2025-what-actually-works-bc51eab02edc)  
29. Perplexity and Burstiness in AI and Human Writing: Two Important Concepts, 2月 10, 2026にアクセス、 [https://www.unic.ac.cy/ai-lc/2023/04/11/perplexity-and-burstiness-in-ai-and-human-writing-two-important-concepts/](https://www.unic.ac.cy/ai-lc/2023/04/11/perplexity-and-burstiness-in-ai-and-human-writing-two-important-concepts/)  
30. Full article: The psychology of LLM interactions: the uncanny valley and other minds, 2月 10, 2026にアクセス、 [https://www.tandfonline.com/doi/full/10.1080/29974100.2025.2457627](https://www.tandfonline.com/doi/full/10.1080/29974100.2025.2457627)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAZCAYAAABD2GxlAAAB7UlEQVR4Xu2WTShtURTH14sn8p6PDKSo1+ullBgwUcxkpkRJGbyhNzAyUTKRZCQTDKRkIDJSUpKBgYFipMzIVUovSb16Bgb4/1t7n7OtRLidY3B/9cu+e63rrrM/j0iOHDneTBmsMhY+yUiRCfjwgjdwNMpOkVvRgiz1okUuwHwTSxQWd287Raf7HJ7CShNLjHLRAjdtALSLFr4PS00sMRpFCxyxATAjGvtjA0nC9XUBq01/g2hxq6Y/UTi9B/AKLsJ5Z0a0uF6Y55PTgNP7Dx5KXBwdgD/itPTgqHGk6mzgs8DpZYHfbeCz4G+M12iFTfCL6NSzzbVZATvh1ygzhudmje0U/U6t6P/qgL+ehmOYwOKubeAZxuARnIXj8MT18QTog9vwW5SteRtwCR7DYtffBVfgHpyDg/DMxSJ4O/iRCx0KkwKaRY8gHkV8KMJDfdcngEv407W7RYsmfhN62txfPhiXF0fydxx+P7xR7oLPGdEXDcI3ny1Y5Nos3hfbD/+7dgiL4wbNGvzRneBzOGKcJr5UtEh8d3tYyDKchiVwzeWwaK5jPhRjH4bTG44Yi+W6KoDroutvSvQHOZpcCn6ND8NJl/9X9IbiQ7DQHsnS6xxvHL/+iN214QYh3MF8EH6Hu9bDNnNtf46s8QhTRmI8YWE5hwAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAZCAYAAADAHFVeAAABt0lEQVR4Xu2VTSgFURTHj1CU8pFIZGFnJfmKsBJZ2LBRNrKwsFWUbGVvrZCUfKyQBTGxwxalLJRSNlYsyMf/79zrnRnGe16W71e/3j333ubOmXNmnkiGDP9MPXyABbAHjsDs0A5lGR5FJ/9CPtyCt2buHV7CQhfzdxg+whY3lxZ9ohdfMXMHsMnEZFwSh6fNpOhhS2YuEL0JTzO8NnHatMMXuG/mzmCtG2eJHp5SVo0SvstO2G3ictH6nJu5Q9FmIcwqaZ0G4IUb8+5e4R0shqtwxq359TF4D59grpufgHt+02+cwA4Tsy4B7HVj1ipKBSwy8ZVoZoQ3tAi33TjEBsxx4zzRA5hNnWibV7m1OFgjZsYLU3bjLBwVfWqxdIk+wproQgyske2+OfhmYiYyZOIQfGQ7ohmmQiCaledY9IX28HrzJpZnuCmaDbNirTytsNLEFmbl6+S5kfBhzOrrvSwVrRHbedCNG9waO21BfiiyaJ0C+b4WzWxK9NF+ws3MjI0wDatFW5/xGizxGyOwTvwoR/Efav9KnMKyxLK+lGxlD7uvzcRRuJ8dF0c/3IXrov8MGTIk5wP800+8m7msugAAAABJRU5ErkJggg==>