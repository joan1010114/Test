#!/usr/bin/env python3
"""E-commerce promotional image generator (CLI entry)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from composer import LAYOUTS, THEMES, render
from copywriter import generate_copy


def _load_product(args: argparse.Namespace) -> dict:
    if args.product_json:
        path = Path(args.product_json)
        if not path.exists():
            sys.exit(f"商品 JSON 檔不存在: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    if not args.name:
        sys.exit("請提供 --name 或 --product-json")
    return {
        "name": args.name,
        "price": args.price,
        "discount_price": args.discount_price,
        "features": [f for f in (args.features or []) if f],
        "image": args.image,
        "tagline": args.tagline,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="電商圖文產生器：生成促銷文案 + 商品行銷圖")
    parser.add_argument("--product-json", help="商品資訊 JSON 檔路徑")
    parser.add_argument("--name", help="商品名稱")
    parser.add_argument("--price", type=float, help="原價")
    parser.add_argument("--discount-price", type=float, help="折扣價（可選）")
    parser.add_argument("--features", nargs="*", help="商品賣點列表（可選，若不指定將由 Claude 生成）")
    parser.add_argument("--image", help="商品圖路徑（可選，建議透明背景 PNG）")
    parser.add_argument("--tagline", help="自訂主打標語（可選）")
    parser.add_argument("--layout", choices=list(LAYOUTS), default="square", help="版型：square (1080x1080) 或 banner (1200x628)")
    parser.add_argument("--theme", choices=list(THEMES), default="sunset", help="配色主題")
    parser.add_argument("--output", "-o", default="output.png", help="輸出 PNG 路徑")
    parser.add_argument("--no-ai", action="store_true", help="跳過 Claude API，只用 fallback 文案")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Claude 模型 ID")
    parser.add_argument("--copy-out", help="另存產生的文案 JSON 至此路徑（可選）")
    args = parser.parse_args()

    product = _load_product(args)

    if args.no_ai:
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)

    print(f"→ 產生文案 (商品: {product.get('name')})")
    copy = generate_copy(product, model=args.model)
    print(f"  標語: {copy.get('tagline')}")
    print(f"  亮點: {copy.get('highlights')}")
    print(f"  CTA : {copy.get('cta')}")
    if copy.get("badge"):
        print(f"  徽章: {copy['badge']}")

    if args.copy_out:
        Path(args.copy_out).write_text(json.dumps(copy, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  文案已存至: {args.copy_out}")

    print(f"→ 合成圖片 (版型: {args.layout}, 主題: {args.theme})")
    out = render(product, copy, layout=args.layout, theme=args.theme, output=args.output)
    print(f"✓ 完成: {out}")


if __name__ == "__main__":
    main()
