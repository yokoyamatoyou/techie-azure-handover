from __future__ import annotations

from billing_rules import SERVICE_KOTOMEGANE, build_billing_policy_microcopy
from config import AppConfig, ProviderOption, get_provider_option, get_provider_total_question_budget, resolve_provider_cache_policy
from run_policy import build_runtime_policy_microcopy


def provider_display_label(provider: ProviderOption) -> str:
    return "ChatGPT" if provider.key == "openai" else provider.label


def build_onboarding_markdown() -> str:
    return (
        "- `コトメガネ` は AI検索での見え方を確認する画面です。\n"
        "- ここで見るのは `AIの主要な参照先 / 自社引用率 / 次に強化すべき論点` です。\n"
        "- まずは質問を 1 件だけ入れます。\n"
        "- 必須は `質問` と `自社URL` だけです。\n"
        "- `名称` には会社名、サービス名、屋号などを入れます。\n"
        "- `重点テーマ` には地域 / 業界 / 用途を入れます。\n"
        "- 比較したい名前があるときだけ `比較対象` を入れます。\n"
        "- 実行後は `AIの主要な参照先` → `AI回答に使われた主要ソース` → `改善優先の質問` の順で見ます。\n\n"
        "例: `東京の製造業でAI検索に見える会社を知りたい` / `サービス名 料金` / `サービス名 導入事例` / `サービス名 FAQ`"
    )


def build_runtime_microcopy(config: AppConfig) -> str:
    provider_option = get_provider_option(config.provider)
    provider = provider_display_label(provider_option)
    cache_policy = resolve_provider_cache_policy(provider_option.key, config.model, config.prompt_cache_retention)
    cache_note = f"（{cache_policy['switch_note']}）" if cache_policy.get("switch_note") else ""
    return (
        f"{provider} / 推論 {config.reasoning_effort} / "
        f"検索 {config.search_context_size} / キャッシュ {cache_policy['display_label']}{cache_note} / "
        f"{build_runtime_policy_microcopy(config)} / 上限 "
        f"{get_provider_total_question_budget(provider_option.key, service_key=config.service_key, plan_key=config.plan_key)}件"
    )


def build_scope_markdown(config: AppConfig) -> str:
    provider_option = get_provider_option(config.provider)
    return (
        f"- 実行先: `{provider_display_label(provider_option)}`\n"
        f"- 実行方式: `{provider_option.summary}`\n"
        "- キャッシュと Batch の挙動を provider ごとに確認\n"
        "- `allowed_domains` は優先参照として扱います\n"
        f"- 実行ガード: `{('上限で停止' if config.budget_guardrail_mode == 'stop' else '上限前に警告')}`\n"
        "- 履歴は SQLite に保存"
    )


def build_runtime_markdown(config: AppConfig) -> str:
    cache_policy = resolve_provider_cache_policy(config.provider, config.model, config.prompt_cache_retention)
    return (
        f"- 接続先: `{provider_display_label(get_provider_option(config.provider))}`\n"
        f"- 推論の深さ: `{config.reasoning_effort}`\n"
        f"- キャッシュ識別キー: `{config.prompt_cache_key}`\n"
        f"- キャッシュ方針: `{cache_policy['display_label']}`\n"
        f"- キャッシュ注記: {cache_policy['note']}\n"
        f"- 検索深度: `{config.search_context_size}`\n"
        f"- 実行ガード: `{('上限で停止' if config.budget_guardrail_mode == 'stop' else '上限前に警告')}`\n"
        "- `allowed_domains`: 強制ではない優先参照"
    )


def build_cost_policy_text(config: AppConfig) -> str:
    return (
        f"{build_billing_policy_microcopy(SERVICE_KOTOMEGANE)}"
        " 実行ガードは内部で維持しつつ、金額は画面に出しません。"
        f" 現在は実行件数が多いときに {('停止' if config.budget_guardrail_mode == 'stop' else '警告')} します。"
    )
