# Phase 02: 文中E-E-A-T検出強化（日本語対応）

優先度: 🔴 高
状態: ✅ 完了（2026-02-27）
依存: P01完了後推奨（独立実行も可）

---

## 背景・根拠

### 現行実装の限界

`aio_analyzer.py` の E-E-A-T 検出は JSON-LD（Schema.org）依存:
```python
# 現行: JSON-LDにAuthor/Organizationがあるかどうかのみ
aeo_patterns = self.analyze_aeo_patterns(soup)
entity_linking = self.calculate_entity_linking(text)
```

### 問題

日本語サイトの実態:
- JSON-LD Author/Person を設定しているサイトは少数派
- 著者情報は「〇〇 一級建築士」「医学博士 △△」のように本文テキストに埋まっている
- 「当院の院長（内科専門医）」「著者：弁護士 山田太郎」のような表記が多い
- E-E-A-Tが AI filtering の**前提条件**になった現状（2025年）、
  日本語サイトの70〜80%が正当に評価できていない

---

## 変更内容

### 新規関数: `detect_inline_eeat()` を `aio_analyzer.py` に追加

JSON-LDに頼らず、本文テキストから日本語固有のE-E-A-Tシグナルを検出する。

#### 検出対象と正規表現パターン

```python
# E-E-A-Tシグナル検出パターン（日本語）
EEAT_PATTERNS_JA = {
    # 資格・免許
    "license": [
        r"(一級|二級|三級)?(建築|施工管理|電気工事|危険物取扱|宅地建物取引)+(士|技士|主任者|検定)",
        r"(医師|歯科医師|薬剤師|看護師|管理栄養士|社会福祉士|精神保健福祉士)",
        r"(弁護士|司法書士|行政書士|税理士|公認会計士|社会保険労務士|中小企業診断士)",
        r"(ファイナンシャルプランナー|FP[1-3]級|AFP|CFP)",
        r"(博士|修士|学士)\s*(号|課程)",
        r"Ph\.?D",
    ],
    # 著者明示
    "author_explicit": [
        r"(著者|筆者|執筆者|監修者?|編集者?)\s*[:：]\s*[\u4e00-\u9fff\u3040-\u30ff]{2,10}",
        r"(執筆|監修)\s*[：:]\s*[\u4e00-\u9fff\u3040-\u30ff]{2,10}",
        r"[\u4e00-\u9fff\u3040-\u30ff]{2,6}\s*(医師|弁護士|税理士|薬剤師|栄養士)",
    ],
    # 組織・経験
    "organization": [
        r"(株式会社|有限会社|合同会社|一般社団法人|公益財団法人|医療法人)",
        r"(〇〇年の経験|[0-9０-９]{1,2}年以上の(経験|実績|キャリア))",
        r"(元\s*[\u4e00-\u9fff]{2,10}|前\s*[\u4e00-\u9fff]{2,10}(勤務|所属|在籍))",
    ],
    # 一次情報シグナル（体験・実測）
    "first_hand": [
        r"(実際に|自分で|筆者が|私が)\s*(試|使|調|体験|確認)",
        r"(実測|計測|独自(調査|検証|データ))",
        r"([0-9０-９]+\s*(件|例|症例|事例|サンプル)\s*(を)?(分析|調査|確認|検証))",
    ],
}
```

#### スコア計算ロジック

```python
def detect_inline_eeat(self, text: str, soup: BeautifulSoup) -> dict:
    """
    日本語本文テキストからE-E-A-Tシグナルを検出し、スコアと詳細を返す。
    Returns:
        {
            "score": float(0〜10),
            "signals": {"license": [...], "author_explicit": [...], ...},
            "signal_count": int,
            "has_json_ld_eeat": bool,
            "combined_score": float,  # JSON-LD + inline の合算
        }
    """
    signals = {}
    total_hits = 0

    for category, patterns in EEAT_PATTERNS_JA.items():
        hits = []
        for pat in patterns:
            matches = re.findall(pat, text)
            hits.extend(matches[:3])  # 同一パターンは最大3件
        signals[category] = list(set(hits))  # 重複除去
        total_hits += len(signals[category])

    # スコア計算（上限10点）
    # - license検出: 最大4点
    # - author_explicit: 最大3点
    # - organization: 最大2点
    # - first_hand: 最大1点
    score = min(10.0, (
        min(4.0, len(signals.get("license", [])) * 2.0) +
        min(3.0, len(signals.get("author_explicit", [])) * 1.5) +
        min(2.0, len(signals.get("organization", [])) * 1.0) +
        min(1.0, len(signals.get("first_hand", [])) * 0.5)
    ))

    # 既存JSON-LD E-E-A-Tスコアと合算（最大10点を超えない）
    existing_eeat = self._get_existing_eeat_score()  # 既存の検出結果を参照
    combined_score = min(10.0, score + existing_eeat * 0.5)

    return {
        "score": round(score, 2),
        "signals": signals,
        "signal_count": total_hits,
        "has_json_ld_eeat": existing_eeat > 0,
        "combined_score": round(combined_score, 2),
    }
```

#### `analyze()` メソッドへの組み込み

`aio_analyzer.py` の `analyze()` 内で `check_technical_aio()` の後に追加:

```python
# Phase 2: 文中E-E-A-T検出（日本語対応）
inline_eeat = self.detect_inline_eeat(text, soup)
```

`total_score` の計算式に組み込む（既存の eeat スコアを inline_eeat で補強）:
```python
# eeat スコアを inline_eeat で底上げ（既存ゼロでも評価可能に）
eeat_score = max(
    scores.get("eeat", {}).get("score", 0.0),
    inline_eeat["combined_score"]
)
```

---

## UI表示の追加

`core/ui/tabs/aio_tab.py` の E-E-A-T セクションに検出シグナルを追加表示:

```
E-E-A-T スコア: 7.5 / 10
  ✅ 資格検出: 税理士, ファイナンシャルプランナー
  ✅ 著者明示: 執筆：山田太郎
  ℹ️ 一次情報: 未検出（実測・独自調査の記載を推奨）
  ℹ️ JSON-LD: Author未設定（schema.org/Person の実装を推奨）
```

---

## 改善アドバイスの追加

`aio_suggestions.py` に以下のアドバイスを追加:

- `inline_eeat.score < 3` の場合:
  「著者の氏名・資格・所属をページ内テキストに明記してください（例: 監修：山田太郎 税理士）」
- `inline_eeat.has_json_ld_eeat == False` の場合:
  「schema.org/Person の JSON-LD を実装し、著者の資格・所属をマークアップしてください」
- `inline_eeat.signals["first_hand"]` が空の場合:
  「実測データ・独自調査・体験談など一次情報を含めると AI に引用されやすくなります」

---

## 完了条件

- [ ] `python -m py_compile core/aio_analyzer.py` がエラーなし
- [ ] `detect_inline_eeat()` が空テキストで `{"score": 0.0, ...}` を返す（エラーなし）
- [ ] 「税理士」「医師」「弁護士」を含むテキストで `score > 0` を返す
- [ ] 「著者：山田太郎」を含むテキストで `author_explicit` に検出結果が入る
- [ ] 既存JSON-LD E-E-A-T検出がある場合に `combined_score > score` になる
- [ ] UIのE-E-A-Tセクションに検出シグナルが表示される
- [ ] WORKLOG更新

---

## 注意事項

- 正規表現は過検出に注意。`re.findall` のマッチ数を最大3件に制限済み
- `first_hand` パターンは誤検出しやすい。スコア寄与を0.5に抑えている
- Sudachi と併用する場合、本関数は**Sudachi不使用**（テキスト直接正規表現）でよい
- fail-open: 検出失敗時は `score=0.0` を返し、分析全体を止めない
