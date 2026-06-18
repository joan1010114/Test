#!/usr/bin/env python3
"""自動執行器：跑完整個行銷團隊，輸出成品檔（週報 Markdown + 貼文圖 PNG）。

用途：給排程（cron）每週自動產出一整波行銷物料，無需開瀏覽器。

用法：
    python3 team_run.py --brand brands/hanfresh.json \
        --request "這週主推泡菜，幫我準備一波完整行銷"

輸出（預設）：marketing_runs/<日期>/
    report.md       完整週報（NORA 派發 + 四位專員產出 + 週報）
    team.json       原始結構化資料
    posts/*.png     MAYA 每篇貼文的社群圖（用 composer.py 合成）
無 ANTHROPIC_API_KEY 時走離線套版，仍會產出檔案。
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from agents import Brand, run_team
from agents.base import DEFAULT_MODEL, has_api_key
from composer import render


def _load_brand(path: str) -> Brand:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Brand(**data)


def _render_posts(brand: Brand, maya: dict, out_dir: Path, theme: str) -> list[str]:
    """把 MAYA 每篇貼文合成一張社群圖。"""
    posts_dir = out_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    calendar = maya.get("weekly_calendar") or []
    for i, post in enumerate(calendar, 1):
        product = {
            "name": brand.name or "品牌",
            "features": brand.selling_points[:3],
            "image": None,
        }
        copy = {
            "tagline": post.get("topic") or (post.get("caption") or "")[:18],
            "highlights": brand.selling_points[:3],
            "cta": "立即選購",
            "badge": post.get("channel"),
        }
        path = posts_dir / f"post_{i:02d}_{post.get('day', '')}.png"
        try:
            render(product, copy, layout="square", theme=theme, output=str(path))
            saved.append(str(path))
        except Exception as exc:  # 出圖失敗不該中斷整批
            print(f"  ! 第 {i} 張貼文圖跳過：{exc}")
    return saved


def _to_markdown(brand: Brand, request: str, data: dict) -> str:
    L: list[str] = []
    mode = "AI 即時生成" if data["online"] else "離線示範套版"
    L.append(f"# {brand.name} · 本週行銷週報")
    L.append(f"> 產出日期：{date.today().isoformat()}　|　模式：{mode}　|　需求：{request}\n")

    d = data["dispatch"]
    L.append("## 👑 NORA · 任務派發")
    for key, label in [("maya", "MAYA 社群"), ("leon", "LEON 設計"), ("iris", "IRIS SEO"), ("jack", "JACK 廣告")]:
        L.append(f"- **{label}**：{d.get(key, '')}")
    for dl in d.get("deadlines", []):
        L.append(f"  - ⏱ {dl}")

    maya = data["results"]["maya"]
    L.append("\n## 📣 MAYA · 社群小編")
    if maya.get("threads_hooks"):
        L.append("**Threads 開頭**")
        L += [f"- {h}" for h in maya["threads_hooks"]]
    if maya.get("weekly_calendar"):
        L.append("\n**一週貼文行事曆**\n")
        L.append("| 日 | 通路 | 主題 | 文案 |")
        L.append("|---|---|---|---|")
        for p in maya["weekly_calendar"]:
            cap = (p.get("caption", "") or "").replace("|", "／").replace("\n", " ")
            L.append(f"| {p.get('day','')} | {p.get('channel','')} | {p.get('topic','')} | {cap} |")
    rw = maya.get("rewrites") or {}
    if rw.get("versions"):
        L.append(f"\n**一鍵改寫**（原文：{rw.get('original','')}）")
        L += [f"- {v}" for v in rw["versions"]]

    leon = data["results"]["leon"]
    L.append("\n## 🎨 LEON · 設計總監")
    bg = leon.get("brand_guidelines") or {}
    if bg:
        L.append(f"- 配色：{bg.get('color_direction','')}")
        L.append(f"- 字體：{bg.get('typography','')}")
        L.append(f"- 影像：{bg.get('imagery','')}")
    for s in leon.get("landing_page", []):
        bits = [b for b in [s.get("headline"), s.get("subhead"), s.get("body"), s.get("cta")] if b]
        L.append(f"- **[LP] {s.get('section','')}**：" + "　".join(bits))
    for s in leon.get("sales_page", []):
        L.append(f"- **[Sales] {s.get('section','')}**：{s.get('content','')}")

    iris = data["results"]["iris"]
    L.append("\n## 🔍 IRIS · SEO 專員")
    if iris.get("keywords"):
        L.append("| 關鍵字 | 意圖 | 難度 |")
        L.append("|---|---|---|")
        for k in iris["keywords"]:
            L.append(f"| {k.get('keyword','')} | {k.get('intent','')} | {k.get('difficulty','')} |")
    ao = iris.get("article_outline") or {}
    if ao:
        L.append(f"\n**文章**：{ao.get('title','')}")
        L.append(f"- Meta 標題：{ao.get('meta_title','')}")
        L.append(f"- Meta 描述：{ao.get('meta_description','')}")
        L += [f"- {o}" for o in ao.get("outline", [])]

    jack = data["results"]["jack"]
    L.append("\n## 📊 JACK · 廣告投放手")
    for a in jack.get("ad_hooks", []):
        L.append(f"- **{a.get('hook','')}** — {a.get('primary_text','')}（{a.get('cta','')}）")
    ab = jack.get("audience_budget") or {}
    if ab.get("audiences"):
        L.append("\n**受眾 / 預算**")
        for a in ab["audiences"]:
            L.append(f"- {a.get('name','')}（{a.get('targeting','')}）：{a.get('budget_pct','')}%")

    rep = data["report"]
    L.append("\n## 👑 NORA · 團隊週報")
    L.append(rep.get("summary", ""))
    if rep.get("next_steps"):
        L.append("\n**等你決策**")
        L += [f"- {n}" for n in rep["next_steps"]]
    return "\n".join(L) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="行銷團隊自動執行器：產出週報 + 貼文圖")
    parser.add_argument("--brand", required=True, help="品牌設定 JSON 路徑，例如 brands/hanfresh.json")
    parser.add_argument("--request", default="依品牌設定推進本週例行行銷工作", help="對 NORA 說的一句話")
    parser.add_argument("--out", default="marketing_runs", help="輸出根目錄")
    parser.add_argument("--theme", default="sunset", choices=["sunset", "ocean", "mono"], help="貼文圖配色")
    parser.add_argument("--no-images", action="store_true", help="只產週報，不出圖")
    args = parser.parse_args()

    brand = _load_brand(args.brand)
    out_dir = Path(args.out) / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"→ 啟動 {brand.name} 行銷團隊（模型：{DEFAULT_MODEL}，{'線上' if has_api_key() else '離線'}）")
    data = run_team(brand, args.request)

    (out_dir / "team.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(_to_markdown(brand, args.request, data), encoding="utf-8")
    print(f"  ✓ 週報：{out_dir / 'report.md'}")

    if not args.no_images:
        saved = _render_posts(brand, data["results"]["maya"], out_dir, args.theme)
        print(f"  ✓ 貼文圖：{len(saved)} 張 → {out_dir / 'posts'}")

    print(f"✓ 完成：{out_dir}")


if __name__ == "__main__":
    main()
