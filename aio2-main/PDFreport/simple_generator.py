# -*- coding: utf-8 -*-
"""HTMLテンプレートベースのシンプルなPDF生成"""
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent / "templates"


def generate_summary_pdf(data: Dict, output_path: str) -> str:
    """エグゼクティブ向けサマリーPDFを生成"""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report_summary.html")
    html_content = template.render(data=data)
    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(output_path)
    return output_path


if __name__ == "__main__":
    test_data = {
        "total_score": 75,
        "top_issues": [
            {"title": "特商法表示の不備", "severity": "high"},
            {"title": "Schema.org未設定", "severity": "low"},
        ],
    }
    generate_summary_pdf(test_data, "test_report.pdf")
    print("PDF generated: test_report.pdf")
