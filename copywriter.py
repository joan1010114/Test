"""Claude API copywriting for e-commerce products."""
from __future__ import annotations

import json
import os

from anthropic import Anthropic

SYSTEM_PROMPT = """你是資深電商文案專家，擅長撰寫繁體中文的社群促銷文案。

根據用戶提供的商品資訊 (JSON)，產出吸睛、簡短、有行動力的文案。

請嚴格輸出以下 JSON 結構（不要加 markdown、不要任何解釋）：
{
  "tagline": "一句吸睛主打標語，最多 18 個全形字",
  "highlights": ["亮點1", "亮點2", "亮點3"],
  "cta": "行動呼籲文字，最多 6 個全形字",
  "badge": "角落徽章文字，最多 5 個全形字，或 null"
}

規則：
- highlights 列出 3 個商品賣點，每項最多 10 個全形字
- 若商品有折扣價，badge 請放「限時特惠」「熱銷中」等；無折扣則為 null
- 文案避免浮誇空話，聚焦商品實際特色
"""

DEFAULT_MODEL = "claude-sonnet-4-6"


def generate_copy(product: dict, model: str = DEFAULT_MODEL, api_key: str | None = None) -> dict:
    """Call Claude API to generate promotional copy; fall back to a template if unavailable."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_copy(product)

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=600,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": json.dumps(product, ensure_ascii=False, indent=2),
            }
        ],
    )
    text = response.content[0].text.strip()
    return _parse_json(text) or _fallback_copy(product)


def _parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _fallback_copy(product: dict) -> dict:
    features = product.get("features") or ["品質保證", "快速出貨", "滿意保固"]
    has_discount = bool(product.get("discount_price"))
    return {
        "tagline": product.get("tagline") or f"{product.get('name', '精選好物')}新上架",
        "highlights": features[:3],
        "cta": "立即購買",
        "badge": "限時特惠" if has_discount else None,
    }
