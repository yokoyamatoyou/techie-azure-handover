from __future__ import annotations

import argparse

from app.services.pipeline_runner import BlogPipelineRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fixture-only Japanese blog generation smoke path.")
    parser.add_argument("--title", default="会社紹介メモ")
    parser.add_argument(
        "--text",
        default="私たちは2018年に創業しました。地域の相談に応じています。初回相談で状況を確認します。",
    )
    args = parser.parse_args()
    result = BlogPipelineRunner().run_manual_sources([(args.title, args.text)])
    print(result.final_article)
    print(f"\nartifact_dir={result.artifact_dir}")


if __name__ == "__main__":
    main()
