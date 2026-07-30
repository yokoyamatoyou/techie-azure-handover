from app.services.source_fact_segmenter import extract_fact_candidates


def test_source_fact_segmenter_splits_heading_heavy_public_page_text():
    text = """
    データ入力・スキャニング | 京都工業株式会社
    SERVICE
    大阪オフィス開設のお知らせ
    前処理から後処理まで一貫対応
    各種自治体・大学での豊富なデータ入力実績
    データ活用の目的はあるが
    やり方がわからない
    データに関する課題を解決し、
    BPOを全面サポート
    RPAとデータエントリの
    総合力
    データ入力・エントリ業務をヒアリングから承ります。充実したスタッフ体制で、国内一貫で入力・チェック・納品まで対応します。
    これからますます重要になる情報資産の保護、セキュリティの対策、デジタル化、自動化、RPAのトレンドに向けて、伝統と革新が同居する古都、京都から新たなデータ化・デジタル化サポートを推進してまいります。
    導入の流れ
    お問い合わせ
    お電話またはメールフォームよりお気軽にお問い合わせください。
    """

    candidates = extract_fact_candidates(text, limit=6)

    assert "SERVICE" not in candidates
    assert all("|" not in candidate for candidate in candidates)
    assert "大阪オフィス開設のお知らせ" not in candidates
    assert "前処理から後処理まで一貫対応" in candidates
    assert "データ活用の目的はあるがやり方がわからない" in candidates
    assert "データに関する課題を解決し、BPOを全面サポート" in candidates
    assert "RPAとデータエントリの総合力" in candidates
    assert "データ入力・エントリ業務をヒアリングから承ります。" in candidates
    assert all("\n" not in candidate for candidate in candidates)
    assert all(len(candidate) <= 90 for candidate in candidates)


def test_source_fact_segmenter_removes_self_voice_and_incomplete_heading_fragments():
    text = """
    京都工業株式会社を先代から引継ぎ、私で4代目となります。
    前処理から後処理まで
    RPAとデータエントリの
    総合力
    納品時に、今後の改善内容についてもご提案させていただきます。
    """

    candidates = extract_fact_candidates(text, limit=6)

    assert all("私で4代目" not in candidate for candidate in candidates)
    assert "前処理から後処理まで" not in candidates
    assert "RPAとデータエントリの総合力" in candidates
    assert "納品時に、今後の改善内容についてもご提案させていただきます。" in candidates
