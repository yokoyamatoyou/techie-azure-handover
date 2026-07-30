"""_parse_outline の実動作テスト: MCP4と同じパターンのLLM応答を渡して検証"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from note.outline_mixin import OutlineMixin

# --- 1. _is_valid_heading テスト ---
print("=== _is_valid_heading テスト ===")
cases = [
    '```json',
    '{',
    '"sections": [',
    '"heading": "日常で感じるAI活用のもどかしさ"',
    'まとめ："required_elements": [',
    '"purpose": "読者の共感を得て、AI活用の現状への課題感を共有する",',
    '日常で感じるAI活用のもどかしさ、その原因は何？',
    'MCPとは何か',
]
for t in cases:
    r = OutlineMixin._is_valid_heading(t)
    mark = "OK" if not r else "PASS"
    if '"' in t or '{' in t or '[' in t or '`' in t:
        mark = "REJECT" if not r else "BUG-PASS"
    else:
        mark = "ACCEPT" if r else "BUG-REJECT"
    print(f"  {mark:12s} | {t[:70]}")

# --- 2. _strip_code_fences テスト ---
print("\n=== _strip_code_fences テスト ===")
raw_with_fence = '```json\n{"sections": [{"heading": "テスト見出し"}]}\n```'
cleaned = OutlineMixin._strip_code_fences(raw_with_fence)
print(f"  Input:   {raw_with_fence!r}")
print(f"  Cleaned: {cleaned!r}")
print(f"  Fences removed: {cleaned != raw_with_fence}")

# --- 3. _parse_outline テスト (正常JSON) ---
print("\n=== _parse_outline テスト (正常JSON) ===")
class Dummy(OutlineMixin):
    def __init__(self):
        self._structure_features = {}
        self._interview_answers = {}
    def _get_outline_section_range(self):
        return (3, 8)
o = Dummy()

raw_json = '```json\n{"sections": [{"heading": "日常で感じるAI活用のもどかしさ", "purpose": "共感"}, {"heading": "MCPとは何か", "purpose": "解説"}]}\n```'
result = o._parse_outline(raw_json)
print(f"  Sections: {len(result)}")
for s in result:
    print(f"    heading: {s['heading'][:80]}")

# --- 4. _parse_outline テスト (壊れたJSON - MCP4パターン) ---
print("\n=== _parse_outline テスト (壊れたJSON - MCP4パターン) ===")
# LLMが返す可能性のある壊れたパターン
raw_broken = """```json
{
  "sections": [
    {
      "heading": "日常で感じるAI活用のもどかしさ、その原因は何？",
      "purpose": "読者の共感を得て、AI活用の現状への課題感を共有する",
      まとめ："required_elements": ["""

result2 = o._parse_outline(raw_broken)
print(f"  Sections: {len(result2)}")
for s in result2:
    print(f"    heading: {s['heading'][:80]}")

# --- 5. _parse_outline テスト (JSONパース成功するが見出しにJSON断片) ---
print("\n=== _parse_outline テスト (見出しにJSON構文が含まれるケース) ===")
raw_bad_headings = '{"sections": [{"heading": "```json"}, {"heading": "{"}, {"heading": "\\"sections\\": ["}, {"heading": "正常な見出し"}]}'
result3 = o._parse_outline(raw_bad_headings)
print(f"  Sections: {len(result3)}")
for s in result3:
    print(f"    heading: {s['heading'][:80]}")

# --- 6. フォールバックテスト ---
print("\n=== フォールバックテスト (JSONパース完全失敗) ===")
raw_no_json = """```json
{
  "sections": [
    {
      "heading": "見出しA",
      "purpose": "テスト"
    },
これは壊れたJSON"""
result4 = o._parse_outline(raw_no_json)
print(f"  Sections: {len(result4)}")
for s in result4:
    print(f"    heading: {s['heading'][:80]}")

# --- 7. _try_partial_json_parse テスト ---
print("\n=== _try_partial_json_parse テスト ===")
# MCP4/20113と同じパターン: JSONが途中で切れている
truncated_json = """```json
{
  "sections": [
    {
      "heading": "AIがもっと便利になる理由は「MCP」の存在だった！",
      "purpose": "読者の関心を引き、AIと外部システムのつながりの重要性を伝える",
      "required_elements": [
        "AIが単独ではできないことの説明",
        "MCP"""
result_partial = OutlineMixin._try_partial_json_parse(truncated_json)
if result_partial:
    print(f"  Recovered {len(result_partial)} sections from truncated JSON:")
    for s in result_partial:
        print(f"    heading: {s['heading'][:80]}")
else:
    print("  FAILED: No sections recovered")

# 複数見出しが切れたJSON
truncated_multi = """{"sections": [
    {"heading": "導入：AIの現状", "purpose": "背景説明"},
    {"heading": "MCPとは何か", "purpose": "解説"},
    {"heading": "具体的な活用例", "purpose": "事例紹介"},
    {"heading": "まとめ：次の一歩"""
result_multi = OutlineMixin._try_partial_json_parse(truncated_multi)
if result_multi:
    print(f"  Recovered {len(result_multi)} sections from multi-heading truncated JSON:")
    for s in result_multi:
        print(f"    heading: {s['heading'][:80]}")
else:
    print("  FAILED: No sections recovered")

# --- 8. _parse_outline で部分パースが動くか統合テスト ---
print("\n=== _parse_outline 統合テスト (切れたJSON) ===")
result_integrated = o._parse_outline(truncated_json)
print(f"  Sections: {len(result_integrated)}")
for s in result_integrated:
    print(f"    heading: {s['heading'][:80]}")
if len(result_integrated) >= 1 and result_integrated[0]['heading'] != '本文':
    print("  OK: 切れたJSONから見出しを回復できた")
else:
    print("  NG: フォールバックの「本文」になってしまった")

print("\n=== 完了 ===")
