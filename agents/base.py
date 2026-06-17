"""Shared Claude API helper for the marketing agent team.

每位 agent 都呼叫 `run_agent()`：傳入角色 system prompt 與任務 payload，
回傳解析後的 JSON dict。沿用 copywriter.py 的模式（system 用 list + cache_control、
嚴格 JSON 輸出、無 API Key 時走 fallback）。
"""
from __future__ import annotations

import json
import os

from anthropic import Anthropic

# 預設模型：依目前 API 指南採用 Claude Opus 4.8。可用環境變數覆寫，
# 例如 ANTHROPIC_MODEL=claude-sonnet-4-6 以降低成本。
DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def run_agent(
    system_prompt: str,
    payload: dict,
    *,
    model: str | None = None,
    api_key: str | None = None,
    max_tokens: int = 1500,
) -> dict:
    """呼叫 Claude，回傳解析後的 JSON dict（失敗時回傳 {}）。

    呼叫端負責在沒有 API Key 時改走自己的 fallback。
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {}

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
    )
    text = next((b.text for b in response.content if b.type == "text"), "").strip()
    return _parse_json(text)


def _parse_json(text: str) -> dict:
    """容錯解析：先直接 parse，失敗則擷取第一個 {...} 區塊。"""
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {}
    return {}
