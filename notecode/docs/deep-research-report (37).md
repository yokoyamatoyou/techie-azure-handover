# GPT系で自然な日本語ブログが崩れやすい理由と、次に試すべき実験設計

## 総合診断

添付資料を読む限り、いま起きている問題は「ソースが足りない」ことでも、「視点指定が甘い」ことでもありません。現行本番方式は source を書き手向けの材料に整理することで安定性を得ている一方、会社紹介になると、会社案内らしさ、文末単調、後半の総括調が残ります。しかも source packet、near-raw source、self-perspective、editor pass、plan-then-write のどれを試しても、別の形で brochure-like な構造へ戻っている。これは、失敗点が表層ではなく、**記事の談話目的を決める層**にあることを示しています。fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 fileciteturn0file4

最優先の原因は、**会社サイトという入力ジャンルの圧力**です。日本語の blog コーパスは semi-spoken として扱われる一方、既存の代表コーパスではブログやフォーラムと company pages は別ジャンルとして分かれており、会社ページはブログ文体の延長としては扱われていません。つまり、会社ページ由来の source を大量に与えると、モデルは自然に「ブログを書く」のではなく、「会社情報を正しく再構成する」方向へ寄りやすいのです。これは今回の比較ケースで、source を圧縮しても raw にしても会社案内化が残った観察と整合しています。fileciteturn0file1 fileciteturn0file4 citeturn11view1turn9view7turn9view6

次の原因は、**grounding 圧力と自然文体の衝突**です。外部研究では、factuality と fluency、あるいは factuality と abstractiveness の間にトレードオフがあることが繰り返し報告されています。文書 grounded 生成でも、faithfulness と fluency は同じ方向に自動では伸びず、重みをどう振るかで出力傾向が変わります。だから「根拠を漏らさない」「source 外を書かない」を強く掛けるほど、生成は安全な説明文・要約文・プロフィール文に寄りやすくなります。citeturn13view3turn9view0

三つ目の原因は、**日本語ブログらしさが sentence-level の装飾ではなく discourse-level の運用だから**です。自然な文章生成では、内容選択、文書計画、文への分配、語彙選択、照応表現の管理を別々に考える必要があることが、古典的 NLG でも近年の neural generation でも指摘されています。現行 Route A は content selection をかなりうまくやっている一方で、document planning、referring expression generation、sentence segmentation が「会社紹介として無難な解」に流れ、そこに AI っぽさが残っているとみるのが妥当です。fileciteturn0file0 citeturn9view2turn9view3

四つ目の原因は、**GPT-5.4 mini を小さな推論モデルとして使うときの literalness**です。entity["company","OpenAI","ai company"] の現行ドキュメントでは、GPT-5.4 は style と evidence-grounded synthesis への強い制御性を持つ一方、`gpt-5.4-mini` は larger models より implicit な補完や曖昧性解消が苦手で、より literal に振る舞いやすいと説明されています。ソース根拠、視点、禁止事項、文体要求をひとつの prompt stack で抱え込むと、小さめの highly steerable model は「自然に書く」より「契約どおりに外さない」を優先しやすく、結果として説明調が強まります。citeturn16view0turn16view1

## なぜ十分なソースがあっても自然なブログにならないのか

「ソースが十分なら、あとはうまく書くだけ」という発想が、この問題では外れています。grounded text generation の研究では、外部ソースを使う課題は単なる style transfer ではなく、**どの事実を、どの順序で、どの粒度で、どの文脈に埋めるか**という content transfer に近い課題だと整理されています。つまり必要なのは facts の供給ではなく、facts を blog の談話目的に合わせて再配置する能力です。citeturn13view0turn13view1turn13view2

今回の失敗履歴は、その構造をよく表しています。source packet 系は grounding を改善したが短くなり会社案内化し、near-raw 系は source loss を減らしたが自然な blog にはならなかった。これは「事実が少なすぎる」問題ではなく、**事実を並べると brochure になり、間引くと薄くなる**という問題です。研究的に見ると、ここで必要なのは global coverage を高めることではなく、段落ごとに使う事実を絞り、局所的に根拠を持たせることです。claim 単位の coverage と attribution を分けて見る ICAT や LAQuer の方向性は、その設計に近いです。fileciteturn0file1 fileciteturn0file2 citeturn9view4turn9view5

特に重要なのは、**会社紹介 source は最初から profile schema を誘発する**ことです。plan-then-write が「歴史・信頼・選ばれる理由・価格」に吸い寄せられたのは偶然ではありません。blog でも summary でも、schema が違うと同じ facts でも別の文章になります。query-based blog summarization の研究では、人が自然に書く blog 要約には rhetorical predicates と schema があり、そこを外すと coherence が崩れやすいことが示されています。逆に言えば、plan 自体が悪いのではなく、**会社プロフィールの schema で plan したこと**が悪かったのです。fileciteturn0file1 fileciteturn0file4 citeturn14view0turn9view12

後処理で直りにくいのも自然です。文の自然さは最後の言い換えだけで決まらず、どこで文を切るか、どの referent を明示するか、何を省くか、といった microplanning に依存します。NLG 研究では sentence boundary や referring expression は planning の後半ではあるものの、realization の前に決めるべき主要選択です。だから editor pass や repair loop は、壊れた談話設計を後から磨くことはできても、安定して作り直すことは難しいです。fileciteturn0file1 citeturn9view3turn8search6

## 日本語ブログ文体で特に難しい点

日本語らしい自然さの中核にあるのは、主語を消すことそのものではなく、**消しても読める談話状態を保つこと**です。日本語の省略は topicalized subject に強く偏り、述語の手がかりと文脈の topic chain に依存して解釈されます。さらに、author/reader に対応する exophoric なゼロ参照も重要です。したがって、「会社名を減らす」「私たちを入れる」といった表面操作だけでは不十分で、だれが見る主体なのか、だれに向けて書いているのか、前段落から何が topic として継続しているのかを制御しないと、自己視点と第三者視点が混ざります。citeturn11view0turn9view8

また、日本語 blog は新聞記事の延長ではなく、semi-spoken な register を帯びやすいです。blog corpus は semi-spoken として扱われ、Japanese web text では line break と sentence boundary が必ずしも一致しないことも観察されています。note 風の「段落呼吸」は、長文を整然と積むより、意味の節目で適度に改行し、ひとかたまりの思考を見せる方向にあります。ここを company profile の均質な段落で埋めると、内容が正しくても息苦しく見えます。citeturn9view7turn9view6

文末単調の問題も、日本語ではかなり本質的です。日本語の style は一人称、文末表現、助詞、補助動詞、honorifics など sentence 全体の組み合わせで立ち上がるとされます。sentence-end expressions は話者の態度や親しさを強く運び、formality は formal / polite / informal といった帯域で測るほうが実態に近い。均一な「です・ます」だけで全段落を流すと、会社案内としては整っても、人が書いた blog の気配は出にくいです。citeturn9view9turn12view0turn9view10

さらに、polite と casual の使い分けは intimacy と結びついています。日本語対話研究では、親密度が低いと polite style、高いと casual style が増える傾向が確認されています。会社ブログでは完全な casual に振る必要はありませんが、ずっと距離が遠いままの polite 語りで押し切ると、読者との関係が最後まで縮まらず、説明調が残ります。必要なのは砕けすぎではなく、**polite を基調にしつつ、主語省略・文長の緩急・軽い評価語で距離を一段だけ近づける**ことです。citeturn17view0

## Claude Sonnet と GPT系の差の仮説

ここは断定ではなく仮説として扱うべきですが、少なくとも比較対象が「Web版 Claude Sonnet」と「ローカルアプリ上の GPT-5.4 mini」である時点で、純粋な model A/B ではありません。entity["company","Anthropic","ai company"] は、claude.ai の Web / mobile では API と別の system prompt を使い、それが定期更新されると明記しています。つまり、Web 版の自然さには、基盤 model だけでなく、製品側の hidden prompt や UX tuning が効いている可能性があります。citeturn4view2

そのうえで傾向差を仮説化すると、Anthropic の現行 doc は Claude の最新世代を「more conversational」「less machine-like」と説明し、negative な禁止より positive examples や general instructions を勧めています。一方で OpenAI の現行 doc は GPT-5.4 / 5.5 系を evidence-rich synthesis、explicit contract、direct and task-oriented、outcome-first prompt に強いモデルとして説明し、gpt-5.4-mini はより literal で暗黙補完に弱いとしています。会社サイト source に grounding 制約を重ねると、後者は「正しく、漏らさず、外さず」に最適化されやすく、その最適解が blog ではなく整った説明文になる、というのが最も筋の通る仮説です。citeturn5view0turn10view0turn16view0

もう一つ大きいのは、prompt accretion への感受性です。OpenAI は process-heavy prompt stacks より shorter, outcome-first prompts を推奨し、高すぎる reasoning effort や conflicting instructions は quality regression を起こしうると述べています。Anthropic も prescriptive steps より general instructions を勧めています。つまり、「自然に」「主語省略」「文末分散」「禁止語回避」「広告っぽくしない」「根拠を落とさない」を全部 prompt に積むほど、モデルは writer ではなく compliance engine に近づきやすい。今回の prompt を足すほど AI っぽくなる感覚は、かなり理にかなっています。citeturn4view0turn10view0turn5view0turn9view1

## これまでの失敗を、外部研究でどう読み直すか

現行本番方式がそこそこ安定する理由は、source をそのまま流し込まず、「今の事業内容」「相談入口」「対応範囲」「進め方」に整理しているからです。これは classical NLG でいう content selection と high-level ordering を先に人為的に整えているのに近く、事実の暴走を抑えるうえでは正しい方向です。にもかかわらず自然な blog に届かないのは、その先の document planning と surface realization が「会社紹介として妥当」な方へ落ちるからです。Route A は壊れているのではなく、**安全な corporate prose に最適化された安定点**にいると見るのが正確です。fileciteturn0file0 citeturn9view3turn8search11

source packet 系が弱かった理由は、事実の整理そのものではなく、**切り口のエネルギーまで消した**ことです。research 的には、content conditioning と style / attribute conditioning をごちゃまぜにすると control が弱くなることが報告されています。つまり source を「使いやすく整理した」だけでは、まだ blog の語り口や段落呼吸は発生しません。facts を書き手の材料に変えるのではなく、**段落ごとの問いに答える材料**へ変える必要があります。fileciteturn0file1 citeturn9view1

near-raw source 系が解けなかった理由は、情報が少ないからではなく、genre prior が強すぎるからです。company page の raw 文脈は、モデルに「歴史」「信頼」「対応範囲」「価格」を優先させる圧力として働きます。これは BCCWJ の blog register とは別物なので、raw にすれば human-like になるという期待自体が外れています。fileciteturn0file1 citeturn11view1turn9view7

self-perspective 系が浅い改善で止まった理由は、視点が pronoun の問題ではないからです。author/reader exophora と zero reference の管理は discourse の問題で、表面上一人称を入れても構造が profile のままなら、読み味は変わりません。会社名を一人称化しないという制約だけでは、読者から見た距離感や topic chain は整いません。fileciteturn0file1 citeturn9view8turn11view0

editor pass / acceptance 系が安定しなかったのも自然です。blog の自然さは「最後に柔らかく言い換える」ことではなく、「何をどこで言うか」と「何を言わないか」で決まります。coherence 改善研究でも、後段の再配列や軽い heuristic は効果がある一方、schema や predicate tagging を外すと弱くなります。今回のケースでは、後処理が遅すぎます。fileciteturn0file1 citeturn14view0

## AIぽさの少ないブログを作るための設計原則

第一原則は、**coverage-first をやめて angle-first にする**ことです。会社紹介で自然に見える blog は、会社の全要素を均等に説明する文章ではなく、「読者にとって何が先に分かると嬉しいか」という角度から facts を選びます。全事実を薄く拾うほど brochure になるので、lead と中盤では「今の業務」「相談境界」「現場感がある運び」に寄せ、歴史・認証・価格は必要なときだけ局所的に使うほうがよいです。fileciteturn0file0 fileciteturn0file4 citeturn14view0turn9view5

第二原則は、**global grounding ではなく local grounding**です。記事全体に「 source を漏らさず反映しろ」を掛けるのではなく、各段落に micro-claim をひとつ置き、その claim に 1〜2 個の evidence span だけを許可する。これなら coverage pressure を下げつつ捏造も抑えられます。claim 単位の attribution と coverage を分離して見る最近の研究は、この発想を支持します。citeturn9view4turn9view5

第三原則は、**視点を文章中の persona ではなく、談話状態として固定する**ことです。具体的には、「語り手は会社内部の編集者」「会社本体は topic entity」「読者は暗黙の相手」という 3 役を内部状態として持ち、会社名・私たち・ゼロ主語のどれを許すかを段落単位で決めます。これで自己視点と第三者視点の混線を避けやすくなります。citeturn9view8turn11view0

第四原則は、**style を禁止語ではなく分布として扱う**ことです。文末、主語明示率、会社名反復率、段落長、formality 帯域、style embedding distance をまとめて見て、分布が target corpus に近いかで判断する。hard-ban を増やすほどモデルは不自然な回避運動をするので、禁止ではなく scorer で見るほうが安定します。citeturn9view9turn9view10turn5view0

## AIぽさの少ないブログ作成アルゴリズム

### 角度先行の claim card 方式

最も有望なのは、本文の前に「記事全体 plan」を作るのではなく、**段落ごとの claim card** を作る方式です。source から atomic facts を抜き出し、それぞれを「今の業務」「相談境界」「進め方」「背景証拠」「brochure-risk」に分類します。そのあと、ユーザーのテーマに対して 3〜5 個の reader angle を生成し、brochure-risk を強く含む angle を落とします。本文前に作るのは JSON の大きな構成表ではなく、各段落について「この段落の一文要約」「使ってよい事実は最大 2 個」「使ってはいけない fact bucket」「この段落の narrator state」だけです。段落生成はその card と直前段落だけを見せて行い、各段落の最後に claim-level grounding だけ検査します。これは source packet の v2 ではなく、coverage-first から angle-first へ目的関数を変える実験です。citeturn13view0turn9view4turn9view5turn14view0

### 視点固定の discourse map 方式

二つ目は、視点指定を prompt 文言から切り離し、**zero-subject を含む referent controller** として実装する方式です。各段落に「主語を省略してよい」「会社名を出してよい」「私たちを出してよい」の許可表を持たせ、lead は会社名 1 回まで、中盤はゼロ主語優先、境界説明では名詞主語を明示、といったルールに落とします。同時に段落機能を「導入の観察」「相談の入り口」「対応範囲の具体」「境界条件」「静かな締め」のような blog schema に固定します。これは self-perspective の再試行ではなく、pronoun を変えるのではなく referent policy を変える実験です。citeturn11view0turn9view8turn14view0

### 局所再生成の surface realization 方式

三つ目は、全文 editor pass をやめて、**段落単位の局所再生成**に限定する方式です。最初の draft は neutral でよく、その後に各段落だけを semi-spoken polite register へ再生成します。この再生成では「一つの正例」を少数与え、negative ban list は使わず、sentence-ending variety、company-name repetition、formality band、style embedding を scorer で見ます。GPT-5.4-mini には exact step order と one correct example が効きやすく、Claude 側の doc でも negative instructions より positive examples が有効だとされています。重要なのは、内容を直すのではなく surface realization だけを局所的にやることです。これなら editor pass のように全文を壊しにくいです。citeturn16view0turn5view0turn9view9turn9view10

### 最初に実装すべき narrow owner scope

最初の一手は、**branding / company_introduction に限定した「角度先行 claim card」だけ**です。Route A は変えず、shadow route で、保存済み company introduction ケースだけに適用する。実装範囲は atomic fact tagging、brochure-risk tagging、reader angle scoring、段落ごとの allowed facts 生成までに絞り、本文生成モデルや repair 回数は増やさない。この範囲なら、既存失敗の主要因である「記事構成の時点で会社案内化する」問題に直接触れつつ、Route A を壊さず、owner scope も小さく保てます。fileciteturn0file0 fileciteturn0file1 fileciteturn0file5

## 日本語文体の評価指標と失敗判定

人手評価だけでは遅いので、まず target corpus を二種類用意するのがよいです。ひとつは自然な日本語の company-operated blog / note 風記事、もうひとつは会社情報ページや brochure 寄りの文章です。特定書き手の模倣ではなく、匿名化した分布だけを使います。そこから以下の指標を取ると、今回の失敗をかなり正確に捉えられます。指標設計の根拠としては、日本語 style が pronouns・sentence endings・formality に強く出ること、blog が semi-spoken で line break を多用すること、blog coherence が discourse schema に依存することが挙げられます。citeturn9view9turn9view10turn9view7turn9view6turn14view0

**主語明示率**は、文頭の会社名・「私たち」・明示主語の頻度を見ます。自然な日本語 blog より高すぎれば、説明的です。**会社名反復率**は 1000 字あたりの会社名出現回数で取り、lead 以降に高ければ brochure 圧が強いと見なせます。**文末多様度**は sentence-ending の entropy や repeated ending ratio で見ます。**formality 帯域**は formal / polite / informal classifier で計測し、全部が formal-polite 側に寄り切っていれば距離が遠すぎます。**style embedding 距離**は target corpus の分布に近いかを見るために使えます。citeturn9view10turn9view9turn12view0

**段落呼吸**は、平均段落長だけでなく、段落長分散、1 文段落率、段落末の information density を見ます。日本語 blog は line break と sentence boundary が一致しないことがあるので、段落は単純な sentence count ではなく、意味のまとまりとして計測する必要があります。**brochure-risk 比率**は、歴史・価格・認証・信頼訴求の facts が lead と締めにどれだけ出たかを見る application-specific 指標です。これは外部一般理論というより、今回の失敗ログから最も効く実務指標です。fileciteturn0file1 fileciteturn0file4 citeturn9view6

失敗判定基準は、次のように明確に切れる形がよいです。**根拠面の失敗**は unsupported claim が 1 つでもあれば失敗です。**構成面の失敗**は lead が歴史・信頼・価格から始まった時点で失敗です。**文体面の失敗**は、文末多様度・主語明示率・会社名反復率・style embedding のうち 2 指標以上が target corpus の許容帯域を外れたら失敗です。**実用品質の失敗**は、人手比較で Route A より自然さが上がらず、しかも grounding precision が下がった場合です。これなら「少し違うけれど良くなった」ではなく、「何をもって reject / park するか」を先に共有できます。fileciteturn0file1 fileciteturn0file5 citeturn9view5turn9view4

要するに、AI っぽさの少ない日本語 blog ができないのは、モデルが日本語を知らないからではありません。**会社サイト由来の facts を、会社案内の schema ではなく、読者の関心を軸にした blog schema へ再配置する層**が欠けているからです。Route A はその手前まではかなりできているので、次に足すべきなのは prompt の禁止事項でも editor でもなく、angle selection、claim-local grounding、referent control、そして distribution-based な日本語 style evaluation です。そこに絞れば、既存失敗の単純な焼き直しではない、実験として意味のある shadow route を作れます。fileciteturn0file0 fileciteturn0file1 fileciteturn0file2 citeturn9view3turn14view0turn16view0