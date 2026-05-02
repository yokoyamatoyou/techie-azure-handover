## OUTPUT_CONTRACT
- 返答は差分ではなく、[TITLE]/[LEAD]/[BODY]/[HASHTAGS] をすべて含む記事全文を返す。
- 未変更の箇所も省略せず残し、target span 以外は元の文面を極力そのまま保つ。
- 同じタグ形式だけを返す。CTAや余計な要約を足さない。
- partial patch-style output は返さない。
